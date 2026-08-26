import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTROL = load("postgame_control", "scripts/control/run_data_refresh.py")
MATRIX = load("postgame_matrix", "scripts/war_room/build_war_room_market_matrix.py")
PULL = load("postgame_pull", "scripts/postgame/pull_cfbd_postgame_2026.py")


class PostgameOperationalServiceTests(unittest.TestCase):
    def test_command_path_is_runtime_only_and_ordered(self):
        commands = CONTROL.postgame_commands()
        names = [Path(command[1]).name for command in commands]
        self.assertEqual(names[0], "pull_cfbd_schedule_2026.py")
        self.assertEqual(names[-2:], ["build_war_room_health.py", "build_war_room_market_matrix.py"])
        joined = " ".join(" ".join(command) for command in commands)
        for forbidden in (
            "build_public_site.py", "build_war_room_home.py", "publish_site.sh",
            "check_public_site.py", "apply_shared_war_room_shell.py",
            "compact_matchups_payload.py", "inject_market_presentation_fixes.py",
        ):
            self.assertNotIn(forbidden, joined)

    def test_postgame_service_needs_no_publish_confirmation(self):
        run = {"status": "RUNNING", "errors": [], "stages": [], "publication": {}}
        with patch.object(CONTROL, "run_commands", return_value=True):
            CONTROL.execute_postgame_service(run)
        self.assertEqual(run["status"], "COMPLETED")
        self.assertEqual(run["publication"]["status"], "SKIPPED_RUNTIME_ONLY")

    def test_no_completed_games_makes_zero_rich_calls(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            PULL, "completed_games", return_value=[]
        ), patch.object(PULL, "AUDIT", Path(temporary) / "audit.json"), patch.object(
            PULL, "require_key", side_effect=AssertionError("credential should not be read")
        ), patch.object(sys, "argv", ["pull_cfbd_postgame_2026.py"]):
            PULL.main()
            audit = json.loads((Path(temporary) / "audit.json").read_text())
        self.assertEqual(audit["status"], "NO_COMPLETED_GAMES")
        self.assertEqual(audit["api_calls_this_run"], 0)

    def test_unlv_hawaii_domain_readiness_progression(self):
        matchup = {"away_team": "UNLV", "home_team": "Hawaii"}
        self.assertEqual((matchup["away_team"], matchup["home_team"]), ("UNLV", "Hawaii"))
        none = MATRIX.shadow_readiness({
            "away_spread_shadow_ready": False, "home_spread_shadow_ready": False,
            "away_total_shadow_ready": False, "home_total_shadow_ready": False,
        })
        partial = MATRIX.shadow_readiness({
            "away_spread_shadow_ready": True, "home_spread_shadow_ready": False,
            "away_total_shadow_ready": False, "home_total_shadow_ready": False,
            "shadow_spread_updated_team_count": 1,
        })
        ready = MATRIX.shadow_readiness({
            "away_spread_shadow_ready": True, "home_spread_shadow_ready": True,
            "away_total_shadow_ready": True, "home_total_shadow_ready": True,
            "shadow_spread_updated_team_count": 2,
            "shadow_total_updated_team_count": 2,
        })
        self.assertFalse(none["away_spread_shadow_ready"])
        self.assertEqual(partial["spread_status"], "PARTIAL")
        self.assertEqual(partial["total_status"], "WAITING")
        self.assertEqual(ready["spread_status"], "READY")
        self.assertEqual(ready["total_status"], "READY")

    def test_readiness_is_component_validity_not_game_final(self):
        state = MATRIX.shadow_readiness({
            "completed_team_update_count": 2,
            "away_spread_shadow_ready": False,
            "home_spread_shadow_ready": False,
            "away_total_shadow_ready": True,
            "home_total_shadow_ready": False,
        })
        self.assertFalse(state["away_spread_shadow_ready"])
        self.assertEqual(state["spread_status"], "WAITING")
        self.assertEqual(state["total_status"], "PARTIAL")
        public = (ROOT / "scripts/site/build_war_room_page.py").read_text()
        self.assertIn("model?.selection_status==='AVAILABLE'", public)
        self.assertIn("readyCount===1?'PARTIAL':'UNAVAILABLE'", public)

    def test_projection_authority_owner_unchanged(self):
        source = (ROOT / "scripts/war_room/build_war_room_market_matrix.py").read_text()
        self.assertIn("if updated_count >= 2:", source)
        self.assertIn('"projection_authority": "HYBRID_REFRESHED_SOURCES"', source)


if __name__ == "__main__":
    unittest.main()
