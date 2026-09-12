from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/model_tracking/v2"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

SPEC = importlib.util.spec_from_file_location(
    "settlement_under_test",
    SCRIPT_DIR / "settle_accepted_observations.py",
)

M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_close_does_not_use_normalized_market():
    checkpoint = {
        "checkpoint": "CLOSE",
        "market_observation_id": "legacy-1",
    }

    result = M.resolve_normalized_checkpoint_market(
        checkpoint,
        {"markets_by_confirmation": {}},
        {"legacy-1": {"line": -7}},
    )

    assert result is None


def test_explicit_confirmation_id_is_preferred():
    market = {
        "market_confirmation_id": "confirm-1",
        "line": -7,
    }

    checkpoint = {
        "checkpoint": "SUNDAY_9PM_ET",
        "market_confirmation_id": "confirm-1",
        "market_observation_id": "legacy-1",
    }

    result = M.resolve_normalized_checkpoint_market(
        checkpoint,
        {
            "markets_by_confirmation": {
                "confirm-1": market,
            }
        },
        {
            "legacy-1": {
                "line": -6.5,
            }
        },
    )

    assert result is market


def test_historical_checkpoint_uses_immutable_snapshot():
    checkpoint = {
        "checkpoint": "TUESDAY_9PM_ET",
        "canonical_game_id": "g1",
        "market_type": "spread",
        "bet_side": "home",
        "market_observation_id": "legacy-1",
        "market_line": -7.0,
        "market_price": -110,
        "market_book": "Pinnacle",
        "market_source": "TEST",
        "market_observed_at":
            "2026-09-09T12:00:00+00:00",
        "market_source_updated_at":
            "2026-09-09T11:59:00+00:00",
    }

    result = M.resolve_normalized_checkpoint_market(
        checkpoint,
        {"markets_by_confirmation": {}},
        {},
    )

    assert result is not None
    assert result["line"] == -7.0
    assert result["price"] == -110
    assert result["sportsbook"] == "Pinnacle"
    assert result["observation_id"] == "legacy-1"



def test_market_semantic_parity_ignores_ids():
    legacy = {
        "canonical_game_id": "g1",
        "market_type": "spread",
        "sportsbook": "Pinnacle",
        "side": "home",
        "line": -7,
        "price": -110,
        "source": "TEST",
        "freshness_status": "LIVE",
        "lifecycle_state": "OPEN",
        "observed_at": "2026-09-01T12:00:00+00:00",
        "source_updated_at":
            "2026-09-01T11:59:00+00:00",
        "observation_id": "legacy",
    }

    normalized = {
        **legacy,
        "observation_id": "confirmation",
        "market_state_id": "state",
        "market_confirmation_id": "confirmation",
    }

    assert M.market_semantics_match(
        legacy,
        normalized,
    )


def test_prediction_accuracy_freezes_latest_valid_pre_kickoff_without_market():
    base = {
        "canonical_game_id": "g1", "model_id": "standard_spread_4src_equal_v1",
        "model_version": "v1", "market_type": "spread", "season": 2026,
        "week": 2, "kickoff_at": "2026-09-12T16:00:00+00:00",
        "availability_status": "AVAILABLE",
    }
    predictions = [
        {**base, "observation_id": "early", "observed_at": "2026-09-11T12:00:00+00:00", "projection": 7},
        {**base, "observation_id": "latest", "observed_at": "2026-09-12T15:00:00+00:00", "projection": 9},
        {**base, "observation_id": "late", "observed_at": "2026-09-12T17:00:00+00:00", "projection": 99},
    ]
    rows, skipped = M.frozen_prediction_scores(
        predictions,
        {"g1": {"home_margin_actual": 6, "total_points_actual": 48}},
        {"g1": "settlement-1"},
    )
    assert len(rows) == 1
    assert rows[0]["prediction_observation_id"] == "latest"
    assert rows[0]["absolute_error"] == 3
    assert skipped["not_pre_kickoff"] == 1
