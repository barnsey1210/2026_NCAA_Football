#!/usr/bin/env python3
"""Build the standalone Futures data contract and daily market QA artifact."""
from pathlib import Path
from datetime import datetime, timezone
import json, re, sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.lib.ncaaf_config import canonical_team

ACTION_PATH = ROOT / "data/markets/action/action_playoff_futures_2026.json"
QA_PATH = ROOT / "data/qa/futures_market_qa.json"
OUT = ROOT / "data/site/futures_view.json"

def number(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None

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

def main():
    html = (ROOT / "v1.html").read_text(encoding="utf-8")
    match = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        raise SystemExit("Embedded canonical database not found in v1.html")

    db = json.loads(match.group(1))
    teams = {canonical_team(x.get("team")): x for x in db.get("teams", [])}

    bets_path = ROOT / "data/site/betting_activity_view.json"
    bets = json.loads(bets_path.read_text()).get("records", []) if bets_path.exists() else []
    open_futures = [
        x for x in bets
        if x.get("is_open") and x.get("market") in {"Win Total", "Conference Future"}
    ]

    movement = {}
    for x in db.get("market_win_totals_movement", []):
        movement[(canonical_team(x.get("team")), x.get("book"))] = x

    title_movement = {}
    for x in db.get("market_conference_futures_movement", []):
        title_movement[(canonical_team(x.get("team")), x.get("book"))] = x

    playoff_model, playoff_prices, playoff_metadata, raw_qa = load_playoff_markets()

    merged_markets = {}
    for source in db.get("market_futures_best_prices", []):
        key = canonical_team(source.get("team"))
        target = merged_markets.setdefault(key, {})
        for field, value in source.items():
            if value not in (None, ""):
                target[field] = value

    rows = []
    # Build one Futures row for every tracked team, then attach market data when
    # available. Previously this loop iterated only market_futures_best_prices,
    # which silently omitted teams with no win-total/conference-title record.
    for key, team in teams.items():
        market = merged_markets.get(key, {})

        projected_wins = number(team.get("avg_total_wins"))
        title_prob = number(team.get("conference_title_pct"))
        total = number(market.get("market_win_total"))
        title_market = number(market.get("market_implied_title_prob"))
        direction = (
            "Over"
            if projected_wins is not None and total is not None and projected_wins >= total
            else "Under"
        )
        price = market.get("best_over_odds" if direction == "Over" else "best_under_odds")
        book_name = market.get("best_over_book" if direction == "Over" else "best_under_book")
        team_bets = [b for b in open_futures if canonical_team(b.get("team")) == key]

        playoff = playoff_model.get(key, {})
        nat_market = playoff_prices.get("national_title", {}).get(key, {})
        cfp_market = playoff_prices.get("make_cfp", {}).get(key, {})

        rows.append({
            "team": team.get("team"),
            "slug": team.get("slug"),
            "conference": team.get("conference"),
            "rank": team.get("rank"),
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
            "title_market_prob": title_market,
            "title_edge": (
                title_prob - title_market
                if title_prob is not None and title_market is not None
                else None
            ),
            "title_price": market.get("best_title_odds"),
            "title_book": market.get("best_title_book"),
            "playoff_model_prob": number(playoff.get("playoff_pct")),
            "playoff_market_prob": number(cfp_market.get("market_prob")),
            "playoff_edge": (
                number(playoff.get("playoff_pct")) - number(cfp_market.get("market_prob"))
                if number(playoff.get("playoff_pct")) is not None
                and number(cfp_market.get("market_prob")) is not None
                else None
            ),
            "playoff_price": cfp_market.get("price"),
            "playoff_book": cfp_market.get("book"),
            "quarterfinal_model_prob": number(playoff.get("quarterfinal_pct")),
            "semifinal_model_prob": number(playoff.get("semifinal_pct")),
            "national_title_game_model_prob": number(playoff.get("national_title_game_pct")),
            "national_title_model_prob": number(playoff.get("national_title_pct")),
            "national_title_market_prob": number(nat_market.get("market_prob")),
            "national_title_edge": (
                number(playoff.get("national_title_pct")) - number(nat_market.get("market_prob"))
                if number(playoff.get("national_title_pct")) is not None
                and number(nat_market.get("market_prob")) is not None
                else None
            ),
            "national_title_price": nat_market.get("price"),
            "national_title_book": nat_market.get("book"),
            "win_movement": movement.get((key, book_name)),
            "title_movement": title_movement.get(
                (key, market.get("best_title_book"))
            ),
            "open_wagers": team_bets,
            "last_updated": market.get("last_updated"),
        })

    qa = build_qa(rows, playoff_metadata, raw_qa)
    QA_PATH.parent.mkdir(parents=True, exist_ok=True)
    QA_PATH.write_text(json.dumps(qa, indent=2) + "\n")

    canonical_books = sorted({
        str(book)
        for row in rows
        for book in (row.get("win_book"), row.get("title_book"))
        if book
    })
    canonical_timestamps = [
        parse_dt(row.get("last_updated"))
        for row in rows
        if parse_dt(row.get("last_updated"))
    ]
    canonical_pulled_at = max(canonical_timestamps).isoformat() if canonical_timestamps else None

    payload = {
        "schema_version": "futures-view-v3",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "model_updated": db.get("meta", {}).get("generated_at"),
        "market_freshness": {
            "playoff_futures": playoff_metadata,
            "win_and_conference_futures": {
                "source": "Canonical futures market feed",
                "status": (
                    "current"
                    if canonical_pulled_at and (age_hours(canonical_pulled_at) or 999) <= 26
                    else "stale" if canonical_pulled_at
                    else "unavailable"
                ),
                "pulled_at": canonical_pulled_at,
                "age_hours": (
                    round(age_hours(canonical_pulled_at), 2)
                    if canonical_pulled_at and age_hours(canonical_pulled_at) is not None
                    else None
                ),
                "books": canonical_books,
            },
        },
        "market_qa": qa,
        "rows": rows,
        "summary": {
            "teams": len(rows),
            "win_markets": sum(x["market_win_total"] is not None for x in rows),
            "title_markets": sum(x["title_price"] is not None for x in rows),
            "playoff_markets": sum(x["playoff_price"] is not None for x in rows),
            "national_title_markets": sum(x["national_title_price"] is not None for x in rows),
            "open_wagers": len(open_futures),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    print(json.dumps(payload["summary"], indent=2))
    print(json.dumps({
        "market_qa": qa["status"],
        "source": qa["source"],
        "last_successful_pull": qa["last_successful_pull"],
        "books": qa["books"],
        "warnings": qa["warnings"],
    }, indent=2))
    print(OUT)
    print(QA_PATH)

if __name__ == "__main__":
    main()
