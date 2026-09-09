from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/model_tracking/v2"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

SPEC = importlib.util.spec_from_file_location(
    "normalized_checkpoint_reader_under_test",
    SCRIPT_DIR / "normalized_checkpoint_reader.py",
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def confirmation(
    *,
    state="state-1",
    observed="2026-09-09T12:00:00+00:00",
    source_updated="2026-09-09T11:59:00+00:00",
):
    row = {
        "market_state_id": state,
        "observed_at": observed,
        "source_updated_at": source_updated,
    }
    row["confirmation_id"] = (
        M.expected_market_confirmation_id(row)
    )
    return row


def test_current_confirmation_identity_is_canonical():
    row = confirmation()
    assert M.is_canonical_market_confirmation(row)


def test_superseded_confirmation_identity_is_rejected():
    row = confirmation()
    row["confirmation_id"] = "old-stage-a-id"
    assert not M.is_canonical_market_confirmation(row)


def test_observed_at_fallback_when_provider_timestamp_missing():
    first = confirmation(
        observed="2026-09-09T12:00:00+00:00",
        source_updated=None,
    )
    second = confirmation(
        observed="2026-09-09T12:02:00+00:00",
        source_updated=None,
    )

    assert (
        first["confirmation_id"]
        != second["confirmation_id"]
    )


def test_normalized_market_retains_legacy_compatibility_id(tmp_path):
    import json

    state = {
        "market_state_id": "state-1",
        "canonical_game_id": "g1",
        "market_type": "spread",
        "sportsbook": "Pinnacle",
        "side": "home",
        "line": -7.0,
        "price": -110,
        "source": "TEST",
        "freshness_status": "LIVE",
        "lifecycle_state": "OPEN",
    }

    confirmation = {
        "market_state_id": "state-1",
        "observed_at": "2026-09-09T12:00:00+00:00",
        "source_updated_at":
            "2026-09-09T11:59:00+00:00",
        "contract_id": "contract-1",
        "kickoff_at": "2026-09-12T23:30:00+00:00",
        "legacy_market_observation_id":
            "legacy-market-123",
    }

    confirmation["confirmation_id"] = (
        M.expected_market_confirmation_id(
            confirmation
        )
    )

    (tmp_path / "market_states.jsonl").write_text(
        json.dumps(state) + "\n"
    )
    (
        tmp_path / "market_confirmations.jsonl"
    ).write_text(
        json.dumps(confirmation) + "\n"
    )
    (tmp_path / "decision_states.jsonl").write_text("")
    (
        tmp_path / "decision_confirmations.jsonl"
    ).write_text("")

    context = M.build_normalized_context(tmp_path)

    assert len(context["markets"]) == 1

    market = context["markets"][0]

    assert (
        market["legacy_market_observation_id"]
        == "legacy-market-123"
    )
    assert (
        market["observation_id"]
        == confirmation["confirmation_id"]
    )


def test_normalized_fallback_retains_legacy_decision_id(tmp_path):
    import json

    state = {
        "market_state_id": "state-1",
        "canonical_game_id": "g1",
        "market_type": "spread",
        "sportsbook": "Reference",
        "side": "home",
        "line": -7.0,
        "price": -110,
        "source": "TEST",
        "freshness_status": "LIVE",
        "lifecycle_state": "OPEN",
    }

    market_confirmation = {
        "market_state_id": "state-1",
        "observed_at": "2026-09-09T12:00:00+00:00",
        "source_updated_at":
            "2026-09-09T11:59:00+00:00",
        "contract_id": "contract-1",
        "kickoff_at": "2026-09-12T23:30:00+00:00",
        "legacy_market_observation_id":
            "legacy-market-1",
    }

    market_confirmation["confirmation_id"] = (
        M.expected_market_confirmation_id(
            market_confirmation
        )
    )

    decision_state = {
        "decision_state_id": "decision-state-1",
        "prediction_observation_id": "prediction-1",
        "market_state_id": "state-1",
        "canonical_game_id": "g1",
        "market_type": "spread",
        "checkpoint": "OPEN",
        "bet_side": "home",
        "edge": 3.0,
        "market_provenance": {},
        "first_observed_at":
            "2026-09-09T12:00:01+00:00",
        "legacy_decision_id":
            "legacy-decision-1",
        "legacy_market_observation_id":
            "legacy-market-1",
    }

    decision_confirmation = {
        "confirmation_id":
            "decision-confirmation-1",
        "decision_state_id":
            "decision-state-1",
        "market_confirmation_id":
            market_confirmation["confirmation_id"],
        "created_at":
            "2026-09-09T12:00:01+00:00",
        "legacy_decision_id":
            "legacy-decision-1",
        "legacy_market_observation_id":
            "legacy-market-1",
    }

    (tmp_path / "market_states.jsonl").write_text(
        json.dumps(state) + "\n"
    )
    (
        tmp_path / "market_confirmations.jsonl"
    ).write_text(
        json.dumps(market_confirmation) + "\n"
    )
    (
        tmp_path / "decision_states.jsonl"
    ).write_text(
        json.dumps(decision_state) + "\n"
    )
    (
        tmp_path / "decision_confirmations.jsonl"
    ).write_text(
        json.dumps(decision_confirmation) + "\n"
    )

    context = M.build_normalized_context(tmp_path)

    market, decision, benchmark = (
        M.choose_reference_fallback(
            context,
            "prediction-1",
            M.parse_dt(
                "2026-09-09T13:00:00+00:00"
            ),
        )
    )

    assert market is not None
    assert decision is not None
    assert benchmark == "CANONICAL_REFERENCE_FALLBACK"

    assert (
        market["legacy_market_observation_id"]
        == "legacy-market-1"
    )
    assert (
        decision["decision_id"]
        == "legacy-decision-1"
    )
