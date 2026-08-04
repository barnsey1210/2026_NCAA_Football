from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

INPUT = BASE / "data/research/conference_returning_production_signal_games.csv"

OUT_DETAIL = BASE / "data/research/conference_rp_component_edge_games.csv"
OUT_SUMMARY = BASE / "data/research/conference_rp_component_edge_summary.csv"
OUT_ROLE = BASE / "data/research/conference_rp_component_edge_role_context.csv"
OUT_FOCUS = BASE / "data/research/conference_rp_component_edge_focus.csv"
OUT_AUDIT = BASE / "data/audits/conference_rp_component_edge_audit.csv"

MIN_EDGE = 5
MIN_SAMPLE = 15


def edge_band(edge):
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


def role_from_spread(spread):
    if pd.isna(spread):
        return "Unknown"
    if float(spread) < 0:
        return "Favorite"
    if float(spread) > 0:
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
        return "Back component-edge team"
    if win_pct <= 0.45:
        return "Fade component-edge team"
    return "Neutral"


def summarize(df, group_cols):
    out = (
        df.groupby(group_cols, dropna=False)
        .agg(
            games=("edge_team_ats_result", "count"),
            wins=("edge_team_ats_result", lambda x: (x == "W").sum()),
            losses=("edge_team_ats_result", lambda x: (x == "L").sum()),
            pushes=("edge_team_ats_result", lambda x: (x == "P").sum()),
            avg_ats_margin=("edge_team_ats_margin", "mean"),
            median_ats_margin=("edge_team_ats_margin", "median"),
            avg_clv=("edge_team_clv", "mean"),
            clv_games=("edge_team_clv", "count"),
            seasons_present=("season", "nunique"),
        )
        .reset_index()
    )

    decisions = out["wins"] + out["losses"]
    out["ats_win_pct"] = out["wins"] / decisions.where(decisions > 0)
    out["ats_edge_pct"] = out["ats_win_pct"] * 100 - 50
    out["confidence"] = out["games"].apply(confidence_tier)
    out["signal"] = out["ats_win_pct"].apply(signal_label)

    return out


def build_component_rows(canonical, component_name, edge_column):
    rows = []

    for _, r in canonical.iterrows():
        edge = r[edge_column]

        if pd.isna(edge) or abs(float(edge)) < MIN_EDGE:
            continue

        if float(edge) > 0:
            edge_team = r["team"]
            edge_opponent = r["opponent"]
            matchup_type = r["conference_matchup_type"]
            team_spread = r["spread"]
            ats_result = r["ats_result"]
            ats_margin = r["ats_margin"]
            team_clv = r["team_clv"]
            source_flipped = False
        else:
            edge_team = r["opponent"]
            edge_opponent = r["team"]
            matchup_type = flip_matchup_type(r["conference_matchup_type"])
            team_spread = -float(r["spread"]) if pd.notna(r["spread"]) else pd.NA
            ats_result = flip_result(r["ats_result"])
            ats_margin = (
                -float(r["ats_margin"])
                if pd.notna(r["ats_margin"])
                else pd.NA
            )
            team_clv = (
                -float(r["team_clv"])
                if pd.notna(r["team_clv"])
                else pd.NA
            )
            source_flipped = True

        rows.append(
            {
                "season": r["season"],
                "week": r["week"],
                "date": r.get("date", pd.NA),
                "game_id": r["game_id"],
                "component": component_name,
                "edge_team": edge_team,
                "edge_opponent": edge_opponent,
                "conference_matchup_type": matchup_type,
                "component_edge": abs(float(edge)),
                "component_edge_band": edge_band(edge),
                "edge_team_role": role_from_spread(team_spread),
                "edge_team_spread": team_spread,
                "edge_team_ats_result": ats_result,
                "edge_team_ats_margin": ats_margin,
                "edge_team_clv": team_clv,
                "source_flipped": source_flipped,
            }
        )

    return rows


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
        "off_vs_def_rp_edge",
        "def_vs_off_rp_edge",
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

    rows.extend(
        build_component_rows(
            canonical,
            component_name="offense_vs_opponent_defense",
            edge_column="off_vs_def_rp_edge",
        )
    )

    rows.extend(
        build_component_rows(
            canonical,
            component_name="defense_vs_opponent_offense",
            edge_column="def_vs_off_rp_edge",
        )
    )

    detail = pd.DataFrame(rows)

    perspective_key = [
        "season",
        "game_id",
        "component",
        "edge_team",
        "edge_opponent",
    ]

    perspective_duplicate_rows = int(
        detail.duplicated(subset=perspective_key, keep=False).sum()
    )

    detail = (
        detail.sort_values(perspective_key)
        .drop_duplicates(subset=perspective_key, keep="first")
        .copy()
    )

    print("Perspective duplicate rows:", perspective_duplicate_rows)
    print("Unique component-edge observations:", len(detail))

    classified = detail[
        detail["conference_matchup_type"].notna()
    ].copy()

    summary = summarize(
        classified,
        [
            "component",
            "conference_matchup_type",
            "component_edge_band",
        ],
    )

    role_context = summarize(
        classified,
        [
            "component",
            "conference_matchup_type",
            "component_edge_band",
            "edge_team_role",
        ],
    )

    summary = summary.sort_values(
        ["component", "conference_matchup_type", "games", "ats_win_pct"],
        ascending=[True, True, False, False],
        na_position="last",
    )

    role_context = role_context.sort_values(
        [
            "component",
            "conference_matchup_type",
            "component_edge_band",
            "games",
        ],
        ascending=[True, True, True, False],
        na_position="last",
    )

    focus_types = ["G6_vs_P4", "P4_vs_G6", "P4_vs_P4"]

    focus = summary[
        (summary["conference_matchup_type"].isin(focus_types))
        &
        (summary["games"] >= MIN_SAMPLE)
    ].copy()

    focus["absolute_ats_edge"] = focus["ats_edge_pct"].abs()

    confidence_order = {
        "Supported": 0,
        "Promising": 1,
        "Exploratory": 2,
        "Insufficient": 3,
    }

    focus["confidence_order"] = focus["confidence"].map(confidence_order)

    focus = focus.sort_values(
        ["confidence_order", "absolute_ats_edge", "games"],
        ascending=[True, False, False],
        na_position="last",
    ).drop(columns=["confidence_order", "absolute_ats_edge"])

    OUT_DETAIL.parent.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)

    detail.to_csv(OUT_DETAIL, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
    role_context.to_csv(OUT_ROLE, index=False)
    focus.to_csv(OUT_FOCUS, index=False)

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
                "metric": "component_edge_observations",
                "value": len(detail),
            },
            {
                "metric": "classified_component_observations",
                "value": len(classified),
            },
            {
                "metric": "unclassified_component_observations",
                "value": int(
                    detail["conference_matchup_type"].isna().sum()
                ),
            },
            {"metric": "minimum_edge", "value": MIN_EDGE},
            {"metric": "minimum_focus_sample", "value": MIN_SAMPLE},
        ]
    )

    audit.to_csv(OUT_AUDIT, index=False)

    print()
    print("Created:")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)
    print(OUT_ROLE)
    print(OUT_FOCUS)
    print(OUT_AUDIT)

    print()
    print("Component-edge focus:")
    if focus.empty:
        print(f"No focus rows met the minimum sample of {MIN_SAMPLE}.")
    else:
        print(focus.to_string(index=False))


if __name__ == "__main__":
    main()
