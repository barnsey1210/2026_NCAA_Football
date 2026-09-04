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
            {
                "watermark_date": "2026-08-29",
                "week_cutoff_at": "2026-08-30T05:49:23Z",
            },
            team_meta or {},
            feed_meta or {},
        )

    @staticmethod
    def changed(date="2026-08-30"):
        return {
            "snapshot_date": "2026-08-30",
            "change_status": "UPDATED",
            "last_changed_at": f"{date}T05:00:00Z",
            "latest_accepted_update_at": f"{date}T06:00:00Z",
            "comparison_available": True,
        }

    @staticmethod
    def unchanged():
        return {
            "snapshot_date": "2026-08-30",
            "change_status": "NO_CHANGE",
            "last_changed_at": "2026-08-25T05:00:00Z",
            "latest_accepted_update_at": "2026-08-25T05:00:00Z",
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
            {
                "watermark_date": None,
                "week_cutoff_at": "2026-08-30T05:49:23Z",
            },
            {"TeamRankings": self.changed()},
            {},
        )
        source = result["sources"]["TeamRankings"]
        self.assertEqual(source["state"], "PRE_GAME")
        self.assertTrue(source["accepted_update"])
        self.assertEqual(result["updated_sources"], 1)
        self.assertEqual(result["temporal_status"], "UPDATED")

    def test_no_change_source_before_cutoff_is_not_an_accepted_update(self):
        unchanged = self.freshness(
            self.module.STANDARD_SPREAD,
            ["SP+"],
            {"SP+": self.unchanged()},
        )
        self.assertFalse(unchanged["sources"]["SP+"]["accepted_update"])

    def test_later_no_change_preserves_qualifying_accepted_update(self):
        metadata = self.changed()
        metadata["change_status"] = "NO_CHANGE"
        metadata["latest_check_status"] = "NO_CHANGE"
        result = self.freshness(
            self.module.STANDARD_SPREAD,
            ["TeamRankings"],
            {"TeamRankings": metadata},
        )
        self.assertTrue(result["sources"]["TeamRankings"]["accepted_update"])
        self.assertEqual(
            result["sources"]["TeamRankings"]["latest_check_status"],
            "NO_CHANGE",
        )

    def test_sagarin_rating_can_consume_projection_owner_evidence(self):
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            status = root / "status.csv"
            status.write_text(
                "source,snapshot_date,pulled_at,comparison_available\n"
                "Sagarin Rating,2026-09-06,2026-09-06T13:00:00Z,False\n"
            )
            team_change = root / "team.json"
            team_change.write_text('{"sources":{}}')
            projection_change = root / "projection.json"
            projection_change.write_text(json.dumps({"sources": {
                "Sagarin Rating": {
                    "latest_check_status": "NO_CHANGE",
                    "latest_accepted_update_at": "2026-09-06T12:00:00Z",
                    "comparison_available": True,
                }
            }}))
            loaded = self.module.load_team_source_snapshots(
                status,
                team_change,
                projection_change,
            )
            self.assertEqual(
                loaded["Sagarin Rating"]["latest_accepted_update_at"],
                "2026-09-06T12:00:00Z",
            )

    def test_incomplete_change_evidence_fails_closed(self):
        for metadata in (
            {
                "snapshot_date": "2026-08-30",
                "change_status": "UPDATED",
                "last_changed_at": None,
                "comparison_available": True,
                "latest_accepted_update_at": None,
            },
            {
                "snapshot_date": "2026-08-30",
                "change_status": "UPDATED",
                "last_changed_at": "2026-08-30T05:00:00Z",
                "comparison_available": False,
                "latest_accepted_update_at": None,
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

    def test_current_week_source_health_fixture(self):
        unchanged = self.unchanged()
        fpi = self.changed()
        fpi["latest_accepted_update_at"] = "2026-08-30T09:19:23Z"
        teamrankings = self.changed()
        teamrankings.update(
            change_status="NO_CHANGE",
            latest_check_status="NO_CHANGE",
            latest_accepted_update_at="2026-08-30T13:58:54Z",
        )
        dratings = self.changed()
        dratings["latest_accepted_update_at"] = "2026-08-30T16:25:53Z"
        massey = self.changed()
        massey["latest_accepted_update_at"] = "2026-08-30T14:01:02Z"
        unverified = {
            "snapshot_date": "2026-08-30",
            "comparison_available": False,
            "latest_accepted_update_at": None,
        }
        spread = {
            "SP+": unchanged,
            "FPI": fpi,
            "TeamRankings": teamrankings,
            "Sagarin Rating": unverified,
            "DRatings": dratings,
        }
        total = {
            "SP+": unchanged,
            "Massey Dual": massey,
            "Sagarin Total": None,
        }

        def color(metadata):
            if metadata is None:
                return "RED"
            if self.module.has_accepted_source_update(
                metadata,
                "2026-08-30T05:49:23Z",
            ):
                return "GREEN"
            return "YELLOW"

        self.assertEqual(
            {source: color(metadata) for source, metadata in spread.items()},
            {
                "SP+": "YELLOW",
                "FPI": "GREEN",
                "TeamRankings": "GREEN",
                "Sagarin Rating": "YELLOW",
                "DRatings": "GREEN",
            },
        )
        self.assertEqual(
            {source: color(metadata) for source, metadata in total.items()},
            {
                "SP+": "YELLOW",
                "Massey Dual": "GREEN",
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

    def test_three_accepted_spread_sources_use_normal_hybrid(self):
        result = self.freshness(
            self.module.STANDARD_SPREAD,
            ["SP+", "FPI", "TeamRankings", "DRatings"],
            {
                "SP+": self.unchanged(),
                "FPI": self.changed(),
                "TeamRankings": self.changed(),
            },
            {"DRatings Predictions": self.changed()},
        )
        self.assertEqual(result["updated_sources"], 3)
        self.assertEqual(result["temporal_status"], "HYBRID")
        self.assertEqual(result["authority_stage"], "HYBRID_AUTHORITY")

    def test_hybrid_blend_excludes_stale_game_source(self):
        game = self.game(self.module.STANDARD_SPREAD, ["FPI", "TeamRankings"])
        game["projections"] = {
            self.module.STANDARD_SPREAD: {
                "component_values": {"FPI": 4.0, "TeamRankings": 2.0},
                "weights": {"FPI": 0.2, "TeamRankings": 0.2},
            }
        }
        freshness = {
            "sources": {
                "FPI": {"state": "STALE", "accepted_update": True},
                "TeamRankings": {"state": "PRE_GAME", "accepted_update": True},
            }
        }
        hybrid = self.module.refreshed_standard_value(
            game,
            freshness,
            self.module.STANDARD_SPREAD,
            "value_home_line",
        )

        # Accepted provider evidence alone is not enough once that provider
        # predates a newer completed-game watermark for this matchup.
        # Only one current source remains, so HYBRID cannot be constructed.
        self.assertIsNone(hybrid)

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

    def test_weekend_hybrid_shadow_hybrid_authority_lifecycle(self):
        """Game authority follows provider freshness relative to team finals."""

        standard_id = self.module.STANDARD_SPREAD
        shadow_id = self.module.SHADOW_SPREAD

        game = {
            "game_id": "g-weekend-regression",
            "away_team": "Away",
            "home_team": "Home",
            "operational_projections": {
                "spread": {
                    "model_id": standard_id,
                    "official_model_id": standard_id,
                    "selection_status": "AVAILABLE",
                    "authority": "OFFICIAL_STANDARD",
                    "value_home_line": -3.5,
                },
            },
            "resolved_projections": {
                standard_id: {
                    "model_id": standard_id,
                    "selection_status": "AVAILABLE",
                    "authority": "OFFICIAL_STANDARD",
                    "component_status": {
                        "SP+": "PRESENT",
                        "FPI": "PRESENT",
                        "TeamRankings": "PRESENT",
                        "DRatings": "PRESENT",
                    },
                    "value_home_line": -3.5,
                },
                shadow_id: {
                    "model_id": shadow_id,
                    "selection_status": "AVAILABLE",
                    "component_status": {},
                    "value_home_line": -4.25,
                },
            },
            "projections": {
                standard_id: {
                    "value_home_line": -3.5,
                    "component_values": {
                        "SP+": 3.0,
                        "FPI": 6.8,
                        "TeamRankings": 6.6,
                        "DRatings": 4.0,
                    },
                    "weights": {
                        "SP+": 0.25,
                        "FPI": 0.25,
                        "TeamRankings": 0.25,
                        "DRatings": 0.25,
                    },
                },
                shadow_id: {
                    "value_home_line": -4.25,
                },
            },
        }

        friday_fpi = {
            "snapshot_date": "2026-09-04",
            "change_status": "UPDATED",
            "last_changed_at": "2026-09-04T12:00:00Z",
            "latest_accepted_update_at": "2026-09-04T12:05:00Z",
            "comparison_available": True,
        }
        friday_tr = {
            "snapshot_date": "2026-09-04",
            "change_status": "UPDATED",
            "last_changed_at": "2026-09-04T12:01:00Z",
            "latest_accepted_update_at": "2026-09-04T12:06:00Z",
            "comparison_available": True,
        }
        stale_sp = {
            "snapshot_date": "2026-08-31",
            "change_status": "NO_CHANGE",
            "last_changed_at": "2026-08-31T12:00:00Z",
            "latest_accepted_update_at": "2026-08-31T12:00:00Z",
            "comparison_available": True,
        }
        stale_dratings = {
            "snapshot_date": "2026-09-04",
            "change_status": "NO_CHANGE",
            "last_changed_at": "2026-08-31T12:00:00Z",
            "latest_accepted_update_at": "2026-08-31T12:00:00Z",
            "comparison_available": True,
        }

        team_meta_friday = {
            "SP+": stale_sp,
            "FPI": friday_fpi,
            "TeamRankings": friday_tr,
        }
        feed_meta_friday = {
            "DRatings Predictions": stale_dratings,
        }

        # Friday: no completed-game watermark is newer than the accepted
        # FPI/TR updates. Exactly two current sources => HYBRID.
        friday = self.module.model_freshness(
            game,
            standard_id,
            {
                "watermark_date": None,
                "week_cutoff_at": "2026-09-01T00:00:00Z",
            },
            team_meta_friday,
            feed_meta_friday,
        )
        self.assertEqual(friday["updated_sources"], 2)
        self.assertEqual(friday["temporal_status"], "HYBRID")

        partial_component = {
            "away_spread_shadow_ready": True,
            "home_spread_shadow_ready": False,
        }
        full_component = {
            "away_spread_shadow_ready": True,
            "home_spread_shadow_ready": True,
        }

        friday_authority = self.module.authority_resolution(
            game,
            partial_component,
            friday,
            standard_id,
            shadow_id,
            "value_home_line",
        )
        self.assertEqual(friday_authority["maturity"], "HYBRID")
        self.assertEqual(
            friday_authority["projection_authority"],
            "HYBRID_REFRESHED_SOURCES",
        )
        self.assertEqual(
            friday_authority["hybrid_components"],
            ["FPI", "TeamRankings"],
        )
        self.assertAlmostEqual(friday_authority["value"], -6.7)

        # Saturday after a completed game: Friday provider updates now predate
        # the game watermark and must no longer count toward HYBRID.
        saturday = self.module.model_freshness(
            game,
            standard_id,
            {
                "watermark_date": "2026-09-05",
                "week_cutoff_at": "2026-09-01T00:00:00Z",
            },
            team_meta_friday,
            feed_meta_friday,
        )
        self.assertEqual(saturday["sources"]["FPI"]["state"], "STALE")
        self.assertEqual(
            saturday["sources"]["TeamRankings"]["state"],
            "STALE",
        )
        self.assertEqual(saturday["updated_sources"], 0)

        # Only one Shadow side is ready: diagnostic PARTIAL only.
        partial_authority = self.module.authority_resolution(
            game,
            partial_component,
            saturday,
            standard_id,
            shadow_id,
            "value_home_line",
        )
        self.assertEqual(partial_authority["source"], "STANDARD")
        self.assertNotEqual(partial_authority["source"], "SHADOW")
        self.assertEqual(
            partial_authority["reason"],
            "shadow_partial_standard_retained",
        )

        partial_state = self.module.maturity_state(
            game,
            partial_component,
            saturday,
            saturday,
            partial_authority,
            partial_authority,
        )
        self.assertEqual(partial_state, "SHADOW_PARTIAL")

        # Once both teams have completed and full Shadow is available, stale
        # Friday provider updates remain below the HYBRID threshold. Shadow
        # becomes the game authority.
        shadow_authority = self.module.authority_resolution(
            game,
            full_component,
            saturday,
            standard_id,
            shadow_id,
            "value_home_line",
        )
        self.assertEqual(shadow_authority["source"], "SHADOW")
        self.assertEqual(shadow_authority["maturity"], "SHADOW")
        self.assertAlmostEqual(shadow_authority["value"], -4.25)
        self.assertEqual(
            shadow_authority["reason"],
            "full_two_team_shadow_active_below_standard_hybrid_threshold",
        )

        # Sunday provider refreshes occur after the Saturday watermark.
        sunday_fpi = dict(friday_fpi)
        sunday_fpi.update(
            snapshot_date="2026-09-06",
            last_changed_at="2026-09-06T12:00:00Z",
            latest_accepted_update_at="2026-09-06T12:05:00Z",
        )
        sunday_tr = dict(friday_tr)
        sunday_tr.update(
            snapshot_date="2026-09-06",
            last_changed_at="2026-09-06T12:01:00Z",
            latest_accepted_update_at="2026-09-06T12:06:00Z",
        )

        sunday = self.module.model_freshness(
            game,
            standard_id,
            {
                "watermark_date": "2026-09-05",
                "week_cutoff_at": "2026-09-01T00:00:00Z",
            },
            {
                "SP+": stale_sp,
                "FPI": sunday_fpi,
                "TeamRankings": sunday_tr,
            },
            feed_meta_friday,
        )
        self.assertEqual(sunday["sources"]["FPI"]["state"], "UPDATED")
        self.assertEqual(
            sunday["sources"]["TeamRankings"]["state"],
            "UPDATED",
        )
        self.assertEqual(sunday["updated_sources"], 2)
        self.assertEqual(sunday["temporal_status"], "HYBRID")

        sunday_authority = self.module.authority_resolution(
            game,
            full_component,
            sunday,
            standard_id,
            shadow_id,
            "value_home_line",
        )
        self.assertEqual(sunday_authority["source"], "STANDARD")
        self.assertEqual(sunday_authority["maturity"], "HYBRID")
        self.assertEqual(
            sunday_authority["projection_authority"],
            "HYBRID_REFRESHED_SOURCES",
        )

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
