from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts/model_tracking/v2"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

SPEC = importlib.util.spec_from_file_location(
    "market_identity_under_test",
    SCRIPT_DIR / "market_identity.py",
)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def market_row(
    *,
    line=-7.0,
    price=-110,
    observed_at="2026-09-09T12:00:00+00:00",
    source_updated_at="2026-09-09T11:59:00+00:00",
    source="The Odds API",
    freshness="LIVE",
    lifecycle="OPEN",
):
    return {
        "observation_id": "legacy-observation",
        "canonical_game_id": "g-test",
        "market_type": "spread",
        "sportsbook": "Pinnacle",
        "side": "home",
        "observed_at": observed_at,
        "source_updated_at": source_updated_at,
        "line": line,
        "price": price,
        "source": source,
        "freshness_status": freshness,
        "lifecycle_state": lifecycle,
        "kickoff_at": "2026-09-12T23:30:00+00:00",
        "contract_id": "contract-test",
    }


def test_timestamp_only_change_keeps_same_material_state():
    first = market_row(
        observed_at="2026-09-09T12:00:00+00:00",
        source_updated_at="2026-09-09T11:59:00+00:00",
    )
    second = market_row(
        observed_at="2026-09-09T12:02:00+00:00",
        source_updated_at="2026-09-09T12:01:00+00:00",
    )

    assert M.market_state_id(first) == M.market_state_id(second)
    assert (
        M.market_confirmation_id(first)
        != M.market_confirmation_id(second)
    )


def test_line_change_creates_new_material_state():
    first = market_row(line=-7.0)
    second = market_row(line=-7.5)

    assert M.market_state_id(first) != M.market_state_id(second)


def test_price_change_creates_new_material_state():
    first = market_row(price=-110)
    second = market_row(price=-105)

    assert M.market_state_id(first) != M.market_state_id(second)


def test_source_change_is_material():
    first = market_row(source="The Odds API")
    second = market_row(source="Action Network")

    assert M.market_state_id(first) != M.market_state_id(second)


def test_freshness_change_is_material():
    first = market_row(freshness="LIVE")
    second = market_row(freshness="STALE")

    assert M.market_state_id(first) != M.market_state_id(second)


def test_lifecycle_change_is_material():
    first = market_row(lifecycle="OPEN")
    second = market_row(lifecycle="CLOSED")

    assert M.market_state_id(first) != M.market_state_id(second)


def test_a_to_b_to_a_reuses_material_a_identity():
    a1 = market_row(
        line=-7.0,
        observed_at="2026-09-09T12:00:00+00:00",
        source_updated_at="2026-09-09T11:59:00+00:00",
    )
    b = market_row(
        line=-7.5,
        observed_at="2026-09-09T12:20:00+00:00",
        source_updated_at="2026-09-09T12:19:00+00:00",
    )
    a2 = market_row(
        line=-7.0,
        observed_at="2026-09-09T12:40:00+00:00",
        source_updated_at="2026-09-09T12:39:00+00:00",
    )

    assert M.market_state_id(a1) != M.market_state_id(b)
    assert M.market_state_id(a1) == M.market_state_id(a2)

    assert (
        M.market_confirmation_id(a1)
        != M.market_confirmation_id(a2)
    )


def test_decision_state_ignores_confirmation_timestamp():
    first = market_row(
        observed_at="2026-09-09T12:00:00+00:00",
        source_updated_at="2026-09-09T11:59:00+00:00",
    )
    second = market_row(
        observed_at="2026-09-09T12:02:00+00:00",
        source_updated_at="2026-09-09T12:01:00+00:00",
    )

    first_id = M.decision_state_id(
        "prediction-1",
        M.market_state_id(first),
        "home",
        3.0,
    )
    second_id = M.decision_state_id(
        "prediction-1",
        M.market_state_id(second),
        "home",
        3.0,
    )

    assert first_id == second_id


def test_decision_state_changes_when_market_state_changes():
    first = market_row(line=-7.0)
    second = market_row(line=-7.5)

    first_id = M.decision_state_id(
        "prediction-1",
        M.market_state_id(first),
        "home",
        3.0,
    )
    second_id = M.decision_state_id(
        "prediction-1",
        M.market_state_id(second),
        "home",
        3.5,
    )

    assert first_id != second_id


def test_repeated_capture_same_provider_evidence_is_same_confirmation():
    first = market_row(
        observed_at="2026-09-09T12:00:00+00:00",
        source_updated_at="2026-09-09T11:59:00+00:00",
    )
    second = market_row(
        observed_at="2026-09-09T12:02:00+00:00",
        source_updated_at="2026-09-09T11:59:00+00:00",
    )

    assert M.market_state_id(first) == M.market_state_id(second)
    assert (
        M.market_confirmation_id(first)
        == M.market_confirmation_id(second)
    )


def test_provider_timestamp_change_creates_confirmation_not_state():
    first = market_row(
        observed_at="2026-09-09T12:00:00+00:00",
        source_updated_at="2026-09-09T11:59:00+00:00",
    )
    second = market_row(
        observed_at="2026-09-09T12:02:00+00:00",
        source_updated_at="2026-09-09T12:01:00+00:00",
    )

    assert M.market_state_id(first) == M.market_state_id(second)
    assert (
        M.market_confirmation_id(first)
        != M.market_confirmation_id(second)
    )


def test_missing_source_timestamp_falls_back_to_observed_at():
    first = market_row(
        observed_at="2026-09-09T12:00:00+00:00",
        source_updated_at=None,
    )
    second = market_row(
        observed_at="2026-09-09T12:02:00+00:00",
        source_updated_at=None,
    )

    assert M.market_state_id(first) == M.market_state_id(second)
    assert (
        M.market_confirmation_id(first)
        != M.market_confirmation_id(second)
    )
