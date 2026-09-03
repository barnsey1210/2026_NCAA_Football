import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "ratings/pull_sagarin_ratings.py"

spec = importlib.util.spec_from_file_location("pull_sagarin_ratings", MODULE)
sagarin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sagarin)


class SagarinRatingsParserTests(unittest.TestCase):
    def test_ratings_parser_rejects_prediction_and_aggregate_rows_and_deduplicates(self):
        html = """
        <html><body><pre>
36  UCLA                 A  =  79.23    0   0    0.00(   0)    0   0  |    0   0  |   79.50   35 |   79.13   35 |   78.75   36 |   78.75   38  BIG TEN             (A)
36  UCLA                 A  =  79.23    0   0    0.00(   0)    0   0  |    0   0  |   79.50   35 |   79.13   35 |   78.75   36 |   78.75   38  BIG TEN             (A)

28     UCLA                   2.63   2.78   2.60   2.47   2.47 @ California               134    57%   24.63  27.26  51.90  -2.63  57%   134

7  American             =  59.41   58.56   7   14   58.82   6.6659   58.5714
        </pre></body></html>
        """

        frame = sagarin.parse_sagarin_text(html, provider_season=2026)

        self.assertEqual(len(frame), 1)

        row = frame.iloc[0]
        self.assertEqual(row["team"], "UCLA")
        self.assertEqual(int(row["rank"]), 36)
        self.assertAlmostEqual(float(row["rating"]), 79.23, places=2)
        self.assertEqual(float(row["wins"]), 0.0)
        self.assertEqual(float(row["losses"]), 0.0)


if __name__ == "__main__":
    unittest.main()
