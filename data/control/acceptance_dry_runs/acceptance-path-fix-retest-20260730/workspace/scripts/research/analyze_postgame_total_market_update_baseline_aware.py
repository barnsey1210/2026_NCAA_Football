#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
SOURCE = ROOT / "scripts/research/analyze_postgame_total_market_update.py"
OUT = ROOT / "data/research/postgame_total_market_update_baseline_aware_2021_2025"

def load_original():
    spec = importlib.util.spec_from_file_location("original_total_model", SOURCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def metric_block(actual, pred):
    actual = np.asarray(actual, dtype=float)
    pred = np.asarray(pred, dtype=float)
    mask = np.isfinite(actual) & np.isfinite(pred)
    actual = actual[mask]
    pred = pred[mask]
    if len(actual) == 0:
        return {"n": 0}
    baseline = np.zeros(len(actual))
    mae = lambda a, b: float(np.mean(np.abs(a-b)))
    base_mae = mae(actual, baseline)
    model_mae = mae(actual, pred)
    corr = float(np.corrcoef(pred, actual)[0,1]) if len(actual) > 1 else None
    return {
        "n": int(len(actual)),
        "baseline_mae": base_mae,
        "model_mae": model_mae,
        "mae_improvement_pct": 100*(base_mae-model_mae)/base_mae if base_mae else None,
        "direction_accuracy": float(np.mean(np.sign(pred)==np.sign(actual))),
        "correlation": corr,
    }

def main():
    mod = load_original()
    OUT.mkdir(parents=True, exist_ok=True)

    games_path = Path(mod.GAMES)
    if not games_path.is_absolute():
        games_path = ROOT / games_path

    pbp_path = Path(mod.PBP)
    if not pbp_path.is_absolute():
        pbp_path = ROOT / pbp_path

    g = pd.read_csv(games_path, low_memory=False)
    g = g[g.closing_total.notna() & g.closing_home_spread.notna()].copy()

    models = mod.total_predictions(g)
    innovations = []
    for r in g.itertuples(index=False):
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
        innovations.append(r.closing_total - (home_pred + away_pred))
    g["target_total_innovation"] = innovations

    pbp = pd.read_csv(pbp_path, low_memory=False)
    pbp_features = list(mod.PBPV)

    team_rows = []
    for r in g.itertuples(index=False):
        home_implied = (r.closing_total - r.closing_home_spread) / 2
        away_implied = (r.closing_total + r.closing_home_spread) / 2

        team_rows.extend([
            {
                "season": r.season,
                "week": r.week,
                "game_id": r.game_id,
                "team": r.home_team,
                "scored_vs_implied": r.home_score - home_implied,
                "allowed_vs_implied": r.away_score - away_implied,
                "total_residual": r.actual_total_points - r.closing_total,
                "ats_margin": r.closing_spread_residual,
            },
            {
                "season": r.season,
                "week": r.week,
                "game_id": r.game_id,
                "team": r.away_team,
                "scored_vs_implied": r.away_score - away_implied,
                "allowed_vs_implied": r.home_score - home_implied,
                "total_residual": r.actual_total_points - r.closing_total,
                "ats_margin": -r.closing_spread_residual,
            },
        ])

    team = (
        pd.DataFrame(team_rows)
        .merge(
            pbp[["season","week","game_id","team"] + pbp_features],
            on=["season","week","game_id","team"],
            how="left",
        )
        .sort_values(["season","team","week","game_id"])
    )

    team["games_played_through_result"] = (
        team.groupby(["season","team"]).cumcount() + 1
    )
    team["next_game_id"] = team.groupby(["season","team"]).game_id.shift(-1)
    team["next_week"] = team.groupby(["season","team"]).week.shift(-1)
    team = team[
        (team.next_week-team.week >= 1)
        & (team.next_week-team.week <= 3)
        & team.next_game_id.notna()
    ].copy()

    base = g[
        ["season","week","game_id","home_team","away_team","target_total_innovation"]
    ].copy()

    prior_metrics = [
        "scored_vs_implied","allowed_vs_implied","total_residual","ats_margin"
    ] + pbp_features

    for side in ("home","away"):
        rename = {
            "team": f"{side}_prior_team",
            "game_id": f"{side}_prev_game_id",
            "games_played_through_result": f"{side}_games_played_before",
        }
        rename.update({c: f"{side}_prev_{c}" for c in prior_metrics})
        z = team.rename(columns=rename)

        keep = [
            "season","next_game_id",f"{side}_prior_team",
            f"{side}_prev_game_id",f"{side}_games_played_before",
        ] + [f"{side}_prev_{c}" for c in prior_metrics]

        base = base.merge(
            z[keep],
            left_on=["season","game_id",f"{side}_team"],
            right_on=["season","next_game_id",f"{side}_prior_team"],
            how="left",
        ).drop(columns=["next_game_id",f"{side}_prior_team"])

        base[f"{side}_has_prior_game"] = (
            base[f"{side}_prev_game_id"].notna().astype(int)
        )
        base[f"{side}_games_played_before"] = (
            pd.to_numeric(base[f"{side}_games_played_before"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

        for c in prior_metrics:
            col = f"{side}_prev_{c}"
            base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0.0)

    base["prior_data_state"] = np.select(
        [
            (base.home_has_prior_game == 1) & (base.away_has_prior_game == 1),
            (base.home_has_prior_game + base.away_has_prior_game == 1),
        ],
        ["both_prior","one_prior"],
        default="neither_prior",
    )

    score_features = [
        f"{side}_prev_{metric}"
        for side in ("home","away")
        for metric in (
            "scored_vs_implied","allowed_vs_implied","total_residual","ats_margin"
        )
    ] + [
        "home_has_prior_game","away_has_prior_game",
        "home_games_played_before","away_games_played_before",
    ]

    full_features = score_features + [
        f"{side}_prev_{metric}"
        for side in ("home","away")
        for metric in pbp_features
    ]

    train = base[base.season <= 2024].copy()
    holdout = base[base.season == 2025].copy()

    score = mod.fit_predict(train, holdout, score_features)
    full = mod.fit_predict(train, holdout, full_features)

    predictions = holdout[
        [
            "season","week","game_id","home_team","away_team",
            "home_prev_game_id","away_prev_game_id",
            "home_has_prior_game","away_has_prior_game",
            "home_games_played_before","away_games_played_before",
            "prior_data_state","target_total_innovation",
        ]
    ].copy()
    predictions["score_only_prediction"] = score["prediction"]
    predictions["score_plus_pbp_prediction"] = full["prediction"]

    segment_results = {}
    for state, rows in predictions.groupby("prior_data_state"):
        segment_results[state] = {
            "score_only": metric_block(
                rows.target_total_innovation,
                rows.score_only_prediction,
            ),
            "score_plus_pbp": metric_block(
                rows.target_total_innovation,
                rows.score_plus_pbp_prediction,
            ),
        }

    summary = {
        "schema_version": "baseline-aware-total-market-v1",
        "target": "next-game closing-total innovation versus rolling market-implied offense/defense baseline",
        "design": {
            "development": "2021-2023",
            "validation": "2024",
            "holdout": "2025",
            "missing_prior_policy": "neutral feature values plus explicit has-prior and games-played indicators",
        },
        "holdout_score_only": {k:v for k,v in score.items() if k != "prediction"},
        "holdout_score_plus_pbp": {k:v for k,v in full.items() if k != "prediction"},
        "holdout_by_prior_data_state": segment_results,
        "rows": {
            "all": int(len(base)),
            "train": int(len(train)),
            "holdout": int(len(holdout)),
            "both_prior": int((base.prior_data_state=="both_prior").sum()),
            "one_prior": int((base.prior_data_state=="one_prior").sum()),
            "neither_prior": int((base.prior_data_state=="neither_prior").sum()),
        },
        "features": {
            "score_only": score_features,
            "score_plus_pbp": full_features,
        },
    }

    base.to_csv(OUT/"modeling_rows_baseline_aware.csv", index=False)
    predictions.to_csv(OUT/"holdout_2025_predictions_baseline_aware.csv", index=False)
    (OUT/"summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    (OUT/"README.md").write_text(
        "# Baseline-aware postgame total update\n\n"
        "Allows both-prior, one-prior, and neither-prior next-game matchups. "
        "Teams without a prior current-season game retain neutral prior-game "
        "features and are identified explicitly with has-prior and games-played "
        "features. Primary target remains next-game closing-total innovation.\n"
    )

    print(json.dumps(summary, indent=2))
    print("wrote:", OUT/"modeling_rows_baseline_aware.csv")
    print("wrote:", OUT/"holdout_2025_predictions_baseline_aware.csv")
    print("wrote:", OUT/"summary.json")

if __name__ == "__main__":
    main()
