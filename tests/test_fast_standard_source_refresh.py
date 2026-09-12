import sys
import unittest

from scripts.ratings.run_fast_standard_source_refresh import commands


class FastStandardSourceRefreshTests(unittest.TestCase):
    def test_massey_refresh_uses_ten_day_rolling_horizon(self):
        command = commands("2026-09-12", "2026-09-19", "2026-09-12")["massey"]
        self.assertEqual(command, [
            sys.executable,
            "scripts/projections/refresh_massey_game_projections_2026.py",
            "--days",
            "10",
            "--as-of-date",
            "2026-09-12",
        ])


if __name__ == "__main__":
    unittest.main()
