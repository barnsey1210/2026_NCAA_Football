#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "data/control/futures_market_scheduler"
STATE = STATE_DIR / "scheduler_state.json"
LATEST = STATE_DIR / "scheduler_latest.json"
RUNS = STATE_DIR / "scheduler_runs.jsonl"
ET = ZoneInfo("America/New_York")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        dir=path.parent,
        delete=False,
        encoding="utf-8",
    ) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp = Path(handle.name)
    temp.replace(path)


def in_window(value: datetime) -> bool:
    local = value.astimezone(ET)
    weekday = local.weekday()
    if weekday == 6:
        return local.hour >= 6
    if weekday == 0:
        return local.hour <= 20
    return False


def slot(value: datetime) -> str:
    return value.astimezone(ET).strftime("%Y-%m-%dT%H")


def persist(report: dict, state: dict) -> None:
    atomic_json(STATE, state)
    atomic_json(LATEST, report)
    RUNS.parent.mkdir(parents=True, exist_ok=True)
    with RUNS.open("a") as handle:
        handle.write(json.dumps(report, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger", default="futures-scheduler")
    args = parser.parse_args()

    now = now_utc()
    local = now.astimezone(ET)
    current_slot = slot(now)
    state = read_json(STATE, {})

    report = {
        "schema_version": 1,
        "checked_at": now.isoformat(),
        "local_time": local.isoformat(),
        "timezone": "America/New_York",
        "schedule": "hourly Sunday 06:00 ET through Monday 20:00 ET",
        "slot": current_slot,
        "status": "OFF_WINDOW",
        "task_id": None,
    }

    if not in_window(now):
        persist(report, state)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if state.get("last_completed_slot") == current_slot:
        report["status"] = "ALREADY_COMPLETED_THIS_HOUR"
        persist(report, state)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    task_id = "futures-auto-" + local.strftime("%Y%m%d%H")
    command = [
        sys.executable,
        "scripts/control/run_war_room_service.py",
        "futures",
        "--trigger",
        args.trigger,
        "--requester",
        "scheduler",
        "--task-id",
        task_id,
    ]

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=3600,
    )

    try:
        task = json.loads(result.stdout)
    except Exception:
        task = {
            "status": "FAILED",
            "returncode": result.returncode,
            "stdout_tail": (result.stdout or "")[-4000:],
            "stderr_tail": (result.stderr or "")[-4000:],
        }

    status = str(task.get("status") or "FAILED")

    report.update(
        status=status,
        task_id=task_id,
        service_result=task,
    )

    if status in {"COMPLETED", "COMPLETED_WITH_WARNINGS"}:
        state.update(
            schema_version=1,
            last_completed_slot=current_slot,
            last_completed_at=now.isoformat(),
            last_status=status,
        )
    else:
        state.update(
            schema_version=1,
            last_attempted_slot=current_slot,
            last_attempted_at=now.isoformat(),
            last_status=status,
        )

    persist(report, state)
    print(json.dumps(report, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
