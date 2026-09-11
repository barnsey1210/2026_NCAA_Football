import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE = Path("/Users/jameslindesmith/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")


class FuturesDashboardTests(unittest.TestCase):
    def run_js(self, body):
        script = f"const F=require('./futures_dashboard.js');{body}"
        completed = subprocess.run(
            [str(NODE), "-e", script], cwd=ROOT, text=True, capture_output=True, check=True
        )
        return json.loads(completed.stdout)

    def test_deterministic_views_and_missing_prior(self):
        result = self.run_js("""
          const rows=[
            {team:'A',conference:'SEC',win_edge:1.0,delta_week:{win:{edge:.4,model:.2,market:-.2}}},
            {team:'B',conference:'ACC',win_edge:.2,delta_week:{win:{edge:.5,model:.1,market:-.4}}},
            {team:'C',conference:'SEC',win_edge:-.1,delta_week:{win:{edge:-.8,model:-.1,market:.2}}},
            {team:'D',conference:'SEC',win_edge:.8,delta_week:{win:{edge:null,model:null,market:null}}}
          ];
          const base={mode:'wins',conference:'all',search:'',period:'week',edgeStatus:'all',sort:'edge'};
          const names=view=>F.queryRows(rows,{...base,view}).map(x=>x.team);
          console.log(JSON.stringify({best:names('best'),movers:F.queryRows(rows,{...base,view:'movers',sort:'edge_change'}).map(x=>x.team),growing:names('growing'),shrinking:names('shrinking'),crossed:names('crossed'),priorMissing:F.priorEdge(rows[3],'wins','week')}));
        """)
        self.assertEqual(result["best"], ["A", "D", "B", "C"])
        self.assertEqual(result["movers"], ["C", "B", "A", "D"])
        self.assertEqual(result["growing"], ["A", "B"])
        self.assertEqual(result["shrinking"], ["C"])
        self.assertEqual(result["crossed"], ["B"])
        self.assertIsNone(result["priorMissing"])

    def test_exact_conference_search_and_edge_status(self):
        result = self.run_js("""
          const rows=[
            {team:'Miami',conference:'ACC',win_edge:.4,delta_day:{win:{edge:.1}}},
            {team:'Miami (OH)',conference:'MAC',win_edge:-.2,delta_day:{win:{edge:-.1}}},
            {team:'Michigan',conference:'B1G',win_edge:.3,delta_day:{win:{edge:.2}}}
          ];
          const state={mode:'wins',conference:'ACC',search:'miami',period:'day',view:'all',edgeStatus:'positive',sort:'team'};
          console.log(JSON.stringify(F.queryRows(rows,state).map(x=>x.team)));
        """)
        self.assertEqual(result, ["Miami"])

    def test_current_payload_detail_contract_and_no_payload_change(self):
        data = json.loads((ROOT / "data/site/futures_view.json").read_text())
        required = {
            "team", "conference", "record", "projected_wins", "market_win_total", "win_edge",
            "title_model_prob", "title_market_prob", "title_edge", "playoff_model_prob",
            "playoff_market_prob", "playoff_edge", "national_title_model_prob",
            "national_title_market_prob", "national_title_edge", "history", "win_quotes",
            "title_quotes", "playoff_quotes", "national_title_quotes", "open_wagers",
            "quarterfinal_model_prob", "semifinal_model_prob", "national_title_game_model_prob",
            "delta_week", "delta_day", "team_rating", "team_rating_date",
            "team_rating_prior_week", "team_rating_prior_week_date",
            "team_rating_delta_week", "team_rating_history",
            "schedule_game_ids",
        }
        self.assertEqual(len(data["rows"]), 138)
        self.assertTrue(all(required <= set(row) for row in data["rows"]))
        self.assertEqual(data["weekly_baseline"]["checkpoint_date"], "2026-08-31")

    def test_requested_teams_have_authentic_weekly_rating_history(self):
        data = json.loads((ROOT / "data/site/futures_view.json").read_text())
        rows = {row["team"]: row for row in data["rows"]}
        for team in ("Massachusetts", "Western Kentucky", "Hawaii", "Ohio State"):
            row = rows[team]
            self.assertEqual(row["team_rating_date"], "2026-09-10")
            self.assertEqual(row["team_rating_prior_week_date"], "2026-09-06")
            self.assertGreaterEqual(len(row["team_rating_history"]), 3)
            self.assertAlmostEqual(
                row["team_rating_delta_week"],
                row["team_rating"] - row["team_rating_prior_week"],
            )

    def test_markup_has_command_center_matrix_focus_rail_and_mobile_cards(self):
        html = (ROOT / "futures.html").read_text()
        js = (ROOT / "futures_dashboard.js").read_text()
        for mode in ('data-mode="wins"', 'data-mode="title"', 'data-mode="playoff"', 'data-mode="bets"'):
            self.assertIn(mode, html)
        for token in ("BOOKS.map", "win_book", "pathButton(x)", "@media(max-width:430px)", "activityRail", "railTabs", "scheduleRow"):
            self.assertIn(token, html + js)
        self.assertIn("futures_dashboard.js", html)
        self.assertIn("selected best executable quote", js)
        self.assertIn("Blank weeks are intentional gaps", js)
        self.assertIn(".tabs .active{background:#fff", html)

    def test_four_book_mapping_and_best_marker_follow_canonical_contract(self):
        data = json.loads((ROOT / "data/site/futures_view.json").read_text())
        ohio = next(row for row in data["rows"] if row["team"] == "Ohio State")
        result = self.run_js(f"""
          const row={json.dumps(ohio)};
          console.log(JSON.stringify({{
            books:F.BOOKS,
            quotes:F.BOOKS.map(book=>F.quoteFor(row.win_quotes,book)),
            best:F.BOOKS.filter(book=>F.isBestBook(row,'wins',book))
          }}));
        """)
        self.assertEqual(result["books"], ["DraftKings", "FanDuel", "BetMGM", "Caesars"])
        self.assertEqual(result["best"], [ohio["win_book"]])
        self.assertIsNone(result["quotes"][3])

    def test_schedule_and_full_history_axis_contract(self):
        data = json.loads((ROOT / "data/site/futures_view.json").read_text())
        ohio = next(row for row in data["rows"] if row["team"] == "Ohio State")
        self.assertEqual(data["history_axis"]["labels"][0:3], ["W0", "Pre-W1", "W1"])
        self.assertEqual(data["history_axis"]["labels"][-1], "W15")
        self.assertEqual(data["schema_version"], "futures-view-v5")
        self.assertEqual(data["schedule_contract"]["schema_version"], "futures-schedule-index-v1")
        self.assertNotIn("schedule", ohio)
        self.assertEqual(len(ohio["schedule_game_ids"]), 12)
        self.assertEqual(len(data["schedule_games"]), len(set(data["schedule_games"])))
        result = self.run_js(f"""
          const row={json.dumps(ohio)};
          console.log(JSON.stringify(F.resolveSchedule(row,{json.dumps(data['schedule_games'])})));
        """)
        self.assertEqual(result[0]["opponent"], "Ball State")
        self.assertEqual(result[0]["result"], "W")
        self.assertIsNone(result[0]["win_probability"])
        self.assertEqual(result[1]["opponent"], "Texas")
        self.assertAlmostEqual(result[1]["win_probability"], 0.5763218799)
        result = self.run_js(f"""
          const row={json.dumps(ohio)};
          const slots=F.historySlots(row,'win',{json.dumps(data['history_axis']['labels'])},'2026-08-31',2);
          console.log(JSON.stringify(slots));
        """)
        self.assertEqual(result[1]["label"], "Pre-W1")
        self.assertIsNotNone(result[1]["model"])
        self.assertIsNotNone(result[3]["model"])
        self.assertTrue(all(point["model"] is None for point in result[4:]))


if __name__ == "__main__":
    unittest.main()
