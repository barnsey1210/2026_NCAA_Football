#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "war_room_dispatcher_anti_starvation",
    ROOT / "scripts/control/run_war_room_service.py",
)
DISPATCHER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DISPATCHER)


class RatingsMarketAntiStarvationTests(unittest.TestCase):
    def configure(self, root: Path):
        control = root / "services"
        tasks = control / "tasks"
        tasks.mkdir(parents=True)
        registry = root / "registry.json"
        registry.write_text(json.dumps({"actions": {
            key: {"controller_mode": mode} for key, mode in {
                "MARKET_REFRESH": "war-room-market",
                "FUTURES_REFRESH": "futures-fast",
                "RATINGS_REFRESH": "ratings",
                "POSTGAME_REFRESH": "postgame",
                "WAR_ROOM_REBUILD": "war-room-rebuild",
            }.items()
        }}))
        patches = [
            mock.patch.object(DISPATCHER, "ROOT", root),
            mock.patch.object(DISPATCHER, "CONTROL", control),
            mock.patch.object(DISPATCHER, "LOCKS", control / "locks"),
            mock.patch.object(DISPATCHER, "TASKS", tasks),
            mock.patch.object(DISPATCHER, "LATEST", control / "latest.json"),
            mock.patch.object(DISPATCHER, "DAILY_STATUS", root / "daily.json"),
            mock.patch.object(DISPATCHER, "REGISTRY", registry),
        ]
        return tasks, patches

    def test_manual_then_scheduled_ratings_outrank_postgame_and_recurring_market(self):
        rows = [
            {"action": "market", "trigger": "market-scheduler"},
            {"action": "postgame", "trigger": "cfbd-final-watcher"},
            {"action": "ratings", "trigger": "ratings-scheduler"},
            {"action": "ratings", "trigger": "cloudflare-access"},
        ]
        self.assertEqual([DISPATCHER.request_priority(row) for row in rows], [5, 2, 1, 0])

    def test_live_queue_applies_priority_then_fifo_without_preempting_lock_owner(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = Path(tmp)
            for name, action, trigger, requested in (
                ("market", "market", "market-scheduler", "2026-09-26T01:00:00Z"),
                ("postgame", "postgame", "cfbd-final-watcher", "2026-09-26T01:00:01Z"),
                ("ratings", "ratings", "ratings-scheduler", "2026-09-26T01:00:02Z"),
            ):
                (tasks / f"{name}.json").write_text(json.dumps({
                    "task_id": name, "action": action, "trigger": trigger,
                    "requested_at": requested, "status": "REQUESTED",
                    "dispatcher_pid": os.getpid(),
                }))
            with mock.patch.object(DISPATCHER, "dispatcher_is_live", return_value=(True, "live")):
                self.assertEqual([row["task_id"] for row in DISPATCHER.live_queue(tasks)],
                                 ["ratings", "postgame", "market"])

    def test_dead_pid_is_abandoned_and_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks = Path(tmp)
            path = tasks / "dead.json"
            path.write_text(json.dumps({"task_id": "dead", "action": "market", "status": "REQUESTED", "dispatcher_pid": 99999999}))
            self.assertEqual(DISPATCHER.live_queue(tasks), [])
            self.assertEqual(json.loads(path.read_text())["status"], "ABANDONED_STALE")

    def test_reused_pid_with_unrelated_command_is_abandoned(self):
        task = {"task_id": "market-reused", "action": "market", "status": "RUNNING", "dispatcher_pid": 13129}
        with mock.patch.object(DISPATCHER, "process_identity", return_value={"started_at": "2026-09-29T12:00:00+00:00", "command": "/System/Library/callservicesd"}):
            self.assertEqual(DISPATCHER.dispatcher_is_live(task), (False, "dispatcher_pid_command_mismatch"))

    def test_stale_task_age_is_rejected_even_when_process_matches(self):
        task = {"task_id": "market-stale", "action": "market", "trigger": "manual", "status": "REQUESTED",
                "dispatcher_pid": 123, "requested_at": "2026-09-01T00:00:00+00:00",
                "dispatcher_process_started_at": "2026-09-01T00:00:00+00:00"}
        with mock.patch.object(DISPATCHER, "process_identity", return_value={"started_at": "2026-09-01T00:00:00+00:00", "command": "python scripts/control/run_war_room_service.py market --task-id market-stale"}):
            live, reason = DISPATCHER.dispatcher_is_live(task, now=DISPATCHER.parse_time("2026-10-02T00:00:00Z"))
        self.assertFalse(live)
        self.assertEqual(reason, "task_age_exceeded")

    def test_legitimate_active_dispatcher_identity_is_live(self):
        task = {"task_id": "market-live", "action": "market", "trigger": "manual", "status": "REQUESTED",
                "dispatcher_pid": 123, "requested_at": "2026-10-02T15:00:00+00:00",
                "dispatcher_process_started_at": "2026-10-02T14:59:59+00:00"}
        with mock.patch.object(DISPATCHER, "process_identity", return_value={"started_at": "2026-10-02T14:59:59+00:00", "command": "python scripts/control/run_war_room_service.py market --task-id market-live"}):
            self.assertEqual(DISPATCHER.dispatcher_is_live(task, now=DISPATCHER.parse_time("2026-10-02T15:01:00Z")), (True, "live"))

    def test_repeated_market_ticks_during_ratings_create_no_pending_backlog(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks, patches = self.configure(Path(tmp))
            (tasks / "ratings-live.json").write_text(json.dumps({
                "task_id": "ratings-live", "action": "ratings", "trigger": "ratings-scheduler",
                "status": "RUNNING", "dispatcher_pid": os.getpid(),
            }))
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], \
                    mock.patch.object(DISPATCHER, "dispatcher_is_live", return_value=(True, "live")):
                for identity in ("market-tick-one", "market-tick-two"):
                    with mock.patch.object(sys, "argv", ["run_war_room_service.py", "market",
                            "--trigger", "market-scheduler", "--task-id", identity]):
                        self.assertEqual(DISPATCHER.main(), 0)
            market = [json.loads(path.read_text()) for path in tasks.glob("market-*.json")]
            self.assertEqual([row["status"] for row in market],
                             ["COALESCED_FOR_RATINGS", "COALESCED_FOR_RATINGS"])
            self.assertFalse(any(row["status"] in DISPATCHER.LIVE_REQUEST_STATUSES for row in market))

    def test_ratings_lock_covers_service_and_exactly_one_catchup_runs_on_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks, patches = self.configure(Path(tmp))
            calls = []
            def run(command, **kwargs):
                calls.append(command)
                if any(part.endswith("run_data_refresh.py") for part in command):
                    self.assertTrue((DISPATCHER.LOCKS / "canonical-writer.lock").exists())
                    return subprocess.CompletedProcess(command, 0, "", "")
                catchup_id = command[-1]
                (tasks / f"{catchup_id}.json").write_text(json.dumps({"status": "COMPLETED"}))
                return subprocess.CompletedProcess(command, 0, "", "")
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], \
                    mock.patch.object(DISPATCHER.subprocess, "run", side_effect=run), \
                    mock.patch.object(DISPATCHER, "dispatcher_is_live", return_value=(True, "live")), \
                    mock.patch.object(DISPATCHER, "process_identity", return_value={"started_at": "2026-10-02T15:00:00+00:00", "command": "dispatcher"}), \
                    mock.patch.object(sys, "argv", ["run_war_room_service.py", "ratings",
                                                    "--task-id", "ratings-success"]):
                self.assertEqual(DISPATCHER.main(), 0)
            task = json.loads((tasks / "ratings-success.json").read_text())
            self.assertEqual((task["status"], task["catchup_market_status"], len(calls)),
                             ("COMPLETED", "COMPLETED", 2))
            self.assertFalse((DISPATCHER.LOCKS / "canonical-writer.lock").exists())

    def test_ratings_failure_releases_lock_and_still_runs_one_catchup(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks, patches = self.configure(Path(tmp))
            calls = []
            def run(command, **kwargs):
                calls.append(command)
                if any(part.endswith("run_data_refresh.py") for part in command):
                    return subprocess.CompletedProcess(command, 2, "provider failed", "")
                catchup_id = command[-1]
                (tasks / f"{catchup_id}.json").write_text(json.dumps({"status": "COMPLETED"}))
                return subprocess.CompletedProcess(command, 0, "", "")
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], \
                    mock.patch.object(DISPATCHER.subprocess, "run", side_effect=run), \
                    mock.patch.object(DISPATCHER, "dispatcher_is_live", return_value=(True, "live")), \
                    mock.patch.object(DISPATCHER, "process_identity", return_value={"started_at": "2026-10-02T15:00:00+00:00", "command": "dispatcher"}), \
                    mock.patch.object(sys, "argv", ["run_war_room_service.py", "ratings",
                                                    "--task-id", "ratings-failed"]):
                self.assertEqual(DISPATCHER.main(), 2)
            task = json.loads((tasks / "ratings-failed.json").read_text())
            self.assertEqual((task["status"], task["catchup_market_status"], len(calls)),
                             ("FAILED", "COMPLETED", 2))
            self.assertFalse((DISPATCHER.LOCKS / "canonical-writer.lock").exists())


if __name__ == "__main__":
    unittest.main()
