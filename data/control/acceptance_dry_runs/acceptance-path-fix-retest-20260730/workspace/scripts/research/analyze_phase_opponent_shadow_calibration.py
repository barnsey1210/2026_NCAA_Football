#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
OUT = ROOT / "data/research/phase_opponent_shadow_calibration"
OUT.mkdir(parents=True, exist_ok=True)

GAMES = ROOT / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"
MARKET_SCRIPT = ROOT / "scripts/research/build_market_implied_power_ratings.py"
MARKET_SUMMARY = ROOT / "data/research/market_implied_ratings/summary.json"
TOTAL_SCRIPT = ROOT / "scripts/research/analyze_postgame_total_market_update.py"
TOTAL_ROWS = ROOT / "data/research/postgame_total_market_update_baseline_aware_2021_2025/modeling_rows_baseline_aware.csv"

SPREAD_FEATURES = [
    "team_margin",
    "team_closing_spread",
    "team_ats_margin",
    "abs_team_closing_spread",
]
SPREAD_TARGET = "target_next_market_innovation"
LAMBDA_GRID = np.round(np.arange(-0.50, 2.001, 0.05), 2)

def norm_id(v):
    s = str(v or "").strip()
    return s[:-2] if s.endswith(".0") else s

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def median_impute_scale(train_x, hold_x):
    train = train_x.copy().astype(float)
    hold = hold_x.copy().astype(float)

    medians = np.nanmedian(train, axis=0)
    medians = np.where(np.isfinite(medians), medians, 0.0)

    train = np.where(np.isfinite(train), train, medians)
    hold = np.where(np.isfinite(hold), hold, medians)

    means = train.mean(axis=0)
    stds = train.std(axis=0)
    stds = np.where(stds > 1e-12, stds, 1.0)

    return (train - means) / stds, (hold - means) / stds

def ridge_fit_predict(train_x, train_y, hold_x, alpha=10.0):
    xtr, xho = median_impute_scale(
        np.asarray(train_x, dtype=float),
        np.asarray(hold_x, dtype=float),
    )
    y = np.asarray(train_y, dtype=float)
    mask = np.isfinite(y)
    xtr = xtr[mask]
    y = y[mask]

    xtx = xtr.T @ xtr
    coef = np.linalg.solve(
        xtx + alpha * np.eye(xtx.shape[0]),
        xtr.T @ y,
    )
    return xho @ coef

def robust_no_intercept_fit(X, y, alpha=0.1, iterations=25):
    x = np.asarray(X, dtype=float)
    target = np.asarray(y, dtype=float)

    medians = np.nanmedian(x, axis=0)
    medians = np.where(np.isfinite(medians), medians, 0.0)
    x = np.where(np.isfinite(x), x, medians)

    mask = np.isfinite(target)
    x = x[mask]
    target = target[mask]

    if len(target) == 0:
        return np.zeros(x.shape[1], dtype=float)

    weights = np.ones(len(target), dtype=float)
    coef = np.zeros(x.shape[1], dtype=float)

    for _ in range(iterations):
        wx = x * np.sqrt(weights)[:, None]
        wy = target * np.sqrt(weights)
        coef = np.linalg.solve(
            wx.T @ wx + alpha * np.eye(x.shape[1]),
            wx.T @ wy,
        )
        residual = target - x @ coef
        scale = np.median(np.abs(residual - np.median(residual))) * 1.4826
        if not np.isfinite(scale) or scale < 1e-8:
            break
        cutoff = 1.35 * scale
        abs_res = np.abs(residual)
        weights = np.where(
            abs_res <= cutoff,
            1.0,
            cutoff / np.maximum(abs_res, 1e-12),
        )

    return coef

