from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")


INPUT = BASE / "data/research/conference_matchup_history_2021_2025.csv"

OUTPUT = BASE / "data/research/conference_matchup_history_2021_2025_bidirectional.csv"



def main():

    df = pd.read_csv(INPUT)

    print("Original rows:", len(df))


    # original direction
    a = df.copy()


    # reverse direction
    b = df.copy()


    b = b.rename(
        columns={
            "team":"opponent",
            "opponent":"team",

            "team_conference":"opponent_conference",
            "opponent_conference":"team_conference",

            "team_tier":"opponent_tier",
            "opponent_tier":"team_tier",

            "team_changed_conference":"opponent_changed_conference",
            "opponent_changed_conference":"team_changed_conference",

            "team_previous_conference":"opponent_previous_conference",
            "opponent_previous_conference":"team_previous_conference",

            "team_years_since_move":"opponent_years_since_move",
            "opponent_years_since_move":"team_years_since_move"
        }
    )


    out = pd.concat(
        [
            a,
            b
        ],
        ignore_index=True
    )


    out = out.drop_duplicates(
        subset=[
            "season",
            "team",
            "opponent"
        ]
    )


    out.to_csv(
        OUTPUT,
        index=False
    )


    print("New rows:",len(out))

    print("Created:")
    print(OUTPUT)



if __name__ == "__main__":
    main()
