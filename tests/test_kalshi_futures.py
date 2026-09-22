import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PULL = load("pull_kalshi_futures", "scripts/markets/pull_kalshi_futures.py")
CONTRACT = load("build_current_futures_market_contract", "scripts/markets/build_current_futures_market_contract.py")


class KalshiFuturesTests(unittest.TestCase):
    def test_official_quadratic_taker_fee_and_net_american_conversion(self):
        self.assertEqual(PULL.kalshi_taker_fee(0.34, "quadratic", 1), 0.02)
        self.assertEqual(PULL.american_from_cost(0.36), 178)
        self.assertIsNone(PULL.kalshi_taker_fee(0.34, "flat", 1))

    def test_event_fee_override_wins_over_series_metadata(self):
        terms = PULL.fee_terms(
            {"fee_type": "quadratic", "fee_multiplier": 1},
            {"fee_type_override": "quadratic_with_maker_fees", "fee_multiplier_override": 0.5},
        )
        self.assertEqual(terms, {"fee_type": "quadratic_with_maker_fees", "fee_multiplier": 0.5})

    def test_win_total_yes_no_semantics(self):
        team, threshold = PULL.parse_win_total_team_and_threshold(
            {"title": "Will Alabama win at least 10 games this season?"}
        )
        self.assertEqual((team, threshold, threshold - 0.5), ("Alabama", 10, 9.5))

    def test_stale_kalshi_payload_is_rejected_without_carry_forward(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "kalshi.json"
            path.write_text(json.dumps({"pulled_at": (datetime.now(timezone.utc) - timedelta(hours=27)).isoformat()}))
            self.assertIsNone(CONTRACT.current_kalshi_payload(path))

    def test_provider_selection_uses_fee_adjusted_price(self):
        quote = CONTRACT.kalshi_quote({
            "american_odds": 178,
            "ask_cents": 34,
            "entry_fee": 0.02,
            "effective_cost": 0.36,
            "market": {"ticker": "KXNCAAF-27-TEST", "pulled_at": "2026-09-22T00:00:00Z"},
        })
        price, provider = CONTRACT.best_price({"DraftKings": {"price": 170}, "Kalshi": quote})
        self.assertEqual((price, provider), (178, "Kalshi"))
        self.assertEqual(quote["display"], "Kalshi 34¢ (+178)")
        self.assertEqual(quote["provider_type"], "exchange")

    def test_national_title_series_is_in_scope(self):
        self.assertEqual(PULL.NATIONAL_TITLE_SERIES, "KXNCAAF")


if __name__ == "__main__":
    unittest.main()
