import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.projections.spplus_total import load_current_components, projected_scores, projected_total

class SpplusTotalAuthorityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.components = load_current_components(ROOT / "data/ratings/spplus_2026_from_espn_latest.csv")

    def total(self, away, home):
        a, h = self.components[away], self.components[home]
        return projected_total(a["offense"], h["defense"], h["offense"], a["defense"])

    def test_known_inputs_swap_hfa_and_score_algebra(self):
        total = projected_total(17.2, 26.0, 23.6, 37.4)
        self.assertAlmostEqual(total, 52.1)
        self.assertAlmostEqual(total, projected_total(23.6, 37.4, 17.2, 26.0))
        a, b = projected_scores(total, -18.4)
        self.assertAlmostEqual(a + b, total)
        self.assertAlmostEqual(a - b, -18.4)

    def test_current_week_examples_use_raw_components(self):
        for matchup in (("Ball State", "Ohio"), ("Pittsburgh", "Louisville"), ("Miami-OH", "Kent State"), ("Akron", "Massachusetts")):
            with self.subTest(matchup=matchup):
                away, home = (self.components[name] for name in matchup)
                expected = (away["offense"] + home["defense"]) / 2 + (home["offense"] + away["defense"]) / 2
                self.assertAlmostEqual(self.total(*matchup), expected)

    def test_source_builder_uses_current_components_not_preseason_overlay(self):
        subprocess.run([sys.executable, "scripts/projections/build_game_projection_sources_2026.py"], cwd=ROOT, check=True, capture_output=True, text=True)
        with (ROOT / "data/projections/game_projection_sources_2026.csv").open() as handle:
            rows = list(csv.DictReader(handle))
        by_game = {(row["away_team"], row["home_team"]): row for row in rows if row["source"] == "SP+"}
        for away, home in (("Ball State", "Ohio"), ("Pittsburgh", "Louisville"), ("Miami-OH", "Kent State"), ("Akron", "Massachusetts")):
            self.assertAlmostEqual(float(by_game[(away, home)]["total"]), self.total(away, home))
            self.assertIn("Current accepted raw SP+", by_game[(away, home)]["notes"])

    def test_ratings_playoff_and_command_center_contract_parity(self):
        subprocess.run([sys.executable, "scripts/site/build_ratings_view.py"], cwd=ROOT, check=True)
        subprocess.run([sys.executable, "scripts/projections/build_current_game_projection_contract.py"], cwd=ROOT, check=True)
        ratings = json.loads((ROOT / "data/site/ratings_view.json").read_text())
        self.assertEqual(len(ratings["teams"]), 138)
        self.assertEqual(ratings["matchup_estimator"]["total"]["formula_version"], "shadow_total_enhanced_spplus_od_v1")
        self.assertIn(".5*(spHome.offense+spAway.defense)+.5*(spAway.offense+spHome.defense)", (ROOT / "playoff_custom.js").read_text())
        games = {row["game_id"]: row for row in json.loads((ROOT / "data/site/current_game_projection_contract.json").read_text())["games"]}
        for game_id, away, home in (("g754", "Ball State", "Ohio"), ("g788", "Pittsburgh", "Louisville"), ("g753", "Miami-OH", "Kent State"), ("g757", "Akron", "Massachusetts")):
            component = games[game_id]["projections"]["standard_total_sp_massey_dratings_v1"]["component_values"]["SP+"]
            self.assertAlmostEqual(component, self.total(away, home))

if __name__ == "__main__":
    unittest.main()
