#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
OUT = ROOT / "data/research/full_saturday_shadow_backtest"
OUT.mkdir(parents=True, exist_ok=True)

GAMES = ROOT / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"
SPREAD_BASE = ROOT / "data/research/market_implied_ratings/holdout_2025_predictions.csv"
SPREAD_DELTA = ROOT / "data/research/postgame_pbp_market_rating_update_2021_2024/holdout_2025_predictions.csv"
TOTAL_MODEL_SCRIPT = ROOT / "scripts/research/analyze_postgame_total_market_update.py"
TOTAL_DELTA = ROOT / "data/research/postgame_total_market_update_baseline_aware_2021_2025/holdout_2025_predictions_baseline_aware.csv"

LAMBDAS = [round(x / 20, 2) for x in range(-10, 41)]  # -0.50 to 2.00

def norm_id(v):
    s = str(v or "").strip()
    return s[:-2] if s.endswith(".0") else s

def safe_corr(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    a, b = a[mask], b[mask]
    if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])

def metrics(actual, pred):
    actual = pd.to_numeric(actual, errors="coerce")
    pred = pd.to_numeric(pred, errors="coerce")
    mask = actual.notna() & pred.notna()
    actual, pred = actual[mask], pred[mask]
    if len(actual) == 0:
        return {"n": 0}
    err = pred - actual
    return {
        "n": int(len(actual)),
        "mae": float(err.abs().mean()),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "direction_accuracy": float(
            np.mean(np.sign(pred) == np.sign(actual))
        ),
        "correlation": safe_corr(actual, pred),
        "mean_error": float(err.mean()),
    }

def build_prev_game_map(games):
    team_rows = []
    for r in games.itertuples(index=False):
        team_rows.extend([
            {
                "season": int(r.season),
                "week": int(r.week),
                "game_id": norm_id(r.game_id),
                "team": r.home_team,
            },
            {
                "season": int(r.season),
                "week": int(r.week),
                "game_id": norm_id(r.game_id),
                "team": r.away_team,
            },
        ])
    team = pd.DataFrame(team_rows).sort_values(
        ["season", "team", "week", "game_id"]
    )
    team["next_game_id"] = team.groupby(
        ["season", "team"]
    ).game_id.shift(-1)
    team["next_week"] = team.groupby(
        ["season", "team"]
    ).week.shift(-1)
    team = team[
        team.next_game_id.notna()
        & ((team.next_week - team.week) >= 1)
        & ((team.next_week - team.week) <= 3)
    ].copy()
    return team

