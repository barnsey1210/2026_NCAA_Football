import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MatchupAnalysisDirectionalSummaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js = (ROOT / "matchup-analysis.js").read_text()
        cls.css = (ROOT / "matchup-analysis.css").read_text()
        cls.playoff_js = (ROOT / "playoff_custom.js").read_text()

    def test_balanced_offenses_use_passing_emphasis(self):
        self.assertIn("runBias>=.58", self.js)
        self.assertIn("runBias<=.45", self.js)
        self.assertIn("if(l==='Adjusted Passing EPA')base=100", self.js)
        self.assertIn("balanced; passing efficiency receives the tiebreaking emphasis", self.js)

    def test_two_directional_cards_feed_overall_advantage(self):
        self.assertIn("OFF vs ${g.home} DEF", self.js)
        self.assertIn("OFF vs ${g.away} DEF", self.js)
        self.assertIn("Overall advantage combines both directional offense-vs-defense matchups", self.js)
        self.assertIn("repeat(5,minmax(145px,1fr))", self.css)

    def test_custom_matchups_have_projection_fallback_and_site_context(self):
        self.assertIn("function ratingsProjection", self.js)
        self.assertIn("data/site/ratings_view.json", self.js)
        self.assertIn("neutral=params.get('neutral')==='1'", self.js)
        self.assertIn("neutral:neutral?'1':'0'", self.playoff_js)


if __name__ == "__main__":
    unittest.main()
