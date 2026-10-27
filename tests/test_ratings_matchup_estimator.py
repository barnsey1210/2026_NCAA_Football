import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RatingsMatchupEstimatorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/site/build_ratings_view.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        cls.payload = json.loads((ROOT / "data/site/ratings_view.json").read_text())
        cls.teams = {team["team"]: team for team in cls.payload["teams"]}

    def margin(self, away, home, neutral=False):
        cfg = self.payload["matchup_estimator"]
        values = []
        for source in cfg["spread"]["required_sources"]:
            values.append(
                self.teams[home]["sources"][source]["rating"]
                - self.teams[away]["sources"][source]["rating"]
            )
        hfa = cfg["home_field_advantage"][
            "neutral_points" if neutral else "non_neutral_points"
        ]
        return sum(values) / len(values) + hfa

    def test_contract_is_strict_three_source_and_spplus_only_total(self):
        cfg = self.payload["matchup_estimator"]
        self.assertEqual(cfg["spread"]["required_sources"], ["spplus", "fpi", "teamrankings"])
        self.assertEqual(cfg["spread"]["missing_component_policy"], "UNAVAILABLE_NO_REWEIGHTING")
        self.assertEqual(cfg["total"]["source"], "SP+")
        self.assertEqual(cfg["total"]["status"], "AVAILABLE")
        self.assertEqual(cfg["total"]["formula_version"], "shadow_total_enhanced_spplus_od_v1")
        self.assertEqual(cfg["total"]["hfa_total_effect"], 0.0)
        self.assertNotIn("sagarin", cfg["spread"]["required_sources"])
        self.assertNotIn("dratings", cfg["spread"]["required_sources"])

    def test_exactly_138_unique_teams_populate(self):
        names = [team["team"] for team in self.payload["teams"]]
        self.assertEqual(len(names), 138)
        self.assertEqual(len(set(names)), 138)

    def test_home_neutral_swap_and_score_algebra(self):
        home_margin = self.margin("Alabama", "Ohio State")
        neutral_margin = self.margin("Alabama", "Ohio State", neutral=True)
        swapped_neutral = self.margin("Ohio State", "Alabama", neutral=True)
        self.assertAlmostEqual(home_margin - neutral_margin, 2.6)
        self.assertAlmostEqual(neutral_margin, -swapped_neutral)

        cfg = self.payload["matchup_estimator"]
        away = self.teams["Alabama"]["spplus_components"]
        home = self.teams["Ohio State"]["spplus_components"]
        total = (
            0.5 * (home["offense"] + away["defense"])
            + 0.5 * (away["offense"] + home["defense"])
        )
        away_score = (total - home_margin) / 2
        home_score = (total + home_margin) / 2
        self.assertAlmostEqual(home_score + away_score, total)
        self.assertAlmostEqual(home_score - away_score, home_margin)
        neutral_total = (
            0.5 * (home["offense"] + away["defense"])
            + 0.5 * (away["offense"] + home["defense"])
        )
        self.assertAlmostEqual(total, neutral_total)

    def test_page_contract_and_same_team_handling(self):
        page = (ROOT / "ratings_v2.html").read_text()
        for marker in (
            "MATCHUP ESTIMATE",
            "matchupAway",
            "matchupHome",
            "matchupNeutral",
            "Choose two different teams",
            "cfg.spread.required_sources",
            "const total=.5*(spHome.offense+spAway.defense)+.5*(spAway.offense+spHome.defense)",
            "const awayScore=(total-homeMargin)/2",
        ):
            self.assertIn(marker, page)

    def test_public_validator_guards_estimator_markers(self):
        validator = (ROOT / "scripts/publish/check_public_site.py").read_text()
        self.assertIn("Ratings matchup estimator marker missing", validator)
        self.assertIn("shadow_total_enhanced_spplus_od_v1", validator)


if __name__ == "__main__":
    unittest.main()
