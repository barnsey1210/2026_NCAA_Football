import json
import unittest
from pathlib import Path

from scripts.site.build_futures_view import build_schedule_index


ROOT = Path(__file__).resolve().parents[1]


class ConferenceProjectionIntegrityTests(unittest.TestCase):
    def test_cfbd_id_preserves_conference_status_when_dates_differ(self):
        schedule = [{
            "cfbd_game_id": 401862838,
            "week": 13,
            "date": "2026-11-27",
            "away_team": "Temple",
            "home_team": "Memphis",
            "conference_game": True,
            "completed": False,
        }]
        preseason = [{
            "cfbd_game_id": 401862838,
            "game_id": "g860",
            "week": 13,
            "date": "2026-11-28",
            "away_team": "Temple",
            "home_team": "Memphis",
            "is_conference_game": True,
        }]
        index, teams = build_schedule_index(
            schedule, [], {"Temple", "Memphis"}, {}, preseason
        )
        self.assertTrue(index["401862838"]["is_conference_game"])
        self.assertEqual(teams["Memphis"], ["401862838"])

    def test_all_preseason_conference_counts_match_explicit_2026_rules(self):
        db = json.loads(
            (ROOT / "data/snapshots/preseason/preseason_db.json").read_text()
        )
        expected = {
            "American": 8, "B12": 9, "B1G": 9, "CUSA": 8,
            "MAC": 8, "MW": 8, "PAC12": 8, "SEC": 9, "Sun Belt": 8,
        }
        acc_eight = {
            "Boston College", "Clemson", "Florida State",
            "Georgia Tech", "North Carolina",
        }
        counts = {team["team"]: 0 for team in db["teams"]}
        for game in db["games"]:
            if not game.get("is_conference_game") or game.get("week") == 14:
                continue
            for team in (game.get("away_team"), game.get("home_team")):
                if team in counts:
                    counts[team] += 1
        for team in db["teams"]:
            conference = team.get("conference")
            target = (
                8 if conference == "ACC" and team["team"] in acc_eight
                else 9 if conference == "ACC"
                else expected.get(conference)
            )
            if target is not None:
                self.assertEqual(counts[team["team"]], target, team["team"])
        self.assertEqual(counts["Memphis"], 8)

    def test_conferences_team_column_wraps_without_clipping_key_text(self):
        source = (
            ROOT / "scripts/site/build_conference_logo_schedule.py"
        ).read_text()
        self.assertIn("grid-template-columns:minmax(250px,280px)", source)
        self.assertIn(".team-column {{ width:100%; min-width:250px", source)
        self.assertIn(".team-meta {{ display:block", source)
        self.assertIn("white-space:normal", source)
        self.assertIn("grid-template-columns:minmax(200px,220px)", source)
        self.assertIn("Conf SOS #", source)
        self.assertIn("Rem #", source)


if __name__ == "__main__":
    unittest.main()
