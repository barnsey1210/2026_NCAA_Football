#!/usr/bin/env python3
"""Bounded War Room operational service dispatcher.

Automatic schedulers and authenticated operator requests enter through this
same allowlisted dispatcher. Domain calculations remain in their existing
owners; this module only coordinates locks, task identity, execution, and
durable status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "data/control/war_room_services"
LOCKS = CONTROL / "locks"
TASKS = CONTROL / "tasks"
LATEST = CONTROL / "latest.json"
DAILY_STATUS = ROOT / "data/control/daily_run_status.json"
REGISTRY = ROOT / "scripts/control/refresh_stage_registry.json"

ACTION_REGISTRY_KEYS = {
    "market": "MARKET_REFRESH",
    "ratings": "RATINGS_REFRESH",
    "postgame": "POSTGAME_REFRESH",
    "war-room-rebuild": "WAR_ROOM_REBUILD",
}

# Registry modes select only these reviewed command templates. Registry text can
# never supply an executable, path, or arbitrary argument.
MODE_COMMANDS = {
    "war-room-market": [sys.executable, "scripts/war_room/run_fast_market_publication.py"],
    "ratings": [sys.executable, "scripts/control/run_data_refresh.py", "ratings", "--execute", "--confirm-publish", "--trigger-source", "war-room-service"],
    "postgame": [sys.executable, "scripts/control/run_data_refresh.py", "postgame", "--execute", "--confirm-publish", "--trigger-source", "war-room-service"],
    "war-room-rebuild": [sys.executable, "scripts/war_room/run_fast_market_publication.py", "--skip-refresh", "--push"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def resolve_command(action: str) -> list[str]:
    registry = read_json(REGISTRY, {})
    registry_key = ACTION_REGISTRY_KEYS[action]
    spec = registry.get("actions", {}).get(registry_key, {})
    mode = spec.get("controller_mode")
    if mode not in MODE_COMMANDS:
        raise RuntimeError(f"unapproved controller mode for {registry_key}: {mode!r}")
    return list(MODE_COMMANDS[mode])


def daily_running() -> bool:
    state = read_json(DAILY_STATUS, {})
    return str(state.get("status", "")).upper() in {"RUNNING", "STARTED", "IN_PROGRESS"}


def task_id(action: str, trigger: str) -> str:
    bucket = int(time.time() // 60)
    raw = f"{action}|{trigger}|{bucket}".encode()
    return f"{action}-{hashlib.sha256(raw).hexdigest()[:12]}"


def acquire(action: str, identity: str) -> Path:
    LOCKS.mkdir(parents=True, exist_ok=True)
    global_lock = LOCKS / "canonical-writer.lock"
    try:
        global_lock.mkdir()
    except FileExistsError:
        owner = read_json(global_lock / "owner.json", {})
        pid = owner.get("pid")
        if isinstance(pid, int):
            try:
                os.kill(pid, 0)
                raise RuntimeError(f"overlap blocked by running task {owner.get('task_id')}")
            except ProcessLookupError:
                shutil.rmtree(global_lock)
                global_lock.mkdir()
        else:
            raise RuntimeError("overlap blocked by canonical writer lock")
    atomic_json(global_lock / "owner.json", {"task_id": identity, "action": action, "pid": os.getpid(), "started_at": utc_now()})
    return global_lock


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=[*ACTION_REGISTRY_KEYS, "status"])
    parser.add_argument("--trigger", default="manual")
    parser.add_argument("--requester", default="scheduler")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--prepared-results",
        action="store_true",
        help="Postgame only: schedule/results were already refreshed by the final watcher.",
    )
    args = parser.parse_args()

    if args.prepared_results and args.action != "postgame":
        parser.error("--prepared-results is valid only for postgame")
    if args.action == "status":
        print(json.dumps(read_json(LATEST, {"status": "NEVER_RUN"}), indent=2))
        return 0

    identity = args.task_id or task_id(args.action, args.trigger)
    if not re.fullmatch(r"[a-z][a-z0-9-]{5,63}", identity):
        parser.error("--task-id must be a safe lowercase task identifier")
    prior = read_json(TASKS / f"{identity}.json", {})
    if prior.get("status") in {
        "RUNNING",
        "COMPLETED",
        "COMPLETED_WITH_WARNINGS",
        "FAILED",
        "BLOCKED_BY_OVERLAP",
        "DEFERRED_BY_DAILY_BACKBONE",
        "DRY_RUN",
    }:
        print(json.dumps(prior, indent=2))
        return 0
    task = prior if prior.get("status") == "REQUESTED" else {}
    task.update(
        schema_version=1,
        task_id=identity,
        action=args.action,
        trigger=args.trigger,
        requester=args.requester[:120],
        requested_at=task.get("requested_at", utc_now()),
        status="REQUESTED",
        command_owner=resolve_command(args.action)[1],
    )
    atomic_json(TASKS / f"{identity}.json", task)
    atomic_json(LATEST, task)
    if daily_running():
        task.update(status="DEFERRED_BY_DAILY_BACKBONE", completed_at=utc_now())
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)
        print(json.dumps(task, indent=2)); return 2
    if args.dry_run:
        task.update(status="DRY_RUN", completed_at=utc_now())
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)
        print(json.dumps(task, indent=2)); return 0

    lock = None
    try:
        lock = acquire(args.action, identity)
        task.update(status="RUNNING", started_at=utc_now())
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)
        command = resolve_command(args.action)
        if args.prepared_results:
            command = [*command, "--postgame-skip-schedule"]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=3600, check=False)
        task.update(
            status="COMPLETED" if result.returncode == 0 else "FAILED",
            completed_at=utc_now(),
            returncode=result.returncode,
            output_tail=((result.stdout or "") + (result.stderr or ""))[-8000:],
        )
    except RuntimeError as exc:
        task.update(status="BLOCKED_BY_OVERLAP", completed_at=utc_now(), error=str(exc))
    except subprocess.TimeoutExpired:
        task.update(status="FAILED", completed_at=utc_now(), error="service execution timed out")
    finally:
        if lock and lock.exists():
            shutil.rmtree(lock)
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)
    print(json.dumps(task, indent=2))
    return 0 if task["status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
