#!/usr/bin/env python3
"""Time-window gate for the existing bounded War Room Ratings service."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "data/control/ratings_scheduler"
LATEST = STATE_DIR / "latest.json"
RUNS = STATE_DIR / "runs.jsonl"
ET = ZoneInfo("America/New_York")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def in_ratings_window(value: datetime) -> bool:
    """Sunday 00:00 through Monday 12:00 ET, inclusive."""
    local = value.astimezone(ET)
    return local.weekday() == 6 or (
        local.weekday() == 0
        and (local.hour, local.minute, local.second, local.microsecond)
        <= (12, 0, 0, 0)
    )


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                          check=False, timeout=3600)


def child_task(stdout: str) -> dict[str, Any]:
    try:
        value = json.loads(stdout)
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        return {}


def execute(*, now: datetime, trigger: str = "ratings-scheduler",
            runner: Callable[[list[str]], subprocess.CompletedProcess[str]] = run_command
            ) -> tuple[int, dict[str, Any]]:
    started = time.monotonic()
    checked_at = iso(now)
    inside = in_ratings_window(now)
    report: dict[str, Any] = {
        "schema_version": 1, "checked_at": checked_at,
        "timezone": "America/New_York",
        "window_status": "INSIDE_RATINGS_WINDOW" if inside else "OUTSIDE_RATINGS_WINDOW",
        "trigger": trigger, "task_id": None,
        "status": "OUTSIDE_RATINGS_WINDOW", "started_at": checked_at,
        "completed_at": None, "duration_seconds": 0.0,
        "service_result": None, "deferred_reason": None,
    }
    if not inside:
        report["completed_at"] = iso(utc_now())
        report["duration_seconds"] = round(time.monotonic() - started, 3)
        return 0, report

    task_id = f"ratings-auto-{now.astimezone(timezone.utc):%Y%m%d%H%M%S}"
    report.update(task_id=task_id, status="REQUESTED")
    command = [sys.executable, "scripts/control/run_war_room_service.py", "ratings",
               "--trigger", trigger, "--requester", "scheduler", "--task-id", task_id]
    try:
        result = runner(command)
        task = child_task(result.stdout or "")
        service_status = str(task.get("status") or "FAILED")
        output_tail = str(task.get("output_tail") or "")
        status = ("NO_CHANGES" if service_status == "COMPLETED"
                  and '"status": "NO_CHANGES"' in output_tail else service_status)
        report.update(status=status, service_result=task or {
            "status": "FAILED", "returncode": result.returncode,
            "error": "Ratings dispatcher returned no structured task result",
        })
        if status == "DEFERRED_BY_DAILY_BACKBONE":
            report["deferred_reason"] = "daily backbone is active"
        elif status == "BLOCKED_BY_OVERLAP":
            report["deferred_reason"] = str(task.get("error") or "canonical writer is active")
        code = 0 if status in {"COMPLETED", "COMPLETED_WITH_WARNINGS", "NO_CHANGES",
                               "DEFERRED_BY_DAILY_BACKBONE", "BLOCKED_BY_OVERLAP"} else 2
    except subprocess.TimeoutExpired:
        report.update(status="FAILED", service_result={"error": "Ratings scheduler dispatch timed out"})
        code = 2
    report["completed_at"] = iso(utc_now())
    report["duration_seconds"] = round(time.monotonic() - started, 3)
    return code, report


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def persist(report: dict[str, Any]) -> None:
    atomic_json(LATEST, report)
    RUNS.parent.mkdir(parents=True, exist_ok=True)
    with RUNS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(report, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger", default="ratings-scheduler")
    args = parser.parse_args()
    code, report = execute(now=utc_now(), trigger=args.trigger)
    persist(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