def metrics(actual, pred):
    a = np.asarray(pd.to_numeric(actual, errors="coerce"), dtype=float)
    p = np.asarray(pd.to_numeric(pred, errors="coerce"), dtype=float)
    mask = np.isfinite(a) & np.isfinite(p)
    a, p = a[mask], p[mask]
    if not len(a):
        return {"n": 0}
    e = p - a
    corr = None
    if len(a) > 1 and np.std(a) > 0 and np.std(p) > 0:
        corr = float(np.corrcoef(a, p)[0, 1])
    return {
        "n": int(len(a)),
        "mae": float(np.mean(np.abs(e))),
        "rmse": float(np.sqrt(np.mean(e ** 2))),
        "mean_error": float(np.mean(e)),
        "direction_accuracy": float(np.mean(np.sign(p) == np.sign(a))),
        "correlation": corr,
    }

def find_spread_modeling_rows():
    candidates = []
    for p in ROOT.glob("data/research/**/*.csv"):
        try:
            df = pd.read_csv(p, nrows=5, low_memory=False)
        except Exception:
            continue
        needed = set(SPREAD_FEATURES + [SPREAD_TARGET, "season", "week", "game_id", "team"])
        if needed.issubset(df.columns):
            candidates.append(p)
    if not candidates:
        raise SystemExit("Could not locate spread postgame modeling rows.")
    candidates.sort(
        key=lambda p: (
            0 if "modeling_rows" in p.name else 1,
            -p.stat().st_size,
        )
    )
    return candidates[0]

def fit_delta_model(rows, train_end, predict_year, features, target):
    train = rows[rows.season <= train_end].copy()
    hold = rows[rows.season == predict_year].copy()
    Xtr = train[features].apply(pd.to_numeric, errors="coerce")
    ytr = pd.to_numeric(train[target], errors="coerce")
    Xho = hold[features].apply(pd.to_numeric, errors="coerce")
    valid = ytr.notna()
    hold = hold.copy()
    hold["prediction"] = ridge_fit_predict(
        Xtr.loc[valid].to_numpy(),
        ytr.loc[valid].to_numpy(),
        Xho.to_numpy(),
        alpha=10.0,
    )
    return hold

def market_baseline(year):
    mod = load_module(MARKET_SCRIPT, "market_ratings")
    params = json.loads(MARKET_SUMMARY.read_text())[
        "parameter_selection"
    ]["selected"]
    games = pd.read_csv(GAMES, low_memory=False)
    games["season"] = pd.to_numeric(games.season, errors="coerce")
    games["week"] = pd.to_numeric(games.week, errors="coerce")
    games = games.dropna(subset=["season", "week"]).copy()
    games["season"] = games.season.astype(int)
    games["week"] = games.week.astype(int)
    _, rows = mod.evaluate_params(games, year, params)
    rows["game_id"] = rows.game_id.map(norm_id)
    return rows

def build_team_schedule(games):
    team_rows = []
    for r in games.itertuples(index=False):
        for team in (r.home_team, r.away_team):
            team_rows.append({
                "season": int(r.season),
                "week": int(r.week),
                "game_id": norm_id(r.game_id),
                "team": team,
            })
    t = pd.DataFrame(team_rows).sort_values(
        ["season", "team", "week", "game_id"]
    )
    t["games_played_through"] = (
        t.groupby(["season", "team"]).cumcount() + 1
    )
    t["next_game_id"] = t.groupby(["season", "team"]).game_id.shift(-1)
    t["next_week"] = t.groupby(["season", "team"]).week.shift(-1)
    return t[
        t.next_game_id.notna()
        & ((t.next_week - t.week) >= 1)
        & ((t.next_week - t.week) <= 3)
    ].copy()

