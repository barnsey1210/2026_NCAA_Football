#!/usr/bin/env python3
"""Fail closed on silently stale Betting/Futures derived pages."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("NCAAF_RUNTIME_ROOT") or Path(__file__).resolve().parents[2])
OUT = ROOT / "data/site/derived_page_status.json"


def load(relative: str) -> dict:
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"missing freshness input: {relative}")
    return json.loads(path.read_text())


def stamp(payload: dict, *fields: str):
    for field in fields:
        value = payload.get(field)
        if not value:
            continue
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            pass
    return None


def main() -> None:
    results = load("data/canonical/game_results_2026.json")
    betting = load("data/site/betting_activity_view.json")
    season = load("data/site/season_simulations_2026.json")
    playoff = load("data/site/playoff_model_2026.json")
    markets = load("data/markets/current_futures_market_2026.json")
    futures = load("data/site/futures_view.json")
    reliability = load("data/audits/futures_market_reliability.json")

    errors = []
    betting_built = stamp(betting, "built_at")
    results_built = stamp(results, "generated_at", "built_at")
    if not betting_built or not results_built or betting_built < results_built:
        errors.append("Betting dashboard predates canonical results")

    completed_weeks = [
        int(game.get("week"))
        for game in results.get("games", [])
        if game.get("completed") and game.get("week") is not None
    ]
    latest_completed_week = max(completed_weeks, default=None)
    represented_weeks = {
        int(row.get("week"))
        for row in betting.get("records", [])
        if row.get("week") not in (None, "")
    }
    latest_betting_week = max(represented_weeks, default=None)
    if latest_completed_week is not None and (
        latest_betting_week is None or latest_betting_week < latest_completed_week
    ):
        errors.append(
            f"Betting latest represented week {latest_betting_week} trails completed week {latest_completed_week}"
        )

    reliability_status = str(reliability.get("status") or "").lower()
    futures_built = stamp(futures, "built_at")
    futures_inputs = [
        stamp(season, "built_at"),
        stamp(playoff, "built_at"),
        stamp(markets, "built_at", "generated_at"),
    ]
    futures_stale = (
        not futures_built
        or any(value is None for value in futures_inputs)
        or any(value > futures_built for value in futures_inputs if value is not None)
    )
    if reliability_status == "fail":
        futures_state = "DEGRADED_PRIOR_ACCEPTED_ARTIFACT_PRESERVED"
    elif futures_stale:
        futures_state = "FAILED_STALE_DERIVED_VIEW"
        errors.append("Futures view predates an accepted simulation or market input")
    else:
        futures_state = "CURRENT"

    payload = {
        "schema_version": "derived-page-status-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "FAIL" if errors else "DEGRADED" if reliability_status == "fail" else "PASS",
        "betting": {
            "status": "FAIL" if any("Betting" in item for item in errors) else "CURRENT",
            "built_at": betting.get("built_at"),
            "results_generated_at": results.get("generated_at") or results.get("built_at"),
            "latest_completed_week": latest_completed_week,
            "latest_represented_week": latest_betting_week,
        },
        "futures": {
            "status": futures_state,
            "built_at": futures.get("built_at"),
            "season_simulation_built_at": season.get("built_at"),
            "playoff_simulation_built_at": playoff.get("built_at"),
            "market_contract_built_at": markets.get("built_at") or markets.get("generated_at"),
            "market_reliability_status": reliability.get("status"),
            "market_reliability_errors": reliability.get("errors", []),
        },
        "errors": errors,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(OUT)
    print(json.dumps(payload, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
