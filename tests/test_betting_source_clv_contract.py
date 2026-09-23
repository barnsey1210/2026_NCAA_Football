import unittest

from betting.build_betting_activity_view import (
    bet_source_group,
    boolean,
    clv_eligible,
    summarize_records,
)


class BettingSourceCLVContractTest(unittest.TestCase):
    def test_source_groups(self):
        self.assertEqual(
            bet_source_group({"Source": "Open"}),
            "Open",
        )
        self.assertEqual(
            bet_source_group({"Source": "Powers"}),
            "Powers",
        )
        self.assertEqual(bet_source_group({"Source": "Steam"}), "Steam")
        self.assertEqual(bet_source_group({"Source": "  OPEN  "}), "Open")
        self.assertEqual(bet_source_group({"Source": " powers "}), "Powers")
        self.assertEqual(
            bet_source_group({"Source": "Model"}),
            "Other",
        )

    def test_clv_only_full_game_spread_total(self):
        game = {"game_id": "g1"}

        self.assertTrue(clv_eligible("Spread", game, True))
        self.assertTrue(clv_eligible("Game Total", game, True))
        self.assertFalse(clv_eligible("Spread", game, False))

        self.assertFalse(clv_eligible("Moneyline", game))
        self.assertFalse(clv_eligible("1H Spread", game))
        self.assertFalse(clv_eligible("1H Total", game))
        self.assertFalse(clv_eligible("2H Spread", game))
        self.assertFalse(clv_eligible("2H Total", game))
        self.assertFalse(clv_eligible("Win Total", game))
        self.assertFalse(clv_eligible("Conference Future", game))

    def test_unlinked_game_market_not_clv_eligible(self):
        self.assertFalse(clv_eligible("Spread", None))
        self.assertFalse(clv_eligible("Game Total", None))

    def test_checkbox_parsing(self):
        for value in (True, "TRUE", "true", "1", "yes", "Y", " checked "):
            self.assertTrue(boolean(value), value)
        for value in (False, "FALSE", "false", "0", "no", "", None, "unchecked"):
            self.assertFalse(boolean(value), value)

    def test_checkbox_denominator_and_clv_signs(self):
        def row(track, state, points, status="Won"):
            return {
                "is_open": False, "stake": 100, "realized_profit": 90,
                "status": status, "clv_pct_current": None,
                "track_close": track, "tracking_clv_state": state,
                "tracking_clv_points": points, "ev_current_pct": None,
            }

        metrics = summarize_records([
            row(True, "FINAL_CLOSE", 2.0),
            row(True, "FINAL_CLOSE", -1.0, "Lost"),
            row(True, "FINAL_CLOSE", 0.0, "Push"),
            row(True, "UNAVAILABLE", None),
            row(False, "FINAL_CLOSE", 9.0),
        ])
        self.assertEqual(metrics["track_close_eligible"], 4)
        self.assertEqual(metrics["track_close_resolved"], 3)
        self.assertEqual(metrics["track_close_unresolved"], 1)
        self.assertEqual(metrics["clv_matched"], 3)
        self.assertEqual(metrics["positive_clv"], 1)
        self.assertEqual(metrics["eligible_positive_clv"], 1)
        self.assertAlmostEqual(metrics["eligible_positive_clv_pct"], 1 / 3, places=4)
        self.assertAlmostEqual(metrics["eligible_avg_clv_points"], 1 / 3, places=3)

    def test_moneyline_na_is_not_unresolved(self):
        metrics = summarize_records([{
            "is_open": False, "stake": 100, "realized_profit": 10,
            "status": "Won", "clv_pct_current": None,
            "track_close": True,
            "tracking_clv_state": "NOT_APPLICABLE_POINT_CLV",
            "tracking_clv_points": None, "ev_current_pct": None,
        }])
        self.assertEqual(metrics["track_close_eligible"], 1)
        self.assertEqual(metrics["track_close_not_applicable"], 1)
        self.assertEqual(metrics["track_close_unresolved"], 0)


if __name__ == "__main__":
    unittest.main()
