#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ratings/pull_sagarin_ratings.py"
SPEC = importlib.util.spec_from_file_location("pull_sagarin_ratings", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

SOURCE_BUILDER_PATH = ROOT / "scripts/projections/build_game_projection_sources_2026.py"
SOURCE_SPEC = importlib.util.spec_from_file_location("build_game_projection_sources", SOURCE_BUILDER_PATH)
SOURCE_MODULE = importlib.util.module_from_spec(SOURCE_SPEC)
assert SOURCE_SPEC.loader is not None
SOURCE_SPEC.loader.exec_module(SOURCE_MODULE)


CURRENT_ROW = """
<html><body><pre>
2026 College Football STARTING ratings
Predictions_with_Totals_and_Moneylines
2026 College Football STARTING ratings
          FAVORITE             Rating   Pred  Golden Recent Strong  UNDERDOG               MONEY   WIN%    home   away  TOTAL
   18   @ Eastern Michigan       8.28   8.28   8.28   8.28   8.28   Sacramento State         243    71%   27.21  24.79  52.00  57%
</pre></body></html>
"""


class SagarinPredictionIntegrityTests(unittest.TestCase):
    def test_current_heading_and_prediction_row_parse(self) -> None:
        self.assertEqual(MODULE.detect_provider_season(CURRENT_ROW), 2026)
        old_index = MODULE.canonical_2026_pair_index
        MODULE.canonical_2026_pair_index = lambda: {
            ("sacramento state", "eastern michigan"): {
                "game_id": "g1", "date": "2026-08-29",
                "away_team": "Sacramento State", "home_team": "Eastern Michigan",
            },
            ("eastern michigan", "sacramento state"): {
                "game_id": "g1", "date": "2026-08-29",
                "away_team": "Sacramento State", "home_team": "Eastern Michigan",
            },
        }
        try:
            frame, _ = MODULE.parse_sagarin_predictions(CURRENT_ROW, 2026)
        finally:
            MODULE.canonical_2026_pair_index = old_index
        self.assertEqual(len(frame), 1)
        row = frame.iloc[0]
        self.assertEqual(row["favorite_spread_rating"], 8.28)
        self.assertEqual(row["projected_total"], 52.0)
        self.assertEqual(row["game_id"], "g1")

    def test_invalid_candidate_preserves_last_known_good(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            latest = root / "latest.csv"
            candidate = root / "candidate.csv"
            status = root / "status.json"
            latest.write_text("game_id,favorite_spread_rating,projected_total\ng1,8.28,52.0\n")
            before = latest.read_bytes()
            result = MODULE.promote_prediction_candidate(
                pd.DataFrame(), None,
                candidate_path=candidate, latest_path=latest, status_path=status,
            )
            self.assertFalse(result["valid"])
            self.assertEqual(latest.read_bytes(), before)
            self.assertTrue(status.is_file())

    def test_blanket_default_totals_are_rejected(self) -> None:
        rows = []
        for game_id, spread in (("g1", 8.28), ("g2", 3.5)):
            rows.append({
                "favorite": "Favorite",
                "underdog": "Underdog",
                "projection_variant": "standard",
                "favorite_spread_rating": spread,
                "projected_total": 52.0,
                "game_id": game_id,
                "source_url": "http://sagarin.com/sports/cfsend.htm#Predictions_with_Totals_and_Moneylines",
                "pulled_at": "2026-08-24T00:00:00Z",
            })
        result, _ = MODULE.validate_prediction_candidate(pd.DataFrame(rows), 2026)
        self.assertFalse(result["valid"])
        self.assertIn("blanket/default", " ".join(result["reasons"]))

    def test_source_builder_treats_headerless_artifact_as_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "sagarin.csv"
            invalid.write_text("\n")
            previous = SOURCE_MODULE.SAGARIN
            SOURCE_MODULE.SAGARIN = invalid
            try:
                rows, audit = SOURCE_MODULE.load_sagarin({})
            finally:
                SOURCE_MODULE.SAGARIN = previous
            self.assertEqual(rows, [])
            self.assertEqual(audit[0]["rows"], 0)
            self.assertIn("invalid/rejected", audit[0]["status"])


if __name__ == "__main__":
    unittest.main()
