import importlib.util
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/model_tracking/v2/recover_w0_w1_prediction_accuracy.py"
SPEC = importlib.util.spec_from_file_location("prediction_recovery", SCRIPT)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_model_set_includes_requested_accuracy_models():
    assert "standard_spread_4src_equal_v1" in M.MODEL_SPECS
    assert "standard_total_sp_massey_dratings_v1" in M.MODEL_SPECS
    assert "sagarin_spread" in M.MODEL_SPECS
    assert "total_sp50_massey50_v1" in M.MODEL_SPECS
    assert "shadow_total_enhanced_spplus_od_v1" in M.MODEL_SPECS


def test_standard_formula_authority_fails_closed():
    valid = {"formula_version": "v1", "formula_status": "PRODUCTION_VALIDATED",
             "weights": {"SP+": .25, "FPI": .25, "TeamRankings": .25, "DRatings": .25}}
    assert M.authority_rejection("standard_spread_4src_equal_v1", valid) is None
    assert M.authority_rejection("standard_spread_4src_equal_v1", {**valid, "weights": {"SP+": 1}}) == "formula_version_unproven"


def test_contract_timestamp_is_prediction_bound_not_component_timestamp():
    assert M.parse_dt("2026-09-01T02:13:57Z") == datetime(2026, 9, 1, 2, 13, 57, tzinfo=timezone.utc)
    source = SCRIPT.read_text()
    assert '"immutable_prediction_bound": observed_at' in source
    assert "evidence[\"built_at\"] >= kickoff" in source


def test_observation_identity_is_deterministic():
    evidence = {"built_at": M.parse_dt("2026-09-01T02:13:57Z"), "commit": "abc", "sha256": "def"}
    game = {"game_id": "g1", "week": 1, "away_team": "A", "home_team": "B"}
    result = {"start_date": "2026-09-03T00:00:00Z"}
    projection = {"formula_version": "v1", "component_values": {}, "weights": {}}
    one = M.prediction_row(game, result, "sp_plus_spread", "spread", projection, 3.5, evidence)
    two = M.prediction_row(game, result, "sp_plus_spread", "spread", projection, 3.5, evidence)
    assert one["observation_id"] == two["observation_id"]
