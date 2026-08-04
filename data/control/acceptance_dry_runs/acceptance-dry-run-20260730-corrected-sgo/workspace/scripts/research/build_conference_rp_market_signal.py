from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

INPUT = BASE / "data/research/conference_returning_production_signal_games.csv"

OUT_DETAIL = BASE / "data/research/conference_rp_market_signal_games.csv"
OUT_SUMMARY_ALL = BASE / "data/research/conference_rp_market_signal_summary_all.csv"
OUT_SUMMARY = BASE / "data/research/conference_rp_market_signal_summary.csv"
OUT_AUDIT = BASE / "data/audits/conference_rp_market_signal_audit.csv"

MIN_SAMPLE = 15


def rp_bucket(edge):
    if pd.isna(edge):
        return "missing"

    edge = abs(float(edge))

    if edge >= 25:
        return "25_plus"
    if edge >= 15:
        return "15_to_25"
    if edge >= 5:
        return "5_to_15"
    return "neutral"


def spread_bucket(spread):
    if pd.isna(spread):
        return "missing"

    spread = float(spread)

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


def role_from_spread(spread):
    if pd.isna(spread):
        return "Unknown"
    if spread < 0:
        return "Favorite"
    if spread > 0:
        return "Underdog"
    return "Pick"


def flip_result(result):
    if result == "W":
        return "L"
    if result == "L":
        return "W"
    return result


def flip_matchup_type(value):
    if pd.isna(value):
        return value

    mapping = {
        "P4_vs_G6": "G6_vs_P4",
        "G6_vs_P4": "P4_vs_G6",
        "P4_vs_P4": "P4_vs_P4",
        "G6_vs_G6": "G6_vs_G6",
        "Other": "Other",
        "Other_vs_Other": "Other_vs_Other",
    }

    return mapping.get(value, value)


def confidence_tier(games):
    if games >= 75:
        return "High"
    if games >= 40:
        return "Medium"
    if games >= MIN_SAMPLE:
        return "Exploratory"
    return "Insufficient"


def main():
    print("Loading RP signal games")

    df = pd.read_csv(INPUT)

    print("Raw rows loaded:", len(df))

    required = [
        "season",
        "week",
        "game_id",
        "team",
        "opponent",
        "conference_matchup_type",
        "overall_rp_edge",
        "spread",
        "ats_result",
        "team_clv",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    key = ["season", "game_id", "team", "opponent"]

    duplicate_rows = int(df.duplicated(subset=key, keep=False).sum())
    unique_before = int(df[key].drop_duplicates().shape[0])

    # The source contains repeated rows for multiple RP case/threshold labels.
    # Keep one canonical row per team-side game before changing perspective.
    canonical = (
        df.sort_values(key)
        .drop_duplicates(subset=key, keep="first")
        .copy()
    )

    print("Duplicate source rows:", duplicate_rows)
    print("Unique team-side games:", unique_before)
    print("Canonical rows used:", len(canonical))

    rows = []

    for _, r in canonical.iterrows():
        edge = r["overall_rp_edge"]

        if pd.isna(edge) or float(edge) == 0:
            continue

        if float(edge) > 0:
            rp_team = r["team"]
            rp_opponent = r["opponent"]
            matchup_type = r["conference_matchup_type"]
            rp_spread = r["spread"]
            ats_result = r["ats_result"]
            rp_clv = r["team_clv"]
            source_flipped = False
        else:
            rp_team = r["opponent"]
            rp_opponent = r["team"]
            matchup_type = flip_matchup_type(r["conference_matchup_type"])
            rp_spread = -float(r["spread"]) if pd.notna(r["spread"]) else pd.NA
            ats_result = flip_result(r["ats_result"])
            rp_clv = -float(r["team_clv"]) if pd.notna(r["team_clv"]) else pd.NA
            source_flipped = True

        rows.append(
            {
                "season": r["season"],
                "week": r["week"],
                "game_id": r["game_id"],
                "rp_team": rp_team,
                "rp_opponent": rp_opponent,
                "conference_matchup_type": matchup_type,
                "rp_edge": abs(float(edge)),
                "rp_edge_bucket": rp_bucket(edge),
                "rp_team_role": role_from_spread(rp_spread),
                "rp_team_spread": rp_spread,
                "spread_bucket": spread_bucket(rp_spread),
                "rp_team_ats_result": ats_result,
                "rp_team_clv": rp_clv,
                "source_flipped": source_flipped,
            }
        )

    signal = pd.DataFrame(rows)

    perspective_key = ["season", "game_id", "rp_team", "rp_opponent"]
    perspective_duplicates = int(
        signal.duplicated(subset=perspective_key, keep=False).sum()
    )

    signal = (
        signal.sort_values(perspective_key)
        .drop_duplicates(subset=perspective_key, keep="first")
        .copy()
    )

    print("Perspective duplicate rows:", perspective_duplicates)
    print("Unique RP-advantage games:", len(signal))

    OUT_DETAIL.parent.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)

    signal.to_csv(OUT_DETAIL, index=False)

    classified = signal[
        signal["conference_matchup_type"].notna()
    ].copy()

    summary_all = (
        classified
        .groupby(
            [
                "conference_matchup_type",
                "rp_edge_bucket",
                "spread_bucket",
            ],
            dropna=False,
        )
        .agg(
            games=("rp_team_ats_result", "count"),
            wins=("rp_team_ats_result", lambda x: (x == "W").sum()),
            losses=("rp_team_ats_result", lambda x: (x == "L").sum()),
            pushes=("rp_team_ats_result", lambda x: (x == "P").sum()),
            avg_clv=("rp_team_clv", "mean"),
        )
        .reset_index()
    )

    graded = summary_all["wins"] + summary_all["losses"]
    summary_all["ats_win_pct"] = (
        summary_all["wins"] / graded.where(graded > 0)
    )
    summary_all["ats_edge_pct"] = (
        summary_all["ats_win_pct"] * 100 - 50
    )
    summary_all["confidence"] = (
        summary_all["games"].apply(confidence_tier)
    )

    summary_all = summary_all.sort_values(
        ["ats_win_pct", "games"],
        ascending=[False, False],
        na_position="last",
    )

    summary = summary_all[
        summary_all["games"] >= MIN_SAMPLE
    ].copy()

    summary_all.to_csv(OUT_SUMMARY_ALL, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)

    audit = pd.DataFrame(
        [
            {"metric": "raw_rows", "value": len(df)},
            {"metric": "duplicate_source_rows", "value": duplicate_rows},
            {"metric": "unique_team_side_games", "value": unique_before},
            {"metric": "canonical_rows_used", "value": len(canonical)},
            {"metric": "perspective_duplicate_rows", "value": perspective_duplicates},
            {"metric": "unique_rp_advantage_games", "value": len(signal)},
            {
                "metric": "classified_rp_advantage_games",
                "value": int(signal["conference_matchup_type"].notna().sum()),
            },
            {
                "metric": "unclassified_rp_advantage_games",
                "value": int(signal["conference_matchup_type"].isna().sum()),
            },
            {"metric": "minimum_summary_sample", "value": MIN_SAMPLE},
        ]
    )
    audit.to_csv(OUT_AUDIT, index=False)

    print()
    print("Created:")
    print(OUT_DETAIL)
    print(OUT_SUMMARY_ALL)
    print(OUT_SUMMARY)
    print(OUT_AUDIT)

    print()
    print("Filtered summary:")
    if summary.empty:
        print(f"No buckets met the minimum sample of {MIN_SAMPLE}.")
    else:
        print(summary.head(50).to_string(index=False))


if __name__ == "__main__":
    main()
