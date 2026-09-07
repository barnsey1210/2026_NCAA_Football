import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/war_room/build_war_room_market_matrix.py"

spec = importlib.util.spec_from_file_location(
    "war_room_matrix_manual_override",
    MODULE,
)

mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ManualProjectionValueTest(unittest.TestCase):

    def test_spread_selected_sources_are_equal_weighted(self):
        game = {
            "projections": {
                mod.STANDARD_SPREAD: {
                    "component_values": {
                        "SP+": 7.0,
                        "FPI": 5.0,
                        "TeamRankings": 3.0,
                        "DRatings": 1.0,
                    },
                    "component_status": {
                        "SP+": "PRESENT",
                        "FPI": "PRESENT",
                        "TeamRankings": "PRESENT",
                        "DRatings": "PRESENT",
                    },
                }
            }
        }

        result = mod.manual_projection_value(
            game,
            model_id=mod.STANDARD_SPREAD,
            field="value_home_line",
            selected_sources=[
                "FPI",
                "TeamRankings",
                "DRatings",
            ],
        )

        self.assertAlmostEqual(result["value"], -3.0)

        self.assertEqual(
            result["participating_sources"],
            ["FPI", "TeamRankings", "DRatings"],
        )

        self.assertAlmostEqual(
            result["weights_used"]["FPI"],
            1 / 3,
        )

        self.assertEqual(result["status"], "FULL")

    def test_total_selected_sources_are_equal_weighted(self):
        game = {
            "projections": {
                mod.STANDARD_TOTAL: {
                    "component_values": {
                        "SP+": 60.0,
                        "Massey Dual": 56.0,
                        "DRatings Total": 58.0,
                    },
                    "component_status": {
                        "SP+": "PRESENT",
                        "Massey Dual": "PRESENT",
                        "DRatings Total": "PRESENT",
                    },
                }
            }
        }

        result = mod.manual_projection_value(
            game,
            model_id=mod.STANDARD_TOTAL,
            field="value_total",
            selected_sources=[
                "SP+",
                "DRatings Total",
            ],
        )

        self.assertAlmostEqual(result["value"], 59.0)


class ManualMissingSourceTest(unittest.TestCase):

    def test_missing_selected_source_is_disclosed(self):
        game = {
            "projections": {
                mod.STANDARD_SPREAD: {
                    "component_values": {
                        "FPI": 6.0,
                        "TeamRankings": 4.0,
                        "DRatings": None,
                    },
                    "component_status": {
                        "FPI": "PRESENT",
                        "TeamRankings": "PRESENT",
                        "DRatings": "MISSING",
                    },
                }
            }
        }

        result = mod.manual_projection_value(
            game,
            model_id=mod.STANDARD_SPREAD,
            field="value_home_line",
            selected_sources=[
                "FPI",
                "TeamRankings",
                "DRatings",
            ],
        )

        self.assertAlmostEqual(result["value"], -5.0)

        self.assertEqual(
            result["missing_sources"],
            ["DRatings"],
        )

        self.assertEqual(result["status"], "DEGRADED")


class ManualOverlayIsolationTest(unittest.TestCase):

    def game(self):
        return {
            "projections": {
                mod.STANDARD_SPREAD: {
                    "component_values": {
                        "SP+": 8.0,
                        "FPI": 6.0,
                        "TeamRankings": 4.0,
                        "DRatings": 2.0,
                    },
                    "component_status": {
                        "SP+": "PRESENT",
                        "FPI": "PRESENT",
                        "TeamRankings": "PRESENT",
                        "DRatings": "PRESENT",
                    },
                },
                mod.STANDARD_TOTAL: {
                    "component_values": {
                        "SP+": 60.0,
                        "Massey Dual": 58.0,
                        "DRatings Total": 56.0,
                    },
                    "component_status": {
                        "SP+": "PRESENT",
                        "Massey Dual": "PRESENT",
                        "DRatings Total": "PRESENT",
                    },
                },
            }
        }

    def best(self):
        return {
            "spread": {
                "away": {"line": 4.0},
                "home": {"line": -4.0},
            },
            "total": {
                "over": {"line": 57.0},
                "under": {"line": 57.0},
            },
        }

    def test_manual_overlay_does_not_replace_auto_authority(self):
        spread_authority = {
            "source": "STANDARD",
            "maturity": "HYBRID",
            "value": -5.0,
        }

        total_authority = {
            "source": "STANDARD",
            "maturity": "HYBRID",
            "value": 59.0,
        }

        overlay = mod.manual_operator_overlay(
            self.game(),
            {
                "mode": "MANUAL",
                "spread_sources": [
                    "FPI",
                    "TeamRankings",
                    "DRatings",
                ],
                "total_sources": [
                    "SP+",
                    "Massey Dual",
                    "DRatings Total",
                ],
            },
            auto_spread_authority=spread_authority,
            auto_total_authority=total_authority,
            best_sportsbook=self.best(),
        )

        self.assertEqual(
            spread_authority["value"],
            -5.0,
        )

        self.assertEqual(
            spread_authority["source"],
            "STANDARD",
        )

        self.assertEqual(
            overlay["auto_authority"]["spread"],
            spread_authority,
        )

        self.assertAlmostEqual(
            overlay["manual"]["spread"]["value"],
            -4.0,
        )

        self.assertIsNotNone(
            overlay["manual_edges"]["spread"],
        )

    def test_auto_mode_has_no_manual_projection_or_edges(self):
        overlay = mod.manual_operator_overlay(
            self.game(),
            {
                "mode": "AUTO",
                "spread_sources": [
                    "FPI",
                    "TeamRankings",
                    "DRatings",
                ],
                "total_sources": [
                    "SP+",
                    "Massey Dual",
                    "DRatings Total",
                ],
            },
            auto_spread_authority={
                "source": "STANDARD",
                "value": -5.0,
            },
            auto_total_authority={
                "source": "STANDARD",
                "value": 59.0,
            },
            best_sportsbook=self.best(),
        )

        self.assertEqual(overlay["mode"], "AUTO")
        self.assertIsNone(overlay["manual"]["spread"])
        self.assertIsNone(overlay["manual"]["total"])
        self.assertIsNone(
            overlay["manual_edges"]["spread"]
        )
        self.assertIsNone(
            overlay["manual_edges"]["total"]
        )


class ProjectionFreezeIsolationTest(unittest.TestCase):

    def test_projection_snapshot_does_not_capture_operator_model(self):
        game = {
            "game_id": "g1",
            "season": 2026,
            "week": 2,
            "away_team": "Away",
            "home_team": "Home",
            "kickoff_time":
                "2026-09-12T16:00:00+00:00",
            "state": "HYBRID",
            "authority": {
                "spread": {"value": -5.0},
                "total": {"value": 59.0},
            },
            "models": {},
            "shadow_readiness": {},
            "standard_freshness": {},
            "operator_model": {
                "mode": "MANUAL",
            },
        }

        snapshot = mod.projection_freeze_payload(
            game,
            "2026-09-12T15:59:00+00:00",
            "2026-09-12T16:00:01+00:00",
        )

        self.assertNotIn(
            "operator_model",
            snapshot,
        )


if __name__ == "__main__":
    unittest.main()
