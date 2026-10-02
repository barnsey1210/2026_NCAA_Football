import ast
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.markets.fast_market_horizon import remaining_season_horizon

ROOT = Path(__file__).resolve().parents[1]


class FastMarketLatencyContractTests(unittest.TestCase):
    def test_provider_request_uses_canonical_remaining_season_and_is_timed(self):
        source = (ROOT / "pull_theodds_ncaaf_lines_2026.py").read_text()
        self.assertIn('params["commenceTimeFrom"]', source)
        self.assertIn('params["commenceTimeTo"]', source)
        self.assertIn("remaining_season_horizon()", source)
        self.assertIn('"CANONICAL_REMAINING_2026_SEASON"', source)
        self.assertNotIn("timedelta(days=4)", source)
        self.assertIn('quota["normalization_ms"]', source)
        ast.parse(source)

    def test_horizon_includes_latest_canonical_kickoff_with_tail(self):
        with tempfile.TemporaryDirectory() as tmp:
            schedule = Path(tmp) / "schedule.json"
            schedule.write_text(json.dumps({"games": [
                {"start_date": "2026-10-10T16:00:00Z"},
                {"start_date": "2026-12-12T20:00:00Z"},
            ]}))
            start, end, latest = remaining_season_horizon(
                schedule,
                now=datetime(2026, 10, 2, tzinfo=timezone.utc),
            )
            self.assertEqual(start, datetime(2026, 10, 2, tzinfo=timezone.utc))
            self.assertEqual(latest, datetime(2026, 12, 12, 20, tzinfo=timezone.utc))
            self.assertEqual(end, datetime(2026, 12, 13, 20, tzinfo=timezone.utc))

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
