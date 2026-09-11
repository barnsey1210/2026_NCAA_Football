#!/usr/bin/env python3
"""Build the standalone Futures data contract and daily market QA artifact."""
from pathlib import Path
from datetime import datetime, timezone
import csv, json, math, os, re, sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.ncaaf_config import canonical_team

DATA_ROOT = Path(
    os.environ.get("NCAAF_RUNTIME_ROOT", str(ROOT))
).expanduser().resolve()

ACTION_PATH = DATA_ROOT / "data/markets/action/action_playoff_futures_2026.json"
MARKET_CONTRACT_PATH = Path(
    os.environ.get(
        "NCAAF_FUTURES_CONTRACT_PATH",
        str(DATA_ROOT / "data/markets/current_futures_market_2026.json"),
    )
).expanduser().resolve()
SEASON_MODEL_PATH = DATA_ROOT / "data/site/season_simulations_2026.json"
PLAYOFF_MODEL_PATH = DATA_ROOT / "data/site/playoff_model_2026.json"
BETS_PATH = DATA_ROOT / "data/site/betting_activity_view.json"
WIN_MOVEMENT_PATH = DATA_ROOT / "market_win_totals_movement.csv"
TITLE_MOVEMENT_PATH = DATA_ROOT / "market_conference_futures_movement.csv"
FUTURES_CHECKPOINTS_PATH = DATA_ROOT / "data/markets/futures_checkpoints_2026.jsonl"
RELIABILITY_AUDIT_PATH = Path(
    os.environ.get(
        "NCAAF_FUTURES_RELIABILITY_PATH",
        str(DATA_ROOT / "data/audits/futures_market_reliability.json"),
    )
).expanduser().resolve()
SCHEDULE_PATH = DATA_ROOT / "data/canonical/cfbd_schedule_2026.json"
RESULTS_PATH = DATA_ROOT / "data/canonical/game_results_2026.json"
PRESEASON_DB_PATH = DATA_ROOT / "data/snapshots/preseason/preseason_db.json"
RATINGS_MASTER_PATH = DATA_ROOT / "data/ratings/ratings_master_latest.csv"
RATINGS_HISTORY_PATH = DATA_ROOT / "data/ratings/ratings_history.csv"
PROJECTION_BLEND_PATH = DATA_ROOT / "data/projections/game_projection_blend_2026.csv"
WIN_PROB_LOGISTIC_SCALE = 6.5

QA_PATH = Path(
    os.environ.get(
        "NCAAF_FUTURES_QA_OUT",
        str(DATA_ROOT / "data/qa/futures_market_qa.json"),
    )
).expanduser().resolve()

OUT = Path(
    os.environ.get(
        "NCAAF_FUTURES_VIEW_OUT",
        str(DATA_ROOT / "data/site/futures_view.json"),
    )
).expanduser().resolve()

def load_futures_checkpoints(path):
    records = []

    if not path.exists():
        return records

    for line in path.read_text().splitlines():
        line = line.strip()

        if not line:
            continue

        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        if isinstance(obj, dict):
            records.append(obj)

    return records


def numeric_delta(current, prior):
    current_value = number(current)
    prior_value = number(prior)

    if current_value is None or prior_value is None:
        return None

    return current_value - prior_value


def select_weekly_baseline(records, games, current_built_at, fbs_teams):
    """Select the latest checkpoint before the prior completed FBS week began."""
    current_dt = parse_dt(current_built_at)
    if not records or current_dt is None:
        return None, {"status": "unavailable", "reason": "No checkpoint history or current build timestamp."}

    completed_weeks = []
    for game in games or []:
        week = game.get("cfbd_week") if game.get("cfbd_week") is not None else game.get("week")
        teams = {canonical_team(game.get("away_team")), canonical_team(game.get("home_team"))}
        if (game.get("cfbd_completed") or game.get("completed")) and week is not None and teams <= fbs_teams:
            completed_weeks.append(int(week))
    if not completed_weeks:
        return None, {"status": "unavailable", "reason": "No completed FBS game week is available."}

    prior_week = max(completed_weeks)
    kickoffs = []
    for game in games or []:
        week = game.get("cfbd_week") if game.get("cfbd_week") is not None else game.get("week")
        teams = {canonical_team(game.get("away_team")), canonical_team(game.get("home_team"))}
        if week is None or int(week) != prior_week or not teams <= fbs_teams:
            continue
        kickoff = parse_dt(game.get("cfbd_start_date") or game.get("start_date") or game.get("date"))
        if kickoff is not None:
            kickoffs.append(kickoff)
    if not kickoffs:
        return None, {"status": "unavailable", "reason": f"Week {prior_week} has no usable FBS kickoff timestamp."}

    cutoff = min(kickoffs)
    candidates = []
    for record in records:
        checkpoint_at = parse_dt(record.get("checkpoint_at") or record.get("source_view_built_at"))
        successful = record.get("status") in (None, "successful")
        if checkpoint_at is not None and checkpoint_at < cutoff and record.get("rows") and successful:
            candidates.append((checkpoint_at, record))
    meta = {"prior_week": prior_week, "cutoff_at": cutoff.isoformat()}
    if not candidates:
        meta.update({"status": "unavailable", "reason": f"No successful checkpoint exists before Week {prior_week}'s first FBS kickoff."})
        return None, meta
    selected_at, selected = max(candidates, key=lambda item: item[0])
    meta.update({"status": "available", "checkpoint_at": selected_at.isoformat(), "checkpoint_date": selected.get("checkpoint_date"), "checkpoint_id": selected.get("checkpoint_id") or f"{selected.get('checkpoint_date')}@{selected_at.isoformat()}"})
    return selected, meta


