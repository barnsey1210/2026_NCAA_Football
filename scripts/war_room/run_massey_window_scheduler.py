#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "data/control/massey_window_state.json"
REPORT = ROOT / "data/control/massey_background_refresh.json"
TZ = ZoneInfo("America/New_York")


def now_et():
    return datetime.now(TZ)


def load(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def current_window(now):
    if now.weekday() == 5:
        return "SATURDAY"
    if now.weekday() == 6:
        return "SUNDAY"
    return None


def same_et_date(timestamp, now):
    if not timestamp:
        return False
    try:
        parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        return parsed.astimezone(TZ).date() == now.date()
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trigger", default="scheduled-window")
    args = parser.parse_args()

    now = now_et()
    window = current_window(now)

    if not window:
        print(json.dumps({
            "status": "OUTSIDE_MASSEY_WINDOW_DAY",
            "now_et": now.isoformat(),
        }, indent=2))
        return 0

    state = load(STATE, {"schema_version": 1, "windows": {}})
    windows = state.setdefault("windows", {})
    key = f"{window}:{now.date().isoformat()}"
    record = windows.get(key) or {}

    if record.get("status") == "CAPTURED":
        print(json.dumps({
            "status": "WINDOW_ALREADY_CAPTURED",
            "window": window,
            "date": now.date().isoformat(),
            "captured_at": record.get("captured_at"),
        }, indent=2))
        return 0

    previous_report = load(REPORT, {})

    if (
        previous_report.get("status") == "UPDATED_AND_PROPAGATED"
        and same_et_date(previous_report.get("completed_at"), now)
    ):
        windows[key] = {
            "status": "CAPTURED",
            "captured_at": previous_report.get("completed_at"),
            "source": "existing-successful-massey-refresh",
        }
        write(STATE, state)
        print(json.dumps({
            "status": "WINDOW_CAPTURED_FROM_EXISTING_REFRESH",
            "window": window,
            "date": now.date().isoformat(),
        }, indent=2))
        return 0

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

    report = load(REPORT, {})

    record = {
        "status": "PENDING",
        "last_checked_at": report.get("completed_at"),
        "last_worker_status": report.get("status"),
        "last_changed": report.get("changed"),
        "trigger": args.trigger,
    }

    if report.get("status") == "UPDATED_AND_PROPAGATED":
        record["status"] = "CAPTURED"
        record["captured_at"] = report.get("completed_at")

    windows[key] = record
    state["updated_at"] = datetime.now(TZ).isoformat()
    write(STATE, state)

    print(json.dumps({
        "window": window,
        "date": now.date().isoformat(),
        "worker_returncode": result.returncode,
        "worker_status": report.get("status"),
        "changed": report.get("changed"),
        "window_status": record["status"],
    }, indent=2))

    return 0 if result.returncode == 0 else result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
