import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAST = load("fast_standard_sources", "scripts/ratings/run_fast_standard_source_refresh.py")
DRATINGS = load("bounded_dratings", "scripts/projections/pull_dratings_ncaaf_predictions.py")
MASSEY = load("bounded_massey", "scripts/projections/build_massey_game_projections_2026.py")
SAGARIN = load("bounded_sagarin", "ratings/pull_sagarin_ratings.py")


class FastRatingsStandardSourceTests(unittest.TestCase):
    def test_next_seven_day_window_is_inclusive_and_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "schedule.json"
            path.write_text(json.dumps({"games": [
                {"game_id":"before","date":"2026-08-24"},
                {"game_id":"start","date":"2026-08-25"},
                {"game_id":"end","date":"2026-09-01"},
                {"game_id":"after","date":"2026-09-02"},
            ]}))
            rows = FAST.window_games(path, "2026-08-25", "2026-09-01")
        self.assertEqual([row["game_id"] for row in rows], ["start", "end"])

    def test_provider_commands_are_fixed_and_bounded(self):
        commands = FAST.commands("2026-08-25", "2026-09-01", "2026-08-25")
        self.assertEqual(set(commands), {"sagarin", "dratings", "massey"})
        self.assertIn("--start-date", commands["dratings"])
        self.assertIn("--end-date", commands["dratings"])
        self.assertIn("--days", commands["massey"])
        self.assertIn("7", commands["massey"])
        self.assertIn("--start-date", commands["sagarin"])

    def test_out_of_window_rows_are_preserved_for_each_matchup_source(self):
        existing = pd.DataFrame([
            {"game_date":"2026-08-20","away_team_raw":"A","home_team_raw":"B","away_team":"A","home_team":"B","game_id":"old","value":1},
            {"game_date":"2026-08-27","away_team_raw":"C","home_team_raw":"D","away_team":"C","home_team":"D","game_id":"inside","value":1},
            {"game_date":"2026-09-10","away_team_raw":"E","home_team_raw":"F","away_team":"E","home_team":"F","game_id":"future","value":1},
        ])
        current = existing.iloc[[1]].assign(value=2)
        d = DRATINGS.merge_window(existing, current, "2026-08-25", "2026-09-01")
        m = MASSEY.merge_window(existing, current, "2026-08-25", "2026-09-01")
        s = SAGARIN.merge_prediction_window(existing, current, "2026-08-25", "2026-09-01")
        for frame in (d, m, s):
            self.assertEqual(set(frame["game_id"]), {"old", "inside", "future"})
            self.assertEqual(int(frame.loc[frame.game_id.eq("inside"), "value"].iloc[0]), 2)

    def test_locked_formulas_remain_literal_in_contract_builder(self):
        source = (ROOT / "scripts/projections/build_current_game_projection_contract.py").read_text()
        self.assertIn('{name: 0.20 for name in SPREAD_COMPONENTS}', source)
        self.assertIn('{"SP+": 0.40, "Massey Dual": 0.40, "Sagarin Total": 0.20}', source)

    def test_team_rating_engine_uses_centered_sagarin_and_equal_weights(self):
        source = (ROOT / "ratings/build_active_2026_ratings_master.py").read_text()
        self.assertIn('pivot["sagarin_raw"] = pivot[sagarin_source]', source)
        self.assertIn('pivot[sagarin_source] = pivot[sagarin_source] - sagarin_mean', source)
        self.assertIn('pivot["power_rating"] = pivot[active_cols].mean', source)


if __name__ == "__main__":
    unittest.main()
