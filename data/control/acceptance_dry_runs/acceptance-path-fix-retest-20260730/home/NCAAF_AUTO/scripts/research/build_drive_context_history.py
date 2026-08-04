#!/usr/bin/env python3
"""Build leakage-safe drive/field-position features from cached CFBD data."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


def read(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        x = json.load(f)
    return x.get("data", x) if isinstance(x, dict) else x


def competitive_drive(d: dict) -> bool:
    try:
        period = int(d.get("startPeriod") or 0)
        margin = abs(int(d.get("startOffenseScore") or 0) - int(d.get("startDefenseScore") or 0))
        plays = int(d.get("plays") or 0)
    except (TypeError, ValueError):
        return False
    if period < 1 or period > 4 or plays < 1:
        return False
    return period == 1 or margin <= {2: 38, 3: 28, 4: 22}.get(period, 10_000)


def ratio(num: float, den: float) -> float:
    return num / den if den else np.nan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache-root", type=Path, default=Path("cfbd_cache/pbp_history"))
    ap.add_argument("--base", type=Path, default=Path("data/research/pbp_history_2021_2025/team_game_tendencies.csv"))
    ap.add_argument("--output-dir", type=Path, default=Path("data/research/drive_context_2021_2025"))
    ap.add_argument("--seasons", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025])
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(args.base, usecols=["season", "week", "game_id", "team", "opponent"])
    valid_keys = set(zip(base.game_id.astype(int), base.team.astype(str)))
    rows = []
    audit = {}

    for season in args.seasons:
        root = args.cache_root / str(season)
        closest = {}
        for path in sorted(root.glob("plays_week_*.json.gz")):
            for p in read(path):
                drive_id, ytg = p.get("driveId"), p.get("yardsToGoal")
                if drive_id is None or ytg is None:
                    continue
                try: y = float(ytg)
                except (TypeError, ValueError): continue
                closest[str(drive_id)] = min(y, closest.get(str(drive_id), 1000.0))

        grouped = defaultdict(list)
        raw = read(root / "drives_regular.json.gz")
        excluded = 0
        for d in raw:
            game_id, offense, defense = d.get("gameId"), d.get("offense"), d.get("defense")
            if game_id is None or (int(game_id), str(offense)) not in valid_keys:
                continue
            if not competitive_drive(d):
                excluded += 1
                continue
            try:
                start_ytg = float(d.get("startYardsToGoal"))
                end_ytg = float(d.get("endYardsToGoal"))
                points = max(0.0, float(d.get("endOffenseScore") or 0) - float(d.get("startOffenseScore") or 0))
            except (TypeError, ValueError):
                continue
            if not 0 <= start_ytg <= 100:
                continue
            min_ytg = min(start_ytg, end_ytg if 0 <= end_ytg <= 100 else 100, closest.get(str(d.get("id")), 100))
            rec = {"start_ytg": start_ytg, "short": start_ytg <= 60, "opportunity": min_ytg <= 40,
                   "points": points, "opp_points": points if min_ytg <= 40 else 0.0,
                   "opp_td": points >= 6 if min_ytg <= 40 else False}
            grouped[(int(game_id), str(offense), str(defense))].append(rec)

        season_rows = 0
        for (game_id, offense, defense), drives in grouped.items():
            n = len(drives); opportunities = sum(x["opportunity"] for x in drives)
            values = {
                "season": season, "game_id": game_id, "team": offense, "opponent": defense,
                "off_drives": n, "off_start_ytg_sum": sum(x["start_ytg"] for x in drives),
                "off_short_fields": sum(x["short"] for x in drives), "off_opportunities": opportunities,
                "off_opportunity_points": sum(x["opp_points"] for x in drives),
                "off_opportunity_tds": sum(x["opp_td"] for x in drives),
                "off_points": sum(x["points"] for x in drives),
            }
            rows.append(values); season_rows += 1
        audit[str(season)] = {"raw_drives": len(raw), "excluded_or_non_fbs_drives": excluded,
                              "team_game_offense_rows": season_rows, "drives_with_pbp_position": len(closest)}

    off = pd.DataFrame(rows)
    # Mirror each offense row into the opponent's defensive context.
    defensive = off.rename(columns={
        "team": "opponent", "opponent": "team", "off_drives": "def_drives",
        "off_start_ytg_sum": "def_opponent_start_ytg_sum", "off_short_fields": "def_short_fields_allowed",
        "off_opportunities": "def_opportunities_allowed", "off_opportunity_points": "def_opportunity_points_allowed",
        "off_opportunity_tds": "def_opportunity_tds_allowed", "off_points": "def_points_allowed",
    })
    game = base.merge(off, on=["season", "game_id", "team", "opponent"], how="left")
    game = game.merge(defensive, on=["season", "game_id", "team", "opponent"], how="left")
    count_cols = [c for c in game if c.startswith("off_") or c.startswith("def_")]
    game[count_cols] = game[count_cols].fillna(0)
    game["off_avg_start_ytg"] = game.off_start_ytg_sum / game.off_drives.replace(0, np.nan)
    game["off_short_field_rate"] = game.off_short_fields / game.off_drives.replace(0, np.nan)
    game["off_opportunity_rate"] = game.off_opportunities / game.off_drives.replace(0, np.nan)
    game["off_points_per_opportunity"] = game.off_opportunity_points / game.off_opportunities.replace(0, np.nan)
    game["off_td_rate_per_opportunity"] = game.off_opportunity_tds / game.off_opportunities.replace(0, np.nan)
    game["off_points_per_drive"] = game.off_points / game.off_drives.replace(0, np.nan)
    game["def_opponent_avg_start_ytg"] = game.def_opponent_start_ytg_sum / game.def_drives.replace(0, np.nan)
    game["def_short_field_rate_allowed"] = game.def_short_fields_allowed / game.def_drives.replace(0, np.nan)
    game["def_opportunity_rate_allowed"] = game.def_opportunities_allowed / game.def_drives.replace(0, np.nan)
    game["def_points_per_opportunity_allowed"] = game.def_opportunity_points_allowed / game.def_opportunities_allowed.replace(0, np.nan)
    game["def_td_rate_per_opportunity_allowed"] = game.def_opportunity_tds_allowed / game.def_opportunities_allowed.replace(0, np.nan)
    game["def_points_per_drive_allowed"] = game.def_points_allowed / game.def_drives.replace(0, np.nan)

    # Cumulative component sums produce properly drive-weighted, pregame-only rates.
    rolling = []
    sums = ["off_drives", "off_start_ytg_sum", "off_short_fields", "off_opportunities", "off_opportunity_points",
            "off_opportunity_tds", "off_points", "def_drives", "def_opponent_start_ytg_sum", "def_short_fields_allowed",
            "def_opportunities_allowed", "def_opportunity_points_allowed", "def_opportunity_tds_allowed", "def_points_allowed"]
    for (season, team), g in game.sort_values(["season", "team", "week", "game_id"]).groupby(["season", "team"]):
        totals = {c: 0.0 for c in sums}; prior = 0
        for r in g.to_dict("records"):
            z = {"season": season, "week": r["week"], "game_id": r["game_id"], "team": team,
                 "opponent": r["opponent"], "prior_games": prior}
            z.update({f"prior_{c}": totals[c] for c in sums})
            z.update({
                "pregame_off_avg_start_ytg": ratio(totals["off_start_ytg_sum"], totals["off_drives"]),
                "pregame_off_short_field_rate": ratio(totals["off_short_fields"], totals["off_drives"]),
                "pregame_off_opportunity_rate": ratio(totals["off_opportunities"], totals["off_drives"]),
                "pregame_off_points_per_opportunity": ratio(totals["off_opportunity_points"], totals["off_opportunities"]),
                "pregame_off_td_rate_per_opportunity": ratio(totals["off_opportunity_tds"], totals["off_opportunities"]),
                "pregame_off_points_per_drive": ratio(totals["off_points"], totals["off_drives"]),
                "pregame_def_opponent_avg_start_ytg": ratio(totals["def_opponent_start_ytg_sum"], totals["def_drives"]),
                "pregame_def_short_field_rate_allowed": ratio(totals["def_short_fields_allowed"], totals["def_drives"]),
                "pregame_def_opportunity_rate_allowed": ratio(totals["def_opportunities_allowed"], totals["def_drives"]),
                "pregame_def_points_per_opportunity_allowed": ratio(totals["def_opportunity_points_allowed"], totals["def_opportunities_allowed"]),
                "pregame_def_td_rate_per_opportunity_allowed": ratio(totals["def_opportunity_tds_allowed"], totals["def_opportunities_allowed"]),
                "pregame_def_points_per_drive_allowed": ratio(totals["def_points_allowed"], totals["def_drives"]),
            })
            rolling.append(z)
            for c in sums: totals[c] += float(r[c])
            prior += 1

    rolling = pd.DataFrame(rolling)
    game.to_csv(args.output_dir / "team_game_drive_context.csv", index=False)
    rolling.to_csv(args.output_dir / "rolling_pregame_drive_context.csv", index=False)
    audit.update({"team_game_rows": len(game), "rolling_rows": len(rolling), "unique_games": int(game.game_id.nunique()),
                  "notes": ["Regulation only; same garbage-time thresholds as PBP tendencies.",
                            "Opportunity means a drive reached the opponent 40-yard line.",
                            "Short field means a drive started 60 or fewer yards from goal.",
                            "All rolling features use prior games in the same season only."]})
    (args.output_dir / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
