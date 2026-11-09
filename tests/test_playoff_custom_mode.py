import json
import math
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PlayoffCustomModeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ratings = json.loads((ROOT / "data/site/ratings_view.json").read_text())
        cls.teams = {row["team"]: row for row in cls.ratings["teams"]}
        cls.js = (ROOT / "playoff_custom.js").read_text()

    def project(self, away, home, hfa):
        required = self.ratings["matchup_estimator"]["spread"]["required_sources"]
        values = [self.teams[home]["sources"][s]["rating"] - self.teams[away]["sources"][s]["rating"] for s in required]
        margin = sum(values) / 3 + hfa
        ah, hh = self.teams[away]["spplus_components"], self.teams[home]["spplus_components"]
        total = .5 * (hh["offense"] + ah["defense"]) + .5 * (ah["offense"] + hh["defense"])
        return margin, total, (total-margin)/2, (total+margin)/2

    def test_138_unique_dropdown_identities_and_strict_contract(self):
        names = [x["team"] for x in self.ratings["teams"]]
        self.assertEqual((len(names), len(set(names))), (138, 138))
        cfg = self.ratings["matchup_estimator"]
        self.assertEqual(cfg["spread"]["required_sources"], ["spplus", "fpi", "teamrankings"])
        self.assertEqual(cfg["spread"]["missing_component_policy"], "UNAVAILABLE_NO_REWEIGHTING")
        self.assertEqual(cfg["total"]["formula_version"], "shadow_total_enhanced_spplus_od_v1")

    def test_bracket_mapping_and_round_sites(self):
        for marker in ("id:'r1_5_12',round:'first'", "id:'r1_8_9',round:'first'", "id:'r1_6_11',round:'first'", "id:'r1_7_10',round:'first'"):
            self.assertIn(marker, self.js)
        self.assertIn("next:'qf_4'", self.js)
        self.assertIn("next:'qf_1'", self.js)
        self.assertIn("next:'qf_3'", self.js)
        self.assertIn("next:'qf_2'", self.js)
        self.assertIn("round==='first'?Number(cfg.home_field_advantage.non_neutral_points)", self.js)
        self.assertIn(":Number(cfg.home_field_advantage.neutral_points)", self.js)

    def test_formula_parity_hfa_total_and_score_algebra(self):
        home = self.project("Alabama", "Ohio State", 2.6)
        neutral = self.project("Alabama", "Ohio State", 0.0)
        self.assertAlmostEqual(home[0]-neutral[0], 2.6)
        self.assertAlmostEqual(home[1], neutral[1])
        self.assertAlmostEqual(home[2]+home[3], home[1])
        self.assertAlmostEqual(home[3]-home[2], home[0])
        self.assertIn("components.reduce((s,x)=>s+x.value,0)/components.length+hfa", self.js)
        self.assertIn(".5*(spHome.offense+spAway.defense)+.5*(spAway.offense+spHome.defense)", self.js)

    def test_manual_invalidation_champion_and_stochastic_simulation_markers(self):
        for marker in ("pruneWinners", "state.winners.championship", "GAME_SIGMA=15.7", "normalCdf(margin/GAME_SIGMA)", "simulateGame(p)", "validateSimulation"):
            self.assertIn(marker, self.js)
        self.assertNotIn("margin>=0?a:b", self.js)

    def test_model_source_is_unchanged_except_toggle_assets(self):
        page = (ROOT / "playoff_v2.html").read_text()
        self.assertIn("playoff_custom.css", page)
        self.assertIn("playoff_custom.js", page)
        self.assertIn("playoff_custom.css?v=cfp-custom-v7", page)
        self.assertIn("playoff_custom.js?v=cfp-custom-v7", page)
        self.assertIn("Projected CFP Field", page)
        self.assertIn("P.projected_field", page)
        self.assertIn("data/site/playoff_model_2026.json", page)
        cloudflare = json.loads((ROOT / "config/cloudflare_pages_manifest.json").read_text())
        for asset in ("playoff_custom.css", "playoff_custom.js"):
            self.assertIn(asset, cloudflare["files"])
            self.assertIn(asset, cloudflare["allowed_top_level"])
        for marker in ("CUSTOM MATCHUP", "playoffMatchupAway", "playoffMatchupHome", "playoffMatchupNeutral", "Ratings-page projection"):
            self.assertIn(marker, self.js)
        for marker in ("overall_rank", "ratingClass", "decorateModelRanks", "decorateCustomRanks"):
            self.assertIn(marker, self.js)

    def test_drag_swap_inline_lines_and_variable_simulated_scores(self):
        for marker in ("swapSeeds", "drag-handle", "data-seed-row", "simulateGame", "normalRandom", "state.scores", "2000/(events.length+4)", "notre-dame", "Number(a.overall_rank)-Number(b.overall_rank)"):
            self.assertIn(marker, self.js)
        self.assertIn("O/U ${p.total.toFixed(1)}", self.js)
        self.assertIn("-${Math.abs(p.margin).toFixed(1)}", self.js)
        self.assertNotIn("(Rtg #${rank})", self.js)

    def test_quarter_scoring_seed_labels_and_champion_banner(self):
        for marker in ("scoreChunks", "scoreEvents", "period:'1Q'", "`${q}Q`", "period:'FINAL'", "champion-team", "🏆"):
            self.assertIn(marker, self.js)
        self.assertIn('<span class="seed-number">${s}</span>', self.js)
        self.assertIn("${seedOf(name)||''}", self.js)
        self.assertNotIn("`Proj ${projected.toFixed(1)}`", self.js)
        css = (ROOT / "playoff_custom.css").read_text()
        self.assertIn(".team-detail em{color:#a9bdd4}", css)

    def test_live_scoring_does_not_rebuild_or_force_scroll(self):
        self.assertIn("function paintLiveGame", self.js)
        self.assertIn("scrollLeft=left", self.js)
        self.assertNotIn("scrollIntoView", self.js)
        self.assertIn("champion-footer", self.js)
        css = (ROOT / "playoff_custom.css").read_text()
        self.assertIn("position:fixed;left:50%;bottom:8px", css)

    def test_mobile_breakpoints_and_no_horizontal_custom_canvas(self):
        css = (ROOT / "playoff_custom.css").read_text()
        self.assertIn("@media(max-width:620px)", css)
        self.assertIn("@media(max-width:350px)", css)
        self.assertIn("grid-template-columns:repeat(4,minmax(280px,84vw))", css)
        self.assertIn("overflow-x:auto", css)
        self.assertIn("scroll-snap-type:x mandatory", css)


if __name__ == "__main__":
    unittest.main()
