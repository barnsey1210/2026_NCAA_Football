import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BettingModelPerformanceIntegrationTests(unittest.TestCase):
    def test_production_page_has_both_views_and_my_bets_is_default(self):
        text = (ROOT / "betting_v2.html").read_text()
        self.assertIn('class="active" data-view="bets">My Bets', text)
        self.assertIn('data-view="model">Model Performance', text)
        self.assertIn('<div id="myBetsView"', text)
        self.assertIn('id="modelPerformanceView" class="modelView" hidden', text)
        self.assertIn("data/site/betting_activity_view.json", text)
        self.assertIn("data/site/matchups_view.json", text)
        self.assertIn("data/site/model_performance_view.json", text)

    def test_my_bets_contract_markers_remain(self):
        text = (ROOT / "betting_v2.html").read_text()
        for marker in ("ownedCount", "exposure", "totalEv", "periodBar", "pDashboard",
                       "pRows", "ncaaf-game-bets-v1", "matchup_workspace.js"):
            self.assertIn(marker, text)
        self.assertNotIn("createPersonalBet", text)

    def test_fixed_hfa_capture_and_duplicate_safeguards(self):
        text = (ROOT / "scripts/model_tracking/capture_model_tracking.py").read_text()
        self.assertIn("NON_NEUTRAL_HFA = 2.6", text)
        self.assertIn("hfa = 0.0 if neutral else 2.6", text)
        self.assertIn('snapshot_timing = "day_before"', text)
        self.assertIn('snapshot_timing = "same_day_fallback"', text)
        self.assertIn('bool(game.get("completed"))', text)
        self.assertIn("accepted_pairs", text)
        self.assertIn('if (game["game_id"], market_type) in accepted_pairs:', text)

    def test_controller_calls_are_active(self):
        text = (ROOT / "scripts/control/run_data_refresh.py").read_text()
        self.assertGreaterEqual(text.count('"scripts/model_tracking/capture_model_tracking.py"'), 1)
        self.assertGreaterEqual(text.count('"scripts/model_tracking/settle_model_tracking.py"'), 2)
        self.assertGreaterEqual(text.count('"scripts/model_tracking/build_model_performance_view.py"'), 2)
        self.assertIn('"--accept"', text)

    def test_public_builder_and_publisher_contract(self):
        builder = (ROOT / "scripts/site/build_public_site.py").read_text()
        publisher = (ROOT / "scripts/publish/publish_site.sh").read_text()
        validator = (ROOT / "scripts/publish/check_public_site.py").read_text()
        self.assertIn("build_model_performance_view.py", builder)
        self.assertIn("model_performance_view.json", publisher)
        self.assertIn("modelPerformanceView", validator)
        self.assertIn("model_performance_view.json", validator)

    def test_runtime_view_contract_fixture(self):
        path = ROOT / "data/site/model_performance_view.json"
        if not path.exists():
            self.skipTest("generated runtime view is not versioned in the source worktree")
        data = json.loads(path.read_text())
        self.assertEqual(data["methodology"]["hfa"]["non_neutral"], 2.6)
        self.assertEqual(data["methodology"]["hfa"]["neutral"], 0.0)
        self.assertEqual(data["ranking_minimum"], 30)


if __name__ == "__main__":
    unittest.main()
