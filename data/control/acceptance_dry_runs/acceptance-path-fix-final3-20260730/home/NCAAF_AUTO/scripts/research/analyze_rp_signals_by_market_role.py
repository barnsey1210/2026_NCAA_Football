#!/usr/bin/env python3
"""Analyze validated RP signals by favorite/underdog role and spread bucket.

Historical inputs:
- data/research/expanded_rp_game_level_2021_2025.csv

2026 inputs:
- data/signals/returning_production_validated_matches_2026.csv

Outputs:
- historical role/spread-bucket summary
- rule-by-role summary
- 2026 candidates annotated with likely market role and historical fit
"""

from __future__ import annotations

from pathlib import Path
import math
import sys

import numpy as np
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

HISTORICAL = BASE / "data/research/expanded_rp_game_level_2021_2025.csv"
CANDIDATES_2026 = BASE / "data/signals/returning_production_validated_matches_2026.csv"

OUT_DETAIL = BASE / "data/research/expanded_rp_role_spread_detail_2021_2025.csv"
OUT_SUMMARY = BASE / "data/research/expanded_rp_role_spread_summary_2021_2025.csv"
OUT_RULE_ROLE = BASE / "data/research/expanded_rp_rule_role_summary_2021_2025.csv"
OUT_2026 = BASE / "data/signals/returning_production_validated_matches_2026_with_market_role.csv"
OUT_AUDIT = BASE / "data/audits/returning_production_role_spread_audit.csv"


def spread_role(spread):
    if pd.isna(spread):
        return "Unknown"
    spread = float(spread)
    if spread < 0:
        return "Favorite"
    if spread > 0:
        return "Underdog"
    return "Pick'em"


def spread_bucket(spread):
    if pd.isna(spread):
        return "Unknown"

    spread = float(spread)

    if spread <= -21:
        return "Fav 21+"
    if spread <= -14:
        return "Fav 14-20.5"
    if spread <= -7:
        return "Fav 7-13.5"
    if spread < 0:
        return "Fav 0.5-6.5"
    if spread == 0:
        return "Pick'em"
    if spread < 7:
        return "Dog 0.5-6.5"
    if spread < 14:
        return "Dog 7-13.5"
    if spread < 21:
        return "Dog 14-20.5"
    return "Dog 21+"


def summarize(df, group_cols):
    out = (
        df.groupby(group_cols, dropna=False)
        .agg(
            games=("rp_team_ats_result", "count"),
            wins=("rp_team_ats_result", lambda s: (s == "W").sum()),
            losses=("rp_team_ats_result", lambda s: (s == "L").sum()),
            pushes=("rp_team_ats_result", lambda s: (s == "P").sum()),
            avg_ats_margin=("rp_team_ats_margin", "mean"),
            median_ats_margin=("rp_team_ats_margin", "median"),
            avg_spread=("rp_team_spread", "mean"),
            seasons_present=("season", "nunique"),
        )
        .reset_index()
    )

    decisions = out["wins"] + out["losses"]
    out["ats_win_pct"] = out["wins"] / decisions.where(decisions > 0)
    out["ats_edge_pct"] = out["ats_win_pct"] * 100 - 50

    def confidence(n):
        if n >= 50:
            return "Supported"
        if n >= 30:
            return "Promising"
        if n >= 15:
            return "Exploratory"
        return "Small sample"

    out["confidence"] = out["games"].apply(confidence)
    return out


def add_rule_flags(df):
    df = df.copy()

    df["rule_p4_g6_either_component_25_plus"] = (
        df["conference_matchup_type"].eq("P4_vs_G6")
        &
        (
            (df["offense_vs_defense_edge"] >= 25)
            |
            (df["defense_vs_offense_edge"] >= 25)
        )
    )

    df["rule_p4_g6_defense_15_plus"] = (
        df["conference_matchup_type"].eq("P4_vs_G6")
        &
        (df["defense_vs_offense_edge"] >= 15)
    )

    df["rule_p4_p4_overall_15_to_24_9"] = (
        df["conference_matchup_type"].eq("P4_vs_P4")
        &
        (df["overall_rp_edge"] >= 15)
        &
        (df["overall_rp_edge"] < 25)
    )

    return df


RULE_MAP = {
    "P4_G6_EITHER_COMPONENT_25_PLUS": "rule_p4_g6_either_component_25_plus",
    "P4_G6_DEFENSE_15_PLUS": "rule_p4_g6_defense_15_plus",
    "P4_P4_OVERALL_15_TO_24_9": "rule_p4_p4_overall_15_to_24_9",
}


