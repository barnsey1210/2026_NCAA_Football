import importlib.util
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
NODE = Path("/Users/jameslindesmith/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
SPEC = importlib.util.spec_from_file_location("build_futures_view", ROOT / "scripts/site/build_futures_view.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONF_SPEC = importlib.util.spec_from_file_location("build_conference_workspace", ROOT / "scripts/site/build_conference_workspace.py")
CONF_MODULE = importlib.util.module_from_spec(CONF_SPEC)
CONF_SPEC.loader.exec_module(CONF_MODULE)


class FuturesWeeklyBaselineTests(unittest.TestCase):
    def test_uses_latest_successful_checkpoint_strictly_before_prior_week_kickoff(self):
        games = [
            {"cfbd_week": 2, "cfbd_completed": True, "away_team": "A", "home_team": "B", "cfbd_start_date": "2026-09-04T23:30:00Z"},
            {"cfbd_week": 2, "cfbd_completed": True, "away_team": "B", "home_team": "A", "cfbd_start_date": "2026-09-05T16:00:00Z"},
        ]
        records = [
            {"checkpoint_date": "2026-09-03", "checkpoint_at": "2026-09-03T12:00:00Z", "rows": [{"team": "A"}]},
            {"checkpoint_date": "2026-09-04", "checkpoint_at": "2026-09-04T12:00:00Z", "rows": [{"team": "A"}]},
            {"checkpoint_date": "2026-09-04", "checkpoint_at": "2026-09-04T23:30:00Z", "rows": [{"team": "A"}]},
        ]
        selected, meta = MODULE.select_weekly_baseline(records, games, "2026-09-10T12:00:00Z", {"A", "B"})
        self.assertEqual(selected["checkpoint_at"], "2026-09-04T12:00:00Z")
        self.assertEqual(meta["prior_week"], 2)
        self.assertEqual(meta["status"], "available")

    def test_reports_reason_when_no_baseline_exists(self):
        games = [{"cfbd_week": 2, "cfbd_completed": True, "away_team": "A", "home_team": "B", "cfbd_start_date": "2026-09-04T23:30:00Z"}]
        selected, meta = MODULE.select_weekly_baseline([], games, "2026-09-10T12:00:00Z", {"A", "B"})
        self.assertIsNone(selected)
        self.assertEqual(meta["status"], "unavailable")
        self.assertTrue(meta["reason"])

    def test_latest_successful_candidate_wins_and_post_kickoff_never_does(self):
        games = [{"cfbd_week": 1, "cfbd_completed": True, "away_team": "A", "home_team": "B", "cfbd_start_date": "2026-09-03T22:00:00Z"}]
        records = [
            {"checkpoint_at": "2026-09-01T12:00:00Z", "status": "successful", "rows": [{"team": "A"}]},
            {"checkpoint_at": "2026-09-03T20:00:00Z", "status": "failed", "rows": [{"team": "A"}]},
            {"checkpoint_at": "2026-09-03T21:00:00Z", "status": "successful", "immutable_historical_input": True, "rows": [{"team": "A"}]},
            {"checkpoint_at": "2026-09-03T22:00:00Z", "status": "successful", "rows": [{"team": "A"}]},
        ]
        selected, _ = MODULE.select_weekly_baseline(records, games, "2026-09-10T12:00:00Z", {"A", "B"})
        self.assertEqual(selected["checkpoint_at"], "2026-09-03T21:00:00Z")
        self.assertTrue(selected["immutable_historical_input"])


class FuturesOperatorMarkupTests(unittest.TestCase):
    def test_public_builder_uses_compact_futures_source(self):
        builder = (ROOT / "scripts/site/build_public_site.py").read_text()
        self.assertIn('"futures.html":"futures.html"', builder)
        self.assertNotIn('"futures_v2.html":"futures.html"', builder)

    def test_movement_button_colors_override_inherited_button_color(self):
        html = (ROOT / "futures.html").read_text()
        self.assertIn(".moveButton.moveUp{color:var(--green)}", html)
        self.assertIn(".moveButton.moveDown{color:var(--red)}", html)
        self.assertIn(".moveButton.neutral{color:var(--muted)}", html)
        self.assertIn("Number(raw.toFixed(1))", html)
        self.assertIn("h.checkpoint_date===data.baselineDate?'Pre-W1':'Checkpoint'", html)

    def test_desktop_and_mobile_operator_contract(self):
        html = (ROOT / "futures.html").read_text()
        for label in ("Model wins", "Market", "CFP model", "Title market", "Open → now"):
            self.assertIn(label, html)
        self.assertIn("@media(max-width:900px)", html)
        self.assertIn("data-quotes", html)
        self.assertIn("delta_week", html)
        self.assertNotIn("header('Quarterfinal'", html)

    def test_mobile_futures_tables_are_compact_sortable_and_keep_desktop_matrix(self):
        js = (ROOT / "futures_dashboard.js").read_text()
        for token in (
            "mobileFuturesTables",
            "mobileFuturesTable",
            "mobileSortState",
            "data-mobile-sort",
            "mobileSortButton('Team',kind,'team')",
            "mobileSortButton('Edge',kind,'edge')",
            "heading:'Playoffs / CFP'",
            "heading:'National Title'",
            "quoteOdds(selected,d.side)",
            ".futuresWorkspace .wrap{display:none!important}",
            "@media(max-width:900px)",
        ):
            self.assertIn(token, js)
        self.assertIn("<th class=\"colNext\">", js)
        self.assertIn("<th class=\"colRating\">", js)
        self.assertIn("position:sticky!important", js)
        self.assertIn("grid-template-columns:repeat(4,1fr)", js)

    def test_mobile_team_and_edge_sorting_for_every_market_table(self):
        script = r"""
const fs=require('fs');
const source=fs.readFileSync('futures_dashboard.js','utf8');
const block=source.match(/function mobileMarketConfig[\s\S]*?(?=function mobileSortButton)/)[0];
const hasNumber=v=>v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v));
const mobileSortState={
  wins:{key:'edge',dir:'desc'},title:{key:'edge',dir:'desc'},
  cfp:{key:'edge',dir:'desc'},national:{key:'edge',dir:'desc'}
};
eval(block);
const rows=[
  {team:'Beta',win_edge:.2,title_edge:.02,playoff_edge:.12,national_title_edge:.04},
  {team:'Alpha',win_edge:.8,title_edge:.08,playoff_edge:.02,national_title_edge:.14},
  {team:'Zulu',win_edge:null,title_edge:null,playoff_edge:null,national_title_edge:null}
];
const out={};
for(const kind of ['wins','title','cfp','national']){
  out[kind]={edgeDesc:mobileSortedRows(rows,kind).map(x=>x.team)};
  mobileSortState[kind]={key:'team',dir:'asc'};
  out[kind].teamAsc=mobileSortedRows(rows,kind).map(x=>x.team);
  mobileSortState[kind].dir='desc';
  out[kind].teamDesc=mobileSortedRows(rows,kind).map(x=>x.team);
  mobileSortState[kind]={key:'edge',dir:'asc'};
  out[kind].edgeAsc=mobileSortedRows(rows,kind).map(x=>x.team);
}
console.log(JSON.stringify(out));
"""
        completed = subprocess.run(
            [str(NODE), "-e", script], cwd=ROOT, text=True,
            capture_output=True, check=True,
        )
        result = json.loads(completed.stdout)
        for kind in ("wins", "title", "cfp", "national"):
            self.assertEqual(result[kind]["edgeDesc"][-1], "Zulu")
            self.assertEqual(result[kind]["teamAsc"], ["Alpha", "Beta", "Zulu"])
            self.assertEqual(result[kind]["teamDesc"], ["Zulu", "Beta", "Alpha"])
            self.assertEqual(result[kind]["edgeAsc"][-1], "Zulu")

    def test_inline_movement_and_consolidated_columns(self):
        html = (ROOT / "futures.html").read_text()
        self.assertIn('class="valueLine"', html)
        self.assertIn('class="marketLine"', html)
        self.assertIn('data-history=', html)
        self.assertIn('data-quotes=', html)
        self.assertIn("'MODEL WINS HISTORY'", html)
        self.assertIn("h.checkpoint_date===data.baselineDate?'Pre-W1':'Checkpoint'", html)
        self.assertIn('label:`W${data.currentWeek} current`', html)
        self.assertIn("x.win_direction==='Over'?'O'", html)
        self.assertNotIn("header('Model side'", html)
        self.assertNotIn("header('Best price'", html)
        self.assertNotIn(' wk</span>', html)
        self.assertIn('.moveUp{color:var(--green)}', html)
        self.assertIn('.moveDown{color:var(--red)}', html)

    def test_missing_weekly_baseline_stays_unavailable(self):
        html = (ROOT / "futures.html").read_text()
        self.assertIn("text=z==null?'—'", html)
        self.assertIn('No historical value was fabricated.', html)

    def test_conference_team_cell_is_compact_and_record_not_duplicated(self):
        html = (ROOT / "conferences.html").read_text()
        self.assertIn("${esc(activeConference)} ${confRecord}", html)
        self.assertIn('Conf SOS #${esc(row.conf_sos_rank)}', html)
        self.assertIn('title="Overall record ${overallRecord}"', html)
        self.assertNotIn("sortHeader('Conf Record'", html)
        self.assertNotIn('class="record-column"', html)
        self.assertIn('tbody tr { height:84px; }', html)

    def test_missing_values_are_not_coerced_to_zero(self):
        html = (ROOT / "futures.html").read_text()
        self.assertIn("const hasNumber=x=>x!==null&&x!==undefined&&x!==''", html)
        self.assertIn("const raw=hasNumber(v)?Number(v)*scale:null", html)
        self.assertIn("a.filter(x=>hasNumber(x.delta_week?.[field]?.[key]))", html)

    def test_futures_view_carries_reliability_warnings(self):
        source = (ROOT / "scripts/site/build_futures_view.py").read_text()
        self.assertIn("NCAAF_FUTURES_RELIABILITY_PATH", source)
        self.assertIn('reliability.get("warnings", [])', source)

    def test_conference_record_overlay_uses_canonical_final(self):
        games = [{"game_id": "g1", "cfbd_completed": False, "away_points": None, "home_points": None}]
        CONF_MODULE.apply_canonical_results(games, [{"game_id": "g1", "completed": True, "away_score": 17, "home_score": 28}])
        self.assertEqual(games[0]["away_points"], 17)
        self.assertEqual(games[0]["home_points"], 28)
        self.assertTrue(games[0]["cfbd_completed"])


if __name__ == "__main__":
    unittest.main()
