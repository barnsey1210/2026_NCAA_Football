from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

INPUT = BASE / "data/research/conference_returning_production_signal_games.csv"

OUT_DETAIL = BASE / "data/research/conference_rp_broad_rule_games.csv"
OUT_OVERALL = BASE / "data/research/conference_rp_broad_rules_overall.csv"
OUT_BY_MATCHUP = BASE / "data/research/conference_rp_broad_rules_by_matchup.csv"
OUT_RANKED = BASE / "data/research/conference_rp_broad_rules_ranked.csv"
OUT_AUDIT = BASE / "data/audits/conference_rp_broad_rules_audit.csv"

MIN_SAMPLE = 15


def rp_band(edge):
    if pd.isna(edge):
        return "missing"

    edge = abs(float(edge))

    if edge >= 25:
        return "25_plus"
    if edge >= 15:
        return "15_to_24_9"
    if edge >= 5:
        return "5_to_14_9"

    return "under_5"


def broad_spread_band(spread):
    if pd.isna(spread):
        return "missing"

    spread = float(spread)

    if spread >= 7:
        return "dog_7_plus"
    if spread > 0:
        return "dog_0_5_to_6_5"
    if spread >= -6.5:
        return "pick_to_fav_6_5"
    if spread >= -13.5:
        return "fav_7_to_13_5"

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
    if games >= 50:
        return "Supported"
    if games >= 30:
        return "Promising"
    if games >= 15:
        return "Exploratory"
    return "Insufficient"


def signal_label(win_pct):
    if pd.isna(win_pct):
        return "No graded results"
    if win_pct >= 0.55:
        return "Back RP-edge team"
    if win_pct <= 0.45:
        return "Fade RP-edge team"
    return "Neutral"


def summarize(df, group_cols):
    summary = (
        df.groupby(group_cols, dropna=False)
        .agg(
            games=("rp_team_ats_result", "count"),
            wins=("rp_team_ats_result", lambda x: (x == "W").sum()),
            losses=("rp_team_ats_result", lambda x: (x == "L").sum()),
            pushes=("rp_team_ats_result", lambda x: (x == "P").sum()),
            avg_ats_margin=("rp_team_ats_margin", "mean"),
            median_ats_margin=("rp_team_ats_margin", "median"),
            avg_clv=("rp_team_clv", "mean"),
            clv_games=("rp_team_clv", "count"),
        )
        .reset_index()
    )

    decisions = summary["wins"] + summary["losses"]

    summary["ats_win_pct"] = (
        summary["wins"] / decisions.where(decisions > 0)
    )

    summary["ats_edge_pct"] = (
        summary["ats_win_pct"] * 100 - 50
    )

    summary["confidence"] = summary["games"].apply(confidence_tier)
    summary["signal"] = summary["ats_win_pct"].apply(signal_label)

    return summary


