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
MAIN_REPO = Path.home() / "NCAAF_MAIN_REPO"


def run(*parts: str) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(parts))
    return subprocess.run(parts, cwd=ROOT, check=True)


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
        (MAIN_REPO / "war-room.html", Path("war-room.html")),
        (ROOT / "data/site/war_room_health.json", Path("data/site/war_room_health.json")),
        (
            ROOT / "data/site/war_room_market_matrix.json",
            Path("data/site/war_room_market_matrix.json"),
        ),
        (
            ROOT / "data/site/war_room_activity.json",
            Path("data/site/war_room_activity.json"),
        ),
    ):
        if not source.is_file():
            raise SystemExit(f"Required fast publication source missing: {source}")
        shutil.copy2(source, BUNDLE / relative)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--push",
        action="store_true",
        help="Commit and push the validated four-file public bundle.",
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

    build_bundle()
    try:
        run(
            sys.executable,
            "scripts/audit/audit_war_room_fast_publication.py",
            "--bundle",
            str(BUNDLE),
        )
    except subprocess.CalledProcessError as exc:
        # Acquisition and live-artifact generation have already succeeded.
        # Preserve that fact while surfacing publication validation separately.
        print("FAST_MARKET_RESULT=" + json.dumps({
            "acquisition_status": "SUCCEEDED" if not args.skip_refresh else "SKIPPED",
            "publication_validation_status": "FAILED",
            "publication_validation_returncode": exc.returncode,
        }, sort_keys=True))
        return 0
    if args.push:
        run("bash", "scripts/publish/publish_site.sh", "--war-room-push")
    else:
        print("LIVE WAR ROOM ARTIFACTS READY; repository publication deferred")
    print("FAST_MARKET_RESULT=" + json.dumps({
        "acquisition_status": "SUCCEEDED" if not args.skip_refresh else "SKIPPED",
        "publication_validation_status": "PASSED",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
