import unittest

from betting.build_betting_activity_view import (
    bet_source_group,
    build_open_weekly_performance,
    boolean,
    clv_eligible,
    summarize_records,
)


class BettingSourceCLVContractTest(unittest.TestCase):
    @staticmethod
    def weekly_row(week, source="Open", track=True, state="FINAL_CLOSE", points=1.0,
                   status="Won", stake=100, profit=90):
        return {
            "week": week, "bet_source_group": source, "is_open": status == "Open",
            "stake": stake, "realized_profit": profit, "status": status,
            "clv_pct_current": None, "track_close": track,
            "tracking_clv_state": state, "tracking_clv_points": points,
            "ev_current_pct": None,
        }

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

    def test_open_weekly_grouping_denominators_and_trend(self):
        rows = [
            self.weekly_row(0, points=1.0),
            self.weekly_row(0, source="Powers", points=9.0),
            self.weekly_row(1, state="UNAVAILABLE", points=None, status="Open", profit=0),
            self.weekly_row(1, state="NOT_APPLICABLE_POINT_CLV", points=None),
            self.weekly_row(2, points=2.0),
            self.weekly_row(3, points=-1.0, status="Lost", profit=-100),
            self.weekly_row(3, track=False, points=20.0),
        ]
        payload = build_open_weekly_performance(rows)
        self.assertEqual([row["label"] for row in payload["weeks"]], ["Week 0", "Week 1", "Week 2", "Week 3"])
        self.assertEqual(payload["season"]["bets"], 6)
        self.assertEqual(payload["reconciliation"]["weekly_open_bets"], 6)
        week1 = payload["weeks"][1]
        self.assertEqual(week1["track_close_unresolved"], 1)
        self.assertEqual(week1["track_close_not_applicable"], 1)
        self.assertIsNone(week1["eligible_avg_clv_points"])
        self.assertEqual(payload["trend"]["latest_resolved_week"], "Week 3")
        self.assertEqual(payload["trend"]["previous_resolved_week"], "Week 2")
        self.assertEqual(payload["trend"]["week_over_week_clv_change"], -3.0)
        self.assertAlmostEqual(payload["trend"]["rolling_3_resolved_week_avg_clv"], 2 / 3, places=3)


if __name__ == "__main__":
    unittest.main()
