#!/usr/bin/env python3
"""Bounded Standard-model matchup-source refresh via approved collectors."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEDULE = ROOT / "data/snapshots/preseason/preseason_db.json"
REPORT = ROOT / "data/control/ratings_fast_source_refresh.json"
OUTPUTS = {
    "sagarin_rating": ROOT / "data/ratings/external_sources/sagarin_latest.csv",
    "sagarin": ROOT / "data/ratings/external_sources/sagarin_game_predictions_latest.csv",
    "dratings": ROOT / "data/ratings/external_sources/dratings_ncaaf_predictions_latest.csv",
    "massey": ROOT / "data/ratings/external_sources/massey_game_projections_2026.csv",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def digest(path):
    if not path.exists():
        return None
    if path.suffix != ".csv":
        return hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(newline="", errors="ignore") as handle:
        rows = list(csv.DictReader(handle))
    volatile = {"pulled_at", "snapshot_date", "source_file"}
    stable = [
        {key: value for key, value in row.items() if key not in volatile}
        for row in rows
    ]
    stable.sort(key=lambda row: json.dumps(row, sort_keys=True))
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()


def window_games(schedule, start_date, end_date):
    payload = json.loads(schedule.read_text())
    rows = []
    for game in payload.get("games") or []:
        game_date = str(game.get("date") or "")[:10]
        if start_date <= game_date <= end_date:
            rows.append({
                "game_id": str(game.get("game_id") or ""),
                "date": game_date,
                "away_team": game.get("away_team"),
                "home_team": game.get("home_team"),
            })
    return sorted(rows, key=lambda row: (row["date"], row["game_id"]))


def team_key(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def provider_coverage(path, games):
    """Report deterministic accepted coverage without fuzzy matching."""
    requested = {row["game_id"]: row for row in games}
    resolved = set()
    accepted_at = None
    if path.exists() and path.stat().st_size:
        with path.open(newline="", errors="ignore") as handle:
            for row in csv.DictReader(handle):
                stamp = row.get("pulled_at") or row.get("snapshot_date")
                if stamp:
                    accepted_at = max(accepted_at or stamp, stamp)
                game_id = str(row.get("game_id") or "")
                if game_id in requested:
                    resolved.add(game_id)
                    continue
                key = (
                    str(row.get("game_date") or row.get("date") or "")[:10],
                    team_key(row.get("away_team")),
                    team_key(row.get("home_team")),
                )
                for candidate_id, game in requested.items():
                    if key == (game["date"], team_key(game["away_team"]), team_key(game["home_team"])):
                        resolved.add(candidate_id)
                        break
    missing = sorted(set(requested) - resolved)
    return {
        "games_requested": len(requested),
        "games_resolved": len(resolved),
        "missing_game_ids": missing,
        "accepted_provider_timestamp": accepted_at,
    }


def commands(start_date, end_date, as_of_date=None):
    clock = ["--as-of-date", as_of_date] if as_of_date else []
    bounds = ["--start-date", start_date, "--end-date", end_date]
    return {
        "sagarin": [sys.executable, "ratings/pull_sagarin_ratings.py", *bounds, *clock],
        "dratings": [sys.executable, "scripts/projections/pull_dratings_ncaaf_predictions.py", *bounds, *clock],
        "massey": [sys.executable, "scripts/projections/refresh_massey_game_projections_2026.py", "--days", "7", *clock],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", help="Fixture-only clock override")
    args = parser.parse_args()
    today = date.fromisoformat(args.as_of_date) if args.as_of_date else date.today()
    start_date = today.isoformat()
    end_date = (today + timedelta(days=7)).isoformat()
    games = window_games(SCHEDULE, start_date, end_date)
    before = {name: digest(path) for name, path in OUTPUTS.items()}
    stages = []
    started = time.monotonic()
    for provider, command in commands(start_date, end_date, args.as_of_date).items():
        stage_started = time.monotonic()
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=300)
        stages.append({
            "provider": provider,
            "status": "PASSED" if result.returncode == 0 else "FAILED",
            "duration_seconds": round(time.monotonic() - stage_started, 3),
            "returncode": result.returncode,
            "output_tail": ((result.stdout or "") + (result.stderr or ""))[-4000:],
        })
        if result.returncode:
            break
    after = {name: digest(path) for name, path in OUTPUTS.items()}
    changed_components = [name for name in OUTPUTS if before[name] != after[name]]
    coverage = {
        provider: provider_coverage(OUTPUTS[provider], games)
        for provider in ("sagarin", "dratings", "massey")
    }
    payload = {
        "schema_version": "ratings-fast-standard-source-refresh-v1",
        "built_at": utc_now(),
        "window": {"start": start_date, "end": end_date, "inclusive": True},
        "canonical_games_considered": len(games),
        "canonical_game_ids": [row["game_id"] for row in games],
        "providers_checked": ["sagarin", "dratings", "massey"],
        "providers_contacted": [row["provider"] for row in stages],
        "changed_components": changed_components,
        "changed_providers": sorted({name.split("_", 1)[0] for name in changed_components}),
        "coverage": coverage,
        "stages": stages,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "success": len(stages) == 3 and all(row["returncode"] == 0 for row in stages),
    }
    atomic_json(REPORT, payload)
    print(json.dumps(payload, indent=2))
    return 0 if payload["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