def first_numeric(row, names):
    for name in names:
        if name in row.index:
            value = row.get(name)
            try:
                if value is not None and str(value).strip() != "":
                    return float(value)
            except (TypeError, ValueError):
                pass
    return np.nan


def signal_team_spread_from_home_spread(row):
    home_spread = first_numeric(
        row,
        [
            "market_spread_home",
            "consensus_spread_home",
            "sgo_spread_home",
            "spread_home",
        ],
    )

    if pd.isna(home_spread):
        return np.nan

    signal_team = str(row.get("signal_team", "")).strip()
    home_team = str(row.get("home_team", "")).strip()
    away_team = str(row.get("away_team", "")).strip()

    if signal_team == home_team:
        return home_spread

    if signal_team == away_team:
        return -home_spread

    return np.nan


def build_historical():
    hist = pd.read_csv(HISTORICAL)

    required = [
        "season",
        "game_id",
        "conference_matchup_type",
        "overall_rp_edge",
        "offense_vs_defense_edge",
        "defense_vs_offense_edge",
        "rp_team_spread",
        "rp_team_ats_result",
        "rp_team_ats_margin",
    ]

    missing = [c for c in required if c not in hist.columns]
    if missing:
        raise KeyError(f"Historical file missing columns: {missing}")

    hist = add_rule_flags(hist)

    hist["market_role"] = hist["rp_team_spread"].apply(spread_role)
    hist["spread_bucket"] = hist["rp_team_spread"].apply(spread_bucket)

    long_rows = []

    for rule_key, flag_col in RULE_MAP.items():
        selected = hist[hist[flag_col]].copy()
        selected["rule_key"] = rule_key
        long_rows.append(selected)

    detail = pd.concat(long_rows, ignore_index=True)

    role_summary = summarize(
        detail,
        ["rule_key", "market_role"],
    )

    bucket_summary = summarize(
        detail,
        ["rule_key", "spread_bucket"],
    )

    combined_summary = summarize(
        detail,
        ["rule_key", "market_role", "spread_bucket"],
    )

    summary = pd.concat(
        [
            role_summary.assign(summary_type="role"),
            bucket_summary.assign(summary_type="spread_bucket"),
            combined_summary.assign(summary_type="role_and_bucket"),
        ],
        ignore_index=True,
        sort=False,
    )

    rule_role = role_summary.sort_values(
        ["rule_key", "games"],
        ascending=[True, False],
    )

    return detail, summary, rule_role


def annotate_2026(summary):
    candidates = pd.read_csv(CANDIDATES_2026)

    candidates["signal_team_spread"] = candidates.apply(
        signal_team_spread_from_home_spread,
        axis=1,
    )
    candidates["market_role"] = candidates["signal_team_spread"].apply(spread_role)
    candidates["spread_bucket"] = candidates["signal_team_spread"].apply(spread_bucket)

    lookup = summary[
        summary["summary_type"].eq("role_and_bucket")
    ].copy()

    lookup = lookup[
        [
            "rule_key",
            "market_role",
            "spread_bucket",
            "games",
            "wins",
            "losses",
            "pushes",
            "ats_win_pct",
            "avg_ats_margin",
            "confidence",
        ]
    ].rename(
        columns={
            "games": "historical_role_bucket_games",
            "wins": "historical_role_bucket_wins",
            "losses": "historical_role_bucket_losses",
            "pushes": "historical_role_bucket_pushes",
            "ats_win_pct": "historical_role_bucket_ats_pct",
            "avg_ats_margin": "historical_role_bucket_avg_margin",
            "confidence": "historical_role_bucket_confidence",
        }
    )

    candidates = candidates.merge(
        lookup,
        on=["rule_key", "market_role", "spread_bucket"],
        how="left",
    )

    role_lookup = summary[
        summary["summary_type"].eq("role")
    ][
        [
            "rule_key",
            "market_role",
            "games",
            "wins",
            "losses",
            "pushes",
            "ats_win_pct",
            "avg_ats_margin",
            "confidence",
        ]
    ].rename(
        columns={
            "games": "historical_role_games",
            "wins": "historical_role_wins",
            "losses": "historical_role_losses",
            "pushes": "historical_role_pushes",
            "ats_win_pct": "historical_role_ats_pct",
            "avg_ats_margin": "historical_role_avg_margin",
            "confidence": "historical_role_confidence",
        }
    )

    candidates = candidates.merge(
        role_lookup,
        on=["rule_key", "market_role"],
        how="left",
    )

    def recommendation(row):
        if row["market_role"] == "Unknown":
            return "Watch for opening spread"

        bucket_n = row.get("historical_role_bucket_games")
        bucket_pct = row.get("historical_role_bucket_ats_pct")

        if pd.notna(bucket_n) and bucket_n >= 15 and pd.notna(bucket_pct):
            if bucket_pct >= 0.57:
                return "Historically favorable role/bucket"
            if bucket_pct <= 0.43:
                return "Historically unfavorable role/bucket"
            return "Historically neutral role/bucket"

        role_n = row.get("historical_role_games")
        role_pct = row.get("historical_role_ats_pct")

        if pd.notna(role_n) and role_n >= 15 and pd.notna(role_pct):
            if role_pct >= 0.57:
                return "Historically favorable role"
            if role_pct <= 0.43:
                return "Historically unfavorable role"
            return "Historically neutral role"

        return "Small historical sample"

    candidates["role_based_read"] = candidates.apply(recommendation, axis=1)

    candidates.sort_values(
        ["week", "date", "rule_priority", "signal_team"],
        inplace=True,
    )

    return candidates


