import unittest

from betting.close_derived_ev import (
    CloseDerivedEV,
    TotalCurve,
    TEAM_TOTAL_CENTS_PER_HALF,
    aggregate_ev,
    ev_result,
    fair_probability,
    implied_probability,
)
from betting.key_aware_spread_ev import SpreadEVCalculator
from pathlib import Path


class CloseDerivedEVTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_spread_key_number_curve(self):
        curve = SpreadEVCalculator(self.ROOT)
        result = curve.ticket_ev(4.0, 6.5, -110)
        self.assertIsNotNone(result)
        self.assertGreater(result["win_probability"], result["loss_probability"])
        self.assertGreater(result["push_probability"], 0)

    def test_total_curve_and_push_probability(self):
        curve = TotalCurve(self.ROOT / "data/research/historical_totals/master_totals_game_matrix_2021_2025.csv")
        (pw, pl, pp), sample = curve.probabilities(52.0, 53.0, "Under", 0.5)
        self.assertAlmostEqual(pw + pl + pp, 1.0, places=9)
        self.assertGreater(pp, 0)
        self.assertGreaterEqual(sample, 0)

    def test_moneyline_devig(self):
        p = fair_probability(-188, 155)
        self.assertAlmostEqual(p, 0.6247068022, places=9)
        result = ev_result(-108, 108, p, 1 - p, close_ev_method="moneyline_devig")
        self.assertAlmostEqual(result["close_ev_pct"], 0.2031390264, places=9)
        self.assertAlmostEqual(result["close_ev_expected_pl"], 21.93901486, places=7)

    def test_team_total_estimated_central_case(self):
        self.assertEqual(TEAM_TOTAL_CENTS_PER_HALF, 10.0)
        p0 = fair_probability(-115, -111)
        fair0 = -100 * p0 / (1 - p0)
        adjusted = -(100 + max(0, abs(fair0) - 100) + 4 * TEAM_TOTAL_CENTS_PER_HALF)
        p = implied_probability(adjusted)
        result = ev_result(100, 210, p, 1 - p)
        self.assertAlmostEqual(result["close_ev_pct"], 0.1724460781, places=9)
        self.assertAlmostEqual(result["close_ev_expected_pl"], 36.2136764, places=7)

    def test_push_probability_has_zero_payoff(self):
        result = ev_result(-110, 110, 0.50, 0.44, 0.06)
        self.assertAlmostEqual(result["close_ev_pct"], 0.0145454545, places=9)

    def test_pending_and_na_contract_names(self):
        self.assertIn("pending", {"pending", "unsupported_na"})
        self.assertIn("unsupported_na", {"pending", "unsupported_na"})

    def test_stake_weighted_aggregation(self):
        rows = [
            {"settled_risk": 100, "close_ev_pct": .10, "close_ev_expected_pl": 10, "realized_pl": 20},
            {"settled_risk": 300, "close_ev_pct": -.05, "close_ev_expected_pl": -15, "realized_pl": -30},
            {"settled_risk": 1000, "close_ev_pct": None, "close_ev_expected_pl": None, "realized_pl": 500},
        ]
        result = aggregate_ev(rows)
        self.assertEqual(result["close_ev_eligible"], 2)
        self.assertEqual(result["close_ev_risk"], 400)
        self.assertEqual(result["close_ev_expected_pl"], -5)
        self.assertEqual(result["close_ev_roi"], -0.0125)
        self.assertEqual(result["close_ev_realized_roi"], -0.025)
        self.assertEqual(result["close_ev_actual_vs_expected"], -0.0125)

    def test_weekly_and_source_aggregation_share_same_contract(self):
        week = [
            {"settled_risk": 110, "close_ev_pct": .04, "close_ev_expected_pl": 4.4, "realized_pl": 100},
            {"settled_risk": 90, "close_ev_pct": .02, "close_ev_expected_pl": 1.8, "realized_pl": -90},
        ]
        self.assertEqual(aggregate_ev(week), aggregate_ev(list(week)))


if __name__ == "__main__":
    unittest.main()
