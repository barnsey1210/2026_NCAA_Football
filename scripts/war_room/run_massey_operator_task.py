#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "data/control/war_room_services/tasks"
LATEST = ROOT / "data/control/war_room_services/latest.json"
MASSEY_REPORT = ROOT / "data/control/massey_background_refresh.json"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--requester", default="operator")
    args = parser.parse_args()

    task_path = TASKS / f"{args.task_id}.json"

    task = read_json(task_path, {})
    task.update(
        schema_version=1,
        task_id=args.task_id,
        action="massey",
        requester=args.requester[:120],
        status="RUNNING",
        started_at=utc_now(),
        command_owner="scripts/war_room/run_massey_background_refresh.py",
        lock_policy="MASSEY_CRAWL_NO_CANONICAL_WRITER_LOCK",
    )

    atomic_json(task_path, task)
    atomic_json(LATEST, task)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/war_room/run_massey_background_refresh.py",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=900,
        check=False,
    )

    report = read_json(MASSEY_REPORT, {})

    worker_status = report.get("status")

    if result.returncode == 0 and worker_status in {
        "NO_CHANGE",
        "UPDATED_AND_PROPAGATED",
        "UPDATED_PROPAGATION_DEFERRED",
        "ALREADY_RUNNING",
    }:
        status = "COMPLETED"
    else:
        status = "FAILED"

    task.update(
        status=status,
        completed_at=utc_now(),
        returncode=result.returncode,
        massey_status=worker_status,
        massey_changed=report.get("changed"),
        massey_checked_at=report.get("completed_at"),
        ratings_triggered=report.get("ratings_triggered"),
        ratings_status=report.get("ratings_status"),
        ratings_returncode=report.get("ratings_returncode"),
        output_tail=((result.stdout or "") + (result.stderr or ""))[-8000:],
    )

    atomic_json(task_path, task)
    atomic_json(LATEST, task)

    print(json.dumps(task, indent=2))
    return 0 if status == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
