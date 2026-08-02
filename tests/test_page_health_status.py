import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("page_health", ROOT / "scripts/site/build_page_health_status.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
NOW = datetime(2026, 8, 1, 16, tzinfo=timezone.utc)


class PageHealthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.registry = json.loads((ROOT / "config/page_health_registry.json").read_text())

    def tearDown(self):
        self.temp.cleanup()

    def write(self, rel, value):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def evaluate(self, page):
        return MOD.evaluate(page, self.registry["pages"][page], MOD.Context(self.root, NOW))

    def test_registry_covers_every_major_page(self):
        self.assertEqual(set(self.registry["pages"]), {"dashboard", "ratings", "openers", "matchups", "odds", "schedule", "futures", "conferences", "playoff", "simulations", "betting"})
        self.assertEqual({v["page_url"] for v in self.registry["pages"].values()}, {"index.html", "ratings.html", "openers.html", "matchups.html", "odds.html", "schedule.html", "futures.html", "conferences.html", "playoff.html", "simulations.html", "betting.html"})

    def test_missing_critical_artifact_is_red(self):
        result = self.evaluate("matchups")
        self.assertEqual(result["status"], "red")
        self.assertTrue(result["critical_failures"])

    def test_healthy_matchups_is_green(self):
        self.write("data/site/matchups_view.json", {"built_at": NOW.isoformat(), "games": [{"game": {"game_id": "g1"}}], "audit_summary": {"games": 1, "model_spread": 1, "model_total": 1, "five_factors_complete": 1, "coach_full_both_teams": 1, "market_spread": 1}})
        self.assertEqual(self.evaluate("matchups")["status"], "green")

    def test_partial_ratings_is_yellow(self):
        teams = [{"rating": 1, "sources": {s: {"rating": 1} for s in ("spplus", "fpi", "teamrankings", "bradpowers")}} for _ in range(138)]
        teams[-1]["sources"]["fpi"]["rating"] = None
        self.write("data/site/ratings_view.json", {"snapshot_date": "2026-08-01", "teams": teams})
        self.assertEqual(self.evaluate("ratings")["status"], "yellow")

    def test_legitimate_inactive_playoff_is_gray(self):
        teams = [{"playoff_pct": .1, "national_title_pct": .01} for _ in range(138)]
        self.write("data/site/playoff_model_2026.json", {"built_at": NOW.isoformat(), "trials": 5000, "teams": teams})
        self.assertEqual(self.evaluate("playoff")["status"], "gray")

    def test_stale_current_odds_never_green(self):
        stale = (NOW - timedelta(hours=30)).isoformat()
        game = {"source_updated_at": stale, "quotes": {"DraftKings": {"spread": {"away": {}}, "total": {"over": {}}, "moneyline": {"away": {}}}}, "data_quality_notes": []}
        self.write("data/site/odds_screen_v2.json", {"built_at": stale, "books": ["DraftKings"], "games": [game]})
        self.write("data/site/odds_futures_v2.json", {"built_at": stale, "categories": {}})
        self.assertEqual(self.evaluate("odds")["status"], "red")

    def test_missing_conference_membership_never_green(self):
        self.write("data/site/conference_workspace.json", {"built_at": NOW.isoformat(), "conferences": [{"teams": [{"team": "A", "title_pct": .2}]} for _ in range(10)]})
        self.assertEqual(self.evaluate("conferences")["status"], "red")

    def test_malformed_betting_output_is_red(self):
        self.write("data/site/matchups_view.json", {"built_at": NOW.isoformat(), "games": [], "audit_summary": {}})
        self.write("data/site/betting_activity_view.json", {"built_at": NOW.isoformat(), "summary": {}, "records": [{"bet_id": "x", "price": float("nan")}]})
        self.assertEqual(self.evaluate("betting")["status"], "red")

    def test_payload_fields_and_status_values(self):
        payload = MOD.build(self.root, ROOT / "config/page_health_registry.json", NOW)
        required = {"page_id", "display_name", "status", "status_label", "summary", "last_success_at", "artifact_built_at", "age_minutes", "age_hours", "metrics", "warnings", "critical_failures", "unavailable_reasons", "page_url", "source_artifacts"}
        self.assertEqual(len(payload["pages"]), 11)
        for page in payload["pages"]:
            self.assertTrue(required.issubset(page))
            self.assertIn(page["status"], MOD.VALID)
            for key in ("last_success_at", "artifact_built_at"):
                if page[key] is not None:
                    self.assertIsNotNone(MOD.parse_time(page[key]))

    def test_shared_assets_and_builder_cover_public_pages(self):
        builder = (ROOT / "scripts/site/build_public_site.py").read_text()
        for page in self.registry["pages"].values():
            self.assertIn(page["page_url"], builder)
        self.assertIn("page_health.css", builder)
        self.assertIn("page_health.js", builder)
        renderer = (ROOT / "page_health.js").read_text()
        for page_id in self.registry["pages"]:
            self.assertIn(f"'{page_id}'", renderer)

    def test_manifest_contains_only_health_source_not_generated_outputs(self):
        manifest = set((ROOT / "deploy/source_manifest.txt").read_text().splitlines())
        expected = {
            "config/page_health_registry.json",
            "scripts/site/build_page_health_status.py",
            "scripts/site/build_public_site.py",
            "scripts/publish/publish_site.sh",
            "scripts/publish/check_public_site.py",
            "page_health.js",
            "page_health.css",
        }
        self.assertTrue(expected.issubset(manifest))
        self.assertFalse(
            manifest & {
                "data/qa/page_health_status.json",
                "data/qa/page_health_status_details.csv",
                "data/site/page_health_status.json",
            }
        )


if __name__ == "__main__":
    unittest.main()
