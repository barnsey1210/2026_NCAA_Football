import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RatingsViewSagarinMetadataTests(unittest.TestCase):
    def test_official_sagarin_uses_rating_health_without_changing_value(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture_root = Path(temporary)
            site_scripts = fixture_root / "scripts/site"
            ratings_data = fixture_root / "data/ratings"
            site_scripts.mkdir(parents=True)
            ratings_data.mkdir(parents=True)

            for name in ("build_ratings_view.py", "ratings_l2.py"):
                shutil.copy2(ROOT / "scripts/site" / name, site_scripts / name)

            teams = [f"Team {index:03d}" for index in range(130)]
            latest_fields = [
                "season", "snapshot_date", "source", "team", "rating", "rank",
                "pulled_at", "source_updated_at",
            ]
            with (ratings_data / "ratings_latest.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=latest_fields)
                writer.writeheader()
                for index, team in enumerate(teams, 1):
                    values = {
                        "SP+": 10.0 + index / 100,
                        "FPI": 20.0 + index / 100,
                        "TeamRankings": 30.0 + index / 100,
                        "Sagarin Predictor": 90.0 + index / 100,
                    }
                    for source, rating in values.items():
                        writer.writerow({
                            "season": 2026,
                            "snapshot_date": "2026-09-10",
                            "source": source,
                            "team": team,
                            "rating": rating,
                            "rank": index,
                            "pulled_at": "2026-09-10T12:01:54Z",
                            "source_updated_at": "",
                        })

            master_fields = [
                "team", "spplus", "fpi", "teamrankings", "sagarin", "sagarin_raw",
            ]
            with (ratings_data / "ratings_master_latest.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=master_fields)
                writer.writeheader()
                for index, team in enumerate(teams, 1):
                    writer.writerow({
                        "team": team,
                        "spplus": 10.0 + index / 100,
                        "fpi": 20.0 + index / 100,
                        "teamrankings": 30.0 + index / 100,
                        "sagarin": 4.0 + index / 100,
                        "sagarin_raw": 90.0 + index / 100,
                    })

            with (ratings_data / "ratings_history.csv").open("w", newline="") as handle:
                csv.writer(handle).writerow(
                    ["season", "snapshot_date", "source", "team", "rating", "pulled_at"]
                )

            with (ratings_data / "ratings_preseason_2026.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["team", "rating", "rank", "snapshot_date"]
                )
                writer.writeheader()
                for index, team in enumerate(teams, 1):
                    writer.writerow({
                        "team": team, "rating": 0.0, "rank": index,
                        "snapshot_date": "2026-08-28",
                    })

            status_fields = [
                "source", "latest_pull_at", "source_updated_at", "last_changed_at",
                "teams_changed", "change_status", "active_2026",
                "production_weight_pct", "display_status",
            ]
            with (ratings_data / "ratings_source_status.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=status_fields)
                writer.writeheader()
                writer.writerow({
                    "source": "Sagarin Rating",
                    "latest_pull_at": "2026-09-10T12:01:54Z",
                    "source_updated_at": "",
                    "last_changed_at": "2026-09-08T12:01:33Z",
                    "teams_changed": 0,
                    "change_status": "NO_CHANGE",
                    "active_2026": "True",
                    "production_weight_pct": 25.0,
                    "display_status": "Active 2026",
                })
                writer.writerow({
                    "source": "Sagarin Predictor",
                    "latest_pull_at": "2026-09-01T00:00:00Z",
                    "source_updated_at": "2026-09-01T00:00:00Z",
                    "last_changed_at": "2026-09-01T00:00:00Z",
                    "teams_changed": 12,
                    "change_status": "REFERENCE_ONLY",
                    "active_2026": "False",
                    "production_weight_pct": 0.0,
                    "display_status": "Stale / reference only",
                })

            subprocess.run(
                [sys.executable, str(site_scripts / "build_ratings_view.py")],
                cwd=fixture_root,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads((fixture_root / "data/site/ratings_view.json").read_text())
            sagarin = payload["source_meta"]["sagarin"]

            self.assertEqual(sagarin["label"], "Sagarin Rating")
            self.assertEqual(sagarin["display_status"], "Active 2026")
            self.assertEqual(sagarin["latest_pull"], "2026-09-10T12:01:54Z")
            self.assertEqual(
                sagarin["last_observed_value_change"], "2026-09-08T12:01:33Z"
            )
            self.assertIsNone(sagarin["provider_updated_at"])
            self.assertEqual(sagarin["production_weight_pct"], 25.0)
            self.assertTrue(sagarin["active_2026"])
            self.assertTrue(sagarin["composite_eligible"])
            self.assertEqual(payload["weights"]["sagarin"], 0.25)
            self.assertEqual(
                payload["composite_model"]["eligible_sources"]["sagarin"],
                "Sagarin Rating",
            )
            self.assertEqual(
                payload["composite_model"]["active_sources"]["sagarin"],
                "Sagarin Rating",
            )

            team = next(item for item in payload["teams"] if item["team"] == "Team 000")
            self.assertAlmostEqual(team["sources"]["sagarin"]["raw_rating"], 90.01)
            self.assertAlmostEqual(team["composite_sources"]["sagarin"]["rating"], 4.01)
            self.assertAlmostEqual(team["rating"], (10.01 + 20.01 + 30.01 + 4.01) / 4)


if __name__ == "__main__":
    unittest.main()