def attach_spread_deltas(base, delta, schedule):
    home_prev = schedule.rename(columns={
        "team": "home_team",
        "game_id": "home_prev_game_id",
        "next_game_id": "game_id",
        "games_played_through": "home_games_played",
    })[["season","game_id","home_team","home_prev_game_id","home_games_played"]]

    away_prev = schedule.rename(columns={
        "team": "away_team",
        "game_id": "away_prev_game_id",
        "next_game_id": "game_id",
        "games_played_through": "away_games_played",
    })[["season","game_id","away_team","away_prev_game_id","away_games_played"]]

    z = base.merge(
        home_prev, on=["season","game_id","home_team"], how="left"
    ).merge(
        away_prev, on=["season","game_id","away_team"], how="left"
    )

    d = delta[["game_id","team","prediction"]].copy()
    d["game_id"] = d.game_id.map(norm_id)

    h = d.rename(columns={
        "game_id":"home_prev_game_id",
        "team":"home_team",
        "prediction":"home_delta",
    })
    a = d.rename(columns={
        "game_id":"away_prev_game_id",
        "team":"away_team",
        "prediction":"away_delta",
    })
    z = z.merge(h, on=["home_prev_game_id","home_team"], how="left")
    z = z.merge(a, on=["away_prev_game_id","away_team"], how="left")
    for c in ("home_delta","away_delta"):
        z[c] = pd.to_numeric(z[c], errors="coerce").fillna(0.0)
    for c in ("home_games_played","away_games_played"):
        z[c] = pd.to_numeric(z[c], errors="coerce").fillna(0).astype(int)

    z["actual_residual"] = (
        z.actual_closing_home_spread - z.predicted_home_spread
    )
    z["raw_matchup_adjustment"] = -z.home_delta + z.away_delta
    return z

def phase_bucket(g):
    if g <= 1:
        return "g1"
    if g <= 3:
        return "g2_3"
    return "g4_plus"

def spread_design(z, kind):
    if kind == "global":
        return pd.DataFrame({"global": z.raw_matchup_adjustment})
    if kind == "separate_home_away":
        return pd.DataFrame({
            "home": -z.home_delta,
            "away": z.away_delta,
        })
    if kind == "phase":
        out = {}
        for bucket in ("g1","g2_3","g4_plus"):
            out[bucket] = (
                -z.home_delta * z.home_games_played.map(
                    lambda x: phase_bucket(x) == bucket
                ).astype(float)
                + z.away_delta * z.away_games_played.map(
                    lambda x: phase_bucket(x) == bucket
                ).astype(float)
            )
        return pd.DataFrame(out)
    if kind == "phase_home_away":
        out = {}
        for side, sign in (("home",-1.0),("away",1.0)):
            games_col = z[f"{side}_games_played"]
            delta_col = z[f"{side}_delta"]
            for bucket in ("g1","g2_3","g4_plus"):
                out[f"{side}_{bucket}"] = (
                    sign * delta_col
                    * games_col.map(lambda x: phase_bucket(x) == bucket).astype(float)
                )
        return pd.DataFrame(out)
    raise ValueError(kind)

def fit_calibrator(validation, kind):
    X = spread_design(validation, kind)
    y = validation.actual_residual
    if kind == "global":
        best = None
        for lam in LAMBDA_GRID:
            pred = lam * X.iloc[:,0]
            m = metrics(y, pred)
            if best is None or m["mae"] < best["metrics"]["mae"]:
                best = {"lambda": float(lam), "metrics": m}
        return {"kind":kind, "coef":[best["lambda"]], "columns":list(X.columns), "validation":best["metrics"]}
    coef = np.clip(
        robust_no_intercept_fit(X.to_numpy(), y.to_numpy(), alpha=0.1),
        -0.5,
        2.0,
    )
    pred = X.to_numpy() @ coef
    return {
        "kind":kind,
        "coef":[float(x) for x in coef],
        "columns":list(X.columns),
        "validation":metrics(y, pred),
    }

def apply_calibrator(z, cal):
    X = spread_design(z, cal["kind"])
    return X.to_numpy() @ np.asarray(cal["coef"])

