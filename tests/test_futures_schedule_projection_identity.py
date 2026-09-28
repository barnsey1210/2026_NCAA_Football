import unittest

from scripts.site.build_futures_view import build_schedule_index


class FuturesScheduleProjectionIdentityTests(unittest.TestCase):
    def test_cfbd_identity_survives_utc_local_date_difference(self):
        schedule = [{
            "cfbd_game_id": 401858487,
            "season_type": "regular",
            "week": 6,
            "date": "2026-10-09",
            "away_team": "Iowa",
            "home_team": "Washington",
            "completed": False,
            "neutral_site": False,
        }]
        projections = [{
            "game_id": "g446",
            "date": "2026-10-10",
            "away_team": "Iowa",
            "home_team": "Washington",
            "blend_spread_home": "-3.3",
            "neutral_site": "False",
        }]
        preseason = [{"game_id": "g446", "cfbd_game_id": 401858487}]

        games, refs = build_schedule_index(
            schedule,
            projections,
            {"Iowa", "Washington"},
            preseason_games=preseason,
        )

        game = games["401858487"]
        self.assertIsNotNone(game["home_win_probability"])
        self.assertEqual(game["win_probability_source"], "GAME_PROJECTION")
        self.assertEqual(refs["Iowa"], ["401858487"])
        self.assertEqual(refs["Washington"], ["401858487"])
