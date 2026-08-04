from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

INPUT = BASE / "data/research/returning_production_games_2021_2025_expanded.csv"

OUT_GAME = BASE / "data/research/expanded_rp_game_level_2021_2025.csv"
OUT_OVERALL = BASE / "data/research/expanded_rp_matchup_summary_2021_2025.csv"
OUT_COMPONENT = BASE / "data/research/expanded_rp_component_summary_2021_2025.csv"
OUT_COMBINED = BASE / "data/research/expanded_rp_combined_summary_2021_2025.csv"
OUT_FOCUS = BASE / "data/research/expanded_rp_focus_rules_2021_2025.csv"
OUT_AUDIT = BASE / "data/audits/expanded_rp_analysis_audit_2021_2025.csv"

MIN_EDGE = 5
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


def confidence(games):
    if games >= 75:
        return "High"
    if games >= 50:
        return "Supported"
    if games >= 30:
        return "Promising"
    if games >= 15:
        return "Exploratory"
    return "Insufficient"


def signal(win_pct):
    if pd.isna(win_pct):
        return "Neutral"
    if win_pct >= 0.55:
        return "Back edge team"
    if win_pct <= 0.45:
        return "Fade edge team"
    return "Neutral"


def summarize(df, group_cols, result_col, margin_col, clv_col, extra_aggs=None):
    aggs = {
        "games": (result_col, "count"),
        "wins": (result_col, lambda x: (x == "W").sum()),
        "losses": (result_col, lambda x: (x == "L").sum()),
        "pushes": (result_col, lambda x: (x == "P").sum()),
        "avg_ats_margin": (margin_col, "mean"),
        "median_ats_margin": (margin_col, "median"),
        "avg_clv": (clv_col, "mean"),
        "clv_games": (clv_col, "count"),
        "seasons_present": ("season", "nunique"),
    }

    if extra_aggs:
        aggs.update(extra_aggs)

    out = (
        df.groupby(group_cols, dropna=False)
        .agg(**aggs)
        .reset_index()
    )

    decisions = out["wins"] + out["losses"]
    out["ats_win_pct"] = out["wins"] / decisions.where(decisions > 0)
    out["ats_edge_pct"] = out["ats_win_pct"] * 100 - 50
    out["confidence"] = out["games"].apply(confidence)
    out["signal"] = out["ats_win_pct"].apply(signal)

    return out


