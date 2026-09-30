import unittest

from pull_actionnetwork_win_totals_api import action_config, action_market_url
from pulls.pull_actionnetwork_conference_futures_api import action_market_url as conference_market_url
from scripts.markets.pull_actionnetwork_playoff_futures import market_url


class ActionFuturesBookIdTests(unittest.TestCase):
    def test_all_action_market_requests_use_frontend_book_ids(self):
        ids = action_config()["book_ids"]
        expected = "bookIds=79%2C123%2C68%2C69%2C71%2C1665%2C15"
        self.assertIn(expected, action_market_url("https://example.test/wins", ids))
        self.assertIn(expected, conference_market_url("https://example.test/conference", ids))
        self.assertIn(expected, market_url("title", ids))

    def test_consensus_and_unapproved_books_are_not_executable(self):
        config = action_config()
        self.assertFalse(config["books"]["15"]["executable"])
        self.assertFalse(config["books"]["79"]["executable"])
        self.assertFalse(config["books"]["71"]["executable"])
        self.assertTrue(config["books"]["1665"]["executable"])
        self.assertEqual(config["books"]["1665"]["brand"], "BetMGM")
        self.assertEqual(config["books"]["1665"]["display_name"], "BetMGM OH")
        self.assertEqual(config["books"]["1665"]["source_name"], "betmgmoh")
        self.assertEqual(
            {detail["brand"] for detail in config["books"].values() if detail["executable"]},
            {"DraftKings", "FanDuel", "Caesars", "BetMGM"},
        )


if __name__ == "__main__":
    unittest.main()
