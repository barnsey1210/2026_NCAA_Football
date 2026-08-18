#!/usr/bin/env python3
"""Refresh the rolling production Massey FBS game-projection window."""
from __future__ import annotations

import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = ROOT / "scripts/projections/collect_massey_games_2026_safari.py"
BUILDER = ROOT / "scripts/projections/build_massey_game_projections_2026.py"


def run(args):
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def main():
    start = date.today()
    end = start + timedelta(days=14)

    run([
        sys.executable,
        str(COLLECTOR),
        "--start-date", start.isoformat(),
        "--end-date", end.isoformat(),
        "--force",
    ])

    run([sys.executable, str(BUILDER)])

    print(
        f"Massey production window refreshed: "
        f"{start.isoformat()} through {end.isoformat()} (inclusive)"
    )


if __name__ == "__main__":
    main()
