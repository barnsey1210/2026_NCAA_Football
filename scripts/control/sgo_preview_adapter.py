#!/usr/bin/env python3
"""Run-scoped SportsGameOdds preview and provider-free replay adapter.

This module is audit-only: it writes private raw/staging/observation artifacts and
never mutates accepted odds, public JSON, HTML, or publication repositories.
"""
from __future__ import annotations

import argparse, csv, hashlib, io, json, os, re, tempfile, unicodedata, urllib.parse, urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from scripts.lib.ncaaf_config import canonical_team, is_neutral_site

ROOT = Path(__file__).resolve().parents[2]
ENDPOINT = "https://api.sportsgameodds.com/v2/events"
SUPPORTED_BOOKS = {"draftkings", "fanduel", "betmgm", "caesars", "bovada"}
MARKETS = {
    "points-away-game-sp-away": ("spread", "away", "spread"),
    "points-home-game-sp-home": ("spread", "home", "spread"),
    "points-all-game-ou-over": ("total", "over", "overUnder"),
    "points-all-game-ou-under": ("total", "under", "overUnder"),
    "points-away-game-ml-away": ("moneyline", "away", "odds"),
    "points-home-game-ml-home": ("moneyline", "home", "odds"),
}
ET = ZoneInfo("America/New_York")
SGO_TEAM_ALIASES = {
    "UMass": "Massachusetts", "Arkansas-Pine Bluff Golden Lions": "UAPB",
    "San José State": "San Jose State", "UCF": "Central Florida", "Miami": "Miami-FL",
    "Long Island University": "LIU", "Southeast Missouri State": "Southeast Missouri",
    "Furman Paladins": "Furman", "Norfolk State Spartans": "Norfolk State",
    "Houston Christian": "HCU", "Jerry Rice Team": "Rice", "SE Louisiana": "Southeastern La.",
    "Northwestern State Demons": "Northwestern State", "Hampton Pirates": "Hampton",
    "Mississippi Valley State Delta Devils": "MVSU", "Charleston Southern": "Charleston So.",
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def num(value):
    try:
        return float(str(value).replace("+", ""))
    except (TypeError, ValueError):
        return None


def integer(value):
    try:
        return int(float(str(value).replace("+", "")))
    except (TypeError, ValueError):
        return None


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def team(event, side):
    return (((event.get("teams") or {}).get(side) or {}).get("names") or {}).get("long")


def events(payload):
    value = payload.get("data", []) if isinstance(payload, dict) else payload
    return value if isinstance(value, list) else []


def norm_team(value):
    value = canonical_team(SGO_TEAM_ALIASES.get(str(value or ""), value))
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def atomic(path: Path, text: str, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        os.write(fd, text.encode())
        os.close(fd)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        Path(tmp).unlink(missing_ok=True)
        raise


def csv_text(rows, fieldnames=None):
    rows = list(rows)
    fields = fieldnames or (list(rows[0]) if rows else [])
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def load_canonical(root=ROOT):
    path = root / "data/site/matchups_view.json"
    payload = json.loads(path.read_text())
    games = []
    for item in payload.get("games", []):
        game = dict(item.get("game") or {})
        teams = item.get("teams") or {}
        game["away_team"] = canonical_team(game.get("away_team"))
        game["home_team"] = canonical_team(game.get("home_team"))
        game["neutral_site"] = is_neutral_site(game)
        game["away_classification"] = "FBS" if (teams.get("away") or {}).get("overall_rank") is not None else "FCS"
        game["home_classification"] = "FBS" if (teams.get("home") or {}).get("overall_rank") is not None else "FCS"
        games.append(game)
    return games


def resolve_canonical_week(canonical_games, as_of):
    """Return nearest canonical week with a game on/after the ET calendar date."""
    dt = parse_dt(as_of) if isinstance(as_of, str) else as_of
    if dt is None:
        dt = datetime.now(timezone.utc)
    today = dt.astimezone(ET).date()
    candidates = []
    for game in canonical_games:
        try:
            game_date = date.fromisoformat(str(game.get("date"))[:10])
            week = int(game.get("week"))
        except (TypeError, ValueError):
            continue
        if game_date >= today:
            candidates.append((game_date, week))
    return min(candidates)[1] if candidates else None


def map_events(payload, canonical_games):
    index = defaultdict(list)
    for game in canonical_games:
        index[(norm_team(game.get("away_team")), norm_team(game.get("home_team")))].append(game)
    mapped, excluded = [], []
    for event in events(payload):
        if event.get("leagueID") not in (None, "NCAAF"):
            excluded.append({"event_id": event.get("eventID"), "reason": "non_ncaaf"})
            continue
        away_raw, home_raw = team(event, "away"), team(event, "home")
        away = canonical_team(SGO_TEAM_ALIASES.get(str(away_raw or ""), away_raw))
        home = canonical_team(SGO_TEAM_ALIASES.get(str(home_raw or ""), home_raw))
        candidates = index.get((norm_team(away), norm_team(home)), [])
        start = parse_dt((event.get("status") or {}).get("startsAt"))
        event_date = start.astimezone(ET).date() if start else None
        exact = [g for g in candidates if event_date and str(g.get("date"))[:10] == event_date.isoformat()]
        if len(exact) == 1:
            mapped.append((event, exact[0]))
        elif len(candidates) == 1 and (event_date is None or abs((date.fromisoformat(str(candidates[0].get("date"))[:10]) - event_date).days) <= 1):
            mapped.append((event, candidates[0]))
        else:
            excluded.append({
                "event_id": event.get("eventID"), "away_team": away, "home_team": home,
                "start_time_utc": start.isoformat() if start else None,
                "reason": "ambiguous" if len(exact) > 1 else "unmatched",
                "candidate_count": len(exact or candidates),
            })
    return mapped, excluded


def quote_identity(row):
    fields = ("provider", "provider_event_id", "sportsbook", "market", "side", "line", "price",
              "available", "suspended", "provider_last_updated_at")
    raw = "|".join(str(row.get(k)) for k in fields)
    return hashlib.sha256(raw.encode()).hexdigest()


def extract_quotes(event, game, pulled_at, run_id, stale_hours=None):
    rows = []
    status = event.get("status") or {}
    for market_key, (market_name, side, value_key) in MARKETS.items():
        market = ((event.get("odds") or {}).get(market_key) or {})
        market_suspended = bool(market.get("cancelled") or market.get("ended") or status.get("cancelled"))
        for book, quote in (market.get("byBookmaker") or {}).items():
            if book not in SUPPORTED_BOOKS or not isinstance(quote, dict):
                continue
            value = num(quote.get(value_key))
            price = integer(quote.get("odds"))
            updated = quote.get("lastUpdatedAt")
            updated_dt, pulled_dt = parse_dt(updated), parse_dt(pulled_at)
            age = (pulled_dt - updated_dt).total_seconds() / 3600 if updated_dt and pulled_dt else None
            stale = age > stale_hours if age is not None and stale_hours is not None else None
            row = {
                "provider": "sports_game_odds", "run_id": run_id,
                "provider_event_id": event.get("eventID"), "canonical_game_id": game.get("game_id"),
                "canonical_cfbd_game_id": game.get("cfbd_game_id"), "canonical_week": game.get("week"),
                "provider_week": (event.get("info") or {}).get("seasonWeek"),
                "away_team": game.get("away_team"), "home_team": game.get("home_team"),
                "sportsbook": book, "market": market_name, "side": side,
                "line": value if market_name != "moneyline" else None,
                "price": price if market_name != "moneyline" else (integer(quote.get("odds")) if price is not None else None),
                "available": bool(quote.get("available")), "suspended": market_suspended,
                "provider_last_updated_at": updated, "opening_line": num(quote.get("open" + value_key[:1].upper() + value_key[1:])),
                "opening_price": integer(quote.get("openOdds")), "ingested_at": pulled_at,
                "quote_age_hours": round(age, 4) if age is not None else None,
                "stale_threshold_hours": stale_hours, "stale": stale,
            }
            row.update({"market_available": row["available"], "market_suspended": row["suspended"],
                        "selected_book": book, "market_last_updated_at": updated,
                        "quote_age": row["quote_age_hours"], "stale_flag": stale})
            if market_name == "moneyline":
                row["line"] = None
            row["quote_id"] = quote_identity(row)
            rows.append(row)
    return rows


def load_accepted(root=ROOT):
    path = root / "data/odds/season_game_lines_2026.csv"
    if not path.exists():
        return {}
    with path.open(newline="") as handle:
        return {str(row.get("game_id")): row for row in csv.DictReader(handle)}


def normalize_book(value):
    key = re.sub(r"[^a-z0-9]", "", str(value or "").lower())
    return {"draftkings": "draftkings", "fanduel": "fanduel", "betmgm": "betmgm",
            "caesars": "caesars", "bovada": "bovada"}.get(key)


def eligible_quote(row):
    return bool(row.get("available")) and not bool(row.get("suspended")) and row.get("stale") is not True


def paired(quotes, market_name, book, sides):
    candidates = {(q["side"]): q for q in quotes if q["market"] == market_name and q["sportsbook"] == book and eligible_quote(q)}
    if not all(side in candidates for side in sides):
        return None
    pair = [candidates[side] for side in sides]
    if market_name == "spread":
        if any(q.get("line") is None for q in pair) or abs(sum(float(q["line"]) for q in pair)) > 0.01:
            return None
    if market_name == "total":
        if any(q.get("line") is None for q in pair) or len({float(q["line"]) for q in pair}) != 1:
            return None
    return {q["side"]: q for q in pair}


def comparison_row(game, quotes, old):
    row = {
        "canonical_game_id": game.get("game_id"), "canonical_cfbd_game_id": game.get("cfbd_game_id"),
        "season": 2026, "week": game.get("week"), "date": game.get("date"),
        "away_team": game.get("away_team"), "home_team": game.get("home_team"),
        "neutral_site": game.get("neutral_site"), "away_classification": game.get("away_classification"),
        "home_classification": game.get("home_classification"),
    }
    if not old:
        row.update({f"{m}_comparison_status": "no_accepted_game" for m in ("spread", "total", "moneyline")})
        return row
    spread_book = normalize_book(old.get("market_spread_book"))
    total_book = normalize_book(old.get("market_total_book"))
    moneyline_book = spread_book or total_book
    selections = {
        "spread": (spread_book, paired(quotes, "spread", spread_book, ("away", "home")) if spread_book else None),
        "total": (total_book, paired(quotes, "total", total_book, ("over", "under")) if total_book else None),
        "moneyline": (moneyline_book, paired(quotes, "moneyline", moneyline_book, ("away", "home")) if moneyline_book else None),
    }
    for market_name, (book, pair) in selections.items():
        row[f"{market_name}_comparison_book"] = book
        if not pair:
            row[f"{market_name}_comparison_status"] = "same_book_pair_unavailable"
            continue
        row[f"{market_name}_comparison_status"] = "comparable"
        if market_name == "spread":
            current, previous = pair["home"]["line"], num(old.get("market_spread_home"))
            if previous is None:
                row[f"{market_name}_comparison_status"] = "accepted_value_missing"
            row.update({"previous_home_spread": previous, "staged_home_spread": current,
                        "home_spread_change": current - previous if previous is not None else None,
                        "staged_away_spread": pair["away"]["line"],
                        "staged_home_spread_price": pair["home"]["price"], "staged_away_spread_price": pair["away"]["price"],
                        "spread_source_timestamp": pair["home"]["provider_last_updated_at"],
                        "spread_available": pair["home"]["available"] and pair["away"]["available"],
                        "spread_stale": pair["home"]["stale"] is True or pair["away"]["stale"] is True})
        elif market_name == "total":
            current, previous = pair["over"]["line"], num(old.get("market_total"))
            if previous is None:
                row[f"{market_name}_comparison_status"] = "accepted_value_missing"
            row.update({"previous_total": previous, "staged_total": current,
                        "total_change": current - previous if previous is not None else None,
                        "staged_over_price": pair["over"]["price"], "staged_under_price": pair["under"]["price"],
                        "total_source_timestamp": pair["over"]["provider_last_updated_at"],
                        "total_available": pair["over"]["available"] and pair["under"]["available"],
                        "total_stale": pair["over"]["stale"] is True or pair["under"]["stale"] is True})
        else:
            previous_values = [num(old.get(f"{side}_moneyline")) for side in ("away", "home")]
            if any(value is None for value in previous_values):
                row[f"{market_name}_comparison_status"] = "accepted_value_missing"
            for side in ("away", "home"):
                current, previous = pair[side]["price"], num(old.get(f"{side}_moneyline"))
                row[f"previous_{side}_moneyline"] = previous
                row[f"staged_{side}_moneyline"] = current
                row[f"staged_{side}_moneyline_price"] = pair[side]["price"]
                row[f"{side}_moneyline_change"] = current - previous if previous is not None else None
            row["moneyline_source_timestamp"] = pair["home"]["provider_last_updated_at"]
            row["moneyline_available"] = pair["away"]["available"] and pair["home"]["available"]
            row["moneyline_stale"] = pair["away"]["stale"] is True or pair["home"]["stale"] is True
    return row


def merge_audit_ledger(path, quotes):
    existing = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                existing[row["quote_id"]] = row
    before = len(existing)
    for row in quotes:
        existing.setdefault(row["quote_id"], row)
    atomic(path, "".join(json.dumps(existing[key], sort_keys=True, separators=(",", ":")) + "\n" for key in sorted(existing)))
    return len(existing) - before, len(existing)


def process_payload(payload, pulled_at, run_id, root=ROOT, stale_hours=24.0, requested_week="current", replay_source=None, page_count=1, external_calls=None):
    canonical = load_canonical(root)
    mapped, excluded = map_events(payload, canonical)
    # Acceptance scope is all upcoming mapped canonical games, not the UI-selected week.
    # requested_week/resolved_week are retained as display/provenance metadata only.
    resolved_week = resolve_canonical_week(canonical, pulled_at) if requested_week == "current" else int(requested_week)
    pulled_dt = parse_dt(pulled_at) or datetime.now(timezone.utc)
    as_of_et = pulled_dt.astimezone(ET).date()

    def is_upcoming(game):
        try:
            return date.fromisoformat(str(game.get("date"))[:10]) >= as_of_et
        except (TypeError, ValueError):
            return False

    staged_pairs = [(event, game) for event, game in mapped if is_upcoming(game)]
    quotes = [q for event, game in staged_pairs for q in extract_quotes(event, game, pulled_at, run_id, stale_hours)]
    accepted = load_accepted(root)
    composites = []
    for event, game in staged_pairs:
        game_quotes = [q for q in quotes if q["canonical_game_id"] == game.get("game_id")]
        composites.append(comparison_row(game, game_quotes, accepted.get(str(game.get("cfbd_game_id")))))

    stage = root / "data/control/staging" / run_id
    observation_dir = root / "data/control/observations/sports_game_odds"
    quote_fields = list(quotes[0]) if quotes else ["quote_id", "provider", "run_id"]
    atomic(stage / "quote_observations.csv", csv_text(quotes, quote_fields))
    composite_fields = sorted({key for row in composites for key in row})
    atomic(stage / "normalized.csv", csv_text(composites, composite_fields))
    atomic(observation_dir / f"{run_id}.jsonl", "".join(json.dumps(q, sort_keys=True, separators=(",", ":")) + "\n" for q in quotes))
    added, ledger_total = merge_audit_ledger(observation_dir / "quote_observations.jsonl", quotes)

    statuses = Counter()
    changes = Counter()
    changed_games = set()
    spread_moves, total_moves = [], []
    for row in composites:
        for market_name in ("spread", "total", "moneyline"):
            statuses[f"{market_name}:{row.get(f'{market_name}_comparison_status')}"] += 1
        for market_name, key in (("spread", "home_spread_change"), ("total", "total_change")):
            if row.get(key) not in (None, 0, 0.0):
                changes[market_name] += 1
                changed_games.add(row["canonical_game_id"])
                (spread_moves if market_name == "spread" else total_moves).append({
                    "canonical_game_id": row["canonical_game_id"],
                    "game": f"{row['away_team']} at {row['home_team']}",
                    "book": row.get(f"{market_name}_comparison_book"), "change": row[key],
                })
        if any(row.get(f"{side}_moneyline_change") not in (None, 0, 0.0) for side in ("away", "home")):
            changes["moneyline"] += 1
            changed_games.add(row["canonical_game_id"])
    provider_weeks = Counter(str((event.get("info") or {}).get("seasonWeek")) for event in events(payload))
    canonical_weeks = Counter(str(game.get("week")) for _, game in mapped)
    book_counts = Counter(q["sportsbook"] for q in quotes)
    market_counts = Counter(q["market"] for q in quotes)
    unavailable = sum(not q["available"] for q in quotes)
    suspended = sum(bool(q["suspended"]) for q in quotes)
    stale = sum(q["stale"] is True for q in quotes)
    reasons = Counter(item["reason"] for item in excluded)
    staged_dates = sorted(str(game.get("date"))[:10] for _, game in staged_pairs)
    classifications = Counter()
    for _, game in staged_pairs:
        a, h = game["away_classification"], game["home_classification"]
        classifications["fbs_vs_fbs" if a == h == "FBS" else "fcs_vs_fcs" if a == h == "FCS" else "fcs_vs_fbs"] += 1
    # Provider coverage is evaluated across every upcoming canonical FBS-vs-FBS
    # event returned and mapped by SGO. Games without an active SGO event are
    # reported separately; they do not cause a complete provider fetch to fail.
    schedule_upcoming_ids = {
        str(g.get("game_id")) for g in canonical
        if is_upcoming(g)
    }
    mapped_ids = {
        str(g.get("game_id")) for _, g in staged_pairs
        if is_upcoming(g)
    }
    expected_ids = set(mapped_ids)
    schedule_without_sgo_ids = sorted(schedule_upcoming_ids - mapped_ids)
    missing_ids = sorted(expected_ids - mapped_ids)
    remaining_cursor = bool(payload.get("nextCursor"))
    complete = not remaining_cursor and reasons["ambiguous"] == 0
    manifest = {
        "run_id": run_id, "provider": "sports_game_odds", "pulled_at": pulled_at,
        "mode": "provider_free_replay" if replay_source else "live_preview",
        "replay_source_run_id": replay_source,
        "external_calls": (0 if replay_source else 1) if external_calls is None else external_calls,
        "estimated_api_cost": (0 if replay_source else 1) if external_calls is None else external_calls,
        "actual_api_cost": None,
        "request_success": True,
        "requested_week": requested_week, "resolved_canonical_week": resolved_week,
        "acceptance_scope": "all_upcoming_mapped_canonical_games",
        "display_default_week_only": resolved_week,
        "provider_week_is_authoritative": False, "events_in_archived_page": len(events(payload)),
        "page_count": page_count, "coverage_status": "COMPLETE" if complete else "PARTIAL",
        "archive_page_coverage": "complete_bounded_fetch" if complete else "partial_bounded_fetch",
        "next_cursor_present": remaining_cursor,
        "pagination_design": "Live preview follows nextCursor up to an explicit maximum page/request budget and blocks acceptance if a cursor remains.",
        "expected_canonical_games": len(expected_ids), "expected_canonical_game_ids": sorted(expected_ids),
        "mapped_canonical_games": len(mapped_ids), "mapped_canonical_game_ids": sorted(mapped_ids),
        "missing_canonical_games": len(missing_ids), "missing_canonical_game_ids": missing_ids,
        "upcoming_schedule_fbs_games": len(schedule_upcoming_ids),
        "upcoming_schedule_fbs_game_ids": sorted(schedule_upcoming_ids),
        "upcoming_schedule_without_sgo_event": len(schedule_without_sgo_ids),
        "upcoming_schedule_without_sgo_event_ids": schedule_without_sgo_ids,
        "acceptance_eligibility": complete and False,
        "acceptance_block_reason": "preview-only; acceptance disabled" if complete else "partial pagination or ambiguous event mapping",
        "provider_week_counts": dict(provider_weeks), "canonical_week_counts_mapped": dict(canonical_weeks),
        "events_mapped": len(mapped), "events_unmatched_or_excluded": len(excluded),
        "events_unmatched": reasons["unmatched"], "events_ambiguous": reasons["ambiguous"],
        "events_excluded": sum(value for key, value in reasons.items() if key not in {"unmatched", "ambiguous"}),
        "events_staged_for_canonical_week": len(staged_pairs),
        "games_returned": len(events(payload)), "books_returned": sorted(book_counts),
        "new_observations": added,
        "selected_week_date_range": [staged_dates[0], staged_dates[-1]] if staged_dates else [],
        "upcoming_date_range": [staged_dates[0], staged_dates[-1]] if staged_dates else [],
        "canonical_weeks_staged": sorted({int(g.get("week")) for _, g in staged_pairs if g.get("week") is not None}),
        "fbs_vs_fbs_staged": classifications["fbs_vs_fbs"], "fbs_vs_fcs_staged": classifications["fcs_vs_fbs"],
        "fcs_vs_fcs_staged": classifications["fcs_vs_fcs"],
        "neutral_site_games_staged": sum(bool(g.get("neutral_site")) for _, g in staged_pairs),
        "excluded_events": excluded, "supported_books": sorted(SUPPORTED_BOOKS),
        "quote_observations_retained": len(quotes), "quote_observations_added_to_audit_ledger": added,
        "quote_audit_ledger_total": ledger_total, "composite_games_staged": len(composites),
        "populated_market_components": dict(market_counts), "quote_rows_by_sportsbook": dict(book_counts),
        "unavailable_quote_rows": unavailable, "suspended_quote_rows": suspended, "stale_quote_rows": stale,
        "stale_threshold_hours": stale_hours,
        "stale_threshold_rationale": "Explicit/configurable quote-age gate; stale quotes are never eligible for current display.",
        "comparison_method": "same accepted display sportsbook, paired sides, current-to-current only",
        "accepted_display_book_priority": "DraftKings then Bovada (build_season_game_lines_2026.py); replay does not redefine it",
        "missing_book_behavior": "comparison unavailable; no newer-book substitution",
        "consensus_and_best_price_behavior": "separate quote-level observations; not used for canonical movement",
        "comparison_status_counts": dict(statuses), "games_changed": len(changed_games),
        "spreads_changed": changes["spread"], "totals_changed": changes["total"], "moneylines_changed": changes["moneyline"],
        "original_preview_counts": {"games_changed": 39, "spreads_changed": 29, "totals_changed": 14, "moneylines_changed": 7},
        "largest_valid_same_book_spread_changes": sorted(spread_moves, key=lambda row: abs(row["change"]), reverse=True)[:10],
        "largest_valid_same_book_total_changes": sorted(total_moves, key=lambda row: abs(row["change"]), reverse=True)[:10],
        "files_that_would_change_in_acceptance": ["data/odds/season_game_lines_2026.csv", "canonical per-book market history", "derived V2 market JSON after validation"],
        "accepted_state_modified": False, "publication": "SKIPPED", "v2_structural_hashes": "unchanged",
        "raw_retention": "archived response replayed; quote observations remain audit-only",
        "observation_ledger": str((observation_dir / f"{run_id}.jsonl").relative_to(root)),
        "shared_deduplicated_ledger": str((observation_dir / "quote_observations.jsonl").relative_to(root)),
        "acceptance_dry_run_design": "A future provider-free command may copy same-book comparable staged values into a temporary accepted-data clone, run canonical builders/audits, diff outputs, and stop before promotion/publication.",
    }
    atomic(stage / "manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    atomic(stage / "mapping.json", json.dumps({"mapped": [{"provider_event_id": e.get("eventID"), "canonical_game_id": g.get("game_id"), "canonical_week": g.get("week"), "away_team": g.get("away_team"), "home_team": g.get("home_team")} for e, g in mapped], "excluded": excluded}, indent=2, sort_keys=True) + "\n")
    summary = f"""# Corrected SGO provider-free replay

- REPLAY_SOURCE_RUN_ID: {replay_source or 'n/a'}
- NETWORK_CALLS: {manifest['external_calls']}
- COVERAGE: {manifest['coverage_status']} ({manifest['page_count']} archived page(s); nextCursor={manifest['next_cursor_present']})
- ACCEPTANCE: SKIPPED
- PUBLICATION: SKIPPED
- Raw events: {manifest['events_in_archived_page']}
- Canonical week: {resolved_week} ({' to '.join(manifest['selected_week_date_range']) if manifest['selected_week_date_range'] else 'no remaining games'})
- Mapped / unmatched / ambiguous / excluded: {manifest['events_mapped']} / {manifest['events_unmatched']} / {manifest['events_ambiguous']} / {manifest['events_excluded']}
- Staged FBS-FBS / FCS-FBS / FCS-FCS / neutral: {manifest['fbs_vs_fbs_staged']} / {manifest['fbs_vs_fcs_staged']} / {manifest['fcs_vs_fcs_staged']} / {manifest['neutral_site_games_staged']}
- Quote observations: {manifest['quote_observations_retained']} (unavailable {unavailable}, suspended {suspended}, stale {stale})
- Corrected changes: games {manifest['games_changed']}, spreads {manifest['spreads_changed']}, totals {manifest['totals_changed']}, moneylines {manifest['moneylines_changed']}
- Original changes: games 39, spreads 29, totals 14, moneylines 7

The material count reduction is intentional: the original preview merged SGO provider Weeks 0/1 into 91 rows, matched only exact lowercase team pairs, and selected the freshest quote across books before comparing it to a DraftKings/Bovada-priority accepted row. The corrected replay stages only canonical Week {resolved_week}, preserves all supported quote rows, and counts movement only when a complete paired quote exists for the accepted row's same display sportsbook. Missing accepted values are not counted as movements.

The response is sufficient to correct and test normalization for the events retained on its first page. It is not sufficient to establish complete upcoming coverage because nextCursor was non-empty. A future production design should use bounded pagination with a declared maximum page/request budget, preflight cost, abort on budget exhaustion, a PARTIAL warning, and no acceptance when required coverage is incomplete. The existing one-request preview guarantee remains unchanged pending approval.
"""
    atomic(stage / "preview_summary.md", summary)
    return manifest


def capture(run_id, fixture=None, stale_hours=24.0, max_pages=5):
    pulled_at = utcnow()
    params = {"leagueID": "NCAAF", "oddsAvailable": "true", "includeAltLines": "false", "includeOpenCloseOdds": "true", "limit": "250"}
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    pages = []
    if fixture:
        text = fixture.read_text(errors="ignore")
        body = text.split("\r\n\r\n", 1)[-1].split("\n\n", 1)[-1]
        external_calls = 0
        pages = [json.loads(body)]
    else:
        key = os.environ.get("SGO_API_KEY")
        if not key:
            raise RuntimeError("SGO_API_KEY is not available to the runner")
        cursor = None
        seen_cursors = set()
        external_calls = 0
        for _page_number in range(1, max_pages + 1):
            page_params = dict(params)
            if cursor: page_params["cursor"] = cursor
            page_url = ENDPOINT + "?" + urllib.parse.urlencode(page_params)
            request = urllib.request.Request(page_url, headers={"Accept": "application/json", "X-API-Key": key, "User-Agent": "NCAAF-Control/2.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                page = json.loads(response.read().decode("utf-8"))
            pages.append(page); external_calls += 1
            cursor = page.get("nextCursor")
            if not cursor: break
            if cursor in seen_cursors: raise RuntimeError("SGO pagination returned a repeated cursor")
            seen_cursors.add(cursor)
        body = json.dumps(pages[-1] if pages else {})
    # Retain one combined raw response for replay while preserving every page.
    # Event IDs are stable; de-duplicate defensively if a page boundary repeats.
    combined_events = {}
    for page in pages:
        for event in events(page): combined_events[str(event.get("eventID"))] = event
    final_cursor = pages[-1].get("nextCursor") if pages else None
    payload = {"data": list(combined_events.values()), "nextCursor": final_cursor}
    raw_dir = ROOT / "data/control/raw/sports_game_odds" / run_id
    atomic(raw_dir / "response.json", json.dumps(payload, separators=(",", ":")) + "\n")
    for number, page in enumerate(pages, 1):
        atomic(raw_dir / f"response_page_{number:03d}.json", json.dumps(page, separators=(",", ":")) + "\n")
    atomic(raw_dir / "meta.json", json.dumps({"run_id": run_id, "provider": "sports_game_odds", "pulled_at": pulled_at, "endpoint": ENDPOINT, "query": params, "external_calls": external_calls, "max_pages": max_pages, "pages_fetched": len(pages), "remaining_cursor": bool(final_cursor), "accepted_state_modified": False, "publication": "SKIPPED"}, indent=2, sort_keys=True) + "\n")
    # Fixtures are provider-free and must never be counted as a live request.
    return process_payload(payload, pulled_at, run_id, ROOT, stale_hours, "current", "fixture" if fixture else None, len(pages), external_calls)


def replay(source_run_id, run_id, stale_hours=24.0):
    raw_dir = ROOT / "data/control/raw/sports_game_odds" / source_run_id
    payload = json.loads((raw_dir / "response.json").read_text())
    meta = json.loads((raw_dir / "meta.json").read_text())
    return process_payload(payload, meta["pulled_at"], run_id, ROOT, stale_hours, "current", source_run_id,
                           int(meta.get("pages_fetched", 1)), 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--replay-source-run-id")
    parser.add_argument("--stale-hours", type=float, default=24.0)
    args = parser.parse_args()
    result = replay(args.replay_source_run_id, args.run_id, args.stale_hours) if args.replay_source_run_id else capture(args.run_id, args.fixture, args.stale_hours)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
