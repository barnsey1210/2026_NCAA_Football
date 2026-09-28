import unittest

import pandas as pd

from pull_actionnetwork_win_totals_api import choose_brand_rows, market_season


class ActionWinTotalsSeasonTests(unittest.TestCase):
    def test_provider_market_name_not_internal_slug_defines_season(self):
        url = (
            "https://api.actionnetwork.com/web/v1/leagues/2/futures/"
            "ncaaf_futures_special_fixture_10997_2027_ncaaf_regular_season_total_wins"
        )
        payload = {"name": "2026 NCAAF Regular Season - Total Wins"}
        self.assertIn("_2027_", url)
        self.assertEqual(market_season(payload), 2026)

    def test_consensus_only_action_payload_leaves_mergeable_empty_schema(self):
        rows = choose_brand_rows(pd.DataFrame(), "OH", "state")
        self.assertIn("pulled_at", rows.columns)
        self.assertIn("book", rows.columns)
        self.assertIn("win_total", rows.columns)
