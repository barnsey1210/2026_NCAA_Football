import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MatchupAnalysisTest(unittest.TestCase):
    def test_player_rank_populations_are_metric_and_position_specific(self):
        payload = json.loads((ROOT / "data/site/matchup_analysis_2026.json").read_text())
        self.assertEqual(len(payload["teams"]), 138)
        sayin = next(
            row for row in payload["teams"]["Ohio State"]["players"]["passing"]
            if row["athleteName"] == "Julian Sayin"
        )
        self.assertEqual(sayin["metric"], "Passing WEPA")
        self.assertGreater(sayin["population"], 1)
        self.assertLessEqual(sayin["rank"], sayin["population"])
        self.assertEqual(sayin["position"], "QB")

    def test_public_page_has_scheduled_and_custom_routes(self):
        page = (ROOT / "matchup-analysis.js").read_text()
        self.assertIn("params.get('game_id')", page)
        self.assertIn("params.get('away')", page)
        self.assertIn("params.get('home')", page)
        self.assertIn("playerCard", page)
        self.assertIn("${r.rank}/${r.population}", page)
        for marker in (
            "NFL DRAFT · 2027 TOP-175 PLAYERS",
            "Last-2 Perf vs Model",
            "Last-4 Perf vs Model",
            "Last-4 SOS",
            "L2 Rating Change",
            "Season Perf vs Model",
            "RECENT FORM",
            " games)",
            "Projected Spread:",
            "Projected Total:",
            "compactMetricLabel",
            "MATCHUP ADVANTAGE",
            "RECENT FORM",
            "QB ADVANTAGE",
            "keyMetrics",
            "key-star",
            "summary-tooltip",
            "Run-heavy tendencies",
            "Last-4 Performance vs Model:",
            "L2 rating:",
            "document.addEventListener('pointerdown'",
            "tip-rows",
            "trendDefinition",
            "trend-tooltip",
            "Drives / Game",
            "ATS ",
            "O/U ",
            "composite-rank",
            "signal-${level}",
            "draftTooltip",
            "OFFENSE · RANK OUT OF 138",
            "--offense-color",
        ):
            self.assertIn(marker, page)
        self.assertNotIn("${r.tied?'T-':''}", page)
        self.assertNotIn("PROJECTED WINNER", page)
        self.assertNotIn("PROJECTED SCORE", page)
        self.assertNotIn("LAST 4 + COMMAND CENTER SIGNALS", page)
        self.assertNotIn("Scale: Small", page)
        self.assertIn("metricRank(m.offense)", page)
        self.assertIn("teamRank(s.talent)", page)
        self.assertNotIn("NO ABSENCE FLAGGED", page)
        self.assertNotIn("availability ${", page)

    def test_desktop_matchups_use_compact_side_by_side_layout(self):
        css = (ROOT / "matchup-analysis.css").read_text()
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", css)
        self.assertIn("@media(max-width:1100px){.matchups{grid-template-columns:1fr}}", css)
        self.assertIn("min-height:42px", css)

    def test_team_colors_and_top175_player_details_are_complete(self):
        payload = json.loads((ROOT / "data/site/matchup_analysis_2026.json").read_text())
        self.assertEqual(sum(bool(row.get("brand")) for row in payload["teams"].values()), 138)
        draft = json.loads((ROOT / "data/canonical/nfl_draft_2027_top175_team_counts.json").read_text())
        players = [player for rows in draft["players_by_team"].values() for player in rows]
        self.assertEqual(len(players), 175)
        self.assertEqual({"rank", "name", "position"}, set(players[0]))

    def test_approved_preview_profile_is_preserved(self):
        payload = json.loads((ROOT / "data/site/matchup_analysis_2026.json").read_text())
        ohio = payload["teams"]["Ohio State"]
        season = ohio["profile"]["season"]
        recent = ohio["profile"]["recent"]
        self.assertEqual(season["talent"]["rank"], 2)
        self.assertEqual(season["coach"]["rank"], 1)
        self.assertEqual(season["draftables"]["value"], 8)
        self.assertTrue(season["draftables"]["players"])
        self.assertEqual(season["draftables"]["players"][0]["name"], "Jeremiah Smith")
        self.assertEqual(ohio["brand"]["primary"], "#ba0c2f")
        self.assertIsNotNone(season["last2PerformanceVsModel"]["value"])
        self.assertIsNotNone(season["last4PerformanceVsModel"]["value"])
        self.assertIsNotNone(recent["sos"]["value"])
        self.assertIsNotNone(season["drivesRank"])
        self.assertIsNotNone(season["compositeRank"])
        self.assertIsNotNone(season["record"])
        self.assertIsNotNone(season["bettingRecord"])
        sayin = next(row for row in ohio["players"]["passing"] if row["athleteName"] == "Julian Sayin")
        self.assertTrue(sayin["availability"]["status"].startswith("OUT"))
        self.assertEqual(sayin["availability"]["replacement"], "Luke Fahey")

    def test_raw_and_adjusted_cfbd_metrics_are_distinct_and_complete(self):
        payload = json.loads((ROOT / "data/site/matchup_analysis_2026.json").read_text())
        ohio = payload["teams"]["Ohio State"]
        adjusted_labels = [row["label"] for row in ohio["metrics"]]
        raw_labels = [row["label"] for row in ohio["raw_metrics"]]
        self.assertIn("Adjusted Rushing Explosiveness", adjusted_labels)
        self.assertNotIn("Explosiveness", adjusted_labels)
        self.assertEqual(raw_labels, [
            "EPA / Play",
            "Success Rate",
            "Explosiveness (Successful-Play EPA)",
            "Points / Opportunity",
            "Havoc (OFF Allowed / DEF Created)",
            "Standard-Down Success",
            "Passing-Down Success",
        ])
        raw = {row["label"]: row for row in ohio["raw_metrics"]}
        self.assertAlmostEqual(raw["EPA / Play"]["offense"]["value"], 0.23508157416079065)
        self.assertEqual(raw["EPA / Play"]["offense"]["rank"], 16)
        self.assertEqual(raw["Points / Opportunity"]["offense"]["rank"], 20)
        self.assertEqual(raw["Havoc (OFF Allowed / DEF Created)"]["offense"]["rank"], 36)
        self.assertTrue(raw["Havoc (OFF Allowed / DEF Created)"]["offense"]["tied"])

    def test_all_fbs_profiles_are_derived_and_receivers_are_ranked(self):
        payload = json.loads((ROOT / "data/site/matchup_analysis_2026.json").read_text())
        self.assertEqual(len(payload["teams"]), 138)
        for team in ("LSU", "Tennessee"):
            row = payload["teams"][team]
            season = row["profile"]["season"]
            recent = row["profile"]["recent"]
            for key in ("talent", "coach", "draftables", "runRank", "passRank", "paceRank", "l2", "last2PerformanceVsModel", "last4PerformanceVsModel", "performanceVsModel"):
                self.assertIsNotNone(season[key], f"{team}: {key}")
            self.assertIsNotNone(recent["sos"], f"{team}: last-4 SOS")
            self.assertIn(recent["trend"], {"Improving", "Stable", "Declining"})
        populated = sum(
            row["profile"]["season"]["last4PerformanceVsModel"] is not None
            for row in payload["teams"].values()
        )
        self.assertEqual(populated, 137)
        lsu_receiver = payload["teams"]["LSU"]["players"]["receiving"][0]
        self.assertEqual(lsu_receiver["metric"], "Receiving PPA")
        self.assertIn(lsu_receiver["position"], {"WR", "TE"})
        self.assertGreaterEqual(lsu_receiver["usage"], 0.05)
        self.assertLessEqual(lsu_receiver["rank"], lsu_receiver["population"])
        self.assertIn("PPA", payload["definitions"]["receivingPPA"])

    def test_command_center_and_ratings_link_to_card(self):
        command = (ROOT / "scripts/site/build_war_room_page.py").read_text()
        public = (ROOT / "scripts/site/build_public_site.py").read_text()
        self.assertIn("matchup-analysis.html?game_id=", command)
        self.assertIn("setMatchupLink(away.team,home.team,-homeMargin,total)", public)
        self.assertIn('target="_blank" rel="noopener" href="matchup-analysis.html?game_id=', command)
        self.assertIn('id="matchupCardLink" class="matchup-card-link" target="_blank" rel="noopener"', public)

    def test_matchup_assets_cannot_remain_stale(self):
        page = (ROOT / "matchup-analysis.html").read_text()
        headers = (ROOT / "deploy/cloudflare_pages/_headers").read_text()
        builder = (ROOT / "scripts/site/build_public_site.py").read_text()
        self.assertIn("matchup-analysis.js?v=", page)
        self.assertIn("matchup-analysis.css?v=", page)
        self.assertIn("/matchup-analysis.js", headers)
        self.assertIn("/matchup-analysis.css", headers)
        self.assertIn("/data/site/matchup_analysis_2026.json", headers)
        self.assertIn("matchup-analysis\\.(?:js|css)", builder)


if __name__ == "__main__":
    unittest.main()
