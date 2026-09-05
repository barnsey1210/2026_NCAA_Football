import unittest
from datetime import datetime, timezone

from scripts.war_room.build_war_room_market_matrix import (
    apply_projection_freeze,
    parse_timestamp,
    resolve_projection_freeze,
)


class WarRoomPregameProjectionFreezeTest(unittest.TestCase):
    def setUp(self):
        self.gid = "g_test"
        self.kickoff = parse_timestamp("2026-09-05T16:00:00Z")
        self.freeze_now = parse_timestamp("2026-09-05T16:01:00Z")

        self.previous_game = {
            "game_id": self.gid,
            "season": 2026,
            "week": 2,
            "away_team": "Away",
            "home_team": "Home",
            "kickoff_time": "2026-09-05T16:00:00Z",
            "state": "HYBRID",
            "authority": {
                "spread": {
                    "value": -3.1,
                    "projection_authority": "HYBRID_REFRESHED_SOURCES",
                },
                "total": {
                    "value": 55.5,
                    "projection_authority": "HYBRID_REFRESHED_SOURCES",
                },
            },
            "models": {
                "standard_spread": {"value_home_line": -4.5},
                "standard_total": {"value_total": 56.0},
                "shadow_spread": {"value_home_line": -2.8},
                "shadow_total": {"value_total": 54.9},
            },
            "shadow_readiness": {
                "spread_status": "READY",
                "total_status": "READY",
            },
            "standard_freshness": {
                "spread": {"updated_sources": 2},
                "total": {"updated_sources": 2},
            },
        }

    def test_first_postkickoff_build_captures_previous_pregame_state(self):
        previous_matrix = {
            "built_at": "2026-09-05T15:55:00Z",
            "games": [self.previous_game],
        }
        frozen = {}

        snapshot, created = resolve_projection_freeze(
            gid=self.gid,
            kickoff=self.kickoff,
            freeze_now=self.freeze_now,
            previous_matrix=previous_matrix,
            previous_matrix_built_at=parse_timestamp(
                previous_matrix["built_at"]
            ),
            previous_games_by_gid={self.gid: self.previous_game},
            frozen_games=frozen,
        )

        self.assertTrue(created)
        self.assertIs(snapshot, frozen[self.gid])
        self.assertEqual(snapshot["state"], "HYBRID")
        self.assertEqual(snapshot["authority"]["spread"]["value"], -3.1)
        self.assertEqual(
            snapshot["models"]["shadow_spread"]["value_home_line"],
            -2.8,
        )
        self.assertEqual(
            snapshot["source_matrix_built_at"],
            "2026-09-05T15:55:00Z",
        )

    def test_later_build_reuses_snapshot_even_if_current_models_change(self):
        frozen = {}

        first_snapshot, created = resolve_projection_freeze(
            gid=self.gid,
            kickoff=self.kickoff,
            freeze_now=self.freeze_now,
            previous_matrix={
                "built_at": "2026-09-05T15:55:00Z",
                "games": [self.previous_game],
            },
            previous_matrix_built_at=parse_timestamp(
                "2026-09-05T15:55:00Z"
            ),
            previous_games_by_gid={self.gid: self.previous_game},
            frozen_games=frozen,
        )
        self.assertTrue(created)

        changed_current_game = {
            "state": "UPDATED",
            "authority": {
                "spread": {"value": -9.5},
                "total": {"value": 63.0},
            },
            "models": {
                "shadow_spread": {"value_home_line": -8.0},
                "shadow_total": {"value_total": 62.0},
            },
            "shadow_readiness": {},
            "standard_freshness": {},
        }

        second_snapshot, created_again = resolve_projection_freeze(
            gid=self.gid,
            kickoff=self.kickoff,
            freeze_now=parse_timestamp("2026-09-05T20:00:00Z"),
            previous_matrix={
                "built_at": "2026-09-05T19:59:00Z",
                "games": [changed_current_game],
            },
            previous_matrix_built_at=parse_timestamp(
                "2026-09-05T19:59:00Z"
            ),
            previous_games_by_gid={self.gid: changed_current_game},
            frozen_games=frozen,
        )

        self.assertFalse(created_again)
        self.assertIs(second_snapshot, first_snapshot)

        apply_projection_freeze(
            changed_current_game,
            second_snapshot,
        )

        self.assertEqual(changed_current_game["state"], "HYBRID")
        self.assertEqual(
            changed_current_game["authority"]["spread"]["value"],
            -3.1,
        )
        self.assertEqual(
            changed_current_game["models"]["shadow_spread"][
                "value_home_line"
            ],
            -2.8,
        )

    def test_no_pregame_matrix_does_not_fabricate_snapshot(self):
        frozen = {}

        snapshot, created = resolve_projection_freeze(
            gid=self.gid,
            kickoff=self.kickoff,
            freeze_now=self.freeze_now,
            previous_matrix={
                "built_at": "2026-09-05T16:00:30Z",
                "games": [self.previous_game],
            },
            previous_matrix_built_at=parse_timestamp(
                "2026-09-05T16:00:30Z"
            ),
            previous_games_by_gid={self.gid: self.previous_game},
            frozen_games=frozen,
        )

        self.assertIsNone(snapshot)
        self.assertFalse(created)
        self.assertNotIn(self.gid, frozen)


if __name__ == "__main__":
    unittest.main()
