#!/usr/bin/env python3
"""Regression tests for exact-slot War Room current-market fallback."""

from collections import defaultdict
from datetime import datetime, timezone
import unittest

from scripts.war_room.build_war_room_market_matrix import (
    merge_current_market_fallbacks,
)


def inventory():
    return defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(dict)
        )
    )


def quote(side, line, updated="2026-08-26T16:00:00Z"):
    return {
        "source": "The Odds API",
        "sportsbook": "BetMGM",
        "venue_type": "sportsbook",
        "market_type": "spread",
        "side": side,
        "line": line,
        "price": -110,
        "source_updated_at": updated,
        "freshness_status": "LIVE",
    }


def payload(sides, *, book="BetMGM", market="spread"):
    return {
        "built_at": "2026-08-26T16:01:00Z",
        "max_quote_age_hours": 18,
        "games": [
            {
                "game_id": "g1",
                "quotes": {book: {market: sides}},
            }
        ],
    }


class WarRoomMarketCoverageFallbackTests(unittest.TestCase):
    def test_complete_fresh_pair_fills_exact_missing_slot(self):
        quotes = inventory()
        accepted, rejected = merge_current_market_fallbacks(
            quotes,
            payload({
                "away": quote("away", 3.5),
                "home": quote("home", -3.5),
            }),
            {"BetMGM"},
            reference_time="2026-08-26T16:32:00Z",
            eligible_game_ids={"g1"},
        )
        self.assertEqual(len(accepted), 1)
        self.assertEqual(rejected, [])
        pair = quotes["g1"]["BetMGM"]["spread"]
        self.assertEqual(set(pair), {"away", "home"})
        self.assertTrue(all(
            q["selection_source"] == "CURRENT_MARKET_CONTRACT_FALLBACK"
            for q in pair.values()
        ))

    def test_latest_fast_valid_pair_always_wins(self):
        quotes = inventory()
        quotes["g1"]["BetMGM"]["spread"] = {
            "away": {"line": 4, "price": -110},
            "home": {"line": -4, "price": -110},
        }
        accepted, rejected = merge_current_market_fallbacks(
            quotes,
            payload({
                "away": quote("away", 3.5),
                "home": quote("home", -3.5),
            }),
            {"BetMGM"},
            reference_time="2026-08-26T16:32:00Z",
            eligible_game_ids={"g1"},
        )
        self.assertEqual(accepted, [])
        self.assertEqual(rejected, [])
        self.assertEqual(
            quotes["g1"]["BetMGM"]["spread"]["away"]["line"],
            4,
        )

    def test_stale_pair_is_rejected(self):
        quotes = inventory()
        accepted, rejected = merge_current_market_fallbacks(
            quotes,
            payload({
                "away": quote("away", 3.5, "2026-08-25T12:00:00Z"),
                "home": quote("home", -3.5, "2026-08-25T12:00:00Z"),
            }),
            {"BetMGM"},
            reference_time="2026-08-26T16:32:00Z",
            eligible_game_ids={"g1"},
        )
        self.assertEqual(accepted, [])
        self.assertEqual(rejected[0]["reason"], "STALE_CURRENT_PAIR")
        self.assertFalse(quotes["g1"]["BetMGM"]["spread"])

    def test_incomplete_pair_is_rejected(self):
        quotes = inventory()
        accepted, rejected = merge_current_market_fallbacks(
            quotes,
            payload({"home": quote("home", -3.5)}),
            {"BetMGM"},
            reference_time="2026-08-26T16:32:00Z",
            eligible_game_ids={"g1"},
        )
        self.assertEqual(accepted, [])
        self.assertEqual(
            rejected[0]["reason"],
            "INVALID_OR_INCOMPLETE_CURRENT_PAIR",
        )

    def test_nonparticipating_provider_is_not_carried_forward(self):
        quotes = inventory()
        accepted, rejected = merge_current_market_fallbacks(
            quotes,
            payload(
                {
                    "away": quote("away", 3.5),
                    "home": quote("home", -3.5),
                },
                book="Kalshi",
            ),
            set(),
            reference_time="2026-08-26T16:32:00Z",
            eligible_game_ids={"g1"},
        )
        self.assertEqual(accepted, [])
        self.assertEqual(rejected, [])
        self.assertNotIn("g1", quotes)


if __name__ == "__main__":
    unittest.main()
