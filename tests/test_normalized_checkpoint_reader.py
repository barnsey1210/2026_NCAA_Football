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
