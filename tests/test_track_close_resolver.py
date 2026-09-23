import unittest

from betting.track_close_resolver import (
    authoritative_frozen_quote,
    canonical_team,
    point_clv,
    resolve_game,
)
from betting.build_betting_activity_view import summarize_records


def game(game_id, week, away, home, spread_home=-3.5, total=52.5, frozen=True):
    status = "FROZEN_CLOSE" if frozen else "LIVE"
    return {
        "game_id": game_id, "week": week, "away_team": away, "home_team": home,
        "quotes": {"Pinnacle": {
            "spread": {
                "away": {"line": -spread_home, "price": -110, "freshness_status": status},
                "home": {"line": spread_home, "price": -110, "freshness_status": status},
            },
            "total": {
                "over": {"line": total, "price": -110, "freshness_status": status},
                "under": {"line": total, "price": -110, "freshness_status": status},
            },
        }},
    }


class TrackCloseResolverTests(unittest.TestCase):
    def test_alias_normalization_and_misspelling(self):
        self.assertEqual(canonical_team("san jose st"), "San Jose State")
        self.assertEqual(canonical_team("minnestoa"), "Minnesota")
        self.assertEqual(canonical_team("Sam Houston State"), "Sam Houston")

    def test_abbreviated_total_matchup_parsing(self):
        games = [game("g198", 3, "Georgia State", "Central Florida")]
        row = {"Bet": "Georgia st/ucf over", "Bet Type": "Total", "Bet Description": "Week 3"}
        resolved, reason = resolve_game(row, games)
        self.assertEqual(resolved["game_id"], "g198")
        self.assertEqual(reason, "exact_matchup_week")

    def test_single_team_side_matching(self):
        games = [game("g88", 1, "Sam Houston", "Troy")]
        row = {"Bet": "Sam Houston State", "team_guess": "Sam Houston State", "Bet Type": "Side", "week_bucket": "Week 1"}
        resolved, _ = resolve_game(row, games)
        self.assertEqual(resolved["game_id"], "g88")

    def test_spread_orientation_for_home_and_away(self):
        g = game("g1", 1, "Away", "Home", spread_home=-7.0)
        away = {"Bet Type": "Side", "team_guess": "Away", "bet_line": 8.5}
        home = {"Bet Type": "Side", "team_guess": "Home", "bet_line": -6.5}
        away_quote, _ = authoritative_frozen_quote(away, g)
        home_quote, _ = authoritative_frozen_quote(home, g)
        self.assertEqual(point_clv(away, away_quote), 1.5)
        self.assertEqual(point_clv(home, home_quote), 0.5)

    def test_total_sign_semantics_and_historical_close_recovery(self):
        g = game("g7", 0, "San Jose State", "USC", total=61.5)
        over = {"Bet": "USC/San Jose State Over 59.5", "Bet Type": "Total", "side": "Over", "bet_line": 59.5}
        under = {"Bet": "USC/San Jose State Under 63.5", "Bet Type": "Total", "side": "Under", "bet_line": 63.5}
        over_quote, reason = authoritative_frozen_quote(over, g)
        under_quote, _ = authoritative_frozen_quote(under, g)
        self.assertEqual(reason, "pinnacle_frozen_close")
        self.assertEqual(point_clv(over, over_quote), 2.0)
        self.assertEqual(point_clv(under, under_quote), 2.0)

    def test_ambiguity_fails_closed(self):
        games = [game("a", 1, "X", "Team"), game("b", 1, "Team", "Y")]
        resolved, reason = resolve_game({"Bet": "Team", "team_guess": "Team", "Bet Type": "Side", "week_bucket": "Week 1"}, games)
        self.assertIsNone(resolved)
        self.assertEqual(reason, "ambiguous_team")

    def test_live_quote_is_not_historical_close(self):
        quote, reason = authoritative_frozen_quote(
            {"Bet Type": "Side", "team_guess": "Home", "bet_line": -3.0},
            game("g", 1, "Away", "Home", frozen=False),
        )
        self.assertIsNone(quote)
        self.assertEqual(reason, "authoritative_frozen_close_missing")

    def test_open_wager_not_resolved_and_moneyline_not_unresolved(self):
        base = {"is_open": False, "stake": 100, "realized_profit": 0, "status": "Won", "clv_pct_current": None, "ev_current_pct": None}
        rows = [
            {**base, "track_close": True, "is_open": True, "tracking_clv_state": "CURRENT_MARKET", "tracking_clv_points": 1.0},
            {**base, "track_close": True, "tracking_clv_state": "NOT_APPLICABLE_POINT_CLV", "tracking_clv_points": None},
        ]
        summary = summarize_records(rows)
        self.assertEqual(summary["track_close_resolved"], 0)
        self.assertEqual(summary["track_close_unresolved"], 1)
        self.assertEqual(summary["track_close_not_applicable"], 1)


if __name__ == "__main__":
    unittest.main()
