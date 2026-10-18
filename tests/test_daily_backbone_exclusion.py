import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "run_war_room_service_daily_guard",
    ROOT / "scripts/control/run_war_room_service.py",
)
SERVICE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SERVICE)


class DailyBackboneExclusionTests(unittest.TestCase):
    def write_status(self, payload: str) -> Path:
        temp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        self.addCleanup(Path(temp.name).unlink, missing_ok=True)
        with temp:
            temp.write(payload)
        return Path(temp.name)

    def test_canonical_overall_result_running_blocks_fast_writers(self):
        path = self.write_status('{"overall_result":"RUNNING"}')
        with mock.patch.object(SERVICE, "DAILY_STATUS", path):
            self.assertTrue(SERVICE.daily_running())

    def test_finished_daily_run_does_not_block_fast_writers(self):
        path = self.write_status('{"overall_result":"PASSED"}')
        with mock.patch.object(SERVICE, "DAILY_STATUS", path):
            self.assertFalse(SERVICE.daily_running())

    def test_legacy_status_field_remains_supported(self):
        path = self.write_status('{"status":"IN_PROGRESS"}')
        with mock.patch.object(SERVICE, "DAILY_STATUS", path):
            self.assertTrue(SERVICE.daily_running())


if __name__ == "__main__":
    unittest.main()
