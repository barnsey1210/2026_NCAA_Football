#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from model_tracking import CORE_SPREAD_MODELS, atomic_json, read_jsonl

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "data/model_tracking"
OUT = ROOT / "data/site/model_performance_view.json"

DISPLAY_NAMES = {
    "spread_core_v1": "Core Spread Consensus",
    "spread_available_average_v1": "Available-Model Average",
    "totals_consensus_v1": "Total Consensus",
    "Production Total": "Site Total Projection",
}

CORE_DEFAULT_MODELS = {
    "spread": {
        "SP+", "FPI", "TeamRankings", "Brad Powers",
        "spread_core_v1", "spread_available_average_v1",
    },
    "total": {"Production Total", "totals_consensus_v1"},
}


def default_status():
    return {
        "status": "NOT_YET_RELEASED",
        "tracking_status": "NOT_ACTIVE_FOR_TRACKING",
        "game_projections": False,
        "team_ratings": False,
        "spread_available": False,
        "total_available": False,
    }


def metric_row(name, market, model_type, status_info):
    return {
        "model": name,
        "display_name": DISPLAY_NAMES.get(name, name),
        "market_type": market,
        "model_type": model_type,
        "status": status_info.get("status", "NOT_YET_RELEASED"),
        "tracking_status": status_info.get("tracking_status", "NOT_ACTIVE_FOR_TRACKING"),
        "latest_source_timestamp": status_info.get("latest_source_timestamp"),
        "default_visible": name in CORE_DEFAULT_MODELS[market],
        "rank": None,
        "ranking_status": "UNRANKED — SMALL SAMPLE",
        "games": 0,
        "availability_pct": None,
        "record": "0-0-0",
        "win_pct": None,
        "roi": None,
        "average_point_clv": None,
        "positive_clv_pct": None,
        "mae": None,
        "bias": None,
        "rmse": None,
        "median_clv": None,
        "clv_ge_1_pct": None,
        "clv_ge_2_pct": None,
        "model_set_version": name if name.endswith("_v1") else None,
    }


def source_statuses(config):
    status_path = ROOT / "data/ratings/ratings_source_status.csv"
    statuses = {}

    if status_path.exists():
        for row in pd.read_csv(status_path).fillna("").to_dict("records"):
            source = row.get("source")
            if not source:
                continue
            active = bool(row.get("active_2026") is True or str(row.get("active_2026")).lower() == "true")
            statuses[source] = {
                "status": "AVAILABLE" if active else "STALE",
                "tracking_status": "TEAM_RATINGS_AVAILABLE" if active else "STALE_SOURCE",
                "latest_source_timestamp": row.get("source_updated_at") or row.get("pulled_at") or row.get("snapshot_date"),
                "game_projections": False,
                "team_ratings": True,
                "spread_available": active,
                "total_available": False,
            }

    aliases = {
        "Sagarin": "Sagarin Predictor",
        "Massey": "Massey Power",
        "Donchess": "Donchess Overall",
    }
    for display, source in aliases.items():
        if source in statuses:
            statuses[display] = dict(statuses[source])

    # The four active source ratings are approved for individual spread tracking.
    for model in CORE_SPREAD_MODELS:
        info = statuses.setdefault(model, default_status())
        if info.get("status") == "AVAILABLE":
            info["tracking_status"] = "ACTIVE_FOR_SPREAD_TRACKING"
            info["spread_available"] = True

    statuses["Production Total"] = {
        "status": "AVAILABLE",
        "tracking_status": "ACTIVE_INDIVIDUAL_TOTAL_ONLY",
        "game_projections": True,
        "team_ratings": False,
        "spread_available": False,
        "total_available": True,
    }
    statuses["spread_core_v1"] = {
        "status": "AVAILABLE",
        "tracking_status": "ACTIVE_WHEN_ALL_FOUR_AVAILABLE",
        "game_projections": True,
        "team_ratings": False,
        "spread_available": True,
        "total_available": False,
    }
    statuses["spread_available_average_v1"] = {
        "status": "AVAILABLE",
        "tracking_status": "VARIABLE_MODEL_SET_COMPARISON",
        "game_projections": True,
        "team_ratings": False,
        "spread_available": True,
        "total_available": False,
    }
    statuses["totals_consensus_v1"] = {
        "status": "NOT_ENOUGH_APPROVED_SOURCES",
        "tracking_status": "REQUIRES_THREE_INDEPENDENT_TOTALS",
        "game_projections": False,
        "team_ratings": False,
        "spread_available": False,
        "total_available": False,
    }
    statuses["Shadow Spread"] = {
        "status": "COMPARISON_ONLY",
        "tracking_status": "EXCLUDED_FROM_CONSENSUS",
        "comparison_only": True,
    }
    statuses["Shadow Total"] = {
        "status": "COMPARISON_ONLY",
        "tracking_status": "EXCLUDED_FROM_CONSENSUS",
        "comparison_only": True,
    }
    statuses["Opening Market"] = {
        "status": "BENCHMARK",
        "tracking_status": "MARKET_BENCHMARK",
    }
    statuses["Closing Market"] = {
        "status": "BENCHMARK",
        "tracking_status": "MARKET_BENCHMARK",
    }

    for model in set(config["approved_spread_models"] + config["approved_total_models"]):
        statuses.setdefault(model, default_status())

    return statuses


