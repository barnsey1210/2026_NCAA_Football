#!/usr/bin/env python3
import importlib.util
import json
import plistlib
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fast_market_scheduler", ROOT / "scripts/war_room/run_fast_market_scheduler.py"
)
SCHEDULER = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(SCHEDULER)
ET = ZoneInfo("America/New_York")


class FastMarketSchedulerTests(unittest.TestCase):
    def run_at(self, now, state=None, success=None, task_status="COMPLETED", output=""):
        calls = []
        def runner(command):
            calls.append(command)
            task = {"task_id": command[-1], "status": task_status, "output_tail": output}
            return subprocess.CompletedProcess(command, 0 if task_status == "COMPLETED" else 2,
                                               json.dumps(task), "")
        code, report, updated = SCHEDULER.execute(
            now=now, state=state or {}, market_success_at=success, runner=runner
        )
        return code, report, updated, calls

    def test_locked_cadence_boundaries(self):
        cases = [
            (datetime(2026, 8, 31, 0, 0, tzinfo=ET), "ROUTINE_HOURLY", 3600),
            (datetime(2026, 9, 5, 21, 59, tzinfo=ET), "ROUTINE_HOURLY", 3600),
            (datetime(2026, 9, 5, 22, 0, tzinfo=ET), "SATURDAY_RAMP_5M", 300),
            (datetime(2026, 9, 5, 23, 0, tzinfo=ET), "SATURDAY_OPENER_90S", 90),
            (datetime(2026, 9, 6, 1, 59, tzinfo=ET), "SATURDAY_OPENER_90S", 90),
            (datetime(2026, 9, 6, 2, 0, tzinfo=ET), "SUNDAY_OVERNIGHT_5M", 300),
            (datetime(2026, 9, 6, 8, 0, tzinfo=ET), "SUNDAY_ACTIVE_2M", 120),
            (datetime(2026, 9, 6, 23, 0, tzinfo=ET), "SUNDAY_TRANSITION_HOURLY", 3600),
        ]
        for value, band, interval in cases:
            with self.subTest(value=value): self.assertEqual(SCHEDULER.cadence(value), (band, interval))

    def test_routine_due_and_not_due(self):
        now = datetime(2026, 8, 31, 14, 0, tzinfo=ET)
        _, due, updated, calls = self.run_at(now)
        self.assertEqual((due["status"], len(calls)), ("COMPLETED", 1))
        _, early, _, calls = self.run_at(now + timedelta(minutes=30), updated)
        self.assertEqual((early["status"], calls), ("NOT_DUE", []))

    def test_routine_recent_manual_or_daily_success_suppresses_slot(self):
        now = datetime(2026, 8, 31, 14, 0, tzinfo=ET)
        state = {"last_due_handled_at": (now - timedelta(hours=1)).isoformat()}
        _, report, updated, calls = self.run_at(now, state, now - timedelta(minutes=3))
        self.assertEqual((report["status"], calls), ("SUPPRESSED_RECENT_REFRESH", []))
        self.assertEqual(updated["last_status"], "SUPPRESSED_RECENT_REFRESH")

    def test_daily_market_stage_participates_in_recent_success_detection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            health = root / "health.json"; daily = root / "daily.json"
            health.write_text(json.dumps({"fast_market_refresh": {
                "last_fast_pull_at": "2026-08-31T16:00:00Z"}}))
            daily.write_text(json.dumps({"stages": [{"id": "game_market_acquisition",
                "status": "PASSED", "finished_at_utc": "2026-08-31T17:57:00Z"}]}))
            self.assertEqual(
                SCHEDULER.latest_market_success(health, daily).isoformat(),
                "2026-08-31T17:57:00+00:00",
            )

    def test_90_second_and_two_minute_due_gating(self):
        cases = [
            (datetime(2026, 9, 5, 23, 10, tzinfo=ET), 90),
            (datetime(2026, 9, 6, 10, 0, tzinfo=ET), 120),
        ]
        for now, interval in cases:
            with self.subTest(interval=interval):
                state = {"last_due_handled_at": (now - timedelta(seconds=interval - 1)).isoformat()}
                _, early, _, calls = self.run_at(now, state)
                self.assertEqual((early["status"], calls), ("NOT_DUE", []))
                state["last_due_handled_at"] = (now - timedelta(seconds=interval)).isoformat()
                _, due, updated, calls = self.run_at(now, state)
                self.assertEqual((due["status"], len(calls)), ("COMPLETED", 1))
                expected = now.astimezone(ET) + timedelta(seconds=interval)
                self.assertEqual(SCHEDULER.parse_time(due["next_due_at"]), expected.astimezone(SCHEDULER.timezone.utc))
                self.assertEqual(updated["last_due_handled_at"], SCHEDULER.iso(now))

    def test_missed_intervals_dispatch_at_most_once_and_restart_deduplicates(self):
        now = datetime(2026, 9, 6, 10, 0, tzinfo=ET)
        old = {"last_due_handled_at": (now - timedelta(hours=3)).isoformat()}
        _, report, updated, calls = self.run_at(now, old)
        self.assertEqual((report["status"], len(calls)), ("COMPLETED", 1))
        _, restarted, _, calls = self.run_at(now + timedelta(seconds=30), updated)
        self.assertEqual((restarted["status"], calls), ("NOT_DUE", []))

    def test_daily_writer_and_other_writer_blocks_retry_without_advancing_due(self):
        now = datetime(2026, 9, 6, 10, 0, tzinfo=ET)
        for status in ("DEFERRED_BY_DAILY_BACKBONE", "BLOCKED_BY_OVERLAP"):
            with self.subTest(status=status):
                _, report, updated, calls = self.run_at(now, task_status=status)
                self.assertEqual((report["status"], len(calls)), (status, 1))
                self.assertNotIn("last_due_handled_at", updated)

    def test_quota_block_is_owned_by_existing_market_service(self):
        now = datetime(2026, 8, 31, 14, 0, tzinfo=ET)
        _, report, _, calls = self.run_at(
            now, task_status="FAILED", output="Fast publication quota preflight unavailable"
        )
        self.assertEqual((report["status"], len(calls)), ("BLOCKED_BY_QUOTA", 1))

    def test_manual_and_automatic_market_share_service_and_owner(self):
        api = (ROOT / "scripts/war_room/war_room_operator_api.py").read_text()
        dispatcher = (ROOT / "scripts/control/run_war_room_service.py").read_text()
        scheduler = (ROOT / "scripts/war_room/run_fast_market_scheduler.py").read_text()
        self.assertIn('@app.post("/war-room/market"', api)
        self.assertIn('"scripts/control/run_war_room_service.py"', api)
        self.assertIn('"scripts/control/run_war_room_service.py"', scheduler)
        self.assertIn('"war-room-market": [sys.executable, "scripts/war_room/run_fast_market_publication.py"]', dispatcher)

    def test_scheduler_has_no_provider_or_browser_logic(self):
        source = (ROOT / "scripts/war_room/run_fast_market_scheduler.py").read_text()
        for forbidden in ("api.the-odds-api.com", "THE_ODDS_API_KEY", "urllib.request",
                          "spreads,totals", "fetch("):
            self.assertNotIn(forbidden, source)

    def test_launchagent_is_dumb_thirty_second_timer(self):
        with (ROOT / "deploy/launchagents/com.jim.ncaaf.fast-market.plist").open("rb") as handle:
            plist = plistlib.load(handle)
        self.assertEqual(plist["StartInterval"], 30)
        self.assertNotIn("StartCalendarInterval", plist)
        self.assertNotIn("RunAtLoad", plist)


if __name__ == "__main__": unittest.main()