def spread_research(games):
    spread_rows_path = find_spread_modeling_rows()
    rows = pd.read_csv(spread_rows_path, low_memory=False)
    rows["season"] = pd.to_numeric(rows.season, errors="coerce")
    rows["week"] = pd.to_numeric(rows.week, errors="coerce")
    rows = rows.dropna(subset=["season","week"]).copy()
    rows["season"] = rows.season.astype(int)
    rows["week"] = rows.week.astype(int)

    d24 = fit_delta_model(rows, 2023, 2024, SPREAD_FEATURES, SPREAD_TARGET)
    d25 = fit_delta_model(rows, 2024, 2025, SPREAD_FEATURES, SPREAD_TARGET)

    schedule = build_team_schedule(games)
    v = attach_spread_deltas(market_baseline(2024), d24, schedule[schedule.season==2024])
    h = attach_spread_deltas(market_baseline(2025), d25, schedule[schedule.season==2025])

    candidates = []
    for kind in ("global","separate_home_away","phase","phase_home_away"):
        cal = fit_calibrator(v, kind)
        v_adj = apply_calibrator(v, cal)
        h_adj = apply_calibrator(h, cal)
        cal["holdout"] = metrics(
            h.actual_closing_home_spread,
            h.predicted_home_spread + h_adj,
        )
        cal["holdout_baseline"] = metrics(
            h.actual_closing_home_spread,
            h.predicted_home_spread,
        )
        cal["validation_full_line"] = metrics(
            v.actual_closing_home_spread,
            v.predicted_home_spread + v_adj,
        )
        candidates.append(cal)

    candidates.sort(key=lambda x: x["validation_full_line"]["mae"])
    selected = candidates[0]
    h["selected_adjustment"] = apply_calibrator(h, selected)
    h["saturday_shadow_spread"] = (
        h.predicted_home_spread + h.selected_adjustment
    )
    h["baseline_abs_error"] = (
        h.predicted_home_spread - h.actual_closing_home_spread
    ).abs()
    h["shadow_abs_error"] = (
        h.saturday_shadow_spread - h.actual_closing_home_spread
    ).abs()

    return {
        "spread_modeling_rows": str(spread_rows_path.relative_to(ROOT)),
        "selected_on_2024": selected,
        "all_candidates": candidates,
        "holdout_improved_games_pct": float(
            (h.shadow_abs_error < h.baseline_abs_error).mean()
        ),
    }, h

def total_baseline(games, year):
    mod = load_module(TOTAL_SCRIPT, "total_model")
    g = games[
        games.closing_total.notna()
        & games.closing_home_spread.notna()
    ].copy()
    models = mod.total_predictions(g)
    rows = []
    for r in g[g.season == year].itertuples(index=False):
        model = models[(r.season, r.week)]
        hp = model["intercept"] + model["off"].get(r.home_team,0) + model["def"].get(r.away_team,0)
        ap = model["intercept"] + model["off"].get(r.away_team,0) + model["def"].get(r.home_team,0)
        rows.append({
            "season":year,
            "week":int(r.week),
            "game_id":norm_id(r.game_id),
            "home_team":r.home_team,
            "away_team":r.away_team,
            "baseline_total":hp+ap,
            "actual_closing_total":float(r.closing_total),
        })
    return pd.DataFrame(rows)

def total_delta_predictions(rows, train_end, predict_year):
    mod = load_module(TOTAL_SCRIPT, "total_model_for_fit")
    score = [
        f"{side}_prev_{metric}"
        for side in ("home","away")
        for metric in ("scored_vs_implied","allowed_vs_implied","total_residual","ats_margin")
    ] + [
        "home_has_prior_game","away_has_prior_game",
        "home_games_played_before","away_games_played_before",
    ]
    pbp = [
        f"{side}_prev_{metric}"
        for side in ("home","away")
        for metric in list(mod.PBPV)
    ]
    features = score + pbp
    train = rows[rows.season <= train_end].copy()
    hold = rows[rows.season == predict_year].copy()
    result = mod.fit_predict(train, hold, features)
    hold = hold.copy()
    hold["prediction"] = result["prediction"]
    hold["game_id"] = hold.game_id.map(norm_id)
    return hold

