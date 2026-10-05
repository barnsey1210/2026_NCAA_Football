import importlib.util
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_current_futures_market_contract",
    ROOT / "scripts/markets/build_current_futures_market_contract.py",
)
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
POLICY = json.loads((ROOT / "config/futures_book_eligibility.json").read_text())


def annotated(domain, segment):
    quotes = {
        book: {"price": price, "source": "retained test observation"}
        for book, price in {
            "DraftKings": 500,
            "FanDuel": 400,
            "BetMGM": 350,
            "Caesars": 300,
            "Kalshi": 900,
        }.items()
    }
    quotes["Kalshi"]["provider_type"] = "exchange"
    return BUILDER.annotate_quotes(
        quotes, market_domain=domain, segment=segment, eligibility=POLICY
    )


class FuturesBookEligibilityTests(unittest.TestCase):
    def test_g6_win_totals_exclude_draftkings_and_betmgm(self):
        quotes = annotated("win_totals", "g6")
        for book in ("DraftKings", "BetMGM"):
            self.assertFalse(quotes[book]["eligible_for_best"])
            self.assertEqual(quotes[book]["exclusion_reason"], "ACTION_SOURCE_STALE_CONTENT")
        for book in ("FanDuel", "Caesars"):
            self.assertTrue(quotes[book]["eligible_for_best"])

    def test_power_win_totals_keep_draftkings_and_betmgm(self):
        quotes = annotated("win_totals", "power")
        self.assertTrue(quotes["DraftKings"]["eligible_for_best"])
        self.assertTrue(quotes["BetMGM"]["eligible_for_edge"])

    def test_g6_conference_titles_exclude_only_draftkings(self):
        quotes = annotated("conference_titles", "g6")
        self.assertFalse(quotes["DraftKings"]["eligible_for_best"])
        for book in ("FanDuel", "BetMGM", "Caesars"):
            self.assertTrue(quotes[book]["eligible_for_edge"])

    def test_power_conference_titles_keep_draftkings(self):
        quotes = annotated("conference_titles", "power")
        self.assertTrue(quotes["DraftKings"]["eligible_for_best"])

    def test_kalshi_is_reference_only_in_every_domain(self):
        for domain, segment in (
            ("win_totals", "power"),
            ("conference_titles", "g6"),
            ("make_cfp", "all"),
            ("national_title", "all"),
        ):
            quote = annotated(domain, segment)["Kalshi"]
            self.assertFalse(quote["eligible_for_best"])
            self.assertFalse(quote["eligible_for_edge"])
            self.assertEqual(quote["quote_status"], "REFERENCE_ONLY")
            self.assertEqual(quote["exclusion_reason"], "EXCHANGE_REFERENCE_ONLY")

    def test_no_eligible_sportsbook_means_no_best(self):
        quotes = {"Kalshi": annotated("national_title", "all")["Kalshi"]}
        self.assertEqual(BUILDER.best_price(quotes), (None, None))

    def test_excluded_quotes_keep_provenance(self):
        quotes = annotated("win_totals", "g6")
        self.assertIn("DraftKings", quotes)
        self.assertEqual(quotes["DraftKings"]["source"], "retained test observation")
        self.assertEqual(quotes["DraftKings"]["market_domain"], "win_totals")
        self.assertEqual(quotes["DraftKings"]["segment"], "g6")

    def test_cli_help_does_not_execute_refresh(self):
        result = subprocess.run(
            ["python3", "scripts/futures/run_fast_futures_publication.py", "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("usage:", result.stdout)
        self.assertNotIn("run_fast_futures_refresh.py", result.stdout)

    def test_ui_has_per_tab_persistence_reset_and_client_recalculation(self):
        source = (ROOT / "futures_dashboard.js").read_text()
        for token in (
            "ncaaf-futures-books-v1:${mode}",
            "localStorage.setItem(tabStorageKey(state.mode)",
            "localStorage.removeItem(tabStorageKey(state.mode))",
            "Reset trusted defaults",
            "function effectiveRow(source)",
            "USER_EXCLUDED",
            "EXCHANGE_REFERENCE_ONLY",
            "visibleRows().map(effectiveRow)",
        ):
            self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
