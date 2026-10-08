import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "war_room_matrix_l2",
    ROOT / "scripts/war_room/build_war_room_market_matrix.py",
)
MATRIX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MATRIX)


class CommandCenterL2TrendTests(unittest.TestCase):
    def test_loader_reuses_all_available_canonical_ratings_values(self):
        path = ROOT / "data/site/ratings_view.json"
        ratings = json.loads(path.read_text())
        expected = {
            MATRIX.normalize_team(row["team"]): (
                row.get("l2_change"), row.get("l2_movement_rank")
            )
            for row in ratings["teams"]
            if row.get("l2_change") is not None
            and row.get("l2_movement_rank") is not None
        }
        actual, meta = MATRIX.load_team_l2_trends(path)
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(
            {team: (row["l2_change"], row["l2_rank"]) for team, row in actual.items()},
            expected,
        )
        self.assertEqual(meta["source"], "ratings_view.teams.l2_change/l2_movement_rank")

    def test_representative_teams_are_exact_canonical_matches(self):
        path = ROOT / "data/site/ratings_view.json"
        ratings = json.loads(path.read_text())
        by_team = {row["team"]: row for row in ratings["teams"]}
        actual, _ = MATRIX.load_team_l2_trends(path)
        for team in ("Ohio State", "Georgia", "Notre Dame", "Alabama", "Miami-FL", "Texas", "Indiana"):
            with self.subTest(team=team):
                row = actual[MATRIX.normalize_team(team)]
                self.assertEqual(row["l2_change"], by_team[team]["l2_change"])
                self.assertEqual(row["l2_rank"], by_team[team]["l2_movement_rank"])

    def test_ui_uses_exact_rank_bands_and_explicit_missing_state(self):
        source = (ROOT / "scripts/site/build_war_room_page.py").read_text()
        for boundary in (28, 55, 83, 110):
            self.assertIn(f"value<={boundary}", source)
        self.assertIn("two-week rating history unavailable", source)
        self.assertIn("toFixed(1)", source)
        self.assertIn("l2TrendCell(game)", source)


if __name__ == "__main__":
    unittest.main()
