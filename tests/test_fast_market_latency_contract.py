import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FastMarketLatencyContractTests(unittest.TestCase):
    def test_provider_request_is_bounded_and_timed(self):
        source = (ROOT / "pull_theodds_ncaaf_lines_2026.py").read_text()
        self.assertIn('params["commenceTimeFrom"]', source)
        self.assertIn('params["commenceTimeTo"]', source)
        self.assertIn('strftime("%Y-%m-%dT%H:%M:%SZ")', source)
        self.assertIn('quota["normalization_ms"]', source)
        ast.parse(source)

    def test_every_fast_pull_records_durable_history(self):
        source = (ROOT / "scripts/war_room/run_fast_market_refresh.py").read_text()
        self.assertIn('"record_fast_refresh_history"', source)
        deferred = source.split('"deferred_to_daily_maintenance": [', 1)[1].split(']', 1)[0]
        self.assertNotIn("record_fast_refresh_history", deferred)

    def test_all_season_overlay_is_post_critical(self):
        source = (ROOT / "scripts/war_room/run_fast_market_refresh.py").read_text()
        ready = source.index("war_room_ready_ms =")
        self.assertLess(source.index('"war_room_market_matrix"'), ready)
        self.assertGreater(source.index('"canonical_current_market_overlay"'), ready)
        self.assertGreater(source.index('"record_fast_refresh_history"'), ready)


if __name__ == "__main__":
    unittest.main()
