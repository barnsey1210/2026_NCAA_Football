import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts/audit/audit_war_room_fast_publication.py"


class WarRoomFastPublicationScopeTest(unittest.TestCase):
    def build_bundle(self, *, health_matched=76, health_unmatched=2, matrix_unmatched=2):
        temporary = tempfile.TemporaryDirectory()
        bundle = Path(temporary.name)
        data = bundle / "data/site"
        data.mkdir(parents=True)
        now = datetime.now(timezone.utc).isoformat()
        page = "cache:'no-store'\n" + "\n".join(
            f"data/site/{name}"
            for name in (
                "war_room_health.json",
                "war_room_market_matrix.json",
                "war_room_activity.json",
            )
        )
        (bundle / "war-room.html").write_text(page.ljust(1200, " "))
        health = {
            "schema_version": "war-room-health-v1",
            "built_at": now,
            "fast_market_refresh": {
                "refresh_id": "theodds_test",
                "last_fast_pull_at": now,
                "upcoming_games_in_pull": 78,
            },
            "projection_health": {
                "scope": "LATEST_FAST_BOARD_FBS_VS_FBS_ONLY",
                "matched_fast_board_games": health_matched,
                "unmatched_fast_board_games": health_unmatched,
                "by_week": {
                    "4": {
                        market: {"status": "OFFICIAL"}
                        for market in ("spread", "total", "shadow")
                    }
                },
            },
        }
        matrix = {
            "schema_version": "war-room-market-matrix-v1",
            "built_at": now,
            "fast_market_refresh": {
                "refresh_id": "theodds_test",
                "last_fast_pull_at": now,
            },
            "summary": {"fast_market_games_matched": 76},
            "games": [{"game_id": "g1"}],
            "audit": {
                "unmatched_fast_rows": [
                    {"provider_game_id": f"provider-{index}"}
                    for index in range(matrix_unmatched)
                ]
            },
        }
        activity = {
            "schema_version": "war-room-activity-v1",
            "events": [],
        }
        for name, payload in (
            ("war_room_health.json", health),
            ("war_room_market_matrix.json", matrix),
            ("war_room_activity.json", activity),
        ):
            (data / name).write_text(json.dumps(payload))
        return temporary, bundle

    def run_audit(self, bundle):
        return subprocess.run(
            [sys.executable, str(AUDIT), "--bundle", str(bundle)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def test_legitimate_out_of_scope_games_reconcile_without_weakening_guard(self):
        temporary, bundle = self.build_bundle()
        with temporary:
            result = self.run_audit(bundle)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unexplained_unmatched_game_still_fails_closed(self):
        temporary, bundle = self.build_bundle(matrix_unmatched=1)
        with temporary:
            result = self.run_audit(bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("distinct unmatched matrix games (1)", result.stdout)


if __name__ == "__main__":
    unittest.main()
