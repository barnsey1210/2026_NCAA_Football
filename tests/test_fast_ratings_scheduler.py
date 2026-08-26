#!/usr/bin/env python3
import importlib.util
import json
import plistlib
import subprocess
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fast_ratings_scheduler", ROOT / "scripts/war_room/run_fast_ratings_scheduler.py"
)
SCHEDULER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCHEDULER)
ET = ZoneInfo("America/New_York")


class FastRatingsSchedulerTests(unittest.TestCase):
    def run_at(self, value, task_status="COMPLETED", output_tail=""):
        calls = []

        def runner(command):
            calls.append(command)
            task = {"task_id": command[-1], "status": task_status,
                    "output_tail": output_tail}
            code = 0 if task_status == "COMPLETED" else 2
            return subprocess.CompletedProcess(command, code, json.dumps(task), "")

        code, report = SCHEDULER.execute(now=value, runner=runner)
        return code, report, calls

    def test_window_boundaries_and_zero_dispatch_outside(self):
        cases = [
            (datetime(2026, 8, 29, 23, 30, tzinfo=ET), False),
            (datetime(2026, 8, 30, 0, 0, tzinfo=ET), True),
            (datetime(2026, 8, 30, 15, 0, tzinfo=ET), True),
            (datetime(2026, 8, 31, 11, 30, tzinfo=ET), True),
            (datetime(2026, 8, 31, 12, 0, tzinfo=ET), True),
            (datetime(2026, 8, 31, 12, 30, tzinfo=ET), False),
        ]
        for value, inside in cases:
            with self.subTest(value=value):
                code, report, calls = self.run_at(value)
                self.assertEqual(code, 0)
                self.assertEqual(bool(calls), inside)
                expected = "INSIDE_RATINGS_WINDOW" if inside else "OUTSIDE_RATINGS_WINDOW"
                self.assertEqual(report["window_status"], expected)

    def test_dispatches_existing_ratings_service_exactly_once(self):
        _, report, calls = self.run_at(datetime(2026, 8, 30, 2, 0, tzinfo=ET))
        self.assertEqual(len(calls), 1)
        self.assertIn("scripts/control/run_war_room_service.py", calls[0])
        self.assertIn("ratings", calls[0])
        self.assertEqual(report["trigger"], "ratings-scheduler")

    def test_no_change_is_preserved_without_scheduler_build_logic(self):
        _, report, _ = self.run_at(
            datetime(2026, 8, 30, 2, 30, tzinfo=ET),
            output_tail='{"status": "NO_CHANGES"}',
        )
        self.assertEqual(report["status"], "NO_CHANGES")

    def test_daily_and_canonical_writer_deferrals_are_clean(self):
        cases = ["DEFERRED_BY_DAILY_BACKBONE", "BLOCKED_BY_OVERLAP"]
        for status in cases:
            with self.subTest(status=status):
                code, report, calls = self.run_at(
                    datetime(2026, 8, 30, 8, 0, tzinfo=ET), status
                )
                self.assertEqual(code, 0)
                self.assertEqual(len(calls), 1)
                self.assertEqual(report["status"], status)
                self.assertTrue(report["deferred_reason"])

    def test_scheduler_has_no_provider_or_authority_calculation(self):
        source = (ROOT / "scripts/war_room/run_fast_ratings_scheduler.py").read_text()
        for forbidden in ("TeamRankings", "DRatings", "Massey", "HYBRID",
                          "OFFICIAL", "0.20", "0.40"):
            self.assertNotIn(forbidden, source)

    def test_manual_and_automatic_paths_share_dispatcher(self):
        api = (ROOT / "scripts/war_room/war_room_operator_api.py").read_text()
        scheduler = (ROOT / "scripts/war_room/run_fast_ratings_scheduler.py").read_text()
        self.assertIn('@app.post("/war-room/ratings"', api)
        self.assertIn('"scripts/control/run_war_room_service.py"', api)
        self.assertIn('"scripts/control/run_war_room_service.py"', scheduler)

    def test_launchagent_is_dumb_thirty_minute_timer(self):
        path = ROOT / "deploy/launchagents/com.jim.ncaaf.fast-ratings.plist"
        with path.open("rb") as handle:
            plist = plistlib.load(handle)
        self.assertEqual(plist["StartInterval"], 1800)
        self.assertNotIn("StartCalendarInterval", plist)
        self.assertNotIn("RunAtLoad", plist)
        self.assertEqual(
            plist["ProgramArguments"][1],
            "/Users/jameslindesmith/NCAAF_AUTO/scripts/war_room/start_fast_ratings_scheduler.sh",
        )


if __name__ == "__main__":
    unittest.main()
