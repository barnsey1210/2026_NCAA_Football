#!/usr/bin/env python3
"""Focused accepted-change tests for War Room authority freshness."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/war_room/build_war_room_market_matrix.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("war_room_matrix", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuthorityFreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_builder()

    def game(self, model_id, components):
        return {
            "resolved_projections": {
                model_id: {
                    "selection_status": "AVAILABLE",
                    "component_status": {
                        component: "PRESENT"
                        for component in components
                    },
                }
            }
        }

    def freshness(self, model_id, components, team_meta=None, feed_meta=None):
        return self.module.model_freshness(
            self.game(model_id, components),
            model_id,
            {"watermark_date": "2026-08-29"},
            team_meta or {},
            feed_meta or {},
        )

    @staticmethod
    def changed(date="2026-08-30"):
        return {
            "snapshot_date": "2026-08-30",
            "change_status": "UPDATED",
            "last_changed_at": f"{date}T05:00:00Z",
            "comparison_available": True,
        }

    @staticmethod
    def unchanged():
        return {
            "snapshot_date": "2026-08-30",
            "change_status": "NO_CHANGE",
            "last_changed_at": "2026-08-25T05:00:00Z",
            "comparison_available": True,
        }

    def test_later_same_value_pull_is_available_but_not_updated(self):
        result = self.freshness(
            self.module.STANDARD_SPREAD,
            ["SP+"],
            {"SP+": self.unchanged()},
        )
        self.assertEqual(result["participating_sources"], 1)
        self.assertEqual(result["updated_sources"], 0)
        self.assertEqual(result["sources"]["SP+"]["state"], "STALE")

    def test_one_accepted_change_does_not_activate_hybrid(self):
        result = self.freshness(
            self.module.STANDARD_SPREAD,
            ["SP+", "FPI"],
            {
                "SP+": self.changed(),
                "FPI": self.unchanged(),
            },
        )
        self.assertEqual(result["updated_sources"], 1)
        self.assertEqual(result["temporal_status"], "STALE")
        self.assertEqual(result["authority_stage"], "BELOW_HYBRID_THRESHOLD")
        self.assertTrue(result["sources"]["SP+"]["accepted_update"])

    def test_source_update_is_independent_of_pregame_game_state(self):
        result = self.module.model_freshness(
            self.game(self.module.STANDARD_SPREAD, ["TeamRankings"]),
            self.module.STANDARD_SPREAD,
            {"watermark_date": None},
            {"TeamRankings": self.changed()},
            {},
        )
        source = result["sources"]["TeamRankings"]
        self.assertEqual(source["state"], "PRE_GAME")
        self.assertTrue(source["accepted_update"])
        self.assertEqual(result["updated_sources"], 0)
        self.assertEqual(result["temporal_status"], "PRE_GAME")

    def test_no_change_source_is_not_an_accepted_update(self):
        unchanged = self.freshness(
            self.module.STANDARD_SPREAD,
            ["SP+"],
            {"SP+": self.unchanged()},
        )
        self.assertFalse(unchanged["sources"]["SP+"]["accepted_update"])

    def test_incomplete_change_evidence_fails_closed(self):
        for metadata in (
            {
                "snapshot_date": "2026-08-30",
                "change_status": "UPDATED",
                "last_changed_at": None,
                "comparison_available": True,
            },
            {
                "snapshot_date": "2026-08-30",
                "change_status": "UPDATED",
                "last_changed_at": "2026-08-30T05:00:00Z",
                "comparison_available": False,
            },
        ):
            with self.subTest(metadata=metadata):
                result = self.freshness(
                    self.module.STANDARD_SPREAD,
                    ["TeamRankings"],
                    {"TeamRankings": metadata},
                )
                self.assertFalse(
                    result["sources"]["TeamRankings"]["accepted_update"]
                )

    def test_current_week_one_source_health_fixture(self):
        unchanged = self.unchanged()
        unverified = {
            "snapshot_date": "2026-08-30",
            "comparison_available": False,
        }
        spread = {
            "SP+": unchanged,
            "FPI": unchanged,
            "TeamRankings": self.changed(),
            "Sagarin Rating": unverified,
            "DRatings": unverified,
        }
        total = {
            "SP+": unchanged,
            "Massey Dual": unverified,
            "Sagarin Total": None,
        }

        def color(metadata):
            if metadata is None:
                return "RED"
            if self.module.has_accepted_source_update(metadata):
                return "GREEN"
            return "YELLOW"

        self.assertEqual(
            {source: color(metadata) for source, metadata in spread.items()},
            {
                "SP+": "YELLOW",
                "FPI": "YELLOW",
                "TeamRankings": "GREEN",
                "Sagarin Rating": "YELLOW",
                "DRatings": "YELLOW",
            },
        )
        self.assertEqual(
            {source: color(metadata) for source, metadata in total.items()},
            {
                "SP+": "YELLOW",
                "Massey Dual": "YELLOW",
                "Sagarin Total": "RED",
            },
        )

    def test_unavailable_component_remains_nonparticipating(self):
        game = {
            "resolved_projections": {
                self.module.STANDARD_SPREAD: {
                    "selection_status": "UNAVAILABLE",
                    "component_status": {"SP+": "MISSING"},
                }
            }
        }
        result = self.module.model_freshness(
            game,
            self.module.STANDARD_SPREAD,
            {"watermark_date": None},
            {"SP+": self.changed()},
            {},
        )
        self.assertFalse(result["sources"]["SP+"]["participating"])
        self.assertEqual(result["participating_sources"], 0)

    def test_two_accepted_changes_activate_hybrid(self):
        result = self.freshness(
            self.module.STANDARD_SPREAD,
            ["SP+", "FPI", "TeamRankings"],
            {
                "SP+": self.changed(),
                "FPI": self.changed(),
                "TeamRankings": self.unchanged(),
            },
        )
        self.assertEqual(result["updated_sources"], 2)
        self.assertEqual(result["temporal_status"], "HYBRID")
        self.assertEqual(result["authority_stage"], "HYBRID_AUTHORITY")

    def test_spread_and_total_transition_independently(self):
        spread = self.freshness(
            self.module.STANDARD_SPREAD,
            ["SP+", "TeamRankings"],
            {
                "SP+": self.changed(),
                "TeamRankings": self.changed(),
            },
        )
        total = self.freshness(
            self.module.STANDARD_TOTAL,
            ["SP+", "Massey Dual"],
            {"SP+": self.changed()},
            {
                "Massey Games": {
                    "snapshot_date": "2026-08-30",
                }
            },
        )
        self.assertEqual(spread["temporal_status"], "UPDATED")
        self.assertEqual(total["updated_sources"], 1)
        self.assertEqual(total["temporal_status"], "STALE")

    def test_unproven_game_feeds_remain_available_but_not_updated(self):
        for model_id, component, key in (
            (self.module.STANDARD_SPREAD, "DRatings", "DRatings Predictions"),
            (self.module.STANDARD_TOTAL, "Massey Dual", "Massey Games"),
        ):
            with self.subTest(component=component):
                result = self.freshness(
                    model_id,
                    [component],
                    feed_meta={key: {"snapshot_date": "2026-08-30"}},
                )
                self.assertEqual(result["participating_sources"], 1)
                self.assertEqual(result["updated_sources"], 0)
                self.assertEqual(result["sources"][component]["state"], "STALE")

    def test_change_before_watermark_does_not_count(self):
        result = self.freshness(
            self.module.STANDARD_SPREAD,
            ["TeamRankings"],
            {"TeamRankings": self.changed("2026-08-28")},
        )
        self.assertEqual(result["updated_sources"], 0)

    def test_audited_shadow_states_do_not_become_hybrid(self):
        stale = {"temporal_status": "STALE", "watermark_date": "2026-08-29"}
        standard = {"source": "STANDARD", "status": "ACTIVE"}
        shadow = {"source": "SHADOW", "status": "ACTIVE"}

        ready = {
            "away_spread_shadow_ready": True,
            "home_spread_shadow_ready": True,
            "away_total_shadow_ready": True,
            "home_total_shadow_ready": True,
        }
        partial = {
            "away_spread_shadow_ready": False,
            "home_spread_shadow_ready": True,
            "away_total_shadow_ready": False,
            "home_total_shadow_ready": True,
        }
        spread_ready_total_partial = {
            "away_spread_shadow_ready": True,
            "home_spread_shadow_ready": True,
            "away_total_shadow_ready": False,
            "home_total_shadow_ready": True,
        }

        cases = (
            ("g19", ready, shadow, shadow, "SHADOW"),
            ("g22", partial, standard, standard, "SHADOW_PARTIAL"),
            ("g42", spread_ready_total_partial, shadow, standard, "SHADOW"),
        )

        for game_id, component, spread_authority, total_authority, expected in cases:
            with self.subTest(game_id=game_id):
                state = self.module.maturity_state(
                    {"game_id": game_id, "week": 1},
                    component,
                    stale,
                    stale,
                    spread_authority,
                    total_authority,
                )
                self.assertEqual(state, expected)
                self.assertNotEqual(state, "HYBRID")


if __name__ == "__main__":
    unittest.main()
