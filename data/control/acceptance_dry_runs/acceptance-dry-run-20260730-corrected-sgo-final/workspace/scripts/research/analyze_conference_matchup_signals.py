from pathlib import Path
import pandas as pd
import numpy as np

INPUT = Path("data/research/conference_matchup_history_2021_2025.csv")

OUT_DIR = Path("data/research/conference_matchup_signals")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_SUMMARY = OUT_DIR / "conference_matchup_signal_summary.csv"
OUT_DETAIL = OUT_DIR / "conference_matchup_signal_detail.csv"


def pct(x):
    if pd.isna(x):
        return ""
    return round(x * 100, 2)


def summarize(df, label):
    if len(df) == 0:
        return {
            "segment": label,
            "games": 0,
            "ats_wins": 0,
            "ats_losses": 0,
            "ats_pushes": 0,
            "ats_pct": None,
            "avg_ats_margin": None,
            "avg_spread": None,
        }

    ats = df["ats_result"].value_counts()

    return {
        "segment": label,
        "games": len(df),
        "ats_wins": int(ats.get("W", 0)),
        "ats_losses": int(ats.get("L", 0)),
        "ats_pushes": int(ats.get("P", 0)),
        "ats_pct": pct(
            ats.get("W", 0) /
            max(1, ats.get("W", 0) + ats.get("L", 0))
        ),
        "avg_ats_margin": round(df["ats_margin"].mean(), 3),
        "avg_spread": round(df["team_spread"].mean(), 3),
    }


def main():

    df = pd.read_csv(INPUT)

    print("Loaded:", len(df))

    # normalize
    df["conference_matchup_type"] = df["conference_matchup_type"].fillna("Other")

    df["is_favorite"] = np.where(
        df["team_spread"] < 0,
        "Favorite",
        np.where(df["team_spread"] > 0, "Underdog", "Pickem")
    )

    # --------------------------------------------------
    # Basic conference matchup splits
    # --------------------------------------------------

    rows = []

    for c in sorted(df["conference_matchup_type"].unique()):
        rows.append(
            summarize(
                df[df["conference_matchup_type"] == c],
                c
            )
        )

    # Favorite / dog splits
    for c in [
        "P4_vs_G6",
        "G6_vs_P4",
        "P4_vs_P4",
        "G6_vs_G6"
    ]:
        for role in [
            "Favorite",
            "Underdog"
        ]:
            rows.append(
                summarize(
                    df[
                        (df["conference_matchup_type"] == c)
                        &
                        (df["is_favorite"] == role)
                    ],
                    f"{c} {role}"
                )
            )


    # --------------------------------------------------
    # Home / Away splits if fields exist
    # --------------------------------------------------

    if "home_away" in df.columns:

        for c in sorted(df["conference_matchup_type"].unique()):

            for loc in df["home_away"].dropna().unique():

                rows.append(
                    summarize(
                        df[
                            (df["conference_matchup_type"] == c)
                            &
                            (df["home_away"] == loc)
                        ],
                        f"{c} {loc}"
                    )
                )


    summary = pd.DataFrame(rows)

    summary.to_csv(
        OUT_SUMMARY,
        index=False
    )


    # --------------------------------------------------
    # Detail audit
    # --------------------------------------------------

    detail_cols = [
        c for c in [
            "season",
            "date",
            "team_clean",
            "opponent_clean",
            "conference_matchup_type",
            "team_spread",
            "ats_margin",
            "ats_result",
            "total_line",
            "total_margin",
            "total_result",
            "is_favorite"
        ]
        if c in df.columns
    ]

    df[detail_cols].to_csv(
        OUT_DETAIL,
        index=False
    )


    print()
    print("Created:")
    print(OUT_SUMMARY)
    print("Rows:", len(summary))

    print()
    print(summary.sort_values(
        ["games","ats_pct"],
        ascending=[False,False]
    ).head(25).to_string(index=False))

    print()
    print("Created:")
    print(OUT_DETAIL)
    print("Rows:", len(df))


if __name__ == "__main__":
    main()
