import unittest

import pandas as pd

from pull_actionnetwork_win_totals_api import (
    action_config,
    action_market_url,
    choose_brand_rows,
    domain_book_ids,
    market_season,
    represented_requested_books,
)


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

    def test_frontend_book_ids_are_always_added(self):
        config = action_config()
        url = action_market_url("https://api.actionnetwork.com/web/v1/leagues/2/futures/example", domain_book_ids(config, "win_totals"))
        self.assertIn("bookIds=79%2C123%2C68%2C69%2C71%2C1665%2C15", url)

    def test_consensus_only_is_not_executable_action_coverage(self):
        config = action_config()
        represented = represented_requested_books(
            {"books": [{"book_id": 15, "odds": [{"money": 100}]}]},
            set(config["book_ids"]),
        )
        executable = {int(key) for key, detail in config["books"].items() if detail["executable"]}
        self.assertEqual(represented, {15})
        self.assertFalse(represented.intersection(executable))
