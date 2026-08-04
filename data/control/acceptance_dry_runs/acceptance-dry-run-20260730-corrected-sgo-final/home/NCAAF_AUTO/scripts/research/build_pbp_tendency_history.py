#!/usr/bin/env python3
"""Build leakage-safe 2021-2025 team-game and rolling PBP tendencies."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from pilot_cfbd_pbp_tendencies import (
    METRIC_COLUMNS,
    flatten_advanced,
    flatten_havoc,
    is_scrimmage,
    mean,
    summarize_defense,
    summarize_offense,
)


ADJUSTMENT_METRICS = {
    "neutral_pass": "off_neutral_pass_rate",
    "success": "off_success_rate",
    "explosiveness": "off_explosiveness",
    "ppa": "off_ppa",
    "pace_seconds": "off_drive_elapsed_seconds_per_play",
}

ROLLING_METRICS = [
    column for column in METRIC_COLUMNS if column != "off_game_clock_seconds_per_play"
] + ["off_drive_elapsed_seconds_per_play"]


def read_gzip(path: Path) -> Any:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def group_plays(rows: List[Dict[str, Any]], fbs: set[str]) -> Tuple[Dict[Tuple[int, str], List[Dict[str, Any]]], Dict[Tuple[int, str], List[Dict[str, Any]]]]:
    offense: Dict[Tuple[int, str], List[Dict[str, Any]]] = defaultdict(list)
    defense: Dict[Tuple[int, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        game_id = row.get("gameId")
        if game_id is None:
            continue
        if row.get("offense") in fbs:
            offense[(int(game_id), str(row["offense"]))].append(row)
        if row.get("defense") in fbs:
            defense[(int(game_id), str(row["defense"]))].append(row)
    return offense, defense


def is_competitive_play(play: Dict[str, Any]) -> bool:
    """Conservative garbage-time filter; overtime is excluded from style features."""
    try:
        period = int(play.get("period") or 0)
        margin = abs(int(play.get("offenseScore") or 0) - int(play.get("defenseScore") or 0))
    except (TypeError, ValueError):
        return True
    if period <= 0:
        return True
    if period > 4:
        return False
    thresholds = {2: 38, 3: 28, 4: 22}
    return period == 1 or margin <= thresholds.get(period, 10_000)


def drive_pace_by_game(rows: List[Dict[str, Any]], fbs: set[str]) -> Dict[Tuple[int, str], float]:
    totals: Dict[Tuple[int, str], List[float]] = defaultdict(lambda: [0.0, 0.0])
    for row in rows:
        game_id, team = row.get("gameId"), row.get("offense")
        if game_id is None or team not in fbs:
            continue
        start = row.get("startTime") or {}
        end = row.get("endTime") or {}
        try:
            start_period = int(row.get("startPeriod") or 0)
            end_period = int(row.get("endPeriod") or 0)
            start_clock = int(start.get("minutes") or 0) * 60 + int(start.get("seconds") or 0)
            end_clock = int(end.get("minutes") or 0) * 60 + int(end.get("seconds") or 0)
            plays = int(row.get("plays") or 0)
        except (TypeError, ValueError):
            continue
        if start_period <= 0 or end_period <= 0 or end_period < start_period:
            continue
        start_margin = abs(int(row.get("startOffenseScore") or 0) - int(row.get("startDefenseScore") or 0))
        garbage_thresholds = {2: 38, 3: 28, 4: 22}
        if start_period > 4 or (start_period in garbage_thresholds and start_margin > garbage_thresholds[start_period]):
            continue
        if start_period == end_period:
            seconds = start_clock - end_clock
        elif start_period <= 4 and end_period <= 4:
            seconds = start_clock + max(0, end_period - start_period - 1) * 900 + (900 - end_clock)
        else:
            continue
        if 0 <= seconds <= 1800 and plays > 0:
            totals[(int(game_id), str(team))][0] += seconds
            totals[(int(game_id), str(team))][1] += plays
    return {key: value[0] / value[1] for key, value in totals.items() if value[1] > 0}


def expanding_means(game_df: pd.DataFrame) -> pd.DataFrame:
    columns = [c for c in ROLLING_METRICS if c in game_df.columns]
    output: List[Dict[str, Any]] = []
    for (season, team), group in game_df.sort_values(["season", "team", "week", "game_id"]).groupby(["season", "team"]):
        history: List[Dict[str, Any]] = []
        for row in group.to_dict("records"):
            record = {
                "season": season, "week": row["week"], "game_id": row["game_id"],
                "team": team, "opponent": row["opponent"], "prior_games": len(history),
            }
            for column in columns:
                record[f"pregame_{column}"] = mean(h.get(column) for h in history)
            output.append(record)
            history.append(row)
    return pd.DataFrame(output)


def shrunk_two_way_effects(
    frame: pd.DataFrame,
    value_col: str,
    actor_col: str,
    context_col: str,
    prior_weight: float = 3.0,
    iterations: int = 12,
) -> Tuple[float, Dict[str, float], Dict[str, float], Dict[str, int], Dict[str, int]]:
    data = frame[[value_col, actor_col, context_col]].dropna().copy()
    if data.empty:
        return np.nan, {}, {}, {}, {}
    data[value_col] = pd.to_numeric(data[value_col], errors="coerce")
    data = data.dropna(subset=[value_col])
    mu = float(data[value_col].mean())
    actors = data[actor_col].astype(str)
    contexts = data[context_col].astype(str)
    actor_effect = {name: 0.0 for name in actors.unique()}
    context_effect = {name: 0.0 for name in contexts.unique()}
    actor_n = actors.value_counts().to_dict()
    context_n = contexts.value_counts().to_dict()
    for _ in range(iterations):
        actor_residual = data[value_col] - mu - contexts.map(context_effect).fillna(0.0)
        raw_actor = actor_residual.groupby(actors).mean()
        actor_effect = {
            name: float(value) * actor_n[name] / (actor_n[name] + prior_weight)
            for name, value in raw_actor.items()
        }
        context_residual = data[value_col] - mu - actors.map(actor_effect).fillna(0.0)
        raw_context = context_residual.groupby(contexts).mean()
        context_effect = {
            name: float(value) * context_n[name] / (context_n[name] + prior_weight)
            for name, value in raw_context.items()
        }
    return mu, actor_effect, context_effect, actor_n, context_n


def add_opponent_adjustments(game_df: pd.DataFrame, rolling_df: pd.DataFrame) -> pd.DataFrame:
    adjusted = rolling_df.copy()
    for season in sorted(game_df["season"].unique()):
        season_games = game_df[game_df["season"].eq(season)].copy()
        for week in sorted(season_games["week"].unique()):
            target_mask = adjusted["season"].eq(season) & adjusted["week"].eq(week)
            history = season_games[season_games["week"].lt(week)]
            if history.empty:
                continue
            target = adjusted.loc[target_mask]
            for label, column in ADJUSTMENT_METRICS.items():
                mu, offense, defense, offense_n, defense_n = shrunk_two_way_effects(
                    history, column, "team", "opponent"
                )
                adjusted.loc[target_mask, f"league_{label}"] = mu
                adjusted.loc[target_mask, f"pregame_adj_off_{label}_effect"] = target["team"].map(offense)
                adjusted.loc[target_mask, f"pregame_adj_def_{label}_allowed_effect"] = target["team"].map(defense)
                adjusted.loc[target_mask, f"matchup_expected_off_{label}"] = (
                    mu + target["team"].map(offense).fillna(0.0) + target["opponent"].map(defense).fillna(0.0)
                )
                adjusted.loc[target_mask, f"adj_off_{label}_games"] = target["team"].map(offense_n).fillna(0)
                adjusted.loc[target_mask, f"adj_def_{label}_games"] = target["team"].map(defense_n).fillna(0)

            mu, defense, offense_allowed, defense_n, offense_n = shrunk_two_way_effects(
                history, "def_havoc_rate", "team", "opponent"
            )
            adjusted.loc[target_mask, "league_havoc"] = mu
            adjusted.loc[target_mask, "pregame_adj_def_havoc_effect"] = target["team"].map(defense)
            adjusted.loc[target_mask, "pregame_adj_off_havoc_allowed_effect"] = target["team"].map(offense_allowed)
            adjusted.loc[target_mask, "matchup_expected_def_havoc"] = (
                mu + target["team"].map(defense).fillna(0.0) + target["opponent"].map(offense_allowed).fillna(0.0)
            )
            adjusted.loc[target_mask, "adj_def_havoc_games"] = target["team"].map(defense_n).fillna(0)
            adjusted.loc[target_mask, "adj_off_havoc_allowed_games"] = target["team"].map(offense_n).fillna(0)
    return adjusted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025])
    parser.add_argument("--cache-root", type=Path, default=Path("cfbd_cache/pbp_history"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/research/pbp_history_2021_2025"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    all_rows: List[Dict[str, Any]] = []
    coverage: Dict[str, Any] = {}
    for season in args.seasons:
        root = args.cache_root / str(season)
        teams = read_gzip(root / "teams_fbs.json.gz")
        fbs = {str(row.get("school")) for row in teams if row.get("school")}
        advanced = read_gzip(root / "advanced_regular.json.gz")
        havoc = read_gzip(root / "havoc_regular.json.gz")
        drives = read_gzip(root / "drives_regular.json.gz")
        drive_pace = drive_pace_by_game(drives, fbs)
        advanced_by_week: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for row in advanced:
            if row.get("team") in fbs and row.get("gameId") is not None:
                advanced_by_week[int(row.get("week") or 0)].append(row)
        havoc_map = {
            (int(row["gameId"]), str(row["team"])): row for row in havoc
            if row.get("gameId") is not None and row.get("team") in fbs
        }
        season_rows = 0
        pbp_missing = 0
        for play_path in sorted(root.glob("plays_week_*.json.gz")):
            week = int(play_path.stem.split("_")[-1].split(".")[0])
            plays = read_gzip(play_path)
            offense_map, defense_map = group_plays(plays, fbs)
            for adv in advanced_by_week.get(week, []):
                game_id, team = int(adv["gameId"]), str(adv["team"])
                offense_plays = offense_map.get((game_id, team), [])
                defense_plays = defense_map.get((game_id, team), [])
                if not offense_plays or not defense_plays:
                    pbp_missing += 1
                row: Dict[str, Any] = {
                    "season": season, "week": week, "game_id": game_id,
                    "team": team, "opponent": str(adv.get("opponent") or ""),
                }
                raw_off_scrimmage = sum(is_scrimmage(play) for play in offense_plays)
                raw_def_scrimmage = sum(is_scrimmage(play) for play in defense_plays)
                competitive_offense = [play for play in offense_plays if is_competitive_play(play)]
                competitive_defense = [play for play in defense_plays if is_competitive_play(play)]
                row.update(summarize_offense(team, competitive_offense))
                row["off_raw_scrimmage_plays"] = raw_off_scrimmage
                row["off_excluded_garbage_or_ot_plays"] = raw_off_scrimmage - row["off_plays"]
                raw_drive_pace = drive_pace.get((game_id, team))
                row["off_drive_elapsed_seconds_per_play_raw"] = raw_drive_pace
                row["off_drive_elapsed_seconds_per_play"] = (
                    raw_drive_pace if raw_drive_pace is not None and 12 <= raw_drive_pace <= 45 else None
                )
                row.update(summarize_defense(competitive_defense))
                row["def_raw_scrimmage_plays"] = raw_def_scrimmage
                row["def_excluded_garbage_or_ot_plays"] = raw_def_scrimmage - row["def_plays"]
                row.update(flatten_advanced(adv))
                row.update(flatten_havoc(havoc_map.get((game_id, team))))
                all_rows.append(row)
                season_rows += 1
            del plays, offense_map, defense_map
        coverage[str(season)] = {
            "fbs_teams": len(fbs), "advanced_team_games": sum(map(len, advanced_by_week.values())),
            "output_team_games": season_rows, "team_games_missing_offense_or_defense_pbp": pbp_missing,
            "havoc_team_games": len(havoc_map),
            "drive_pace_team_games": len(drive_pace),
        }
        print(season, coverage[str(season)])

    game_df = pd.DataFrame(all_rows).drop_duplicates(["season", "game_id", "team"])
    game_df = game_df.sort_values(["season", "team", "week", "game_id"])
    game_df["off_play_count_diff_vs_advanced"] = game_df["off_raw_scrimmage_plays"] - pd.to_numeric(game_df["adv_off_plays"], errors="coerce")
    game_df["def_play_count_diff_vs_advanced"] = game_df["def_raw_scrimmage_plays"] - pd.to_numeric(game_df["adv_def_plays"], errors="coerce")
    rolling_df = expanding_means(game_df)
    adjusted_df = add_opponent_adjustments(game_df, rolling_df)

    game_path = args.output_dir / "team_game_tendencies.csv"
    rolling_path = args.output_dir / "rolling_pregame_tendencies.csv"
    adjusted_path = args.output_dir / "rolling_pregame_opponent_adjusted.csv"
    audit_path = args.output_dir / "audit.json"
    game_df.to_csv(game_path, index=False)
    rolling_df.to_csv(rolling_path, index=False)
    adjusted_df.to_csv(adjusted_path, index=False)
    audit = {
        "seasons": args.seasons, "coverage": coverage,
        "team_game_rows": len(game_df), "rolling_rows": len(rolling_df), "adjusted_rows": len(adjusted_df),
        "unique_games": int(game_df["game_id"].nunique()), "unique_teams": int(game_df["team"].nunique()),
        "off_play_exact_match_rate": float(game_df["off_play_count_diff_vs_advanced"].eq(0).mean()),
        "def_play_exact_match_rate": float(game_df["def_play_count_diff_vs_advanced"].eq(0).mean()),
        "off_play_within_2_rate": float(game_df["off_play_count_diff_vs_advanced"].abs().le(2).mean()),
        "def_play_within_2_rate": float(game_df["def_play_count_diff_vs_advanced"].abs().le(2).mean()),
        "valid_drive_pace_rows": int(game_df["off_drive_elapsed_seconds_per_play"].notna().sum()),
        "invalid_drive_pace_rows": int(game_df["off_drive_elapsed_seconds_per_play"].isna().sum()),
        "off_competitive_scrimmage_plays": int(game_df["off_plays"].sum()),
        "off_excluded_garbage_or_ot_plays": int(game_df["off_excluded_garbage_or_ot_plays"].sum()),
        "off_excluded_garbage_or_ot_rate": float(
            game_df["off_excluded_garbage_or_ot_plays"].sum() / game_df["off_raw_scrimmage_plays"].sum()
        ),
        "notes": [
            "No betting results or markets were loaded.",
            "Every rolling and opponent-adjusted row uses games from earlier weeks only.",
            "Opponent adjustment is an iterative regularized two-way actor/context model with a 3-game prior weight.",
            "Positive defensive pass-tendency effect means opponents pass more than expected (pass-funnel direction).",
            "Positive defensive success/PPA/explosiveness allowed effects are worse; positive defensive havoc effect is better.",
            "Drive pace retains a raw audit field; values outside 12-45 seconds/play are excluded as corrupted clocks.",
            "Garbage time is excluded when the pre-play margin exceeds 38 in Q2, 28 in Q3, or 22 in Q4; overtime is excluded.",
        ],
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    print("wrote", game_path, rolling_path, adjusted_path, audit_path, sep="\n")


if __name__ == "__main__":
    main()
