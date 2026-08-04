#!/usr/bin/env python3
"""Backtest weighted averages of GC, SOS, quality wins, and Top-25 wins.

Weights are searched on training seasons only and evaluated on the held-out
season. Metrics are converted to within-week percentile scores before blending,
so the weights are directly comparable and do not depend on raw units.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/models/cfp_weekly_rankings_history.csv"
OUTPUT = ROOT / "data/models/cfp_core_metric_backtest.json"


def weight_grid(step_units=20):
    for a in range(step_units + 1):
        for b in range(step_units - a + 1):
            for c in range(step_units - a - b + 1):
                d = step_units - a - b - c
                yield np.array([a, b, c, d], dtype=float) / step_units


def prepare(frame, game_control_column, top25_column):
    cols = [game_control_column, "sos", "quality_wins", top25_column]
    out = frame.copy()
    for col in cols:
        out[col + "_pct"] = out.groupby(["season", "week"])[col].rank(pct=True, method="average")
    return out, [c + "_pct" for c in cols]


def evaluate(frame, feature_cols, weights):
    work = frame.copy()
    work["score"] = work[feature_cols].to_numpy() @ weights
    work["model_rank"] = work.groupby(["season", "week"])["score"].rank(ascending=False, method="first")
    ranked = work[work.actual_cfp_rank <= 25]
    top12 = work[work.actual_cfp_rank <= 12]
    actual_top25 = len(ranked)
    return {
        "top12_recall": float((top12.model_rank <= 12).mean()),
        "top25_recall": float((ranked.model_rank <= 25).mean()),
        "top25_mae": float((ranked.model_rank - ranked.actual_cfp_rank).abs().mean()),
        "ranked_rows": int(actual_top25),
    }


def select_weights(train, feature_cols, grid):
    best = None
    for weights in grid:
        metrics = evaluate(train, feature_cols, weights)
        key = (metrics["top12_recall"], metrics["top25_recall"], -metrics["top25_mae"])
        if best is None or key > best[0]: best = (key, weights.copy(), metrics)
    return best[1], best[2]


def run_folds(data, features, names, grid):
    folds=[]
    for held in sorted(data.season.unique()):
        weights, train_metrics = select_weights(data[data.season != held], features, grid)
        test_metrics = evaluate(data[data.season == held], features, weights)
        folds.append({"held_out_season": int(held), "weights": dict(zip(names, map(float, weights.round(3)))), "train":train_metrics,"test":test_metrics})
    total=sum(f["test"]["ranked_rows"] for f in folds)
    aggregate={key:float(sum(f["test"][key]*f["test"]["ranked_rows"] for f in folds)/total) for key in ["top12_recall","top25_recall","top25_mae"]}
    return folds,aggregate


def experiment(frame, game_control_column, top25_column):
    names = [game_control_column, "sos", "quality_wins", top25_column]
    data, features = prepare(frame, game_control_column, top25_column)
    grid = list(weight_grid())
    folds,aggregate=run_folds(data,features,names,grid)
    forced_folds,forced_aggregate=run_folds(data,features,names,[w for w in grid if w[1]>=.10])
    global_weights, global_metrics = select_weights(data, features, grid)
    equal = evaluate(data, features, np.array([.25,.25,.25,.25]))
    return {"game_control_definition": game_control_column, "top25_definition": top25_column, "normalization": "within-week percentile",
            "selection": "maximize training Top-12 recall, then Top-25 recall, then minimize Top-25 MAE",
            "held_out_folds": folds, "held_out_aggregate": aggregate,
            "forced_sos_min_10pct": {"held_out_folds":forced_folds,"held_out_aggregate":forced_aggregate},
            "equal_weight_baseline": equal,
            "descriptive_full_sample_best": {"weights":dict(zip(names,map(float,global_weights.round(3)))),"metrics":global_metrics}}


def main():
    frame = pd.read_csv(SOURCE)
    results = {"championship_flags_used": False, "seasons": sorted(map(int,frame.season.unique())),
               "snapshots": int(frame.groupby(["season","week"]).ngroups),
               "experiments": [experiment(frame,gc,t25) for gc in ["game_control","raw_game_control"] for t25 in ["top25_wins","prior_top25_wins","provisional_top25_wins"]]}
    OUTPUT.write_text(json.dumps(results, indent=2)+"\n")
    for result in results["experiments"]:
        print(f"\n{result['game_control_definition']} + {result['top25_definition']}")
        print("held-out aggregate", json.dumps(result["held_out_aggregate"], indent=2))
        print("forced SOS >=10%", json.dumps(result["forced_sos_min_10pct"]["held_out_aggregate"], indent=2))
        print("equal weights", json.dumps(result["equal_weight_baseline"], indent=2))
        print("full-sample descriptive weights", result["descriptive_full_sample_best"]["weights"])
        for fold in result["held_out_folds"]:
            print(f"  hold {fold['held_out_season']}: {fold['weights']} -> Top12 {fold['test']['top12_recall']:.1%}, MAE {fold['test']['top25_mae']:.2f}")
    print(f"\nWrote {OUTPUT}")


if __name__ == "__main__": main()
