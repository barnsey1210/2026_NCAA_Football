import importlib.util
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "agents" / "build_daily_betting_angles.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_daily_betting_angles", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DailyBettingAnglesEmptyInputTest(unittest.TestCase):
    def test_empty_optional_csv_is_zero_rows(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "market_arbitrage_opportunities.csv"
            path.write_text("", encoding="utf-8")
            result = module.read_csv(path)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

    def test_nonempty_csv_still_parses_normally(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "market_arbitrage_opportunities.csv"
            path.write_text("type,team\nArbitrage,Ohio State\n", encoding="utf-8")
            result = module.read_csv(path)

        self.assertEqual(
            result.to_dict("records"),
            [{"type": "Arbitrage", "team": "Ohio State"}],
        )

    def test_daily_pipeline_scoped_futures_publish_precedes_injuries(self):
        source = (ROOT / "daily_market_update.sh").read_text(encoding="utf-8")
        publish = source.index("bash scripts/publish/publish_site.sh --futures-push")
        injuries = source.index('# STAGE: injuries_and_signals')
        self.assertLess(publish, injuries)


if __name__ == "__main__":
    unittest.main()