def build_one_row_per_game(raw):
    required = [
        "season",
        "week",
        "game_id",
        "team",
        "opponent",
        "spread",
        "ats_result",
        "ats_margin",
        "team_clv",
        "conference_matchup_type",
        "team_overall",
        "team_offense",
        "team_defense",
        "opp_overall",
        "opp_offense",
        "opp_defense",
        "overall_rp_edge",
        "off_vs_def_rp_edge",
        "def_vs_off_rp_edge",
    ]

    missing = [c for c in required if c not in raw.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    complete = raw[
        raw["team_overall"].notna()
        &
        raw["opp_overall"].notna()
    ].copy()

    # Exactly one source row per game.
    base = (
        complete.sort_values(["season", "game_id", "team"])
        .drop_duplicates(subset=["season", "game_id"], keep="first")
        .copy()
    )

    rows = []

    for _, r in base.iterrows():
        overall_edge = float(r["overall_rp_edge"])
        off_edge = float(r["off_vs_def_rp_edge"])
        def_edge = float(r["def_vs_off_rp_edge"])

        if overall_edge >= 0:
            rp_team = r["team"]
            rp_opponent = r["opponent"]
            matchup = r["conference_matchup_type"]
            rp_spread = r["spread"]
            rp_result = r["ats_result"]
            rp_margin = r["ats_margin"]
            rp_clv = r["team_clv"]
            oriented_overall = overall_edge
            oriented_off = off_edge
            oriented_def = def_edge
            flipped = False
        else:
            rp_team = r["opponent"]
            rp_opponent = r["team"]
            matchup = flip_matchup_type(r["conference_matchup_type"])
            rp_spread = -float(r["spread"]) if pd.notna(r["spread"]) else pd.NA
            rp_result = flip_result(r["ats_result"])
            rp_margin = -float(r["ats_margin"]) if pd.notna(r["ats_margin"]) else pd.NA
            rp_clv = -float(r["team_clv"]) if pd.notna(r["team_clv"]) else pd.NA
            oriented_overall = -overall_edge
            oriented_off = -def_edge
            oriented_def = -off_edge
            flipped = True

        rows.append(
            {
                "season": r["season"],
                "week": r["week"],
                "game_id": r["game_id"],
                "rp_team": rp_team,
                "rp_opponent": rp_opponent,
                "conference_matchup_type": matchup,
                "overall_rp_edge": oriented_overall,
                "overall_rp_band": edge_band(oriented_overall),
                "offense_vs_defense_edge": oriented_off,
                "defense_vs_offense_edge": oriented_def,
                "rp_team_spread": rp_spread,
                "rp_team_ats_result": rp_result,
                "rp_team_ats_margin": rp_margin,
                "rp_team_clv": rp_clv,
                "source_flipped": flipped,
            }
        )

    return pd.DataFrame(rows)


def build_component_rows(raw):
    complete = raw[
        raw["team_overall"].notna()
        &
        raw["opp_overall"].notna()
    ].copy()

    base = (
        complete.sort_values(["season", "game_id", "team"])
        .drop_duplicates(subset=["season", "game_id"], keep="first")
        .copy()
    )

    rows = []

    for _, r in base.iterrows():
        component_specs = [
            (
                "offense_vs_opponent_defense",
                float(r["off_vs_def_rp_edge"]),
                float(r["def_vs_off_rp_edge"]),
            ),
            (
                "defense_vs_opponent_offense",
                float(r["def_vs_off_rp_edge"]),
                float(r["off_vs_def_rp_edge"]),
            ),
        ]

        for component_name, component_edge, opposite_edge in component_specs:
            if abs(component_edge) < MIN_EDGE:
                continue

            if component_edge > 0:
                edge_team = r["team"]
                edge_opponent = r["opponent"]
                matchup = r["conference_matchup_type"]
                edge_result = r["ats_result"]
                edge_margin = r["ats_margin"]
                edge_clv = r["team_clv"]
                positive_edge = component_edge
                other_edge = opposite_edge
            else:
                edge_team = r["opponent"]
                edge_opponent = r["team"]
                matchup = flip_matchup_type(r["conference_matchup_type"])
                edge_result = flip_result(r["ats_result"])
                edge_margin = -float(r["ats_margin"]) if pd.notna(r["ats_margin"]) else pd.NA
                edge_clv = -float(r["team_clv"]) if pd.notna(r["team_clv"]) else pd.NA
                positive_edge = -component_edge
                other_edge = -opposite_edge

            rows.append(
                {
                    "season": r["season"],
                    "week": r["week"],
                    "game_id": r["game_id"],
                    "component": component_name,
                    "edge_team": edge_team,
                    "edge_opponent": edge_opponent,
                    "conference_matchup_type": matchup,
                    "component_edge": positive_edge,
                    "component_edge_band": edge_band(positive_edge),
                    "other_component_edge": other_edge,
                    "edge_team_ats_result": edge_result,
                    "edge_team_ats_margin": edge_margin,
                    "edge_team_clv": edge_clv,
                }
            )

    return pd.DataFrame(rows)


def build_combined_rows(raw):
    complete = raw[
        raw["team_overall"].notna()
        &
        raw["opp_overall"].notna()
    ].copy()

    base = (
        complete.sort_values(["season", "game_id", "team"])
        .drop_duplicates(subset=["season", "game_id"], keep="first")
        .copy()
    )

    rows = []

    for _, r in base.iterrows():
        off_edge = float(r["off_vs_def_rp_edge"])
        def_edge = float(r["def_vs_off_rp_edge"])
        total_edge = off_edge + def_edge

        if total_edge >= 0:
            team = r["team"]
            opponent = r["opponent"]
            matchup = r["conference_matchup_type"]
            result = r["ats_result"]
            margin = r["ats_margin"]
            clv = r["team_clv"]
            oriented_off = off_edge
            oriented_def = def_edge
        else:
            team = r["opponent"]
            opponent = r["team"]
            matchup = flip_matchup_type(r["conference_matchup_type"])
            result = flip_result(r["ats_result"])
            margin = -float(r["ats_margin"]) if pd.notna(r["ats_margin"]) else pd.NA
            clv = -float(r["team_clv"]) if pd.notna(r["team_clv"]) else pd.NA
            oriented_off = -def_edge
            oriented_def = -off_edge

        flags = {
            "both_positive": oriented_off > 0 and oriented_def > 0,
            "both_5_plus": oriented_off >= 5 and oriented_def >= 5,
            "offense_15_plus": oriented_off >= 15,
            "defense_15_plus": oriented_def >= 15,
            "either_component_25_plus": oriented_off >= 25 or oriented_def >= 25,
            "both_15_plus": oriented_off >= 15 and oriented_def >= 15,
            "offense_15_plus_def_nonnegative": oriented_off >= 15 and oriented_def >= 0,
            "defense_15_plus_off_nonnegative": oriented_def >= 15 and oriented_off >= 0,
        }

        for rule_name, qualifies in flags.items():
            if not qualifies:
                continue

            rows.append(
                {
                    "season": r["season"],
                    "week": r["week"],
                    "game_id": r["game_id"],
                    "continuity_team": team,
                    "continuity_opponent": opponent,
                    "conference_matchup_type": matchup,
                    "combined_rule": rule_name,
                    "offense_vs_defense_edge": oriented_off,
                    "defense_vs_offense_edge": oriented_def,
                    "continuity_team_ats_result": result,
                    "continuity_team_ats_margin": margin,
                    "continuity_team_clv": clv,
                }
            )

    return pd.DataFrame(rows)


def main():
    print("Loading expanded 2021-2025 RP history")

    raw = pd.read_csv(INPUT)

    print("Raw team-side rows:", len(raw))

    game_level = build_one_row_per_game(raw)
    component_rows = build_component_rows(raw)
    combined_rows = build_combined_rows(raw)

    print("Unique complete games:", len(game_level))
    print("Component observations:", len(component_rows))
    print("Combined-rule observations:", len(combined_rows))

    matchup_summary = summarize(
        game_level[
            (game_level["overall_rp_edge"] >= MIN_EDGE)
            &
            (game_level["conference_matchup_type"].notna())
        ],
        ["conference_matchup_type", "overall_rp_band"],
        "rp_team_ats_result",
        "rp_team_ats_margin",
        "rp_team_clv",
        extra_aggs={
            "avg_overall_rp_edge": ("overall_rp_edge", "mean"),
        },
    )

    component_summary = summarize(
        component_rows[
            component_rows["conference_matchup_type"].notna()
        ],
        ["component", "conference_matchup_type", "component_edge_band"],
        "edge_team_ats_result",
        "edge_team_ats_margin",
        "edge_team_clv",
        extra_aggs={
            "avg_component_edge": ("component_edge", "mean"),
            "avg_other_component_edge": ("other_component_edge", "mean"),
        },
    )

    combined_summary = summarize(
        combined_rows[
            combined_rows["conference_matchup_type"].notna()
        ],
        ["combined_rule", "conference_matchup_type"],
        "continuity_team_ats_result",
        "continuity_team_ats_margin",
        "continuity_team_clv",
        extra_aggs={
            "avg_offense_edge": ("offense_vs_defense_edge", "mean"),
            "avg_defense_edge": ("defense_vs_offense_edge", "mean"),
        },
    )

    for frame in [matchup_summary, component_summary, combined_summary]:
        frame.sort_values(
            ["games", "ats_win_pct"],
            ascending=[False, False],
            inplace=True,
            na_position="last",
        )

    focus_frames = []

    m = matchup_summary[
        (matchup_summary["games"] >= MIN_SAMPLE)
        &
        (matchup_summary["conference_matchup_type"].isin(
            ["G6_vs_P4", "P4_vs_G6", "P4_vs_P4"]
        ))
    ].copy()
    m["analysis_type"] = "overall_rp"
    focus_frames.append(m)

    c = component_summary[
        (component_summary["games"] >= MIN_SAMPLE)
        &
        (component_summary["conference_matchup_type"].isin(
            ["G6_vs_P4", "P4_vs_G6", "P4_vs_P4"]
        ))
    ].copy()
    c["analysis_type"] = "component_rp"
    focus_frames.append(c)

    b = combined_summary[
        (combined_summary["games"] >= MIN_SAMPLE)
        &
        (combined_summary["conference_matchup_type"].isin(
            ["G6_vs_P4", "P4_vs_G6", "P4_vs_P4"]
        ))
    ].copy()
    b["analysis_type"] = "combined_rp"
    focus_frames.append(b)

    focus = pd.concat(focus_frames, ignore_index=True, sort=False)
    focus["absolute_ats_edge"] = focus["ats_edge_pct"].abs()

    confidence_order = {
        "High": 0,
        "Supported": 1,
        "Promising": 2,
        "Exploratory": 3,
        "Insufficient": 4,
    }

    focus["confidence_order"] = focus["confidence"].map(confidence_order)
    focus.sort_values(
        ["confidence_order", "absolute_ats_edge", "games"],
        ascending=[True, False, False],
        inplace=True,
        na_position="last",
    )
    focus.drop(columns=["confidence_order", "absolute_ats_edge"], inplace=True)

    OUT_GAME.parent.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)

    game_level.to_csv(OUT_GAME, index=False)
    matchup_summary.to_csv(OUT_OVERALL, index=False)
    component_summary.to_csv(OUT_COMPONENT, index=False)
    combined_summary.to_csv(OUT_COMBINED, index=False)
    focus.to_csv(OUT_FOCUS, index=False)

    audit = pd.DataFrame(
        [
            {"metric": "raw_team_side_rows", "value": len(raw)},
            {"metric": "unique_complete_games", "value": len(game_level)},
            {"metric": "seasons", "value": game_level["season"].nunique()},
            {"metric": "weeks", "value": ",".join(map(str, sorted(game_level["week"].dropna().unique())))},
            {"metric": "matchup_summary_rows", "value": len(matchup_summary)},
            {"metric": "component_summary_rows", "value": len(component_summary)},
            {"metric": "combined_summary_rows", "value": len(combined_summary)},
            {"metric": "focus_rows", "value": len(focus)},
            {"metric": "minimum_edge", "value": MIN_EDGE},
            {"metric": "minimum_sample", "value": MIN_SAMPLE},
        ]
    )

    audit.to_csv(OUT_AUDIT, index=False)

    print()
    print("Created:")
    print(OUT_GAME)
    print(OUT_OVERALL)
    print(OUT_COMPONENT)
    print(OUT_COMBINED)
    print(OUT_FOCUS)
    print(OUT_AUDIT)

    print()
    print("Expanded focus rules:")
    print(focus.head(100).to_string(index=False))


if __name__ == "__main__":
    main()
