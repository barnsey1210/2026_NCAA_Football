#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
OUT = ROOT / "data/research/shadow_close_calibration"
OUT.mkdir(parents=True, exist_ok=True)

SPREAD_PRED = ROOT / "data/research/postgame_pbp_market_rating_update_2021_2024/holdout_2025_predictions.csv"
TOTAL_PRED = ROOT / "data/research/postgame_total_market_update_baseline_aware_2021_2025/holdout_2025_predictions_baseline_aware.csv"

LAMBDAS = [round(x / 20, 2) for x in range(-10, 41)]  # -0.50 through 2.00

def safe_corr(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    a, b = a[mask], b[mask]
    if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])

def metrics(actual, pred):
    actual = np.asarray(actual, dtype=float)
    pred = np.asarray(pred, dtype=float)
    mask = np.isfinite(actual) & np.isfinite(pred)
    actual, pred = actual[mask], pred[mask]
    if len(actual) == 0:
        return {"n": 0}
    err = pred - actual
    return {
        "n": int(len(actual)),
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "direction_accuracy": float(np.mean(np.sign(pred) == np.sign(actual))),
        "correlation": safe_corr(actual, pred),
        "mean_prediction": float(np.mean(pred)),
        "mean_actual": float(np.mean(actual)),
    }

def lambda_grid(actual, delta):
    rows = []
    actual = pd.to_numeric(actual, errors="coerce")
    delta = pd.to_numeric(delta, errors="coerce")
    for lam in LAMBDAS:
        pred = lam * delta
        m = metrics(actual, pred)
        rows.append({"lambda": lam, **m})
    rows.sort(key=lambda r: (r.get("mae", math.inf), r.get("rmse", math.inf)))
    return rows

def identify_column(fields, candidates):
    lower = {c.lower(): c for c in fields}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None

