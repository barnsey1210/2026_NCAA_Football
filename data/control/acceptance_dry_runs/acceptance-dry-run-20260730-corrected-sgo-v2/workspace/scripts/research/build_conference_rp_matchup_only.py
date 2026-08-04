from pathlib import Path
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

INPUT = BASE / "data/research/conference_rp_broad_rule_games.csv"

OUT_MATCHUP = BASE / "data/research/conference_rp_matchup_overall_summary.csv"
OUT_RP_BANDS = BASE / "data/research/conference_rp_matchup_rp_band_summary.csv"
OUT_ROLE_CONTEXT = BASE / "data/research/conference_rp_matchup_role_context.csv"
OUT_FOCUS = BASE / "data/research/conference_rp_g6_p4_p4_focus.csv"
OUT_AUDIT = BASE / "data/audits/conference_rp_matchup_only_audit.csv"

MIN_SAMPLE = 15


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
    out = (
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


def main():
    print("Loading corrected RP-edge game detail")

    df = pd.read_csv(INPUT)

    print("Rows loaded:", len(df))

    required = [
        "season",
        "game_id",
        "conference_matchup_type",
        "rp_band",
        "rp_team_role",
        "rp_team_ats_result",
        "rp_team_ats_margin",
        "rp_team_clv",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    classified = df[df["conference_matchup_type"].notna()].copy()

    # Broadest possible view: matchup type only.
    matchup = summarize(
        classified,
        ["conference_matchup_type"],
    )

    # Main research view: matchup type plus RP advantage size.
    rp_bands = summarize(
        classified,
        ["conference_matchup_type", "rp_band"],
    )

    # Secondary context only: favorite/underdog role, without spread buckets.
    role_context = summarize(
        classified,
        ["conference_matchup_type", "rp_band", "rp_team_role"],
    )

    matchup = matchup.sort_values(
        ["games", "ats_win_pct"],
        ascending=[False, False],
        na_position="last",
    )

    rp_bands = rp_bands.sort_values(
        ["conference_matchup_type", "games", "ats_win_pct"],
        ascending=[True, False, False],
        na_position="last",
    )

    role_context = role_context.sort_values(
        ["conference_matchup_type", "rp_band", "games"],
        ascending=[True, True, False],
        na_position="last",
    )

    focus_types = ["G6_vs_P4", "P4_vs_G6", "P4_vs_P4"]

    focus_matchup = matchup[
        matchup["conference_matchup_type"].isin(focus_types)
    ].copy()
    focus_matchup["view"] = "Matchup overall"

    focus_bands = rp_bands[
        rp_bands["conference_matchup_type"].isin(focus_types)
    ].copy()
    focus_bands["view"] = "Matchup + RP band"

    focus = pd.concat(
        [focus_matchup, focus_bands],
        ignore_index=True,
        sort=False,
    )

    focus = focus[
        focus["games"] >= MIN_SAMPLE
    ].copy()

    focus["absolute_ats_edge"] = focus["ats_edge_pct"].abs()
    focus = focus.sort_values(
        ["confidence", "absolute_ats_edge", "games"],
        ascending=[True, False, False],
        na_position="last",
    ).drop(columns=["absolute_ats_edge"])

    OUT_MATCHUP.parent.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)

    matchup.to_csv(OUT_MATCHUP, index=False)
    rp_bands.to_csv(OUT_RP_BANDS, index=False)
    role_context.to_csv(OUT_ROLE_CONTEXT, index=False)
    focus.to_csv(OUT_FOCUS, index=False)

    audit = pd.DataFrame(
        [
            {"metric": "corrected_detail_rows", "value": len(df)},
            {"metric": "classified_rows", "value": len(classified)},
            {"metric": "unclassified_rows", "value": int(df["conference_matchup_type"].isna().sum())},
            {"metric": "matchup_summary_rows", "value": len(matchup)},
            {"metric": "rp_band_summary_rows", "value": len(rp_bands)},
            {"metric": "role_context_rows", "value": len(role_context)},
            {"metric": "focus_rows_minimum_sample", "value": len(focus)},
            {"metric": "minimum_sample", "value": MIN_SAMPLE},
        ]
    )

    audit.to_csv(OUT_AUDIT, index=False)

    print()
    print("Created:")
    print(OUT_MATCHUP)
    print(OUT_RP_BANDS)
    print(OUT_ROLE_CONTEXT)
    print(OUT_FOCUS)
    print(OUT_AUDIT)

    print()
    print("G6/P4 and P4/P4 focus:")
    if focus.empty:
        print(f"No focus rows met the minimum sample of {MIN_SAMPLE}.")
    else:
        print(focus.to_string(index=False))


if __name__ == "__main__":
    main()