def number(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def build_schedule_index(schedule_games, projection_rows, fbs_teams):
    """Store each canonical game once and return chronological team references."""
    projections = {}
    for row in projection_rows:
        key = (
            str(row.get("date") or "")[:10],
            canonical_team(row.get("away_team")),
            canonical_team(row.get("home_team")),
        )
        projections[key] = number(row.get("site_spread_home"))

    schedule_index = {}
    team_game_ids = {team: [] for team in fbs_teams}
    for game in schedule_games or []:
        if str(game.get("season_type") or "regular").lower() != "regular":
            continue
        away = canonical_team(game.get("away_team"))
        home = canonical_team(game.get("home_team"))
        participants = [team for team in (away, home) if team in team_game_ids]
        if not participants:
            continue
        date = str(game.get("date") or game.get("start_date") or "")[:10]
        margin_home = projections.get((date, away, home))
        home_win_prob = (
            1.0 / (1.0 + math.exp(-margin_home / WIN_PROB_LOGISTIC_SCALE))
            if margin_home is not None and not game.get("completed")
            else None
        )
        provider_id = game.get("cfbd_game_id") or game.get("game_id")
        game_id = str(provider_id or f"{date}:{away}:{home}")
        schedule_index[game_id] = {
            "week": game.get("week"),
            "date": date,
            "away_team": away,
            "home_team": home,
            "neutral_site": bool(game.get("neutral_site")),
            "completed": bool(game.get("completed")),
            "away_score": number(game.get("away_points")),
            "home_score": number(game.get("home_points")),
            "home_win_probability": home_win_prob,
        }
        for team in participants:
            team_game_ids[team].append(game_id)
    order = lambda game_id: (
        int(schedule_index[game_id].get("week") or 99),
        schedule_index[game_id].get("date") or "",
        game_id,
    )
    for game_ids in team_game_ids.values():
        game_ids.sort(key=order)
    schedule_index = dict(sorted(schedule_index.items(), key=lambda item: order(item[0])))
    return schedule_index, team_game_ids

def implied(odds):
    odds = number(odds)
    if odds is None:
        return None
    return (-odds) / ((-odds) + 100) if odds < 0 else 100 / (odds + 100)

def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None

def age_hours(value):
    dt = parse_dt(value)
    if not dt:
        return None
    return max(0.0, (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 3600)


ACTION_TEAM_ALIASES = {
    "florida st": "Florida State",
    "ok state": "Oklahoma State",
    "oklahoma st": "Oklahoma State",
    "san diego st": "San Diego State",
    "boise st": "Boise State",
    "fresno st": "Fresno State",
    "colorado st": "Colorado State",
    "utah st": "Utah State",
    "arizona st": "Arizona State",
    "kansas st": "Kansas State",
    "michigan st": "Michigan State",
    "ohio st": "Ohio State",
    "penn st": "Penn State",
    "oregon st": "Oregon State",
    "washington st": "Washington State",
    "iowa st": "Iowa State",
    "mississippi st": "Mississippi State",
    "app state": "Appalachian State",
    "appalachian st": "Appalachian State",
    "ga state": "Georgia State",
    "georgia st": "Georgia State",
    "ga southern": "Georgia Southern",
    "miami fl": "Miami-FL",
    "miami florida": "Miami-FL",
    "miami oh": "Miami-OH",
    "miami ohio": "Miami-OH",
    "ucf": "Central Florida",
    "usf": "South Florida",
    "utsa": "UTSA",
    "utep": "UTEP",
    "fiu": "Florida International",
    "fau": "Florida Atlantic",
    "lsu": "LSU",
    "smu": "SMU",
    "tcu": "TCU",
    "uab": "UAB",
    "byu": "BYU",
    "umass": "Massachusetts",
    "ole miss": "Mississippi",
    "southern miss": "Southern Mississippi",
    "nc state": "NC State",
    "north carolina st": "NC State",
    "arkansas st": "Arkansas State",
    "boston col": "Boston College",
    "c michigan": "Central Michigan",
    "coastal car": "Coastal Carolina",
    "e carolina": "East Carolina",
    "e michigan": "Eastern Michigan",
    "fl atlantic": "Florida Atlantic",
    "ga tech": "Georgia Tech",
    "jax state": "Jacksonville State",
    "k state": "Kansas State",
    "kennesaw st": "Kennesaw State",
    "la tech": "Louisiana Tech",
    "la monroe": "Louisiana-Monroe",
    "middle tenn": "Middle Tennessee",
    "mississippi": "Ole Miss",
    "missouri st": "Missouri State",
    "n illinois": "Northern Illinois",
    "n mexico st": "New Mexico State",
    "nd state": "North Dakota State",
    "s alabama": "South Alabama",
    "s carolina": "South Carolina",
    "s florida": "South Florida",
    "sac state": "Sacramento State",
    "san jose st": "San Jose State",
    "southern mississippi": "Southern Miss",
    "texas st": "Texas State",
    "uconn": "Connecticut",
    "unc": "North Carolina",
    "va tech": "Virginia Tech",
    "w kentucky": "Western Kentucky",
    "w michigan": "Western Michigan",
}

def normalize_action_team(value):
    raw = str(value or "").strip()
    key = re.sub(r"[^a-z0-9]+", " ", raw.lower()).strip()
    mapped = ACTION_TEAM_ALIASES.get(key, raw)
    return canonical_team(mapped)


ACTION_MODEL_CANDIDATES = {
    "louisiana monroe": ["Louisiana-Monroe", "Louisiana Monroe", "UL Monroe", "ULM"],
    "mississippi": ["Mississippi", "Ole Miss"],
    "southern mississippi": ["Southern Mississippi", "Southern Miss"],
}

EXACT_ACTION_MODEL_NAMES = {
    "la monroe": "UL-Monroe",
    "louisiana monroe": "UL-Monroe",
    "mississippi": "Ole Miss",
    "southern mississippi": "Southern Miss",
}

def resolve_action_team(value, model_keys):
    """Resolve an Action team label to the exact key used by the playoff model."""
    raw = str(value or "").strip()
    raw_key = re.sub(r"[^a-z0-9]+", " ", raw.lower()).strip()

    # These three names must bypass canonical_team(), which converts them back
    # to different canonical labels than the playoff model actually uses.
    exact = EXACT_ACTION_MODEL_NAMES.get(raw_key)
    if exact and exact in model_keys:
        return exact

    normalized = normalize_action_team(raw)

    # Some Action labels are first normalized to the site's broader canonical
    # names, while the playoff model retains the shorter display names.
    normalized_exact = {
        "Mississippi": "Ole Miss",
        "Southern Mississippi": "Southern Miss",
        "Louisiana-Monroe": "UL-Monroe",
    }.get(normalized)
    if normalized_exact and normalized_exact in model_keys:
        return normalized_exact

    if normalized in model_keys:
        return normalized

    candidates = ACTION_MODEL_CANDIDATES.get(raw_key, [])
    for candidate in candidates:
        if candidate in model_keys:
            return candidate
        canonical = canonical_team(candidate)
        if canonical in model_keys:
            return canonical

    # Last-resort punctuation-insensitive comparison against model keys.
    compact = re.sub(r"[^a-z0-9]+", "", normalized.lower())
    for model_key in model_keys:
        if re.sub(r"[^a-z0-9]+", "", str(model_key).lower()) == compact:
            return model_key

    return normalized

def load_playoff_markets():
    """Load model probabilities plus normalized executable Action Network prices."""
    model_path = ROOT / "data/site/playoff_model_2026.json"
    model = json.loads(model_path.read_text()) if model_path.exists() else {"teams": []}
    by_team = {canonical_team(x.get("team")): x for x in model.get("teams", [])}

    prices = {"make_cfp": {}, "national_title": {}}
    metadata = {
        "source": "Action Network",
        "status": "unavailable",
        "pulled_at": None,
        "age_hours": None,
        "books": [],
        "pull_succeeded": False,
    }
    raw_counts = {"make_cfp": 0, "national_title": 0}
    invalid_prices = 0
    skipped_incomplete_offers = 0
    repeated_offer_rows = 0
    unmatched_market_teams = set()
    seen_rows = set()

    if not ACTION_PATH.exists():
        return by_team, prices, metadata, {
            "raw_offer_counts": raw_counts,
            "invalid_prices": invalid_prices,
            "skipped_incomplete_offers": skipped_incomplete_offers,
            "repeated_offer_rows": repeated_offer_rows,
            "unmatched_market_teams": sorted(unmatched_market_teams),
        }

    payload = json.loads(ACTION_PATH.read_text())
    pulled_at = payload.get("pulled_at")
    hours = age_hours(pulled_at)
    metadata = {
        "source": payload.get("source") or "Action Network",
        "status": (
            "current" if payload.get("pull_succeeded") and hours is not None and hours <= 26
            else "stale" if pulled_at
            else "unavailable"
        ),
        "pulled_at": pulled_at,
        "age_hours": round(hours, 2) if hours is not None else None,
        "books": payload.get("represented_books") or [],
        "pull_succeeded": bool(payload.get("pull_succeeded")),
    }

    book_names = payload.get("books", {})
    represented = set(metadata["books"])

    for market_key, market in payload.get("markets", {}).items():
        names = {
            str(x.get("id")): resolve_action_team(
                x.get("display_name") or x.get("location") or x.get("full_name"),
                by_team,
            )
            for x in market.get("teams", [])
        }
        options = market.get("rules", {}).get("options", {})
        for book in market.get("books", []):
            bid = str(book.get("book_id"))
            bname = book_names.get(bid) or f"Book {bid}"
            if bname.lower() == "consensus":
                continue
            represented.add(bname)
            for odd in book.get("odds", []):
                team = names.get(str(odd.get("team_id")))
                price = number(odd.get("money"))
                option = options.get(str(odd.get("option_type_id")), {}).get("option_type")
                if market_key == "make_cfp" and option not in (None, "Yes"):
                    continue
                if not team or price is None:
                    skipped_incomplete_offers += 1
                    continue
                if team not in by_team:
                    unmatched_market_teams.add(team)
                if price == 0 or price < -1000000 or price > 1000000:
                    invalid_prices += 1
                    continue

                raw_counts[market_key] = raw_counts.get(market_key, 0) + 1
                row_key = (market_key, team, bname, option or "Win", price)
                if row_key in seen_rows:
                    repeated_offer_rows += 1
                seen_rows.add(row_key)

                target = prices.setdefault(market_key, {})
                if team not in target or price > target[team]["price"]:
                    target[team] = {
                        "price": price,
                        "book": bname,
                        "market_prob": implied(price),
                        "option": option or "Win",
                    }

    selected_books = sorted({
        offer.get("book")
        for market_prices in prices.values()
        for offer in market_prices.values()
        if offer.get("book")
    })
    metadata["books"] = selected_books
    return by_team, prices, metadata, {
        "raw_offer_counts": raw_counts,
        "invalid_prices": invalid_prices,
        "skipped_incomplete_offers": skipped_incomplete_offers,
        "repeated_offer_rows": repeated_offer_rows,
        "unmatched_market_teams": sorted(unmatched_market_teams),
    }

def build_qa(rows, metadata, raw_qa):
    probability_fields = (
        "playoff_market_prob", "national_title_market_prob", "title_market_prob"
    )
    invalid_probabilities = sum(
        1
        for row in rows
        for field in probability_fields
        if row.get(field) is not None and not (0 <= row[field] <= 1)
    )
    make_cfp_coverage = sum(row["playoff_price"] is not None for row in rows)
    national_title_coverage = sum(row["national_title_price"] is not None for row in rows)
    conference_title_coverage = sum(row["title_price"] is not None for row in rows)
    win_total_coverage = sum(row["market_win_total"] is not None for row in rows)

    warnings = []
    if metadata["status"] != "current":
        warnings.append("Action Network playoff futures pull is stale or unavailable.")
    if not metadata["books"]:
        warnings.append("No sportsbook names were represented in the Action Network payload.")
    if make_cfp_coverage == 0:
        warnings.append("No Make CFP market prices were matched to site teams.")
    if national_title_coverage == 0:
        warnings.append("No national-title market prices were matched to site teams.")
    if raw_qa["invalid_prices"]:
        warnings.append(f'{raw_qa["invalid_prices"]} invalid raw prices were rejected.')
    if invalid_probabilities:
        warnings.append(f"{invalid_probabilities} implied probabilities were outside 0–100%.")
    if raw_qa.get("unmatched_market_teams"):
        warnings.append(
            f'{len(raw_qa["unmatched_market_teams"])} Action Network team names did not match the site model.'
        )
    # Repeated raw rows are informational because Action Network can return
    # multiple records for the same team/book/price. The normalization step
    # deliberately collapses them to one best executable offer.

    status = "pass" if not warnings else "warn"
    return {
        "schema_version": "futures-market-qa-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source": metadata["source"],
        "last_successful_pull": metadata["pulled_at"],
        "age_hours": metadata["age_hours"],
        "books": metadata["books"],
        "coverage": {
            "teams": len(rows),
            "win_totals": win_total_coverage,
            "conference_titles": conference_title_coverage,
            "make_cfp": make_cfp_coverage,
            "national_title": national_title_coverage,
        },
        "raw_offer_counts": raw_qa["raw_offer_counts"],
        "invalid_prices": raw_qa["invalid_prices"],
        "invalid_implied_probabilities": invalid_probabilities,
        "skipped_incomplete_offers": raw_qa["skipped_incomplete_offers"],
        "repeated_offer_rows": raw_qa["repeated_offer_rows"],
        "unmatched_market_teams": raw_qa.get("unmatched_market_teams", []),
        "duplicate_offers": 0,
        "warnings": warnings,
    }

def read_csv_rows(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def build_weekly_team_ratings(master_path, history_path):
    """Return authentic weekly snapshots of the official four-source composite."""
    master = read_csv_rows(master_path)
    current = {
        canonical_team(row.get("team")): number(row.get("power_rating"))
        for row in master
        if row.get("team")
    }
    current_date = max(
        (str(row.get("rating_date")) for row in master if row.get("rating_date")),
        default=None,
    )
    by_date = {}
    for row in read_csv_rows(history_path):
        day = str(row.get("snapshot_date") or "")
        source = str(row.get("source") or "")
        if not day or source not in {"SP+", "FPI", "TeamRankings", "Sagarin Rating"}:
            continue
        rating = number(row.get("rating"))
        team = canonical_team(row.get("team"))
        if rating is not None and team:
            by_date.setdefault(day, {}).setdefault(team, {})[source] = rating

    composites = {}
    for day, teams_for_day in by_date.items():
        sagarin = [sources["Sagarin Rating"] for sources in teams_for_day.values() if "Sagarin Rating" in sources]
        if not sagarin:
            continue
        sagarin_mean = sum(sagarin) / len(sagarin)
        for team, sources in teams_for_day.items():
            if not all(source in sources for source in ("SP+", "FPI", "TeamRankings", "Sagarin Rating")):
                continue
            composites.setdefault(team, {})[day] = (
                sources["SP+"] + sources["FPI"] + sources["TeamRankings"]
                + sources["Sagarin Rating"] - sagarin_mean
            ) / 4.0

    output = {}
    for team, values in composites.items():
        weekly = {}
        for day, value in values.items():
            parsed = datetime.fromisoformat(day).date()
            cycle = parsed.isocalendar()[:2]
            if cycle not in weekly or day > weekly[cycle]["date"]:
                weekly[cycle] = {"date": day, "rating": value}
        history = [weekly[cycle] for cycle in sorted(weekly)]
        if current_date and team in current:
            history = [point for point in history if point["date"] != current_date]
            history.append({"date": current_date, "rating": current[team]})
        prior = history[-2] if len(history) >= 2 else None
        output[team] = {
            "current": current.get(team),
            "current_date": current_date,
            "prior": prior.get("rating") if prior else None,
            "prior_date": prior.get("date") if prior else None,
            "delta": numeric_delta(current.get(team), prior.get("rating") if prior else None),
            "history": history,
        }
    return output


def freshness(timestamp, source, books=None, current_hours=26):
    hours = age_hours(timestamp)
    return {
        "source": source,
        "status": (
            "current"
            if timestamp and hours is not None and hours <= current_hours
            else "stale" if timestamp
            else "unavailable"
        ),
        "pulled_at": timestamp,
        "age_hours": round(hours, 2) if hours is not None else None,
        "books": sorted(set(books or [])),
    }


def observed_date_freshness(observed_date, source, books=None, current_days=1):
    if not observed_date:
        return {
            "source": source,
            "status": "unavailable",
            "observed_date": None,
            "age_days": None,
            "books": sorted(set(books or [])),
        }

    try:
        observed = datetime.fromisoformat(str(observed_date)).date()
        today = datetime.now(timezone.utc).date()
        age_days = max(0, (today - observed).days)
    except ValueError:
        return {
            "source": source,
            "status": "unavailable",
            "observed_date": observed_date,
            "age_days": None,
            "books": sorted(set(books or [])),
        }

    return {
        "source": source,
        "status": "current" if age_days <= current_days else "stale",
        "observed_date": observed_date,
        "age_days": age_days,
        "books": sorted(set(books or [])),
    }


def main():
    required = (
        MARKET_CONTRACT_PATH,
        SEASON_MODEL_PATH,
        PLAYOFF_MODEL_PATH,
    )
    missing = [str(x) for x in required if not x.exists()]
    if missing:
        raise SystemExit(
            "Missing Futures canonical inputs: " + ", ".join(missing)
        )

    market_contract = json.loads(MARKET_CONTRACT_PATH.read_text())
    season_model = json.loads(SEASON_MODEL_PATH.read_text())
    playoff_model_payload = json.loads(PLAYOFF_MODEL_PATH.read_text())
    schedule = json.loads(SCHEDULE_PATH.read_text()) if SCHEDULE_PATH.exists() else {"games": []}
    results = json.loads(RESULTS_PATH.read_text()) if RESULTS_PATH.exists() else {"games": []}
    preseason_db = json.loads(PRESEASON_DB_PATH.read_text()) if PRESEASON_DB_PATH.exists() else {"games": []}
    weekly_ratings = build_weekly_team_ratings(RATINGS_MASTER_PATH, RATINGS_HISTORY_PATH)

    teams = {
        canonical_team(x.get("team")): x
        for x in season_model.get("teams", [])
    }
    projection_rows = read_csv_rows(PROJECTION_BLEND_PATH)
    schedule_index, team_schedule_game_ids = build_schedule_index(
        schedule.get("games", []), projection_rows, set(teams)
    )
    regular_weeks = [
        int(game.get("week"))
        for game in schedule.get("games", [])
        if game.get("week") is not None
        and str(game.get("season_type") or "regular").lower() == "regular"
        and ({canonical_team(game.get("away_team")), canonical_team(game.get("home_team"))} & set(teams))
    ]
    final_regular_week = max(regular_weeks, default=15)

    playoff_model = {
        canonical_team(x.get("team")): x
        for x in playoff_model_payload.get("teams", [])
    }

    bets = (
        json.loads(BETS_PATH.read_text()).get("records", [])
        if BETS_PATH.exists()
        else []
    )
    open_futures = [
        x for x in bets
        if x.get("is_open")
        and x.get("market") in {"Win Total", "Conference Future"}
    ]

    win_market = {
        canonical_team(x.get("team")): x
        for x in market_contract.get("win_totals", {}).get("rows", [])
    }

    title_market = {
        canonical_team(x.get("team")): x
        for x in market_contract.get("conference_titles", {}).get("rows", [])
    }

    cfp_market = {
        canonical_team(x.get("team")): x
        for x in market_contract.get("make_cfp", {}).get("rows", [])
        if x.get("outcome") == "Yes"
    }

    national_market = {
        canonical_team(x.get("team")): x
        for x in market_contract.get("national_title", {}).get("rows", [])
        if x.get("outcome") == "Yes"
    }

    movement = {}
    for x in read_csv_rows(WIN_MOVEMENT_PATH):
        movement[(canonical_team(x.get("team")), x.get("book"))] = x

    title_movement = {}
    for x in read_csv_rows(TITLE_MOVEMENT_PATH):
        title_movement[(canonical_team(x.get("team")), x.get("book"))] = x

    build_generated_at = datetime.now(timezone.utc).isoformat()

    checkpoint_history = load_futures_checkpoints(
        FUTURES_CHECKPOINTS_PATH
    )

    baseline_checkpoint, weekly_baseline = select_weekly_baseline(
        checkpoint_history,
        schedule.get("games", []),
        build_generated_at,
        set(teams),
    )

    records = {key: {"wins": 0, "losses": 0, "conf_wins": 0, "conf_losses": 0} for key in teams}
    conference_by_game = {str(game.get("game_id")): bool(game.get("is_conference_game")) for game in preseason_db.get("games", [])}
    for game in results.get("games", []):
        if not game.get("completed"):
            continue
        away, home = canonical_team(game.get("away_team")), canonical_team(game.get("home_team"))
        ap, hp = number(game.get("away_score")), number(game.get("home_score"))
        if ap is None or hp is None or away not in records or home not in records or ap == hp:
            continue
        winner, loser = (away, home) if ap > hp else (home, away)
        records[winner]["wins"] += 1; records[loser]["losses"] += 1
        if conference_by_game.get(str(game.get("game_id")), False):
            records[winner]["conf_wins"] += 1; records[loser]["conf_losses"] += 1

    baseline_rows = {
        canonical_team(x.get("team")): x
        for x in (
            baseline_checkpoint.get("rows", [])
            if baseline_checkpoint
            else []
        )
        if isinstance(x, dict) and x.get("team")
    }
    current_dt = parse_dt(build_generated_at)
    prior_candidates = []
    for checkpoint in checkpoint_history:
        checkpoint_at = parse_dt(checkpoint.get("checkpoint_at") or checkpoint.get("source_view_built_at"))
        if checkpoint_at and current_dt and checkpoint_at.date() < current_dt.date() and checkpoint.get("rows"):
            prior_candidates.append((checkpoint_at, checkpoint))
    daily_checkpoint = max(prior_candidates, key=lambda item: item[0])[1] if prior_candidates else None
    daily_rows = {canonical_team(x.get("team")): x for x in (daily_checkpoint or {}).get("rows", []) if isinstance(x, dict) and x.get("team")}

    rows = []

    for key, team in teams.items():
        win = win_market.get(key, {})
        title = title_market.get(key, {})
        playoff = playoff_model.get(key, {})
        cfp = cfp_market.get(key, {})
        national = national_market.get(key, {})
        rating = weekly_ratings.get(key, {})

        projected_wins = number(team.get("avg_total_wins"))
        title_prob = number(team.get("conference_title_pct"))

        reference_total = number(win.get("reference_number"))

        direction = (
            "Over"
            if projected_wins is not None
            and reference_total is not None
            and projected_wins >= reference_total
            else "Under"
        )

        win_offer = (
            win.get("best_over")
            if direction == "Over"
            else win.get("best_under")
        ) or {}

        total = number(win_offer.get("number"))
        if total is None:
            total = reference_total

        price = (
            win_offer.get("over_price")
            if direction == "Over"
            else win_offer.get("under_price")
        )
        book_name = win_offer.get("book")

        title_price = title.get("best_executable_price")
        title_book = title.get("best_executable_book")
        title_market_prob = implied(title_price)

        cfp_price = cfp.get("best_executable_price")
        cfp_book = cfp.get("best_executable_book")
        cfp_prob = implied(cfp_price)

        national_price = national.get("best_executable_price")
        national_book = national.get("best_executable_book")
        national_prob = implied(national_price)

        playoff_prob = number(playoff.get("playoff_pct"))
        national_model_prob = number(playoff.get("national_title_pct"))

        team_bets = [
            b for b in open_futures
            if canonical_team(b.get("team")) == key
        ]

        rows.append({
            "team": team.get("team"),
            "slug": team.get("slug"),
            "conference": team.get("conference"),
            "rank": team.get("rank"),
            "record": records.get(key),
            "team_rating": rating.get("current"),
            "team_rating_date": rating.get("current_date"),
            "team_rating_prior_week": rating.get("prior"),
            "team_rating_prior_week_date": rating.get("prior_date"),
            "team_rating_delta_week": rating.get("delta"),
            "team_rating_history": rating.get("history", []),
            "schedule_game_ids": team_schedule_game_ids.get(key, []),

            "projected_wins": projected_wins,
            "market_win_total": total,
            "win_edge": (
                projected_wins - total
                if projected_wins is not None and total is not None
                else None
            ),
            "win_direction": direction,
            "win_price": price,
            "win_book": book_name,

            "title_model_prob": title_prob,
            "title_market_prob": title_market_prob,
            "title_edge": (
                title_prob - title_market_prob
                if title_prob is not None and title_market_prob is not None
                else None
            ),
            "title_price": title_price,
            "title_book": title_book,

            "playoff_model_prob": playoff_prob,
            "playoff_market_prob": cfp_prob,
            "playoff_edge": (
                playoff_prob - cfp_prob
                if playoff_prob is not None and cfp_prob is not None
                else None
            ),
            "playoff_price": cfp_price,
            "playoff_book": cfp_book,

            "quarterfinal_model_prob": number(
                playoff.get("quarterfinal_pct")
            ),
            "semifinal_model_prob": number(
                playoff.get("semifinal_pct")
            ),
            "national_title_game_model_prob": number(
                playoff.get("national_title_game_pct")
            ),
            "national_title_model_prob": national_model_prob,
            "national_title_market_prob": national_prob,
            "national_title_edge": (
                national_model_prob - national_prob
                if national_model_prob is not None
                and national_prob is not None
                else None
            ),
            "national_title_price": national_price,
            "national_title_book": national_book,

            "win_movement": movement.get((key, book_name)),
            "title_movement": title_movement.get((key, title_book)),
            "open_wagers": team_bets,

            # Backward-compatible field used by the current Futures UI.
            "last_updated": (
                win.get("last_observed_date")
                or title.get("last_observed_date")
                or market_contract.get("built_at")
            ),

            # New quote-breadth metadata for later UI work.
            "win_books": win.get("executable_books", []),
            "win_book_count": win.get("executable_book_count", 0),
            "title_books": title.get("executable_books", []),
            "title_book_count": title.get("executable_book_count", 0),
            "playoff_books": cfp.get("executable_books", []),
            "playoff_book_count": cfp.get("executable_book_count", 0),
            "national_title_books": national.get("executable_books", []),
            "national_title_book_count": national.get(
                "executable_book_count", 0
            ),
            "win_quotes": win.get("quotes", {}),
            "title_quotes": title.get("quotes", {}),
            "playoff_quotes": cfp.get("quotes", {}),
            "national_title_quotes": national.get("quotes", {}),

            "delta_week": (
                {
                    "baseline_date": baseline_checkpoint.get(
                        "checkpoint_date"
                    ),
                    "baseline_at": baseline_checkpoint.get(
                        "checkpoint_at"
                    ),

                    "win": {
                        "model": numeric_delta(
                            projected_wins,
                            baseline_rows.get(key, {}).get(
                                "projected_wins"
                            ),
                        ),
                        "market": numeric_delta(
                            total,
                            baseline_rows.get(key, {}).get(
                                "market_win_total"
                            ),
                        ),
                        "edge": numeric_delta(
                            (
                                projected_wins - total
                                if projected_wins is not None
                                and total is not None
                                else None
                            ),
                            baseline_rows.get(key, {}).get(
                                "win_edge"
                            ),
                        ),
                    },

                    "conference_title": {
                        "model": numeric_delta(
                            title_prob,
                            baseline_rows.get(key, {}).get(
                                "title_model_prob"
                            ),
                        ),
                        "market": numeric_delta(
                            title_market_prob,
                            baseline_rows.get(key, {}).get(
                                "title_market_prob"
                            ),
                        ),
                        "edge": numeric_delta(
                            (
                                title_prob - title_market_prob
                                if title_prob is not None
                                and title_market_prob is not None
                                else None
                            ),
                            baseline_rows.get(key, {}).get(
                                "title_edge"
                            ),
                        ),
                    },

                    "make_cfp": {
                        "model": numeric_delta(
                            playoff_prob,
                            baseline_rows.get(key, {}).get(
                                "playoff_model_prob"
                            ),
                        ),
                        "market": numeric_delta(
                            cfp_prob,
                            baseline_rows.get(key, {}).get(
                                "playoff_market_prob"
                            ),
                        ),
                        "edge": numeric_delta(
                            (
                                playoff_prob - cfp_prob
                                if playoff_prob is not None
                                and cfp_prob is not None
                                else None
                            ),
                            baseline_rows.get(key, {}).get(
                                "playoff_edge"
                            ),
                        ),
                    },

                    "national_title": {
                        "model": numeric_delta(
                            national_model_prob,
                            baseline_rows.get(key, {}).get(
                                "national_title_model_prob"
                            ),
                        ),
                        "market": numeric_delta(
                            national_prob,
                            baseline_rows.get(key, {}).get(
                                "national_title_market_prob"
                            ),
                        ),
                        "edge": numeric_delta(
                            (
                                national_model_prob - national_prob
                                if national_model_prob is not None
                                and national_prob is not None
                                else None
                            ),
                            baseline_rows.get(key, {}).get(
                                "national_title_edge"
                            ),
                        ),
                    },
                }
                if baseline_checkpoint
                else None
            ),
        })

        # Temporary compatibility for consumers that have not migrated yet.
        rows[-1]["delta_7d"] = rows[-1]["delta_week"]

        current_row = rows[-1]
        prior_row = daily_rows.get(key, {})
        current_row["delta_day"] = ({
            "baseline_date": daily_checkpoint.get("checkpoint_date"),
            "baseline_at": daily_checkpoint.get("checkpoint_at"),
            "win": {field: numeric_delta(current_row.get(source), prior_row.get(source)) for field, source in {"model":"projected_wins", "market":"market_win_total", "edge":"win_edge"}.items()},
            "conference_title": {field: numeric_delta(current_row.get(source), prior_row.get(source)) for field, source in {"model":"title_model_prob", "market":"title_market_prob", "edge":"title_edge"}.items()},
            "make_cfp": {field: numeric_delta(current_row.get(source), prior_row.get(source)) for field, source in {"model":"playoff_model_prob", "market":"playoff_market_prob", "edge":"playoff_edge"}.items()},
            "national_title": {field: numeric_delta(current_row.get(source), prior_row.get(source)) for field, source in {"model":"national_title_model_prob", "market":"national_title_market_prob", "edge":"national_title_edge"}.items()},
        } if daily_checkpoint else None)

        history = []
        for checkpoint in checkpoint_history:
            historical = next((x for x in checkpoint.get("rows", []) if canonical_team(x.get("team")) == key), None)
            if not historical:
                continue
            history.append({
                "checkpoint_date": checkpoint.get("checkpoint_date"), "checkpoint_at": checkpoint.get("checkpoint_at"),
                "model_projected_wins": historical.get("projected_wins"), "market_win_total": historical.get("market_win_total"), "win_edge": historical.get("win_edge"), "win_book": historical.get("win_book"),
                "conference_title_model_prob": historical.get("title_model_prob"), "conference_title_market_prob": historical.get("title_market_prob"), "conference_title_edge": historical.get("title_edge"), "conference_title_book": historical.get("title_book"),
                "cfp_model_prob": historical.get("playoff_model_prob"), "cfp_market_prob": historical.get("playoff_market_prob"), "cfp_edge": historical.get("playoff_edge"), "cfp_book": historical.get("playoff_book"),
                "national_title_model_prob": historical.get("national_title_model_prob"), "national_title_market_prob": historical.get("national_title_market_prob"), "national_title_edge": historical.get("national_title_edge"), "national_title_book": historical.get("national_title_book"),
            })
        current_row["history"] = history

    season_built = season_model.get("built_at")
    playoff_built = playoff_model_payload.get("built_at")

    win_date = market_contract.get(
        "win_totals", {}
    ).get("last_observed_date")

    title_date = market_contract.get(
        "conference_titles", {}
    ).get("last_observed_date")

    playoff_pulled = market_contract.get(
        "make_cfp", {}
    ).get("pulled_at")

    national_pulled = market_contract.get(
        "national_title", {}
    ).get("pulled_at")

    win_books = {
        b
        for x in market_contract.get("win_totals", {}).get("rows", [])
        for b in x.get("executable_books", [])
    }

    title_books = {
        b
        for x in market_contract.get(
            "conference_titles", {}
        ).get("rows", [])
        for b in x.get("executable_books", [])
    }

    cfp_books = {
        b
        for x in market_contract.get("make_cfp", {}).get("rows", [])
        for b in x.get("executable_books", [])
    }

    national_books = {
        b
        for x in market_contract.get(
            "national_title", {}
        ).get("rows", [])
        for b in x.get("executable_books", [])
    }

    # Current CSVs retain a daily observation date rather than an exact
    # acquisition timestamp, so report that distinction explicitly instead
    # of manufacturing a precise pull time.
    win_market_meta = observed_date_freshness(
        win_date,
        market_contract.get("win_totals", {}).get("source"),
        win_books,
    )

    title_market_meta = observed_date_freshness(
        title_date,
        market_contract.get(
            "conference_titles", {}
        ).get("source"),
        title_books,
    )

    playoff_market_meta = freshness(
        playoff_pulled,
        market_contract.get("make_cfp", {}).get("source")
        or "Action Network",
        cfp_books,
    )

    national_market_meta = freshness(
        national_pulled,
        market_contract.get("national_title", {}).get("source")
        or "Action Network",
        national_books,
    )

    warnings = []

    if not win_date:
        warnings.append("Win-total market data unavailable.")
    if not title_date:
        warnings.append("Conference-title market data unavailable.")
    if playoff_market_meta["status"] != "current":
        warnings.append("Make-CFP market data is stale or unavailable.")
    if national_market_meta["status"] != "current":
        warnings.append("National-title market data is stale or unavailable.")

    unmatched = market_contract.get("audit", {}).get("unmatched", {})
    if any(unmatched.get(k) for k in unmatched):
        warnings.append("One or more futures market team identities were unmatched.")

    reliability = {}
    if RELIABILITY_AUDIT_PATH.exists():
        reliability = json.loads(RELIABILITY_AUDIT_PATH.read_text())
        warnings.extend(
            warning for warning in reliability.get("warnings", [])
            if warning not in warnings
        )

    qa = {
        "schema_version": "futures-market-qa-v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not warnings else "warn",
        "market_domains": {
            "win_totals": win_market_meta,
            "conference_titles": title_market_meta,
            "make_cfp": playoff_market_meta,
            "national_title": national_market_meta,
        },
        "coverage": {
            "teams": len(rows),
            "win_totals": sum(
                x["market_win_total"] is not None for x in rows
            ),
            "conference_titles": sum(
                x["title_price"] is not None for x in rows
            ),
            "make_cfp": sum(
                x["playoff_price"] is not None for x in rows
            ),
            "national_title": sum(
                x["national_title_price"] is not None for x in rows
            ),
        },
        "unmatched_market_teams": unmatched,
        "reliability_audit": {
            "status": reliability.get("status"),
            "generated_at": reliability.get("generated_at"),
        },
        "warnings": warnings,
    }

    QA_PATH.parent.mkdir(parents=True, exist_ok=True)
    QA_PATH.write_text(json.dumps(qa, indent=2) + "\n")

    payload = {
        "schema_version": "futures-view-v5",
        "built_at": build_generated_at,

        # Backward compatibility for current UI.
        "model_updated": season_built,

        "model_freshness": {
            "season_simulation": {
                "built_at": season_built,
                "trials": season_model.get("trials"),
                "schema_version": season_model.get("schema_version"),
                "simulation_model": season_model.get("simulation_model"),
            },
            "playoff_simulation": {
                "built_at": playoff_built,
                "trials": playoff_model_payload.get("trials"),
                "schema_version": playoff_model_payload.get("schema_version"),
            },
        },

        "market_freshness": {
            # New domain-specific authority.
            "win_totals": win_market_meta,
            "conference_titles": title_market_meta,
            "make_cfp": playoff_market_meta,
            "national_title": national_market_meta,

            # Backward compatibility until futures_v2.html is updated.
            "playoff_futures": playoff_market_meta,
            "win_and_conference_futures": {
                "source": "Canonical current futures market contract",
                "status": (
                    "current"
                    if win_date and title_date
                    else "unavailable"
                ),
                "pulled_at": None,
                "observed_date": max(
                    x for x in (win_date, title_date) if x
                ) if (win_date or title_date) else None,
                "age_hours": None,
                "books": sorted(win_books | title_books),
            },
        },

        "market_qa": qa,
        "market_contract": {
            "schema_version": market_contract.get("schema_version"),
            "built_at": market_contract.get("built_at"),
            "approved_executable_books": market_contract.get(
                "market_policy", {}
            ).get("approved_executable_books", []),
        },

        "weekly_baseline": weekly_baseline,
        "history_axis": {
            "labels": ["W0", "Pre-W1"] + [f"W{week}" for week in range(1, final_regular_week + 1)],
            "final_regular_week": final_regular_week,
            "current_week": (weekly_baseline.get("prior_week") or 0) + 1,
            "missing_value_policy": "gap_null_never_zero_or_interpolated",
        },
        "schedule_contract": {
            "schema_version": "futures-schedule-index-v1",
            "source": str(SCHEDULE_PATH.relative_to(DATA_ROOT)),
            "projection_source": str(PROJECTION_BLEND_PATH.relative_to(DATA_ROOT)),
            "win_probability_model": "logistic_margin_scale_6_5_v1",
            "completed_games": "canonical_final_score_frozen",
            "team_reference_field": "schedule_game_ids",
            "perspective_policy": "browser_derives_team_view_from_shared_game",
        },

        "schedule_games": schedule_index,

        "rows": rows,

        "summary": {
            "teams": len(rows),
            "win_markets": sum(
                x["market_win_total"] is not None for x in rows
            ),
            "title_markets": sum(
                x["title_price"] is not None for x in rows
            ),
            "playoff_markets": sum(
                x["playoff_price"] is not None for x in rows
            ),
            "national_title_markets": sum(
                x["national_title_price"] is not None for x in rows
            ),
            "open_wagers": len(open_futures),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, separators=(",", ":")) + "\n"
    )

    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
