#!/usr/bin/env python3

from pathlib import Path
import json
import re

import numpy as np
import pandas as pd


ROOT = Path(".")
SOURCE = (
    ROOT
    / "data/research/returning_production_clv"
    / "returning_production_games_with_clv.csv"
)
OUT_DIR = ROOT / "data/research/returning_production_clv"
AUDIT_OUT = (
    ROOT
    / "data/audit/returning_production_conference_tier_audit.json"
)

# Adjust these names only if the source conference labels differ.
POWER_CONFERENCES = {
    "ACC",
    "Big Ten",
    "Big 12",
    "SEC",
    "Pac-12",
}

FBS_GROUP_CONFERENCES = {
    "American Athletic",
    "American",
    "Conference USA",
    "CUSA",
    "Mid-American",
    "MAC",
    "Mountain West",
    "MWC",
    "Sun Belt",
}

INDEPENDENT_FBS = {
    "Notre Dame",
    "Connecticut",
    "UConn",
    "UMass",
}


def norm(value):
    return re.sub(
        r"\s+",
        " ",
        str(value or "").strip().lower(),
    )


def find_team_metadata():
    candidates = [
        ROOT / "data/site/ratings_view.json",
        ROOT / "data/site/matchups_view.json",
    ]

    metadata = {}

    ratings_path = candidates[0]

    if ratings_path.exists():
        data = json.loads(ratings_path.read_text())

        for row in data.get("teams", []):
            team = row.get("team")
            conference = (
                row.get("conference")
                or row.get("team_conference")
                or ""
            )

            if team:
                metadata[norm(team)] = {
                    "team": team,
                    "conference": conference,
                }

    matchups_path = candidates[1]

    if matchups_path.exists():
        data = json.loads(matchups_path.read_text())
        games = data.get("games", data)

        for game in games:
            for side in ["away", "home"]:
                team_row = game.get("teams", {}).get(side, {})
                game_row = game.get("game", {})
                team = game_row.get(f"{side}_team")

                conference = (
                    team_row.get("conference")
                    or team_row.get("team_conference")
                    or ""
                )

                if team and norm(team) not in metadata:
                    metadata[norm(team)] = {
                        "team": team,
                        "conference": conference,
                    }

    return metadata


def classify(team, conference):
    conference = str(conference or "").strip()

    if conference in POWER_CONFERENCES:
        return "Power"

    if conference in FBS_GROUP_CONFERENCES:
        return "Group"

    if team in INDEPENDENT_FBS:
        return "Independent FBS"

    if conference:
        return "Other/FCS"

    return "Unknown"


def matchup_class(team_tier, opponent_tier):
    if team_tier == "Power" and opponent_tier == "Power":
        return "Power vs Power"

    if team_tier == "Power" and opponent_tier == "Group":
        return "Power vs Group"

    if team_tier == "Group" and opponent_tier == "Power":
        return "Group vs Power"

    if team_tier == "Group" and opponent_tier == "Group":
        return "Group vs Group"

    if "Other/FCS" in {team_tier, opponent_tier}:
        return "FBS/FCS or Other"

    return f"{team_tier} vs {opponent_tier}"


def summarize(group):
    decided = group[group["ats_result"].isin(["W", "L"])]
    clv = pd.to_numeric(group["team_clv"], errors="coerce").dropna()

    wins = int((decided["ats_result"] == "W").sum())
    losses = int((decided["ats_result"] == "L").sum())

    return pd.Series({
        "games": len(group),
        "ats_w": wins,
        "ats_l": losses,
        "ats_p": int((group["ats_result"] == "P").sum()),
        "ats_pct": wins / len(decided) if len(decided) else np.nan,
        "avg_ats_margin": pd.to_numeric(
            group["ats_margin"],
            errors="coerce",
        ).mean(),
        "clv_games": len(clv),
        "avg_clv": clv.mean(),
        "median_clv": clv.median(),
        "positive_clv_pct": (
            float((clv > 0).mean())
            if len(clv)
            else np.nan
        ),
        "seasons": group["season"].nunique(),
    })


def main():
    if not SOURCE.exists():
        raise SystemExit(f"Missing source: {SOURCE}")

    df = pd.read_csv(SOURCE)
    metadata = find_team_metadata()

    df["team_conference"] = df["team"].map(
        lambda value: metadata.get(
            norm(value),
            {},
        ).get("conference", "")
    )

    df["opponent_conference"] = df["opponent"].map(
        lambda value: metadata.get(
            norm(value),
            {},
        ).get("conference", "")
    )

    df["team_tier"] = [
        classify(team, conf)
        for team, conf in zip(
            df["team"],
            df["team_conference"],
        )
    ]

    df["opponent_tier"] = [
        classify(team, conf)
        for team, conf in zip(
            df["opponent"],
            df["opponent_conference"],
        )
    ]

    df["matchup_class"] = [
        matchup_class(team_tier, opponent_tier)
        for team_tier, opponent_tier in zip(
            df["team_tier"],
            df["opponent_tier"],
        )
    ]

    canonical = df[
        df["case"].isin([
            "off_vs_def_gap",
            "def_vs_off_gap",
            "overall_gap",
        ])
        & df["threshold"].eq("gap_10+")
    ].copy()

    summary = (
        canonical
        .groupby(
            [
                "case",
                "role",
                "matchup_class",
            ],
            dropna=False,
        )
        .apply(summarize)
        .reset_index()
    )

    by_season = (
        canonical
        .groupby(
            [
                "case",
                "role",
                "matchup_class",
                "season",
            ],
            dropna=False,
        )
        .apply(summarize)
        .reset_index()
    )

    by_bucket = (
        canonical
        .groupby(
            [
                "case",
                "role",
                "matchup_class",
                "spread_bucket",
            ],
            dropna=False,
        )
        .apply(summarize)
        .reset_index()
    )

    canonical.to_csv(
        OUT_DIR
        / "returning_production_games_with_conference_tier.csv",
        index=False,
    )

    summary.to_csv(
        OUT_DIR
        / "returning_production_clv_by_conference_tier.csv",
        index=False,
    )

    by_season.to_csv(
        OUT_DIR
        / "returning_production_clv_by_conference_tier_season.csv",
        index=False,
    )

    by_bucket.to_csv(
        OUT_DIR
        / "returning_production_clv_by_conference_tier_spread.csv",
        index=False,
    )

    unknown_teams = sorted(
        set(
            canonical.loc[
                canonical["team_tier"].eq("Unknown"),
                "team",
            ].dropna()
        )
        | set(
            canonical.loc[
                canonical["opponent_tier"].eq("Unknown"),
                "opponent",
            ].dropna()
        )
    )

    audit = {
        "status": "PASS",
        "source": str(SOURCE),
        "rows": len(canonical),
        "matchup_class_counts": (
            canonical["matchup_class"]
            .value_counts(dropna=False)
            .to_dict()
        ),
        "unknown_teams": unknown_teams,
        "warning": (
            "Conference tiers are only as reliable as the current "
            "team-conference metadata. Review Unknown and Other/FCS teams."
        ),
    }

    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_OUT.write_text(json.dumps(audit, indent=2))

    print(json.dumps(audit, indent=2))

    print("\nOFFENSE RP VS DEFENSE RP — FAVORITES")
    print(
        summary[
            summary["case"].eq("off_vs_def_gap")
            & summary["role"].eq("Favorite")
        ]
        .sort_values("games", ascending=False)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
