import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MatchupAnalysisTest(unittest.TestCase):
    def test_player_rank_populations_are_metric_and_position_specific(self):
        payload = json.loads((ROOT / "data/site/matchup_analysis_2026.json").read_text())
        self.assertEqual(len(payload["teams"]), 138)
        sayin = next(
            row for row in payload["teams"]["Ohio State"]["players"]["passing"]
            if row["athleteName"] == "Julian Sayin"
        )
        self.assertEqual(sayin["metric"], "Passing WEPA")
        self.assertGreater(sayin["population"], 1)
        self.assertLessEqual(sayin["rank"], sayin["population"])
        self.assertEqual(sayin["position"], "QB")

    def test_public_page_has_scheduled_and_custom_routes(self):
        page = (ROOT / "matchup-analysis.js").read_text()
        self.assertIn("params.get('game_id')", page)
        self.assertIn("params.get('away')", page)
        self.assertIn("params.get('home')", page)
        self.assertIn("playerCard", page)
        self.assertIn("${r.rank}/${r.population}", page)

    def test_command_center_and_ratings_link_to_card(self):
        command = (ROOT / "scripts/site/build_war_room_page.py").read_text()
        public = (ROOT / "scripts/site/build_public_site.py").read_text()
        self.assertIn("matchup-analysis.html?game_id=", command)
        self.assertIn("setMatchupLink(away.team,home.team,-homeMargin,total)", public)


if __name__ == "__main__":
    unittest.main()
