#!/usr/bin/env python3
"""Discover standalone first-half returning-production betting patterns.

Historical RP source:
    data/research/expanded_rp_game_level_2021_2025.csv

First-half odds/results source:
    SGO/sgo_ncaaf_2024_2025_halves_odds.csv

Study window:
    2024-2025, Weeks 1-4

Purpose
-------
This is a discovery study, not a production-rule installer.

It evaluates first-half ATS performance for many returning-production
configurations without requiring a game to satisfy the existing full-game RP
rules first.

Safeguards
----------
- Uses one oriented observation per game/side/rule.
- Requires positive average ATS margin for a positive candidate.
- Reports 2024 and 2025 separately.
- Tracks season stability.
- Flags small samples.
- Produces a ranked shortlist but does not automatically promote any rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import re
import sys
import unicodedata
from typing import Callable

import numpy as np
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

RP_FILE = BASE / "data/research/expanded_rp_game_level_2021_2025.csv"
HALVES_FILE = BASE / "SGO/sgo_ncaaf_2024_2025_halves_odds.csv"

OUT_DETAIL = BASE / "data/research/rp_1h_discovery_detail_2024_2025.csv"
OUT_ALL_RULES = BASE / "data/research/rp_1h_discovery_all_rules_2024_2025.csv"
OUT_SEASON = BASE / "data/research/rp_1h_discovery_by_season_2024_2025.csv"
OUT_SHORTLIST = BASE / "data/research/rp_1h_discovery_shortlist_2024_2025.csv"
OUT_STABILITY = BASE / "data/research/rp_1h_discovery_stability_2024_2025.csv"
OUT_UNMATCHED = BASE / "data/audits/rp_1h_discovery_unmatched_2024_2025.csv"
OUT_AUDIT = BASE / "data/audits/rp_1h_discovery_audit_2024_2025.csv"


ALIASES = {
    "app st": "appalachian state",
    "app state": "appalachian state",
    "appalachian st": "appalachian state",
    "arizona st": "arizona state",
    "arkansas st": "arkansas state",
    "ball st": "ball state",
    "boise st": "boise state",
    "boston coll": "boston college",
    "central florida": "ucf",
    "cmu": "central michigan",
    "colorado st": "colorado state",
    "e michigan": "eastern michigan",
    "emu": "eastern michigan",
    "fau": "florida atlantic",
    "fiu": "florida international",
    "florida int l": "florida international",
    "florida st": "florida state",
    "fresno st": "fresno state",
    "ga southern": "georgia southern",
    "ga tech": "georgia tech",
    "georgia st": "georgia state",
    "hawai i": "hawaii",
    "iowa st": "iowa state",
    "kansas st": "kansas state",
    "kent st": "kent state",
    "la tech": "louisiana tech",
    "massachusetts": "umass",
    "miami oh": "miami ohio",
    "michigan st": "michigan state",
    "mississippi st": "mississippi state",
    "miss st": "mississippi state",
    "mtsu": "middle tennessee",
    "n carolina": "north carolina",
    "nc st": "nc state",
    "new mexico st": "new mexico state",
    "n texas": "north texas",
    "niu": "northern illinois",
    "ohio st": "ohio state",
    "oklahoma st": "oklahoma state",
    "oregon st": "oregon state",
    "penn st": "penn state",
    "s carolina": "south carolina",
    "san diego st": "san diego state",
    "san jose st": "san jose state",
    "so miss": "southern miss",
    "texas a m": "texas a&m",
    "texas st": "texas state",
    "utah st": "utah state",
    "va tech": "virginia tech",
    "wash st": "washington state",
    "washington st": "washington state",
    "w kentucky": "western kentucky",
    "wku": "western kentucky",
    "w michigan": "western michigan",
    "w virginia": "west virginia",
}


def normalize_team(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return ALIASES.get(text, text)


def role(spread: object) -> str:
    try:
        value = float(spread)
    except (TypeError, ValueError):
        return "Unknown"
    if np.isnan(value):
        return "Unknown"
    if value < 0:
        return "Favorite"
    if value > 0:
        return "Underdog"
    return "Pick'em"


def spread_bucket(spread: object) -> str:
    try:
        value = float(spread)
    except (TypeError, ValueError):
        return "Unknown"
    if np.isnan(value):
        return "Unknown"
    if value <= -21:
        return "Fav 21+"
    if value <= -14:
        return "Fav 14-20.5"
    if value <= -7:
        return "Fav 7-13.5"
    if value < 0:
        return "Fav 0.5-6.5"
    if value == 0:
        return "Pick'em"
    if value < 7:
        return "Dog 0.5-6.5"
    if value < 14:
        return "Dog 7-13.5"
    if value < 21:
        return "Dog 14-20.5"
    return "Dog 21+"


def ats_result(margin: float) -> str:
    if margin > 1e-9:
        return "W"
    if margin < -1e-9:
        return "L"
    return "P"


@dataclass(frozen=True)
class Rule:
    key: str
    label: str
    family: str
    mask: Callable[[pd.DataFrame], pd.Series]


def band_mask(series: pd.Series, low: float, high: float | None = None) -> pd.Series:
    if high is None:
        return series >= low
    return (series >= low) & (series < high)


def build_rules() -> list[Rule]:
    rules: list[Rule] = []

    matchup_types = {
        "ALL": None,
        "P4_vs_G6": "P4_vs_G6",
        "P4_vs_P4": "P4_vs_P4",
        "G6_vs_P4": "G6_vs_P4",
        "G6_vs_G6": "G6_vs_G6",
    }

    overall_bands = [
        (5, 10, "5_TO_9_9"),
        (10, 15, "10_TO_14_9"),
        (15, 25, "15_TO_24_9"),
        (25, None, "25_PLUS"),
    ]

    component_bands = [
        (10, 15, "10_TO_14_9"),
        (15, 25, "15_TO_24_9"),
        (25, None, "25_PLUS"),
    ]

    for matchup_key, matchup_value in matchup_types.items():
        def matchup_filter(df: pd.DataFrame, mv=matchup_value) -> pd.Series:
            if mv is None:
                return pd.Series(True, index=df.index)
            return df["conference_matchup_type"].eq(mv)

        for low, high, suffix in overall_bands:
            rules.append(
                Rule(
                    key=f"{matchup_key}__OVERALL__{suffix}",
                    label=f"{matchup_key}: overall RP edge {low}+"
                    if high is None
                    else f"{matchup_key}: overall RP edge {low}-{high - 0.1:.1f}",
                    family="overall_edge",
                    mask=lambda df, low=low, high=high, mf=matchup_filter:
                        mf(df) & band_mask(df["overall_rp_edge"], low, high),
                )
            )

        for metric, family, label_name in [
            ("offense_vs_defense_edge", "offense_vs_defense", "Off RP vs opp Def RP"),
            ("defense_vs_offense_edge", "defense_vs_offense", "Def RP vs opp Off RP"),
        ]:
            for low, high, suffix in component_bands:
                rules.append(
                    Rule(
                        key=f"{matchup_key}__{family.upper()}__{suffix}",
                        label=(
                            f"{matchup_key}: {label_name} edge {low}+"
                            if high is None
                            else f"{matchup_key}: {label_name} edge {low}-{high - 0.1:.1f}"
                        ),
                        family=family,
                        mask=lambda df, metric=metric, low=low, high=high, mf=matchup_filter:
                            mf(df) & band_mask(df[metric], low, high),
                    )
                )

        for threshold in [5, 10, 15, 25]:
            rules.append(
                Rule(
                    key=f"{matchup_key}__BOTH_COMPONENTS__{threshold}_PLUS",
                    label=f"{matchup_key}: both RP components {threshold}+",
                    family="both_components",
                    mask=lambda df, threshold=threshold, mf=matchup_filter:
                        mf(df)
                        & (df["offense_vs_defense_edge"] >= threshold)
                        & (df["defense_vs_offense_edge"] >= threshold),
                )
            )

        for threshold in [15, 25]:
            rules.append(
                Rule(
                    key=f"{matchup_key}__EITHER_COMPONENT__{threshold}_PLUS",
                    label=f"{matchup_key}: either RP component {threshold}+",
                    family="either_component",
                    mask=lambda df, threshold=threshold, mf=matchup_filter:
                        mf(df)
                        & (
                            (df["offense_vs_defense_edge"] >= threshold)
                            | (df["defense_vs_offense_edge"] >= threshold)
                        ),
                )
            )

        rules.append(
            Rule(
                key=f"{matchup_key}__OFF_POS_DEF_NEG",
                label=f"{matchup_key}: offense edge positive, defense edge negative",
                family="mixed_components",
                mask=lambda df, mf=matchup_filter:
                    mf(df)
                    & (df["offense_vs_defense_edge"] > 0)
                    & (df["defense_vs_offense_edge"] < 0),
            )
        )

        rules.append(
            Rule(
                key=f"{matchup_key}__DEF_POS_OFF_NEG",
                label=f"{matchup_key}: defense edge positive, offense edge negative",
                family="mixed_components",
                mask=lambda df, mf=matchup_filter:
                    mf(df)
                    & (df["defense_vs_offense_edge"] > 0)
                    & (df["offense_vs_defense_edge"] < 0),
            )
        )

    return rules


def prepare_rp() -> pd.DataFrame:
    rp = pd.read_csv(RP_FILE)

    required = {
        "season",
        "week",
        "game_id",
        "rp_team",
        "rp_opponent",
        "conference_matchup_type",
        "overall_rp_edge",
        "offense_vs_defense_edge",
        "defense_vs_offense_edge",
        "rp_team_ats_result",
        "rp_team_ats_margin",
    }

    missing = sorted(required - set(rp.columns))
    if missing:
        raise KeyError(f"RP file missing columns: {missing}")

    rp["season"] = pd.to_numeric(rp["season"], errors="coerce")
    rp["week"] = pd.to_numeric(rp["week"], errors="coerce")

    rp = rp[
        rp["season"].isin([2024, 2025])
        & rp["week"].between(1, 4, inclusive="both")
    ].copy()

    rp["rp_team_norm"] = rp["rp_team"].map(normalize_team)
    rp["rp_opponent_norm"] = rp["rp_opponent"].map(normalize_team)
    rp["team_pair_key"] = rp.apply(
        lambda row: "||".join(
            sorted([row["rp_team_norm"], row["rp_opponent_norm"]])
        ),
        axis=1,
    )

    return rp


def prepare_halves() -> pd.DataFrame:
    halves = pd.read_csv(HALVES_FILE, low_memory=False)

    required = {
        "season_year",
        "event_id",
        "starts_at",
        "away_team",
        "home_team",
        "away_1h_points",
        "home_1h_points",
        "home_1h_spread",
        "away_1h_spread",
    }

    missing = sorted(required - set(halves.columns))
    if missing:
        raise KeyError(f"Halves file missing columns: {missing}")

    halves["season"] = pd.to_numeric(halves["season_year"], errors="coerce")
    halves = halves[halves["season"].isin([2024, 2025])].copy()

    halves["away_norm"] = halves["away_team"].map(normalize_team)
    halves["home_norm"] = halves["home_team"].map(normalize_team)
    halves["team_pair_key"] = halves.apply(
        lambda row: "||".join(
            sorted([row["away_norm"], row["home_norm"]])
        ),
        axis=1,
    )

    for col in [
        "away_1h_points",
        "home_1h_points",
        "home_1h_spread",
        "away_1h_spread",
    ]:
        halves[col] = pd.to_numeric(halves[col], errors="coerce")

    halves = halves[
        halves["away_1h_points"].notna()
        & halves["home_1h_points"].notna()
        & (
            halves["home_1h_spread"].notna()
            | halves["away_1h_spread"].notna()
        )
    ].copy()

    halves["starts_at_dt"] = pd.to_datetime(
        halves["starts_at"],
        errors="coerce",
        utc=True,
    )

    halves.sort_values(
        ["season", "team_pair_key", "starts_at_dt"],
        inplace=True,
    )

    return halves


def merge_and_orient(rp: pd.DataFrame, halves: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = rp.merge(
        halves,
        on=["season", "team_pair_key"],
        how="left",
        suffixes=("_rp", "_sgo"),
        indicator=True,
    )

    merged.sort_values(
        ["season", "game_id", "starts_at_dt"],
        inplace=True,
    )

    merged = merged.drop_duplicates(
        subset=["season", "game_id"],
        keep="first",
    )

    unmatched = merged[merged["_merge"] != "both"].copy()
    matched = merged[merged["_merge"] == "both"].copy()

    def orient(row: pd.Series) -> pd.Series:
        rp_team = row["rp_team_norm"]

        if rp_team == row["home_norm"]:
            side = "home"
            spread = row["home_1h_spread"]
            if pd.isna(spread) and pd.notna(row["away_1h_spread"]):
                spread = -row["away_1h_spread"]
            team_points = row["home_1h_points"]
            opp_points = row["away_1h_points"]
        elif rp_team == row["away_norm"]:
            side = "away"
            spread = row["away_1h_spread"]
            if pd.isna(spread) and pd.notna(row["home_1h_spread"]):
                spread = -row["home_1h_spread"]
            team_points = row["away_1h_points"]
            opp_points = row["home_1h_points"]
        else:
            return pd.Series(
                {
                    "rp_team_1h_side": "unresolved",
                    "rp_team_1h_spread": np.nan,
                    "rp_team_1h_points": np.nan,
                    "rp_opponent_1h_points": np.nan,
                    "rp_team_1h_margin": np.nan,
                    "rp_team_1h_ats_margin": np.nan,
                    "rp_team_1h_ats_result": "",
                }
            )

        actual_margin = team_points - opp_points
        ats_margin_value = actual_margin + spread

        return pd.Series(
            {
                "rp_team_1h_side": side,
                "rp_team_1h_spread": spread,
                "rp_team_1h_points": team_points,
                "rp_opponent_1h_points": opp_points,
                "rp_team_1h_margin": actual_margin,
                "rp_team_1h_ats_margin": ats_margin_value,
                "rp_team_1h_ats_result": ats_result(ats_margin_value),
            }
        )

    oriented = matched.apply(orient, axis=1)
    matched = pd.concat(
        [matched.reset_index(drop=True), oriented.reset_index(drop=True)],
        axis=1,
    )

    matched = matched[
        matched["rp_team_1h_side"].isin(["home", "away"])
        & matched["rp_team_1h_spread"].notna()
    ].copy()

    matched["one_h_market_role"] = matched["rp_team_1h_spread"].map(role)
    matched["one_h_spread_bucket"] = matched["rp_team_1h_spread"].map(spread_bucket)
    matched["week_segment"] = np.where(
        matched["week"].isin([1, 2]),
        "Weeks 1-2",
        "Weeks 3-4",
    )
    matched["venue_role"] = matched["rp_team_1h_side"].map(
        {"home": "Home", "away": "Away"}
    )

    return matched, unmatched


def summarize_rule_rows(detail: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    out = (
        detail.groupby(groups, dropna=False)
        .agg(
            games=("rp_team_1h_ats_result", "count"),
            wins=("rp_team_1h_ats_result", lambda s: (s == "W").sum()),
            losses=("rp_team_1h_ats_result", lambda s: (s == "L").sum()),
            pushes=("rp_team_1h_ats_result", lambda s: (s == "P").sum()),
            avg_1h_ats_margin=("rp_team_1h_ats_margin", "mean"),
            median_1h_ats_margin=("rp_team_1h_ats_margin", "median"),
            avg_1h_spread=("rp_team_1h_spread", "mean"),
            seasons_present=("season", "nunique"),
        )
        .reset_index()
    )

    decisions = out["wins"] + out["losses"]
    out["one_h_ats_win_pct"] = out["wins"] / decisions.where(decisions > 0)
    out["one_h_ats_edge_pct"] = out["one_h_ats_win_pct"] * 100 - 50

    return out


def score_candidates(
    overall: pd.DataFrame,
    by_season: pd.DataFrame,
) -> pd.DataFrame:
    season_pivot = by_season.pivot_table(
        index=["rule_key", "rule_label", "family"],
        columns="season",
        values=[
            "games",
            "one_h_ats_win_pct",
            "avg_1h_ats_margin",
        ],
        aggfunc="first",
    )

    season_pivot.columns = [
        f"{metric}_{int(season)}"
        for metric, season in season_pivot.columns
    ]
    season_pivot = season_pivot.reset_index()

    out = overall.merge(
        season_pivot,
        on=["rule_key", "rule_label", "family"],
        how="left",
    )

    for col in [
        "games_2024",
        "games_2025",
        "one_h_ats_win_pct_2024",
        "one_h_ats_win_pct_2025",
        "avg_1h_ats_margin_2024",
        "avg_1h_ats_margin_2025",
    ]:
        if col not in out.columns:
            out[col] = np.nan

    out["positive_seasons"] = (
        (out["one_h_ats_win_pct_2024"] > 0.5).astype(int)
        + (out["one_h_ats_win_pct_2025"] > 0.5).astype(int)
    )
    out["positive_margin_seasons"] = (
        (out["avg_1h_ats_margin_2024"] > 0).astype(int)
        + (out["avg_1h_ats_margin_2025"] > 0).astype(int)
    )
    out["min_season_games"] = out[
        ["games_2024", "games_2025"]
    ].min(axis=1)
    out["season_pct_gap"] = (
        out["one_h_ats_win_pct_2024"]
        - out["one_h_ats_win_pct_2025"]
    ).abs()
    out["season_margin_gap"] = (
        out["avg_1h_ats_margin_2024"]
        - out["avg_1h_ats_margin_2025"]
    ).abs()

    # Discovery score rewards sample, win rate, margin, and season stability.
    sample_component = np.minimum(out["games"], 60) / 60 * 30
    ats_component = np.clip(
        (out["one_h_ats_win_pct"] - 0.5) / 0.15,
        -1,
        1,
    ) * 35
    margin_component = np.clip(
        out["avg_1h_ats_margin"] / 4.0,
        -1,
        1,
    ) * 20
    stability_component = (
        out["positive_seasons"] * 5
        + out["positive_margin_seasons"] * 5
        - np.minimum(out["season_pct_gap"].fillna(1), 0.30) / 0.30 * 10
    )

    out["discovery_score"] = (
        sample_component
        + ats_component
        + margin_component
        + stability_component
    ).round(2)

    def status(row: pd.Series) -> str:
        n = int(row["games"])
        pct = row["one_h_ats_win_pct"]
        margin = row["avg_1h_ats_margin"]
        positive_seasons = int(row["positive_seasons"])
        min_season_games = row["min_season_games"]

        if (
            n >= 30
            and pct >= 0.57
            and margin > 0.75
            and positive_seasons == 2
            and min_season_games >= 10
        ):
            return "Candidate for validation"

        if (
            n >= 20
            and pct >= 0.55
            and margin > 0
            and positive_seasons >= 1
        ):
            return "Promising exploratory"

        if (
            n >= 15
            and pct >= 0.55
            and margin > 0
        ):
            return "Exploratory"

        if n < 15 and pct >= 0.60 and margin > 0:
            return "Small-sample lead"

        return "No actionable signal"

    out["status"] = out.apply(status, axis=1)

    return out


def build_detail(base: pd.DataFrame, rules: list[Rule]) -> pd.DataFrame:
    rows = []

    for rule in rules:
        selected = base[rule.mask(base)].copy()
        if selected.empty:
            continue

        selected["rule_key"] = rule.key
        selected["rule_label"] = rule.label
        selected["family"] = rule.family
        rows.append(selected)

    if not rows:
        raise RuntimeError("No discovery-rule observations were generated")

    return pd.concat(rows, ignore_index=True)


def print_table(title: str, frame: pd.DataFrame, columns: list[str], limit: int | None = None) -> None:
    print()
    print(title)
    print("=" * 120)

    display = frame.copy()

    if limit is not None:
        display = display.head(limit)

    for col in [
        "one_h_ats_win_pct",
        "one_h_ats_win_pct_2024",
        "one_h_ats_win_pct_2025",
    ]:
        if col in display.columns:
            display[col] = (display[col] * 100).round(1)

    for col in [
        "avg_1h_ats_margin",
        "median_1h_ats_margin",
        "avg_1h_spread",
        "avg_1h_ats_margin_2024",
        "avg_1h_ats_margin_2025",
        "discovery_score",
    ]:
        if col in display.columns:
            display[col] = display[col].round(2)

    print(display[columns].to_string(index=False))


def main() -> None:
    print("Discovering standalone first-half returning-production patterns")

    rp = prepare_rp()
    halves = prepare_halves()
    base, unmatched = merge_and_orient(rp, halves)
    rules = build_rules()
    detail = build_detail(base, rules)

    overall = summarize_rule_rows(
        detail,
        ["rule_key", "rule_label", "family"],
    )
    by_season = summarize_rule_rows(
        detail,
        ["rule_key", "rule_label", "family", "season"],
    )

    scored = score_candidates(overall, by_season)

    shortlist = scored[
        scored["status"].isin(
            [
                "Candidate for validation",
                "Promising exploratory",
                "Exploratory",
                "Small-sample lead",
            ]
        )
    ].copy()

    shortlist.sort_values(
        [
            "status",
            "discovery_score",
            "games",
            "one_h_ats_win_pct",
        ],
        ascending=[True, False, False, False],
        inplace=True,
    )

    stability = scored.sort_values(
        ["discovery_score", "games"],
        ascending=[False, False],
    ).copy()

    for path in [
        OUT_DETAIL,
        OUT_ALL_RULES,
        OUT_SEASON,
        OUT_SHORTLIST,
        OUT_STABILITY,
        OUT_UNMATCHED,
        OUT_AUDIT,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)

    detail.to_csv(OUT_DETAIL, index=False)
    scored.to_csv(OUT_ALL_RULES, index=False)
    by_season.to_csv(OUT_SEASON, index=False)
    shortlist.to_csv(OUT_SHORTLIST, index=False)
    stability.to_csv(OUT_STABILITY, index=False)
    unmatched.to_csv(OUT_UNMATCHED, index=False)

    audit = pd.DataFrame(
        [
            {"metric": "base_unique_games_with_1h_data", "value": base["game_id"].nunique()},
            {"metric": "base_rows_2024", "value": int((base["season"] == 2024).sum())},
            {"metric": "base_rows_2025", "value": int((base["season"] == 2025).sum())},
            {"metric": "candidate_rules_tested", "value": len(rules)},
            {"metric": "rules_with_observations", "value": len(overall)},
            {"metric": "shortlisted_rules", "value": len(shortlist)},
            {"metric": "unmatched_rp_games", "value": len(unmatched)},
            {
                "metric": "coverage_warning",
                "value": "Interpret 2025 separately because local SGO 2025 halves coverage may be incomplete.",
            },
            {
                "metric": "multiple_testing_warning",
                "value": "This is a discovery scan. Shortlisted rules require separate validation before production use.",
            },
        ]
    )
    audit.to_csv(OUT_AUDIT, index=False)

    best_supported = scored[
        (scored["games"] >= 20)
        & (scored["avg_1h_ats_margin"] > 0)
    ].sort_values(
        ["discovery_score", "games"],
        ascending=[False, False],
    )

    print_table(
        "TOP STANDALONE 1H RP PATTERNS — MINIMUM 20 GAMES AND POSITIVE ATS MARGIN",
        best_supported,
        [
            "rule_label",
            "games",
            "wins",
            "losses",
            "pushes",
            "one_h_ats_win_pct",
            "avg_1h_ats_margin",
            "one_h_ats_win_pct_2024",
            "one_h_ats_win_pct_2025",
            "avg_1h_ats_margin_2024",
            "avg_1h_ats_margin_2025",
            "discovery_score",
            "status",
        ],
        limit=25,
    )

    print_table(
        "SHORTLISTED DISCOVERY RULES",
        shortlist.sort_values(
            ["discovery_score", "games"],
            ascending=[False, False],
        ),
        [
            "rule_label",
            "family",
            "games",
            "wins",
            "losses",
            "pushes",
            "one_h_ats_win_pct",
            "avg_1h_ats_margin",
            "positive_seasons",
            "min_season_games",
            "discovery_score",
            "status",
        ],
        limit=40,
    )

    role_detail = detail.merge(
        scored[
            [
                "rule_key",
                "status",
                "discovery_score",
            ]
        ],
        on="rule_key",
        how="left",
    )

    shortlisted_keys = set(shortlist["rule_key"])
    shortlisted_detail = role_detail[
        role_detail["rule_key"].isin(shortlisted_keys)
    ].copy()

    if not shortlisted_detail.empty:
        role_summary = summarize_rule_rows(
            shortlisted_detail,
            ["rule_key", "rule_label", "one_h_market_role"],
        ).sort_values(
            ["rule_key", "games"],
            ascending=[True, False],
        )

        bucket_summary = summarize_rule_rows(
            shortlisted_detail,
            ["rule_key", "rule_label", "one_h_spread_bucket"],
        )
        bucket_summary = bucket_summary[
            bucket_summary["games"] >= 5
        ].sort_values(
            ["rule_key", "games"],
            ascending=[True, False],
        )

        print_table(
            "SHORTLISTED RULES BY 1H MARKET ROLE",
            role_summary,
            [
                "rule_label",
                "one_h_market_role",
                "games",
                "wins",
                "losses",
                "pushes",
                "one_h_ats_win_pct",
                "avg_1h_ats_margin",
            ],
            limit=60,
        )

        print_table(
            "SHORTLISTED RULES BY 1H SPREAD BUCKET — MINIMUM 5 GAMES",
            bucket_summary,
            [
                "rule_label",
                "one_h_spread_bucket",
                "games",
                "wins",
                "losses",
                "pushes",
                "one_h_ats_win_pct",
                "avg_1h_ats_margin",
            ],
            limit=80,
        )

    print()
    print("Created:")
    print(OUT_DETAIL)
    print(OUT_ALL_RULES)
    print(OUT_SEASON)
    print(OUT_SHORTLIST)
    print(OUT_STABILITY)
    print(OUT_UNMATCHED)
    print(OUT_AUDIT)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
