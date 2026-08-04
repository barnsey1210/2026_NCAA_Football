#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
SOURCE = ROOT / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"
OUT = ROOT / "data/research/market_implied_ratings"
RATINGS_OUT = ROOT / "data/ratings/market_implied_ratings_history.csv"
LATEST_OUT = ROOT / "data/ratings/market_implied_ratings_latest.csv"
MATCHUPS_2026 = ROOT / "data/site/matchups_view.json"
TARGET_OUT = ROOT / "data/ratings/market_implied_target_excluded_2026.json"
PRODUCTION_AUDIT = ROOT / "data/research/market_implied_ratings/production_2026_audit.json"

HFA = 2.5
GRID = {
    "lookback_weeks": [4, 6, 8, 99],
    "half_life_weeks": [2.0, 4.0, 8.0],
    "ridge_alpha": [1.0, 5.0, 10.0, 20.0],
}

def norm_id(v):
    s = str(v or "").strip()
    return s[:-2] if s.endswith(".0") else s

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as f:
        f.write(text)
        tmp = Path(f.name)
    tmp.replace(path)

def atomic_csv(frame, path):
    atomic_text(path, frame.to_csv(index=False))

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def validate_source(df):
    needed = {
        "season", "week", "game_id", "home_team", "away_team",
        "closing_home_spread",
    }
    missing = needed - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns in {SOURCE}: {sorted(missing)}")

def fit_ratings(history, snapshot_week, lookback, half_life, alpha):
    h = history.copy()
    h = h[h.week <= snapshot_week].copy()
    if lookback < 90:
        h = h[h.week >= snapshot_week - lookback + 1].copy()

    teams = sorted(set(h.home_team).union(h.away_team))
    if not teams:
        return {}, {}, 0

    idx = {t: i for i, t in enumerate(teams)}
    X = np.zeros((len(h), len(teams)))
    y = np.zeros(len(h))
    w = np.ones(len(h))

    for row_i, r in enumerate(h.itertuples(index=False)):
        X[row_i, idx[r.home_team]] = 1.0
        X[row_i, idx[r.away_team]] = -1.0
        # closing_home_spread is negative when the home team is favored.
        y[row_i] = -float(r.closing_home_spread) - HFA
        age = max(0.0, snapshot_week - float(r.week))
        w[row_i] = 0.5 ** (age / half_life)

    # Ridge plus a strong sum-to-zero constraint for identifiability.
    WX = X * np.sqrt(w)[:, None]
    Wy = y * np.sqrt(w)
    A = WX.T @ WX + alpha * np.eye(len(teams))
    b = WX.T @ Wy
    A += 1000.0 * np.ones((len(teams), len(teams)))
    ratings = np.linalg.solve(A, b)

    games_used = {}
    eff_weight = {}
    for team in teams:
        mask = (h.home_team == team) | (h.away_team == team)
        games_used[team] = int(mask.sum())
        eff_weight[team] = float(w[mask.to_numpy()].sum())

    return (
        {team: float(ratings[idx[team]]) for team in teams},
        {
            team: {
                "games_used": games_used[team],
                "effective_games_weight": eff_weight[team],
            }
            for team in teams
        },
        len(h),
    )

def connected_components(games):
    graph = {}
    for r in games.itertuples(index=False):
        graph.setdefault(r.home_team, set()).add(r.away_team)
        graph.setdefault(r.away_team, set()).add(r.home_team)
    component = {}
    sizes = {}
    cid = 0
    for start in sorted(graph):
        if start in component:
            continue
        cid += 1
        stack = [start]
        members = []
        component[start] = cid
        while stack:
            team = stack.pop()
            members.append(team)
            for other in graph.get(team, ()):
                if other not in component:
                    component[other] = cid
                    stack.append(other)
        sizes[cid] = len(members)
    return component, sizes

def sample_status(games_used, component_size):
    if games_used <= 0:
        return "unavailable"
    if component_size <= 2:
        return "disconnected_component"
    if games_used == 1:
        return "early_one_game"
    if games_used <= 2:
        return "early_limited"
    if games_used <= 4:
        return "connected_low_sample"
    if games_used <= 7:
        return "connected_moderate_sample"
    return "established"

