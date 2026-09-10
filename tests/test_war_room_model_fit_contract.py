import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.war_room import build_war_room_market_matrix as matrix


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "scripts/site/build_war_room_page.py"
MATRIX_PATH = ROOT / "scripts/war_room/build_war_room_market_matrix.py"


class WarRoomModelFitContractTests(unittest.TestCase):
    def test_desktop_and_mobile_render_the_same_model_fit_cell(self):
        source = PAGE.read_text()
        self.assertIn('<th class="matrix-header-cell model-fit-col context-group">PERF<br>VS MODEL</th>', source)
        self.assertIn('${modelFitCell(game)}', source)
        self.assertIn('<span class="mobile-foot-label">PERF VS MODEL</span>${modelFitCell(game)}', source)
        self.assertIn("fit.agreement==='DISAGREE'", source)
        for field in (
            "games_evaluated", "model_fit_health", "sample_state",
            "performance_vs_model", "score_vs_model",
            "sp_plus_vs_model", "cfbd_vs_model", "lens_gap",
        ):
            self.assertIn(field, source)
        self.assertIn("Score vs Model ${modelFitNumber(fit.score_vs_model)}", source)
        self.assertNotIn("Performance margin ${modelFitNumber(fit.performance_margin)}", source)
        self.assertNotIn("+ = outperformed model · - = underperformed model", source)
        self.assertNotIn("eligible teams", source)
        self.assertNotIn("fit.agreement||", source)
        self.assertNotIn("SP+ vs Market:", source)
        self.assertNotIn("CFBD vs Market:", source)

    def test_exchange_quotes_remain_data_only_in_priority_matrix(self):
        source = PAGE.read_text()
        self.assertNotIn("SPREAD</span><br>EXCH", source)
        self.assertNotIn("TOTAL<br>EXCH", source)
        self.assertNotIn('<td class="exchange-col', source)
        self.assertNotIn("game.market?.best_exchange", source)

    def test_matrix_projects_team_aggregates_without_calculating_fit(self):
        source = MATRIX_PATH.read_text()
        self.assertIn('TEAM_GAME_EVALUATIONS = ROOT / "data/site/team_game_evaluations_2026.json"', source)
        self.assertIn('"source": "team_game_evaluations_2026.team_aggregates"', source)
        self.assertIn('"display_only": True', source)
        self.assertIn("selected_week_model_fit", source)

    def test_value_colors_and_rank_use_canonical_helpers(self):
        source = PAGE.read_text()
        self.assertIn("if(n>=2) return 'positive'", source)
        self.assertIn("if(n<=-2) return 'negative'", source)
        self.assertIn("compositeRankClass(rank)", source)
        self.assertIn('<span class="team-composite-rank ${compositeRankClass(rank)}">${rank?esc(rank):\'—\'}</span>', source)
        self.assertNotIn("'#'+esc(rank)", source)
        self.assertNotIn("model-fit-rank", source)
        self.assertIn("fit.performance_vs_model", source)

    def test_selected_week_health_pending_complete_degraded_bye_and_no_sample(self):
        schedule = [
            {"game_id":"g1","week":1,"away_team":"Alpha","home_team":"Beta","kickoff_time":"2026-09-01T00:00:00Z"},
            {"game_id":"g2","week":2,"away_team":"Alpha","home_team":"Gamma","kickoff_time":"2026-09-08T00:00:00Z"},
        ]
        universe = {matrix.normalize_team(team) for team in ("Alpha","Beta","Gamma","Bye Team")}
        complete = {"team":"Alpha","games_evaluated":1,"performance_vs_model":3.0,"model_fit_health":"COMPLETE","model_fit_status":"GREEN"}
        evaluations = [{"game_id":"g1","team":"Alpha","lifecycle_state":"COMPLETE"}]
        now = datetime(2026,9,11,tzinfo=timezone.utc)
        week2 = matrix.selected_week_model_fit(complete,"Alpha",2,schedule,{"g1":{"completed":True}},evaluations,universe,now)
        self.assertEqual(week2["model_fit_status"],"GREEN")
        week3_pending = matrix.selected_week_model_fit(complete,"Alpha",3,schedule,{"g1":{"completed":True},"g2":{"completed":False}},evaluations,universe,now)
        self.assertEqual((week3_pending["model_fit_health"],week3_pending["model_fit_status"]),("PENDING","YELLOW"))
        overdue = matrix.selected_week_model_fit(complete,"Alpha",3,schedule,{"g1":{"completed":True},"g2":{"completed":True}},evaluations,universe,now)
        self.assertEqual(overdue["model_fit_status"],"RED")
        bye = matrix.selected_week_model_fit(complete,"Beta",3,schedule,{"g1":{"completed":True},"g2":{"completed":False}},[{"game_id":"g1","team":"Beta","lifecycle_state":"COMPLETE"}],evaluations and universe,now)
        self.assertEqual(bye["model_fit_status"],"GREEN")
        no_sample = matrix.selected_week_model_fit({},"Bye Team",2,schedule,{},[],universe,now)
        self.assertEqual(no_sample["model_fit_status"],"GRAY")


if __name__ == "__main__":
    unittest.main()
