import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("war_room", ROOT / "scripts/site/build_war_room_preview.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class WarRoomPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = MOD.build_payload()
        cls.output = MOD.render(cls.payload)

    def test_static_sources_and_provenance(self):
        self.assertGreaterEqual(len(self.payload["source_paths"]), 8)
        for source in self.payload["source_paths"]:
            self.assertIn(source, self.output)
            if source != MOD.SOURCES["injuries"]:
                self.assertTrue((ROOT / source).is_file(), source)
        self.assertFalse((ROOT / MOD.SOURCES["injuries"]).exists())
        self.assertNotIn("fetch(", self.output)

    def test_upcoming_week_is_first_uncompleted_week(self):
        all_future = [g for g in self.payload["matchups"]["games"] if not g["game"].get("completed")]
        self.assertEqual(self.payload["week"], min(g["game"]["week"] for g in all_future))
        self.assertTrue(all(g["game"]["week"] == self.payload["week"] for g in self.payload["slate"]))

    def test_categories_are_separate(self):
        self.assertIn("Spread opportunities", self.output)
        self.assertIn("Total opportunities", self.output)
        self.assertIn("Futures opportunities", self.output)
        self.assertIn("Market Inefficiencies", self.output)
        self.assertLess(self.output.index("Model Opportunities"), self.output.index("Market Inefficiencies"))

    def test_adaptive_preseason_and_injury_states(self):
        self.assertEqual(self.payload["performance"]["status"], "PRESEASON_NOT_STARTED")
        self.assertIn("Preseason tracking has not started", self.output)
        self.assertEqual(self.payload["injury_state"], "unreleased")
        self.assertIn("injuries unreleased", self.output)

    def test_in_season_performance_state_uses_available_values(self):
        payload = dict(self.payload)
        payload["performance"] = {
            "status": "ACTIVE",
            "summary": {"predictions": 48, "settled": 31},
        }
        output = MOD.render(payload)
        self.assertNotIn("Preseason tracking has not started", output)
        self.assertIn(">48</b>", output)
        self.assertIn(">31</b>", output)

    def test_spread_side_uses_selected_team_perspective(self):
        sample = next(g for g in self.payload["slate"] if MOD.spread_edge(g))
        edge = MOD.spread_edge(sample)
        self.assertIsNotNone(edge)
        if edge["model"] > edge["market"]:
            self.assertEqual(edge["side"], sample["game"]["away_team"])
        else:
            self.assertEqual(edge["side"], sample["game"]["home_team"])

    def test_known_invalid_book_quote_is_excluded_from_disagreement(self):
        odds_game = next(g for g in self.payload["odds"]["games"] if g["game_id"] == "g3")
        self.assertEqual(MOD.best_book_range(odds_game, "spread"), 0.0)

    def test_empty_sections_render_cleanly(self):
        self.assertIn("No qualifying current opportunities", MOD.opportunity_rows([], "spread"))

    def test_destination_links_exist_and_canonical_index_untouched(self):
        for href in MOD.DESTINATIONS.values():
            self.assertTrue((ROOT / href.replace("../../", "")).is_file(), href)
        self.assertNotEqual(MOD.OUT.resolve(), (ROOT / "index.html").resolve())


if __name__ == "__main__":
    unittest.main()
