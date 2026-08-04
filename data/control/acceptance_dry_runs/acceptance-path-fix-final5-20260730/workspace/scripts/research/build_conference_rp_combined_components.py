from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

INPUT = BASE / "data/research/conference_returning_production_signal_games.csv"

OUT_GAMES = BASE / "data/research/conference_rp_combined_component_games.csv"
OUT_RULE_DETAIL = BASE / "data/research/conference_rp_combined_component_rule_detail.csv"
OUT_SUMMARY = BASE / "data/research/conference_rp_combined_component_summary.csv"
OUT_FOCUS = BASE / "data/research/conference_rp_combined_component_focus.csv"
OUT_AUDIT = BASE / "data/audits/conference_rp_combined_component_audit.csv"

MIN_SAMPLE = 15


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


def role_from_spread(spread):
    if pd.isna(spread):
        return "Unknown"
    if float(spread) < 0:
        return "Favorite"
    if float(spread) > 0:
        return "Underdog"
    return "Pick"


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
        return "Back continuity-edge team"
    if win_pct <= 0.45:
        return "Fade continuity-edge team"
    return "Neutral"


def profile_label(off_edge, def_edge):
    if off_edge >= 5 and def_edge >= 5:
        return "balanced_both_5_plus"

    if off_edge >= 15 and def_edge >= 0:
        return "offense_15_plus_def_nonnegative"

    if def_edge >= 15 and off_edge >= 0:
        return "defense_15_plus_off_nonnegative"

    if off_edge >= 15 and def_edge < 0:
        return "offense_led_mixed"

    if def_edge >= 15 and off_edge < 0:
        return "defense_led_mixed"

    if off_edge > 0 and def_edge > 0:
        return "balanced_both_positive"

    if off_edge >= 5 and def_edge <= -5:
        return "offense_positive_defense_negative"

    if def_edge >= 5 and off_edge <= -5:
        return "defense_positive_offense_negative"

    return "small_or_mixed"


def rule_flags(off_edge, def_edge):
    return {
        "both_positive": off_edge > 0 and def_edge > 0,
        "both_5_plus": off_edge >= 5 and def_edge >= 5,
        "offense_15_plus": off_edge >= 15,
        "defense_15_plus": def_edge >= 15,
        "offense_15_plus_def_nonnegative": off_edge >= 15 and def_edge >= 0,
        "defense_15_plus_off_nonnegative": def_edge >= 15 and off_edge >= 0,
        "offense_25_plus": off_edge >= 25,
        "defense_25_plus": def_edge >= 25,
        "either_component_25_plus": off_edge >= 25 or def_edge >= 25,
        "both_15_plus": off_edge >= 15 and def_edge >= 15,
        "offense_led_mixed": off_edge >= 15 and def_edge < 0,
        "defense_led_mixed": def_edge >= 15 and off_edge < 0,
    }


