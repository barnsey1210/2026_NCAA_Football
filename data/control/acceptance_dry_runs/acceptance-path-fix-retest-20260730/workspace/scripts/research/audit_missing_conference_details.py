from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

RP_FILE = BASE / "data/research/returning_production_clv/returning_production_games_with_clv.csv"

CONF_FILE = BASE / "data/research/conference_matchup_history_2021_2025_bidirectional.csv"

OUT = BASE / "data/audits/missing_conference_details.csv"


def clean(x):
    return (
        str(x)
        .strip()
        .lower()
    )


def main():

    rp = pd.read_csv(RP_FILE)

    conf = pd.read_csv(CONF_FILE)


    for df in [rp, conf]:

        df["team_key"] = df["team"].apply(clean)
        df["opp_key"] = df["opponent"].apply(clean)


    merged = rp.merge(
        conf[
            [
                "season",
                "team_key",
                "opp_key",
                "conference_matchup_type"
            ]
        ],
        on=[
            "season",
            "team_key",
            "opp_key"
        ],
        how="left"
    )


    missing = merged[
        merged["conference_matchup_type"].isna()
    ]


    out = missing[
        [
            "season",
            "team",
            "opponent"
        ]
    ].drop_duplicates()


    out.to_csv(
        OUT,
        index=False
    )


    print("Missing:",len(out))

    print()

    print(
        out.to_string(index=False)
    )

    print()

    print("Created:")
    print(OUT)



if __name__ == "__main__":
    main()

