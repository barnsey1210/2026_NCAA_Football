from pathlib import Path
import pandas as pd
import numpy as np
import re


CONF_FILE = Path(
    "data/research/conference_matchup_history_2021_2025.csv"
)

BET_FILE = Path(
    "data/research/returning_production_clv/returning_production_games_with_clv.csv"
)

OUT = Path(
    "data/research/conference_matchup_betting_history_2021_2025.csv"
)


def clean(x):

    if pd.isna(x):
        return ""

    x=str(x).lower()

    replacements={
        "hawai'i":"hawaii",
        "miami (fl)":"miami",
        "st.":"state",
    }

    for a,b in replacements.items():
        x=x.replace(a,b)

    x=re.sub(
        r"[^a-z0-9 ]",
        "",
        x
    )

    return re.sub(
        r"\s+",
        " ",
        x
    ).strip()



def main():

    conf=pd.read_csv(CONF_FILE)

    bets=pd.read_csv(BET_FILE)


    print("Conference rows:",len(conf))
    print("Bet rows:",len(bets))


    # Build team-season reference table

    team_conf=pd.concat(
        [
            conf[
                [
                    "season",
                    "team",
                    "team_conference",
                    "team_tier",
                    "team_changed_conference",
                    "team_previous_conference",
                    "team_years_since_move"
                ]
            ].rename(
                columns={
                    "team_conference":"conference",
                    "team_tier":"tier",
                    "team_changed_conference":"changed_conference",
                    "team_previous_conference":"previous_conference",
                    "team_years_since_move":"years_since_move"
                }
            ),

            conf[
                [
                    "season",
                    "opponent",
                    "opponent_conference",
                    "opponent_tier",
                    "opponent_changed_conference",
                    "opponent_previous_conference",
                    "opponent_years_since_move"
                ]
            ].rename(
                columns={
                    "opponent":"team",
                    "opponent_conference":"conference",
                    "opponent_tier":"tier",
                    "opponent_changed_conference":"changed_conference",
                    "opponent_previous_conference":"previous_conference",
                    "opponent_years_since_move":"years_since_move"
                }
            )
        ]
    ).drop_duplicates()


    for df in [team_conf,bets]:

        df["team_key"]=df["team"].map(clean)


    team_conf=team_conf.drop_duplicates(
        ["season","team_key"]
    )


    merged=bets.copy()

    merged["team_key"]=merged["team"].map(clean)
    merged["opp_key"]=merged["opponent"].map(clean)


    # team lookup

    merged=merged.merge(
        team_conf,
        left_on=[
            "season",
            "team_key"
        ],
        right_on=[
            "season",
            "team_key"
        ],
        how="left"
    )


    merged=merged.rename(
        columns={
            "conference":"team_conference",
            "tier":"team_tier",
            "changed_conference":"team_changed_conference",
            "previous_conference":"team_previous_conference",
            "years_since_move":"team_years_since_move"
        }
    )


    # opponent lookup

    opp_conf=team_conf.rename(
        columns={
            "team_key":"opp_key",
            "conference":"opponent_conference",
            "tier":"opponent_tier",
            "changed_conference":"opponent_changed_conference",
            "previous_conference":"opponent_previous_conference",
            "years_since_move":"opponent_years_since_move"
        }
    )


    merged=merged.merge(
        opp_conf[
            [
                "season",
                "opp_key",
                "opponent_conference",
                "opponent_tier",
                "opponent_changed_conference",
                "opponent_previous_conference",
                "opponent_years_since_move"
            ]
        ],
        on=[
            "season",
            "opp_key"
        ],
        how="left"
    )


    def matchup(row):

        if row.team_tier=="P4" and row.opponent_tier=="P4":
            return "P4_vs_P4"

        if row.team_tier=="P4" and row.opponent_tier=="G6":
            return "P4_vs_G6"

        if row.team_tier=="G6" and row.opponent_tier=="P4":
            return "G6_vs_P4"

        if row.team_tier=="G6" and row.opponent_tier=="G6":
            return "G6_vs_G6"

        return "Other"


    merged["conference_matchup_type"]=merged.apply(
        matchup,
        axis=1
    )


    merged["favorite_status"]=np.where(
        merged["spread"]<0,
        "Favorite",
        np.where(
            merged["spread"]>0,
            "Underdog",
            "Pickem"
        )
    )


    cols=[
        "season",
        "week",
        "date",
        "game_id",
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
        "home_away",
        "spread",
        "favorite_status",
        "ats_margin",
        "ats_result",
        "team_closing_spread",
        "team_clv"
    ]


    out=merged[
        [c for c in cols if c in merged.columns]
    ]


    out.to_csv(
        OUT,
        index=False
    )


    print()
    print("Created:")
    print(OUT)

    print()
    print("Rows:",len(out))

    print()
    print(out["conference_matchup_type"].value_counts())

    print()
    print("Missing conference:",
          out["team_conference"].isna().sum(),
          out["opponent_conference"].isna().sum())


if __name__=="__main__":
    main()
