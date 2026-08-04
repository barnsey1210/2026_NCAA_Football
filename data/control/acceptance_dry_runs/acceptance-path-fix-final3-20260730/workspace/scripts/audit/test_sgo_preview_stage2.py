#!/usr/bin/env python3
"""Provider-free Stage 2 SGO mapping, normalization, replay, and safety tests."""
from __future__ import annotations

import csv, hashlib, json, os, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
sys.path.insert(0, str(ROOT))
import scripts.control.sgo_preview_adapter as adapter

shells = [*ROOT.glob("*_v2.html"), ROOT / "index.html", ROOT / "team.html", ROOT / "matchup.html"]
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
before = {str(path): digest(path) for path in shells}
failures = []


def check(condition, message):
    if not condition:
        failures.append(message)


def odd(value_key, value, price, updated, available=True, **extra):
    row = {value_key: value, "odds": price, "lastUpdatedAt": updated, "available": available}
    row.update(extra)
    return row


def event(event_id, week, starts, away="North Carolina", home="TCU", revised=False):
    current = -111 if revised else -110
    return {
        "leagueID": "NCAAF", "eventID": event_id,
        "status": {"startsAt": starts, "cancelled": False}, "info": {"seasonWeek": week},
        "teams": {"away": {"names": {"long": away}}, "home": {"names": {"long": home}}},
        "odds": {
            "points-away-game-sp-away": {"byBookmaker": {
                "draftkings": odd("spread", 6.5, current, "2026-07-30T03:49:00Z", openSpread=7),
                "fanduel": odd("spread", 7.5, -105, "2026-07-30T03:51:00Z")}},
            "points-home-game-sp-home": {"byBookmaker": {
                "draftkings": odd("spread", -6.5, -110, "2026-07-30T03:49:00Z", openSpread=-7),
                "fanduel": odd("spread", -7.5, -115, "2026-07-30T03:51:00Z")}},
            "points-all-game-ou-over": {"byBookmaker": {
                "bovada": odd("overUnder", 49.5, -108, "2026-07-30T03:48:00Z"),
                "draftkings": odd("overUnder", 50.5, -110, "2026-07-28T00:00:00Z")}},
            "points-all-game-ou-under": {"byBookmaker": {
                "bovada": odd("overUnder", 49.5, -112, "2026-07-30T03:48:00Z"),
                "draftkings": odd("overUnder", 50.5, -110, "2026-07-28T00:00:00Z")}},
            "points-away-game-ml-away": {"byBookmaker": {
                "draftkings": odd("odds", 205, 205, "2026-07-30T03:49:00Z"),
                "fanduel": odd("odds", 215, 215, "2026-07-30T03:51:00Z", available=False)}},
            "points-home-game-ml-home": {"byBookmaker": {
                "draftkings": odd("odds", -250, -250, "2026-07-30T03:49:00Z"),
                "fanduel": odd("odds", -260, -260, "2026-07-30T03:51:00Z")}},
        },
    }