def model_type(name):
    if name.startswith("spread_") or name.startswith("totals_"):
        return "consensus"
    if "Market" in name:
        return "benchmark"
    if name.startswith("Shadow"):
        return "shadow"
    return "individual"


def main():
    config = json.loads((STORE / "config.json").read_text())
    statuses = source_statuses(config)

    spread_names = (
        list(config["approved_spread_models"])
        + ["spread_core_v1", "spread_available_average_v1", "Shadow Spread", "Opening Market", "Closing Market"]
    )
    total_names = (
        list(config["approved_total_models"])
        + ["totals_consensus_v1", "Shadow Total", "Opening Market", "Closing Market"]
    )

    spread = [metric_row(name, "spread", model_type(name), statuses.get(name, default_status())) for name in spread_names]
    totals = [metric_row(name, "total", model_type(name), statuses.get(name, default_status())) for name in total_names]

    opportunities = read_jsonl(STORE / "model_opportunities.jsonl")
    predictions = read_jsonl(STORE / "model_predictions.jsonl")
    scores = read_jsonl(STORE / "model_prediction_scores.jsonl")

    spread_opps = [x for x in opportunities if x.get("market_type") == "spread"]
    total_opps = [x for x in opportunities if x.get("market_type") == "total"]
    spread_scores = [x for x in scores if x.get("market_type") == "spread"]
    total_scores = [x for x in scores if x.get("market_type") == "total"]

    tracking_started = bool(opportunities or predictions or scores)

    view = {
        "schema_version": "model-performance-view-v2",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "season": 2026,
        "status": "ACTIVE_PROSPECTIVE" if tracking_started else "PRESEASON_NOT_STARTED",
        "tracking_started": tracking_started,
        "ranking_minimum": config["ranking_minimum_settled"],
        "summary": {
            "opportunities": len(opportunities),
            "predictions": len(predictions),
            "settled": len(scores),
            "spread": {"opportunities": len(spread_opps), "settled_selections": len(spread_scores)},
            "totals": {"opportunities": len(total_opps), "settled_selections": len(total_scores)},
        },
        "spread_matrix": spread,
        "total_matrix": totals,
        "opportunities": opportunities,
        "predictions": predictions,
        "model_availability": statuses,
        "methodology": {
            "spread_projection_formula": "home rating - away rating + HFA",
            "hfa": {"non_neutral": 2.6, "neutral": 0.0, "method": "validated_fixed_hfa"},
            "spread_core_v1": config["spread_core_v1"],
            "spread_available_average_v1": {
                "variable_model_set": True,
                "comparison_only": True,
            },
            "total": {
                "minimum_independent_sources": config["total_consensus_minimum"],
                "single_model_is_consensus": False,
                "shadow_total_excluded": True,
            },
        },
        "consensus_rules": {
            "spread_core_v1": config["spread_core_v1"],
            "spread_available_average_v1": {"variable_model_set": True},
            "total": {
                "minimum": config["total_consensus_minimum"],
                "single_model_is_consensus": False,
            },
        },
        "periods": ["W0"] + [f"W{i}" for i in range(1, 15)] + ["Conference Championships", "Bowl / Playoff", "All"],
    }

    atomic_json(OUT, view)
    print(f"Wrote {OUT} ({len(opportunities)} opportunities, {len(scores)} settled)")


if __name__ == "__main__":
    main()
