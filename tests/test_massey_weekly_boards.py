import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REFRESH = load("massey_refresh", ROOT / "scripts/projections/refresh_massey_game_projections_2026.py")
PARSER = load("massey_parser", ROOT / "scripts/projections/build_massey_game_projections_2026.py")


class MasseyWeeklyBoardTests(unittest.TestCase):
    def test_current_and_following_saturdays(self):
        self.assertEqual(
            REFRESH.football_week_saturdays(date(2026, 9, 26)),
            (date(2026, 9, 26), date(2026, 10, 3)),
        )

    def test_week_rollover_after_saturday(self):
        self.assertEqual(
            REFRESH.football_week_saturdays(date(2026, 9, 27)),
            (date(2026, 10, 3), date(2026, 10, 10)),
        )

    def test_final_weekday_row_keeps_team_identity(self):
        fixture = """Thu 09.24
FINAL
Liberty
@ Coastal Car
# 86 (3-1)
# 121 (1-3)
34
17
26
27
48 %
52 %
-1.5
53.5
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "massey_games_20260926.txt"
            path.write_text(fixture)
            rows, _ = PARSER.parse_file(path)
        self.assertEqual(rows[0]["away_team"], "Liberty")
        self.assertEqual(rows[0]["home_team"], "Coastal Car")
        self.assertEqual(rows[0]["game_status"], "FINAL")

    def test_neutral_row_preserves_rendered_evidence(self):
        fixture = """Sat 10.03
4:00.PM.ET
Texas A&M
Arkansas
Arlington, TX
# 25 (2-1)
# 62 (1-2)
0
0
31
28
56 %
44 %
-2.5
58.5
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "massey_games_20261003.txt"
            path.write_text(fixture)
            rows, _ = PARSER.parse_file(path)
        self.assertTrue(rows[0]["neutral_site_hint"])


if __name__ == "__main__":
    unittest.main()
