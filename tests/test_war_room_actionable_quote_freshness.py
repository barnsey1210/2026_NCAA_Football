import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/war_room/build_war_room_market_matrix.py"

spec = importlib.util.spec_from_file_location(
    "war_room_market_matrix_under_test",
    SCRIPT,
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def quote(book, line, side, updated, freshness=None):
    row = {
        "book": book,
        "market": "total",
        "side": side,
        "line": line,
        "price": -110,
        "last_update": updated,
    }
    if freshness is not None:
        row["freshness_status"] = freshness
    return row


class WarRoomActionableQuoteFreshnessTests(unittest.TestCase):
    def test_old_quote_disappears_and_cannot_win_best(self):
        inventory = {
            "g-test": {
                "DraftKings": {
                    "total": {
                        "over": quote(
                            "DraftKings",
                            60.5,
                            "over",
                            "2026-09-05T23:40:00+00:00",
                        ),
                        "under": quote(
                            "DraftKings",
                            60.5,
                            "under",
                            "2026-09-05T23:40:00+00:00",
                        ),
                    }
                },
                "FanDuel": {
                    "total": {
                        "over": quote(
                            "FanDuel",
                            61.5,
                            "over",
                            "2026-09-06T00:20:00+00:00",
                        ),
                        "under": quote(
                            "FanDuel",
                            61.5,
                            "under",
                            "2026-09-06T00:20:00+00:00",
                        ),
                    }
                },
            }
        }

        removed = mod.prune_non_actionable_quote_inventory(
            inventory,
            reference_time="2026-09-06T01:00:00+00:00",
        )

        self.assertNotIn(
            "total",
            inventory["g-test"]["DraftKings"],
        )
        self.assertIn(
            "total",
            inventory["g-test"]["FanDuel"],
        )

        self.assertEqual(len(removed), 1)
        self.assertEqual(
            removed[0]["reason"],
            "ACTIONABLE_QUOTE_TOO_OLD",
        )

        best = mod.best_quote(
            inventory["g-test"],
            "total",
            "over",
            allowed_books=["DraftKings", "FanDuel"],
        )

        self.assertIsNotNone(best)
        self.assertEqual(best["book"], "FanDuel")
        self.assertEqual(best["line"], 61.5)

    def test_frozen_close_is_not_pruned(self):
        inventory = {
            "g-final": {
                "DraftKings": {
                    "spread": {
                        "home": {
                            "book": "DraftKings",
                            "line": -3.5,
                            "price": -110,
                            "last_update": "2026-09-01T12:00:00+00:00",
                            "freshness_status": "FROZEN_CLOSE",
                        },
                        "away": {
                            "book": "DraftKings",
                            "line": 3.5,
                            "price": -110,
                            "last_update": "2026-09-01T12:00:00+00:00",
                            "freshness_status": "FROZEN_CLOSE",
                        },
                    }
                }
            }
        }

        removed = mod.prune_non_actionable_quote_inventory(
            inventory,
            reference_time="2026-09-06T01:00:00+00:00",
        )

        self.assertEqual(removed, [])
        self.assertIn(
            "spread",
            inventory["g-final"]["DraftKings"],
        )


if __name__ == "__main__":
    unittest.main()
