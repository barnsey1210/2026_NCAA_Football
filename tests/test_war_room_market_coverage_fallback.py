#!/usr/bin/env python3
"""Regression tests for exact-slot War Room current-market fallback."""

from collections import defaultdict
from datetime import datetime, timezone
import csv
import tempfile
from pathlib import Path
import unittest

from scripts.markets.build_current_market_contract import (
    load_pregame_close_pairs,
    post_kickoff_quote,
)
from scripts.war_room.build_war_room_market_matrix import (
    merge_current_market_fallbacks,
    resolve_kickoff_time,
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
    def test_market_kickoff_remains_authoritative(self):
        self.assertEqual(
            resolve_kickoff_time(
                "g16",
                {"g16": "2026-09-03T22:05:00Z"},
                {"g16": "2026-09-03T22:00:00Z"},
                {"g16": "2026-09-03T21:55:00Z"},
            ),
            "2026-09-03T22:05:00Z",
        )

    def test_schedule_kickoff_fills_missing_market_kickoff(self):
        self.assertEqual(
            resolve_kickoff_time(
                "g16",
                {},
                {"g16": "2026-09-03T22:00:00Z"},
                {},
            ),
            "2026-09-03T22:00:00Z",
        )

    def test_completed_kickoff_remains_final_fallback(self):
        self.assertEqual(
            resolve_kickoff_time(
                "g16",
                {},
                {},
                {"g16": "2026-09-03T22:00:00Z"},
            ),
            "2026-09-03T22:00:00Z",
        )

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

    def test_frozen_close_remains_eligible_after_normal_freshness_window(self):
        quotes = inventory()
        frozen = {
            "away": {
                **quote("away", 3.5, "2026-08-29T15:59:00Z"),
                "freshness_status": "FROZEN_CLOSE",
            },
            "home": {
                **quote("home", -3.5, "2026-08-29T15:59:00Z"),
                "freshness_status": "FROZEN_CLOSE",
            },
        }
        contract = payload(frozen)
        contract["games"][0]["availability_status"] = "CLOSING"
        accepted, rejected = merge_current_market_fallbacks(
            quotes,
            contract,
            {"BetMGM"},
            reference_time="2026-09-02T16:00:00Z",
            eligible_game_ids=set(),
        )
        self.assertEqual(len(accepted), 1)
        self.assertEqual(rejected, [])
        self.assertTrue(all(
            item["selection_source"] == "FROZEN_CLOSE"
            for item in quotes["g1"]["BetMGM"]["spread"].values()
        ))

    def test_close_history_excludes_post_kickoff_pair(self):
        headers = [
            "canonical_game_id", "book", "market", "side", "line",
            "price", "source_updated_at", "paired_market_id", "available",
        ]
        rows = [
            ["g1", "BetMGM", "spread", "away", "3.5", "-110", "2026-08-29T15:59:00Z", "pregame", "true"],
            ["g1", "BetMGM", "spread", "home", "-3.5", "-110", "2026-08-29T15:59:00Z", "pregame", "true"],
            ["g1", "BetMGM", "spread", "away", "10.5", "-110", "2026-08-29T16:01:00Z", "live", "true"],
            ["g1", "BetMGM", "spread", "home", "-10.5", "-110", "2026-08-29T16:01:00Z", "live", "true"],
        ]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "history.csv"
            with path.open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(headers)
                writer.writerows(rows)
            pairs = load_pregame_close_pairs(
                path,
                {"g1": datetime(2026, 8, 29, 16, tzinfo=timezone.utc)},
            )
        selected = pairs["g1"]["BetMGM"]["spread"]
        self.assertEqual(selected["away"]["line"], 3.5)
        self.assertEqual(selected["home"]["line"], -3.5)
        self.assertTrue(all(
            item["freshness_status"] == "FROZEN_CLOSE"
            for item in selected.values()
        ))
        self.assertTrue(post_kickoff_quote(
            "2026-08-29T16:01:00Z",
            "2026-08-29T16:00:00Z",
        ))


if __name__ == "__main__":
    unittest.main()
