#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(".")
RP_GAMES = ROOT / "data/research/returning_production_threshold_sensitivity_games.csv"

MARKET_CANDIDATES = [
    ROOT / "data/research/pbp_market_modeling_2021_2025/provider_market_rows.csv",
    ROOT / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv",
]

OUT_DIR = ROOT / "data/research/returning_production_clv"
AUDIT_OUT = ROOT / "data/audit/returning_production_clv_audit.json"


ALIASES = {
    "central florida": "ucf",
    "connecticut": "uconn",
    "miami fl": "miami",
    "miami florida": "miami",
    "miami oh": "miami ohio",
    "miami (oh)": "miami ohio",
    "southern california": "usc",
    "texas san antonio": "utsa",
    "texas-san antonio": "utsa",
    "louisiana monroe": "ulm",
    "louisiana-monroe": "ulm",
    "ul monroe": "ulm",
    "appalachian st": "appalachian state",
    "florida st": "florida state",
    "fresno st": "fresno state",
    "iowa st": "iowa state",
    "kansas st": "kansas state",
    "michigan st": "michigan state",
    "mississippi st": "mississippi state",
    "north carolina st": "nc state",
    "ohio st": "ohio state",
    "oklahoma st": "oklahoma state",
    "oregon st": "oregon state",
    "penn st": "penn state",
    "san diego st": "san diego state",
    "san jose st": "san jose state",
    "utah st": "utah state",
    "washington st": "washington state",
}


def norm(value):
    value = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()
    value = re.sub(r"\s+", " ", value)
    return ALIASES.get(value, value)


def numeric(series):
    return pd.to_numeric(series, errors="coerce")


def first_column(df, choices):
    lower = {str(column).lower(): column for column in df.columns}

    for choice in choices:
        if choice.lower() in lower:
            return lower[choice.lower()]

    return None


