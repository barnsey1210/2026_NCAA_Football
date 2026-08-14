#!/usr/bin/env python3
"""Build the site-facing historical Shadow performance contract.

This is an adapter over frozen research artifacts. It does not fit models,
acquire market data, or alter any public page.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCOPES = ("2024", "2025", "POOLED_COMPARABLE")
SPREAD_THRESHOLDS = ("ALL", "2+", "2.5+", "3+", "3.5+", "4+", "5+")
TOTAL_THRESHOLDS = ("ALL", "1+", "1.5+", "2+", "2.5+", "3+", "3.5+", "4+", "5+")
EXPECTED_N = {
    "spread": {"2024": 163, "2025": 307, "POOLED_COMPARABLE": 470},
    "totals": {"2024": 163, "2025": 299, "POOLED_COMPARABLE": 462},
}

SOURCE_PATHS = {
    "spread_thresholds": "data/research/historical/shadow/all_games_baseline/shadow_historical_threshold_matrix.csv",
    "spread_quality": "data/research/historical/shadow/all_games_baseline/shadow_all_games_stale_vs_shadow.csv",
    "spread_audit": "data/research/historical/shadow/all_games_baseline/shadow_all_games_audit.json",
    "checkpoint_audit": "data/research/historical/shadow/checkpoint_comparison/shadow_checkpoint_comparison_audit.json",
    "candidate_specification": "data/research/historical/shadow/2026_candidate/provisional_2026_spread_shadow_specification.json",
    "candidate_summary": "data/research/historical/shadow/2026_candidate/provisional_2026_shadow_research_summary.md",
    "totals_thresholds": "data/research/historical/shadow/totals_all_games_baseline/shadow_totals_threshold_matrix.csv",
    "totals_quality": "data/research/historical/shadow/totals_all_games_baseline/shadow_totals_all_games_stale_vs_shadow.csv",
    "totals_audit": "data/research/historical/shadow/totals_all_games_baseline/shadow_totals_all_games_audit.json",
}

SPREAD_LABELS = {
    "ALL": "MODEL", "2+": "WATCH", "2.5+": "LEAN", "3+": "SIGNAL",
    "3.5+": "SIGNAL", "4+": "ACTIONABLE", "5+": "SMALLER N / STRONG CLV",
}
TOTAL_LABELS = {
    "ALL": "MODEL", "1+": "RESEARCH", "1.5+": "RESEARCH", "2+": "WATCH",
    "2.5+": "WATCH", "3+": "RESEARCH", "3.5+": "RESEARCH",
    "4+": "RESEARCH", "5+": "RESEARCH",
}


def fail(message: str) -> None:
    raise SystemExit(f"Shadow performance contract validation failed: {message}")


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        fail(f"missing research source: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing research source: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def number(row: dict[str, str], key: str) -> float:
    try:
        value = float(row[key])
    except (KeyError, TypeError, ValueError):
        fail(f"invalid numeric field {key!r} in row {row}")
    if not math.isfinite(value):
        fail(f"non-finite metric {key!r} in row {row}")
    return value


def integer(row: dict[str, str], key: str) -> int:
    value = number(row, key)
    if not value.is_integer():
        fail(f"expected integer {key!r}, got {value}")
    return int(value)


def record_parts(value: str) -> dict[str, Any]:
    try:
        wins, losses, pushes = (int(piece) for piece in value.split("-"))
    except (AttributeError, TypeError, ValueError):
        fail(f"invalid record: {value!r}")
    return {"display": value, "wins": wins, "losses": losses, "pushes": pushes}


def metric_row(row: dict[str, str], market: str) -> dict[str, Any]:
    record_key = "ats_record" if market == "spread" else "ou_record"
    win_key = "ats_pct" if market == "spread" else "win_pct"
    return {
        "threshold": row["cumulative_threshold"],
        "sample_size": integer(row, "n"),
        "record": record_parts(row[record_key]),
        "win_pct": number(row, win_key),
        "roi_minus_110": number(row, "roi_minus_110"),
        "average_clv_points": number(row, "average_clv"),
        "median_clv_points": number(row, "median_clv"),
        "positive_clv_pct": number(row, "positive_clv_pct"),
    }


def threshold_sections(rows: list[dict[str, str]], market: str) -> dict[str, Any]:
    required = SPREAD_THRESHOLDS if market == "spread" else TOTAL_THRESHOLDS
    expected_n = EXPECTED_N[market]
    selected = [row for row in rows if row.get("checkpoint") == "9AM" and row.get("scope") in SCOPES]
    keys = [(row["scope"], row["cumulative_threshold"]) for row in selected]
    if len(keys) != len(set(keys)):
        fail(f"duplicate {market} scope/threshold rows")
    expected = {(scope, threshold) for scope in SCOPES for threshold in required}
    if set(keys) != expected:
        fail(f"{market} threshold coverage mismatch: expected {sorted(expected)}, got {sorted(keys)}")

    output: dict[str, Any] = {}
    for scope in SCOPES:
        scope_rows = {row["cumulative_threshold"]: row for row in selected if row["scope"] == scope}
        if integer(scope_rows["ALL"], "n") != expected_n[scope]:
            fail(f"{market} {scope} ALL N does not equal {expected_n[scope]}")
        output["pooled" if scope == "POOLED_COMPARABLE" else scope] = {
            "scope": "2024-2025" if scope == "POOLED_COMPARABLE" else scope,
            "checkpoint": "SUN_9AM_ET",
            "thresholds": [metric_row(scope_rows[threshold], market) for threshold in required],
        }
    return output


def quality_model(row: dict[str, str], market: str) -> dict[str, Any]:
    record_key = "ats_record" if market == "spread" else "ou_record"
    result_mae_key = "actual_margin_mae" if market == "spread" else "actual_total_mae"
    win_key = "ats_pct" if market == "spread" else "win_pct"
    return {
        "sample_size": integer(row, "n"),
        "close_mae": number(row, "close_mae"),
        "actual_result_mae": number(row, result_mae_key),
        "record": record_parts(row[record_key]),
        "win_pct": number(row, win_key),
        "roi_minus_110": number(row, "roi_minus_110"),
        "average_clv_points": number(row, "average_clv"),
        "positive_clv_pct": number(row, "positive_clv_pct"),
    }


def quality_sections(rows: list[dict[str, str]], market: str) -> dict[str, Any]:
    model_names = ("stale_sp_sag", "shadow_sp_sag") if market == "spread" else ("stale_spplus_total", "shadow_spplus_total")
    selected = [row for row in rows if row.get("checkpoint") == "9AM" and row.get("scope") in SCOPES]
    keys = [(row["scope"], row["model"]) for row in selected]
    expected = {(scope, model) for scope in SCOPES for model in model_names}
    if len(keys) != len(set(keys)) or set(keys) != expected:
        fail(f"{market} stale-vs-Shadow row coverage mismatch")

    output: dict[str, Any] = {}
    for scope in SCOPES:
        indexed = {row["model"]: row for row in selected if row["scope"] == scope}
        stale, shadow = indexed[model_names[0]], indexed[model_names[1]]
        expected_n = EXPECTED_N[market][scope]
        if integer(stale, "n") != expected_n or integer(shadow, "n") != expected_n:
            fail(f"{market} {scope} quality N does not equal {expected_n}")
        output["pooled" if scope == "POOLED_COMPARABLE" else scope] = {
            "scope": "2024-2025" if scope == "POOLED_COMPARABLE" else scope,
            "checkpoint": "SUN_9AM_ET",
            "stale": quality_model(stale, market),
            "shadow": quality_model(shadow, market),
            "shadow_closer_to_close_pct": number(shadow, "shadow_closer_to_close_pct"),
            "shadow_farther_from_close_pct": number(shadow, "shadow_farther_from_close_pct"),
            "shadow_approximately_unchanged_pct": number(shadow, "shadow_approximately_unchanged_pct"),
            "close_mae_improvement_points": number(stale, "close_mae") - number(shadow, "close_mae"),
            "actual_result_mae_improvement_points": number(stale, "actual_margin_mae" if market == "spread" else "actual_total_mae") - number(shadow, "actual_margin_mae" if market == "spread" else "actual_total_mae"),
        }
    return output


def validate_audits(spread_audit: dict[str, Any], totals_audit: dict[str, Any], checkpoint_audit: dict[str, Any]) -> None:
    if spread_audit.get("eligible_forecasts_2024_exact_state") != 252 or spread_audit.get("eligible_forecasts_2025_comparable") != 394:
        fail("spread season eligibility audit changed")
    if totals_audit.get("eligible_2024_games") != 252 or totals_audit.get("eligible_2025_games") != 394:
        fail("totals season eligibility audit changed")
    forbidden = {
        "spread api calls": spread_audit.get("api_calls"),
        "spread refits": spread_audit.get("model_refits"),
        "totals api calls": totals_audit.get("api_calls"),
        "totals refits": totals_audit.get("models_refit"),
        "totals next-week market inputs": totals_audit.get("next_week_market_model_inputs"),
        "checkpoint api calls": checkpoint_audit.get("api_calls"),
        "checkpoint network requests": checkpoint_audit.get("network_requests"),
        "checkpoint spread refits": checkpoint_audit.get("models_refit_for_spread_analysis"),
        "checkpoint next-week market inputs": checkpoint_audit.get("next_week_market_features_in_provider_update_models"),
    }
    nonzero = {key: value for key, value in forbidden.items() if value != 0}
    if nonzero:
        fail(f"frozen/no-network audit invariant changed: {nonzero}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build site-facing Shadow model performance data.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--built-at", help="Optional ISO-8601 build timestamp for deterministic releases.")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    paths = {name: root / relative for name, relative in SOURCE_PATHS.items()}
    for name, path in paths.items():
        if not path.is_file():
            fail(f"missing {name}: {path}")

    spread_thresholds = threshold_sections(load_csv(paths["spread_thresholds"]), "spread")
    totals_thresholds = threshold_sections(load_csv(paths["totals_thresholds"]), "totals")
    spread_quality = quality_sections(load_csv(paths["spread_quality"]), "spread")
    totals_quality = quality_sections(load_csv(paths["totals_quality"]), "totals")
    spread_audit = load_json(paths["spread_audit"])
    totals_audit = load_json(paths["totals_audit"])
    checkpoint_audit = load_json(paths["checkpoint_audit"])
    candidate = load_json(paths["candidate_specification"])
    validate_audits(spread_audit, totals_audit, checkpoint_audit)

    core_inputs = candidate.get("model_specification", {}).get("core_stale_inputs")
    if core_inputs != ["SP+", "Sagarin"]:
        fail(f"candidate core inputs changed: {core_inputs}")
    weighting_status = "PROVISIONAL / TO_BE_PROSPECTIVELY_CALIBRATED"
    built_at = args.built_at or datetime.now(timezone.utc).isoformat()

    payload = {
        "schema_version": "shadow-model-performance-v1",
        "metadata": {
            "sport": "NCAAF",
            "built_at": built_at,
            "status": "HISTORICAL_VALIDATION_WITH_PROVISIONAL_2026_METHODOLOGY",
            "primary_checkpoint": "SUN_9AM_ET",
            "primary_seasons": [2024, 2025],
            "checkpoint_note": "The market checkpoint is sampled and is not necessarily the true opener.",
            "policy_note": "Display labels summarize historical evidence and are not automatic betting rules.",
            "provenance": [{"role": name, "path": relative} for name, relative in SOURCE_PATHS.items()],
        },
        "spread": {
            "methodology": {
                "historical_engine": ["SP+", "Sagarin"],
                "provider_update_forecasts": "FROZEN",
                "description": "Predicts forthcoming provider ratings before official updates.",
                "market_checkpoint": "SUN_9AM_ET",
            },
            "pooled": spread_thresholds["pooled"],
            "2024": spread_thresholds["2024"],
            "2025": spread_thresholds["2025"],
            "stale_vs_shadow": spread_quality,
        },
        "totals": {
            "methodology": {
                "engine": "SP+ offense/defense Shadow",
                "provider_update_forecasts": "FROZEN_ENHANCED",
                "features": ["prior-game closing spread", "prior-game closing total", "actual score", "implied scoring surprise", "PBP/efficiency"],
                "market_checkpoint": "SUN_9AM_ET",
                "status": "WATCH / RESEARCH",
            },
            "research_finding": {
                "descriptive_strongest_region_points": "2.0-2.99",
                "edge_response": "NON_MONOTONIC",
                "automatic_betting_rule": "NONE_FROZEN",
            },
            "pooled": totals_thresholds["pooled"],
            "2024": totals_thresholds["2024"],
            "2025": totals_thresholds["2025"],
            "stale_vs_shadow": totals_quality,
        },
        "live_methodology": {
            "state_definitions": {
                "STALE": "Latest officially available provider rating before update.",
                "SHADOW": "Predicted forthcoming provider rating.",
                "HYBRID": "Actual newly updated provider values plus Shadow values for providers not yet updated.",
                "FULL_UPDATED": "All desired current provider ratings released.",
            },
            "provider_selection_rule": "Use ACTUAL_UPDATED when a verified current post-Saturday provider update exists; otherwise use SHADOW_PREDICTED.",
            "core_historical_spread_providers": ["SP+", "Sagarin"],
            "supplemental_prospective_providers": ["FPI", "TeamRankings"],
            "supplemental_providers_gate_output": False,
            "potential_later_provider": ["DRatings"],
            "ensemble_weighting_status": weighting_status,
            "betting_policy_status": candidate.get("betting_policy_status"),
        },
        "status_labels": {
            "disclaimer": "Presentation metadata only; labels are not automatic betting rules.",
            "spread": SPREAD_LABELS,
            "totals": TOTAL_LABELS,
        },
    }

    output = root / "data/site/shadow_model_performance.json"
    audit_output = root / "data/audits/shadow_model_performance_contract_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    audit_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    audit = {
        "status": "PASS",
        "schema_version": payload["schema_version"],
        "output": "data/site/shadow_model_performance.json",
        "source_paths": list(SOURCE_PATHS.values()),
        "primary_checkpoint": "SUN_9AM_ET",
        "spread_primary_n": EXPECTED_N["spread"],
        "totals_primary_n": EXPECTED_N["totals"],
        "spread_thresholds": list(SPREAD_THRESHOLDS),
        "totals_thresholds": list(TOTAL_THRESHOLDS),
        "duplicate_thresholds": 0,
        "non_finite_metrics": 0,
        "api_calls": 0,
        "network_requests": 0,
        "models_refit": 0,
        "html_changes": 0,
    }
    audit_output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Wrote {audit_output}")
    print("VALIDATION: PASS")


if __name__ == "__main__":
    main()