def load_2026_board():
    """Load the canonical, single-selected V2 market spread per scheduled game.

    The selection itself is owned by the existing odds/matchups builders. This
    function does not shop or average books again.
    """
    if not MATCHUPS_2026.exists():
        raise SystemExit(f"Missing canonical 2026 matchup market payload: {MATCHUPS_2026}")
    payload = json.loads(MATCHUPS_2026.read_text(encoding="utf-8"))
    rows = []
    rejected_completed = []
    for item in payload.get("games", []):
        game = item.get("game") or {}
        if int(game.get("season") or 2026) != 2026:
            continue
        spread = ((item.get("market") or {}).get("spread") or {})
        line = spread.get("home_line")
        if line is None:
            continue
        completed = bool(game.get("completed")) or str(game.get("status") or "").lower() in {"final", "completed", "complete"}
        # Upcoming games use the existing canonical selected current line. A
        # completed game must expose an explicit canonical close; current market
        # state is never relabeled as a close.
        if completed:
            close = game.get("closing_home_spread") or game.get("closing_spread_home")
            if close is None:
                rejected_completed.append(norm_id(game.get("game_id")))
                continue
            line = close
            line_kind = "completed_canonical_close"
        else:
            line_kind = "upcoming_canonical_current"
        rows.append({
            "season": 2026,
            "week": int(game.get("week") or 0),
            "game_id": norm_id(game.get("game_id")),
            "date": game.get("date"),
            "kickoff": game.get("kickoff") or game.get("start_date"),
            "away_team": game.get("away_team"),
            "home_team": game.get("home_team"),
            "neutral_site": bool(game.get("neutral_site")),
            "closing_home_spread": float(line),
            "line_kind": line_kind,
            "line_book": spread.get("book"),
            "line_timestamp": spread.get("updated_at"),
        })
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise SystemExit("No canonical 2026 market spreads were available.")
    frame = frame.drop_duplicates("game_id", keep="last")
    return frame, rejected_completed

def solve_2026(games, params, generated_at):
    snapshot_week = int(games.week.max())
    ratings, meta, source_games = fit_ratings(
        games, snapshot_week, params["lookback_weeks"], params["half_life_weeks"], params["ridge_alpha"]
    )
    components, component_sizes = connected_components(games)
    order = sorted(ratings, key=ratings.get, reverse=True)
    ranks = {team: i for i, team in enumerate(order, 1)}
    cutoff_values = pd.to_datetime(games.line_timestamp, errors="coerce", utc=True)
    board_cutoff = cutoff_values.max().isoformat() if cutoff_values.notna().any() else generated_at
    source_hash = sha256(MATCHUPS_2026)
    rows = []
    for team in order:
        cid = components.get(team)
        csize = component_sizes.get(cid, 1)
        used = int(meta[team]["games_used"])
        residual_rows = games[(games.home_team == team) | (games.away_team == team)]
        rows.append({
            "season": 2026, "through_week": snapshot_week,
            "snapshot_date": generated_at[:10], "snapshot_timestamp": generated_at,
            "board_cutoff": board_cutoff, "team": team,
            "market_implied_rating": ratings[team], "market_implied_rank": ranks[team],
            "games_used": used, "games_in_rating": used,
            "effective_games_weight": meta[team]["effective_games_weight"],
            "weighted_games_in_rating": meta[team]["effective_games_weight"],
            "connected_component_id": cid, "component_size": csize,
            "sample_status": sample_status(used, csize),
            "stability_proxy": 1.0 / math.sqrt(max(meta[team]["effective_games_weight"], 1e-9)),
            "source_game_count": source_games, "source_line_cutoff": board_cutoff,
            "source_hashes": source_hash, "model_version": "market-implied-rating-2026.1",
            "lookback_weeks": params["lookback_weeks"], "half_life_weeks": params["half_life_weeks"],
            "ridge_alpha": params["ridge_alpha"], "hfa": HFA,
            "training_games": source_games,
        })
    return pd.DataFrame(rows), ratings, board_cutoff

