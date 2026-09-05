import unittest

from betting.build_betting_activity_view import (
    bet_source_group,
    clv_eligible,
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
        self.assertEqual(
            bet_source_group({"Source": "Model"}),
            "Other",
        )
        self.assertEqual(
            bet_source_group({"Source": "Steam"}),
            "Other",
        )

    def test_clv_only_full_game_spread_total(self):
        game = {"game_id": "g1"}

        self.assertTrue(clv_eligible("Spread", game))
        self.assertTrue(clv_eligible("Game Total", game))

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


if __name__ == "__main__":
    unittest.main()
