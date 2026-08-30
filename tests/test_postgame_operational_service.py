import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTROL = load("postgame_control", "scripts/control/run_data_refresh.py")
MATRIX = load("postgame_matrix", "scripts/war_room/build_war_room_market_matrix.py")
PULL = load("postgame_pull", "scripts/postgame/pull_cfbd_postgame_2026.py")
FEATURES = load("postgame_features", "scripts/postgame/build_postgame_features_2026.py")
SHADOW_FEATURES = load(
    "shadow_team_features",
    "scripts/postgame/build_shadow_team_game_features_2026.py",
)
TEAM_IDENTITY = load("postgame_team_identity", "scripts/site/team_identity.py")


class PostgameOperationalServiceTests(unittest.TestCase):
    def test_canonical_team_identity_folds_diacritics_without_fuzzy_matching(self):
        self.assertEqual(
            TEAM_IDENTITY.canonical_team_name("San Jos\u00e9 State"),
            "San Jose State",
        )
        self.assertEqual(
            TEAM_IDENTITY.canonical_team_name("Eastern Michigan"),
            "Eastern Michigan",
        )
        self.assertNotEqual(
            TEAM_IDENTITY.canonical_team_key("Miami (OH)"),
            TEAM_IDENTITY.canonical_team_key("Miami (FL)"),
        )

    def test_postgame_pbp_matches_accented_provider_team_to_canonical_team(self):
        results = [{
            "game_id": "g7",
            "cfbd_game_id": 401864494,
            "home_team": "USC",
            "away_team": "San Jose State",
        }]
        plays = [
            {
                "gameId": 401864494,
                "offense": "San Jos\u00e9 State",
                "defense": "USC",
                "playType": "Rush",
                "ppa": 0.4,
                "period": 1,
            },
            {
                "gameId": 401864494,
                "offense": "USC",
                "defense": "San Jos\u00e9 State",
                "playType": "Pass Reception",
                "ppa": -0.1,
                "period": 1,
            },
        ]
        rows = FEATURES.build_pbp_rows(0, results, plays, [])
        sjsu = next(row for row in rows if row["team"] == "San Jose State")
        self.assertEqual(sjsu["off_plays"], 1)
        self.assertEqual(sjsu["off_ppa"], 0.4)
        self.assertEqual(sjsu["def_ppa_allowed"], -0.1)

    def test_shadow_clean_preserves_ordered_multi_value_data(self):
        value = {
            "array": np.array([1.0, np.nan, 3.0]),
            "series": pd.Series([np.int64(4), "x"]),
            "tuple": (True, np.float64(2.5)),
            "list": [None, {"nested": np.int64(7)}],
        }
        self.assertEqual(
            SHADOW_FEATURES.clean(value),
            {
                "array": [1.0, None, 3.0],
                "series": [4, "x"],
                "tuple": [True, 2.5],
                "list": [None, {"nested": 7}],
            },
        )

    def test_command_path_is_runtime_only_and_ordered(self):
        commands = CONTROL.postgame_commands()
        names = [Path(command[1]).name for command in commands]
        self.assertEqual(names[0], "pull_cfbd_schedule_2026.py")
        self.assertLess(
            names.index("build_market_implied_power_ratings.py"),
            names.index("build_shadow_team_game_features_2026.py"),
        )
        market_command = commands[
            names.index("build_market_implied_power_ratings.py")
        ]
        self.assertIn("--production-2026", market_command)
        self.assertEqual(
            names[-3:],
            [
                "build_war_room_health.py",
                "build_war_room_market_matrix.py",
                "build_war_room_activity.py",
            ],
        )
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

    def test_prepared_results_skips_only_schedule_and_results(self):
        full = CONTROL.postgame_commands()
        prepared = CONTROL.postgame_commands(skip_schedule=True)
        self.assertEqual(prepared, full[2:])
        self.assertEqual(Path(prepared[0][1]).name, "pull_cfbd_postgame_2026.py")
        dispatcher = (ROOT / "scripts/control/run_war_room_service.py").read_text()
        self.assertIn('command = [*command, "--postgame-skip-schedule"]', dispatcher)

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

    def test_week_cache_refreshes_when_new_final_is_missing(self):
        completed = {"401761599", "401761602"}
        first_final_only = [
            {"gameId": 401761599, "playType": "Rush"},
        ]
        self.assertFalse(
            PULL.cache_covers_completed_games(
                first_final_only,
                completed,
            )
        )
        self.assertEqual(
            PULL.row_game_ids(first_final_only),
            {"401761599"},
        )

    def test_week_cache_is_reused_after_all_finals_are_present(self):
        completed = {"401761599", "401761602"}
        complete = [
            {"gameId": 401761599},
            {"game_id": "401761602"},
        ]
        self.assertTrue(
            PULL.cache_covers_completed_games(
                complete,
                completed,
            )
        )

    def test_provider_week_translation_uses_schedule_owned_mapping(self):
        known_game_ids = {
            401856766,
            401858202,
            401864494,
            401864577,
            401866408,
        }
        opening_week = [
            {"week": 0, "provider_week": 1, "cfbd_game_id": game_id}
            for game_id in known_game_ids
        ]
        provider_week_one_plays = [
            {"gameId": game_id, "playType": "fixture"}
            for game_id in known_game_ids
        ]
        later_week = [
            {"week": 2, "provider_week": 2, "cfbd_game_id": 401000001},
        ]
        week_one = [
            {"week": 1, "provider_week": 1, "cfbd_game_id": 401000000},
        ]
        self.assertEqual(PULL.resolve_provider_week(opening_week, 0), 1)
        self.assertTrue(PULL.cache_covers_completed_games(
            provider_week_one_plays,
            {str(game_id) for game_id in known_game_ids},
        ))
        self.assertEqual(PULL.resolve_provider_week(week_one, 1), 1)
        self.assertEqual(PULL.resolve_provider_week(later_week, 2), 2)

    def test_provider_week_translation_rejects_missing_or_ambiguous_mapping(self):
        with self.assertRaisesRegex(RuntimeError, "Missing CFBD provider_week"):
            PULL.resolve_provider_week(
                [{"week": 0, "cfbd_game_id": 401864494}],
                0,
            )
        with self.assertRaisesRegex(RuntimeError, "Ambiguous CFBD provider_week"):
            PULL.resolve_provider_week(
                [
                    {"week": 0, "provider_week": 1, "cfbd_game_id": 1},
                    {"week": 0, "provider_week": 2, "cfbd_game_id": 2},
                ],
                0,
            )

    def test_main_refreshes_incomplete_endpoint_caches_without_force(self):
        completed = [
            {"week": 0, "provider_week": 1, "cfbd_game_id": 401761599},
            {"week": 0, "provider_week": 1, "cfbd_game_id": 401761602},
        ]

        class FixtureClient:
            instance = None

            def __init__(self, key, max_calls):
                self.calls = 0
                self.requested = []
                FixtureClient.instance = self

            def get(self, endpoint, params):
                self.calls += 1
                self.requested.append((endpoint, dict(params)))
                return [
                    {"gameId": 401761599},
                    {"gameId": 401761602},
                ]

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            week_dir = root / "week_00"
            for name, endpoint in (
                ("plays", "/plays"),
                ("drives", "/drives"),
                ("havoc", "/stats/game/havoc"),
            ):
                PULL.write_gzip(
                    week_dir / f"{name}.json.gz",
                    endpoint,
                    {"year": 2026, "week": 0},
                    [{"gameId": 401761599}],
                )

            with patch.object(
                PULL, "completed_games", return_value=completed
            ), patch.object(
                PULL, "ROOT", root
            ), patch.object(
                PULL, "OUT_ROOT", root
            ), patch.object(
                PULL, "AUDIT", root / "audit.json"
            ), patch.object(
                PULL, "require_key", return_value="fixture-only"
            ), patch.object(
                PULL, "CFBDClient", FixtureClient
            ), patch.object(
                sys, "argv", ["pull_cfbd_postgame_2026.py", "--week", "0"]
            ):
                PULL.main()

            audit = json.loads((root / "audit.json").read_text())

        self.assertEqual(audit["api_calls_this_run"], 3)
        self.assertEqual(audit["status"], "READY")
        self.assertEqual(
            [endpoint for endpoint, _ in FixtureClient.instance.requested],
            ["/plays", "/drives", "/stats/game/havoc"],
        )
        self.assertTrue(all(
            params["week"] == 1
            for _, params in FixtureClient.instance.requested
        ))
        for row in audit["files"].values():
            self.assertEqual(row["completed_game_ids_missing_after_read"], [])
        self.assertEqual(audit["week"], 0)
        self.assertEqual(audit["provider_week"], 1)
        self.assertTrue(all(
            row["source"] == "api_incomplete_cache_refresh"
            for row in audit["files"].values()
        ))

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