def main():
    print("Loading original RP signal games")

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
        "ats_margin",
        "team_clv",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    source_key = ["season", "game_id", "team", "opponent"]

    duplicate_source_rows = int(
        df.duplicated(subset=source_key, keep=False).sum()
    )

    canonical = (
        df.sort_values(source_key)
        .drop_duplicates(subset=source_key, keep="first")
        .copy()
    )

    print("Duplicate source rows:", duplicate_source_rows)
    print("Canonical team-side rows:", len(canonical))

    rows = []

    for _, r in canonical.iterrows():
        edge = r["overall_rp_edge"]

        if pd.isna(edge) or abs(float(edge)) < 5:
            continue

        if float(edge) > 0:
            rp_team = r["team"]
            rp_opponent = r["opponent"]
            matchup_type = r["conference_matchup_type"]
            rp_spread = r["spread"]
            rp_ats_result = r["ats_result"]
            rp_ats_margin = r["ats_margin"]
            rp_clv = r["team_clv"]
            source_flipped = False
        else:
            rp_team = r["opponent"]
            rp_opponent = r["team"]
            matchup_type = flip_matchup_type(r["conference_matchup_type"])
            rp_spread = -float(r["spread"]) if pd.notna(r["spread"]) else pd.NA
            rp_ats_result = flip_result(r["ats_result"])
            rp_ats_margin = (
                -float(r["ats_margin"])
                if pd.notna(r["ats_margin"])
                else pd.NA
            )
            rp_clv = (
                -float(r["team_clv"])
                if pd.notna(r["team_clv"])
                else pd.NA
            )
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
                "rp_band": rp_band(edge),
                "rp_team_role": role_from_spread(rp_spread),
                "rp_team_spread": rp_spread,
                "broad_spread_band": broad_spread_band(rp_spread),
                "rp_team_ats_result": rp_ats_result,
                "rp_team_ats_margin": rp_ats_margin,
                "rp_team_clv": rp_clv,
                "source_flipped": source_flipped,
            }
        )

    detail = pd.DataFrame(rows)

    perspective_key = ["season", "game_id", "rp_team", "rp_opponent"]

    perspective_duplicate_rows = int(
        detail.duplicated(subset=perspective_key, keep=False).sum()
    )

    detail = (
        detail.sort_values(perspective_key)
        .drop_duplicates(subset=perspective_key, keep="first")
        .copy()
    )

    print("Perspective duplicate rows:", perspective_duplicate_rows)
    print("Unique RP-edge games:", len(detail))

    OUT_DETAIL.parent.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)

    detail.to_csv(OUT_DETAIL, index=False)

    # Main broad rules across every matchup type.
    overall = summarize(
        detail,
        ["rp_band", "broad_spread_band"],
    )

    # Secondary broad rules split by conference/tier matchup.
    by_matchup = summarize(
        detail[detail["conference_matchup_type"].notna()].copy(),
        [
            "conference_matchup_type",
            "rp_band",
            "broad_spread_band",
        ],
    )

    overall = overall.sort_values(
        ["games", "ats_win_pct"],
        ascending=[False, False],
        na_position="last",
    )

    by_matchup = by_matchup.sort_values(
        ["games", "ats_win_pct"],
        ascending=[False, False],
        na_position="last",
    )

    overall.to_csv(OUT_OVERALL, index=False)
    by_matchup.to_csv(OUT_BY_MATCHUP, index=False)

    overall_ranked = overall[overall["games"] >= MIN_SAMPLE].copy()
    overall_ranked["rule_level"] = "Overall"

    matchup_ranked = by_matchup[by_matchup["games"] >= MIN_SAMPLE].copy()
    matchup_ranked["rule_level"] = "By matchup"

    ranked = pd.concat(
        [overall_ranked, matchup_ranked],
        ignore_index=True,
        sort=False,
    )

    confidence_order = {
        "Supported": 0,
        "Promising": 1,
        "Exploratory": 2,
        "Insufficient": 3,
    }

    ranked["confidence_order"] = ranked["confidence"].map(confidence_order)
    ranked["absolute_ats_edge"] = ranked["ats_edge_pct"].abs()

    ranked = ranked.sort_values(
        [
            "confidence_order",
            "absolute_ats_edge",
            "games",
        ],
        ascending=[True, False, False],
        na_position="last",
    ).drop(columns=["confidence_order", "absolute_ats_edge"])

    ranked.to_csv(OUT_RANKED, index=False)

    audit = pd.DataFrame(
        [
            {"metric": "raw_rows", "value": len(df)},
            {
                "metric": "duplicate_source_rows",
                "value": duplicate_source_rows,
            },
            {
                "metric": "canonical_team_side_rows",
                "value": len(canonical),
            },
            {
                "metric": "perspective_duplicate_rows",
                "value": perspective_duplicate_rows,
            },
            {
                "metric": "unique_rp_edge_games",
                "value": len(detail),
            },
            {
                "metric": "overall_broad_rules",
                "value": len(overall),
            },
            {
                "metric": "matchup_broad_rules",
                "value": len(by_matchup),
            },
            {
                "metric": "ranked_rules_minimum_sample",
                "value": len(ranked),
            },
            {
                "metric": "minimum_sample",
                "value": MIN_SAMPLE,
            },
        ]
    )

    audit.to_csv(OUT_AUDIT, index=False)

    print()
    print("Created:")
    print(OUT_DETAIL)
    print(OUT_OVERALL)
    print(OUT_BY_MATCHUP)
    print(OUT_RANKED)
    print(OUT_AUDIT)

    print()
    print("Main broad rules:")
    print(
        overall[overall["games"] >= MIN_SAMPLE]
        .head(50)
        .to_string(index=False)
    )

    print()
    print("Ranked rules:")
    if ranked.empty:
        print(f"No rules met the minimum sample of {MIN_SAMPLE}.")
    else:
        print(ranked.head(50).to_string(index=False))


if __name__ == "__main__":
    main()
