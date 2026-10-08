import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/site/ratings_l2.py"
SPEC = importlib.util.spec_from_file_location("ratings_l2_under_test", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_history(path, snapshots):
    fields = ["snapshot_date", "season", "source", "team", "rating", "pulled_at"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for snapshot_date, values in snapshots:
            for source, teams in values.items():
                for team, rating in teams.items():
                    writer.writerow({
                        "snapshot_date": snapshot_date,
                        "season": "2026",
                        "source": source,
                        "team": team,
                        "rating": rating,
                        "pulled_at": f"{snapshot_date}T12:00:00Z",
                    })


def panel(a, b, include_sagarin=True):
    values = {
        "SP+": {"A": a, "B": b},
        "FPI": {"A": a, "B": b},
        "TeamRankings": {"A": a, "B": b},
        "Brad Powers": {"A": 999, "B": -999},
    }
    if include_sagarin:
        values["Sagarin Rating"] = {"A": 100 + a, "B": 100 + b}
    return values


class RatingsL2Test(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.history = Path(self.tempdir.name) / "history.csv"

    def tearDown(self):
        self.tempdir.cleanup()

    def test_uses_latest_complete_snapshot_in_exact_two_week_cycle(self):
        write_history(self.history, [
            ("2026-08-30", panel(8, -8)),
            ("2026-09-01", panel(10, -10)),
            ("2026-09-06", panel(12, -12)),
            ("2026-09-08", panel(14, -14)),
        ])

        # Week 35 is two cycle buckets before current Week 37; Aug. 30 is the
        # latest accepted complete snapshot in that baseline cycle.
        resolved = MODULE.two_cycle_ago_baseline(
            self.history, "2026-09-09", min_teams=2
        )
        self.assertEqual(resolved["snapshot_date"], "2026-08-30")
        self.assertEqual(resolved["ratings"], {"A": 8.0, "B": -8.0})

    def test_incomplete_three_source_date_is_rejected(self):
        write_history(self.history, [
            ("2026-08-30", panel(8, -8)),
            ("2026-09-06", panel(12, -12)),
            ("2026-09-07", panel(500, -500, include_sagarin=False)),
        ])
        snapshots = MODULE.canonical_cycle_snapshots(self.history, min_teams=2)
        self.assertEqual(
            [x["snapshot_date"] for x in snapshots],
            ["2026-08-30", "2026-09-06"],
        )

    def test_reference_feed_never_changes_composite(self):
        write_history(self.history, [("2026-08-30", panel(8, -8))])
        snapshot = MODULE.canonical_cycle_snapshots(
            self.history, min_teams=2
        )[0]
        self.assertEqual(snapshot["ratings"], {"A": 8.0, "B": -8.0})

    def test_missing_exact_two_week_cycle_does_not_fall_back_farther(self):
        write_history(self.history, [
            ("2026-08-23", panel(6, -6)),
            ("2026-09-06", panel(12, -12)),
        ])
        self.assertIsNone(MODULE.two_cycle_ago_baseline(
            self.history, "2026-09-09", min_teams=2
        ))

    def test_directional_movement_ranks_improvement_before_decline(self):
        ranks = MODULE.directional_movement_ranks({
            "Alpha": -4.0,
            "Beta": 2.0,
            "Gamma": 4.0,
            "Missing": None,
        })
        self.assertEqual(ranks, {"Gamma": 1, "Beta": 2, "Alpha": 3})
        self.assertEqual(sorted(ranks.values()), [1, 2, 3])

    def test_directional_movement_rank_ties_use_team_name(self):
        changes = {"Zulu": 1.5, "Alpha": 1.5, "Middle": 0.0}
        self.assertEqual(
            MODULE.directional_movement_ranks(changes),
            {"Alpha": 1, "Zulu": 2, "Middle": 3},
        )


if __name__ == "__main__":
    unittest.main()