def total_research(games):
    rows = pd.read_csv(TOTAL_ROWS, low_memory=False)
    rows["season"] = pd.to_numeric(rows.season, errors="coerce").astype(int)
    d24 = total_delta_predictions(rows, 2023, 2024)
    d25 = total_delta_predictions(rows, 2024, 2025)

    def join(year, delta):
        z = total_baseline(games, year).merge(
            delta[[
                "game_id","prediction","prior_data_state",
                "home_games_played_before","away_games_played_before"
            ]],
            on="game_id",
            how="left",
        )
        z["prediction"] = pd.to_numeric(z.prediction, errors="coerce").fillna(0.0)
        z["raw_adjustment"] = np.where(
            z.prior_data_state.eq("both_prior"),
            z.prediction,
            0.0,
        )
        z["actual_residual"] = z.actual_closing_total - z.baseline_total
        return z

    v = join(2024, d24)
    h = join(2025, d25)

    # Global lambda selected on 2024, using PBP-enabled both-prior delta.
    best = None
    for lam in LAMBDA_GRID:
        pred = v.baseline_total + lam * v.raw_adjustment
        m = metrics(v.actual_closing_total, pred)
        if best is None or m["mae"] < best["validation"]["mae"]:
            best = {"lambda":float(lam), "validation":m}

    h["saturday_shadow_total"] = h.baseline_total + best["lambda"] * h.raw_adjustment
    best["holdout_baseline"] = metrics(h.actual_closing_total, h.baseline_total)
    best["holdout_shadow"] = metrics(h.actual_closing_total, h.saturday_shadow_total)

    both = h[h.prior_data_state.eq("both_prior")]
    best["holdout_both_prior_baseline"] = metrics(
        both.actual_closing_total, both.baseline_total
    )
    best["holdout_both_prior_shadow"] = metrics(
        both.actual_closing_total, both.saturday_shadow_total
    )
    best["uses_pbp"] = True
    best["pbp_feature_source"] = "score_plus_pbp feature set from analyze_postgame_total_market_update.py"
    return best, h

def main():
    for p in (GAMES, MARKET_SCRIPT, MARKET_SUMMARY, TOTAL_SCRIPT, TOTAL_ROWS):
        if not p.exists():
            raise SystemExit(f"Missing required input: {p}")

    games = pd.read_csv(GAMES, low_memory=False)
    games["season"] = pd.to_numeric(games.season, errors="coerce")
    games["week"] = pd.to_numeric(games.week, errors="coerce")
    games = games.dropna(subset=["season","week"]).copy()
    games["season"] = games.season.astype(int)
    games["week"] = games.week.astype(int)

    spread_summary, spread_rows = spread_research(games)
    total_summary, total_rows = total_research(games)

    spread_rows.to_csv(OUT/"spread_2025_holdout_phase_opponent.csv", index=False)
    total_rows.to_csv(OUT/"total_2025_holdout_pbp.csv", index=False)

    summary = {
        "schema_version":"phase-opponent-shadow-calibration-v1",
        "primary_goal":"predict next closing spread and total",
        "validation_design":{
            "delta_train_for_2024":"2021-2023",
            "calibration_selection":"2024 only",
            "locked_holdout":"2025",
        },
        "spread":{
            "opponent_adjustment_note":(
                "The matchup adjustment already uses both teams: "
                "-home delta + away delta. Additional candidates test "
                "separate home/away coefficients and games-played phase effects."
            ),
            **spread_summary,
        },
        "total":{
            "pbp_note":(
                "Totals use the validated score-plus-PBP feature set for "
                "both-prior games. One-prior and neither-prior retain baseline."
            ),
            **total_summary,
        },
        "adoption_rule":(
            "Choose structure and coefficients on 2024 only. "
            "Adopt only if frozen settings improve 2025 closing-line MAE."
        ),
    }
    (OUT/"summary.json").write_text(
        json.dumps(summary,indent=2)+"\n",
        encoding="utf-8",
    )
    print(json.dumps(summary,indent=2))
    print("wrote:",OUT/"summary.json")
    print("wrote:",OUT/"spread_2025_holdout_phase_opponent.csv")
    print("wrote:",OUT/"total_2025_holdout_pbp.csv")

if __name__=="__main__":
    main()
