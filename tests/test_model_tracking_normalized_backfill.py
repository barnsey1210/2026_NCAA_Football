from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/model_tracking/v2"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

SPEC = importlib.util.spec_from_file_location(
    "normalized_backfill_under_test",
    SCRIPT_DIR / "backfill_normalized_market_tracking.py",
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def market(
    observation_id,
    *,
    line=-7.0,
    observed_at="2026-09-09T12:00:00+00:00",
    source_updated_at="2026-09-09T11:59:00+00:00",
):
    return {
        "observation_id": observation_id,
        "canonical_game_id": "g1",
        "market_type": "spread",
        "sportsbook": "Pinnacle",
        "side": "home",
        "line": line,
        "price": -110,
        "source": "The Odds API",
        "freshness_status": "LIVE",
        "lifecycle_state": "OPEN",
        "observed_at": observed_at,
        "source_updated_at": source_updated_at,
        "contract_id": "contract-1",
        "kickoff_at": "2026-09-12T23:30:00+00:00",
    }


def decision(decision_id, market_id, created_at, edge=3.0):
    return {
        "decision_id": decision_id,
        "prediction_observation_id": "prediction-1",
        "market_observation_id": market_id,
        "canonical_game_id": "g1",
        "market_type": "spread",
        "checkpoint": "OPEN",
        "bet_side": "home",
        "edge": edge,
        "market_provenance": {
            "sportsbook": "Pinnacle",
            "source": "The Odds API",
            "freshness_status": "LIVE",
        },
        "created_at": created_at,
    }


def test_repeated_poll_collapses_confirmation_to_earliest_observation():
    a = market(
        "m1",
        observed_at="2026-09-09T12:00:00+00:00",
    )
    b = market(
        "m2",
        observed_at="2026-09-09T12:05:00+00:00",
    )

    rows = M.unique_market_confirmations([b, a])

    assert len(rows) == 1
    assert rows[0]["observed_at"] == "2026-09-09T12:00:00+00:00"


def test_a_b_a_has_two_states_and_three_confirmations():
    a1 = market(
        "m1",
        line=-7.0,
        observed_at="2026-09-09T12:00:00+00:00",
        source_updated_at="2026-09-09T11:59:00+00:00",
    )
    b = market(
        "m2",
        line=-7.5,
        observed_at="2026-09-09T12:20:00+00:00",
        source_updated_at="2026-09-09T12:19:00+00:00",
    )
    a2 = market(
        "m3",
        line=-7.0,
        observed_at="2026-09-09T12:40:00+00:00",
        source_updated_at="2026-09-09T12:39:00+00:00",
    )

    assert len(M.unique_market_states([a1, b, a2])) == 2
    assert len(M.unique_market_confirmations([a1, b, a2])) == 3


def test_duplicate_material_decisions_collapse_to_earliest():
    a = market("m1")
    b = market(
        "m2",
        observed_at="2026-09-09T12:05:00+00:00",
    )

    markets = {
        "m1": a,
        "m2": b,
    }

    d1 = decision(
        "d1",
        "m1",
        "2026-09-09T12:00:01+00:00",
    )
    d2 = decision(
        "d2",
        "m2",
        "2026-09-09T12:05:01+00:00",
    )

    rows, unresolved = M.unique_decision_states(
        [d2, d1],
        markets,
    )

    assert unresolved == 0
    assert len(rows) == 1
    assert rows[0]["first_observed_at"] == "2026-09-09T12:00:01+00:00"


def test_repeated_identical_decision_evidence_collapses_confirmation():
    a = market(
        "m1",
        observed_at="2026-09-09T12:00:00+00:00",
        source_updated_at="2026-09-09T11:59:00+00:00",
    )
    b = market(
        "m2",
        observed_at="2026-09-09T12:05:00+00:00",
        source_updated_at="2026-09-09T11:59:00+00:00",
    )

    markets = {"m1": a, "m2": b}

    d1 = decision(
        "d1",
        "m1",
        "2026-09-09T12:00:01+00:00",
    )
    d2 = decision(
        "d2",
        "m2",
        "2026-09-09T12:05:01+00:00",
    )

    rows, unresolved = M.unique_decision_confirmations(
        [d2, d1],
        markets,
    )

    assert unresolved == 0
    assert len(rows) == 1
    assert rows[0]["created_at"] == "2026-09-09T12:00:01+00:00"


def test_new_market_evidence_creates_decision_confirmation():
    a = market(
        "m1",
        source_updated_at="2026-09-09T11:59:00+00:00",
    )
    b = market(
        "m2",
        observed_at="2026-09-09T12:05:00+00:00",
        source_updated_at="2026-09-09T12:04:00+00:00",
    )

    markets = {"m1": a, "m2": b}

    d1 = decision(
        "d1",
        "m1",
        "2026-09-09T12:00:01+00:00",
    )
    d2 = decision(
        "d2",
        "m2",
        "2026-09-09T12:05:01+00:00",
    )

    rows, unresolved = M.unique_decision_confirmations(
        [d1, d2],
        markets,
    )

    assert unresolved == 0
    assert len(rows) == 2
