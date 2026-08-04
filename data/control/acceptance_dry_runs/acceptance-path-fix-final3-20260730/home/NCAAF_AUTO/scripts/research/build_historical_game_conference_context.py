from pathlib import Path
import pandas as pd


GAME_HISTORY = Path(
    "data/research/game_control_history_2021_2025/team_game_game_control.csv"
)

CONF_HISTORY = Path(
    "data/reference/team_conference_history.csv"
)

OUT = Path(
    "data/research/conference_matchup_history_2021_2025.csv"
)


# Conference tier mapping
P4 = {
    "SEC",
    "Big Ten",
    "Big 12",
    "ACC",
}

G6 = {
    "American",
    "Mountain West",
    "Sun Belt",
    "MAC",
    "Conference USA",
}


def conference_tier(conf):
    if conf in P4:
        return "P4"
    if conf in G6:
        return "G6"
    if conf == "Independent":
        return "Independent"
    return "Other"


def main():

    games = pd.read_csv(GAME_HISTORY)

    conf = pd.read_csv(CONF_HISTORY)

    print("Game rows:", len(games))
    print("Conference rows:", len(conf))


    # normalize names
    games["team_clean"] = games["team"].str.strip()
    games["opponent_clean"] = games["opponent"].str.strip()

    conf["team_clean"] = conf["team"].str.strip()


    # keep only seasons covered
    games = games[
        games["season"].between(2021, 2025)
    ].copy()


    # merge team conference
    games = games.merge(
        conf[
            [
                "season",
                "team_clean",
                "conference",
                "conference_changed",
                "previous_conference",
            ]
        ],
        left_on=["season", "team_clean"],
        right_on=["season", "team_clean"],
        how="left",
    )

    games = games.rename(
        columns={
            "conference": "team_conference",
            "conference_changed": "team_changed_conference",
            "previous_conference": "team_previous_conference",
        }
    )


    # merge opponent conference
    games = games.merge(
        conf[
            [
                "season",
                "team_clean",
                "conference",
                "conference_changed",
                "previous_conference",
            ]
        ],
        left_on=["season", "opponent_clean"],
        right_on=["season", "team_clean"],
        how="left",
        suffixes=("", "_opp"),
    )


    games = games.rename(
        columns={
            "conference": "opponent_conference",
            "conference_changed": "opponent_changed_conference",
            "previous_conference": "opponent_previous_conference",
        }
    )


    # remove FCS / unmatched games
    games = games[
        games["team_conference"].notna()
        &
        games["opponent_conference"].notna()
    ].copy()


    # tiers
    games["team_tier"] = games["team_conference"].apply(
        conference_tier
    )

    games["opponent_tier"] = games["opponent_conference"].apply(
        conference_tier
    )


    # only FBS vs FBS
    games = games[
        games["team_tier"].isin(["P4", "G6", "Independent"])
        &
        games["opponent_tier"].isin(["P4", "G6", "Independent"])
    ].copy()


    def matchup_type(row):

        a = row["team_tier"]
        b = row["opponent_tier"]

        if a == "P4" and b == "G6":
            return "P4_vs_G6"

        if a == "G6" and b == "P4":
            return "G6_vs_P4"

        if a == "P4" and b == "P4":
            return "P4_vs_P4"

        if a == "G6" and b == "G6":
            return "G6_vs_G6"

        return "Other"


    games["conference_matchup_type"] = games.apply(
        matchup_type,
        axis=1
    )


    # years since conference move
    games["team_years_since_move"] = None
    games["opponent_years_since_move"] = None


    def years_since_move(row, side):

        changed = row[f"{side}_changed_conference"]

        if not changed:
            return None

        return 0


    games["team_years_since_move"] = games.apply(
        lambda x: years_since_move(x, "team"),
        axis=1
    )

    games["opponent_years_since_move"] = games.apply(
        lambda x: years_since_move(x, "opponent"),
        axis=1
    )


    cols = [
        "season",
        "date",
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
        "opponent_years_since_move",
        "team_spread",
        "ats_margin",
        "ats_result",
        "total_line",
        "total_margin",
        "total_result",
    ]

    cols = [
        c for c in cols
        if c in games.columns
    ]


    games[cols].to_csv(
        OUT,
        index=False
    )


    print()
    print("Created:")
    print(OUT)
    print("Rows:", len(games))
    print()
    print(
        games["conference_matchup_type"]
        .value_counts()
    )


if __name__ == "__main__":
    main()
