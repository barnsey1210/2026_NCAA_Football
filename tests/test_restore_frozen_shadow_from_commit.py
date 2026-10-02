#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/war_room/restore_frozen_shadow_from_commit.py"
SPEC = importlib.util.spec_from_file_location("restore_frozen_shadow", SCRIPT)
RESTORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESTORE)
MATRIX_SPEC = importlib.util.spec_from_file_location(
    "freeze_matrix", ROOT / "scripts/war_room/build_war_room_market_matrix.py"
)
MATRIX = importlib.util.module_from_spec(MATRIX_SPEC)
MATRIX_SPEC.loader.exec_module(MATRIX)


class RestoreFrozenShadowTests(unittest.TestCase):
    def test_exact_total_is_copied_but_unpersisted_spread_stays_blank(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "freeze.json"
            store.write_text(json.dumps({"games": {"g333": {
                "kickoff_time": "2026-10-02T01:00:00Z",
                "models": {
                    "shadow_spread": {"value_home_line": None, "selection_status": "UNAVAILABLE"},
                    "shadow_total": {"value_total": None, "selection_status": "UNAVAILABLE"},
                },
            }}}))
            contract = {"games": [{"game_id": "g333", "projections": {
                "shadow_spread_sp_sagarin_v1": {"value_home_line": None}
            }}]}
            components = {"games": [{
                "game_id": "g333", "predicted_sp_plus_component_total": 57.777564620585665,
                "spread_projection_readiness": "ready", "total_projection_readiness": "ready",
            }]}

            def git_bytes(_repo, _commit, relative):
                payload = contract if "current_game_projection" in relative else components
                return json.dumps(payload).encode()

            with mock.patch.object(RESTORE, "git_bytes", side_effect=git_bytes), \
                    mock.patch.object(RESTORE, "commit_time", return_value=RESTORE.parsed("2026-10-01T20:00:00Z")), \
                    mock.patch.object(sys, "argv", ["restore", "--source-repo", tmp,
                        "--source-commit", "63f2bc3f", "--freeze-store", str(store),
                        "--game-id", "g333", "--apply"]):
                self.assertEqual(RESTORE.main(), 0)

            frozen = json.loads(store.read_text())["games"]["g333"]
            self.assertEqual(frozen["models"]["shadow_total"]["value_total"], 57.777564620585665)
            self.assertIsNone(frozen["models"]["shadow_spread"]["value_home_line"])
            self.assertEqual(frozen["models"]["shadow_total"]["selection_reason"], "EXACT_FROZEN_PREGAME_SNAPSHOT")

    def test_all_refresh_paths_reapply_frozen_shadow_numerics(self):
        snapshot = {
            "models": {
                "shadow_spread": {"value_home_line": None, "selection_status": "UNAVAILABLE"},
                "shadow_total": {"value_total": 54.858164315391974,
                                 "selection_status": "AVAILABLE",
                                 "selection_reason": "EXACT_FROZEN_PREGAME_SNAPSHOT"},
            },
            "shadow_readiness": {"overall_status": "PARTIAL"},
        }
        for refresh in ("market", "ratings", "postgame"):
            game = {"models": {"shadow_total": {"value_total": None}}, "refresh": refresh}
            MATRIX.apply_projection_freeze(game, snapshot)
            self.assertEqual(game["models"]["shadow_total"]["value_total"], 54.858164315391974)
            self.assertIsNone(game["models"]["shadow_spread"]["value_home_line"])
            self.assertEqual(game["shadow_readiness"]["overall_status"], "PARTIAL")


if __name__ == "__main__":
    unittest.main()
