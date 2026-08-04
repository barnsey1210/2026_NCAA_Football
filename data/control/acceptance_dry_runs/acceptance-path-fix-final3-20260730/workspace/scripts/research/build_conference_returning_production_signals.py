from pathlib import Path
import pandas as pd
import numpy as np


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

RP_FILE = BASE / "data/research/returning_production_clv/returning_production_games_with_clv.csv"
CONF_FILE = BASE / "data/research/conference_matchup_history_2021_2025.csv"

OUT_GAMES = BASE / "data/research/conference_returning_production_signal_games.csv"
OUT_SUMMARY = BASE / "data/research/conference_returning_production_signal_summary.csv"


P4 = {
    "ACC",
    "Big Ten",
    "Big 12",
    "SEC",
    "Pac-12"
}


def tier(conf):
    if conf in P4:
        return "P4"
    if pd.isna(conf):
        return "Other"
    return "G6"


def bucket(x):
    if pd.isna(x):
        return "missing"
    if x >= 25:
        return "25_plus"
    if x >= 15:
        return "15_to_25"
    if x >= 5:
        return "5_to_15"
    if x > -5:
        return "neutral"
    if x > -15:
        return "-15_to_-5"
    if x > -25:
        return "-25_to_-15"
    return "-25_or_less"


def main():

    print("Loading RP")

    df = pd.read_csv(RP_FILE)

    print("RP rows:", len(df))


    print("Loading conference history")

    conf = pd.read_csv(CONF_FILE)

    print("Conference rows:", len(conf))


    # create lookup for team side
    team_conf = conf[
        [
            "season",
            "team",
            "opponent",
            "team_conference",
            "opponent_conference"
        ]
    ].copy()


    # normalize
    for c in ["team","opponent"]:
        df[c+"_key"] = (
            df[c]
            .astype(str)
            .str.lower()
            .str.strip()
        )

        team_conf[c+"_key"] = (
            team_conf[c]
            .astype(str)
            .str.lower()
            .str.strip()
        )


    df = df.merge(
        team_conf,
        on=[
            "season",
            "team_key",
            "opponent_key"
        ],
        how="left"
    )


    print("After conference attach:", len(df))


    df["team_tier"] = df["team_conference"].apply(tier)
    df["opponent_tier"] = df["opponent_conference"].apply(tier)


    df["conference_matchup_type"] = (
        df["team_tier"]
        +
        "_vs_"
        +
        df["opponent_tier"]
    )


    df["overall_rp_edge"] = (
        df["team_overall"]
        -
        df["opp_overall"]
    )

    df["off_vs_def_rp_edge"] = (
        df["team_offense"]
        -
        df["opp_defense"]
    )

    df["def_vs_off_rp_edge"] = (
        df["team_defense"]
        -
        df["opp_offense"]
    )


    for c in [
        "overall_rp_edge",
        "off_vs_def_rp_edge",
        "def_vs_off_rp_edge"
    ]:
        df[c+"_bucket"] = df[c].apply(bucket)


    df["early_season"] = (
        df["week"] <= 4
    )


    df.to_csv(
        OUT_GAMES,
        index=False
    )


    print("Created:")
    print(OUT_GAMES)
    print("Rows:", len(df))


    summary = (
        df
        .dropna(subset=["ats_result"])
        .groupby(
            [
                "conference_matchup_type",
                "role",
                "early_season",
                "overall_rp_edge_bucket"
            ]
        )
        .agg(
            games=("ats_result","count"),
            wins=("ats_result",
                  lambda x:(x=="W").sum()),
            losses=("ats_result",
                    lambda x:(x=="L").sum()),
            avg_clv=("team_clv","mean")
        )
        .reset_index()
    )


    summary["ats_win_pct"] = (
        summary["wins"]
        /
        summary["games"]
    )


    summary.to_csv(
        OUT_SUMMARY,
        index=False
    )


    print("Created:")
    print(OUT_SUMMARY)

    print(
        summary
        .sort_values("games",ascending=False)
        .head(30)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
