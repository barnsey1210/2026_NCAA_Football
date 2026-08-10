#!/usr/bin/env python3

from pathlib import Path
import json
import math
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

PROFILE = ROOT / "data/site/team_advanced_profiles.json"
SOURCE = ROOT / "data/research/advanced_directional_game_level_2021_2025.csv"
AUDIT = ROOT / "data/audit/team_advanced_profiles_drive_extension_audit.json"

ALIASES = {
    "Hawai'i": "Hawaii",
}

def clean_team(value):
    value = str(value or "").strip()
    return ALIASES.get(value, value)

def finite(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None

def rank_values(values, higher_better=True):
    valid = [(team, value) for team, value in values.items() if value is not None]

    valid.sort(
        key=lambda item: item[1],
        reverse=higher_better,
    )

    n = len(valid)
    result = {}

    for rank, (team, value) in enumerate(valid, 1):
        percentile = (
            (n - rank) / (n - 1)
            if n > 1
            else 1.0
        )

        result[team] = {
            "rank": rank,
            "percentile": percentile,
        }

    return result

def main():
    payload = json.loads(PROFILE.read_text())
    profiles = payload.get("teams", [])

    df = pd.read_csv(SOURCE, low_memory=False)
    df["game_id"] = df["game_id"].astype(str)

    # First collect exact snapshot values for every team.
    extracted = {}

    for profile in profiles:
        raw_team = profile.get("team")
        team = clean_team(raw_team)

        snapshot = profile.get("snapshot") or {}
        source_game_id = str(snapshot.get("source_game_id") or "").strip()

        if not source_game_id:
            continue

        rows = df[
            (df["season"] == 2025)
            & (df["game_id"] == source_game_id)
        ]

        if rows.empty:
            continue

        row = rows.iloc[-1]

        side = None

        if clean_team(row.get("home_team")) == team:
            side = "home"
        elif clean_team(row.get("away_team")) == team:
            side = "away"

        if not side:
            continue

        extracted[team] = {
            "finishing_off": finite(
                row.get(f"{side}_drive_pregame_off_points_per_opportunity")
            ),
            "finishing_def": finite(
                row.get(f"{side}_drive_pregame_def_points_per_opportunity_allowed")
            ),
            "field_off": finite(
                row.get(f"{side}_drive_pregame_off_avg_start_ytg")
            ),
            "field_def": finite(
                row.get(f"{side}_drive_pregame_def_opponent_avg_start_ytg")
            ),
            "havoc_off": finite(
                row.get(f"{side}_pregame_adj_off_havoc_allowed_effect")
            ),
            "havoc_def": finite(
                row.get(f"{side}_pregame_adj_def_havoc_effect")
            ),
        }

    rankings = {
        # More points per scoring opportunity is better.
        "finishing_off": rank_values(
            {t: v["finishing_off"] for t, v in extracted.items()},
            higher_better=True,
        ),

        # Fewer points allowed per scoring opportunity is better.
        "finishing_def": rank_values(
            {t: v["finishing_def"] for t, v in extracted.items()},
            higher_better=False,
        ),

        # Yards-to-go at drive start: lower means better starting field position.
        "field_off": rank_values(
            {t: v["field_off"] for t, v in extracted.items()},
            higher_better=False,
        ),

        # On defense, forcing opponents farther from the goal is better.
        "field_def": rank_values(
            {t: v["field_def"] for t, v in extracted.items()},
            higher_better=True,
        ),

        # Lower opponent-adjusted havoc allowed effect is better offensively.
        "havoc_off": rank_values(
            {t: v["havoc_off"] for t, v in extracted.items()},
            higher_better=False,
        ),

        # Higher opponent-adjusted havoc creation effect is better defensively.
        "havoc_def": rank_values(
            {t: v["havoc_def"] for t, v in extracted.items()},
            higher_better=True,
        ),
    }

    updated = 0

    for profile in profiles:
        team = clean_team(profile.get("team"))

        values = extracted.get(team)
        if not values:
            continue

        offense = profile.setdefault("offense", {})
        defense = profile.setdefault("defense", {})

        def metric(value_key, description, direction, ranking_basis):
            value = values[value_key]
            rank_info = rankings[value_key].get(team, {})

            return {
                "raw_value": value,
                "opponent_adjusted_effect": (
                    value
                    if value_key in {"havoc_off", "havoc_def"}
                    else None
                ),
                "sample_games": (
                    profile.get("snapshot", {}).get("prior_games")
                ),
                "rank": rank_info.get("rank"),
                "percentile": rank_info.get("percentile"),
                "direction": direction,
                "format": "decimal",
                "description": description,
                "ranking_basis": ranking_basis,
            }

        offense["finishing_drives"] = metric(
            "finishing_off",
            "Offensive points scored per scoring opportunity.",
            "higher",
            "raw_value",
        )

        defense["finishing_drives_allowed"] = metric(
            "finishing_def",
            "Defensive points allowed per opponent scoring opportunity.",
            "lower",
            "raw_value",
        )

        offense["field_position"] = metric(
            "field_off",
            "Average yards to goal at the start of offensive drives; lower is better.",
            "lower",
            "raw_value",
        )

        defense["field_position_allowed"] = metric(
            "field_def",
            "Average opponent yards to goal at the start of drives; higher is better defensively.",
            "higher",
            "raw_value",
        )

        offense["havoc_avoidance"] = metric(
            "havoc_off",
            "Opponent-adjusted offensive havoc allowed effect; lower is better.",
            "lower",
            "opponent_adjusted_effect",
        )

        # Preserve the existing richer havoc_rate object if present, but
        # ensure its opponent-adjusted rank comes from the same final snapshot.
        if values["havoc_def"] is not None:
            existing = defense.get("havoc_rate") or {}

            existing["opponent_adjusted_effect"] = values["havoc_def"]
            existing["rank"] = rankings["havoc_def"].get(team, {}).get("rank")
            existing["percentile"] = rankings["havoc_def"].get(team, {}).get("percentile")
            existing["ranking_basis"] = "opponent_adjusted_effect"

            defense["havoc_rate"] = existing

        updated += 1

    payload["teams"] = profiles

    methodology = payload.setdefault("methodology", {})
    methodology["drive_extension"] = {
        "source": "advanced_directional_game_level_2021_2025.csv",
        "source_season": 2025,
        "snapshot_alignment": "existing final-available 2025 pregame source_game_id",
        "metrics": [
            "finishing_drives",
            "field_position",
            "havoc_avoidance",
        ],
    }

    PROFILE.write_text(json.dumps(payload, indent=2) + "\n")

    audit = {
        "status": "PASS",
        "profiles_total": len(profiles),
        "profiles_extended": updated,
        "profiles_not_extended": len(profiles) - updated,
        "source_season": 2025,
        "source": str(SOURCE.relative_to(ROOT)),
        "profile": str(PROFILE.relative_to(ROOT)),
    }

    AUDIT.write_text(json.dumps(audit, indent=2) + "\n")

    print("profiles total:", len(profiles))
    print("profiles extended:", updated)
    print("profiles not extended:", len(profiles) - updated)
    print("wrote:", PROFILE)
    print("wrote:", AUDIT)

if __name__ == "__main__":
    main()