def target_excluded_solves(games, params, all_board, generated_at):
    all_meta = all_board.set_index("team").to_dict("index")
    rows = []
    for target in games.itertuples(index=False):
        pool = games[games.game_id != target.game_id].copy()
        snapshot_week = int(pool.week.max()) if not pool.empty else 0
        ratings, meta, _ = fit_ratings(pool, snapshot_week, params["lookback_weeks"], params["half_life_weeks"], params["ridge_alpha"])
        comp, sizes = connected_components(pool)
        away_games = int(meta.get(target.away_team, {}).get("games_used", 0))
        home_games = int(meta.get(target.home_team, {}).get("games_used", 0))
        same_component = comp.get(target.away_team) is not None and comp.get(target.away_team) == comp.get(target.home_team)
        component_size = sizes.get(comp.get(target.home_team), 0) if same_component else 0
        # Predeclared structural rule: each team must retain another game and
        # both must remain in the same component containing at least 3 teams.
        ready = away_games >= 1 and home_games >= 1 and same_component and component_size >= 3
        all_available = target.away_team in all_meta and target.home_team in all_meta
        if ready:
            state = "independent_market_ready"
            reason = "target excluded; both teams retain non-target support in the same 3+ team component"
            hfa = 0.0 if bool(target.neutral_site) else HFA
            fair = -(ratings[target.home_team] - ratings[target.away_team] + hfa)
        elif all_available:
            state = "market_context_only"
            reason = "target exclusion leaves one or both teams without independent connected market support"
            fair = None
        else:
            state = "market_unavailable"
            reason = "no usable all-board rating for one or both teams"
            fair = None
        rows.append({
            "game_id": target.game_id, "season": 2026, "week": int(target.week),
            "away_team": target.away_team, "home_team": target.home_team,
            "neutral_site": bool(target.neutral_site), "generated_at": generated_at,
            "target_game_excluded": True, "market_readiness_state": state,
            "market_readiness_reason": reason, "away_non_target_games": away_games,
            "home_non_target_games": home_games, "leave_one_out_component_size": component_size,
            "predicted_market_rating_spread": fair,
            "away_market_rating_entering": ratings.get(target.away_team),
            "home_market_rating_entering": ratings.get(target.home_team),
            "target_market_spread": float(target.closing_home_spread),
        })
    return rows

def evaluate_params(games, season, params):
    rows = []
    season_games = games[games.season == season].copy()
    for week in sorted(season_games.week.dropna().unique()):
        train = season_games[season_games.week < week]
        ratings, meta, n_train = fit_ratings(
            train,
            snapshot_week=int(week) - 1,
            lookback=params["lookback_weeks"],
            half_life=params["half_life_weeks"],
            alpha=params["ridge_alpha"],
        )
        current = season_games[season_games.week == week]
        for r in current.itertuples(index=False):
            if r.home_team not in ratings or r.away_team not in ratings:
                continue
            predicted_home_margin = (
                ratings[r.home_team] - ratings[r.away_team] + HFA
            )
            predicted_home_spread = -predicted_home_margin
            actual_close = float(r.closing_home_spread)
            rows.append({
                "season": int(r.season),
                "week": int(r.week),
                "game_id": norm_id(r.game_id),
                "home_team": r.home_team,
                "away_team": r.away_team,
                "predicted_home_spread": predicted_home_spread,
                "actual_closing_home_spread": actual_close,
                "error": predicted_home_spread - actual_close,
                "abs_error": abs(predicted_home_spread - actual_close),
                "training_games": n_train,
            })
    out = pd.DataFrame(rows)
    if out.empty:
        return {
            "n": 0, "mae": None, "rmse": None,
            "direction_accuracy": None, "correlation": None,
        }, out

    corr = None
    if out.predicted_home_spread.std() > 0 and out.actual_closing_home_spread.std() > 0:
        corr = float(out.predicted_home_spread.corr(out.actual_closing_home_spread))

    metrics = {
        "n": int(len(out)),
        "mae": float(out.abs_error.mean()),
        "rmse": float(np.sqrt(np.mean(out.error ** 2))),
        "direction_accuracy": float(
            np.mean(
                np.sign(out.predicted_home_spread)
                == np.sign(out.actual_closing_home_spread)
            )
        ),
        "correlation": corr,
    }
    return metrics, out

def select_params(games):
    grid_rows = []
    best = None
    for lookback in GRID["lookback_weeks"]:
        for half_life in GRID["half_life_weeks"]:
            for alpha in GRID["ridge_alpha"]:
                params = {
                    "lookback_weeks": lookback,
                    "half_life_weeks": half_life,
                    "ridge_alpha": alpha,
                }
                metrics, _ = evaluate_params(games, 2024, params)
                row = {**params, **metrics}
                grid_rows.append(row)
                if metrics["n"] and (
                    best is None
                    or metrics["mae"] < best["mae"]
                    or (
                        metrics["mae"] == best["mae"]
                        and metrics["rmse"] < best["rmse"]
                    )
                ):
                    best = row
    return best, pd.DataFrame(grid_rows).sort_values(["mae", "rmse"])

