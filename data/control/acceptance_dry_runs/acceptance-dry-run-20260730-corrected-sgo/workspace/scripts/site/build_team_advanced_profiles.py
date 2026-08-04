#!/usr/bin/env python3

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(".")
SOURCE = (
    ROOT
    / "data/research/pbp_history_2021_2025"
    / "rolling_pregame_opponent_adjusted.csv"
)
RATINGS_VIEW = ROOT / "data/site/ratings_view.json"
OUTPUT = ROOT / "data/site/team_advanced_profiles.json"
AUDIT = ROOT / "data/audit/team_advanced_profiles_audit.json"

SOURCE_SEASON = 2025


METRICS = {
    "offense": {
        "success_rate": {
            "raw": "pregame_off_success_rate",
            "adjusted": "pregame_adj_off_success_effect",
            "sample": "adj_off_success_games",
            "direction": "higher",
            "format": "percentage",
            "description": "Offensive success rate and opponent-adjusted offensive success effect.",
        },
        "ppa": {
            "raw": "pregame_off_ppa",
            "adjusted": "pregame_adj_off_ppa_effect",
            "sample": "adj_off_ppa_games",
            "direction": "higher",
            "format": "decimal",
            "description": "Offensive predicted points added per play.",
        },
        "explosiveness": {
            "raw": "pregame_off_explosiveness",
            "adjusted": "pregame_adj_off_explosiveness_effect",
            "sample": "adj_off_explosiveness_games",
            "direction": "higher",
            "format": "decimal",
            "description": "Average PPA generated on successful offensive plays.",
        },
        "rush_success_rate": {
            "raw": "pregame_off_rush_success_rate",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "higher",
            "format": "percentage",
            "description": "Offensive rushing success rate.",
        },
        "pass_success_rate": {
            "raw": "pregame_off_pass_success_rate",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "higher",
            "format": "percentage",
            "description": "Offensive passing success rate.",
        },
        "explosive_rush_rate": {
            "raw": "pregame_off_explosive_rush_rate",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "higher",
            "format": "percentage",
            "description": "Rate of rushing plays gaining at least 10 yards.",
        },
        "explosive_pass_rate": {
            "raw": "pregame_off_explosive_pass_rate",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "higher",
            "format": "percentage",
            "description": "Rate of passing plays gaining at least 20 yards.",
        },
        "neutral_pass_rate": {
            "raw": "pregame_off_neutral_pass_rate",
            "adjusted": "pregame_adj_off_neutral_pass_effect",
            "sample": "adj_off_neutral_pass_games",
            "direction": "style",
            "format": "percentage",
            "description": "Pass tendency in neutral game situations.",
        },
        "early_down_pass_rate": {
            "raw": "pregame_off_early_down_pass_rate",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "style",
            "format": "percentage",
            "description": "Passing frequency on early downs.",
        },
        "qb_run_share": {
            "raw": "pregame_off_qb_run_share",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "style",
            "format": "percentage",
            "description": "Quarterback share of designed and scramble rushing attempts.",
        },
        "pace_seconds": {
            "raw": "pregame_off_drive_elapsed_seconds_per_play",
            "adjusted": "pregame_adj_off_pace_seconds_effect",
            "sample": "adj_off_pace_seconds_games",
            "direction": "lower",
            "format": "seconds",
            "description": "Average offensive seconds per play; lower values indicate faster pace.",
        },
    },
    "defense": {
        "success_rate_allowed": {
            "raw": "pregame_def_success_allowed",
            "adjusted": "pregame_adj_def_success_allowed_effect",
            "sample": "adj_def_success_games",
            "direction": "lower",
            "format": "percentage",
            "description": "Defensive success rate allowed.",
        },
        "ppa_allowed": {
            "raw": "pregame_def_ppa_allowed",
            "adjusted": "pregame_adj_def_ppa_allowed_effect",
            "sample": "adj_def_ppa_games",
            "direction": "lower",
            "format": "decimal",
            "description": "Defensive PPA allowed per play.",
        },
        "explosiveness_allowed": {
            "raw": "pregame_def_explosiveness_allowed",
            "adjusted": "pregame_adj_def_explosiveness_allowed_effect",
            "sample": "adj_def_explosiveness_games",
            "direction": "lower",
            "format": "decimal",
            "description": "Average PPA allowed on successful opponent plays.",
        },
        "rush_success_allowed": {
            "raw": "pregame_def_rush_success_allowed",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "lower",
            "format": "percentage",
            "description": "Rushing success rate allowed.",
        },
        "pass_success_allowed": {
            "raw": "pregame_def_pass_success_allowed",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "lower",
            "format": "percentage",
            "description": "Passing success rate allowed.",
        },
        "explosive_rush_allowed": {
            "raw": "pregame_def_explosive_rush_allowed",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "lower",
            "format": "percentage",
            "description": "Rate of opponent rushing plays gaining at least 10 yards.",
        },
        "explosive_pass_allowed": {
            "raw": "pregame_def_explosive_pass_allowed",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "lower",
            "format": "percentage",
            "description": "Rate of opponent passing plays gaining at least 20 yards.",
        },
        "havoc_rate": {
            "raw": "pregame_def_havoc_rate",
            "adjusted": "pregame_adj_def_havoc_effect",
            "sample": "adj_def_havoc_games",
            "direction": "higher",
            "format": "percentage",
            "description": "Defensive havoc generated through tackles for loss, passes defended and turnovers.",
        },
        "front_seven_havoc": {
            "raw": "pregame_def_front_seven_havoc_rate",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "higher",
            "format": "percentage",
            "description": "Havoc generated by the defensive front seven.",
        },
        "db_havoc": {
            "raw": "pregame_def_db_havoc_rate",
            "adjusted": None,
            "sample": "prior_games",
            "direction": "higher",
            "format": "percentage",
            "description": "Havoc generated by defensive backs.",
        },
    },
}


