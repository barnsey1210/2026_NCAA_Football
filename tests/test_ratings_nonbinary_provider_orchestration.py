import importlib.util
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ratings_refresh", ROOT / "scripts/control/run_data_refresh.py"
)
refresh = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(refresh)


def base_run():
    return {
        "status": "RUNNING",
        "errors": [],
        "warnings": [],
        "stages": [],
        "validation_results": {},
        "providers_called": [],
        "api": {"calls_consumed": 0},
    }


def execute_with_partial(changed_provider, failed_provider=None):
    run = base_run()
    report = {
        "changed_providers": [changed_provider],
        "coverage": {
            "massey": {
                "games_requested": 117,
                "games_resolved": 116,
                "missing_game_ids": ["g451"],
            }
        },
        "provider_warnings": (
            [{"provider": failed_provider, "status": "FAILED_LAST_KNOWN_GOOD_RETAINED"}]
            if failed_provider else []
        ),
    }
    with patch.object(refresh, "run_commands", return_value=True) as runner, patch.object(
        refresh, "accepted_ratings_changed", return_value=(False, {"SP+": "NO_CHANGE"})
    ), patch.object(refresh, "matchup_source_refresh_status", return_value=(True, report)):
        refresh.execute_ratings_service(run, {"publication_policy": {"ratings": True}}, True)
    return run, runner


def test_spplus_change_with_partial_massey_propagates_and_publishes():
    run, runner = execute_with_partial("spplus")
    assert run["status"] == "COMPLETED_WITH_WARNINGS"
    assert run["publication"]["status"] == "LIVE_RUNTIME_READY"
    assert run["change_counts"]["projections"] == 1
    assert runner.call_count == 2


def test_dratings_change_with_partial_massey_propagates_and_publishes():
    run, _ = execute_with_partial("dratings")
    assert run["status"] == "COMPLETED_WITH_WARNINGS"
    assert run["change_counts"] == {"ratings": 1, "projections": 1}


def test_one_provider_hard_failure_does_not_block_other_valid_change():
    run, _ = execute_with_partial("dratings", failed_provider="sagarin")
    warnings = run["validation_results"]["provider_warnings"]
    assert {row["provider"] for row in warnings} == {"sagarin", "massey"}
    assert run["status"] == "COMPLETED_WITH_WARNINGS"


def test_change_path_rebuilds_strict_projection_and_public_status_contracts():
    names = [Path(command[1]).name for command in refresh.ratings_change_commands()]
    assert names.index("build_game_projection_sources_2026.py") < names.index(
        "build_current_game_projection_contract.py"
    )
    assert names.index("build_current_game_projection_contract.py") < names.index(
        "build_projection_source_status_view.py"
    )
    assert names.index("build_projection_source_status_view.py") < names.index(
        "build_war_room_market_matrix.py"
    )
