#!/usr/bin/env python3
"""Validate the transparent CFP resume score against historical weekly rankings."""
import csv
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/models/cfp_weekly_rankings_history.csv"
WEIGHTS = {
    "game_control": 30.0,
    "championship_wins_power": 8.0, "championship_wins_g6": 5.0,
    "quality_wins": 2.5, "top25_wins": 3.5, "avg_capped_mov": 0.18,
    "avg_weighted_mol": -0.25, "bad_losses": -5.0, "sos": 12.0,
}

def num(row, key):
    try: return float(row.get(key) or 0)
    except ValueError: return 0.0

def score(row):
    return (WEIGHTS["game_control"] * (num(row, "game_control") - .5)
            + sum(num(row, k) * w for k, w in WEIGHTS.items() if k not in {"sos", "game_control"})
            + WEIGHTS["sos"] * (num(row, "sos") - .5))

def main():
    rows = list(csv.DictReader(SOURCE.open()))
    if not rows:
        print(f"No historical rows yet: {SOURCE}")
        print("Populate weekly committee ranks and the eight pre-ranking resume metrics; no model weights were changed.")
        return
    groups = defaultdict(list)
    for r in rows: groups[(r["season"], r["week"])].append(r)
    abs_error = ranked_rows = top12_hits = top12_total = 0
    for key, group in sorted(groups.items()):
        modeled = sorted(group, key=score, reverse=True)
        for rank, row in enumerate(modeled, 1):
            actual = int(float(row["actual_cfp_rank"]))
            if actual <= 25:
                abs_error += abs(rank - actual); ranked_rows += 1
            if actual <= 12:
                top12_total += 1
                top12_hits += rank <= 12
    print(f"Weekly snapshots: {len(groups)}")
    print(f"Team-week rows: {len(rows)}")
    print(f"Mean absolute ranking error (official Top 25 only): {abs_error/ranked_rows:.3f}")
    print(f"Top-12 recall: {top12_hits}/{top12_total} ({top12_hits/top12_total:.1%})" if top12_total else "Top-12 recall: n/a")

    # Leakage-safe coefficient diagnostic: each season is scored by a model fit
    # only on the other seasons. Harmful variables are sign-flipped first.
    features = ["game_control", "quality_wins", "top25_wins", "avg_capped_mov", "avg_weighted_mol", "bad_losses", "sos"]
    directions = np.array([1, 1, 1, 1, -1, -1, 1], dtype=float)
    matrix = np.array([[num(r, f) for f in features] for r in rows], dtype=float) * directions
    target = np.array([max(0, 26-int(float(r["actual_cfp_rank"]))) for r in rows], dtype=float)
    seasons = np.array([int(r["season"]) for r in rows])
    predictions = np.zeros(len(rows)); fold_coefs = []
    for held in sorted(set(seasons)):
        train, test = seasons != held, seasons == held
        mean, std = matrix[train].mean(0), matrix[train].std(0)
        std[std < 1e-8] = 1
        x = (matrix[train]-mean)/std; y = target[train]
        design = np.column_stack([np.ones(len(x)), x])
        penalty = np.eye(design.shape[1])*5.0; penalty[0,0] = 0
        beta = np.linalg.solve(design.T@design+penalty, design.T@y)
        predictions[test] = np.column_stack([np.ones(test.sum()),(matrix[test]-mean)/std])@beta
        fold_coefs.append(beta[1:]*directions/std)
    fit_hits = fit_total = fit_abs = fit_ranked = 0
    grouped = defaultdict(list)
    for i,r in enumerate(rows): grouped[(r["season"],r["week"])].append(i)
    for indices in grouped.values():
        modeled = sorted(indices,key=lambda i:predictions[i],reverse=True)
        model_rank = {idx:rank for rank,idx in enumerate(modeled,1)}
        for idx in indices:
            actual=int(float(rows[idx]["actual_cfp_rank"]))
            if actual<=25: fit_abs+=abs(model_rank[idx]-actual);fit_ranked+=1
            if actual<=12: fit_total+=1;fit_hits+=model_rank[idx]<=12
    coefs=np.mean(fold_coefs,axis=0)
    print("\nLeave-one-season-out ridge diagnostic (2021-24):")
    print(f"Mean absolute ranking error (official Top 25 only): {fit_abs/fit_ranked:.3f}")
    print(f"Top-12 recall: {fit_hits}/{fit_total} ({fit_hits/fit_total:.1%})")
    print("Average raw-scale coefficients (diagnostic, not yet production weights):")
    for name,value in zip(features,coefs): print(f"  {name}: {value:+.3f}")

if __name__ == "__main__": main()
