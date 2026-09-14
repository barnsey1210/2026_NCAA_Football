import json
import tempfile
import unittest
from pathlib import Path

from scripts.site.build_matchups_view import apply_canonical_composite_ratings


ROOT = Path(__file__).resolve().parents[1]


class RatingsUiAuthorityTest(unittest.TestCase):
    def test_matchups_uses_canonical_rating_and_rank_without_changing_od_ranks(self):
        teams = [{
            "team": "Ohio",
            "rank": 108,
            "combo": -11.000815,
            "sp_offense": 10.0,
            "sp_defense": 20.0,
        }]
        canonical_teams = [
            {"team": f"Team {index}", "overall_rank": index, "rating": 100-index}
            for index in range(1, 130)
        ]
        canonical_teams.append({"team": "Ohio", "overall_rank": 112, "rating": -10.7535869565})

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ratings_view.json"
            path.write_text(json.dumps({"teams": canonical_teams}))
            result = apply_canonical_composite_ratings(teams, path)

        self.assertEqual(result[0]["rank"], 112)
        self.assertAlmostEqual(result[0]["combo"], -10.7535869565)
        self.assertEqual(result[0]["sp_offense"], 10.0)
        self.assertEqual(result[0]["sp_defense"], 20.0)

    def test_all_ratings_refresh_paths_rebuild_matchups_before_matrix(self):
        source = (ROOT / "scripts/control/run_data_refresh.py").read_text()
        for function_name in ("ratings_change_commands", "ratings_no_change_commands"):
            start = source.index(f"def {function_name}")
            end = source.index("\ndef ", start + 5)
            block = source[start:end]
            self.assertLess(block.index("build_ratings_view.py"), block.index("build_matchups_view.py"))
            self.assertLess(block.index("build_matchups_view.py"), block.index("build_war_room_market_matrix.py"))

    def test_ratings_page_bypasses_cached_rating_and_matchup_payloads(self):
        for page in ("ratings_v2.html", "ratings.html"):
            source = (ROOT / page).read_text()
            self.assertIn("const version=Date.now();", source)
            self.assertIn("ratings_view.json?v=${version}", source)
            self.assertIn("matchups_view.json?v=${version}", source)
            self.assertEqual(source.count("{cache:'no-store'}"), 2)

    def test_public_build_refreshes_ratings_before_matchups(self):
        source = (ROOT / "scripts/site/build_public_site.py").read_text()
        self.assertLess(source.index("build_ratings_view.py"), source.index("build_matchups_view.py"))


if __name__ == "__main__":
    unittest.main()
