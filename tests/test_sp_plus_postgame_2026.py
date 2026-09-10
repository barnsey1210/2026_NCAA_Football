import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sp_postgame", ROOT / "scripts/postgame/pull_sp_plus_postgame_2026.py")
SP = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(SP)


class SpPlusPostgameTests(unittest.TestCase):
    def test_normalizes_source_fields_and_percentage(self):
        text = "date,team,opponent,win,pts,opp pts,margin,PGWE,adj mgn\n9/5/26,Ohio State,Ball State,1,56,3,53,100.0%,58.7\n"
        row = SP.normalize_csv(text, "2026-09-10T12:00:00Z")[0]
        self.assertEqual(row["date"], "2026-09-05")
        self.assertEqual((row["team"], row["opponent"]), ("Ohio State", "Ball State"))
        self.assertEqual((row["pts"], row["opp_pts"], row["actual_margin"]), (56, 3, 53.0))
        self.assertEqual((row["sp_plus_pgwe"], row["sp_plus_adjusted_margin"]), (1.0, 58.7))
        self.assertEqual(row["collected_at"], "2026-09-10T12:00:00Z")

    def test_rejects_empty_export(self):
        with self.assertRaises(ValueError):
            SP.normalize_csv("date,team,opponent,win,pts,opp pts,margin,PGWE,adj mgn\n", "t")


if __name__ == "__main__": unittest.main()
