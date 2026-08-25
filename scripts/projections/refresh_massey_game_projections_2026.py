#!/usr/bin/env python3
"""Refresh the rolling production Massey FBS game-projection window."""
from __future__ import annotations

import subprocess
import sys
import argparse
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = ROOT / "scripts/projections/collect_massey_games_2026_safari.py"
BUILDER = ROOT / "scripts/projections/build_massey_game_projections_2026.py"


def run(args):
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", help="Fixture-only clock override")
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    start = date.fromisoformat(args.as_of_date) if args.as_of_date else date.today()
    end = start + timedelta(days=args.days)

    run([
        sys.executable,
        str(COLLECTOR),
        "--start-date", start.isoformat(),
        "--end-date", end.isoformat(),
        "--force",
    ])

    run([sys.executable, str(BUILDER), "--start-date", start.isoformat(), "--end-date", end.isoformat()])

    print(
        f"Massey production window refreshed: "
        f"{start.isoformat()} through {end.isoformat()} (inclusive)"
    )


if __name__ == "__main__":
    main()
