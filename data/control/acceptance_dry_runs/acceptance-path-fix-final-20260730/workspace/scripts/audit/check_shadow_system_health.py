#!/usr/bin/env python3
"""Read-only operational health summary for the production Shadow system."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    "components": ROOT / "data/site/saturday_shadow_component_predictions.json",
    "lines": ROOT / "data/site/saturday_shadow_lines.json",
    "schedule": ROOT / "data/site/schedule_live_enrichment.json",
    "matchups": ROOT / "data/site/matchups_view.json",
    "audit": ROOT / "data/audits/saturday_shadow_production_integration.json",
}


def load_json(path: Path):
    return json.loads(path.read_text())


def main() -> None:
    parsed, errors = {}, {}
    for name, path in FILES.items():
        try:
            parsed[name] = load_json(path)
        except Exception as exc:
            errors[name] = str(exc)

    components = parsed.get("components", {}).get("games", [])
    lines = parsed.get("lines", {}).get("games", [])
    schedule = parsed.get("schedule", {}).get("games", [])
    matchups = parsed.get("matchups", {}).get("games", [])
    season = parsed.get("components", {}).get("season") or 2026
    upcoming = sum(not bool((r.get("game") or {}).get("completed")) for r in matchups)
    completed = sum(bool((r.get("game") or {}).get("completed")) for r in matchups)

    reasons = Counter()
    for row in components:
        if row.get("shadow_display_ready") is not True:
            reason = row.get("shadow_activation_reason") or "unknown"
            if reason == "required_inputs_unavailable":
                missing = row.get("shadow_missing_reasons") or [reason]
                reasons.update(missing)
            else:
                reasons[reason] += 1

    schedule_by_id = {str(r.get("game_id")): r for r in schedule}
    mismatches = 0
    for row in lines:
        other = schedule_by_id.get(str(row.get("game_id")))
        if not other:
            continue
        pairs = (
            (row.get("saturday_shadow_spread"), other.get("next_projection_spread")),
            (row.get("saturday_shadow_total"), other.get("next_projection_total")),
            (row.get("spread_value_tier"), other.get("spread_value_tier")),
            (row.get("total_value_tier"), other.get("total_value_tier")),
            (row.get("shadow_display_ready"), other.get("shadow_display_ready")),
        )
        mismatches += any(a != b for a, b in pairs)

    snapshot = "unavailable"
    rating_path = ROOT / "data/ratings/market_implied_ratings_latest.csv"
    try:
        ratings = pd.read_csv(rating_path, low_memory=False)
        for col in ("snapshot_time", "generated_at", "source_updated_at", "snapshot_date"):
            if col in ratings and ratings[col].notna().any():
                snapshot = str(ratings[col].dropna().max())
                break
    except Exception:
        pass

    public_files = ["openers.html", "schedule.html", "ratings.html"]
    public_dir = ROOT / "build/public_site"
    public_status = "ready" if all((public_dir / name).exists() for name in public_files) else "missing or incomplete"
    audit = parsed.get("audit", {})
    fixture_contamination = sum(bool(r.get("fixture_only")) for r in components + lines + schedule)

    print("SHADOW SYSTEM HEALTH")
    print(f"season: {season}")
    print(f"latest market-rating snapshot: {snapshot}")
    print(f"upcoming games: {upcoming}")
    print(f"completed games found: {completed}")
    print(f"games awaiting updates: {sum(r.get('shadow_activation_reason') == 'awaiting_completed_game' for r in components)}")
    print(f"active Shadow spread: {sum(r.get('shadow_spread') is not None for r in components)}")
    print(f"active Shadow total: {sum(r.get('shadow_total') is not None for r in components)}")
    print("unavailable by reason: " + (", ".join(f"{k}={v}" for k, v in reasons.most_common()) or "none"))
    print(f"JSON parse status: {'PASS' if not errors else 'FAIL ' + str(errors)}")
    print(f"Openers/Schedule mismatch count: {mismatches}")
    print(f"fixture contamination count: {fixture_contamination}")
    print(f"latest integration audit: {audit.get('status', 'not run')}")
    print(f"local public build: {public_status}")


if __name__ == "__main__":
    main()
