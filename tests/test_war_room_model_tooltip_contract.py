#!/usr/bin/env python3
"""Guards for canonical projection metadata passed to War Room tooltips."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/war_room/build_war_room_market_matrix.py"
PAGE_BUILDER = ROOT / "scripts/site/build_war_room_page.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("war_room_matrix", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WarRoomModelTooltipContractTests(unittest.TestCase):
    def test_render_path_consumes_passed_component_values(self):
        source = PAGE_BUILDER.read_text(encoding="utf-8")
        self.assertIn("const values = model?.component_values || {};", source)
        self.assertIn(
            "modelTooltip(game, game.models?.standard_spread, 'spread')",
            source,
        )
        self.assertIn(
            "modelTooltip(game, game.models?.standard_total, 'total')",
            source,
        )

    def test_selected_operational_model_exposes_existing_components(self):
        module = load_builder()
        game = {
            "operational_projections": {
                "spread": {
                    "model_id": module.STANDARD_SPREAD,
                    "selection_status": "AVAILABLE",
                    "weights_used": {"SP+": 0.2},
                }
            },
            "projections": {
                module.STANDARD_SPREAD: {
                    "component_values": {"SP+": 7.25},
                    "component_status": {"SP+": "PRESENT"},
                }
            },
        }

        summary = module.model_summary(game, module.STANDARD_SPREAD)

        self.assertEqual(summary["component_values"], {"SP+": 7.25})
        self.assertEqual(summary["component_status"], {"SP+": "PRESENT"})
        self.assertEqual(summary["weights_used"], {"SP+": 0.2})

    def test_missing_components_remain_missing(self):
        module = load_builder()
        game = {
            "operational_projections": {
                "total": {
                    "model_id": module.DEGRADED_TOTAL,
                    "selection_status": "AVAILABLE",
                    "missing_components": ["DRatings Total"],
                }
            },
            "projections": {
                module.DEGRADED_TOTAL: {
                    "component_values": {
                        "SP+": 51.4,
                        "Massey Dual": 48.8,
                        "DRatings Total": None,
                    },
                    "component_status": {"DRatings Total": "MISSING"},
                }
            },
        }

        summary = module.model_summary(game, module.STANDARD_TOTAL)

        self.assertIsNone(summary["component_values"]["DRatings Total"])
        self.assertEqual(summary["missing_components"], ["DRatings Total"])


class WarRoomMaturityStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_builder()
        cls.standard = {"source": "STANDARD", "status": "ACTIVE"}

    @staticmethod
    def freshness(status="PRE_GAME", watermark=None):
        return {
            "temporal_status": status,
            "watermark_date": watermark,
        }

    def state(self, week, spread_status="PRE_GAME", total_status="PRE_GAME", spread_authority=None, total_authority=None):
        return self.module.maturity_state(
            {"week": week},
            {},
            self.freshness(spread_status),
            self.freshness(total_status),
            spread_authority or self.standard,
            total_authority or self.standard,
        )

    def test_week_zero_initial_baseline_is_updated(self):
        self.assertEqual(self.state(0), "UPDATED")

    def test_later_pre_game_cycle_remains_stale(self):
        self.assertEqual(self.state(1), "STALE")

    def test_ready_shadow_authority_remains_shadow(self):
        component = {
            "shadow_spread_updated_team_count": 2,
            "away_spread_shadow_ready": True,
            "home_spread_shadow_ready": True,
        }
        state = self.module.maturity_state(
            {"week": 1},
            component,
            self.freshness(),
            self.freshness(),
            {"source": "SHADOW", "status": "ACTIVE"},
            self.standard,
        )
        self.assertEqual(state, "SHADOW")

    def test_hybrid_and_updated_transitions_are_preserved(self):
        self.assertEqual(self.state(1, spread_status="HYBRID"), "HYBRID")
        self.assertEqual(
            self.state(1, spread_status="UPDATED", total_status="UPDATED"),
            "UPDATED",
        )


if __name__ == "__main__":
    unittest.main()
