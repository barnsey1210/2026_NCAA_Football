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
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "data/control/war_room_services"
LOCKS = CONTROL / "locks"
TASKS = CONTROL / "tasks"
LATEST = CONTROL / "latest.json"
DAILY_STATUS = ROOT / "data/control/daily_run_status.json"
MARKET_SCHEDULER_LATEST = ROOT / "data/control/market_scheduler/latest.json"
REGISTRY = ROOT / "scripts/control/refresh_stage_registry.json"
POSTGAME_LOCK_WAIT_SECONDS = 900
POSTGAME_LOCK_POLL_SECONDS = 1.0
POSTGAME_TARGET_SECONDS = 30
POSTGAME_SAFETY_SECONDS = 15
POSTGAME_REQUIRED_GAP_SECONDS = POSTGAME_TARGET_SECONDS + POSTGAME_SAFETY_SECONDS
MARKET_SCHEDULER_STALE_SECONDS = 45
MARKET_LOCK_WAIT_SECONDS = 900
ET = ZoneInfo("America/New_York")

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


def acquire_with_priority(
    action: str,
    identity: str,
    *,
    timeout_seconds: float = POSTGAME_LOCK_WAIT_SECONDS,
    poll_seconds: float = POSTGAME_LOCK_POLL_SECONDS,
    waiting=None,
    sleeper=time.sleep,
) -> Path:
    """Queue Market/Postgame visibly instead of rejecting an accepted task."""
    if action not in {"market", "postgame"}:
        return acquire(action, identity)
    if action == "market":
        timeout_seconds = max(timeout_seconds, MARKET_LOCK_WAIT_SECONDS)
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    while True:
        try:
            return acquire(action, identity)
        except RuntimeError as exc:
            if time.monotonic() >= deadline:
                raise
            if waiting is not None:
                waiting(str(exc))
            sleeper(max(0.01, poll_seconds))


def high_frequency_market_band(now: datetime | None = None) -> bool:
    """Whether live cadence owns the canonical writer ahead of Postgame."""
    local = (now or datetime.now(timezone.utc)).astimezone(ET)
    seconds = local.hour * 3600 + local.minute * 60 + local.second
    if local.weekday() == 5:
        return seconds >= 22 * 3600
    if local.weekday() == 6:
        return seconds < 23 * 3600
    return False


def parse_utc(value) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def postgame_market_gap(
    now: datetime | None = None,
    latest_path: Path = MARKET_SCHEDULER_LATEST,
) -> dict:
    """Return conservative Postgame admission state for the live Market cadence."""
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if not high_frequency_market_band(current):
        return {
            "allowed": True,
            "reason": "outside high-frequency Market cadence",
            "next_market_due_at": None,
            "market_gap_seconds": None,
            "required_gap_seconds": POSTGAME_REQUIRED_GAP_SECONDS,
        }
    latest = read_json(latest_path, {})
    checked_at = parse_utc(latest.get("checked_at"))
    next_due = parse_utc(latest.get("next_due_at"))
    if checked_at is None or next_due is None:
        return {
            "allowed": False,
            "reason": "Market scheduler deadline is unavailable",
            "next_market_due_at": None,
            "market_gap_seconds": None,
            "required_gap_seconds": POSTGAME_REQUIRED_GAP_SECONDS,
        }
    scheduler_age = max(0.0, (current - checked_at).total_seconds())
    gap = (next_due - current).total_seconds()
    allowed = (
        scheduler_age <= MARKET_SCHEDULER_STALE_SECONDS
        and gap >= POSTGAME_REQUIRED_GAP_SECONDS
        and str(latest.get("status")) == "NOT_DUE"
    )
    if scheduler_age > MARKET_SCHEDULER_STALE_SECONDS:
        reason = "Market scheduler deadline is stale"
    elif str(latest.get("status")) != "NOT_DUE":
        reason = f"Market scheduler status is {latest.get('status') or 'UNKNOWN'}"
    elif gap < POSTGAME_REQUIRED_GAP_SECONDS:
        reason = "insufficient slack before next Market due time"
    else:
        reason = "safe Market gap is open"
    return {
        "allowed": allowed,
        "reason": reason,
        "next_market_due_at": next_due.isoformat(),
        "market_gap_seconds": round(gap, 3),
        "required_gap_seconds": POSTGAME_REQUIRED_GAP_SECONDS,
        "market_scheduler_checked_at": checked_at.isoformat(),
    }


