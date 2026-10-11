import csv
import tempfile
import unittest
from pathlib import Path

from scripts.site.build_matchups_view import load_canonical_spplus_component_ranks


class MatchupsSpplusRankAuthorityTests(unittest.TestCase):
    def test_component_ranks_use_accepted_spplus_direction_and_keep_all_teams(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spplus.csv"
            teams = ["Tennessee"] + [f"Team {index:03d}" for index in range(137)]
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=("team", "spplus_off", "spplus_def")
                )
                writer.writeheader()
                for index, team in enumerate(teams):
                    writer.writerow({
                        "team": team,
                        "spplus_off": 200 - index,
                        "spplus_def": index,
                    })
            offense, defense = load_canonical_spplus_component_ranks(path)
            self.assertEqual(len(offense), 138)
            self.assertEqual(len(defense), 138)
            self.assertEqual(offense["Tennessee"], 1)
            self.assertEqual(defense["Tennessee"], 1)

    def test_missing_component_value_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spplus.csv"
            with path.open("w", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=("team", "spplus_off", "spplus_def")
                )
                writer.writeheader()
                for index in range(138):
                    writer.writerow({
                        "team": f"Team {index}",
                        "spplus_off": "" if index == 0 else index,
                        "spplus_def": index,
                    })
            with self.assertRaises(SystemExit):
                load_canonical_spplus_component_ranks(path)


if __name__ == "__main__":
    unittest.main()
