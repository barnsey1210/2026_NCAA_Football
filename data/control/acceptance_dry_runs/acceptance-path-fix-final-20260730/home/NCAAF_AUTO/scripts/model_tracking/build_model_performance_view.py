#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from model_tracking import CORE_SPREAD_MODELS, read_jsonl, atomic_json

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "data/model_tracking"
OUT = ROOT / "data/site/model_performance_view.json"


def metric_row(name, market, model_type, status="AVAILABLE"):
    return {"model": name, "market_type": market, "model_type": model_type, "status": status,
            "rank": None, "ranking_status": "UNRANKED — SMALL SAMPLE", "games": 0,
            "availability_pct": None, "record": "0-0-0", "win_pct": None, "roi": None,
            "average_point_clv": None, "positive_clv_pct": None, "mae": None, "bias": None,
            "rmse": None, "median_clv": None, "clv_ge_1_pct": None, "clv_ge_2_pct": None,
            "model_set_version": None}


def main():
    config = json.loads((STORE / "config.json").read_text())
    status_path = ROOT / "data/ratings/ratings_source_status.csv"
    statuses = {}
    if status_path.exists():
        for r in pd.read_csv(status_path).fillna("").to_dict("records"):
            statuses[r["source"]] = {"status": "AVAILABLE" if r.get("active_2026") is True else "STALE",
                                     "latest_source_timestamp": r.get("source_updated_at") or r.get("pulled_at") or r.get("snapshot_date"),
                                     "game_projections": False, "team_ratings": True,
                                     "spread_available": bool(r.get("active_2026")), "total_available": False}
    aliases = {"Sagarin": "Sagarin Predictor", "Massey": "Massey Power"}
    for display, source in aliases.items():
        if source in statuses: statuses[display] = dict(statuses[source])
    for model in CORE_SPREAD_MODELS:
        statuses.setdefault(model, {"status": "NOT YET RELEASED"})
    statuses["Production Total"] = {"status": "AVAILABLE", "game_projections": True,
                                      "spread_available": False, "total_available": True}
    statuses["Shadow Spread"] = {"status": "AVAILABLE_WHEN_TIMING_ELIGIBLE", "comparison_only": True}
    statuses["Shadow Total"] = {"status": "AVAILABLE_WHEN_TIMING_ELIGIBLE", "comparison_only": True}
    for model in set(config["approved_spread_models"] + config["approved_total_models"]):
        statuses.setdefault(model, {"status": "NOT YET RELEASED", "game_projections": False,
                                    "spread_available": False, "total_available": False})

    spread_names = list(config["approved_spread_models"]) + ["spread_core_v1", "spread_available_average_v1", "Shadow Spread", "Opening Market", "Closing Market"]
    total_names = list(config["approved_total_models"]) + ["Shadow Total", "Opening Market", "Closing Market"]
    spread = [metric_row(x, "spread", "consensus" if x.startswith("spread_") else "benchmark" if "Market" in x else "shadow" if x.startswith("Shadow") else "individual", statuses.get(x,{}).get("status","NOT YET RELEASED")) for x in spread_names]
    totals = [metric_row(x, "total", "benchmark" if "Market" in x else "shadow" if x.startswith("Shadow") else "individual", statuses.get(x,{}).get("status","NOT YET RELEASED")) for x in total_names]

    opportunities = read_jsonl(STORE / "model_opportunities.jsonl")
    predictions = read_jsonl(STORE / "model_predictions.jsonl")
    scores = read_jsonl(STORE / "model_prediction_scores.jsonl")
    view = {"schema_version": "model-performance-view-v1", "built_at": datetime.now(timezone.utc).isoformat(),
            "season": 2026, "status": "PRESEASON_PROSPECTIVE", "ranking_minimum": config["ranking_minimum_settled"],
            "summary": {"opportunities": len(opportunities), "predictions": len(predictions), "settled": len(scores),
                        "spread": {"opportunities": 0, "settled_selections": 0},
                        "totals": {"opportunities": 0, "settled_selections": 0}},
            "spread_matrix": spread, "total_matrix": totals, "opportunities": opportunities,
            "model_availability": statuses,
            "consensus_rules": {"spread_core_v1": config["spread_core_v1"],
                                "spread_available_average_v1": {"variable_model_set": True},
                                "total": {"minimum": config["total_consensus_minimum"], "single_model_is_consensus": False}},
            "periods": ["W0"] + [f"W{i}" for i in range(1,15)] + ["Conference Championships", "Bowl / Playoff", "All"]}
    atomic_json(OUT, view)
    print(f"Wrote {OUT} ({len(opportunities)} opportunities, {len(scores)} settled)")


if __name__ == "__main__": main()