def number(value):
    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    return value if math.isfinite(value) else None


def integer(value):
    value = number(value)
    return int(value) if value is not None else None


def team_key(value):
    return " ".join(str(value or "").strip().lower().split())


def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing advanced input: {SOURCE}")

    df = pd.read_csv(SOURCE)
    df = df[pd.to_numeric(df["season"], errors="coerce").eq(SOURCE_SEASON)].copy()

    if df.empty:
        raise SystemExit(f"No {SOURCE_SEASON} rows found in {SOURCE}")

    df["week_num"] = pd.to_numeric(df["week"], errors="coerce")
    df["prior_games_num"] = pd.to_numeric(df["prior_games"], errors="coerce")

    # Select the most complete leakage-safe snapshot available for each team.
    latest = (
        df.sort_values(
            ["team", "prior_games_num", "week_num"],
            ascending=[True, True, True],
        )
        .groupby("team", as_index=False)
        .tail(1)
        .copy()
    )

    profiles = []

    for row in latest.to_dict("records"):
        profile = {
            "team": row["team"],
            "team_key": team_key(row["team"]),
            "snapshot": {
                "profile_type": "final_available_2025_pregame",
                "source_season": SOURCE_SEASON,
                "source_week": integer(row.get("week")),
                "through_week": (
                    max(0, integer(row.get("week")) - 1)
                    if integer(row.get("week")) is not None
                    else None
                ),
                "prior_games": integer(row.get("prior_games")),
                "source_game_id": str(row.get("game_id") or ""),
                "next_opponent_at_snapshot": row.get("opponent"),
                "current_2026": False,
                "display_label": "2025 final available pregame profile",
            },
            "offense": {},
            "defense": {},
        }

        for phase, phase_metrics in METRICS.items():
            for metric_name, config in phase_metrics.items():
                profile[phase][metric_name] = {
                    "raw_value": number(row.get(config["raw"])),
                    "opponent_adjusted_effect": (
                        number(row.get(config["adjusted"]))
                        if config["adjusted"]
                        else None
                    ),
                    "sample_games": integer(row.get(config["sample"])),
                    "rank": None,
                    "percentile": None,
                    "direction": config["direction"],
                    "format": config["format"],
                    "description": config["description"],
                }

        profiles.append(profile)

    # Rank every metric across available teams. Adjusted values are preferred
    # where they exist; otherwise raw values are used.
    for phase, phase_metrics in METRICS.items():
        for metric_name, config in phase_metrics.items():
            usable = []

            for profile in profiles:
                metric = profile[phase][metric_name]
                ranking_value = (
                    metric["opponent_adjusted_effect"]
                    if metric["opponent_adjusted_effect"] is not None
                    else metric["raw_value"]
                )

                if ranking_value is not None:
                    usable.append((profile, ranking_value))

            if not usable:
                continue

            values = pd.Series([value for _, value in usable], dtype=float)

            if config["direction"] == "lower":
                ranks = values.rank(method="min", ascending=True)
                percentiles = values.rank(method="average", pct=True, ascending=False)
            elif config["direction"] == "higher":
                ranks = values.rank(method="min", ascending=False)
                percentiles = values.rank(method="average", pct=True, ascending=True)
            else:
                ranks = pd.Series([np.nan] * len(values))
                percentiles = values.rank(method="average", pct=True, ascending=True)

            for index, (profile, _) in enumerate(usable):
                metric = profile[phase][metric_name]
                metric["rank"] = (
                    int(ranks.iloc[index])
                    if config["direction"] != "style"
                    else None
                )
                metric["percentile"] = float(percentiles.iloc[index])
                metric["ranking_basis"] = (
                    "opponent_adjusted_effect"
                    if metric["opponent_adjusted_effect"] is not None
                    else "raw_value"
                )

    site_teams = []

    if RATINGS_VIEW.exists():
        ratings = json.loads(RATINGS_VIEW.read_text())
        site_teams = [
            row["team"]
            for row in ratings.get("teams", [])
            if row.get("team")
        ]

    profile_keys = {profile["team_key"] for profile in profiles}
    missing_site_teams = [
        team for team in site_teams if team_key(team) not in profile_keys
    ]

    payload = {
        "schema_version": "team-advanced-profiles-v1",
        "source": str(SOURCE),
        "source_season": SOURCE_SEASON,
        "profile_type": "final_available_2025_pregame",
        "current_2026": False,
        "methodology": {
            "raw_metrics": "Leakage-safe rolling pregame CFBD/PBP aggregates.",
            "opponent_adjustment": (
                "Iterative regularized two-way offense/defense context model "
                "with a three-game prior weight."
            ),
            "selection": (
                "Latest available 2025 leakage-safe pregame snapshot for each team, "
                "selected by prior_games and week."
            ),
            "ranking": (
                "Opponent-adjusted effect where available; raw metric otherwise."
            ),
        },
        "teams": sorted(profiles, key=lambda row: row["team"]),
    }

    audit = {
        "status": "PASS",
        "source_rows_2025": int(len(df)),
        "profiles": len(profiles),
        "site_teams": len(site_teams),
        "site_teams_matched": len(site_teams) - len(missing_site_teams),
        "site_teams_missing": len(missing_site_teams),
        "missing_site_team_names": missing_site_teams,
        "minimum_prior_games": int(latest["prior_games_num"].min()),
        "maximum_prior_games": int(latest["prior_games_num"].max()),
        "source_weeks": sorted(
            int(value)
            for value in latest["week_num"].dropna().unique()
        ),
        "warnings": [
            "Profiles are 2025 historical context, not current 2026 performance.",
            "Each row is the team's final available pregame snapshot and may exclude its final 2025 game.",
            "North Dakota State and Sacramento State may lack FBS-history coverage.",
        ],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT.write_text(json.dumps(payload, indent=2))
    AUDIT.write_text(json.dumps(audit, indent=2))

    print("wrote:", OUTPUT)
    print("wrote:", AUDIT)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
