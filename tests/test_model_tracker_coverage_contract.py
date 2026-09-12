import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "model_performance_coverage",
    ROOT / "scripts/model_tracking/build_model_performance_view.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def score(game, *, result=1, clv=0.5, profit=0.909, error=2.0):
    return {
        "canonical_game_id": game,
        "result": result,
        "clv": clv,
        "profit": profit,
        "absolute_error": error,
        "signed_error": error,
        "squared_error": error * error,
    }


def checkpoints(n, checkpoint="SUNDAY_9PM_ET"):
    return [
        {
            "checkpoint_id": f"cp-{i}",
            "market_observation_id": f"m-{i}",
            "market_line": -3.5,
            "market_book": "Pinnacle",
            "market_source": "The Odds API",
            "checkpoint_at": "2026-09-06T21:00:00-04:00",
        }
        for i in range(n)
    ]


def test_w1_spread_population_and_metric_specific_denominators():
    rows = [score(f"g{i}", clv=None if i >= 31 else 0.5) for i in range(37)]
    metrics = MODULE.coverage_metrics(
        rows,
        checkpoint="SUNDAY_9PM_ET",
        schedule_n=91,
        projection_n=43,
        captured_rows=checkpoints(37),
        model_id="sp_plus_spread",
        market_type="spread",
        period="W1",
    )
    assert metrics["schedule_eligible_n"] == 91
    assert metrics["projection_eligible_n"] == 43
    assert metrics["captured_n"] == metrics["settled_n"] == 37
    assert metrics["ats_n"] == metrics["roi_n"] == metrics["mae_n"] == 37
    assert metrics["clv_n"] == 31
    assert metrics["omission_reasons"]["market_checkpoint_missing"] == 6


def test_close_clv_is_explicitly_unavailable():
    metrics = MODULE.coverage_metrics(
        [score("g1")], checkpoint="CLOSE", schedule_n=91,
        projection_n=43, captured_rows=checkpoints(1, "CLOSE"),
        model_id="fpi_spread", market_type="spread", period="W1",
    )
    assert metrics["clv_n"] is None
    assert metrics["average_point_clv"] is None
    assert metrics["provenance"]["market_timestamp_semantics"] == "EXACT_FROZEN_CLOSE"


def test_known_historical_absence_reasons_are_precise():
    standard = MODULE.coverage_metrics(
        [], checkpoint="SUNDAY_9PM_ET", schedule_n=91, projection_n=0,
        captured_rows=[], model_id="standard_spread_4src_equal_v1",
        market_type="spread", period="W1",
    )
    dratings = MODULE.coverage_metrics(
        [], checkpoint="CLOSE", schedule_n=91, projection_n=0,
        captured_rows=[], model_id="dratings_spread",
        market_type="spread", period="W1",
    )
    assert standard["omission_reasons"] == {"model_projection_not_historically_captured": 91}
    assert dratings["omission_reasons"]["model_projection_not_historically_captured"] == 91
    assert dratings["omission_reasons"]["close_capture_not_active"] == 91


def test_season_counts_use_underlying_rows_not_weekly_percentages():
    rows = [score("w1", result=1), score("w2", result=-1), score("w3", result=0)]
    metrics = MODULE.coverage_metrics(
        rows, checkpoint="TUESDAY_9PM_ET", schedule_n=268,
        projection_n=120, captured_rows=checkpoints(3),
        model_id="sp_plus_spread", market_type="spread", period="Season",
    )
    assert metrics["settled_n"] == 3
    assert metrics["ats_n"] == 2
    assert metrics["ats_or_ou_pct"] == 0.5
    assert metrics["roi_n"] == 3


def test_schema_covers_normalized_ledgers_and_missing_audit_is_truthful(tmp_path):
    schema = json.loads((ROOT / "data/model_tracking/v2/schema.json").read_text())
    for name in (
        "checkpoint_observations.jsonl", "market_states.jsonl",
        "market_confirmations.jsonl", "decision_states.jsonl",
        "decision_confirmations.jsonl", "prediction_scores.jsonl",
    ):
        assert name in schema["datasets"]
    old_store = MODULE.STORE
    try:
        MODULE.STORE = tmp_path
        audit = MODULE.ledger_audit(["scores.jsonl"])
    finally:
        MODULE.STORE = old_store
    assert audit["status"] == "UNAVAILABLE"
    assert audit["ledgers"]["scores.jsonl"]["rows"] is None


def test_prediction_and_final_without_market_scores_accuracy_only():
    accuracy = [score("g1")]
    metrics = MODULE.coverage_metrics(
        [], accuracy_rows=accuracy, checkpoint="SUNDAY_9PM_ET",
        schedule_n=1, projection_n=1, captured_rows=[],
        model_id="standard_spread_4src_equal_v1",
        market_type="spread", period="W2",
    )
    assert metrics["mae_n"] == metrics["rmse_n"] == metrics["bias_n"] == 1
    assert metrics["settled_prediction_n"] == 1
    assert metrics["market_n"] == metrics["ats_n"] == metrics["roi_n"] == 0
    assert metrics["clv_n"] == 0


def test_prediction_market_and_final_scores_accuracy_and_betting_without_clv():
    accuracy = [score("g1")]
    betting = [score("g1", clv=None)]
    metrics = MODULE.coverage_metrics(
        betting, accuracy_rows=accuracy, checkpoint="SUNDAY_9PM_ET",
        schedule_n=1, projection_n=1, captured_rows=checkpoints(1),
        model_id="standard_spread_4src_equal_v1",
        market_type="spread", period="W2",
    )
    assert metrics["mae_n"] == metrics["ats_n"] == metrics["roi_n"] == 1
    assert metrics["clv_n"] == 0


def test_prediction_market_close_and_final_scores_all_metric_families():
    accuracy = [score("g1")]
    betting = [score("g1", clv=0.5)]
    metrics = MODULE.coverage_metrics(
        betting, accuracy_rows=accuracy, checkpoint="SUNDAY_9PM_ET",
        schedule_n=1, projection_n=1, captured_rows=checkpoints(1),
        model_id="standard_spread_4src_equal_v1",
        market_type="spread", period="W2",
    )
    assert metrics["mae_n"] == metrics["ats_n"] == metrics["roi_n"] == 1
    assert metrics["clv_n"] == 1


def test_schedule_denominators_are_fbs_vs_fbs_only():
    source = (ROOT / "scripts/model_tracking/build_model_performance_view.py").read_text()
    assert "PRESEASON_DB" in source
    assert 'game.get("away_team") in fbs_teams' in source
    assert 'game.get("home_team") in fbs_teams' in source
    assert 'str(row.get("canonical_game_id")) in fbs_game_ids' in source
    assert 'str(row.get("prediction_observation_id")) in fbs_prediction_ids' in source
