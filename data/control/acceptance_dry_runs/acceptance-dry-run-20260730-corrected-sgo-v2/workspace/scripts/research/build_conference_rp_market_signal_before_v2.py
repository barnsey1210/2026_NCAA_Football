from pathlib import Path
import pandas as pd

BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

INPUT = BASE / "data/research/conference_returning_production_signal_games.csv"
OUT_DETAIL = BASE / "data/research/conference_rp_market_signal_games.csv"
OUT_SUMMARY = BASE / "data/research/conference_rp_market_signal_summary.csv"


def bucket(x):
    if pd.isna(x):
        return "missing"
    x = abs(x)
    if x >= 25:
        return "25_plus"
    if x >= 15:
        return "15_to_25"
    if x >= 5:
        return "5_to_15"
    return "neutral"


def spread_bucket(spread):
    if pd.isna(spread):
        return "missing"
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


def flip_result(x):
    if x == "W":
        return "L"
    if x == "L":
        return "W"
    return x


def main():

    print("Loading RP signal games")

    df = pd.read_csv(INPUT)

    print("Rows loaded:", len(df))

    rows = []

    for _, r in df.iterrows():

        edge = r["overall_rp_edge"]

        if pd.isna(edge):
            continue

        if edge > 0:
            rows.append({
                "season": r["season"],
                "week": r["week"],
                "team": r["team"],
                "opponent": r["opponent"],
                "conference_matchup_type": r["conference_matchup_type"],
                "rp_edge": edge,
                "rp_edge_bucket": bucket(edge),
                "role": r["role"],
                "spread": r["spread"],
                "spread_bucket": spread_bucket(r["spread"]),
                "ats_result": r["ats_result"],
                "team_clv": r["team_clv"]
            })

        else:
            rows.append({
                "season": r["season"],
                "week": r["week"],
                "team": r["opponent"],
                "opponent": r["team"],
                "conference_matchup_type": r["conference_matchup_type"],
                "rp_edge": abs(edge),
                "rp_edge_bucket": bucket(edge),
                "role": "Underdog" if r["role"] == "Favorite" else "Favorite",
                "spread": -r["spread"],
                "spread_bucket": spread_bucket(-r["spread"]),
                "ats_result": flip_result(r["ats_result"]),
                "team_clv": r["team_clv"]
            })

    signal = pd.DataFrame(rows)

    print("RP advantage rows:", len(signal))

    signal.to_csv(OUT_DETAIL, index=False)

    summary = (
        signal
        .groupby(
            ["conference_matchup_type", "rp_edge_bucket", "spread_bucket"],
            dropna=False
        )
        .agg(
            games=("ats_result","count"),
            wins=("ats_result", lambda x:(x=="W").sum()),
            losses=("ats_result", lambda x:(x=="L").sum()),
            avg_clv=("team_clv","mean")
        )
        .reset_index()
    )

    summary["ats_win_pct"] = summary["wins"] / summary["games"]
    summary["ats_edge_pct"] = summary["ats_win_pct"] * 100 - 50

    summary = summary[summary["games"] >= 20]

    summary = summary.sort_values(
        ["ats_win_pct","games"],
        ascending=[False, False]
    )

    summary.to_csv(OUT_SUMMARY, index=False)

    print("Created:")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)

    print(summary.head(50).to_string(index=False))


if __name__ == "__main__":
    main()
