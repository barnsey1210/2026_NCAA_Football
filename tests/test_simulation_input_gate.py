import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "simulation_input_gate", ROOT / "scripts/simulations/simulation_input_gate.py"
)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class SimulationInputGateTests(unittest.TestCase):
    def test_digest_changes_only_with_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a").write_text("one")
            (root / "b").write_text("two")
            with mock.patch.object(gate, "ROOT", root):
                first = gate.digest(("a", "b"))
                self.assertEqual(first, gate.digest(("a", "b")))
                (root / "b").write_text("three")
                self.assertNotEqual(first, gate.digest(("a", "b")))

    def test_daily_pipeline_preserves_outputs_when_unchanged(self):
        source = (ROOT / "daily_market_update.sh").read_text()
        self.assertIn("simulation_input_gate.py conference", source)
        self.assertIn("simulation_input_gate.py playoff", source)
        self.assertIn("preserving accepted output", source)


if __name__ == "__main__":
    unittest.main()
