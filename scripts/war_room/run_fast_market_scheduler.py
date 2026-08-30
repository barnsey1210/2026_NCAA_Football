#!/usr/bin/env python3
"""Durable cadence gate for the existing bounded War Room Market service."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "data/control/market_scheduler"
LATEST = STATE_DIR / "latest.json"
STATE = STATE_DIR / "state.json"
RUNS = STATE_DIR / "runs.jsonl"
HEALTH = ROOT / "data/site/war_room_health.json"
DAILY_STATUS = ROOT / "data/control/daily_run_status.json"
SERVICE_TASKS = ROOT / "data/control/war_room_services/tasks"
ET = ZoneInfo("America/New_York")
ROUTINE_SUPPRESSION_SECONDS = 600
POSTGAME_PRIORITY_STATUSES = {"REQUESTED", "WAITING_FOR_CANONICAL_WRITER", "RUNNING"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def cadence(value: datetime) -> tuple[str, int]:
    """Return the locked weekly ET cadence band and interval."""
    local = value.astimezone(ET)
    weekday = local.weekday()
    seconds = local.hour * 3600 + local.minute * 60 + local.second
    if weekday == 5:
        if seconds < 22 * 3600:
            return "ROUTINE_HOURLY", 3600
        if seconds < 23 * 3600:
            return "SATURDAY_RAMP_5M", 300
        return "SATURDAY_OPENER_90S", 90
    if weekday == 6:
        if seconds < 2 * 3600:
            return "SATURDAY_OPENER_90S", 90
        if seconds < 8 * 3600:
            return "SUNDAY_OVERNIGHT_5M", 300
        if seconds < 23 * 3600:
            return "SUNDAY_ACTIVE_2M", 120
        return "SUNDAY_TRANSITION_HOURLY", 3600
    return "ROUTINE_HOURLY", 3600


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return default


def latest_market_success(health_path: Path = HEALTH,
                          daily_path: Path = DAILY_STATUS) -> datetime | None:
    """Latest accepted fast/manual pull or completed daily game-market stage."""
    payload = read_json(health_path, {})
    candidates = [parse_time((payload.get("fast_market_refresh") or {}).get("last_fast_pull_at"))]
    daily = read_json(daily_path, {})
    for stage in daily.get("stages") or []:
        if stage.get("id") == "game_market_acquisition" and stage.get("status") == "PASSED":
            candidates.append(parse_time(stage.get("finished_at_utc")))
    valid = [value for value in candidates if value]
    return max(valid) if valid else None


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True,
                          check=False, timeout=3600)


def child_task(stdout: str) -> dict[str, Any]:
    try:
        value = json.loads(stdout)
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError):
        return {}


def postgame_priority_pending(tasks_dir: Path = SERVICE_TASKS) -> bool:
    """Return true only for a live Postgame dispatcher requesting the writer."""
    try:
        paths = tasks_dir.glob("*.json")
    except OSError:
        return False
    for path in paths:
        task = read_json(path, {})
        if task.get("action") != "postgame" or task.get("status") not in POSTGAME_PRIORITY_STATUSES:
            continue
        pid = task.get("dispatcher_pid")
        if not isinstance(pid, int):
            continue
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            continue
    return False


def execute(*, now: datetime, state: dict[str, Any], market_success_at: datetime | None,
            trigger: str = "market-scheduler",
            runner: Callable[[list[str]], subprocess.CompletedProcess[str]] = run_command,
            postgame_pending: Callable[[], bool] = postgame_priority_pending,
            ) -> tuple[int, dict[str, Any], dict[str, Any]]:
    started = time.monotonic()
    now_utc = now.astimezone(timezone.utc)
    band, interval = cadence(now)
    last_due = parse_time(state.get("last_due_handled_at"))
    last_scheduled = parse_time(state.get("last_scheduled_dispatch_at"))
    critical = band not in {"ROUTINE_HOURLY", "SUNDAY_TRANSITION_HOURLY"}
    reference_candidates = [x for x in (last_due, market_success_at if critical else None) if x]
    reference = max(reference_candidates) if reference_candidates else None
    due = reference is None or (now_utc - reference).total_seconds() >= interval
    next_due = now_utc if due else reference + timedelta(seconds=interval)
    report: dict[str, Any] = {
        "schema_version": 1, "checked_at": iso(now), "timezone": "America/New_York",
        "cadence_band": band, "required_interval_seconds": interval,
        "last_market_success_at": iso(market_success_at) if market_success_at else None,
        "last_scheduled_dispatch_at": iso(last_scheduled) if last_scheduled else None,
        "next_due_at": iso(next_due), "status": "NOT_DUE", "task_id": None,
        "trigger": trigger, "duration_seconds": 0.0, "deferred_reason": None,
        "service_result": None,
    }
    new_state = dict(state)
    if not due:
        report["duration_seconds"] = round(time.monotonic() - started, 3)
        return 0, report, new_state

    if postgame_pending():
        new_state.update(schema_version=1, last_status="DEFERRED_BY_POSTGAME")
        report.update(
            status="DEFERRED_BY_POSTGAME",
            deferred_reason="Postgame is pending or running",
            next_due_at=iso(now_utc),
            duration_seconds=round(time.monotonic() - started, 3),
        )
        return 0, report, new_state

    if (band == "ROUTINE_HOURLY" and market_success_at
            and 0 <= (now_utc - market_success_at).total_seconds() < ROUTINE_SUPPRESSION_SECONDS):
        new_state.update(schema_version=1, last_due_handled_at=iso(now),
                         last_status="SUPPRESSED_RECENT_REFRESH")
        report.update(status="SUPPRESSED_RECENT_REFRESH",
                      next_due_at=iso(now_utc + timedelta(seconds=interval)))
        report["duration_seconds"] = round(time.monotonic() - started, 3)
        return 0, report, new_state

    task_id = f"market-auto-{now_utc:%Y%m%d%H%M%S}"
    command = [sys.executable, "scripts/control/run_war_room_service.py", "market",
               "--trigger", trigger, "--requester", "scheduler", "--task-id", task_id]
    report.update(status="REQUESTED", task_id=task_id)
    result = runner(command)
    task = child_task(result.stdout or "")
    service_status = str(task.get("status") or "FAILED")
    output = str(task.get("output_tail") or "")
    if service_status == "FAILED" and "quota" in output.lower():
        status = "BLOCKED_BY_QUOTA"
    else:
        status = service_status
    new_state.update(schema_version=1, last_scheduled_dispatch_at=iso(now),
                     last_status=status, cadence_band=band)
    if status in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}:
        new_state.update(last_due_handled_at=iso(now), last_scheduled_success_at=iso(now))
        report["next_due_at"] = iso(now_utc + timedelta(seconds=interval))
    elif status == "DEFERRED_BY_DAILY_BACKBONE":
        report["deferred_reason"] = "daily backbone is active"
    elif status == "BLOCKED_BY_OVERLAP":
        report["deferred_reason"] = str(task.get("error") or "canonical writer is active")
    elif status == "BLOCKED_BY_QUOTA":
        report["deferred_reason"] = "existing Market quota governor blocked acquisition"
    report.update(status=status, last_scheduled_dispatch_at=iso(now),
                  service_result=task or {"status": "FAILED", "returncode": result.returncode,
                                          "error": "Market dispatcher returned no structured task result"},
                  duration_seconds=round(time.monotonic() - started, 3))
    code = 0 if status in {"COMPLETED", "COMPLETED_WITH_WARNINGS",
                           "DEFERRED_BY_DAILY_BACKBONE", "BLOCKED_BY_OVERLAP",
                           "BLOCKED_BY_QUOTA", "DEFERRED_BY_POSTGAME"} else 2
    return code, report, new_state


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True); handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def persist(report: dict[str, Any], state: dict[str, Any]) -> None:
    atomic_json(STATE, state); atomic_json(LATEST, report)
    RUNS.parent.mkdir(parents=True, exist_ok=True)
    with RUNS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(report, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--trigger", default="market-scheduler")
    args = parser.parse_args()
    code, report, state = execute(now=utc_now(), state=read_json(STATE, {}),
                                  market_success_at=latest_market_success(), trigger=args.trigger)
    persist(report, state); print(json.dumps(report, indent=2, sort_keys=True)); return code


if __name__ == "__main__":
    raise SystemExit(main())
