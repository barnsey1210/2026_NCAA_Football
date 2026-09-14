import importlib.util
import unittest
from pathlib import Path

SCRIPT=Path("scripts/war_room/build_war_room_market_matrix.py")

spec=importlib.util.spec_from_file_location(
    "war_room_matrix",
    SCRIPT,
)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class MissingWeekCutoffFallbackTest(unittest.TestCase):

    def test_later_accepted_date_qualifies_without_exact_cutoff(self):
        meta={
            "latest_accepted_update_at":
                "2026-09-06T08:39:45Z"
        }

        self.assertTrue(
            mod.has_accepted_source_update(
                meta,
                None,
                "2026-09-05",
            )
        )

    def test_same_day_does_not_qualify_without_exact_cutoff(self):
        meta={
            "latest_accepted_update_at":
                "2026-09-05T23:59:00Z"
        }

        self.assertFalse(
            mod.has_accepted_source_update(
                meta,
                None,
                "2026-09-05",
            )
        )

    def test_exact_cutoff_remains_authoritative_when_available(self):
        meta={
            "latest_accepted_update_at":
                "2026-09-06T05:00:00Z"
        }

        self.assertFalse(
            mod.has_accepted_source_update(
                meta,
                "2026-09-06T06:24:22Z",
                "2026-09-05",
            )
        )


if __name__ == "__main__":
    unittest.main()

class AcceptedUpdateStateTest(unittest.TestCase):

    def test_authority_source_counts_when_accepted_and_updated(self):
        self.assertTrue(
            mod.authority_source_is_current({
                "accepted_update": True,
                "state": "UPDATED",
            })
        )

    def test_authority_source_does_not_count_stale(self):
        self.assertFalse(
            mod.authority_source_is_current({
                "accepted_update": True,
                "state": "STALE",
            })
        )

class AuthorityCurrentFallbackTest(unittest.TestCase):

    def test_explicit_authority_current_can_count_stale_diagnostic_state(self):
        self.assertTrue(
            mod.authority_source_is_current({
                "accepted_update": True,
                "state": "STALE",
                "authority_current": True,
            })
        )

    def test_exact_cutoff_stale_source_remains_excluded(self):
        self.assertFalse(
            mod.authority_source_is_current({
                "accepted_update": True,
                "state": "STALE",
                "authority_current": False,
            })
        )

class AcceptedProviderFallbackScopeTest(unittest.TestCase):

    def test_game_feed_can_use_date_only_fallback(self):
        meta={
            "latest_accepted_update_at":
                "2026-09-06T16:52:11Z"
        }

        self.assertTrue(
            mod.has_accepted_source_update(
                meta,
                None,
                "2026-09-05",
            )
        )

    def test_team_rating_can_use_date_only_fallback(self):
        meta={
            "latest_accepted_update_at":
                "2026-09-06T15:16:16Z"
        }

        self.assertTrue(
            mod.has_accepted_source_update(
                meta,
                None,
                "2026-09-05",
            )
        )

class GameFeedAuthorityFallbackIntegrationTest(unittest.TestCase):

    def test_game_feed_accepted_after_watermark_counts_current(self):
        game = {
            "game_id": "test-game",
            "resolved_projections": {
                mod.STANDARD_SPREAD: {
                    "selection_status": "AVAILABLE",
                    "component_status": {
                        "DRatings": "PRESENT",
                    },
                },
            },
        }

        result = mod.model_freshness(
            game,
            mod.STANDARD_SPREAD,
            {
                "watermark_date": "2026-09-05",
                "week_cutoff_at": None,
            },
            {},
            {
                "DRatings Predictions": {
                    "snapshot_date": "2026-09-06",
                    "pulled_at": "2026-09-06T17:00:00Z",
                    "latest_check_status": "NO_CHANGE",
                    "latest_accepted_update_at":
                        "2026-09-06T16:52:11Z",
                    "comparison_available": True,
                },
            },
        )

        source = result["sources"]["DRatings"]

        self.assertTrue(source["accepted_update"])
        self.assertTrue(source["authority_current"])
        self.assertEqual(result["updated_sources"], 1)
        self.assertEqual(result["temporal_status"], "UPDATED")

    def test_game_feed_accepted_on_watermark_date_still_fails_closed(self):
        game = {
            "game_id": "test-game",
            "resolved_projections": {
                mod.STANDARD_SPREAD: {
                    "selection_status": "AVAILABLE",
                    "component_status": {
                        "DRatings": "PRESENT",
                    },
                },
            },
        }

        result = mod.model_freshness(
            game,
            mod.STANDARD_SPREAD,
            {
                "watermark_date": "2026-09-05",
                "week_cutoff_at": None,
            },
            {},
            {
                "DRatings Predictions": {
                    "snapshot_date": "2026-09-05",
                    "pulled_at": "2026-09-05T23:59:00Z",
                    "latest_check_status": "NO_CHANGE",
                    "latest_accepted_update_at":
                        "2026-09-05T23:59:00Z",
                    "comparison_available": True,
                },
            },
        )

        self.assertFalse(
            result["sources"]["DRatings"]["accepted_update"]
        )
        self.assertFalse(
            result["sources"]["DRatings"]["authority_current"]
        )
        self.assertEqual(result["updated_sources"], 0)