def clean_game_id(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text.endswith(".0"):
        text = text[:-2]

    return text


def choose_market_source():
    diagnostics = []

    for path in MARKET_CANDIDATES:
        if not path.exists():
            diagnostics.append({
                "path": str(path),
                "exists": False,
            })
            continue

        df = pd.read_csv(path)

        columns = {
            "game_id": first_column(df, ["game_id", "id"]),
            "season": first_column(df, ["season", "year"]),
            "week": first_column(df, ["week"]),
            "home_team": first_column(df, ["home_team", "home"]),
            "away_team": first_column(df, ["away_team", "away"]),
            "opening_home_spread": first_column(
                df,
                [
                    "opening_home_spread",
                    "open_home_spread",
                    "home_opening_spread",
                ],
            ),
            "closing_home_spread": first_column(
                df,
                [
                    "closing_home_spread",
                    "close_home_spread",
                    "home_closing_spread",
                ],
            ),
        }

        usable = all(
            columns[key]
            for key in [
                "game_id",
                "opening_home_spread",
                "closing_home_spread",
            ]
        )

        diagnostics.append({
            "path": str(path),
            "exists": True,
            "rows": len(df),
            "columns": columns,
            "usable": usable,
        })

        if usable:
            return path, df, columns, diagnostics

    raise SystemExit(
        "No usable historical market source with game_id, opening home spread "
        "and closing home spread."
    )


def result_record(series):
    counts = series.value_counts()

    return {
        "wins": int(counts.get("W", 0)),
        "losses": int(counts.get("L", 0)),
        "pushes": int(counts.get("P", 0)),
    }


def summarize(group):
    graded = group[group["ats_result"].isin(["W", "L", "P"])]
    decided = graded[graded["ats_result"].isin(["W", "L"])]

    record = result_record(graded["ats_result"])

    clv = numeric(group["team_clv"]).dropna()

    return pd.Series({
        "games": len(group),
        "ats_graded": len(graded),
        "ats_w": record["wins"],
        "ats_l": record["losses"],
        "ats_p": record["pushes"],
        "ats_pct": (
            record["wins"] / len(decided)
            if len(decided)
            else np.nan
        ),
        "avg_ats_margin": numeric(group["ats_margin"]).mean(),
        "clv_games": len(clv),
        "avg_clv": clv.mean(),
        "median_clv": clv.median(),
        "positive_clv_games": int((clv > 0).sum()),
        "positive_clv_pct": (
            float((clv > 0).mean())
            if len(clv)
            else np.nan
        ),
        "zero_clv_games": int((clv == 0).sum()),
        "negative_clv_games": int((clv < 0).sum()),
        "avg_opening_spread": numeric(group["team_opening_spread"]).mean(),
        "avg_closing_spread": numeric(group["team_closing_spread"]).mean(),
    })


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)

    rp = pd.read_csv(RP_GAMES)
    market_path, market, columns, source_diagnostics = choose_market_source()

    rp["game_id_key"] = rp["game_id"].map(clean_game_id)
    market["game_id_key"] = market[columns["game_id"]].map(clean_game_id)

    market_small = pd.DataFrame({
        "game_id_key": market["game_id_key"],
        "market_opening_home_spread": numeric(
            market[columns["opening_home_spread"]]
        ),
        "market_closing_home_spread": numeric(
            market[columns["closing_home_spread"]]
        ),
    })

    if columns.get("season"):
        market_small["market_season"] = numeric(
            market[columns["season"]]
        )

    if columns.get("week"):
        market_small["market_week"] = numeric(
            market[columns["week"]]
        )

    if columns.get("home_team"):
        market_small["market_home_team"] = market[
            columns["home_team"]
        ].astype(str)
        market_small["market_home_key"] = market_small[
            "market_home_team"
        ].map(norm)

    if columns.get("away_team"):
        market_small["market_away_team"] = market[
            columns["away_team"]
        ].astype(str)
        market_small["market_away_key"] = market_small[
            "market_away_team"
        ].map(norm)

    market_small = (
        market_small
        .drop_duplicates("game_id_key", keep="last")
    )

    joined = rp.merge(
        market_small,
        on="game_id_key",
        how="left",
        validate="many_to_one",
    )

    joined["team_key"] = joined["team"].map(norm)
    joined["opponent_key"] = joined["opponent"].map(norm)

    if "market_home_key" in joined:
        joined["team_is_home_market"] = (
            joined["team_key"] == joined["market_home_key"]
        )
        joined["team_is_away_market"] = (
            joined["team_key"] == joined["market_away_key"]
        )
        joined["market_team_identity_valid"] = (
            joined["team_is_home_market"]
            | joined["team_is_away_market"]
        )
    else:
        joined["team_is_home_market"] = joined["side"].eq("home")
        joined["team_is_away_market"] = joined["side"].eq("away")
        joined["market_team_identity_valid"] = True

    joined["team_opening_spread"] = np.where(
        joined["team_is_home_market"],
        joined["market_opening_home_spread"],
        -joined["market_opening_home_spread"],
    )

    joined["team_closing_spread"] = np.where(
        joined["team_is_home_market"],
        joined["market_closing_home_spread"],
        -joined["market_closing_home_spread"],
    )

    # Positive CLV means the selected team received a better number at open
    # than was available at close.
    #
    # Example:
    # Bet favorite -7, closes -9 => +2 CLV.
    # Bet underdog +7, closes +5 => +2 CLV.
    joined["team_clv"] = (
        joined["team_opening_spread"]
        - joined["team_closing_spread"]
    )

    joined.loc[
        ~joined["market_team_identity_valid"],
        [
            "team_opening_spread",
            "team_closing_spread",
            "team_clv",
        ],
    ] = np.nan

    joined["market_joined"] = (
        joined["market_opening_home_spread"].notna()
        & joined["market_closing_home_spread"].notna()
        & joined["market_team_identity_valid"]
    )

    joined.to_csv(
        OUT_DIR / "returning_production_games_with_clv.csv",
        index=False,
    )

    canonical = joined[
        joined["case"].isin([
            "overall_gap",
            "off_vs_def_gap",
            "def_vs_off_gap",
        ])
        & joined["threshold"].eq("gap_10+")
    ].copy()

    overall = (
        canonical.groupby(
            ["case", "threshold", "role"],
            dropna=False,
        )
        .apply(summarize, include_groups=False)
        .reset_index()
    )

    by_season = (
        canonical.groupby(
            ["case", "threshold", "role", "season"],
            dropna=False,
        )
        .apply(summarize, include_groups=False)
        .reset_index()
    )

    by_bucket = (
        canonical.groupby(
            ["case", "threshold", "role", "spread_bucket"],
            dropna=False,
        )
        .apply(summarize, include_groups=False)
        .reset_index()
    )

    by_season_bucket = (
        canonical.groupby(
            [
                "case",
                "threshold",
                "role",
                "spread_bucket",
                "season",
            ],
            dropna=False,
        )
        .apply(summarize, include_groups=False)
        .reset_index()
    )

    overall.to_csv(
        OUT_DIR / "returning_production_clv_summary.csv",
        index=False,
    )
    by_season.to_csv(
        OUT_DIR / "returning_production_clv_by_season.csv",
        index=False,
    )
    by_bucket.to_csv(
        OUT_DIR / "returning_production_clv_by_spread_bucket.csv",
        index=False,
    )
    by_season_bucket.to_csv(
        OUT_DIR
        / "returning_production_clv_by_season_spread_bucket.csv",
        index=False,
    )

    season_direction = []

    for keys, group in by_season.groupby(
        ["case", "role"],
        dropna=False,
    ):
        valid = group[
            group["avg_clv"].notna()
            & group["avg_ats_margin"].notna()
        ]

        season_direction.append({
            "case": keys[0],
            "role": keys[1],
            "seasons_available": int(valid["season"].nunique()),
            "positive_ats_margin_seasons": int(
                (valid["avg_ats_margin"] > 0).sum()
            ),
            "positive_clv_seasons": int(
                (valid["avg_clv"] > 0).sum()
            ),
            "ats_above_52_4_seasons": int(
                (valid["ats_pct"] > 0.524).sum()
            ),
        })

    pd.DataFrame(season_direction).to_csv(
        OUT_DIR / "returning_production_season_stability.csv",
        index=False,
    )

    missing = joined[~joined["market_joined"]].copy()
    missing.to_csv(
        OUT_DIR / "returning_production_clv_missing_games.csv",
        index=False,
    )

    audit = {
        "status": "PASS",
        "rp_source": str(RP_GAMES),
        "market_source_selected": str(market_path),
        "market_source_diagnostics": source_diagnostics,
        "rp_rows": len(rp),
        "unique_rp_games": int(rp["game_id_key"].nunique()),
        "rows_with_valid_open_close": int(joined["market_joined"].sum()),
        "rows_missing_valid_open_close": int((~joined["market_joined"]).sum()),
        "coverage_pct": (
            float(joined["market_joined"].mean())
            if len(joined)
            else 0.0
        ),
        "canonical_gap_10_rows": len(canonical),
        "canonical_gap_10_clv_rows": int(
            canonical["team_clv"].notna().sum()
        ),
        "team_perspective_clv_formula": (
            "opening team spread minus closing team spread; positive means "
            "the selected team beat the closing line"
        ),
        "production_signals_changed": False,
        "warnings": [
            "This is a research audit only.",
            "No current 2026 returning-production signals were changed.",
            "Historical opener and close provenance must be reviewed before promotion.",
        ],
    }

    AUDIT_OUT.write_text(json.dumps(audit, indent=2))

    print(json.dumps(audit, indent=2))
    print("\nOVERALL GAP-10 SUMMARY")
    print(overall.to_string(index=False))

    print("\nSEASON STABILITY")
    print(
        pd.DataFrame(season_direction).to_string(index=False)
    )

    print("\nwrote:", OUT_DIR)
    print("wrote:", AUDIT_OUT)


if __name__ == "__main__":
    main()
