import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "massey_safari", ROOT / "scripts/projections/collect_massey_games_2026_safari.py"
)
MASSEY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MASSEY)


class RatingsOperationalCleanupTests(unittest.TestCase):
    def test_sagarin_centering_and_composite_invariants(self):
        frame = pd.read_csv(ROOT / "data/ratings/ratings_master_latest.csv")
        raw = pd.to_numeric(frame["sagarin_raw"], errors="coerce")
        normalized = pd.to_numeric(frame["sagarin"], errors="coerce")
        self.assertAlmostEqual(float(normalized.mean()), 0.0, places=9)
        self.assertEqual(list(raw.rank(method="min")), list(normalized.rank(method="min")))
        self.assertAlmostEqual(float(raw.iloc[0] - raw.iloc[1]), float(normalized.iloc[0] - normalized.iloc[1]), places=9)
        expected = frame[["spplus", "fpi", "teamrankings", "sagarin"]].mean(axis=1)
        self.assertLess(float((expected - frame["power_rating"]).abs().max()), 1e-9)

    def test_safari_worker_scripts_never_use_front_window(self):
        calls = []
        def fake(script, timeout=45):
            calls.append(script)
            return "4242" if "priorIds" in script else "page text"
        with patch.object(MASSEY, "run_applescript", side_effect=fake):
            worker = MASSEY.create_safari_worker()
            MASSEY.safari_capture("2026-08-29", worker, wait_seconds=0)
            MASSEY.close_safari_worker(worker)
        self.assertEqual(worker, 4242)
        joined = "\n".join(calls)
        self.assertNotIn("front window", joined)
        self.assertNotIn("activate", joined)
        self.assertIn("window id 4242", calls[1])
        self.assertIn("close window id 4242", calls[2])

    def test_cleanup_is_best_effort_and_worker_scoped(self):
        with patch.object(MASSEY, "run_applescript", side_effect=RuntimeError("fixture")):
            MASSEY.close_safari_worker(77)

    def test_fast_and_daily_horizons_remain_seven_and_fourteen(self):
        fast = (ROOT / "scripts/ratings/run_fast_standard_source_refresh.py").read_text()
        daily = (ROOT / "daily_market_update.sh").read_text()
        wrapper = (ROOT / "scripts/projections/refresh_massey_game_projections_2026.py").read_text()
        self.assertIn('"--days", "7"', fast)
        self.assertIn('default=14', wrapper)
        self.assertIn('end = start + timedelta(days=args.days)', wrapper)
        self.assertIn('refresh_massey_game_projections_2026.py', daily)

    def test_public_operator_never_posts_directly(self):
        public = (ROOT / "scripts/site/build_war_room_page.py").read_text()
        protected = (ROOT / "scripts/war_room/war_room_operator_api.py").read_text()
        self.assertNotIn("method:'POST'", public)
        self.assertIn("event.source!==window.opener", protected)
        self.assertIn("event.origin!==TARGET_ORIGIN", protected)
        self.assertIn("channelNonce", protected)


if __name__ == "__main__":
    unittest.main()