def audit_historical_official_blends():
    required_identity = ["season", "week", "game_id", "home_team", "away_team"]
    spread_candidates = [
        "official_model_spread", "model_spread", "blended_spread",
        "projected_spread", "site_spread", "spread_projection",
    ]
    total_candidates = [
        "official_model_total", "model_total", "blended_total",
        "projected_total", "site_total", "total_projection",
    ]
    close_spread_candidates = [
        "closing_home_spread", "close_spread", "closing_spread",
        "market_close_spread",
    ]
    close_total_candidates = [
        "closing_total", "close_total", "market_close_total",
    ]

    found = []
    for path in ROOT.glob("data/**/*.csv"):
        try:
            with path.open(newline="", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                fields = next(reader, [])
        except Exception:
            continue
        fieldset = set(fields)
        identity_count = sum(x in fieldset for x in required_identity)
        official_spread = identify_column(fields, spread_candidates)
        official_total = identify_column(fields, total_candidates)
        close_spread = identify_column(fields, close_spread_candidates)
        close_total = identify_column(fields, close_total_candidates)
        if official_spread or official_total:
            found.append({
                "file": str(path.relative_to(ROOT)),
                "identity_columns_found": identity_count,
                "official_spread_column": official_spread,
                "official_total_column": official_total,
                "closing_spread_column": close_spread,
                "closing_total_column": close_total,
                "usable_for_spread_close_calibration": bool(
                    identity_count >= 3 and official_spread and close_spread
                ),
                "usable_for_total_close_calibration": bool(
                    identity_count >= 3 and official_total and close_total
                ),
            })
    return found

def spread_market_repricing():
    if not SPREAD_PRED.exists():
        return {"status": "missing", "file": str(SPREAD_PRED)}
    df = pd.read_csv(SPREAD_PRED, low_memory=False)
    target = "target_next_market_innovation"
    pred = "score_prediction"
    pbp = "score_pbp_prediction"

    result = {
        "status": "ok",
        "file": str(SPREAD_PRED.relative_to(ROOT)),
        "primary_target": target,
        "score_only": metrics(df[target], df[pred]),
        "score_plus_pbp": metrics(df[target], df[pbp]) if pbp in df else None,
        "score_only_lambda_grid": lambda_grid(df[target], df[pred]),
    }
    return result

def total_market_repricing():
    if not TOTAL_PRED.exists():
        return {"status": "missing", "file": str(TOTAL_PRED)}
    df = pd.read_csv(TOTAL_PRED, low_memory=False)
    target = "target_total_innovation"
    score = "score_only_prediction"
    pbp = "score_plus_pbp_prediction"

    segments = {}
    for state, z in df.groupby("prior_data_state"):
        segments[state] = {
            "score_only": metrics(z[target], z[score]),
            "score_plus_pbp": metrics(z[target], z[pbp]),
            "score_plus_pbp_lambda_grid": lambda_grid(z[target], z[pbp]),
        }

    return {
        "status": "ok",
        "file": str(TOTAL_PRED.relative_to(ROOT)),
        "primary_target": target,
        "segments": segments,
        "production_candidate_segment": "both_prior",
        "one_prior_policy": "baseline retained until a separately validated model beats zero-change baseline",
        "neither_prior_policy": "baseline retained pending target/linkage audit",
    }

def main():
    official_files = audit_historical_official_blends()
    usable_spread = [x for x in official_files if x["usable_for_spread_close_calibration"]]
    usable_total = [x for x in official_files if x["usable_for_total_close_calibration"]]

    summary = {
        "schema_version": "shadow-close-calibration-research-v1",
        "research_priority": {
            "primary": "predict the next closing spread and total and identify opener prices likely to beat that close",
            "secondary": "measure whether the same temporary adjustment improves next-game score prediction",
        },
        "definitions": {
            "raw_postgame_delta": "predicted next-game market innovation from the completed game",
            "expected_market_close": "market baseline plus calibrated raw postgame delta",
            "official_model": "existing SP+/FPI/TeamRankings/Powers blended game projection",
            "saturday_shadow_line": "official model plus a separately validated temporary adjustment",
        },
        "market_repricing_validation": {
            "spread": spread_market_repricing(),
            "total": total_market_repricing(),
        },
        "official_blend_history_audit": {
            "candidate_files": official_files,
            "usable_spread_files": usable_spread,
            "usable_total_files": usable_total,
            "status": (
                "ready"
                if usable_spread or usable_total
                else "historical official blend snapshots not found"
            ),
        },
        "next_experiment": {
            "when_official_history_exists": [
                "join each pregame official projection to the same game's closing line",
                "attach the prior completed game's raw postgame delta for each team",
                "test official + lambda*delta against the next closing line",
                "select lambda on 2024 validation and report untouched 2025 holdout",
                "repeat against actual margin/total only as a secondary scorecard",
            ],
            "lambda_grid": LAMBDAS,
            "adoption_rule": (
                "The primary Saturday adjustment is adopted only if it reduces "
                "next-closing-line MAE and improves calibration on the locked holdout."
            ),
        },
    }

    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    # Compact lambda tables for inspection.
    spread = summary["market_repricing_validation"]["spread"]
    if spread.get("status") == "ok":
        pd.DataFrame(spread["score_only_lambda_grid"]).to_csv(
            OUT / "spread_market_delta_lambda_grid.csv", index=False
        )

    total = summary["market_repricing_validation"]["total"]
    if total.get("status") == "ok":
        for state, data in total["segments"].items():
            pd.DataFrame(data["score_plus_pbp_lambda_grid"]).to_csv(
                OUT / f"total_{state}_lambda_grid.csv", index=False
            )

    pd.DataFrame(official_files).to_csv(
        OUT / "historical_official_blend_file_audit.csv", index=False
    )

    print(json.dumps(summary, indent=2, allow_nan=False))
    print("wrote:", OUT / "summary.json")
    print("wrote:", OUT / "spread_market_delta_lambda_grid.csv")
    print("wrote:", OUT / "historical_official_blend_file_audit.csv")

if __name__ == "__main__":
    main()
