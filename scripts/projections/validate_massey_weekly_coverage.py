#!/usr/bin/env python3
"""Fail closed unless weekly Massey boards cover required FBS-vs-FBS games."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projections.build_game_projection_sources_2026 import (
    load_db,
    load_massey,
    site_game_index,
)

OUT = ROOT / "data/control/massey_weekly_coverage.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--board-dates", nargs="+", required=True)
    args = parser.parse_args()

    db = load_db()
    fbs = {str(row.get("team") or "").strip() for row in db.get("teams", [])}
    required = [
        game for game in db.get("games", [])
        if args.start_date <= str(game.get("date") or "")[:10] <= args.end_date
        and game.get("away_team") in fbs
        and game.get("home_team") in fbs
    ]
    rows, audit = load_massey(site_game_index(db))
    matched = {
        str(row.get("game_id")): row
        for row in rows
        if row.get("game_id")
        and args.start_date <= str(row.get("date") or "")[:10] <= args.end_date
    }
    missing = [game for game in required if str(game.get("game_id")) not in matched]
    spread = sum(pd.notna(matched.get(str(g.get("game_id")), {}).get("spread_home")) for g in required)
    total = sum(pd.notna(matched.get(str(g.get("game_id")), {}).get("total")) for g in required)
    payload = {
        "schema_version": "massey-weekly-coverage-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not missing else "FAIL",
        "window": {"start": args.start_date, "end": args.end_date},
        "board_dates": args.board_dates,
        "required_games": len(required),
        "canonical_matches": len(required) - len(missing),
        "spread_predictions": spread,
        "total_predictions": total,
        "missing_games": [
            {key: game.get(key) for key in ("game_id", "date", "away_team", "home_team")}
            for game in missing
        ],
        "unmatched_rows": sum(1 for row in audit if not row.get("matched")),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUT.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(OUT)
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
