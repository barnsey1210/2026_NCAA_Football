import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MARKET = load(
    "performance_market_contract",
    "scripts/markets/build_current_market_contract.py",
)
MODEL_FIT = load(
    "performance_model_fit",
    "scripts/model_fit/build_team_game_evaluations_2026.py",
)
SHADOW_LINES = load(
    "performance_shadow_lines",
    "scripts/site/build_saturday_shadow_lines.py",
)
MATRIX = load(
    "performance_market_matrix",
    "scripts/war_room/build_war_room_market_matrix.py",
)


class PipelinePerformanceIndexTests(unittest.TestCase):
    def test_shadow_snapshot_appends_without_loading_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "snapshots.csv"
            first = pd.DataFrame([{"game_id": "g1", "value": 1.0}])
            second = pd.DataFrame([{"value": 2.0, "game_id": "g2"}])
            SHADOW_LINES.append_snapshot(path, first)
            with patch.object(
                SHADOW_LINES.pd, "read_csv", side_effect=AssertionError("history loaded")
            ):
                SHADOW_LINES.append_snapshot(path, second)
            self.assertEqual(pd.read_csv(path).game_id.tolist(), ["g1", "g2"])

    def test_model_fit_game_index_preserves_candidate_rows(self):
        rows = [
            {"canonical_game_id": "g1", "value": 1},
            {"canonical_game_id": "g2", "value": 2},
            {"canonical_game_id": "g1", "value": 3},
            {"value": 4},
        ]
        indexed = MODEL_FIT.index_by_game(rows, "canonical_game_id")
        self.assertEqual(
            list(MODEL_FIT.game_rows(indexed, "g1")),
            [rows[0], rows[2]],
        )
        self.assertIs(MODEL_FIT.game_rows(rows, "g1"), rows)

    def test_pregame_close_cache_preserves_pairs_and_skips_rescan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            history = root / "history.csv"
            cache = root / "cache.json"
            history.write_text(
                "canonical_game_id,book,market,side,line,price,source_updated_at\n"
                "g1,DraftKings,spread,away,3.5,-110,2026-09-12T15:00:00Z\n"
                "g1,DraftKings,spread,home,-3.5,-110,2026-09-12T15:00:00Z\n"
            )
            kickoffs = {
                "g1": datetime(2026, 9, 12, 16, 0, tzinfo=timezone.utc)
            }
            first = MARKET.load_pregame_close_pairs(history, kickoffs, cache)
            with patch.object(MARKET, "csv_rows", side_effect=AssertionError("rescanned")):
                second = MARKET.load_pregame_close_pairs(history, kickoffs, cache)
            self.assertEqual(first, second)
            self.assertEqual(second["g1"]["DraftKings"]["spread"]["home"]["line"], -3.5)

    def test_model_fit_indexes_match_legacy_selection_inputs(self):
        games = [
            {"game_id": "g1", "week": 1, "away_team": "Alpha", "home_team": "Beta"},
            {"game_id": "g2", "week": 2, "away_team": "Alpha", "home_team": "Gamma"},
        ]
        evaluations = [{"game_id": "g1", "team": "Alpha", "lifecycle_state": "COMPLETE"}]
        fbs = {MATRIX.normalize_team(x) for x in ("Alpha", "Beta", "Gamma")}
        expected, evaluation_index = MATRIX.build_selected_week_model_fit_indexes(
            games, evaluations, fbs
        )
        self.assertEqual(
            [row["game_id"] for row in expected[("2", MATRIX.normalize_team("Alpha"))]],
            ["g1"],
        )
        self.assertIs(
            evaluation_index[("g1", MATRIX.normalize_team("Alpha"))],
            evaluations[0],
        )


if __name__ == "__main__":
    unittest.main()