def spread_backtest(games):
    base = pd.read_csv(SPREAD_BASE, low_memory=False)
    delta = pd.read_csv(SPREAD_DELTA, low_memory=False)

    for c in ("game_id",):
        base[c] = base[c].map(norm_id)
        delta[c] = delta[c].map(norm_id)

    prev = build_prev_game_map(games[games.season == 2025].copy())

    home_prev = prev.rename(columns={
        "team": "home_team",
        "game_id": "home_prev_game_id",
        "next_game_id": "game_id",
    })[
        ["season", "game_id", "home_team", "home_prev_game_id"]
    ]
    away_prev = prev.rename(columns={
        "team": "away_team",
        "game_id": "away_prev_game_id",
        "next_game_id": "game_id",
    })[
        ["season", "game_id", "away_team", "away_prev_game_id"]
    ]

    base = base.merge(
        home_prev,
        on=["season", "game_id", "home_team"],
        how="left",
    ).merge(
        away_prev,
        on=["season", "game_id", "away_team"],
        how="left",
    )

    delta_keep = delta[
        ["game_id", "team", "score_prediction", "score_pbp_prediction"]
    ].copy()

    home_delta = delta_keep.rename(columns={
        "game_id": "home_prev_game_id",
        "team": "home_team",
        "score_prediction": "home_spread_delta",
        "score_pbp_prediction": "home_spread_delta_pbp",
    })
    away_delta = delta_keep.rename(columns={
        "game_id": "away_prev_game_id",
        "team": "away_team",
        "score_prediction": "away_spread_delta",
        "score_pbp_prediction": "away_spread_delta_pbp",
    })

    base = base.merge(
        home_delta,
        on=["home_prev_game_id", "home_team"],
        how="left",
    ).merge(
        away_delta,
        on=["away_prev_game_id", "away_team"],
        how="left",
    )

    for col in ("home_spread_delta", "away_spread_delta"):
        base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0.0)

    # Delta is team-perspective market innovation. Convert to home-spread convention:
    # stronger home adjustment makes home spread more negative; stronger away adjustment makes it less negative.
    base["raw_matchup_shadow_adjustment"] = (
        -base.home_spread_delta + base.away_spread_delta
    )

    grid = []
    for lam in LAMBDAS:
        pred = (
            base.predicted_home_spread
            + lam * base.raw_matchup_shadow_adjustment
        )
        m = metrics(base.actual_closing_home_spread, pred)
        grid.append({"lambda": lam, **m})
    grid = pd.DataFrame(grid).sort_values(["mae", "rmse"])
    best = grid.iloc[0].to_dict()

    base["shadow_home_spread_best"] = (
        base.predicted_home_spread
        + float(best["lambda"]) * base.raw_matchup_shadow_adjustment
    )
    base["baseline_abs_error"] = (
        base.predicted_home_spread - base.actual_closing_home_spread
    ).abs()
    base["shadow_abs_error"] = (
        base.shadow_home_spread_best - base.actual_closing_home_spread
    ).abs()
    base["shadow_improved"] = (
        base.shadow_abs_error < base.baseline_abs_error
    )

    return {
        "baseline": metrics(
            base.actual_closing_home_spread,
            base.predicted_home_spread,
        ),
        "best_lambda": float(best["lambda"]),
        "best_shadow": metrics(
            base.actual_closing_home_spread,
            base.shadow_home_spread_best,
        ),
        "games_improved_pct": float(base.shadow_improved.mean()),
        "rows_with_home_delta": int(base.home_prev_game_id.notna().sum()),
        "rows_with_away_delta": int(base.away_prev_game_id.notna().sum()),
        "rows": int(len(base)),
    }, base, grid

