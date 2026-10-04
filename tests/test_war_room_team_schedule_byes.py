from pathlib import Path
import unittest

from scripts.site.build_matchups_view import regular_season_week_calendar
from scripts.site.build_public_site import compact_public_matchups_payload


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "scripts/site/build_war_room_page.py"


class WarRoomTeamScheduleByeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text()

    def test_calendar_uses_only_defined_regular_season_weeks_and_modal_dates(self):
        games = [
            {"week": 4, "date": "2026-09-26"},
            {"week": 4, "date": "2026-09-26"},
            {"week": 4, "date": "2026-09-25"},
            {"week": 5, "date": "2026-10-03"},
            {"week": 14, "date": "2026-12-05"},
        ]
        self.assertEqual(
            regular_season_week_calendar(games),
            [
                {"week": 4, "date": "2026-09-26"},
                {"week": 5, "date": "2026-10-03"},
            ],
        )

    def test_renderer_inserts_unique_byes_in_canonical_week_order(self):
        block = self.source.split("function scheduleRows(", 1)[1].split(
            "function renderTeamSchedule", 1
        )[0]
        self.assertIn("scheduledWeeks=new Set", block)
        self.assertIn("seenByeWeeks=new Set", block)
        self.assertIn("scheduledWeeks.has(week)", block)
        self.assertIn("seenByeWeeks.has(week)", block)
        self.assertIn("bye:true", block)
        self.assertIn("const weekDelta=Number(a.week)-Number(b.week)", block)

    def test_bye_markup_has_dashes_and_is_not_a_game_state(self):
        block = self.source.split("if(row.bye){", 1)[1].split(
            "const opponentFull", 1
        )[0]
        self.assertIn('class="bye"', block)
        self.assertIn('data-row-type="bye"', block)
        self.assertIn("<td>BYE</td>", block)
        self.assertEqual(block.count("<td>—</td>"), 6)
        self.assertNotIn("completed", block)
        self.assertNotIn("resultClass", block)

    def test_bye_styling_is_shared_and_responsive_safe(self):
        self.assertIn(".team-context-table .bye{", self.source)
        self.assertIn(".team-context-table .bye td{", self.source)
        self.assertIn(".team-table-wrap{overflow-x:auto}", self.source)
        self.assertIn("table-layout:fixed", self.source)

    def test_public_compaction_preserves_calendar_and_real_game_count(self):
        payload = {
            "regular_season_week_calendar": [
                {"week": 4, "date": "2026-09-26"},
                {"week": 5, "date": "2026-10-03"},
            ],
            "games": [
                {
                    "game": {"game_id": "g1"},
                    "model": {"home_spread": -3, "internal": "omit"},
                    "teams": {
                        "away": {"recent_form": [], "upcoming_schedule": []},
                        "home": {"recent_form": [], "upcoming_schedule": []},
                    },
                }
            ],
        }
        public = compact_public_matchups_payload(payload)
        self.assertEqual(len(public["games"]), 1)
        self.assertEqual(public["games"][0]["game"]["game_id"], "g1")
        self.assertEqual(len(public["regular_season_week_calendar"]), 2)
        for side in ("away", "home"):
            team = public["games"][0]["teams"][side]
            real_rows = team["recent_form"] + team["upcoming_schedule"]
            self.assertFalse(any(row.get("opponent") == "BYE" for row in real_rows))

    def test_records_and_counts_are_not_derived_from_display_rows(self):
        renderer = self.source.split("function scheduleRows(", 1)[1].split(
            "function renderTeamSchedule", 1
        )[0]
        self.assertNotIn("betting_record", renderer)
        self.assertNotIn("record_2026", renderer)
        self.assertNotIn("game_id", renderer)


if __name__ == "__main__":
    unittest.main()
