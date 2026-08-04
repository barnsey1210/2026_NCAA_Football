#!/usr/bin/env python3
"""No-look-ahead season-stage calibration for the Saturday Shadow research layer."""
from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import math
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/research/shadow_season_stage_calibration"
REPORT = ROOT / "build/research/shadow_season_stage_calibration/index.html"
GAMES = ROOT / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"
SPREAD_ROWS = ROOT / "data/research/postgame_pbp_market_rating_update_2021_2024/modeling_rows_2021_2025.csv"
TOTAL_ROWS = ROOT / "data/research/postgame_total_market_update_baseline_aware_2021_2025/modeling_rows_baseline_aware.csv"
TOTAL_SCRIPT = ROOT / "scripts/research/analyze_postgame_total_market_update.py"
CONFIG = ROOT / "config/market_shadow_production.json"
PUBLIC_REPO = Path("/Users/jameslindesmith/Sites/NCAAF_SITE")
HFA = 2.5
SPREAD_FEATURES = ["team_margin", "team_closing_spread", "team_ats_margin", "abs_team_closing_spread"]
TOTAL_SCORE = [
    "home_prev_scored_vs_implied", "home_prev_allowed_vs_implied", "home_prev_total_residual", "home_prev_ats_margin",
    "away_prev_scored_vs_implied", "away_prev_allowed_vs_implied", "away_prev_total_residual", "away_prev_ats_margin",
]
TOTAL_PBP_BASE = ["off_success_rate", "off_ppa", "off_explosiveness", "def_success_allowed", "def_ppa_allowed", "def_explosiveness_allowed", "off_drive_elapsed_seconds_per_play", "off_plays"]
TOTAL_FEATURES = TOTAL_SCORE + [f"{side}_prev_{field}" for side in ("home", "away") for field in TOTAL_PBP_BASE]
STAGES = [(1, 3, "Weeks 1-3"), (4, 6, "Weeks 4-6"), (7, 9, "Weeks 7-9"), (10, 12, "Weeks 10-12"), (13, 99, "Weeks 13+")]
GAME_STAGES = [(0, 2, "0-2"), (3, 5, "3-5"), (6, 8, "6-8"), (9, 99, "9+")]
PROTECTED = [
    "config/market_shadow_production.json", "scripts/site/build_saturday_shadow_lines.py",
    "scripts/site/build_postgame_shadow_updates.py", "openers_v2.html", "schedule_v2.html",
    "daily_market_update.sh", "scripts/publish/publish_site.sh",
    "data/site/postgame_shadow_updates.json", "data/site/saturday_shadow_lines.json",
    "data/site/schedule_live_enrichment.json",
]


