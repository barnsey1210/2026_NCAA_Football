import unittest

from scripts.results.build_game_results_2026 import (
    align_provider_result_to_site_game,
    closing_market_fields,
)


def quote(line, status="FROZEN_CLOSE", book="Pinnacle", venue_type="sharp_reference"):
    return {
        "line": line,
        "freshness_status": status,
        "sportsbook": book,
        "venue_type": venue_type,
        "source_updated_at": "2026-09-11T12:01:20Z",
    }


class GameResultsMarketCloseTests(unittest.TestCase):
    def test_reversed_neutral_orientation_swaps_scores_and_pgwe(self):
        aligned = align_provider_result_to_site_game(
            {
                "away_team": "West Virginia",
                "home_team": "Virginia",
                "away_points": 38,
                "home_points": 27,
                "away_postgame_win_probability": 0.97,
                "home_postgame_win_probability": 0.03,
            },
            {"away_team": "Virginia", "home_team": "West Virginia"},
        )
        self.assertEqual(aligned["away_score"], 27)
        self.assertEqual(aligned["home_score"], 38)
        self.assertEqual(aligned["away_postgame_win_probability"], 0.03)
        self.assertEqual(aligned["home_postgame_win_probability"], 0.97)
        self.assertTrue(aligned["provider_orientation_reversed"])

    def test_canonical_frozen_pinnacle_precedes_legacy_close(self):
        canonical = {"quotes": {
            "DraftKings": {
                "spread": {"home": quote(-3.0, book="DraftKings", venue_type="sportsbook")},
                "total": {"over": quote(54.5, book="DraftKings", venue_type="sportsbook")},
            },
            "Pinnacle": {
                "spread": {"home": quote(-3.5)},
                "total": {"over": quote(53.5)},
            },
        }}
        resolved = closing_market_fields(
            canonical, {"closing_home_spread": -2.5, "closing_total": 52.0}
        )
        self.assertEqual(resolved["closing_home_spread"], -3.5)
        self.assertEqual(resolved["closing_total"], 53.5)
        self.assertEqual(resolved["closing_home_spread_book"], "Pinnacle")
        self.assertEqual(resolved["closing_total_book"], "Pinnacle")
        self.assertEqual(
            resolved["closing_home_spread_source"],
            "data/site/current_market_contract.json",
        )

    def test_legacy_close_is_preserved_when_frozen_quote_is_missing(self):
        resolved = closing_market_fields(
            {}, {"closing_home_spread": 2.5, "closing_total": 47.0}
        )
        self.assertEqual(resolved["closing_home_spread"], 2.5)
        self.assertEqual(resolved["closing_total"], 47.0)
        self.assertEqual(
            resolved["closing_total_source"],
            "data/snapshots/preseason/preseason_db.json",
        )

    def test_non_frozen_quotes_are_rejected_before_legacy_fallback(self):
        canonical = {"quotes": {"Pinnacle": {
            "spread": {"home": quote(-7.5, status="LIVE")},
            "total": {"over": quote(61.5, status="CURRENT")},
        }}}
        resolved = closing_market_fields(
            canonical, {"closing_home_spread": -1.5, "closing_total": 48.5}
        )
        self.assertEqual(resolved["closing_home_spread"], -1.5)
        self.assertEqual(resolved["closing_total"], 48.5)
        self.assertIsNone(resolved["closing_home_spread_book"])
        self.assertIsNone(resolved["closing_total_book"])


if __name__ == "__main__":
    unittest.main()
