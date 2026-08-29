import unittest

import pandas as pd

from betting.build_betting_activity_view import bet_period, strategy_tags
from betting.pull_google_sheet_bets import normalize_wager_frame


class BettingPagePipelineTests(unittest.TestCase):
    def test_published_sheet_normalization_rejects_summary_and_blank_rows(self):
        frame = pd.DataFrame([
            {"Date": "8/24/2026", "Bet Description": "Week 0", "Source": "Powers", "Sportsbook": "Draft Kings", "Bet Amount": "$50", "Sport": "NCAAF", "Bet": "USC / New Mexico State Over 59.5", "Bet Type": "Total"},
            {"Date": "", "Bet Description": "", "Source": "", "Sportsbook": "", "Bet Amount": "", "Sport": "", "Bet": "", "Bet Type": ""},
        ])
        normalized = normalize_wager_frame(frame)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized.iloc[0]["Source"], "Powers")

    def test_period_classification(self):
        self.assertEqual(bet_period({"Bet Description": "Week 0"}), "Week 0")
        self.assertEqual(bet_period({"Bet Description": "Week 2"}), "Week 2")
        self.assertEqual(bet_period({"Bet Description": "Win Total"}), "Futures")
        self.assertEqual(bet_period({"Bet Description": "Conf Title"}), "Futures")
        self.assertEqual(bet_period({"Bet Description": "Heisman"}), "Futures")
        self.assertEqual(bet_period({"Bet Description": "Bowl / Playoff"}), "Bowl / Playoff")
        self.assertEqual(bet_period({"Bet Description": "Week 14"}), "Conference Championships")

    def test_source_and_model_open_strategy_classification(self):
        self.assertIn("Powers", strategy_tags({"Source": " Powers ", "Bet Description": "Win Total"}))
        self.assertIn("Model", strategy_tags({"Source": "Model", "Bet Description": "Win Total"}))
        self.assertIn("Model", strategy_tags({"Source": "Tunes", "Bet Description": "Week 1"}))


if __name__ == "__main__":
    unittest.main()
