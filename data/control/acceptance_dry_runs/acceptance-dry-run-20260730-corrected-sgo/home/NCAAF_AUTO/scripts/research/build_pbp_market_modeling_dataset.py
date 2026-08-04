#!/usr/bin/env python3
"""Join leakage-safe PBP features to CFBD historical full-game markets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


PROVIDER_PRIORITY = [
    "consensus", "ESPN Bet", "DraftKings", "Draft Kings",
    "William Hill (New Jersey)", "Bovada", "teamrankings",
    "Caesars Sportsbook (Colorado)", "Caesars (Pennsylvania)",
]


def provider_rank(name: str) -> int:
    try:
        return PROVIDER_PRIORITY.index(name)
    except ValueError:
        return len(PROVIDER_PRIORITY) + 1


def split_name(season: int) -> str:
    if season <= 2023:
        return "development"
    if season == 2024:
        return "validation"
    return "locked_test"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--features",
        type=Path,
        default=Path("data/research/pbp_history_2021_2025/rolling_pregame_opponent_adjusted.csv"),
    )
    parser.add_argument(
        "--line-cache", type=Path, default=Path("cfbd_cache/coach_full_game_fav_dog")
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/research/pbp_market_modeling_2021_2025")
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    features = pd.read_csv(args.features, low_memory=False)
    provider_rows: List[Dict[str, Any]] = []
    games: List[Dict[str, Any]] = []
    for season in range(2021, 2026):
        raw = json.loads((args.line_cache / f"lines_{season}_regular.json").read_text(encoding="utf-8"))
        for game in raw:
            base = {
                "game_id": int(game["id"]), "season": int(game["season"]),
                "week": int(game.get("week") or 0), "start_date": game.get("startDate"),
                "home_team": game.get("homeTeam"), "away_team": game.get("awayTeam"),
                "home_score": game.get("homeScore"), "away_score": game.get("awayScore"),
            }
            nested = []
            for line in game.get("lines") or []:
                row = {
                    **base, "provider": line.get("provider"),
                    "closing_home_spread": line.get("spread"),
                    "opening_home_spread": line.get("spreadOpen"),
                    "closing_total": line.get("overUnder"),
                    "opening_total": line.get("overUnderOpen"),
                    "home_moneyline": line.get("homeMoneyline"),
                    "away_moneyline": line.get("awayMoneyline"),
                }
                provider_rows.append(row)
                nested.append(row)
            usable = [r for r in nested if r["closing_home_spread"] is not None and r["closing_total"] is not None]
            if usable:
                usable.sort(key=lambda r: (provider_rank(str(r["provider"])), str(r["provider"])))
                games.append(dict(usable[0]))

    provider_df = pd.DataFrame(provider_rows)
    market_df = pd.DataFrame(games).drop_duplicates("game_id")
    home_features = features.add_prefix("home_").rename(columns={"home_game_id": "game_id"})
    away_features = features.add_prefix("away_").rename(columns={"away_game_id": "game_id"})
    model = market_df.merge(home_features, on="game_id", how="inner")
    model = model[model["home_team_x"].eq(model["home_team_y"])].copy()
    model = model.rename(columns={"home_team_x": "home_team"}).drop(columns=["home_team_y"])
    model = model.merge(away_features, on="game_id", how="inner")
    model = model[model["away_team_x"].eq(model["away_team_y"])].copy()
    model = model.rename(columns={"away_team_x": "away_team"}).drop(columns=["away_team_y"])

    model["home_score"] = pd.to_numeric(model["home_score"], errors="coerce")
    model["away_score"] = pd.to_numeric(model["away_score"], errors="coerce")
    for column in ["closing_home_spread", "opening_home_spread", "closing_total", "opening_total"]:
        model[column] = pd.to_numeric(model[column], errors="coerce")
    model["actual_home_margin"] = model["home_score"] - model["away_score"]
    model["actual_total_points"] = model["home_score"] + model["away_score"]
    model["closing_spread_residual"] = model["actual_home_margin"] + model["closing_home_spread"]
    model["closing_total_residual"] = model["actual_total_points"] - model["closing_total"]
    model["spread_move_close_minus_open"] = model["closing_home_spread"] - model["opening_home_spread"]
    model["total_move_close_minus_open"] = model["closing_total"] - model["opening_total"]
    model["split"] = model["season"].map(split_name)
    model["minimum_prior_games"] = model[["home_prior_games", "away_prior_games"]].min(axis=1)
    model["eligible_week5_plus"] = model["minimum_prior_games"].ge(4)

    provider_path = args.output_dir / "provider_market_rows.csv"
    model_path = args.output_dir / "full_game_modeling_rows.csv"
    audit_path = args.output_dir / "audit.json"
    provider_df.to_csv(provider_path, index=False)
    model.to_csv(model_path, index=False)
    audit = {
        "provider_rows": len(provider_df), "selected_market_games": len(market_df),
        "joined_fbs_vs_fbs_games": len(model),
        "development_games": int(model["split"].eq("development").sum()),
        "validation_games": int(model["split"].eq("validation").sum()),
        "locked_test_games": int(model["split"].eq("locked_test").sum()),
        "week5_plus_games": int(model["eligible_week5_plus"].sum()),
        "games_with_opening_spread": int(model["opening_home_spread"].notna().sum()),
        "games_with_opening_total": int(model["opening_total"].notna().sum()),
        "notes": [
            "2021-2023 is development, 2024 is validation, and 2025 is locked_test.",
            "No model fitting or performance analysis is performed by this script.",
            "Spread is home-team oriented; ATS residual is actual home margin plus home spread.",
            "Opening-to-closing movement uses the same selected provider row.",
        ],
    }
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    print("wrote", provider_path, model_path, audit_path, sep="\n")


if __name__ == "__main__":
    main()