def finite(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else np.nan
    except (TypeError, ValueError):
        return np.nan


def norm_id(v):
    s = str(v or "").strip()
    return s[:-2] if s.endswith(".0") else s


def sha(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def protected_hashes():
    return {p: sha(ROOT / p) for p in PROTECTED if (ROOT / p).exists()}


def repo_state():
    return {
        "head": subprocess.run(["git", "-C", str(PUBLIC_REPO), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip(),
        "status": subprocess.run(["git", "-C", str(PUBLIC_REPO), "status", "--short"], check=True, text=True, capture_output=True).stdout.strip(),
    }


def stage(week):
    for lo, hi, label in STAGES:
        if lo <= week <= hi:
            return label
    raise ValueError(week)


def game_stage(n):
    for lo, hi, label in GAME_STAGES:
        if lo <= n <= hi:
            return label
    return "9+"


def ridge_predict(train: pd.DataFrame, test: pd.DataFrame, features, target, alpha=20.0):
    if len(train) < 100 or test.empty:
        return np.full(len(test), np.nan)
    x = train[features].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    xt = test[features].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    med = np.nanmedian(x, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    x = np.where(np.isnan(x), med, x); xt = np.where(np.isnan(xt), med, xt)
    mu = x.mean(0); sd = np.where(x.std(0) > 1e-9, x.std(0), 1.0)
    x = (x - mu) / sd; xt = (xt - mu) / sd
    x = np.c_[np.ones(len(x)), x]; xt = np.c_[np.ones(len(xt)), xt]
    penalty = alpha * np.eye(x.shape[1]); penalty[0, 0] = 0
    beta = np.linalg.solve(x.T @ x + penalty, x.T @ pd.to_numeric(train[target], errors="coerce").to_numpy(float))
    return xt @ beta


def load_total_module():
    spec = importlib.util.spec_from_file_location("shadow_total_calibration", TOTAL_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def baseline_rows(games):
    """Reproduce frozen preopener spread and total states using only earlier weeks."""
    spread = []
    for season, d in games.groupby("season"):
        teams = sorted(set(d.home_team) | set(d.away_team)); idx = {t: i for i, t in enumerate(teams)}
        for week in sorted(d.week.unique()):
            hist = d[(d.week < week) & (d.week >= week - 6) & d.closing_home_spread.notna()]
            if hist.empty:
                ratings = {t: 0.0 for t in teams}
            else:
                x = np.zeros((len(hist), len(teams))); y = np.zeros(len(hist))
                for j, r in enumerate(hist.itertuples(index=False)):
                    x[j, idx[r.home_team]] = 1; x[j, idx[r.away_team]] = -1
                    y[j] = -float(r.closing_home_spread) - HFA
                b = np.linalg.solve(x.T @ x + 8.0 * np.eye(len(teams)), x.T @ y); b -= b.mean()
                ratings = {t: float(b[idx[t]]) for t in teams}
            for r in d[d.week == week].itertuples(index=False):
                spread.append({"game_id": norm_id(r.game_id), "spread_baseline": -(ratings.get(r.home_team, 0) - ratings.get(r.away_team, 0) + HFA)})
    total_mod = load_total_module()
    eligible = games[games.closing_total.notna() & games.closing_home_spread.notna()].copy()
    models = total_mod.total_predictions(eligible)
    total = []
    for r in eligible.itertuples(index=False):
        m = models[(r.season, r.week)]
        hp = m["intercept"] + m["off"].get(r.home_team, 0) + m["def"].get(r.away_team, 0)
        ap = m["intercept"] + m["off"].get(r.away_team, 0) + m["def"].get(r.home_team, 0)
        total.append({"game_id": norm_id(r.game_id), "total_baseline": hp + ap})
    return pd.DataFrame(spread).merge(pd.DataFrame(total), on="game_id", how="left")


def walk_forward_impacts(games):
    """Fit each week's raw signal using only targets known before that week's cutoff."""
    sr = pd.read_csv(SPREAD_ROWS, low_memory=False); sr["game_id"] = sr.game_id.map(norm_id)
    tr = pd.read_csv(TOTAL_ROWS, low_memory=False); tr["game_id"] = tr.game_id.map(norm_id)
    spread_pred = []
    for (season, completed_week), test in sr.groupby(["season", "week"]):
        train = sr[(sr.season < season) | ((sr.season == season) & (sr.next_week <= completed_week))].dropna(subset=["target_next_market_innovation"])
        pred = ridge_predict(train, test, SPREAD_FEATURES, "target_next_market_innovation")
        for (_, r), p in zip(test.iterrows(), pred):
            spread_pred.append({"prev_game_id": r.game_id, "team": r.team, "completed_week": int(completed_week), "raw_team_spread": p, "spread_train_n": len(train)})
    sp = pd.DataFrame(spread_pred)
    team_games = []
    for r in games.itertuples(index=False):
        team_games += [{"game_id": norm_id(r.game_id), "season": int(r.season), "week": int(r.week), "team": r.home_team, "side": "home", "prior_games": finite(r.home_prior_games)},
                       {"game_id": norm_id(r.game_id), "season": int(r.season), "week": int(r.week), "team": r.away_team, "side": "away", "prior_games": finite(r.away_prior_games)}]
    tg = pd.DataFrame(team_games).sort_values(["season", "team", "week", "game_id"])
    tg["prev_game_id"] = tg.groupby(["season", "team"]).game_id.shift(1)
    tg["prev_week"] = tg.groupby(["season", "team"]).week.shift(1)
    target_sp = tg.merge(sp[["prev_game_id", "team", "raw_team_spread", "spread_train_n"]], on=["prev_game_id", "team"], how="left")
    target_sp.loc[(target_sp.week-target_sp.prev_week)!=1,"raw_team_spread"] = np.nan
    wide = target_sp.pivot(index="game_id", columns="side", values="raw_team_spread").rename(columns={"home": "raw_home_spread", "away": "raw_away_spread"}).reset_index()
    counts = target_sp.groupby("game_id").agg(spread_update_count=("raw_team_spread", lambda x: int(x.notna().sum())), avg_games_played=("prior_games", "mean")).reset_index()
    spread_game = wide.merge(counts, on="game_id", how="outer")
    game_week = dict(zip(games.game_id.map(norm_id), games.week))
    tr["home_prev_game_id"] = tr.home_prev_game_id.map(norm_id); tr["away_prev_game_id"] = tr.away_prev_game_id.map(norm_id)
    tr["immediate_both_prior"] = tr.prior_data_state.eq("both_prior") & tr.home_prev_game_id.map(game_week).eq(tr.week-1) & tr.away_prev_game_id.map(game_week).eq(tr.week-1)
    total_pred = []
    for (season, target_week), test in tr.groupby(["season", "week"]):
        train = tr[((tr.season < season) | ((tr.season == season) & (tr.week < target_week))) & tr.immediate_both_prior].dropna(subset=["target_total_innovation"])
        pred = ridge_predict(train, test, TOTAL_FEATURES, "target_total_innovation")
        for (_, r), p in zip(test.iterrows(), pred):
            eligible = bool(r.immediate_both_prior and np.isfinite(p))
            total_pred.append({"game_id": r.game_id, "raw_total": p if eligible else np.nan, "total_train_n": len(train), "both_prior_total": eligible})
    return spread_game.merge(pd.DataFrame(total_pred), on="game_id", how="outer")


def signal_class(pred_move, actual_move, tol):
    if not np.isfinite(pred_move) or not np.isfinite(actual_move): return "ineligible"
    if abs(pred_move) <= tol: return "unchanged"
    if abs(actual_move) <= tol: return "actual_no_move"
    if np.sign(pred_move) != np.sign(actual_move): return "wrong"
    if abs(pred_move) > abs(actual_move) + tol: return "overshoot"
    if abs(pred_move) < abs(actual_move) - tol: return "undershoot"
    return "correct"


def apply_model(df, market, spec):
    raw = df["raw_spread" if market == "spread" else "raw_total"].fillna(0).to_numpy(float)
    weeks = df.week.to_numpy(int); games = df.avg_games_played.fillna(0).to_numpy(float)
    family = spec["family"]
    if family in ("none", "constant"):
        lam = np.full(len(df), spec.get("lambda", 0.0))
    elif family == "week_bucket":
        lam = np.array([spec["schedule"][stage(w)] for w in weeks])
    elif family == "games_bucket":
        lam = np.array([spec["schedule"][game_stage(g)] for g in games])
    elif family == "exp_decay":
        lam = spec["base"] * np.exp(-spec["k"] * games)
    elif family == "sqrt_decay":
        lam = spec["base"] / np.sqrt(games + spec["c"])
    else:
        raise ValueError(family)
    scaled = raw * lam
    cap = spec.get("cap")
    if cap is not None:
        if spec.get("cap_type") == "smooth":
            applied = cap * np.tanh(scaled / cap)
        else:
            applied = np.clip(scaled, -cap, cap)
    else:
        applied = scaled
    return applied, lam


def metrics(df, market, spec, tol=0.5):
    applied, lam = apply_model(df, market, spec)
    baseline = df[f"{market}_baseline"].to_numpy(float); close = df[f"closing_{market}"].to_numpy(float)
    opener = df[f"opening_{market}"].to_numpy(float); result = df["actual_home_margin" if market == "spread" else "actual_total_points"].to_numpy(float)
    pred = baseline + applied
    valid = np.isfinite(pred) & np.isfinite(close)
    err = pred[valid] - close[valid]
    eval_move = close - opener; pred_move = pred - opener
    sig = np.array([signal_class(a, b, tol) for a, b in zip(pred_move, eval_move)])
    directional = np.isin(sig, ["correct", "overshoot", "undershoot", "wrong"])
    bets = np.isfinite(opener) & (np.abs(pred_move) > tol)
    clv = np.where(pred_move > 0, eval_move, -eval_move)
    actual_err = np.abs(pred - (-result if market == "spread" else result))
    out = {
        "n": int(valid.sum()), "opener_n": int(np.isfinite(opener).sum()), "direction_n": int(directional.sum()),
        "direction_accuracy": float(np.mean(sig[directional] != "wrong")) if directional.any() else None,
        "positive_clv_rate": float(np.mean(clv[bets] > tol)) if bets.any() else None,
        "average_clv": float(np.mean(clv[bets])) if bets.any() else None,
        "median_clv": float(np.median(clv[bets])) if bets.any() else None,
        "mae": float(np.mean(np.abs(err))) if len(err) else None, "median_ae": float(np.median(np.abs(err))) if len(err) else None,
        "signed_error": float(np.mean(err)) if len(err) else None,
        "overshoot_rate": float(np.mean(sig[directional] == "overshoot")) if directional.any() else None,
        "undershoot_rate": float(np.mean(sig[directional] == "undershoot")) if directional.any() else None,
        "wrong_direction_rate": float(np.mean(sig[directional] == "wrong")) if directional.any() else None,
        "unchanged_rate": float(np.mean(sig == "unchanged")) if len(sig) else None,
        "average_abs_adjustment": float(np.mean(np.abs(applied))),
        "actual_result_mae": float(np.nanmean(actual_err)),
    }
    return out, pred, applied, lam, sig, clv


def score_key(m):
    def n(v, fallback): return fallback if v is None or not np.isfinite(v) else v
    return (-n(m["direction_accuracy"], -1), -n(m["positive_clv_rate"], -1), -n(m["average_clv"], -999), -n(m["median_clv"], -999), n(m["mae"], 999), n(m["overshoot_rate"], 1))


def monotonic_schedule(train, market, grid):
    sched = {}; last = max(grid)
    for _, _, label in STAGES:
        z = train[train.stage == label]
        ranked = []
        for lam in grid:
            spec = {"family": "constant", "lambda": min(lam, last)}
            m, *_ = metrics(z, market, spec)
            if m["direction_n"] >= 10: ranked.append((score_key(m), min(lam, last)))
        chosen = min(ranked)[1] if ranked else 0.0
        sched[label] = chosen; last = chosen
    return sched


def candidates(train, market):
    max_lam = .50 if market == "spread" else .85
    grid = [round(x, 2) for x in np.arange(0, max_lam + .001, .05)]
    specs = [{"name": "no_adjustment", "family": "none", "lambda": 0.0},
             {"name": "current_benchmark", "family": "constant", "lambda": max_lam}]
    specs += [{"name": f"constant_{x:.2f}", "family": "constant", "lambda": x} for x in grid]
    ws = monotonic_schedule(train, market, grid)
    specs.append({"name": "week_bucket_monotonic", "family": "week_bucket", "schedule": ws})
    gs = {}
    for _, _, label in GAME_STAGES:
        z = train[train.games_stage == label]; ranked = []
        for x in grid:
            m, *_ = metrics(z, market, {"family": "constant", "lambda": x})
            if m["direction_n"] >= 10: ranked.append((score_key(m), x))
        gs[label] = min(ranked)[1] if ranked else 0.0
    specs.append({"name": "games_bucket", "family": "games_bucket", "schedule": gs})
    for base in grid[1:]:
        for k in (.03, .06, .10, .15, .20): specs.append({"name": f"exp_{base}_{k}", "family": "exp_decay", "base": base, "k": k})
        for c in (.5, 1, 2, 4): specs.append({"name": f"sqrt_{base}_{c}", "family": "sqrt_decay", "base": base, "c": c})
    caps = ([1, 1.5, 2, 2.5, 3, 4] if market == "spread" else [1, 1.5, 2, 2.5, 3, 4, 5])
    bases = [s for s in specs if s["name"] in ("current_benchmark", "week_bucket_monotonic", "games_bucket")]
    for base in bases:
        for cap in caps:
            for typ in ("hard", "smooth"):
                q = dict(base); q.update(name=f"{base['name']}_{typ}_cap_{cap}", cap=cap, cap_type=typ); specs.append(q)
    return specs


def movement_tables(games):
    # Spread: canonical weekly market-implied rating history. Total: rolling market offense/defense state.
    hist = pd.read_csv(ROOT / "data/ratings/market_implied_ratings_history.csv", low_memory=False)
    hist = hist[hist.season.between(2021, 2025)].sort_values(["season", "team", "through_week"])
    hist["movement"] = hist.groupby(["season", "team"]).market_implied_rating.diff(); hist["market"] = "spread"
    hist = hist.rename(columns={"through_week": "completed_week", "games_used": "games_played"})
    total_mod = load_total_module(); eg = games[games.closing_total.notna() & games.closing_home_spread.notna()]
    models = total_mod.total_predictions(eg); trows = []
    for (season, week), m in models.items():
        for team in set(m["off"]) | set(m["def"]):
            trows.append({"season": season, "completed_week": week - 1, "team": team, "state": m["off"].get(team, 0) + m["def"].get(team, 0), "games_played": np.nan})
    th = pd.DataFrame(trows).sort_values(["season", "team", "completed_week"]); th["movement"] = th.groupby(["season", "team"]).state.diff(); th["market"] = "total"
    mv = pd.concat([hist[["season", "completed_week", "team", "games_played", "movement", "market"]], th], ignore_index=True)
    mv["target_week"] = mv.completed_week + 1; mv["stage"] = mv.target_week.map(stage); mv["games_stage"] = mv.games_played.fillna(0).map(game_stage)
    mv = mv[mv.movement.notna()].copy()
    def aggregate(keys):
        rows=[]
        for vals,z in mv.groupby(keys, dropna=False):
            vals = vals if isinstance(vals,tuple) else (vals,)
            a=z.movement.abs(); rows.append({**dict(zip(keys,vals)),"n":len(z),"mean_abs":a.mean(),"median_abs":a.median(),"p25_abs":a.quantile(.25),"p75_abs":a.quantile(.75),"p90_abs":a.quantile(.90),"signed_mean":z.movement.mean()})
        return pd.DataFrame(rows)
    return aggregate(["market","season","completed_week","target_week"]), aggregate(["market","season","stage"]), mv


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--strict", action="store_true"); args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True); REPORT.parent.mkdir(parents=True, exist_ok=True)
    public_before = repo_state()
    if public_before["status"]: raise SystemExit("Publication repository must be clean")
    before = protected_hashes()
    games = pd.read_csv(GAMES, low_memory=False); games = games[games.season.between(2021, 2025)].copy()
    games["game_id"] = games.game_id.map(norm_id)
    bases = baseline_rows(games); impacts = walk_forward_impacts(games)
    d = games.merge(bases, on="game_id", how="left").merge(impacts, on="game_id", how="left")
    # Week 1 has no completed Week 0 input and is not an eligible Saturday-to-next-week replay.
    d = d[d.week >= 2].copy()
    d["raw_spread"] = -d.raw_home_spread.fillna(0) + d.raw_away_spread.fillna(0)
    d["raw_total"] = d.raw_total.fillna(0); d["spread_update_count"] = d.spread_update_count.fillna(0).astype(int)
    d["closing_spread"] = d.closing_home_spread; d["opening_spread"] = d.opening_home_spread
    d["closing_total"] = d.closing_total; d["opening_total"] = d.opening_total
    d["stage"] = d.week.map(stage); d["games_stage"] = d.avg_games_played.fillna(0).map(game_stage)
    d["neutral_site"] = np.nan; d["location_status"] = "uncertain_not_in_historical_repository_source"; d["hfa_used"] = HFA
    d["favorite_role"] = np.where(d.closing_home_spread < 0, "home_favorite", np.where(d.closing_home_spread > 0, "away_favorite", "pickem"))
    d["prior_surprise_size"] = np.where(d.raw_spread.abs()<1,"small",np.where(d.raw_spread.abs()<3,"medium","large"))
    movement_week, movement_stage, movement_raw = movement_tables(games)
    movement_week.to_csv(OUT/"market_movement_by_week.csv", index=False); movement_stage.to_csv(OUT/"market_movement_by_stage.csv", index=False)
    movement_summary = {"definition":{"spread":"one-week change in canonical market-implied team rating","total":"one-week change in rolling offense-plus-defense market state"},"neutral_site":"not applicable to team-state movement; target-game neutral flags unavailable","rows":len(movement_raw)}
    (OUT/"market_movement_summary.json").write_text(json.dumps(movement_summary,indent=2)+"\n")

    train=d[d.season<=2023]; validation=d[d.season==2024]; holdout=d[d.season==2025]
    grid_rows=[]; selected={}; selection_results={}
    for market in ("spread","total"):
        specs=candidates(train,market); candidates_2024=[]
        for spec in specs:
            mt,*_=metrics(train,market,spec); mv,*_=metrics(validation,market,spec)
            row={"market":market,"name":spec["name"],"spec_json":json.dumps(spec,sort_keys=True),"candidate_count":len(specs),**{f"train_{k}":v for k,v in mt.items()},**{f"validation_{k}":v for k,v in mv.items()}}
            grid_rows.append(row); candidates_2024.append((score_key(mv),spec,mv))
        candidates_2024.sort(key=lambda x:x[0]); chosen=candidates_2024[0]
        selected[market]=chosen[1]; selection_results[market]={"selected":chosen[1],"validation":chosen[2],"candidates":len(specs)}
    grid_df=pd.DataFrame(grid_rows); grid_df.to_csv(OUT/"model_grid_results.csv",index=False)
    selection_lock=hashlib.sha256(json.dumps(selected,sort_keys=True).encode()).hexdigest()

    model_specs={"no_adjustment":{"spread":{"family":"none","lambda":0},"total":{"family":"none","lambda":0}},"current_benchmark":{"spread":{"family":"constant","lambda":.50},"total":{"family":"constant","lambda":.85}},"selected":selected}
    weekly=[]; stages=[]; game_audit=[]; holdout_rows=[]; size_rows=[]; tolerance_rows=[]
    for model_name,pair in model_specs.items():
        for market in ("spread","total"):
            spec=pair[market]
            for season_part,z in d.groupby("season"):
                m,pred,applied,lam,sig,clv=metrics(z,market,spec)
                if season_part==2025: holdout_rows.append({"model":model_name,"market":market,**m})
                for idx,(_,r) in enumerate(z.iterrows()):
                    if model_name=="selected":
                        game_audit.append({"season":int(r.season),"week":int(r.week),"game_id":r.game_id,"home_team":r.home_team,"away_team":r.away_team,"market":market,"baseline":r[f"{market}_baseline"],"raw_impact":r[f"raw_{market}"],"spread_update_count":int(r.spread_update_count),"both_prior_total":bool(r.both_prior_total) if pd.notna(r.both_prior_total) else False,"coefficient":lam[idx],"applied_impact":applied[idx],"projected_close":pred[idx],"opener":r[f"opening_{market}"],"actual_close":r[f"closing_{market}"],"signal_class":sig[idx],"clv":clv[idx] if np.isfinite(clv[idx]) else np.nan,"stage":r.stage,"games_stage":r.games_stage,"location_status":r.location_status,"hfa_used":r.hfa_used,"max_input_week":int(r.week)-1,"selection_partition":"locked_holdout" if r.season==2025 else ("validation" if r.season==2024 else "training")})
            for (season,week),z in d.groupby(["season","week"]):
                m,*_=metrics(z,market,spec); weekly.append({"model":model_name,"market":market,"season":season,"target_week":week,"stage":stage(week),"coefficient":json.dumps(spec,sort_keys=True),"cap":spec.get("cap"),**m})
            for (season,st),z in d.groupby(["season","stage"]):
                m,*_=metrics(z,market,spec); stages.append({"model":model_name,"market":market,"season":season,"stage":st,**m})
            if model_name=="selected":
                for tol in (.25,.5,1.0):
                    m,*_=metrics(holdout,market,spec,tol); tolerance_rows.append({"market":market,"tolerance":tol,**m})
                _,_,applied,_,_,_=metrics(d,market,spec)
                tmp=d.copy();tmp["abs_adjustment"]=abs(applied)
                tmp["adjustment_bucket"]=pd.cut(tmp.abs_adjustment,[-.001,.5,1,1.5,2,3,np.inf],labels=["0-0.5","0.5-1.0","1.0-1.5","1.5-2.0","2.0-3.0","3.0+"])
                for (season,b),z in tmp.groupby(["season","adjustment_bucket"],observed=True):
                    m,*_=metrics(z,market,spec);size_rows.append({"market":market,"season":season,"bucket":str(b),**m})
    pd.DataFrame(weekly).to_csv(OUT/"weekly_results.csv",index=False);pd.DataFrame(stages).to_csv(OUT/"stage_results.csv",index=False)
    pd.DataFrame(holdout_rows).to_csv(OUT/"holdout_2025_results.csv",index=False);pd.DataFrame(game_audit).to_csv(OUT/"game_level_audit.csv",index=False)
    pd.DataFrame(size_rows).to_csv(OUT/"adjustment_size_results.csv",index=False);pd.DataFrame(tolerance_rows).to_csv(OUT/"tolerance_sensitivity.csv",index=False)
    # Confidence analysis is deliberately descriptive, not an additional holdout-tuned selector.
    conf=[]
    ga=pd.DataFrame(game_audit)
    for market in ("spread","total"):
        z=ga[ga.market==market]
        for key,subset in [("one_team",z[z.spread_update_count==1] if market=="spread" else z.iloc[0:0]),("two_team",z[z.spread_update_count==2] if market=="spread" else z[z.both_prior_total]),("early",z[z.stage.isin(["Weeks 1-3","Weeks 4-6"])]),("late",z[z.stage.isin(["Weeks 10-12","Weeks 13+"])])]:
            if len(subset): conf.append({"market":market,"segment":key,"n":len(subset),"mean_abs_adjustment":subset.applied_impact.abs().mean(),"average_clv":subset.clv.mean(),"positive_clv_rate":float((subset.clv>.5).mean())})
    pd.DataFrame(conf).to_csv(OUT/"signal_confidence_results.csv",index=False)

    hold=pd.DataFrame(holdout_rows); stage_df=pd.DataFrame(stages); size_df=pd.DataFrame(size_rows)
    final={"schema_version":"shadow-season-stage-calibration-v1","built_at":datetime.now(timezone.utc).isoformat(),"split":{"training":[2021,2022,2023],"selection":2024,"locked_holdout":2025,"selection_lock_sha256":selection_lock},"formula_audit":{"spread":{"sign":"negative home spread means home favored","baseline":"six-week rolling ridge market ratings; target week uses prior weeks only","raw_update":"walk-forward ridge on score, closing spread, ATS margin, absolute closing spread","benchmark":"baseline + 0.50 * (-home raw team update + away raw team update)","hfa":HFA},"total":{"baseline":"six-week rolling market-implied offense versus opponent defense plus away offense versus home defense","raw_update":"walk-forward both-prior combined score and PBP ridge target","benchmark":"baseline + 0.85 * combined raw total update","separate_team_impacts":False,"pbp_fields":TOTAL_PBP_BASE}},"location_audit":{"resolved_neutral_games":0,"uncertain_games":len(d),"policy":"No repository historical neutral field exists. Rows are flagged uncertain; baseline uses validated legacy 2.5 HFA. Neutral-excluded sensitivity is unavailable rather than fabricated."},"opener_coverage":{str(y):{"spread":int(z.opening_home_spread.notna().sum()),"total":int(z.opening_total.notna().sum()),"games":len(z)} for y,z in d.groupby("season")},"selection":selection_results,"selected_formula":selected,"holdout_2025":hold.to_dict("records"),"tolerance_sensitivity":tolerance_rows,"candidate_count":int(len(grid_df)),"protected_before":before,"publication_before":public_before,"limitations":["Historical neutral-site flags are absent from repository sources.","2021-2022 opener coverage is effectively absent and 2023 is partial; direction and CLV use only observed opener rows.","Total update is combined both-prior and cannot be honestly separated into team-side impacts."]}
    (OUT/"final_selection.json").write_text(json.dumps(final,indent=2,default=lambda x:x.item() if hasattr(x,"item") else x)+"\n")
    # Compact local report, entirely driven by written research outputs.
    def table(df,cols):
        return "<table><thead><tr>"+"".join(f"<th>{html.escape(c)}</th>" for c in cols)+"</tr></thead><tbody>"+"".join("<tr>"+"".join(f"<td>{html.escape(str(r.get(c,'')))}</td>" for c in cols)+"</tr>" for r in df.to_dict('records'))+"</tbody></table>"
    selected_hold=hold[hold.model.isin(["no_adjustment","current_benchmark","selected"])]
    report=f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Shadow Season-Stage Calibration</title><style>body{{font:15px system-ui;background:#07152c;color:#eef4ff;margin:24px;max-width:100%}}h1,h2{{color:#fff}}.warn{{background:#402a12;border:1px solid #d99b38;padding:12px;border-radius:8px}}table{{border-collapse:collapse;width:100%;margin:12px 0 28px;display:block;overflow-x:auto}}th,td{{padding:8px;border:1px solid #294c72;text-align:left;white-space:nowrap}}th{{background:#17365f}}code{{color:#76e3ad}}</style></head><body><h1>Saturday Shadow Season-Stage Calibration</h1><div class='warn'>LOCAL RESEARCH ONLY. Historical neutral-site flags are unavailable; all locations are explicitly uncertain. 2021–22 opener coverage is effectively absent.</div><h2>Locked 2025 holdout</h2>{table(selected_hold,['model','market','n','direction_n','direction_accuracy','positive_clv_rate','average_clv','median_clv','mae','overshoot_rate'])}<h2>Selected formulas</h2><pre>{html.escape(json.dumps(selected,indent=2))}</pre><h2>Market movement by stage</h2>{table(movement_stage,['market','season','stage','n','mean_abs','median_abs','p75_abs','p90_abs','signed_mean'])}<h2>2025 results by stage</h2>{table(stage_df[(stage_df.season==2025)&stage_df.model.isin(['current_benchmark','selected'])],['model','market','stage','n','direction_accuracy','positive_clv_rate','average_clv','mae','overshoot_rate'])}<h2>Adjustment size</h2>{table(size_df[size_df.season==2025],['market','bucket','n','direction_accuracy','positive_clv_rate','average_clv','mae','overshoot_rate'])}</body></html>"""
    REPORT.write_text(report)
    after=protected_hashes(); public_after=repo_state(); final["protected_after"]=after;final["publication_after"]=public_after;final["protected_unchanged"]=before==after;final["publication_unchanged_clean"]=public_before==public_after and not public_after["status"]
    (OUT/"final_selection.json").write_text(json.dumps(final,indent=2,default=lambda x:x.item() if hasattr(x,"item") else x)+"\n")
    if args.strict and (before!=after or public_before!=public_after): raise SystemExit("Protected state changed")
    print(json.dumps({"selected":selected,"holdout":hold.to_dict('records'),"protected_unchanged":before==after,"publication_clean":not public_after['status'],"report":str(REPORT)},indent=2))


if __name__ == "__main__": main()
