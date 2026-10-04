import sys
import unittest

from scripts.ratings.run_fast_standard_source_refresh import commands, provider_run_status


class FastStandardSourceRefreshTests(unittest.TestCase):
    def test_massey_refresh_uses_shared_dynamic_weekly_path(self):
        command = commands("2026-09-12", "2026-09-19", "2026-09-12")["massey"]
        self.assertEqual(command, [
            sys.executable,
            "scripts/projections/refresh_massey_game_projections_2026.py",
            "--as-of-date",
            "2026-09-12",
        ])

    def test_one_provider_failure_is_a_successful_partial_orchestration(self):
        status, success = provider_run_status([
            {"provider": "dratings", "returncode": 0},
            {"provider": "massey", "returncode": 2},
        ])
        self.assertTrue(success)
        self.assertEqual(status, "COMPLETED_WITH_WARNINGS")

    def test_all_provider_failures_remain_global_failure(self):
        status, success = provider_run_status([
            {"provider": "dratings", "returncode": 1},
            {"provider": "massey", "returncode": 2},
        ])
        self.assertFalse(success)
        self.assertEqual(status, "FAILED")


if __name__ == "__main__":
    unittest.main()