def load_total_module():
    spec = importlib.util.spec_from_file_location(
        "total_model", TOTAL_MODEL_SCRIPT
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def total_baseline_predictions(games):
    mod = load_total_module()
    g = games[
        games.closing_total.notna()
        & games.closing_home_spread.notna()
    ].copy()
    models = mod.total_predictions(g)

    rows = []
    for r in g[g.season == 2025].itertuples(index=False):
        model = models[(r.season, r.week)]
        home_pred = (
            model["intercept"]
            + model["off"].get(r.home_team, 0)
            + model["def"].get(r.away_team, 0)
        )
        away_pred = (
            model["intercept"]
            + model["off"].get(r.away_team, 0)
            + model["def"].get(r.home_team, 0)
        )
        rows.append({
            "season": int(r.season),
            "week": int(r.week),
            "game_id": norm_id(r.game_id),
            "home_team": r.home_team,
            "away_team": r.away_team,
            "predicted_closing_total_baseline": home_pred + away_pred,
            "actual_closing_total": float(r.closing_total),
        })
    return pd.DataFrame(rows)

def total_backtest(games):
    base = total_baseline_predictions(games)
    delta = pd.read_csv(TOTAL_DELTA, low_memory=False)
    delta["game_id"] = delta.game_id.map(norm_id)

    keep = [
        "game_id", "prior_data_state",
        "score_only_prediction", "score_plus_pbp_prediction",
        "home_prev_game_id", "away_prev_game_id",
    ]
    base = base.merge(delta[keep], on="game_id", how="left")

    # Production candidate: apply only both-prior PBP delta; otherwise retain baseline.
    base["raw_total_shadow_adjustment"] = np.where(
        base.prior_data_state.eq("both_prior"),
        pd.to_numeric(base.score_plus_pbp_prediction, errors="coerce").fillna(0.0),
        0.0,
    )

    grid = []
    for lam in LAMBDAS:
        pred = (
            base.predicted_closing_total_baseline
            + lam * base.raw_total_shadow_adjustment
        )
        m = metrics(base.actual_closing_total, pred)
        grid.append({"lambda": lam, **m})
    grid = pd.DataFrame(grid).sort_values(["mae", "rmse"])
    best = grid.iloc[0].to_dict()

    base["shadow_total_best"] = (
        base.predicted_closing_total_baseline
        + float(best["lambda"]) * base.raw_total_shadow_adjustment
    )
    base["baseline_abs_error"] = (
        base.predicted_closing_total_baseline - base.actual_closing_total
    ).abs()
    base["shadow_abs_error"] = (
        base.shadow_total_best - base.actual_closing_total
    ).abs()
    base["shadow_improved"] = (
        base.shadow_abs_error < base.baseline_abs_error
    )

    segments = {}
    for state, z in base.groupby(
        base.prior_data_state.fillna("missing")
    ):
        segments[state] = {
            "baseline": metrics(
                z.actual_closing_total,
                z.predicted_closing_total_baseline,
            ),
            "shadow": metrics(
                z.actual_closing_total,
                z.shadow_total_best,
            ),
            "n": int(len(z)),
        }

    return {
        "baseline": metrics(
            base.actual_closing_total,
            base.predicted_closing_total_baseline,
        ),
        "best_lambda": float(best["lambda"]),
        "best_shadow": metrics(
            base.actual_closing_total,
            base.shadow_total_best,
        ),
        "games_improved_pct": float(base.shadow_improved.mean()),
        "segments": segments,
        "rows": int(len(base)),
    }, base, grid

def main():
    for path in (
        GAMES, SPREAD_BASE, SPREAD_DELTA,
        TOTAL_MODEL_SCRIPT, TOTAL_DELTA,
    ):
        if not path.exists():
            raise SystemExit(f"Missing required input: {path}")

    games = pd.read_csv(GAMES, low_memory=False)
    games["season"] = pd.to_numeric(games.season, errors="coerce")
    games["week"] = pd.to_numeric(games.week, errors="coerce")
    games = games.dropna(subset=["season", "week"]).copy()
    games["season"] = games.season.astype(int)
    games["week"] = games.week.astype(int)

    spread_summary, spread_rows, spread_grid = spread_backtest(games)
    total_summary, total_rows, total_grid = total_backtest(games)

    spread_rows.to_csv(OUT / "spread_holdout_2025_rows.csv", index=False)
    spread_grid.to_csv(OUT / "spread_lambda_grid.csv", index=False)
    total_rows.to_csv(OUT / "total_holdout_2025_rows.csv", index=False)
    total_grid.to_csv(OUT / "total_lambda_grid.csv", index=False)

    summary = {
        "schema_version": "full-saturday-shadow-backtest-v1",
        "primary_goal": "predict next closing spread and total",
        "spread": spread_summary,
        "total": total_summary,
        "interpretation": {
            "spread_formula": (
                "market baseline home spread + lambda * "
                "(-home team delta + away team delta)"
            ),
            "total_formula": (
                "market baseline total + lambda * validated both-prior "
                "score-plus-PBP total delta"
            ),
            "one_prior_total_policy": "baseline retained",
            "neither_prior_total_policy": "baseline retained",
        },
        "adoption_rule": (
            "Adopt only when shadow MAE is lower than baseline MAE "
            "on the locked 2025 holdout."
        ),
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))
    print("wrote:", OUT / "spread_holdout_2025_rows.csv")
    print("wrote:", OUT / "spread_lambda_grid.csv")
    print("wrote:", OUT / "total_holdout_2025_rows.csv")
    print("wrote:", OUT / "total_lambda_grid.csv")
    print("wrote:", OUT / "summary.json")

if __name__ == "__main__":
    main()
