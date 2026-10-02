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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "data/control/war_room_services"
LOCKS = CONTROL / "locks"
TASKS = CONTROL / "tasks"
LATEST = CONTROL / "latest.json"
DAILY_STATUS = ROOT / "data/control/daily_run_status.json"
REGISTRY = ROOT / "scripts/control/refresh_stage_registry.json"
WRITER_QUEUE_WAIT_SECONDS = 900
WRITER_QUEUE_POLL_SECONDS = 1.0
STALE_TASK_MAX_AGE_SECONDS = 24 * 60 * 60
LIVE_REQUEST_STATUSES = {
    "REQUESTED", "WAITING_FOR_CANONICAL_WRITER", "QUEUED_FOR_MARKET_GAP",
}
RATINGS_PROTECTED_STATUSES = LIVE_REQUEST_STATUSES | {
    "RUNNING", "RATINGS_CATCHUP_MARKET",
}

ACTION_REGISTRY_KEYS = {
    "market": "MARKET_REFRESH",
    "futures": "FUTURES_REFRESH",
    "ratings": "RATINGS_REFRESH",
    "postgame": "POSTGAME_REFRESH",
    "war-room-rebuild": "WAR_ROOM_REBUILD",
}

# Registry modes select only these reviewed command templates. Registry text can
# never supply an executable, path, or arbitrary argument.
MODE_COMMANDS = {
    "war-room-market": [sys.executable, "scripts/war_room/run_fast_market_publication.py"],
    "futures-fast": [sys.executable, "scripts/futures/run_fast_futures_publication.py"],
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


def fast_market_result(output: str) -> dict:
    for line in reversed(output.splitlines()):
        if not line.startswith("FAST_MARKET_RESULT="):
            continue
        try:
            value = json.loads(line.split("=", 1)[1])
            return value if isinstance(value, dict) else {}
        except (TypeError, ValueError):
            return {}
    return {}


def daily_running() -> bool:
    state = read_json(DAILY_STATUS, {})
    return str(state.get("status", "")).upper() in {"RUNNING", "STARTED", "IN_PROGRESS"}


def task_id(action: str, trigger: str) -> str:
    bucket = int(time.time() // 60)
    raw = f"{action}|{trigger}|{bucket}".encode()
    return f"{action}-{hashlib.sha256(raw).hexdigest()[:12]}"


def parse_time(value: object) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def process_identity(pid: int) -> Optional[dict]:
    """Return immutable start time and command for one macOS/POSIX process."""
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "lstart=", "-o", "command="],
            text=True, capture_output=True, timeout=2, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    line = (result.stdout or "").strip()
    if result.returncode or not line:
        return None
    parts = line.split(None, 5)
    if len(parts) < 6:
        return None
    try:
        started = datetime.strptime(" ".join(parts[:5]), "%a %b %d %H:%M:%S %Y")
    except ValueError:
        return None
    return {
        "started_at": started.replace(tzinfo=timezone.utc).isoformat(),
        "command": parts[5],
    }


def dispatcher_is_live(task: dict, *, now: Optional[datetime] = None) -> tuple[bool, str]:
    """Reject dead, reused, unrelated, or time-incompatible dispatcher PIDs."""
    pid = task.get("dispatcher_pid")
    if not isinstance(pid, int):
        return False, "missing_dispatcher_pid"
    identity = process_identity(pid)
    if not identity:
        return False, "dispatcher_pid_not_running"
    command = identity["command"]
    action = str(task.get("action") or "")
    task_identity = str(task.get("task_id") or "")
    if "run_war_room_service.py" not in command or not re.search(
        rf"(?:^|\s){re.escape(action)}(?:\s|$)", command
    ):
        return False, "dispatcher_pid_command_mismatch"
    recorded_start = parse_time(task.get("dispatcher_process_started_at"))
    actual_start = parse_time(identity["started_at"])
    if recorded_start and actual_start and abs((actual_start - recorded_start).total_seconds()) > 1:
        return False, "dispatcher_pid_start_time_mismatch"
    requested = parse_time(task.get("requested_at"))
    if requested and actual_start and actual_start > requested + timedelta(seconds=5):
        return False, "dispatcher_started_after_request"
    if task_identity not in command:
        trigger = str(task.get("trigger") or "")
        if requested:
            bucket = int(requested.timestamp() // 60)
            expected = f"{action}-{hashlib.sha256(f'{action}|{trigger}|{bucket}'.encode()).hexdigest()[:12]}"
            if task_identity != expected:
                return False, "dispatcher_task_id_mismatch"
        elif task.get("dispatcher_process_started_at") is None:
            return False, "dispatcher_task_identity_unverifiable"
    current = now or datetime.now(timezone.utc)
    if requested and (current - requested).total_seconds() > STALE_TASK_MAX_AGE_SECONDS:
        return False, "task_age_exceeded"
    return True, "live"


def reconcile_stale_tasks(tasks_dir: Optional[Path] = None) -> list[dict]:
    """Durably abandon stale queue records before priority/FIFO decisions."""
    tasks_dir = tasks_dir or TASKS
    abandoned = []
    for path in tasks_dir.glob("*.json"):
        task = read_json(path, {})
        if task.get("action") not in ACTION_REGISTRY_KEYS or task.get("status") not in RATINGS_PROTECTED_STATUSES:
            continue
        live, reason = dispatcher_is_live(task)
        if live:
            continue
        task.update(
            status="ABANDONED_STALE",
            completed_at=utc_now(),
            stale_reconciliation_reason=reason,
        )
        atomic_json(path, task)
        abandoned.append(task)
    return abandoned


def acquire(action: str, identity: str) -> Path:
    LOCKS.mkdir(parents=True, exist_ok=True)
    global_lock = LOCKS / "canonical-writer.lock"
    try:
        global_lock.mkdir()
    except FileExistsError:
        owner = read_json(global_lock / "owner.json", {})
        owner_task = read_json(TASKS / f"{owner.get('task_id')}.json", {})
        live, _ = dispatcher_is_live(owner_task)
        if live:
            raise RuntimeError(f"overlap blocked by running task {owner.get('task_id')}")
        if not isinstance(owner.get("pid"), int):
            raise RuntimeError("overlap blocked by canonical writer lock")
        shutil.rmtree(global_lock)
        global_lock.mkdir()
    atomic_json(global_lock / "owner.json", {"task_id": identity, "action": action, "pid": os.getpid(), "started_at": utc_now()})
    return global_lock


def live_queue(tasks_dir: Optional[Path] = None) -> list[dict]:
    """Return live writer requests in durable priority/FIFO order."""
    tasks_dir = tasks_dir or TASKS
    reconcile_stale_tasks(tasks_dir)
    queued = []
    for path in tasks_dir.glob("*.json"):
        task = read_json(path, {})
        if task.get("action") not in ACTION_REGISTRY_KEYS or task.get("status") not in LIVE_REQUEST_STATUSES:
            continue
        live, _ = dispatcher_is_live(task)
        if not live:
            continue
        queued.append(task)
    return sorted(queued, key=lambda row: (
        request_priority(row), str(row.get("requested_at") or ""), str(row.get("task_id") or ""),
    ))


def request_priority(task: dict) -> int:
    """Ratings reservations outrank queued work; running work is never preempted."""
    action = task.get("action")
    trigger = str(task.get("trigger") or "")
    if action == "ratings":
        return 0 if trigger not in {"ratings-scheduler"} else 1
    if action == "postgame":
        return 2
    if action == "market" and trigger == "ratings-catchup":
        return 3
    if action == "market" and trigger == "market-scheduler":
        return 5
    return 4


def ratings_protection_active(tasks_dir: Optional[Path] = None) -> Optional[dict]:
    """Return a live Ratings reservation covering queue wait through catch-up Market."""
    tasks_dir = tasks_dir or TASKS
    reconcile_stale_tasks(tasks_dir)
    for path in tasks_dir.glob("*.json"):
        task = read_json(path, {})
        if task.get("action") != "ratings" or task.get("status") not in RATINGS_PROTECTED_STATUSES:
            continue
        live, _ = dispatcher_is_live(task)
        if live:
            return task
    return None


def acquire_fifo(
    action: str,
    identity: str,
    *,
    timeout_seconds: float = WRITER_QUEUE_WAIT_SECONDS,
    poll_seconds: float = WRITER_QUEUE_POLL_SECONDS,
    waiting=None,
    sleeper=time.sleep,
) -> Path:
    """Acquire the writer in durable Ratings/Postgame/Market priority then FIFO order."""
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    while True:
        queue = live_queue()
        if queue and queue[0].get("task_id") == identity:
            try:
                return acquire(action, identity)
            except RuntimeError as exc:
                reason = str(exc)
        else:
            reason = f"FIFO queue position {next((i + 1 for i, row in enumerate(queue) if row.get('task_id') == identity), 1)}"
        if waiting is not None:
            waiting(reason)
        if time.monotonic() >= deadline:
            raise RuntimeError(f"writer queue timeout: {reason}")
        sleeper(max(0.01, poll_seconds))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=[*ACTION_REGISTRY_KEYS, "status"])
    parser.add_argument("--trigger", default="manual")
    parser.add_argument("--requester", default="scheduler")
    parser.add_argument("--task-id", default=None)
    parser.add_argument(
        "--rating-source",
        choices=["spplus", "fpi", "teamrankings"],
        help="Ratings only: refresh one accepted source without unrelated providers.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--prepared-results",
        action="store_true",
        help="Postgame only: schedule/results were already refreshed by the final watcher.",
    )
    args = parser.parse_args()

    if args.prepared_results and args.action != "postgame":
        parser.error("--prepared-results is valid only for postgame")
    if args.rating_source and args.action != "ratings":
        parser.error("--rating-source is valid only for ratings")
    if args.action == "status":
        print(json.dumps(read_json(LATEST, {"status": "NEVER_RUN"}), indent=2))
        return 0

    identity = args.task_id or task_id(args.action, args.trigger)
    if not re.fullmatch(r"[a-z][a-z0-9-]{5,63}", identity):
        parser.error("--task-id must be a safe lowercase task identifier")
    prior = read_json(TASKS / f"{identity}.json", {})
    if prior.get("status") in {
        "WAITING_FOR_CANONICAL_WRITER",
        "RUNNING",
        "COMPLETED",
        "COMPLETED_WITH_WARNINGS",
        "FAILED",
        "BLOCKED_BY_OVERLAP",
        "DEFERRED_BY_DAILY_BACKBONE",
        "DEFERRED_BY_MARKET_PRIORITY",
        "QUEUED_FOR_MARKET_GAP",
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
        dispatcher_pid=os.getpid(),
        dispatcher_process_started_at=(process_identity(os.getpid()) or {}).get("started_at"),
        command_owner=resolve_command(args.action)[1],
    )
    atomic_json(TASKS / f"{identity}.json", task)
    atomic_json(LATEST, task)
    if (args.action == "market" and args.trigger == "market-scheduler"
            and (reservation := ratings_protection_active())):
        task.update(
            status="COALESCED_FOR_RATINGS",
            completed_at=utc_now(),
            ratings_task_id=reservation.get("task_id"),
            waiting_reason="Market paused for Ratings; one fresh Market refresh follows Ratings",
        )
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)
        print(json.dumps(task, indent=2)); return 0
    if daily_running():
        task.update(status="DEFERRED_BY_DAILY_BACKBONE", completed_at=utc_now())
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)
        print(json.dumps(task, indent=2)); return 2
    if args.dry_run:
        task.update(status="DRY_RUN", completed_at=utc_now())
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)
        print(json.dumps(task, indent=2)); return 0

    lock = None
    ratings_started = False
    terminal_status = None
    try:
        last_wait_write = [0.0]
        def record_waiting(reason: str) -> None:
            current = time.monotonic()
            if task.get("waiting_reason") == reason and current - last_wait_write[0] < 5.0:
                return
            task.update(
                status="WAITING_FOR_CANONICAL_WRITER",
                waiting_since=task.get("waiting_since", utc_now()),
                waiting_reason=reason,
            )
            atomic_json(TASKS / f"{identity}.json", task)
            atomic_json(LATEST, task)
            last_wait_write[0] = current

        lock = acquire_fifo(args.action, identity, waiting=record_waiting)
        ratings_started = args.action == "ratings"
        task.update(
            status="RUNNING",
            started_at=utc_now(),
            queue_policy="RATINGS_PRIORITY_THEN_FIFO",
        )
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)
        command = resolve_command(args.action)
        if args.rating_source:
            command = [*command, "--providers", args.rating_source]
        if args.prepared_results:
            command = [*command, "--postgame-skip-schedule"]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=3600, check=False)
        output = (result.stdout or "") + (result.stderr or "")
        market_result = fast_market_result(output) if args.action == "market" else {}
        completed_status = (
            "COMPLETED_WITH_WARNINGS"
            if market_result.get("publication_validation_status") == "FAILED"
            else "COMPLETED"
        )
        task.update(
            status=completed_status if result.returncode == 0 else "FAILED",
            completed_at=utc_now(),
            returncode=result.returncode,
            output_tail=output[-8000:],
        )
        if market_result:
            task.update(market_result)
        terminal_status = task["status"]
    except RuntimeError as exc:
        task.update(status="BLOCKED_BY_OVERLAP", completed_at=utc_now(), error=str(exc))
    except subprocess.TimeoutExpired:
        task.update(status="FAILED", completed_at=utc_now(), error="service execution timed out")
        terminal_status = "FAILED"
    finally:
        if lock and lock.exists():
            shutil.rmtree(lock)
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)

    if ratings_started:
        # Keep the Ratings reservation live until exactly one fresh Market run has
        # followed the protected acquisition/propagation/validation/publication transaction.
        task.update(status="RATINGS_CATCHUP_MARKET", ratings_phase="Market resumed")
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)
        catchup_id = f"market-after-ratings-{hashlib.sha256(identity.encode()).hexdigest()[:12]}"
        try:
            catchup = subprocess.run(
                [sys.executable, "scripts/control/run_war_room_service.py", "market",
                 "--trigger", "ratings-catchup", "--requester", "ratings-controller",
                 "--task-id", catchup_id],
                cwd=ROOT, text=True, capture_output=True, timeout=3600, check=False,
            )
            catchup_returncode = catchup.returncode
        except subprocess.TimeoutExpired:
            catchup_returncode = 2
        catchup_task = read_json(TASKS / f"{catchup_id}.json", {})
        task.update(
            status=terminal_status or task.get("status", "FAILED"),
            catchup_market_task_id=catchup_id,
            catchup_market_status=catchup_task.get("status", "FAILED"),
            catchup_market_returncode=catchup_returncode,
            completed_at=utc_now(),
        )
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)
    print(json.dumps(task, indent=2))
    return 0 if task["status"] in {"COMPLETED", "COMPLETED_WITH_WARNINGS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