def build_history(games, params):
    rows = []
    for season in sorted(games.season.dropna().unique()):
        season_games = games[games.season == season].copy()
        for week in sorted(season_games.week.dropna().unique()):
            through = season_games[season_games.week <= week]
            ratings, meta, n_train = fit_ratings(
                through,
                snapshot_week=int(week),
                lookback=params["lookback_weeks"],
                half_life=params["half_life_weeks"],
                alpha=params["ridge_alpha"],
            )
            ordered = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
            ranks = {team: rank for rank, (team, _) in enumerate(ordered, 1)}
            for team, rating in ratings.items():
                rows.append({
                    "season": int(season),
                    "through_week": int(week),
                    "team": team,
                    "market_implied_rating": rating,
                    "market_implied_rank": ranks[team],
                    "games_used": meta[team]["games_used"],
                    "effective_games_weight": meta[team]["effective_games_weight"],
                    "lookback_weeks": params["lookback_weeks"],
                    "half_life_weeks": params["half_life_weeks"],
                    "ridge_alpha": params["ridge_alpha"],
                    "hfa": HFA,
                    "training_games": n_train,
                })
    hist = pd.DataFrame(rows)
    if not hist.empty:
        hist["market_move_1w"] = (
            hist.sort_values(["season", "team", "through_week"])
            .groupby(["season", "team"])["market_implied_rating"]
            .diff()
        )
        hist["market_move_4w"] = (
            hist.sort_values(["season", "team", "through_week"])
            .groupby(["season", "team"])["market_implied_rating"]
            .diff(4)
        )
    return hist

def historical_main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing source: {SOURCE}")

    games = pd.read_csv(SOURCE, low_memory=False)
    validate_source(games)
    games = games[
        games.closing_home_spread.notna()
        & games.home_team.notna()
        & games.away_team.notna()
    ].copy()

    games["season"] = pd.to_numeric(games["season"], errors="coerce")
    games["week"] = pd.to_numeric(games["week"], errors="coerce")
    games["closing_home_spread"] = pd.to_numeric(
        games["closing_home_spread"], errors="coerce"
    )
    games = games.dropna(
        subset=["season", "week", "closing_home_spread"]
    ).copy()
    games["season"] = games.season.astype(int)
    games["week"] = games.week.astype(int)

    best, grid = select_params(games)
    if best is None:
        raise SystemExit("No valid 2024 validation rows were generated.")

    params = {
        "lookback_weeks": int(best["lookback_weeks"]),
        "half_life_weeks": float(best["half_life_weeks"]),
        "ridge_alpha": float(best["ridge_alpha"]),
    }

    validation, validation_rows = evaluate_params(games, 2024, params)
    holdout, holdout_rows = evaluate_params(games, 2025, params)
    history = build_history(games, params)

    latest_season = int(history.season.max())
    latest_week = int(
        history.loc[history.season == latest_season, "through_week"].max()
    )
    latest = history[
        (history.season == latest_season)
        & (history.through_week == latest_week)
    ].copy().sort_values("market_implied_rank")

    OUT.mkdir(parents=True, exist_ok=True)
    RATINGS_OUT.parent.mkdir(parents=True, exist_ok=True)

    grid.to_csv(OUT / "parameter_grid_2024.csv", index=False)
    validation_rows.to_csv(OUT / "validation_2024_predictions.csv", index=False)
    holdout_rows.to_csv(OUT / "holdout_2025_predictions.csv", index=False)
    history.to_csv(RATINGS_OUT, index=False)
    latest.to_csv(LATEST_OUT, index=False)

    summary = {
        "schema_version": "market-implied-power-rating-backtest-v1",
        "rating_definition": (
            "Team strength inferred from closing spreads. Positive is stronger. "
            "Home closing margin is modeled as home rating minus away rating plus 2.5 HFA."
        ),
        "leakage_policy": (
            "Each game prediction uses closing lines from earlier weeks only. "
            "Weekly rating snapshots include games through that completed week."
        ),
        "parameter_selection": {
            "development": "2021-2023 available for future walk-forward expansion",
            "validation": 2024,
            "locked_holdout": 2025,
            "selected": params,
        },
        "validation_2024": validation,
        "holdout_2025": holdout,
        "latest_snapshot": {
            "season": latest_season,
            "through_week": latest_week,
            "teams": int(len(latest)),
        },
        "production_policy": {
            "blend_into_fundamental_rating": False,
            "display_separately": True,
            "primary_uses": [
                "market baseline for Saturday Shadow Line",
                "fundamental-versus-market disagreement",
                "market rating movement over time",
                "next-closing-line prediction",
            ],
        },
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(summary, indent=2))
    print("wrote:", OUT / "parameter_grid_2024.csv")
    print("wrote:", OUT / "validation_2024_predictions.csv")
    print("wrote:", OUT / "holdout_2025_predictions.csv")
    print("wrote:", RATINGS_OUT)
    print("wrote:", LATEST_OUT)
    print("wrote:", OUT / "summary.json")

