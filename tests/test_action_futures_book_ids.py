import unittest

from pull_actionnetwork_win_totals_api import action_config, action_market_url, domain_book_ids
from pulls.pull_actionnetwork_conference_futures_api import action_market_url as conference_market_url
from scripts.markets.pull_actionnetwork_playoff_futures import (
    domain_book_ids as playoff_book_ids,
    executable_provider_counts,
    market_url,
    normalized_book_map,
)


class ActionFuturesBookIdTests(unittest.TestCase):
    def test_healthy_domains_retain_shared_approved_book_ids(self):
        config = action_config()
        ids = config["book_ids"]
        expected = "bookIds=79%2C123%2C68%2C69%2C71%2C1665%2C15"
        self.assertEqual(domain_book_ids(config, "win_totals"), ids)
        self.assertEqual(config["domains"]["conference_titles"]["book_ids"], ids)
        self.assertEqual(playoff_book_ids(config, "national_title"), ids)
        self.assertIn(expected, action_market_url("https://example.test/wins", ids))
        self.assertIn(expected, conference_market_url("https://example.test/conference", ids))
        self.assertIn(expected, market_url("title", ids))

    def test_make_cfp_uses_proven_ohio_dk_and_caesars_feeds(self):
        config = action_config()
        ids = playoff_book_ids(config, "make_cfp")
        self.assertEqual(ids, [79, 2029, 2031, 69, 71, 15])
        self.assertNotIn(68, ids)
        self.assertNotIn(123, ids)
        self.assertNotIn(1665, ids)
        self.assertIn("bookIds=79%2C2029%2C2031%2C69%2C71%2C15", market_url("cfp", ids))

    def test_make_cfp_draftkings_oh_normalizes_with_23_row_breadth(self):
        config = action_config()
        books = normalized_book_map(config, [{"id": 2031, "display_name": "DK OH"}])
        market = {"books": [{"book_id": 2031, "odds": [{"team_id": n} for n in range(23)]}]}
        self.assertEqual(books["2031"], "DraftKings")
        self.assertEqual(executable_provider_counts(market, config, "make_cfp"), {"DraftKings": 23})

    def test_consensus_and_unapproved_books_are_not_executable(self):
        config = action_config()
        self.assertFalse(config["books"]["15"]["executable"])
        self.assertFalse(config["books"]["79"]["executable"])
        self.assertFalse(config["books"]["71"]["executable"])
        self.assertTrue(config["books"]["1665"]["executable"])
        self.assertEqual(config["books"]["1665"]["brand"], "BetMGM")
        self.assertEqual(config["books"]["1665"]["display_name"], "BetMGM OH")
        self.assertEqual(config["books"]["1665"]["source_name"], "betmgmoh")
        self.assertEqual(config["books"]["2029"]["brand"], "Caesars")
        self.assertEqual(config["books"]["2031"]["brand"], "DraftKings")
        self.assertEqual(
            {detail["brand"] for detail in config["books"].values() if detail["executable"]},
            {"DraftKings", "FanDuel", "Caesars", "BetMGM"},
        )


if __name__ == "__main__":
    unittest.main()
