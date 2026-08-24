#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DB = ROOT / "data/snapshots/preseason/preseason_db.json"
CONTRACT = ROOT / "data/site/current_game_projection_contract.json"
OUT = ROOT / "data/audits/projection_fbs_production_coverage.json"

STANDARD_SPREAD = "standard_spread_five_source_v1"
STANDARD_TOTAL = "standard_total_sp_massey_sagarin_v1"
DEGRADED_SPREAD = "standard_spread_degraded_v1"
DEGRADED_TOTAL = "standard_total_degraded_v1"


def main():
    db = json.loads(DB.read_text())
    contract = json.loads(CONTRACT.read_text())

    fbs = {
        str(row.get("team")).strip()
        for row in db.get("teams", [])
        if row.get("team")
    }

    production_games = [
        g for g in contract.get("games", [])
        if g.get("away_team") in fbs
        and g.get("home_team") in fbs
    ]

    def model_summary(model_id, degraded_model_id):
        statuses = Counter(
            g["projections"][model_id]["availability_status"]
            for g in production_games
        )

        degraded_statuses = Counter(
            g["projections"][degraded_model_id]["availability_status"]
            for g in production_games
        )
        operational = sum(
            1
            for g in production_games
            if (
                g["projections"][model_id]["availability_status"] == "AVAILABLE"
                or g["projections"][degraded_model_id]["availability_status"] == "DEGRADED"
            )
        )

        missing = [
            {
                "game_id": g.get("game_id"),
                "date": g.get("date"),
                "away_team": g.get("away_team"),
                "home_team": g.get("home_team"),
                "availability_status":
                    g["projections"][model_id]["availability_status"],
                "component_values":
                    g["projections"][model_id].get("component_values", {}),
            }
            for g in production_games
            if (
                g["projections"][model_id]["availability_status"] != "AVAILABLE"
                and g["projections"][degraded_model_id]["availability_status"] != "DEGRADED"
            )
        ]

        return {
            "games": len(production_games),
            "full_available": statuses.get("AVAILABLE", 0),
            "degraded_available": degraded_statuses.get("DEGRADED", 0),
            "displayable": operational,
            "coverage_pct":
                100.0 * operational / len(production_games)
                if production_games else 0.0,
            "status_counts": dict(statuses),
            "degraded_status_counts": dict(degraded_statuses),
            "missing_games": missing,
        }

    spread = model_summary(STANDARD_SPREAD, DEGRADED_SPREAD)
    total = model_summary(STANDARD_TOTAL, DEGRADED_TOTAL)

    total_source_mix = Counter()
    for g in production_games:
        p = g["projections"][STANDARD_TOTAL]
        resolution = p.get("resolution") or {}
        mix = tuple(resolution.get("available_components") or [])
        total_source_mix[" + ".join(mix) if mix else "NONE"] += 1

    passed = (
        spread["displayable"] == len(production_games)
        and total["displayable"] == len(production_games)
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if passed else "FAIL",
        "production_scope": "FBS_VS_FBS",
        "production_games": len(production_games),
        "standard_spread": spread,
        "standard_total": total,
        "standard_total_source_mix": dict(total_source_mix),
        "note":
            "Non-FBS games remain in the canonical schedule for data completeness "
            "but are not part of the production FBS-vs-FBS projection coverage gate.",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print(json.dumps({
        "status": payload["status"],
        "production_scope": payload["production_scope"],
        "production_games": payload["production_games"],
        "standard_spread_displayable":
            f'{spread["displayable"]}/{spread["games"]}',
        "standard_total_displayable":
            f'{total["displayable"]}/{total["games"]}',
        "standard_total_source_mix":
            payload["standard_total_source_mix"],
        "output": str(OUT.relative_to(ROOT)),
    }, indent=2))

    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
