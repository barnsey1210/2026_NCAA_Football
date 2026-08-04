from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

MISSING = BASE / "data/audits/missing_conference_details.csv"

SOURCE = BASE / "data/research/conference_matchup_history_2021_2025.csv"


def clean(x):
    return (
        str(x)
        .lower()
        .strip()
        .replace("'","")
        .replace(".","")
    )


def main():

    missing = pd.read_csv(MISSING)
    source = pd.read_csv(SOURCE)


    source["team_key"] = source["team"].apply(clean)
    source["opp_key"] = source["opponent"].apply(clean)


    print("Checking missing games against source...")
    print()


    found = []

    for _,r in missing.iterrows():

        season = r["season"]

        team = clean(r["team"])
        opp = clean(r["opponent"])


        check = source[
            (source["season"] == season)
            &
            (
                (
                    (source["team_key"] == team)
                    &
                    (source["opp_key"] == opp)
                )
                |
                (
                    (source["team_key"] == opp)
                    &
                    (source["opp_key"] == team)
                )
            )
        ]


        if len(check):

            found.append(
                {
                    "season":season,
                    "team":r["team"],
                    "opponent":r["opponent"],
                    "source_team":check.iloc[0]["team"],
                    "source_opponent":check.iloc[0]["opponent"]
                }
            )


    result = pd.DataFrame(found)


    print("Found in source:",len(result))
    print()

    if len(result):
        print(result.to_string(index=False))


if __name__ == "__main__":
    main()