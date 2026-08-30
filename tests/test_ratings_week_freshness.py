#!/usr/bin/env python3
import subprocess
import sys
import unittest
import tempfile
from pathlib import Path

import pandas as pd

from scripts.ratings.freshness_evidence import (
    accepted_after_cutoff,
    completed_week_cutoffs,
)
from scripts.ratings.accept_live_rating_candidates_with_status import compare_source


class RatingsWeekFreshnessTests(unittest.TestCase):
    def test_status_acceptor_loads_helper_when_executed_directly(self):
        root = Path(__file__).resolve().parents[1]
        script = root / "scripts/ratings/accept_live_rating_candidates_with_status.py"
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)
        self.assertIn("--sources", result.stdout)

    def test_ratings_owner_persists_accepted_update_across_no_change(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            accepted = root / "accepted.csv"
            candidate = root / "candidate.csv"
            pd.DataFrame([{"team": "A", "fpi": 1.0}]).to_csv(accepted, index=False)
            pd.DataFrame([{"team": "A", "fpi": 1.0}]).to_csv(candidate, index=False)
            result = compare_source(
                "FPI",
                candidate,
                accepted,
                ["fpi"],
                {
                    "latest_accepted_update_at": "2026-08-30T09:19:23Z",
                    "last_changed_at": "2026-08-30T09:19:23Z",
                },
                "2026-08-30T15:51:57Z",
            )
            self.assertEqual(result["latest_check_status"], "NO_CHANGE")
            self.assertEqual(result["latest_accepted_update_at"], "2026-08-30T09:19:23Z")

    def test_ratings_owner_advances_only_on_actual_change(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            accepted = root / "accepted.csv"
            candidate = root / "candidate.csv"
            pd.DataFrame([{"team": "A", "fpi": 1.0}]).to_csv(accepted, index=False)
            pd.DataFrame([{"team": "A", "fpi": 2.0}]).to_csv(candidate, index=False)
            result = compare_source(
                "FPI", candidate, accepted, ["fpi"], {}, "2026-08-30T09:19:23Z"
            )
            self.assertEqual(result["latest_check_status"], "UPDATED")
            self.assertEqual(result["latest_accepted_update_at"], "2026-08-30T09:19:23Z")

    def test_accepted_change_after_cutoff_survives_no_change(self):
        metadata = {
            "latest_check_status": "NO_CHANGE",
            "latest_accepted_update_at": "2026-08-30T13:58:54Z",
        }
        self.assertTrue(
            accepted_after_cutoff(metadata, "2026-08-30T05:49:23Z")
        )

    def test_before_cutoff_baseline_and_pull_do_not_qualify(self):
        cutoff = "2026-08-30T05:49:23Z"
        self.assertFalse(accepted_after_cutoff(
            {"latest_accepted_update_at": "2026-08-30T05:49:22Z"},
            cutoff,
        ))
        self.assertFalse(accepted_after_cutoff(
            {"latest_pull_at": "2026-08-30T15:00:00Z"},
            cutoff,
        ))
        self.assertFalse(accepted_after_cutoff(
            {"change_status": "BASELINE_ESTABLISHED", "last_changed_at": "2026-08-30T15:00:00Z"},
            cutoff,
        ))
        self.assertFalse(accepted_after_cutoff(
            {"latest_check_status": "REJECTED", "latest_check_at": "2026-08-30T15:00:00Z"},
            cutoff,
        ))

    def test_week_cutoff_uses_last_accepted_completed_game(self):
        results = {"games": [
            {"game_id": "g1", "week": 0, "completed": True, "away_team": "A", "home_team": "B"},
            {"game_id": "g2", "week": 0, "completed": True, "away_team": "C", "home_team": "D"},
            {"game_id": "postponed", "week": 0, "completed": False, "status": "postponed"},
            {"game_id": "w1", "week": 1, "completed": True, "away_team": "E", "home_team": "F"},
        ]}
        watcher = {"accepted": {
            "g1": {"accepted_at": "2026-08-30T02:00:00Z"},
            "g2": {"accepted_at": "2026-08-30T05:49:23Z"},
            "w1": {"accepted_at": "2026-09-06T06:10:00Z"},
        }}
        cutoffs = completed_week_cutoffs(results, watcher)
        self.assertEqual(cutoffs[1]["game_id"], "g2")
        self.assertEqual(cutoffs[1]["final_completion_at"], "2026-08-30T05:49:23Z")
        self.assertEqual(cutoffs[2]["game_id"], "w1")
        self.assertNotIn(3, cutoffs)

    def test_week_cutoff_fails_closed_for_missing_final_event(self):
        results = {"games": [
            {"game_id": "g1", "week": 0, "completed": True},
            {"game_id": "g2", "week": 0, "completed": True},
            {"game_id": "canceled", "week": 0, "completed": False, "status": "canceled"},
        ]}
        watcher = {"accepted": {
            "g1": {"accepted_at": "2026-08-30T02:00:00Z"},
        }}
        self.assertNotIn(1, completed_week_cutoffs(results, watcher))


if __name__ == "__main__":
    unittest.main()
