import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "parse_rating_source_tables",
    ROOT / "scripts/ratings/parse_rating_source_tables.py",
)
PARSER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PARSER)


class RatingSourceTeamNormalizationTests(unittest.TestCase):
    def test_fpi_fcs_mascot_names_are_canonicalized_upstream(self):
        self.assertEqual(
            PARSER.canonical("North Dakota State Bison"), "North Dakota State"
        )
        self.assertEqual(
            PARSER.canonical("Sacramento State Hornets"), "Sacramento State"
        )

    def test_strict_acceptance_universe_check_remains_present(self):
        source = (
            ROOT / "scripts/ratings/accept_live_rating_candidates.py"
        ).read_text()
        self.assertIn("if len(df) != 138", source)
        self.assertIn('if df["team"].nunique() != 138', source)
        self.assertIn("if teams != baseline", source)


if __name__ == "__main__":
    unittest.main()