def prepare(root):
    games = [
        {"game": {"game_id": "g1", "cfbd_game_id": 101, "week": 0, "date": "2026-08-29", "away_team": "North Carolina", "home_team": "TCU", "neutral_site": True},
         "teams": {"away": {"overall_rank": 20}, "home": {"overall_rank": 10}}},
        {"game": {"game_id": "g2", "cfbd_game_id": 102, "week": 1, "date": "2026-09-05", "away_team": "Miami-FL", "home_team": "Stanford", "neutral_site": False},
         "teams": {"away": {"overall_rank": 8}, "home": {"overall_rank": 50}}},
        {"game": {"game_id": "g3", "cfbd_game_id": 103, "week": 2, "date": "2026-09-12", "away_team": "FCS Example", "home_team": "TCU", "neutral_site": False},
         "teams": {"away": {"overall_rank": None}, "home": {"overall_rank": 10}}},
    ]
    path = root / "data/site/matchups_view.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"games": games}))
    accepted = root / "data/odds/season_game_lines_2026.csv"
    accepted.parent.mkdir(parents=True)
    with accepted.open("w", newline="") as handle:
        fields = ["game_id", "away_team", "home_team", "market_spread_home", "market_spread_book", "market_total", "market_total_book", "away_moneyline", "home_moneyline"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({"game_id": 101, "away_team": "North Carolina", "home_team": "TCU", "market_spread_home": -6.5, "market_spread_book": "DraftKings", "market_total": 49.5, "market_total_book": "Bovada", "away_moneyline": 205, "home_moneyline": -250})


payload = {"nextCursor": "partial", "data": [
    event("w0", "1", "2026-08-29T16:00:00Z"),
    event("w1", "1", "2026-09-05T19:30:00Z", "Miami-FL", "Stanford"),
    event("bad", "1", "2026-09-05T19:30:00Z", "Unknown", "Unknown State"),
]}

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    prepare(root)
    manifest = adapter.process_payload(payload, "2026-07-30T03:54:06Z", "replay-a", root, 24.0, "current", "source")
    check(manifest["external_calls"] == 0, "replay reported a provider call")
    check(manifest["resolved_canonical_week"] == 0, "provider Week 1 was trusted instead of canonical Week 0")
    check(manifest["events_mapped"] == 2 and manifest["events_unmatched_or_excluded"] == 1, "mapping counts incorrect")
    check(manifest["events_staged_for_canonical_week"] == 1, "multiweek response was not restricted to canonical current week")
    check(manifest["archive_page_coverage"] == "partial_first_page", "nextCursor partial coverage not reported")
    quotes = list(csv.DictReader((root / "data/control/staging/replay-a/quote_observations.csv").open()))
    check(len(quotes) == 12, "quote-level supported-book rows were collapsed or lost")
    check(any(q["available"] == "False" for q in quotes), "unavailable quote was not preserved for audit")
    check(any(q["stale"] == "True" for q in quotes), "stale quote was not flagged")
    rows = list(csv.DictReader((root / "data/control/staging/replay-a/normalized.csv").open()))
    check(rows[0].get("neutral_site") == "True", "canonical neutral-site value was not preserved")
    check(rows[0].get("spread_comparison_book") == "draftkings" and rows[0].get("staged_home_spread") == "-6.5", "same-book spread selection failed")
    check(rows[0].get("total_comparison_book") == "bovada" and rows[0].get("staged_total") == "49.5", "paired same-book total selection failed")
    check(rows[0].get("moneyline_comparison_book") == "draftkings", "same-book moneyline selection failed")
    first_total = manifest["quote_audit_ledger_total"]
    again = adapter.process_payload(payload, "2026-07-30T03:54:06Z", "replay-b", root, 24.0, "current", "source")
    check(again["quote_audit_ledger_total"] == first_total and again["quote_observations_added_to_audit_ledger"] == 0, "identical replay duplicated quote identities")
    revised_payload = json.loads(json.dumps(payload))
    revised_payload["data"][0] = event("w0", "1", "2026-08-29T16:00:00Z", revised=True)
    revised = adapter.process_payload(revised_payload, "2026-07-30T03:54:06Z", "replay-c", root, 24.0, "current", "source")
    check(revised["quote_audit_ledger_total"] == first_total + 1, "revised quote did not append as a new identity")
    canonical = adapter.load_canonical(root)
    check(adapter.resolve_canonical_week(canonical, datetime(2026, 8, 1, tzinfo=timezone.utc)) == 0, "pre-Week-0 resolution failed")
    check(adapter.resolve_canonical_week(canonical, datetime(2026, 8, 30, 12, tzinfo=timezone.utc)) == 1, "between Week 0 and Week 1 resolution failed")
    check(adapter.resolve_canonical_week(canonical, datetime(2026, 9, 5, 12, tzinfo=timezone.utc)) == 1, "during-week resolution failed")
    check(adapter.resolve_canonical_week(canonical, datetime(2027, 1, 1, tzinfo=timezone.utc)) is None, "no-remaining-games resolution failed")
    check(any(g["away_classification"] == "FCS" and g["home_classification"] == "FBS" for g in canonical), "FBS/FCS classification was not retained")
    # Ambiguous canonical candidates must be rejected, never silently selected.
    duplicate = list(canonical) + [dict(canonical[0], game_id="g1-duplicate")]
    mapped, excluded = adapter.map_events({"data": [payload["data"][0]]}, duplicate)
    check(not mapped and excluded[0]["reason"] == "ambiguous", "ambiguous canonical mapping was not rejected")
    # Suspended markets remain observable but cannot form a selected pair.
    suspended_event = event("suspended", "1", "2026-08-29T16:00:00Z")
    suspended_event["odds"]["points-home-game-sp-home"]["cancelled"] = True
    suspended_quotes = adapter.extract_quotes(suspended_event, canonical[0], "2026-07-30T03:54:06Z", "s", 24)
    check(any(q["suspended"] for q in suspended_quotes), "suspended quote was not retained and flagged")
    check(adapter.paired(suspended_quotes, "spread", "draftkings", ("away", "home")) is None, "suspended spread side was selected")

# Ensure the test itself never reaches the network.
original_open = adapter.urllib.request.urlopen
adapter.urllib.request.urlopen = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network forbidden"))
try:
    with tempfile.TemporaryDirectory() as td:
        adapter.ROOT = Path(td)
        prepare(adapter.ROOT)
        fixture = adapter.ROOT / "fixture.json"
        fixture.write_text(json.dumps(payload))
        preview = adapter.capture("fixture", fixture)
        check(preview["external_calls"] == 0, "fixture capture reported a provider call")
finally:
    adapter.ROOT = ROOT
    adapter.urllib.request.urlopen = original_open

ctl = ROOT / "scripts/control/run_data_refresh.py"
cases = [
    (["odds", "--execute", "--scope", "games", "--providers", "the_odds_api"], 1, "wrong provider"),
    (["odds", "--execute", "--scope", "games", "--providers", "sports_game_odds", "--confirm-publish"], 1, "confirm publish"),
    (["odds", "--dry-run", "--scope", "games", "--providers", "sports_game_odds", "--test-scenario", "cooldown_block"], 2, "cooldown"),
]
for args, expected, label in cases:
    result = subprocess.run([PY, str(ctl), *args], cwd=ROOT, text=True, capture_output=True, env={k: v for k, v in os.environ.items() if k != "SGO_API_KEY"})
    check(result.returncode == expected, f"{label} rejection returned {result.returncode}, expected {expected}")

after = {str(path): digest(path) for path in shells}
check(before == after, "V2 structural hashes changed")
print("Stage 2 SGO preview tests:", "FAILED" if failures else "PASSED")
print("- external provider calls: 0")
print("- canonical mapping/week, FBS classification, quote preservation: tested")
print("- unavailable, stale, same-book pairing, idempotent replay: tested")
print("- publication: no")
print("- V2 structural hashes unchanged:", before == after)
for failure in failures:
    print("ERROR:", failure)
raise SystemExit(bool(failures))
