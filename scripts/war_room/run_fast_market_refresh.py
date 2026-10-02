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

    matrix_env = env.copy()
    matrix_env["NCAAF_LEAN_MARKET_OUTPUT"] = "1"
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
    try:
        quota = json.loads((ROOT / "data/war_room/audits/theodds_api_quota_status_fast.json").read_text())
        stages[-1]["substeps"] = {
            "provider_http_ms": quota.get("http_latency_ms"),
            "normalize_rows_ms": quota.get("normalization_ms"),
            "provider_games_returned": quota.get("provider_games_returned"),
            "commence_time_from": quota.get("commence_time_from"),
            "commence_time_to": quota.get("commence_time_to"),
        }
    except (OSError, ValueError, TypeError):
        pass

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
            matrix_env,
        )
    )

    # The live Command Center matrix is the hot-path publication boundary.
    # Activity, historical ledgers, Odds/Matchups overlays, and other broad
    # current-state views are maintained by the deferred daily pipeline.
    war_room_ready_ms = round(
        (perf_counter() - start) * 1000,
        1,
    )

    # Canonical all-season reconciliation and durable operational history are
    # required current-state maintenance, but the matrix above resolves the
    # accepted near-term fast quotes directly. Keep these gates intact without
    # making the browser wait for all-season work.
    current_market_env = env.copy()
    current_market_env["NCAAF_ENABLE_FAST_CURRENT_MARKET_OVERLAY"] = "1"
    stages.append(
        run_stage(
            "canonical_current_market_overlay",
            [sys.executable, "scripts/markets/build_current_market_contract.py"],
            current_market_env,
        )
    )
    stages.append(
        run_stage(
            "record_fast_refresh_history",
            [sys.executable, "scripts/war_room/record_fast_refresh_history.py"],
            env,
        )
    )

    # Detect accepted BEST/EDGE transitions on every fast cycle so the public
    # 30-minute alert window is anchored to the cycle that actually changed the
    # resolved matrix. This is local contract work and makes no provider call.
    stages.append(
        run_stage(
            "war_room_activity",
            [
                sys.executable,
                "scripts/war_room/build_war_room_activity.py",
                "--fast-cycle",
            ],
            env,
        )
    )
    stages.append(
        run_stage(
            "war_room_market_activity_enrichment",
            [
                sys.executable,
                "scripts/war_room/build_war_room_market_matrix.py",
                "--activity-enrichment-only",
            ],
            matrix_env,
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
        "critical_path_duration_ms": war_room_ready_ms,
        "deferred_to_daily_maintenance": [
            "odds_screen_v2_rebuild",
            "matchups_current_market_overlay",
            "append_current_market_book_history",
            "build_matchup_line_history_clean",
            "inject_matchup_line_history_asset",
        ],
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
