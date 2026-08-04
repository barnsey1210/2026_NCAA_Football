from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")


INPUT = BASE / (
    "data/research/"
    "conference_returning_production_signal_summary.csv"
)


OUTPUT = BASE / (
    "data/research/"
    "conference_rp_signal_rankings.csv"
)



def classify_confidence(row):

    games = row["games"]
    ats = row["ats_win_pct"]
    clv = row["avg_clv"]


    if games < 50:
        return "Low"


    if (
        ats >= .60
        and clv >= 0
    ):
        return "High"


    if (
        ats >= .55
        and clv >= 0
    ):
        return "Medium"


    if (
        ats <= .45
        and clv <= 0
    ):
        return "Fade"


    return "Neutral"



def build_interpretation(row):

    matchup = row["conference_matchup_type"]
    role = row["role"]
    bucket = row["overall_rp_edge_bucket"]

    ats = row["ats_win_pct"]


    team_description = (
        f"{role} with {bucket} returning production edge"
    )


    if ats >= .55:

        return (
            f"Positive signal: {team_description} "
            f"in {matchup} situations historically "
            f"outperformed ATS."
        )


    if ats <= .45:

        return (
            f"Fade signal: {team_description} "
            f"in {matchup} situations historically "
            f"failed to create ATS value."
        )


    return (
        f"Neutral signal: {team_description} "
        f"in {matchup} situations has limited ATS edge."
    )



def main():

    print("Loading summary")

    df = pd.read_csv(INPUT)


    print("Rows loaded:", len(df))


    # -------------------------
    # ADVANTAGE METRICS
    # -------------------------

    df["ats_edge"] = (
        df["ats_win_pct"]
        -
        .50
    )


    df["ats_edge_pct"] = (
        df["ats_edge"]
        *
        100
    )


    df["clv_signal"] = (
        df["avg_clv"]
        .apply(
            lambda x:
            "Positive"
            if x > 0
            else "Negative"
        )
    )



    # -------------------------
    # SIGNAL SCORING
    # -------------------------

    df["signal_score"] = (

        (df["ats_edge_pct"] * 2)

        +

        (
            df["avg_clv"]
            .fillna(0)
        )

        +

        (
            df["games"]
            .clip(upper=500)
            /
            50
        )

    )



    df["confidence"] = (
        df.apply(
            classify_confidence,
            axis=1
        )
    )



    df["interpretation"] = (
        df.apply(
            build_interpretation,
            axis=1
        )
    )



    # -------------------------
    # SORT
    # -------------------------

    df = df.sort_values(

        [
            "signal_score",
            "games"

        ],

        ascending=[
            False,
            False
        ]

    )



    # -------------------------
    # OUTPUT
    # -------------------------

    columns = [

        "conference_matchup_type",

        "role",

        "overall_rp_edge_bucket",

        "games",

        "ats_win_pct",

        "ats_edge_pct",

        "avg_clv",

        "clv_signal",

        "signal_score",

        "confidence",

        "interpretation"

    ]


    df = df[columns]


    df.to_csv(
        OUTPUT,
        index=False
    )


    print()
    print("Created:")
    print(OUTPUT)

    print()
    print(
        df.head(30)
        .to_string(index=False)
    )



if __name__ == "__main__":
    main()