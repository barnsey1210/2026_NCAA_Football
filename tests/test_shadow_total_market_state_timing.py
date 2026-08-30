#!/usr/bin/env python3
"""No-lookahead regressions for completed-week Shadow Total market state."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MARKET = load(
    "shadow_total_market_state",
    "scripts/research/build_market_implied_power_ratings.py",
)
SHADOW = load(
    "shadow_total_features",
    "scripts/postgame/build_shadow_team_game_features_2026.py",
)
MATRIX = load(
    "shadow_total_matrix",
    "scripts/war_room/build_war_room_market_matrix.py",
)


PARAMS = {
    "lookback_weeks": 99,
    "half_life_weeks": 8.0,
    "ridge_alpha": 1.0,
}
INFERENCE = "2026-08-30T12:00:00Z"


def game(
    game_id,
    week,
    away,
    home,
    line,
    line_timestamp,
    kickoff,
    *,
    completed=True,
    line_kind="completed_frozen_close",
    selection_source="FROZEN_CLOSE",
):
    return {
        "season": 2026,
        "week": week,
        "game_id": game_id,
        "away_team": away,
        "home_team": home,
        "neutral_site": False,
        "closing_home_spread": line,
        "line_timestamp": line_timestamp,
        "kickoff": kickoff,
        "completed": completed,
        "line_kind": line_kind,
        "selection_source": selection_source,
    }


class ShadowTotalMarketStateTimingTests(unittest.TestCase):
    def setUp(self):
        self.games = pd.DataFrame([
            game(
                "g1", 0, "Sacramento State", "Eastern Michigan", -9.5,
                "2026-08-29T12:01:31Z", "2026-08-29T22:30:00Z",
            ),
            game(
                "g7", 0, "San Jose State", "USC", -38.5,
                "2026-08-29T12:01:31Z", "2026-08-29T19:00:00Z",
            ),
            game(
                "future", 1, "Future Away", "Future Home", -3.0,
                "2026-08-30T11:00:00Z", "2026-09-05T16:00:00Z",
                completed=False,
                line_kind="upcoming_canonical_current",
                selection_source="CURRENT_MARKET_CONTRACT",
            ),
            game(
                "live", 0, "Live Away", "Live Home", -7.0,
                "2026-08-29T19:05:00Z", "2026-08-29T19:00:00Z",
            ),
        ])

    def test_week_zero_state_uses_only_frozen_pregame_week_zero_closes(self):
        state, source, _ = MARKET.completed_week_state(
            self.games, 0, PARAMS, INFERENCE
        )
        self.assertEqual(set(source.game_id), {"g1", "g7"})
        self.assertEqual(set(source.week), {0})
        self.assertEqual(set(source.selection_source), {"FROZEN_CLOSE"})
        self.assertEqual(set(state.through_week), {0})
        self.assertEqual(set(state.max_source_week), {0})
        self.assertEqual(set(state.state_kind), {"COMPLETED_WEEK_FROZEN_CLOSES"})
        self.assertTrue(state.accepted_for_shadow.all())
        self.assertEqual(set(state.source_game_count), {2})
        self.assertIn("USC", set(state.team))
        self.assertIn("Sacramento State", set(state.team))

    def test_loader_uses_results_completion_and_matchups_frozen_close(self):
        matchups = {
            "games": [{
                "game": {
                    "season": 2026,
                    "week": 0,
                    "game_id": "g7",
                    "away_team": "San Jose State",
                    "home_team": "USC",
                    "status": "scheduled",
                    "completed": False,
                },
                "market": {"spread": {
                    "home_line": -38.5,
                    "book": "Pinnacle",
                    "updated_at": "2026-08-29T12:01:31Z",
                    "availability_status": "CLOSING",
                    "availability_reason": "Pregame market frozen at kickoff",
                }},
            }]
        }
        results = {"games": [{
            "game_id": "g7",
            "start_date": "2026-08-29T19:00:00Z",
        }]}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            matchup_path = root / "matchups.json"
            result_path = root / "results.json"
            matchup_path.write_text(json.dumps(matchups))
            result_path.write_text(json.dumps(results))
            with patch.object(MARKET, "MATCHUPS_2026", matchup_path), patch.object(
                MARKET, "RESULTS_2026", result_path
            ):
                loaded, rejected = MARKET.load_2026_board()
        self.assertEqual(rejected, [])
        self.assertTrue(bool(loaded.iloc[0].completed))
        self.assertEqual(loaded.iloc[0].closing_home_spread, -38.5)
        self.assertEqual(loaded.iloc[0].selection_source, "FROZEN_CLOSE")

    def test_loader_rejects_post_kickoff_close(self):
        matchups = {
            "games": [{
                "game": {
                    "season": 2026, "week": 0, "game_id": "g7",
                    "away_team": "San Jose State", "home_team": "USC",
                },
                "market": {"spread": {
                    "home_line": -20.5,
                    "updated_at": "2026-08-29T19:01:00Z",
                    "availability_status": "CLOSING",
                    "availability_reason": "Pregame market frozen at kickoff",
                }},
            }]
        }
        results = {"games": [{
            "game_id": "g7", "start_date": "2026-08-29T19:00:00Z",
        }]}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            matchup_path = root / "matchups.json"
            result_path = root / "results.json"
            matchup_path.write_text(json.dumps(matchups))
            result_path.write_text(json.dumps(results))
            with patch.object(MARKET, "MATCHUPS_2026", matchup_path), patch.object(
                MARKET, "RESULTS_2026", result_path
            ):
                with self.assertRaisesRegex(SystemExit, "No canonical"):
                    MARKET.load_2026_board()

    def test_future_and_post_kickoff_rows_cannot_enter_week_zero(self):
        source = MARKET.completed_week_games(self.games, 0, INFERENCE)
        self.assertNotIn("future", set(source.game_id))
        self.assertNotIn("live", set(source.game_id))
        timestamps = pd.to_datetime(source.line_timestamp, utc=True)
        kickoffs = pd.to_datetime(source.kickoff, utc=True)
        self.assertTrue((timestamps < kickoffs).all())

    def test_exact_completed_week_is_required_without_stale_fallback(self):
        state, _, _ = MARKET.completed_week_state(
            self.games, 0, PARAMS, INFERENCE
        )
        usc = SHADOW.entering_market_rating(state, "USC", 0, INFERENCE)
        sacramento = SHADOW.entering_market_rating(
            state, "Sacramento State", 0, INFERENCE
        )
        self.assertIsNotNone(usc)
        self.assertIsNotNone(sacramento)
        self.assertIsNone(
            SHADOW.entering_market_rating(state, "USC", 1, INFERENCE)
        )

        stale = state.copy()
        stale["through_week"] = -1
        self.assertIsNone(
            SHADOW.entering_market_rating(stale, "USC", 0, INFERENCE)
        )

    def test_state_cutoff_after_inference_is_rejected(self):
        state, _, _ = MARKET.completed_week_state(
            self.games, 0, PARAMS, INFERENCE
        )
        state["state_cutoff"] = "2026-08-31T00:00:00Z"
        self.assertIsNone(
            SHADOW.entering_market_rating(state, "USC", 0, INFERENCE)
        )

    def test_opponent_market_ratings_populate_for_sjsu_and_emu(self):
        state, _, _ = MARKET.completed_week_state(
            self.games, 0, PARAMS, INFERENCE
        )
        sjsu_opponent = SHADOW.entering_market_rating(
            state, "USC", 0, INFERENCE
        )
        emu_opponent = SHADOW.entering_market_rating(
            state, "Sacramento State", 0, INFERENCE
        )
        self.assertIsInstance(sjsu_opponent, float)
        self.assertIsInstance(emu_opponent, float)

    def test_total_readiness_remains_per_team(self):
        partial = MATRIX.shadow_readiness({
            "away_spread_shadow_ready": True,
            "home_spread_shadow_ready": True,
            "away_total_shadow_ready": True,
            "home_total_shadow_ready": False,
        })
        ready = MATRIX.shadow_readiness({
            "away_spread_shadow_ready": True,
            "home_spread_shadow_ready": True,
            "away_total_shadow_ready": True,
            "home_total_shadow_ready": True,
        })
        self.assertEqual(partial["total_status"], "PARTIAL")
        self.assertEqual(ready["total_status"], "READY")
        self.assertEqual(ready["spread_status"], "READY")


if __name__ == "__main__":
    unittest.main()