def print_key_results(rule_role, summary, candidates):
    print()
    print("HISTORICAL FAVORITE / UNDERDOG RESULTS")
    print("=" * 100)

    display = rule_role.copy()
    display["ats_win_pct"] = (display["ats_win_pct"] * 100).round(1)
    display["avg_ats_margin"] = display["avg_ats_margin"].round(2)

    print(
        display[
            [
                "rule_key",
                "market_role",
                "games",
                "wins",
                "losses",
                "pushes",
                "ats_win_pct",
                "avg_ats_margin",
                "confidence",
            ]
        ].to_string(index=False)
    )

    print()
    print("BEST SPREAD BUCKETS WITH AT LEAST 15 GAMES")
    print("=" * 100)

    buckets = summary[
        summary["summary_type"].eq("spread_bucket")
        &
        (summary["games"] >= 15)
    ].copy()

    buckets["ats_win_pct"] = (buckets["ats_win_pct"] * 100).round(1)
    buckets["avg_ats_margin"] = buckets["avg_ats_margin"].round(2)

    buckets.sort_values(
        ["rule_key", "ats_win_pct", "games"],
        ascending=[True, False, False],
        inplace=True,
    )

    print(
        buckets[
            [
                "rule_key",
                "spread_bucket",
                "games",
                "wins",
                "losses",
                "pushes",
                "ats_win_pct",
                "avg_ats_margin",
                "confidence",
            ]
        ].to_string(index=False)
    )

    print()
    print("2026 CANDIDATES WITH CURRENT MARKET ROLE")
    print("=" * 100)

    display_cols = [
        "week",
        "date",
        "away_team",
        "home_team",
        "signal_team",
        "rule_label",
        "signal_team_spread",
        "market_role",
        "spread_bucket",
        "historical_role_games",
        "historical_role_ats_pct",
        "historical_role_bucket_games",
        "historical_role_bucket_ats_pct",
        "role_based_read",
    ]

    printable = candidates[display_cols].copy()

    for col in [
        "historical_role_ats_pct",
        "historical_role_bucket_ats_pct",
    ]:
        printable[col] = (printable[col] * 100).round(1)

    printable["signal_team_spread"] = printable["signal_team_spread"].round(1)

    print(printable.to_string(index=False))


def main():
    print("Analyzing RP signals by favorite/underdog role and spread bucket")

    detail, summary, rule_role = build_historical()
    candidates = annotate_2026(summary)

    for path in [OUT_DETAIL, OUT_SUMMARY, OUT_RULE_ROLE, OUT_2026, OUT_AUDIT]:
        path.parent.mkdir(parents=True, exist_ok=True)

    detail.to_csv(OUT_DETAIL, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
    rule_role.to_csv(OUT_RULE_ROLE, index=False)
    candidates.to_csv(OUT_2026, index=False)

    audit = pd.DataFrame(
        [
            {"metric": "historical_rule_rows", "value": len(detail)},
            {"metric": "historical_unique_games", "value": detail["game_id"].nunique()},
            {"metric": "historical_rows_with_spread", "value": detail["rp_team_spread"].notna().sum()},
            {"metric": "historical_rows_missing_spread", "value": detail["rp_team_spread"].isna().sum()},
            {"metric": "candidate_rows_2026", "value": len(candidates)},
            {"metric": "candidate_rows_with_market_spread", "value": candidates["signal_team_spread"].notna().sum()},
            {"metric": "candidate_rows_missing_market_spread", "value": candidates["signal_team_spread"].isna().sum()},
        ]
    )
    audit.to_csv(OUT_AUDIT, index=False)

    print_key_results(rule_role, summary, candidates)

    print()
    print("Created:")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)
    print(OUT_RULE_ROLE)
    print(OUT_2026)
    print(OUT_AUDIT)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
