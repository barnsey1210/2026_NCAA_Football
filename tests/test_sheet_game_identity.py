import unittest

import pandas as pd

from betting.build_betting_activity_view import game_match
from betting.pull_google_sheet_bets import attach_game_identity
from betting.track_close_resolver import (
    authoritative_frozen_quote,
    point_clv,
    resolve_game,
)


def canonical_game(game_id="g7", week=0, away="San Jose State", home="USC"):
    return {
        "game_id": game_id,
        "week": week,
        "date": "2026-08-29",
        "away_team": away,
        "home_team": home,
        "quotes": {
            "Pinnacle": {
                "spread": {
                    "away": {"line": 21.5, "price": -110, "freshness_status": "FROZEN_CLOSE"},
                    "home": {"line": -21.5, "price": -110, "freshness_status": "FROZEN_CLOSE"},
                },
                "total": {
                    "over": {"line": 61.5, "price": -110, "freshness_status": "FROZEN_CLOSE"},
                    "under": {"line": 61.5, "price": -110, "freshness_status": "FROZEN_CLOSE"},
                },
            }
        },
    }


class SheetGameIdentityTests(unittest.TestCase):
    def test_valid_sheet_id_bypasses_fuzzy_resolver_and_attaches_canonical_fields(self):
        games = [canonical_game()]
        frame = pd.DataFrame([{
            "Bet": "Completely unrelated text",
            "Bet Type": "Side",
            "Week": "Week 99",
            "Game": "08/29 San Jose State @ USC",
            "Game ID": "g7",
        }])
        row = attach_game_identity(frame, games).iloc[0]
        self.assertEqual(row["game_id"], "g7")
        self.assertEqual(row["game_identity_source"], "SHEET_GAME_ID")
        self.assertEqual(row["canonical_game_week"], 0)
        self.assertEqual(row["canonical_away_team"], "San Jose State")

    def test_invalid_populated_sheet_id_fails_closed(self):
        games = [canonical_game()]
        row = {
            "raw_sheet_game_id": "g-does-not-exist",
            "Bet": "USC",
            "team_guess": "USC",
            "Bet Type": "Side",
            "Week": "Week 0",
        }
        resolved, reason = resolve_game(row, games)
        self.assertIsNone(resolved)
        self.assertEqual(reason, "invalid_sheet_game_id")

    def test_game_label_mismatch_is_warning_not_identity_override(self):
        frame = pd.DataFrame([{
            "Bet": "USC",
            "Bet Type": "Side",
            "Week": "Week 0",
            "Game": "08/29 Hawaii @ Stanford",
            "Game ID": "g7",
        }])
        row = attach_game_identity(frame, [canonical_game()]).iloc[0]
        self.assertEqual(row["game_id"], "g7")
        self.assertTrue(row["game_label_mismatch"])

    def test_blank_sheet_id_uses_fallback_and_is_audited(self):
        frame = pd.DataFrame([{
            "Bet": "USC",
            "team_guess": "USC",
            "Bet Type": "Side",
            "Week": "Week 0",
            "Game": "",
            "Game ID": "",
        }])
        row = attach_game_identity(frame, [canonical_game()]).iloc[0]
        self.assertEqual(row["game_id"], "g7")
        self.assertEqual(row["game_identity_source"], "FALLBACK_RESOLVER")

    def test_spread_and_total_orientation_use_sheet_game_id(self):
        game = canonical_game()
        away = {"raw_sheet_game_id": "g7", "Bet Type": "Side", "team_guess": "San Jose State", "bet_line": 23.5}
        resolved, reason = resolve_game(away, [game])
        self.assertEqual(reason, "sheet_game_id")
        quote, _ = authoritative_frozen_quote(away, resolved)
        self.assertEqual(point_clv(away, quote), 2.0)

        under = {"raw_sheet_game_id": "g7", "Bet Type": "Total", "side": "Under", "bet_line": 63.5}
        resolved, _ = resolve_game(under, [game])
        quote, _ = authoritative_frozen_quote(under, resolved)
        self.assertEqual(point_clv(under, quote), 2.0)

    def test_activity_linkage_prefers_game_id_for_settled_and_open_rows(self):
        game = canonical_game()
        by_id = {"g7": game}
        for status in ("Won", "Open"):
            resolved, reason = game_match(
                {"game_id": "g7", "game_identity_source": "SHEET_GAME_ID", "status": status},
                {},
                by_id,
            )
            self.assertEqual(resolved["game_id"], "g7")
            self.assertEqual(reason, "sheet_game_id")


if __name__ == "__main__":
    unittest.main()
