import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "cfbd_schedule", ROOT / "scripts/schedule/pull_cfbd_schedule_2026.py"
)
CFBD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(CFBD)


class CfbdSchedulePgweTests(unittest.TestCase):
    def test_valid_pair_is_preserved_on_zero_to_one_scale(self):
        self.assertEqual(
            CFBD.pgwe_pair(
                {
                    "homePostgameWinProbability": 0.767,
                    "awayPostgameWinProbability": 0.233,
                }
            ),
            (0.767, 0.233, "available"),
        )

    def test_exact_endpoints_remain_raw(self):
        self.assertEqual(
            CFBD.pgwe_pair(
                {
                    "homePostgameWinProbability": 1,
                    "awayPostgameWinProbability": 0,
                }
            ),
            (1.0, 0.0, "available"),
        )

    def test_bad_or_incomplete_pairs_fail_closed(self):
        cases = [
            ({}, "missing"),
            ({"homePostgameWinProbability": 0.8}, "invalid"),
            (
                {
                    "homePostgameWinProbability": 0.8,
                    "awayPostgameWinProbability": 0.3,
                },
                "non_complementary",
            ),
            (
                {
                    "homePostgameWinProbability": 1.1,
                    "awayPostgameWinProbability": -0.1,
                },
                "invalid",
            ),
        ]
        for payload, status in cases:
            with self.subTest(payload=payload):
                self.assertEqual(CFBD.pgwe_pair(payload), (None, None, status))


if __name__ == "__main__":
    unittest.main()
