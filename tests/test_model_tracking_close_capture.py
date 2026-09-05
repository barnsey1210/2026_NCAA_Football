import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/model_tracking/v2"
SCRIPT = SCRIPT_DIR / "capture_close_checkpoints.py"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

spec = importlib.util.spec_from_file_location(
    "capture_close_checkpoints_under_test",
    SCRIPT,
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows)
    )


def read_jsonl(path):
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


class ProspectiveCloseCaptureTests(unittest.TestCase):
    def test_frozen_close_captures_spread_and_total_once(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            data_dir = td / "data/model_tracking/v2"
            market_contract = td / "data/site/current_market_contract.json"

            now = datetime.now(timezone.utc)
            prediction_at = now - timedelta(minutes=20)
            close_at = now - timedelta(minutes=5)
            kickoff = now + timedelta(hours=1)

            predictions = [
                {
                    "observation_id": "pred-spread",
                    "canonical_game_id": "g-test",
                    "season": 2026,
                    "week": 2,
                    "away_team": "Away",
                    "home_team": "Home",
                    "kickoff_at": kickoff.isoformat(),
                    "model_id": "sp_plus_spread",
                    "model_version": "v1",
                    "market_type": "spread",
                    "observed_at": prediction_at.isoformat(),
                    "source_updated_at": prediction_at.isoformat(),
                    "projection": 7.0,
                },
                {
                    "observation_id": "pred-total",
                    "canonical_game_id": "g-test",
                    "season": 2026,
                    "week": 2,
                    "away_team": "Away",
                    "home_team": "Home",
                    "kickoff_at": kickoff.isoformat(),
                    "model_id": "sp_plus_total",
                    "model_version": "v1",
                    "market_type": "total",
                    "observed_at": prediction_at.isoformat(),
                    "source_updated_at": prediction_at.isoformat(),
                    "projection": 55.0,
                },
            ]

            write_jsonl(
                data_dir / "prediction_observations.jsonl",
                predictions,
            )
            write_jsonl(
                data_dir / "market_observations.jsonl",
                [],
            )
            write_jsonl(
                data_dir / "checkpoint_observations.jsonl",
                [],
            )

            frozen_common = {
                "price": -110,
                "sportsbook": "Pinnacle",
                "source": "TEST",
                "source_updated_at": close_at.isoformat(),
                "freshness_status": "FROZEN_CLOSE",
                "market_lifecycle_state": "CLOSED",
                "kickoff_at": kickoff.isoformat(),
            }

            payload = {
                "built_at": now.isoformat(),
                "games": [
                    {
                        "game_id": "g-test",
                        "away_team": "Away",
                        "home_team": "Home",
                        "reference": {
                            "spread": {
                                "sportsbook": "Pinnacle",
                                "home": {
                                    **frozen_common,
                                    "line": -3.0,
                                },
                                "away": {
                                    **frozen_common,
                                    "line": 3.0,
                                },
                            },
                            "total": {
                                "sportsbook": "Pinnacle",
                                "over": {
                                    **frozen_common,
                                    "line": 51.5,
                                },
                                "under": {
                                    **frozen_common,
                                    "line": 51.5,
                                },
                            },
                        },
                    },
                    {
                        "game_id": "g-live",
                        "away_team": "Other Away",
                        "home_team": "Other Home",
                        "reference": {
                            "spread": {
                                "sportsbook": "Pinnacle",
                                "home": {
                                    **frozen_common,
                                    "line": -4.0,
                                    "freshness_status": "CURRENT",
                                },
                            },
                        },
                    },
                ],
            }

            market_contract.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            market_contract.write_text(json.dumps(payload))

            old_d = mod.D
            old_market = mod.MARKET_CONTRACT
            old_argv = sys.argv[:]

            try:
                mod.D = data_dir
                mod.MARKET_CONTRACT = market_contract

                sys.argv = [
                    str(SCRIPT),
                    "--accept",
                ]

                with contextlib.redirect_stdout(io.StringIO()):
                    mod.main()

                checkpoints = read_jsonl(
                    data_dir / "checkpoint_observations.jsonl"
                )
                markets = read_jsonl(
                    data_dir / "market_observations.jsonl"
                )

                self.assertEqual(len(checkpoints), 2)
                self.assertEqual(
                    {row["market_type"] for row in checkpoints},
                    {"spread", "total"},
                )
                self.assertTrue(
                    all(
                        row["checkpoint"] == "CLOSE"
                        for row in checkpoints
                    )
                )
                self.assertTrue(
                    all(
                        row["selection_status"] == "OFFICIAL"
                        for row in checkpoints
                    )
                )
                self.assertTrue(
                    all(
                        row["market_benchmark"]
                        == "CANONICAL_FROZEN_CLOSE"
                        for row in checkpoints
                    )
                )

                self.assertEqual(len(markets), 2)
                self.assertTrue(
                    all(
                        row["freshness_status"]
                        == "FROZEN_CLOSE"
                        for row in markets
                    )
                )

                checkpoint_market_ids = {
                    row["market_observation_id"]
                    for row in checkpoints
                }
                stored_market_ids = {
                    row["observation_id"]
                    for row in markets
                }

                self.assertEqual(
                    checkpoint_market_ids,
                    stored_market_ids,
                )

                with contextlib.redirect_stdout(io.StringIO()):
                    mod.main()

                checkpoints_after = read_jsonl(
                    data_dir / "checkpoint_observations.jsonl"
                )
                markets_after = read_jsonl(
                    data_dir / "market_observations.jsonl"
                )

                self.assertEqual(
                    len(checkpoints_after),
                    2,
                    "CLOSE checkpoints must be immutable/idempotent",
                )
                self.assertEqual(
                    len(markets_after),
                    2,
                    "Frozen market observations must not duplicate",
                )

            finally:
                mod.D = old_d
                mod.MARKET_CONTRACT = old_market
                sys.argv = old_argv


if __name__ == "__main__":
    unittest.main()
