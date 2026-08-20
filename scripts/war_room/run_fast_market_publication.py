#!/usr/bin/env python3
"""Run the fast market refresh and publish only Command Center artifacts."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MAIN_REPO = Path.home() / "NCAAF_MAIN_REPO"

BUNDLE = ROOT / "build/war_room_public"


def run(*parts: str) -> None:
    print("+", " ".join(parts))
    subprocess.run(parts, cwd=ROOT, check=True)


def sync_fast_artifacts_to_main_repo() -> None:

    files = [
        (
            ROOT / "data/site/war_room_health.json",
            MAIN_REPO / "data/site/war_room_health.json",
        ),
        (
            ROOT / "data/site/war_room_market_matrix.json",
            MAIN_REPO / "data/site/war_room_market_matrix.json",
        ),
    ]

    for source, destination in files:

        if not source.is_file():
            raise SystemExit(
                f"Fast refresh artifact missing: {source}"
            )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(source, destination)

    print("FAST ARTIFACTS SYNCED TO MAIN REPO")


def build_bundle() -> None:

    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)

    (BUNDLE / "data/site").mkdir(parents=True)

    files = [
        (
            MAIN_REPO / "war-room.html",
            BUNDLE / "war-room.html",
        ),
        (
            MAIN_REPO / "data/site/war_room_health.json",
            BUNDLE / "data/site/war_room_health.json",
        ),
        (
            MAIN_REPO / "data/site/war_room_market_matrix.json",
            BUNDLE / "data/site/war_room_market_matrix.json",
        ),
    ]

    for source, destination in files:

        if not source.is_file():
            raise SystemExit(
                f"Required fast publication source missing: {source}"
            )

        shutil.copy2(source, destination)

    print("FAST PUBLIC BUNDLE BUILT")
    print(BUNDLE)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--push",
        action="store_true",
        help="Commit and push validated bundle.",
    )

    parser.add_argument(
        "--skip-refresh",
        action="store_true",
        help="Skip market refresh.",
    )

    args = parser.parse_args()


    if not args.skip_refresh:

        run(
            sys.executable,
            "scripts/war_room/run_fast_market_refresh.py",
        )


    sync_fast_artifacts_to_main_repo()

    build_bundle()


    run(
        sys.executable,
        "scripts/audit/audit_war_room_fast_publication.py",
        "--bundle",
        str(BUNDLE),
    )


    mode = (
        "--push"
        if args.push
        else "--check"
    )


    run(
        "bash",
        "scripts/publish/publish_site.sh",
        mode,
    )


if __name__ == "__main__":
    main()