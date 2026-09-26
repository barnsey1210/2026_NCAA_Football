#!/usr/bin/env python3
"""Refresh the rolling production Massey FBS game-projection window."""
from __future__ import annotations

import subprocess
import sys
import argparse
import shutil
import tempfile
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = ROOT / "scripts/projections/collect_massey_games_2026_safari.py"
BUILDER = ROOT / "scripts/projections/build_massey_game_projections_2026.py"
OUTPUT = ROOT / "data/ratings/external_sources/massey_game_projections_2026.csv"


def run(args):
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def football_week_saturdays(as_of: date) -> tuple[date, date]:
    """Return the current Sunday-Saturday week end and the following one."""
    current = as_of + timedelta(days=(5 - as_of.weekday()) % 7)
    return current, current + timedelta(days=7)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", help="Fixture-only clock override")
    parser.add_argument(
        "--days", type=int, default=None,
        help="Legacy compatibility only; weekly board selection is authoritative",
    )
    args = parser.parse_args()
    start = date.fromisoformat(args.as_of_date) if args.as_of_date else date.today()
    current_saturday, next_saturday = football_week_saturdays(start)
    window_start = current_saturday - timedelta(days=6)
    end = next_saturday
    board_dates = [current_saturday.isoformat(), next_saturday.isoformat()]

    with tempfile.TemporaryDirectory(prefix="massey-refresh-") as tmp:
        backup = Path(tmp) / OUTPUT.name
        had_output = OUTPUT.exists()
        if had_output:
            shutil.copy2(OUTPUT, backup)
        try:
            run([
                sys.executable,
                str(COLLECTOR),
                "--dates", *board_dates,
                "--force",
            ])
            run([
                sys.executable, str(BUILDER),
                "--start-date", window_start.isoformat(),
                "--end-date", end.isoformat(),
                "--board-dates", *board_dates,
            ])
            run([
                sys.executable,
                "scripts/projections/validate_massey_weekly_coverage.py",
                "--start-date", window_start.isoformat(),
                "--end-date", end.isoformat(),
                "--board-dates", *board_dates,
            ])
        except Exception:
            if had_output:
                shutil.copy2(backup, OUTPUT)
            elif OUTPUT.exists():
                OUTPUT.unlink()
            raise

    print(
        f"Massey production window refreshed: "
        f"{window_start.isoformat()} through {end.isoformat()} (inclusive); "
        f"boards={','.join(board_dates)}"
    )


if __name__ == "__main__":
    main()
