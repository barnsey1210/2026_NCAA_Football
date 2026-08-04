from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

CONF_FILE = BASE / "data/research/conference_matchup_betting_history_2021_2025.csv"
CONF_SOURCE = BASE / "data/research/conference_matchup_history_2021_2025.csv"

RP_FILE = BASE / "data/research/returning_production_clv/returning_production_games_with_clv.csv"

OUT_GAMES = BASE / "data/research/conference_returning_production_signal_games.csv"
OUT_SUMMARY = BASE / "data/research/conference_returning_production_signal_summary.csv"


def bucket(x):

    if pd.isna(x):
        return "missing"

    if x >= 25:
        return "25_plus"

    if x >= 15:
        return "15_to_25"

    if x >= 5:
        return "5_to_15"

    if x <= -25:
        return "minus_25"

    if x <= -15:
        return "minus_15_to_25"

    if x <= -5:
        return "minus_5_to_15"

    return "neutral"



def normalize_text(df):

    for c in ["team", "opponent"]:

        if c in df.columns:

            df[c] = (
                df[c]
                .astype(str)
                .str.strip()
            )

    df["season"] = df["season"].astype(int)

    return df



def load_conference():

    conf = pd.read_csv(CONF_FILE)

    print("Conference original columns:")
    print(conf.columns.tolist())


    if "team" in conf.columns:
        return conf


    print()
    print("Team column missing.")
    print("Rebuilding conference data from source file...")


    source = pd.read_csv(CONF_SOURCE)

    print("Conference source rows:", len(source))


    keep = [

        "season",
        "team",
        "opponent",

        "team_conference",
        "opponent_conference",

        "team_tier",
        "opponent_tier",

        "conference_matchup_type",

        "team_changed_conference",
        "opponent_changed_conference",

        "team_previous_conference",
        "opponent_previous_conference",

        "team_years_since_move",
        "opponent_years_since_move"

    ]


    conf = source[keep].copy()


    conf = normalize_text(conf)


    conf = conf.drop_duplicates(
        subset=[
            "season",
            "team",
            "opponent"
        ]
    )


    return conf



def normalize_rp(df):

    if "team" not in df.columns:

        if "team_x" in df.columns:
            df["team"] = df["team_x"]

        elif "team_y" in df.columns:
            df["team"] = df["team_y"]


    if "opponent" not in df.columns:

        if "opponent_x" in df.columns:
            df["opponent"] = df["opponent_x"]

        elif "opponent_y" in df.columns:
            df["opponent"] = df["opponent_y"]


    return df



def main():

    print("Loading files")


    conf = load_conference()

    rp = pd.read_csv(RP_FILE)


    print()
    print("Conference rows:", len(conf))
    print("RP rows:", len(rp))


    rp = normalize_rp(rp)

    rp = normalize_text(rp)



    # -------------------------
    # BUILD RP EDGES
    # -------------------------

    rp["overall_rp_edge"] = (
        rp["team_overall"]
        -
        rp["opp_overall"]
    )


    rp["off_vs_def_rp_edge"] = (
        rp["team_offense"]
        -
        rp["opp_defense"]
    )


    rp["def_vs_off_rp_edge"] = (
        rp["team_defense"]
        -
        rp["opp_offense"]
    )


    rp["overall_rp_edge_bucket"] = (
        rp["overall_rp_edge"]
        .apply(bucket)
    )



    rp = rp[

        [
            "season",
            "week",
            "date",
            "game_id",

            "team",
            "opponent",

            "role",
            "spread",

            "ats_result",
            "ats_margin",

            "team_clv",

            "overall_rp_edge",
            "off_vs_def_rp_edge",
            "def_vs_off_rp_edge",

            "overall_rp_edge_bucket"

        ]

    ]



    print()
    print("RP before merge:", len(rp))
    print("Conference before merge:", len(conf))



    # -------------------------
    # MERGE
    # -------------------------

    df = rp.merge(

        conf,

        on=[

            "season",
            "team",
            "opponent"

        ],

        how="left"

    )


    print()
    print("After merge:", len(df))


    print()
    print(
        "Missing conference matches:",
        df["conference_matchup_type"].isna().sum()
    )

    print(
        "Matched conference rows:",
        df["conference_matchup_type"].notna().sum()
    )



    # -------------------------
    # FEATURES
    # -------------------------

    df["off_vs_def_rp_edge_bucket"] = (
        df["off_vs_def_rp_edge"]
        .apply(bucket)
    )


    df["def_vs_off_rp_edge_bucket"] = (
        df["def_vs_off_rp_edge"]
        .apply(bucket)
    )


    df["early_season"] = (
        df["week"] <= 4
    )



    df.to_csv(
        OUT_GAMES,
        index=False
    )



    # -------------------------
    # SUMMARY
    # -------------------------

    summary_base = df[
        (df["early_season"])
        &
        (df["conference_matchup_type"].notna())
    ].copy()


    print()
    print(
        "Summary rows used:",
        len(summary_base)
    )



    summary = (

        summary_base

        .groupby(

            [

                "conference_matchup_type",
                "role",
                "overall_rp_edge_bucket"

            ],

            dropna=False

        )

        .agg(

            games=("ats_result","count"),

            wins=(
                "ats_result",
                lambda x:(x=="W").sum()
            ),

            losses=(
                "ats_result",
                lambda x:(x=="L").sum()
            ),

            avg_clv=(
                "team_clv",
                "mean"
            )

        )

        .reset_index()

    )



    summary["ats_win_pct"] = (
        summary["wins"]
        /
        summary["games"]
    )



    summary = summary[
        summary["games"] >= 20
    ].copy()



    summary = summary.sort_values(

        [

            "ats_win_pct",
            "games"

        ],

        ascending=[

            False,
            False

        ]

    )



    summary.to_csv(
        OUT_SUMMARY,
        index=False
    )



    print()
    print("Created:")
    print(OUT_GAMES)
    print("Rows:", len(df))


    print()
    print("Created:")
    print(OUT_SUMMARY)


    print()
    print(
        summary.head(30)
        .to_string(index=False)
    )



if __name__ == "__main__":
    main()