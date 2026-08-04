#!/usr/bin/env python3
"""Backtest validated returning-production signals against first-half spreads.

Historical RP source:
    data/research/expanded_rp_game_level_2021_2025.csv

First-half market/results source:
    SGO/sgo_ncaaf_2024_2025_halves_odds.csv

Study window:
    2024-2025, Weeks 1-4

Validated full-game RP rules:
1. P4 vs G6, either component edge >= 25
2. P4 vs G6, defensive RP edge >= 15
3. P4 vs P4, overall RP edge from 15 to 24.9

The script:
- matches RP games to SGO 1H data by season and normalized teams
- orients spread/results to the RP signal team
- calculates 1H ATS result and ATS margin directly from scores and line
- reports coverage, ATS records, role splits, spread buckets, and season splits
- preserves overlapping rules but also produces a primary-rule-only summary
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unicodedata

import numpy as np
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

RP_FILE = BASE / "data/research/expanded_rp_game_level_2021_2025.csv"
HALVES_FILE = BASE / "SGO/sgo_ncaaf_2024_2025_halves_odds.csv"

OUT_DETAIL = BASE / "data/research/rp_1h_signal_games_2024_2025.csv"
OUT_RULE = BASE / "data/research/rp_1h_rule_summary_2024_2025.csv"
OUT_PRIMARY = BASE / "data/research/rp_1h_primary_rule_summary_2024_2025.csv"
OUT_SEASON = BASE / "data/research/rp_1h_rule_by_season_2024_2025.csv"
OUT_ROLE = BASE / "data/research/rp_1h_rule_by_market_role_2024_2025.csv"
OUT_BUCKET = BASE / "data/research/rp_1h_rule_by_spread_bucket_2024_2025.csv"
OUT_AGREEMENT = BASE / "data/research/rp_full_game_vs_1h_agreement_2024_2025.csv"
OUT_UNMATCHED = BASE / "data/audits/rp_1h_unmatched_games_2024_2025.csv"
OUT_AUDIT = BASE / "data/audits/rp_1h_backtest_audit_2024_2025.csv"


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
    "san josé state": "san jose state",
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


RULES = {
    "P4_G6_EITHER_COMPONENT_25_PLUS": {
        "label": "P4 vs G6: either RP component edge 25+",
        "priority": 1,
    },
    "P4_G6_DEFENSE_15_PLUS": {
        "label": "P4 vs G6: defensive RP edge 15+",
        "priority": 2,
    },
    "P4_P4_OVERALL_15_TO_24_9": {
        "label": "P4 vs P4: overall RP edge 15-24.9",
        "priority": 3,
    },
}


def normalize_team(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return ALIASES.get(text, text)


def week_from_date(series: pd.Series) -> pd.Series:
    # RP file already contains week. This is only an audit fallback for SGO rows.
    dates = pd.to_datetime(series, errors="coerce", utc=True)
    return dates


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


def rule_mask(df: pd.DataFrame, rule_key: str) -> pd.Series:
    if rule_key == "P4_G6_EITHER_COMPONENT_25_PLUS":
        return (
            df["conference_matchup_type"].eq("P4_vs_G6")
            &
            (
                (df["offense_vs_defense_edge"] >= 25)
                |
                (df["defense_vs_offense_edge"] >= 25)
            )
        )

    if rule_key == "P4_G6_DEFENSE_15_PLUS":
        return (
            df["conference_matchup_type"].eq("P4_vs_G6")
            &
            (df["defense_vs_offense_edge"] >= 15)
        )

    if rule_key == "P4_P4_OVERALL_15_TO_24_9":
        return (
            df["conference_matchup_type"].eq("P4_vs_P4")
            &
            (df["overall_rp_edge"] >= 15)
            &
            (df["overall_rp_edge"] < 25)
        )

    raise KeyError(rule_key)


def summarize(df: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    out = (
        df.groupby(groups, dropna=False)
        .agg(
            games=("rp_team_1h_ats_result", "count"),
            wins=("rp_team_1h_ats_result", lambda s: (s == "W").sum()),
            losses=("rp_team_1h_ats_result", lambda s: (s == "L").sum()),
            pushes=("rp_team_1h_ats_result", lambda s: (s == "P").sum()),
            avg_1h_ats_margin=("rp_team_1h_ats_margin", "mean"),
            median_1h_ats_margin=("rp_team_1h_ats_margin", "median"),
            avg_1h_spread=("rp_team_1h_spread", "mean"),
            seasons_present=("season", "nunique"),
            full_game_wins=("rp_team_ats_result", lambda s: (s == "W").sum()),
            full_game_losses=("rp_team_ats_result", lambda s: (s == "L").sum()),
            full_game_pushes=("rp_team_ats_result", lambda s: (s == "P").sum()),
        )
        .reset_index()
    )

    decisions = out["wins"] + out["losses"]
    out["one_h_ats_win_pct"] = out["wins"] / decisions.where(decisions > 0)

    fg_decisions = out["full_game_wins"] + out["full_game_losses"]
    out["full_game_ats_win_pct_in_1h_sample"] = (
        out["full_game_wins"] / fg_decisions.where(fg_decisions > 0)
    )

    out["one_h_ats_edge_pct"] = out["one_h_ats_win_pct"] * 100 - 50

    def confidence(n: int) -> str:
        if n >= 50:
            return "Supported"
        if n >= 30:
            return "Promising"
        if n >= 15:
            return "Exploratory"
        return "Small sample"

    out["confidence"] = out["games"].apply(confidence)
    return out


def build_rp_rule_rows() -> pd.DataFrame:
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
        &
        rp["week"].between(1, 4, inclusive="both")
    ].copy()

    rows = []

    for rule_key, meta in RULES.items():
        selected = rp[rule_mask(rp, rule_key)].copy()
        selected["rule_key"] = rule_key
        selected["rule_label"] = meta["label"]
        selected["rule_priority"] = meta["priority"]
        rows.append(selected)

    detail = pd.concat(rows, ignore_index=True)
    detail["rp_team_norm"] = detail["rp_team"].map(normalize_team)
    detail["rp_opponent_norm"] = detail["rp_opponent"].map(normalize_team)

    # Match key is order-independent.
    detail["team_pair_key"] = detail.apply(
        lambda r: "||".join(
            sorted([r["rp_team_norm"], r["rp_opponent_norm"]])
        ),
        axis=1,
    )

    return detail


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
        "home_1h_ats_result",
    }

    missing = sorted(required - set(halves.columns))
    if missing:
        raise KeyError(f"Halves file missing columns: {missing}")

    halves["season"] = pd.to_numeric(
        halves["season_year"],
        errors="coerce",
    )
    halves = halves[halves["season"].isin([2024, 2025])].copy()

    halves["away_norm"] = halves["away_team"].map(normalize_team)
    halves["home_norm"] = halves["home_team"].map(normalize_team)
    halves["team_pair_key"] = halves.apply(
        lambda r: "||".join(sorted([r["away_norm"], r["home_norm"]])),
        axis=1,
    )

    for col in [
        "away_1h_points",
        "home_1h_points",
        "home_1h_spread",
        "away_1h_spread",
    ]:
        halves[col] = pd.to_numeric(halves[col], errors="coerce")

    # Retain completed rows with usable 1H scores and a usable spread.
    halves = halves[
        halves["away_1h_points"].notna()
        &
        halves["home_1h_points"].notna()
        &
        (
            halves["home_1h_spread"].notna()
            |
            halves["away_1h_spread"].notna()
        )
    ].copy()

    # Keep one row per season/team pair. If duplicates exist, prefer rows with
    # explicit home 1H ATS result and odds availability.
    halves["_ats_present"] = halves["home_1h_ats_result"].notna().astype(int)
    halves["_odds_present"] = (
        halves.get("odds_available", False)
        .astype(str)
        .str.lower()
        .isin(["true", "1", "yes"])
        .astype(int)
    )

    halves.sort_values(
        ["season", "team_pair_key", "_ats_present", "_odds_present", "starts_at"],
        ascending=[True, True, False, False, True],
        inplace=True,
    )

    duplicates = halves.duplicated(
        subset=["season", "team_pair_key"],
        keep=False,
    )

    # Most team pairs occur once in Weeks 1-4. Repeated same-season matchups are
    # possible, so preserve all duplicates for a later score/date disambiguation.
    halves["same_pair_count"] = (
        halves.groupby(["season", "team_pair_key"])["event_id"]
        .transform("count")
    )

    return halves


def match_games(rp_rows: pd.DataFrame, halves: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = rp_rows.merge(
        halves,
        on=["season", "team_pair_key"],
        how="left",
        suffixes=("_rp", "_sgo"),
        indicator=True,
    )

    # In rare repeated-pair cases, choose the SGO event whose date is most
    # consistent with the RP week ordering. This dataset is mainly early season,
    # so the first occurrence is the intended one.
    merged["starts_at_dt"] = pd.to_datetime(
        merged["starts_at"],
        errors="coerce",
        utc=True,
    )
    merged.sort_values(
        ["season", "game_id", "rule_priority", "starts_at_dt"],
        inplace=True,
    )
    merged = merged.drop_duplicates(
        subset=["season", "game_id", "rule_key"],
        keep="first",
    )

    unmatched = merged[merged["_merge"] != "both"].copy()
    matched = merged[merged["_merge"] == "both"].copy()

    def orient(row: pd.Series) -> pd.Series:
        rp_team = row["rp_team_norm"]

        if rp_team == row["home_norm"]:
            team_side = "home"
            spread = row["home_1h_spread"]
            if pd.isna(spread) and pd.notna(row["away_1h_spread"]):
                spread = -row["away_1h_spread"]
            team_points = row["home_1h_points"]
            opp_points = row["away_1h_points"]
        elif rp_team == row["away_norm"]:
            team_side = "away"
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
        cover_margin = actual_margin + spread

        return pd.Series(
            {
                "rp_team_1h_side": team_side,
                "rp_team_1h_spread": spread,
                "rp_team_1h_points": team_points,
                "rp_opponent_1h_points": opp_points,
                "rp_team_1h_margin": actual_margin,
                "rp_team_1h_ats_margin": cover_margin,
                "rp_team_1h_ats_result": ats_result(cover_margin),
            }
        )

    oriented = matched.apply(orient, axis=1)
    matched = pd.concat([matched.reset_index(drop=True), oriented.reset_index(drop=True)], axis=1)

    matched = matched[
        matched["rp_team_1h_side"].isin(["home", "away"])
        &
        matched["rp_team_1h_spread"].notna()
    ].copy()

    matched["one_h_market_role"] = matched["rp_team_1h_spread"].map(role)
    matched["one_h_spread_bucket"] = matched["rp_team_1h_spread"].map(spread_bucket)
    matched["full_game_and_1h_result"] = (
        matched["rp_team_ats_result"].astype(str)
        + "/"
        + matched["rp_team_1h_ats_result"].astype(str)
    )
    matched["same_direction"] = (
        matched["rp_team_ats_result"].astype(str)
        == matched["rp_team_1h_ats_result"].astype(str)
    )

    return matched, unmatched


def primary_only(detail: pd.DataFrame) -> pd.DataFrame:
    primary = detail.sort_values(
        ["season", "game_id", "rule_priority"],
    ).drop_duplicates(
        subset=["season", "game_id"],
        keep="first",
    )
    return primary.copy()


def print_summary(title: str, frame: pd.DataFrame, columns: list[str]) -> None:
    print()
    print(title)
    print("=" * 110)

    display = frame.copy()

    for col in ["one_h_ats_win_pct", "full_game_ats_win_pct_in_1h_sample"]:
        if col in display.columns:
            display[col] = (display[col] * 100).round(1)

    for col in ["avg_1h_ats_margin", "median_1h_ats_margin", "avg_1h_spread"]:
        if col in display.columns:
            display[col] = display[col].round(2)

    print(display[columns].to_string(index=False))


def main() -> None:
    print("Building 2024-2025 first-half RP signal backtest")

    rp_rows = build_rp_rule_rows()
    halves = prepare_halves()
    detail, unmatched = match_games(rp_rows, halves)
    primary = primary_only(detail)

    rule_summary = summarize(detail, ["rule_key", "rule_label"])
    primary_summary = summarize(primary, ["rule_key", "rule_label"])
    season_summary = summarize(detail, ["rule_key", "season"])
    role_summary = summarize(detail, ["rule_key", "one_h_market_role"])
    bucket_summary = summarize(detail, ["rule_key", "one_h_spread_bucket"])
    agreement_summary = (
        detail.groupby(["rule_key", "full_game_and_1h_result"], dropna=False)
        .agg(games=("game_id", "count"))
        .reset_index()
    )

    for path in [
        OUT_DETAIL,
        OUT_RULE,
        OUT_PRIMARY,
        OUT_SEASON,
        OUT_ROLE,
        OUT_BUCKET,
        OUT_AGREEMENT,
        OUT_UNMATCHED,
        OUT_AUDIT,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)

    detail.to_csv(OUT_DETAIL, index=False)
    rule_summary.to_csv(OUT_RULE, index=False)
    primary_summary.to_csv(OUT_PRIMARY, index=False)
    season_summary.to_csv(OUT_SEASON, index=False)
    role_summary.to_csv(OUT_ROLE, index=False)
    bucket_summary.to_csv(OUT_BUCKET, index=False)
    agreement_summary.to_csv(OUT_AGREEMENT, index=False)
    unmatched.to_csv(OUT_UNMATCHED, index=False)

    audit = pd.DataFrame(
        [
            {"metric": "rp_rule_rows_2024_2025", "value": len(rp_rows)},
            {"metric": "rp_unique_games_2024_2025", "value": rp_rows["game_id"].nunique()},
            {"metric": "sgo_usable_1h_rows_2024_2025", "value": len(halves)},
            {"metric": "matched_rule_rows", "value": len(detail)},
            {"metric": "matched_unique_games", "value": detail["game_id"].nunique()},
            {"metric": "primary_unique_games", "value": len(primary)},
            {"metric": "unmatched_rule_rows", "value": len(unmatched)},
            {"metric": "matched_2024_rule_rows", "value": int((detail["season"] == 2024).sum())},
            {"metric": "matched_2025_rule_rows", "value": int((detail["season"] == 2025).sum())},
            {
                "metric": "coverage_warning",
                "value": (
                    "Interpret 2025 separately because the local 2025 SGO halves "
                    "history may be incomplete."
                ),
            },
        ]
    )
    audit.to_csv(OUT_AUDIT, index=False)

    print_summary(
        "1H ATS RESULTS BY VALIDATED RP RULE",
        rule_summary,
        [
            "rule_key",
            "games",
            "wins",
            "losses",
            "pushes",
            "one_h_ats_win_pct",
            "avg_1h_ats_margin",
            "full_game_ats_win_pct_in_1h_sample",
            "confidence",
        ],
    )

    print_summary(
        "PRIMARY RULE ONLY — ONE OBSERVATION PER GAME",
        primary_summary,
        [
            "rule_key",
            "games",
            "wins",
            "losses",
            "pushes",
            "one_h_ats_win_pct",
            "avg_1h_ats_margin",
            "full_game_ats_win_pct_in_1h_sample",
            "confidence",
        ],
    )

    print_summary(
        "1H ATS RESULTS BY SEASON",
        season_summary,
        [
            "rule_key",
            "season",
            "games",
            "wins",
            "losses",
            "pushes",
            "one_h_ats_win_pct",
            "avg_1h_ats_margin",
            "confidence",
        ],
    )

    print_summary(
        "1H ATS RESULTS BY 1H MARKET ROLE",
        role_summary,
        [
            "rule_key",
            "one_h_market_role",
            "games",
            "wins",
            "losses",
            "pushes",
            "one_h_ats_win_pct",
            "avg_1h_ats_margin",
            "confidence",
        ],
    )

    print_summary(
        "1H ATS RESULTS BY 1H SPREAD BUCKET",
        bucket_summary[
            bucket_summary["games"] >= 5
        ].sort_values(
            ["rule_key", "games"],
            ascending=[True, False],
        ),
        [
            "rule_key",
            "one_h_spread_bucket",
            "games",
            "wins",
            "losses",
            "pushes",
            "one_h_ats_win_pct",
            "avg_1h_ats_margin",
            "confidence",
        ],
    )

    print()
    print("Created:")
    print(OUT_DETAIL)
    print(OUT_RULE)
    print(OUT_PRIMARY)
    print(OUT_SEASON)
    print(OUT_ROLE)
    print(OUT_BUCKET)
    print(OUT_AGREEMENT)
    print(OUT_UNMATCHED)
    print(OUT_AUDIT)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
