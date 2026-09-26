#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MASSEY = ROOT / "data/ratings/external_sources/massey_game_projections_2026.csv"
LOCK = ROOT / "data/control/massey_background.lock"
REPORT = ROOT / "data/control/massey_background_refresh.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def digest(path: Path) -> str | None:
    if not path.exists():
        return None

    with path.open(newline="", errors="ignore") as handle:
        rows = list(csv.DictReader(handle))

    volatile = {"pulled_at", "snapshot_date", "source_file"}
    stable = [
        {key: value for key, value in row.items() if key not in volatile}
        for row in rows
    ]
    stable.sort(key=lambda row: json.dumps(row, sort_keys=True))

    return hashlib.sha256(
        json.dumps(stable, sort_keys=True).encode()
    ).hexdigest()


def acquire_lock() -> None:
    LOCK.parent.mkdir(parents=True, exist_ok=True)

    try:
        LOCK.mkdir()
    except FileExistsError:
        owner = {}
        try:
            owner = json.loads((LOCK / "owner.json").read_text())
        except Exception:
            pass

        pid = owner.get("pid")

        if isinstance(pid, int):
            try:
                os.kill(pid, 0)
                raise RuntimeError(
                    f"Massey refresh already running under pid {pid}"
                )
            except ProcessLookupError:
                shutil.rmtree(LOCK)
                LOCK.mkdir()
        else:
            raise RuntimeError(
                "Massey refresh lock exists with unknown owner"
            )

    atomic_json(
        LOCK / "owner.json",
        {
            "pid": os.getpid(),
            "started_at": utc_now(),
        },
    )


def extract_service_status(stdout: str) -> str | None:
    try:
        payload = json.loads(stdout)
        if isinstance(payload, dict):
            return str(payload.get("status") or "") or None
    except (TypeError, ValueError):
        pass
    return None


def main() -> int:
    started = time.monotonic()

    prior_report = {}
    try:
        prior_report = json.loads(REPORT.read_text()) if REPORT.exists() else {}
    except Exception:
        prior_report = {}

    report = {
        "schema_version": 1,
        "started_at": utc_now(),
        "completed_at": None,
        "status": "STARTING",
        "changed": False,
        "before_fingerprint": None,
        "after_fingerprint": None,
        "crawl_returncode": None,
        "ratings_triggered": False,
        "ratings_returncode": None,
        "ratings_status": None,
        "elapsed_seconds": None,
        "last_changed_at": prior_report.get("last_changed_at"),
        "last_model_applied_at": prior_report.get("last_model_applied_at"),
    }

    try:
        acquire_lock()
    except RuntimeError as exc:
        report.update(
            status="ALREADY_RUNNING",
            error=str(exc),
            completed_at=utc_now(),
            elapsed_seconds=round(time.monotonic() - started, 3),
        )
        atomic_json(REPORT, report)
        print(json.dumps(report, indent=2))
        return 0

    try:
        before = digest(MASSEY)
        report["before_fingerprint"] = before
        report["status"] = "CRAWLING"

        crawl = subprocess.run(
            [
                sys.executable,
                "scripts/projections/refresh_massey_game_projections_2026.py",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=600,
            check=False,
        )

        report["crawl_returncode"] = crawl.returncode
        report["crawl_output_tail"] = (
            (crawl.stdout or "") + (crawl.stderr or "")
        )[-8000:]

        if crawl.returncode != 0:
            report["status"] = "CRAWL_FAILED"
            return 2

        after = digest(MASSEY)
        report["after_fingerprint"] = after

        changed = (
            before is not None
            and after is not None
            and before != after
        )

        report["changed"] = changed

        if not changed:
            report["status"] = "NO_CHANGE"
            return 0

        report["last_changed_at"] = utc_now()
        report["status"] = "UPDATED_PENDING_PROPAGATION"

        ratings = subprocess.run(
            [
                sys.executable,
                "scripts/control/run_war_room_service.py",
                "ratings",
                "--trigger",
                "massey-background",
                "--requester",
                "massey-background",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=600,
            check=False,
        )

        report["ratings_triggered"] = True
        report["ratings_returncode"] = ratings.returncode
        report["ratings_status"] = extract_service_status(
            ratings.stdout or ""
        )
        report["ratings_output_tail"] = (
            (ratings.stdout or "") + (ratings.stderr or "")
        )[-8000:]

        deferred_statuses = {
            "DEFERRED_BY_DAILY_BACKBONE",
            "DEFERRED_BY_MARKET_PRIORITY",
            "BLOCKED_BY_OVERLAP",
            "WAITING_FOR_CANONICAL_WRITER",
            "QUEUED_FOR_MARKET_GAP",
        }

        if report["ratings_status"] in deferred_statuses:
            report["status"] = "UPDATED_PROPAGATION_DEFERRED"
            return 0

        if (
            ratings.returncode == 0
            and report["ratings_status"] in {
                "COMPLETED",
                "COMPLETED_WITH_WARNINGS",
            }
        ):
            report["status"] = "UPDATED_AND_PROPAGATED"
            report["last_model_applied_at"] = utc_now()
            return 0

        report["status"] = "UPDATED_PROPAGATION_FAILED"
        return 2

    finally:
        report["completed_at"] = utc_now()
        report["elapsed_seconds"] = round(
            time.monotonic() - started,
            3,
        )

        atomic_json(REPORT, report)

        if LOCK.exists():
            shutil.rmtree(LOCK)

        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
