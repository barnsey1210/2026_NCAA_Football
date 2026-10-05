from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "recover_odds_payloads", ROOT / "scripts/control/recover_odds_payloads.py"
)
recovery = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(recovery)


class OddsPayloadRecoveryTests(unittest.TestCase):
    def write_json(self, root: Path, relative: str, value: dict) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_recovers_stale_odds_from_fresh_accepted_market_without_acquisition(self):
        now = datetime(2026, 10, 5, 12, tzinfo=timezone.utc)
        market_time = now - timedelta(minutes=5)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_json(root, "data/site/current_market_contract.json", {
                "schema_version": "current-market-contract-v1", "built_at": market_time.isoformat()
            })
            self.write_json(root, "data/site/odds_screen_v2.json", {
                "built_at": (now - timedelta(hours=36)).isoformat()
            })

            def rebuilt(command, cwd, check):
                if command[-1].endswith("build_odds_screen_v2.py"):
                    self.write_json(root, "data/site/odds_screen_v2.json", {"built_at": market_time.isoformat()})

            with mock.patch.object(recovery.subprocess, "run", side_effect=rebuilt) as run:
                self.assertEqual(recovery.recover(root, 18, now), "recovered")
            self.assertEqual(run.call_count, 2)
            self.assertTrue(all("pull" not in " ".join(call.args[0]) for call in run.call_args_list))

    def test_refuses_recovery_from_genuinely_stale_market(self):
        now = datetime(2026, 10, 5, 12, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_json(root, "data/site/current_market_contract.json", {
                "schema_version": "current-market-contract-v1",
                "built_at": (now - timedelta(hours=19)).isoformat(),
            })
            with mock.patch.object(recovery.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "recovery limit"):
                    recovery.recover(root, 18, now)
            run.assert_not_called()

    def test_copy_mtime_cannot_make_stale_payload_current(self):
        publisher = (ROOT / "scripts/publish/publish_site.sh").read_text(encoding="utf-8")
        gate = publisher[publisher.index("payload = json.loads"):publisher.index('log "public build validation passed"')]
        self.assertIn('payload.get("built_at")', gate)
        self.assertNotIn("path.stat().st_mtime", gate)

    def test_abort_path_attempts_bounded_recovery_before_finalization(self):
        source = (ROOT / "daily_market_update.sh").read_text(encoding="utf-8")
        exit_block = source[source.index("on_exit()") : source.index("trap on_exit EXIT")]
        self.assertIn("recover_odds_payloads.py --max-age-hours 18", exit_block)
        self.assertLess(exit_block.index("recover_odds_payloads.py"), exit_block.index("finalize_run_status"))
        self.assertIn('odds_status" = "PENDING"', exit_block)

    def test_simulation_recording_passes_domain_as_argument(self):
        source = (ROOT / "daily_market_update.sh").read_text(encoding="utf-8")
        self.assertIn('run_py "scripts/simulations/simulation_input_gate.py" "simulation_input_gate.py" conference --record', source)
        self.assertNotIn('simulation_input_gate.py conference --record"', source)


if __name__ == "__main__":
    unittest.main()