def live_market_request_pending(tasks_dir: Path = TASKS) -> bool:
    """Give a live Market dispatcher admission priority over Postgame."""
    try:
        paths = tasks_dir.glob("*.json")
    except OSError:
        return False
    for path in paths:
        task = read_json(path, {})
        if task.get("action") != "market" or task.get("status") not in {
            "REQUESTED", "WAITING_FOR_CANONICAL_WRITER", "RUNNING",
        }:
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


def acquire_postgame_in_market_gap(
    identity: str,
    *,
    timeout_seconds: float = POSTGAME_LOCK_WAIT_SECONDS,
    poll_seconds: float = POSTGAME_LOCK_POLL_SECONDS,
    waiting=None,
    gap_reader=postgame_market_gap,
    market_pending=live_market_request_pending,
    sleeper=time.sleep,
) -> tuple[Path, dict]:
    """Admit Postgame only while its reserved runtime fits before Market is due."""
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    while True:
        gap = gap_reader()
        if market_pending():
            gap = {**gap, "allowed": False, "reason": "live Market request has admission priority"}
        if gap.get("allowed"):
            try:
                lock = acquire("postgame", identity)
            except RuntimeError as exc:
                gap = {**gap, "allowed": False, "reason": str(exc)}
            else:
                # Close the check/acquire race: never start from a deadline that
                # became unsafe while the canonical writer lock was contended.
                confirmed = gap_reader()
                if market_pending():
                    confirmed = {
                        **confirmed,
                        "allowed": False,
                        "reason": "live Market request has admission priority",
                    }
                if confirmed.get("allowed"):
                    return lock, confirmed
                if lock.exists():
                    shutil.rmtree(lock)
                gap = confirmed
        if waiting is not None:
            waiting(gap)
        if time.monotonic() >= deadline:
            raise RuntimeError(
                "no safe Market gap opened before Postgame queue timeout: "
                + str(gap.get("reason") or "unknown reason")
            )
        sleeper(max(0.01, poll_seconds))


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
        def record_waiting(reason: str) -> None:
            task.update(
                status="WAITING_FOR_CANONICAL_WRITER",
                waiting_since=task.get("waiting_since", utc_now()),
                waiting_reason=reason,
            )
            atomic_json(TASKS / f"{identity}.json", task)
            atomic_json(LATEST, task)

        if args.action == "postgame":
            def record_gap_wait(gap: dict) -> None:
                task.update(
                    status="QUEUED_FOR_MARKET_GAP",
                    queued_since=task.get("queued_since", utc_now()),
                    queue_reason=gap.get("reason"),
                    next_market_due_at=gap.get("next_market_due_at"),
                    market_gap_seconds=gap.get("market_gap_seconds"),
                    required_gap_seconds=gap.get("required_gap_seconds"),
                )
                atomic_json(TASKS / f"{identity}.json", task)
                atomic_json(LATEST, task)

            lock, admitted_gap = acquire_postgame_in_market_gap(
                identity,
                waiting=record_gap_wait,
            )
        else:
            lock = acquire_with_priority(
                args.action,
                identity,
                waiting=record_waiting,
            )
            admitted_gap = {}
        task.update(
            status="RUNNING",
            started_at=utc_now(),
            admitted_market_gap=admitted_gap or None,
        )
        atomic_json(TASKS / f"{identity}.json", task); atomic_json(LATEST, task)
        command = resolve_command(args.action)
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