def summarize(df, group_cols):
    out = (
        df.groupby(group_cols, dropna=False)
        .agg(
            games=("continuity_team_ats_result", "count"),
            wins=("continuity_team_ats_result", lambda x: (x == "W").sum()),
            losses=("continuity_team_ats_result", lambda x: (x == "L").sum()),
            pushes=("continuity_team_ats_result", lambda x: (x == "P").sum()),
            avg_ats_margin=("continuity_team_ats_margin", "mean"),
            median_ats_margin=("continuity_team_ats_margin", "median"),
            avg_clv=("continuity_team_clv", "mean"),
            clv_games=("continuity_team_clv", "count"),
            seasons_present=("season", "nunique"),
            avg_offense_edge=("offense_vs_defense_edge", "mean"),
            avg_defense_edge=("defense_vs_offense_edge", "mean"),
        )
        .reset_index()
    )

    decisions = out["wins"] + out["losses"]
    out["ats_win_pct"] = out["wins"] / decisions.where(decisions > 0)
    out["ats_edge_pct"] = out["ats_win_pct"] * 100 - 50
    out["confidence"] = out["games"].apply(confidence_tier)
    out["signal"] = out["ats_win_pct"].apply(signal_label)

    return out


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

    game_rows = []

    for _, r in canonical.iterrows():
        off_edge = r["off_vs_def_rp_edge"]
        def_edge = r["def_vs_off_rp_edge"]

        if pd.isna(off_edge) or pd.isna(def_edge):
            continue

        off_edge = float(off_edge)
        def_edge = float(def_edge)

        # Orient each game toward the team with the stronger combined
        # offense-vs-defense plus defense-vs-offense continuity position.
        combined_edge = off_edge + def_edge

        if combined_edge >= 0:
            continuity_team = r["team"]
            continuity_opponent = r["opponent"]
            matchup_type = r["conference_matchup_type"]
            team_spread = r["spread"]
            ats_result = r["ats_result"]
            ats_margin = r["ats_margin"]
            team_clv = r["team_clv"]
            oriented_off = off_edge
            oriented_def = def_edge
            source_flipped = False
        else:
            continuity_team = r["opponent"]
            continuity_opponent = r["team"]
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

            # When perspective flips:
            # opponent offense vs original team defense = -original def edge
            # opponent defense vs original team offense = -original off edge
            oriented_off = -def_edge
            oriented_def = -off_edge
            source_flipped = True

        game_rows.append(
            {
                "season": r["season"],
                "week": r["week"],
                "date": r.get("date", pd.NA),
                "game_id": r["game_id"],
                "continuity_team": continuity_team,
                "continuity_opponent": continuity_opponent,
                "conference_matchup_type": matchup_type,
                "continuity_team_role": role_from_spread(team_spread),
                "continuity_team_spread": team_spread,
                "offense_vs_defense_edge": oriented_off,
                "defense_vs_offense_edge": oriented_def,
                "combined_component_edge": oriented_off + oriented_def,
                "component_profile": profile_label(oriented_off, oriented_def),
                "continuity_team_ats_result": ats_result,
                "continuity_team_ats_margin": ats_margin,
                "continuity_team_clv": team_clv,
                "source_flipped": source_flipped,
            }
        )

    games = pd.DataFrame(game_rows)

    perspective_key = [
        "season",
        "game_id",
        "continuity_team",
        "continuity_opponent",
    ]

    perspective_duplicate_rows = int(
        games.duplicated(subset=perspective_key, keep=False).sum()
    )

    games = (
        games.sort_values(perspective_key)
        .drop_duplicates(subset=perspective_key, keep="first")
        .copy()
    )

    print("Perspective duplicate rows:", perspective_duplicate_rows)
    print("Unique combined-component games:", len(games))

    rule_rows = []

    for _, r in games.iterrows():
        flags = rule_flags(
            r["offense_vs_defense_edge"],
            r["defense_vs_offense_edge"],
        )

        for rule_name, qualifies in flags.items():
            if not qualifies:
                continue

            row = r.to_dict()
            row["combined_rule"] = rule_name
            rule_rows.append(row)

    rule_detail = pd.DataFrame(rule_rows)

    classified = rule_detail[
        rule_detail["conference_matchup_type"].notna()
    ].copy()

    summary = summarize(
        classified,
        ["combined_rule", "conference_matchup_type"],
    )

    summary = summary.sort_values(
        ["combined_rule", "games", "ats_win_pct"],
        ascending=[True, False, False],
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

    OUT_GAMES.parent.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)

    games.to_csv(OUT_GAMES, index=False)
    rule_detail.to_csv(OUT_RULE_DETAIL, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
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
                "metric": "unique_combined_component_games",
                "value": len(games),
            },
            {
                "metric": "overlapping_rule_observations",
                "value": len(rule_detail),
            },
            {
                "metric": "classified_rule_observations",
                "value": len(classified),
            },
            {"metric": "minimum_focus_sample", "value": MIN_SAMPLE},
        ]
    )

    audit.to_csv(OUT_AUDIT, index=False)

    print()
    print("Created:")
    print(OUT_GAMES)
    print(OUT_RULE_DETAIL)
    print(OUT_SUMMARY)
    print(OUT_FOCUS)
    print(OUT_AUDIT)

    print()
    print("Combined component focus:")
    if focus.empty:
        print(f"No focus rules met the minimum sample of {MIN_SAMPLE}.")
    else:
        print(focus.to_string(index=False))


if __name__ == "__main__":
    main()
