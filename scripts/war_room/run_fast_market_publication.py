#!/usr/bin/env python3
"""Run the fast market refresh and publish only Command Center artifacts."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "build/war_room_public"
HEALTH = ROOT / "data/site/war_room_health.json"


def run(*parts: str) -> None:
    print("+", " ".join(parts))
    subprocess.run(parts, cwd=ROOT, check=True)


def quota_preflight() -> None:
    try:
        health = json.loads(HEALTH.read_text())
        quota = health["api_quota"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise SystemExit(f"Fast publication quota preflight unavailable: {exc}") from exc
    if quota.get("scheduled_refresh_allowed") is not True:
        raise SystemExit(
            "Fast publication blocked: provider quota is at reserve or unavailable. "
            "No API request was made."
        )


def build_bundle() -> None:
    if BUNDLE.exists():
        shutil.rmtree(BUNDLE)
    (BUNDLE / "data/site").mkdir(parents=True)
    for source, relative in (
        (ROOT / "war-room.html", Path("war-room.html")),
        (ROOT / "data/site/war_room_health.json", Path("data/site/war_room_health.json")),
        (
            ROOT / "data/site/war_room_market_matrix.json",
            Path("data/site/war_room_market_matrix.json"),
        ),
    ):
        if not source.is_file():
            raise SystemExit(f"Required fast publication source missing: {source}")
        shutil.copy2(source, BUNDLE / relative)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--push",
        action="store_true",
        help="Commit and push the validated three-file public bundle.",
    )
    parser.add_argument(
        "--skip-refresh",
        action="store_true",
        help="Offline packaging/validation only; do not call the provider.",
    )
    args = parser.parse_args()

    if not args.skip_refresh:
        quota_preflight()
        run(sys.executable, "scripts/war_room/run_fast_market_refresh.py")

    run(sys.executable, "scripts/site/build_war_room_page.py")
    build_bundle()
    run(
        sys.executable,
        "scripts/audit/audit_war_room_fast_publication.py",
        "--bundle",
        str(BUNDLE),
    )
    mode = "--war-room-push" if args.push else "--war-room-check"
    run("bash", "scripts/publish/publish_site.sh", mode)


if __name__ == "__main__":
    main()
