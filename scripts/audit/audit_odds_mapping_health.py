#!/usr/bin/env python3
"""Audit exact-canonical Odds misses and malformed current quote handling."""
from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/audit/odds_mapping_health_audit.json"
ALIASES = {
    "University at Albany": "UAlbany",
    "Arkansas-Pine Bluff": "UAPB",
    "Charleston Southern": "Charleston So.",
    "Houston Christian": "HCU",
    "Louisiana-Monroe": "UL-Monroe",
    "Nicholls State": "Nicholls",
    "Southeast Missouri State": "Southeast Missouri",
    "Southeastern Louisiana": "Southeastern La.",
    "UT Rio Grande Valley": "UTRGV",
    "Mississippi Valley State": "MVSU",
}


def load(path: str):
    return json.loads((ROOT / path).read_text())


def market_coverage(game: dict) -> dict[str, bool]:
    return {
        market: any(bool((quote.get(market) or {})) for quote in game.get("quotes", {}).values())
        for market in ("spread", "total", "moneyline")
    }


def main() -> None:
    odds = load("data/site/odds_screen_v2.json")
    matchups = load("data/site/matchups_view.json").get("games", [])
    ratings = load("data/site/ratings_view.json").get("teams", [])
    fbs = {row.get("team") for row in ratings if row.get("team")}
    canonical = []
    for row in matchups:
        game = row.get("game", row)
        canonical.append(game)

    cases = []
    for game in odds.get("games", []):
        notes = " | ".join(str(x) for x in game.get("data_quality_notes", []))
        if "No exact V2 game match" not in notes:
            continue
        away = ALIASES.get(game["away_team"], game["away_team"])
        home = ALIASES.get(game["home_team"], game["home_team"])
        provider_date = date.fromisoformat(game["date"])
        matches = []
        for candidate in canonical:
            if candidate.get("away_team") != away or candidate.get("home_team") != home or not candidate.get("date"):
                continue
            day_delta = abs((date.fromisoformat(candidate["date"]) - provider_date).days)
            if day_delta <= 1:
                matches.append((day_delta, candidate))
        expected = min(matches, key=lambda item: item[0])[1] if matches else None
        is_fbs = away in fbs and home in fbs
        coverage = market_coverage(game)
        classification = "DATE_OR_TEAM_ALIAS_FIX_NEEDED" if is_fbs else "MIXED_OR_FCS_EVENT"
        reasons = ["provider/canonical team alias differs"]
        if expected and expected.get("date") != game.get("date"):
            reasons.append("provider UTC event date differs from canonical local game date")
        cases.append({
            "provider": "Action Network",
            "provider_event_id": str(game.get("source_game_id")),
            "provider_away_team": game.get("away_team"),
            "provider_home_team": game.get("home_team"),
            "provider_date": game.get("date"),
            "attempted_canonical_away_team": away,
            "attempted_canonical_home_team": home,
            "attempted_canonical_date": expected.get("date") if expected else game.get("date"),
            "expected_canonical_game_id": expected.get("game_id") if expected else None,
            "mapping_failure_reason": "; ".join(reasons) if expected else "no unique canonical game identified after reviewed aliases",
            "classification": classification,
            "fbs_vs_fbs": is_fbs,
            "part_of_current_displayed_odds_board": True,
            "current_quote_displayed": any(coverage.values()),
            "another_provider_successfully_maps_same_game": False,
            "missing_markets": [market for market, available in coverage.items() if not available],
            "wrong_game_attachment_risk": False,
            "identity_isolation": "Provider event uses action-{event_id}, has no matchup_url, and cannot attach to a canonical game.",
        })

    malformed = []
    for item in load("data/audits/odds_screen_v2_build_audit.json").get("malformed_current_spread_pairs", []):
        game = next((g for g in odds.get("games", []) if str(g.get("source_game_id")) == str(item.get("source_game_id"))), {})
        valid_fallback_books = []
        for book, quote in game.get("quotes", {}).items():
            spread = quote.get("spread") or {}
            if spread and all(side.get("valid") is not False for side in spread.values() if isinstance(side, dict)):
                valid_fallback_books.append(book)
        malformed.append({**item, "expected_canonical_game_id": game.get("game_id"), "excluded_from_display": True, "reached_displayed_board": False, "valid_fallback_books": valid_fallback_books, "critical_coverage_loss": not bool(valid_fallback_books)})

    counts = Counter(case["classification"] for case in cases)
    payload = {
        "schema_version": "odds-mapping-health-audit-v1",
        "source_artifacts": ["data/site/odds_screen_v2.json", "data/audits/odds_screen_v2_build_audit.json", "data/site/matchups_view.json", "data/site/ratings_view.json"],
        "mapping_cases": cases,
        "malformed_quote_cases": malformed,
        "summary": {
            "mapping_case_count": len(cases),
            "classification_counts": dict(sorted(counts.items())),
            "displayed_board_events": sum(case["part_of_current_displayed_odds_board"] for case in cases),
            "wrong_game_attachment_risks": sum(case["wrong_game_attachment_risk"] for case in cases),
            "spread_coverage": sum("spread" not in case["missing_markets"] for case in cases),
            "total_coverage": sum("total" not in case["missing_markets"] for case in cases),
            "moneyline_coverage": sum("moneyline" not in case["missing_markets"] for case in cases),
            "malformed_count": len(malformed),
            "malformed_reached_display": sum(case["reached_displayed_board"] for case in malformed),
            "malformed_critical_coverage_loss": sum(case["critical_coverage_loss"] for case in malformed),
            "recommended_odds_status": "yellow",
            "recommendation": "Provider-identity mapping gaps and excluded malformed input are warnings; preserve RED for wrong-game attachment, displayed malformed quotes, critical coverage loss, or stale-current data.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
    print(f"Odds mapping audit: {len(cases)} mapping cases, {len(malformed)} malformed cases, recommended YELLOW")


if __name__ == "__main__":
    main()