def production_2026_main():
    grid_path = OUT / "parameter_grid_2024.csv"
    if not grid_path.exists():
        raise SystemExit(f"Missing locked parameter selection: {grid_path}")
    grid = pd.read_csv(grid_path)
    best = grid.sort_values(["mae", "rmse"]).iloc[0]
    params = {
        "lookback_weeks": int(best["lookback_weeks"]),
        "half_life_weeks": float(best["half_life_weeks"]),
        "ridge_alpha": float(best["ridge_alpha"]),
    }
    games, rejected_completed = load_2026_board()
    generated_at = utc_now()
    latest, _, board_cutoff = solve_2026(games, params, generated_at)
    targets = target_excluded_solves(games, params, latest, generated_at)

    if RATINGS_OUT.exists():
        history = pd.read_csv(RATINGS_OUT, low_memory=False)
        history = history[pd.to_numeric(history.get("season"), errors="coerce") != 2026].copy()
        for col in latest.columns:
            if col not in history.columns:
                history[col] = None
        for col in history.columns:
            if col not in latest.columns:
                latest[col] = None
        combined = pd.concat([history, latest[history.columns]], ignore_index=True)
    else:
        combined = latest.copy()

    # Historical rows are retained byte-for-data; only the current 2026 slice is replaced.
    atomic_csv(combined, RATINGS_OUT)
    atomic_csv(latest, LATEST_OUT)
    atomic_text(TARGET_OUT, json.dumps({
        "schema_version": "market-implied-target-excluded-2026-v1",
        "generated_at": generated_at,
        "board_cutoff": board_cutoff,
        "readiness_rule": "each team >=1 non-target game; same connected component; component size >=3",
        "fixture_only": False,
        "games": targets,
    }, indent=2) + "\n")
    states = pd.Series([r["market_readiness_state"] for r in targets]).value_counts().to_dict()
    audit = {
        "schema_version": "market-implied-production-2026-audit-v1",
        "generated_at": generated_at,
        "canonical_current_line_source": "data/site/matchups_view.json market.spread.home_line",
        "line_selection_owner": "existing odds builders and scripts/site/build_matchups_view.py; exactly one selected home-perspective spread per canonical game_id",
        "completed_close_policy": "only an explicit canonical closing_home_spread/closing_spread_home is eligible; current state is never relabeled as close",
        "rejected_completed_games_without_explicit_close": rejected_completed,
        "solver": "existing weighted ridge least squares, sum-to-zero constraint, HFA 2.5; neutral HFA 0 in target fair spread",
        "selected_parameters": params,
        "board_games": int(len(games)), "teams": int(len(latest)),
        "sample_status_distribution": latest.sample_status.value_counts().to_dict(),
        "component_size_distribution": latest.component_size.value_counts().sort_index().to_dict(),
        "readiness_distribution": states,
        "historical_rows_preserved": int(len(combined) - len(latest)),
    }
    atomic_text(PRODUCTION_AUDIT, json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))
    print("wrote:", LATEST_OUT)
    print("wrote:", RATINGS_OUT)
    print("wrote:", TARGET_OUT)
    print("wrote:", PRODUCTION_AUDIT)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--production-2026", action="store_true", help="Build current 2026 all-board and target-excluded states without refitting")
    args = ap.parse_args()
    if args.production_2026:
        production_2026_main()
    else:
        historical_main()

if __name__ == "__main__":
    main()
