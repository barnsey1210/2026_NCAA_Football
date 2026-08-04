from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")


FILE = BASE / "data/research/conference_returning_production_signal_games.csv"

OUT = BASE / "data/audits/missing_conference_matches.csv"


def main():

    df = pd.read_csv(FILE)


    missing = df[
        df["conference_matchup_type"].isna()
    ][
        [
            "season",
            "team",
            "opponent"
        ]
    ]


    missing = (
        missing
        .drop_duplicates()
        .sort_values(
            [
                "team",
                "opponent"
            ]
        )
    )


    OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    missing.to_csv(
        OUT,
        index=False
    )


    print("Missing rows:",len(missing))

    print()

    print(
        missing.head(100)
        .to_string(index=False)
    )

    print()

    print("Created:")
    print(OUT)



if __name__ == "__main__":
    main()
