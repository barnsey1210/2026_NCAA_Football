from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")


INPUT = BASE / "data/research/conference_returning_production_signal_games.csv"

OUT_DETAIL = BASE / "data/research/conference_rp_spread_angles.csv"

OUT_SUMMARY = BASE / "data/research/conference_rp_spread_angle_summary.csv"



def spread_bucket(spread):

    if pd.isna(spread):
        return "missing"

    # positive = underdog
    if spread >= 14.5:
        return "dog_14_plus"

    if spread >= 7.5:
        return "dog_7_14"

    if spread >= 3.5:
        return "dog_3_7"

    if spread > -3.5:
        return "pick_to_3"

    if spread > -7.5:
        return "fav_3_7"

    if spread > -14.5:
        return "fav_7_14"

    return "fav_14_plus"



def rp_direction(row):

    """
    Determine whether the team with RP edge
    is favorite or underdog.

    Returning production edge is from the team perspective.
    """

    edge = row["overall_rp_edge"]

    if edge > 0:
        return "team_has_rp_edge"

    if edge < 0:
        return "opponent_has_rp_edge"

    return "neutral"



def abs_bucket(x):

    x = abs(x)

    if x >= 25:
        return "25_plus"

    if x >= 15:
        return "15_to_25"

    if x >= 5:
        return "5_to_15"

    return "neutral"



def main():

    print("Loading RP signal games")

    df = pd.read_csv(INPUT)


    print("Rows loaded:",len(df))


    # normalize

    df["rp_edge_bucket"] = (
        df["overall_rp_edge"]
        .abs()
        .apply(abs_bucket)
    )


    df["spread_bucket"] = (
        df["spread"]
        .apply(spread_bucket)
    )


    df["rp_edge_side"] = (
        df
        .apply(rp_direction, axis=1)
    )


    # only games where someone had RP advantage

    df = df[
        df["rp_edge_side"] != "neutral"
    ].copy()


    df.to_csv(
        OUT_DETAIL,
        index=False
    )


    print()
    print("Created:")
    print(OUT_DETAIL)

    print("Rows:",len(df))


    print()
    print("Building summary")


    summary = (

        df[

            df["conference_matchup_type"]
            .notna()

        ]

        .groupby(

            [

                "conference_matchup_type",

                "role",

                "rp_edge_bucket",

                "spread_bucket"

            ]

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


    summary["ats_edge_pct"] = (
        summary["ats_win_pct"] * 100
        -
        50
    )


    # minimum sample size

    summary = summary[
        summary["games"] >= 20
    ]


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
    print(OUT_SUMMARY)


    print()

    print(
        summary.head(50)
        .to_string(index=False)
    )



if __name__ == "__main__":
    main()