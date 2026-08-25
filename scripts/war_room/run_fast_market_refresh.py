#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import subprocess
import sys

from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]

TIMING_OUT = (
    ROOT
    / "data/war_room/audits/fast_market_pipeline_timing.json"
)


def run_stage(name, cmd, env):
    started_at = datetime.now(timezone.utc)
    start = perf_counter()

    print()
    print(f"START {name}")
    print("+", " ".join(str(x) for x in cmd))

    subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        check=True,
    )

    elapsed_ms = round(
        (perf_counter() - start) * 1000,
        1,
    )

    finished_at = datetime.now(timezone.utc)

    print(
        f"END   {name}: "
        f"{elapsed_ms / 1000:.3f}s"
    )

    return {
        "stage": name,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_ms": elapsed_ms,
    }


def main():
    if not os.environ.get("THE_ODDS_API_KEY_FAST"):
        raise SystemExit(
            "Missing THE_ODDS_API_KEY_FAST. "
            "No API request was made."
        )

    env = os.environ.copy()

    # Locked Command Center configuration.
    env["NCAAF_THEODDS_PROFILE"] = "command_center"
    env["NCAAF_THEODDS_MARKETS"] = "spreads,totals"

    started_at = datetime.now(timezone.utc)
    start = perf_counter()

    print("=" * 72)
    print("WAR ROOM FAST MARKET REFRESH")
    print("=" * 72)
    print("profile: command_center")
    print("credential: THE_ODDS_API_KEY_FAST")
    print("markets: spreads,totals")
    print("moneyline: NO")
    print("started_at:", started_at.isoformat())

    stages = []

    stages.append(
        run_stage(
            "the_odds_api_pull_and_normalize",
            [
                sys.executable,
                "pull_theodds_ncaaf_lines_2026.py",
            ],
            env,
        )
    )

    stages.append(
        run_stage(
            "latency_analysis",
            [
                sys.executable,
                "scripts/war_room/analyze_fast_market_latency.py",
            ],
            env,
        )
    )

    stages.append(
        run_stage(
            "war_room_health",
            [
                sys.executable,
                "scripts/war_room/build_war_room_health.py",
            ],
            env,
        )
    )

    stages.append(
        run_stage(
            "war_room_market_matrix",
            [
                sys.executable,
                "scripts/war_room/build_war_room_market_matrix.py",
            ],
            env,
        )
    )

    # Preserve the accepted fast state in the canonical historical contract.
    # These stages are offline and idempotent; they make the latest fast pull
    # available to Openers without changing current-market selection.
    stages.append(
        run_stage(
            "append_current_market_book_history",
            [sys.executable, "scripts/odds/append_current_market_book_history.py"],
            env,
        )
    )
    stages.append(
        run_stage(
            "build_matchup_line_history",
            [sys.executable, "scripts/history/build_matchup_line_history_clean.py", "--incremental-fast"],
            env,
        )
    )
    stages.append(
        run_stage(
            "publish_matchup_line_history_asset",
            [sys.executable, "scripts/site/inject_matchup_line_history.py", "--asset-only"],
            env,
        )
    )

    stages.append(
        run_stage(
            "refresh_history",
            [
                sys.executable,
                "scripts/war_room/record_fast_refresh_history.py",
            ],
            env,
        )
    )

    total_ms = round(
        (perf_counter() - start) * 1000,
        1,
    )

    finished_at = datetime.now(timezone.utc)

    payload = {
        "schema_version": "war-room-fast-pipeline-timing-v1",
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "total_duration_ms": total_ms,
        "stages": stages,
    }

    TIMING_OUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    TIMING_OUT.write_text(
        json.dumps(payload, indent=2) + "\n"
    )

    print()
    print("=" * 72)
    print("FAST MARKET REFRESH COMPLETE")
    print("=" * 72)

    for stage in stages:
        print(
            f'{stage["stage"]:36} '
            f'{stage["duration_ms"] / 1000:8.3f}s'
        )

    print("-" * 48)
    print(
        f'{"TOTAL":36} '
        f'{total_ms / 1000:8.3f}s'
    )

    print()
    print(
        "timing:",
        TIMING_OUT.relative_to(ROOT),
    )


if __name__ == "__main__":
    main()
