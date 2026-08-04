#!/usr/bin/env python3
"""Validate simple PBP margin/total models without reading the locked 2025 split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


FEATURES = [
    f"{side}_matchup_expected_off_{metric}"
    for side in ("home", "away")
    for metric in ("neutral_pass", "success", "explosiveness", "ppa", "pace_seconds")
] + [
    "home_matchup_expected_def_havoc", "away_matchup_expected_def_havoc",
]
ALPHAS = [0.1, 1.0, 10.0, 100.0, 1000.0]


class Ridge:
    def __init__(self, alpha: float):
        self.alpha = alpha

    def fit(self, frame: pd.DataFrame, target: pd.Series) -> "Ridge":
        self.medians = frame.median(numeric_only=True)
        x = frame.fillna(self.medians).to_numpy(dtype=float)
        self.mean = x.mean(axis=0)
        self.scale = x.std(axis=0)
        self.scale[self.scale == 0] = 1.0
        z = (x - self.mean) / self.scale
        y = target.to_numpy(dtype=float)
        self.intercept = float(y.mean())
        centered = y - self.intercept
        self.coef = np.linalg.solve(z.T @ z + self.alpha * np.eye(z.shape[1]), z.T @ centered)
        return self

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        x = frame.fillna(self.medians).to_numpy(dtype=float)
        return self.intercept + ((x - self.mean) / self.scale) @ self.coef


def metrics(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    error = actual - predicted
    return {
        "n": int(len(actual)),
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error ** 2))),
        "bias_actual_minus_prediction": float(np.mean(error)),
    }


def choose_alpha(data: pd.DataFrame, target_col: str) -> Tuple[float, Dict[str, float]]:
    scores: Dict[str, float] = {}
    for alpha in ALPHAS:
        fold_mae: List[float] = []
        for season in sorted(data["season"].unique()):
            train = data[~data["season"].eq(season)]
            test = data[data["season"].eq(season)]
            model = Ridge(alpha).fit(train[FEATURES], train[target_col])
            prediction = model.predict(test[FEATURES])
            fold_mae.append(float(np.mean(np.abs(test[target_col].to_numpy() - prediction))))
        scores[str(alpha)] = float(np.mean(fold_mae))
    best = min(ALPHAS, key=lambda value: scores[str(value)])
    return best, scores


def fit_validate(
    development: pd.DataFrame,
    validation: pd.DataFrame,
    target_col: str,
    market_prediction_col: str,
    residual_target_col: str,
) -> Dict[str, object]:
    football_alpha, football_cv = choose_alpha(development, target_col)
    residual_alpha, residual_cv = choose_alpha(development, residual_target_col)
    football = Ridge(football_alpha).fit(development[FEATURES], development[target_col])
    residual = Ridge(residual_alpha).fit(development[FEATURES], development[residual_target_col])
    actual = validation[target_col].to_numpy(dtype=float)
    market_prediction = validation[market_prediction_col].to_numpy(dtype=float)
    football_prediction = football.predict(validation[FEATURES])
    residual_prediction = market_prediction + residual.predict(validation[FEATURES])
    result: Dict[str, object] = {
        "football_alpha": football_alpha,
        "residual_alpha": residual_alpha,
        "football_cv_mae_by_alpha": football_cv,
        "residual_cv_mae_by_alpha": residual_cv,
        "validation_market_baseline": metrics(actual, market_prediction),
        "validation_football_model": metrics(actual, football_prediction),
        "validation_market_plus_pbp_residual": metrics(actual, residual_prediction),
    }
    market_error = actual - market_prediction
    predicted_error = residual_prediction - market_prediction
    result["validation_residual_correlation"] = float(np.corrcoef(market_error, predicted_error)[0, 1])
    result["validation_model_edge_mean_abs"] = float(np.mean(np.abs(predicted_error)))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path,
        default=Path("data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/research/pbp_market_modeling_2021_2025/validation_2024.json"),
    )
    args = parser.parse_args()
    usecols = [
        "season", "split", "eligible_week5_plus", "actual_home_margin", "actual_total_points",
        "closing_home_spread", "closing_total", "closing_spread_residual", "closing_total_residual",
        *FEATURES,
    ]
    # usecols prevents locked-test identifiers and rows from entering model logic beyond split filtering.
    data = pd.read_csv(args.input, usecols=usecols, low_memory=False)
    data = data[data["eligible_week5_plus"].astype(str).str.lower().eq("true")].copy()
    development = data[data["split"].eq("development")].copy()
    validation = data[data["split"].eq("validation")].copy()
    del data
    development["market_margin_prediction"] = -development["closing_home_spread"]
    validation["market_margin_prediction"] = -validation["closing_home_spread"]
    development["market_total_prediction"] = development["closing_total"]
    validation["market_total_prediction"] = validation["closing_total"]
    result = {
        "protocol": {
            "development": "2021-2023, Week 5+ only",
            "validation": "2024, Week 5+ only",
            "locked_test": "2025 not evaluated or reported",
            "features": FEATURES,
        },
        "development_rows": len(development),
        "validation_rows": len(validation),
        "margin": fit_validate(
            development, validation, "actual_home_margin", "market_margin_prediction", "closing_spread_residual"
        ),
        "total": fit_validate(
            development, validation, "actual_total_points", "market_total_prediction", "closing_total_residual"
        ),
    }
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
