#!/usr/bin/env python3
"""Validate two standalone 1H RP candidates and identify 2026 matches.

Historical validation window:
    2024-2025, Weeks 1-4

2026 estimated first-half spread:
    estimated_1h_spread = full_game_model_spread / 2

Candidate A — Defensive continuity favorite
    Defense RP minus opponent offense RP >= threshold
    Estimated 1H spread makes the RP team a favorite

Candidate B — Offensive continuity underdog
    Offense RP minus opponent defense RP >= minimum offensive edge
    Defense RP minus opponent offense RP < 0
    Estimated 1H spread makes the RP team an underdog

This is a research/line-watch output. Estimated 1H spreads are not actual
sportsbook prices and should be replaced when real 1H openers become available.
"""

from __future__ import annotations

from pathlib import Path
import json
import math
import re
import sys
import unicodedata
from typing import Any

import numpy as np
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")

HIST_DETAIL = BASE / "data/research/rp_1h_discovery_detail_2024_2025.csv"
INDEX_HTML = BASE / "index.html"

OUT_VALIDATION = BASE / "data/research/rp_1h_candidate_validation_2024_2025.csv"
OUT_SEASON = BASE / "data/research/rp_1h_candidate_by_season_2024_2025.csv"
OUT_SENSITIVITY = BASE / "data/research/rp_1h_candidate_threshold_sensitivity_2024_2025.csv"
OUT_2026 = BASE / "data/signals/rp_1h_candidate_matches_2026_estimated.csv"
OUT_JSON = BASE / "data/site/rp_1h_candidate_matches_2026_estimated.json"
OUT_AUDIT = BASE / "data/audits/rp_1h_candidate_matches_2026_audit.csv"


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


def js_object(text: str, const_name: str) -> Any:
    pattern = re.compile(
        rf"const\s+{re.escape(const_name)}\s*=\s*",
        flags=re.M,
    )
    match = pattern.search(text)
    if not match:
        raise KeyError(f"Could not find JavaScript constant {const_name}")

    start = match.end()
    while start < len(text) and text[start].isspace():
        start += 1

    opening = text[start]
    if opening not in "[{":
        raise ValueError(f"{const_name} does not begin with an object or array")

    closing = "}" if opening == "{" else "]"
    depth = 0
    in_string = False
    quote = ""
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                in_string = False
            continue

        if char in {"'", '"', "`"}:
            in_string = True
            quote = char
            continue

        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                raw = text[start:index + 1]
                # Expected project constants are JSON-compatible.
                try:
                    return json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"{const_name} was found but is not strict JSON: {exc}"
                    ) from exc

    raise ValueError(f"Could not find end of {const_name}")


def embedded_db(text: str) -> dict[str, Any]:
    match = re.search(
        r'<script[^>]+id=["\']db["\'][^>]*>(.*?)</script>',
        text,
        flags=re.S | re.I,
    )
    if not match:
        raise KeyError("Could not find embedded <script id='db'>")
    return json.loads(match.group(1))


def numeric(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        number = float(value)
        return number if np.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def first_number(obj: dict[str, Any], keys: list[str]) -> float | None:
    for key in keys:
        if key in obj:
            value = numeric(obj.get(key))
            if value is not None:
                return value
    return None


def rp_values(row: dict[str, Any]) -> tuple[float | None, float | None, float | None]:
    overall = first_number(
        row,
        ["overall", "overall_pct", "overall_rp", "overall_returning_production"],
    )
    offense = first_number(
        row,
        ["offense", "offense_pct", "off_rp", "offensive_returning_production"],
    )
    defense = first_number(
        row,
        ["defense", "defense_pct", "def_rp", "defensive_returning_production"],
    )
    return overall, offense, defense


def model_home_spread(game: dict[str, Any]) -> float | None:
    """Return model spread from the home-team perspective."""
    keys = [
        "model_spread_home",
        "projected_spread_home",
        "site_spread_home",
        "blend_spread_home",
        "consensus_model_spread_home",
        "home_model_spread",
        "model_home_spread",
    ]

    value = first_number(game, keys)
    if value is not None:
        return value

    # Some project rows store the projected line under a general spread key.
    for container_key in ["projection", "model", "projections"]:
        container = game.get(container_key)
        if isinstance(container, dict):
            value = first_number(container, keys + ["home_spread", "spread_home"])
            if value is not None:
                return value

    # Fallback: a projected favorite and margin.
    favorite = str(
        game.get("model_favorite")
        or game.get("projected_favorite")
        or ""
    ).strip()
    margin = first_number(
        game,
        ["model_margin", "projected_margin", "spread_margin"],
    )

    if favorite and margin is not None:
        home = str(game.get("home_team", "")).strip()
        away = str(game.get("away_team", "")).strip()
        magnitude = abs(margin)
        if favorite == home:
            return -magnitude
        if favorite == away:
            return magnitude

    return None


def oriented_spread(
    home_spread: float | None,
    team: str,
    home_team: str,
    away_team: str,
) -> float | None:
    if home_spread is None:
        return None
    if team == home_team:
        return home_spread
    if team == away_team:
        return -home_spread
    return None


def ats_result(series: pd.Series) -> tuple[int, int, int, float]:
    wins = int((series == "W").sum())
    losses = int((series == "L").sum())
    pushes = int((series == "P").sum())
    decisions = wins + losses
    pct = wins / decisions if decisions else np.nan
    return wins, losses, pushes, pct


def historical_base() -> pd.DataFrame:
    detail = pd.read_csv(HIST_DETAIL, low_memory=False)

    required = {
        "season",
        "week",
        "game_id",
        "rp_team",
        "rp_opponent",
        "overall_rp_edge",
        "offense_vs_defense_edge",
        "defense_vs_offense_edge",
        "rp_team_1h_spread",
        "rp_team_1h_ats_result",
        "rp_team_1h_ats_margin",
    }
    missing = sorted(required - set(detail.columns))
    if missing:
        raise KeyError(f"Discovery detail missing columns: {missing}")

    # The discovery detail contains repeated rows for many tested rules.
    # Collapse to one underlying team-side observation per game.
    base = (
        detail.sort_values(["season", "game_id"])
        .drop_duplicates(["season", "game_id", "rp_team"], keep="first")
        .copy()
    )

    base["season"] = pd.to_numeric(base["season"], errors="coerce")
    base["week"] = pd.to_numeric(base["week"], errors="coerce")
    base["rp_team_1h_spread"] = pd.to_numeric(
        base["rp_team_1h_spread"],
        errors="coerce",
    )

    return base


def candidate_mask(
    frame: pd.DataFrame,
    candidate: str,
    threshold: float,
) -> pd.Series:
    if candidate == "A_DEFENSIVE_FAVORITE":
        return (
            (frame["defense_vs_offense_edge"] >= threshold)
            & (frame["rp_team_1h_spread"] < 0)
        )

    if candidate == "B_OFFENSIVE_UNDERDOG":
        return (
            (frame["offense_vs_defense_edge"] >= threshold)
            & (frame["defense_vs_offense_edge"] < 0)
            & (frame["rp_team_1h_spread"] > 0)
        )

    raise KeyError(candidate)


def summarize_historical(
    frame: pd.DataFrame,
    candidate: str,
    threshold: float,
) -> dict[str, Any]:
    selected = frame[candidate_mask(frame, candidate, threshold)].copy()

    wins, losses, pushes, pct = ats_result(
        selected["rp_team_1h_ats_result"]
    )

    by_season = []
    for season, group in selected.groupby("season"):
        sw, sl, sp, spct = ats_result(group["rp_team_1h_ats_result"])
        by_season.append(
            {
                "candidate_key": candidate,
                "threshold": threshold,
                "season": int(season),
                "games": len(group),
                "wins": sw,
                "losses": sl,
                "pushes": sp,
                "ats_pct": spct,
                "avg_ats_margin": group["rp_team_1h_ats_margin"].mean(),
                "median_ats_margin": group["rp_team_1h_ats_margin"].median(),
            }
        )

    return {
        "candidate_key": candidate,
        "threshold": threshold,
        "games": len(selected),
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "ats_pct": pct,
        "avg_ats_margin": selected["rp_team_1h_ats_margin"].mean(),
        "median_ats_margin": selected["rp_team_1h_ats_margin"].median(),
        "positive_seasons": sum(
            1 for row in by_season
            if pd.notna(row["ats_pct"]) and row["ats_pct"] > 0.5
        ),
        "season_rows": by_season,
    }


def load_2026() -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    text = INDEX_HTML.read_text(encoding="utf-8", errors="ignore")
    db = embedded_db(text)
    rp_raw = js_object(text, "RETURNING_PRODUCTION_2026")

    rp_lookup: dict[str, dict[str, Any]] = {}

    if isinstance(rp_raw, dict):
        iterator = rp_raw.items()
    elif isinstance(rp_raw, list):
        iterator = [
            (
                row.get("team")
                or row.get("team_name")
                or row.get("name")
                or "",
                row,
            )
            for row in rp_raw
            if isinstance(row, dict)
        ]
    else:
        raise TypeError("RETURNING_PRODUCTION_2026 has unexpected type")

    for team_name, row in iterator:
        if isinstance(row, dict):
            rp_lookup[normalize_team(team_name)] = row

    games = db.get("games")
    if not isinstance(games, list):
        raise KeyError("Embedded DB does not contain a games list")

    return db, rp_lookup, games


def build_2026_matches(
    rp_lookup: dict[str, dict[str, Any]],
    games: list[dict[str, Any]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for game in games:
        week = numeric(game.get("week"))
        if week is None or not (1 <= week <= 4):
            continue

        away = str(game.get("away_team", "")).strip()
        home = str(game.get("home_team", "")).strip()
        if not away or not home:
            continue

        away_rp = rp_lookup.get(normalize_team(away))
        home_rp = rp_lookup.get(normalize_team(home))
        if not away_rp or not home_rp:
            continue

        away_overall, away_off, away_def = rp_values(away_rp)
        home_overall, home_off, home_def = rp_values(home_rp)

        if None in [away_off, away_def, home_off, home_def]:
            continue

        home_model_spread = model_home_spread(game)
        if home_model_spread is None:
            continue

        for team, opponent, is_home in [
            (away, home, False),
            (home, away, True),
        ]:
            if is_home:
                overall_edge = (
                    None
                    if home_overall is None or away_overall is None
                    else home_overall - away_overall
                )
                offense_edge = home_off - away_def
                defense_edge = home_def - away_off
            else:
                overall_edge = (
                    None
                    if away_overall is None or home_overall is None
                    else away_overall - home_overall
                )
                offense_edge = away_off - home_def
                defense_edge = away_def - home_off

            full_game_team_spread = oriented_spread(
                home_model_spread,
                team,
                home,
                away,
            )
            estimated_1h_spread = (
                full_game_team_spread / 2
                if full_game_team_spread is not None
                else None
            )

            candidate_a = (
                defense_edge >= 25
                and estimated_1h_spread is not None
                and estimated_1h_spread < 0
            )
            candidate_b = (
                offense_edge > 0
                and defense_edge < 0
                and estimated_1h_spread is not None
                and estimated_1h_spread > 0
            )

            if not candidate_a and not candidate_b:
                continue

            candidate_keys = []
            if candidate_a:
                candidate_keys.append("A_DEFENSIVE_FAVORITE")
            if candidate_b:
                candidate_keys.append("B_OFFENSIVE_UNDERDOG")

            for key in candidate_keys:
                rows.append(
                    {
                        "game_id": str(game.get("game_id", "")),
                        "week": int(week),
                        "date": str(game.get("date", "")),
                        "away_team": away,
                        "home_team": home,
                        "signal_team": team,
                        "signal_opponent": opponent,
                        "candidate_key": key,
                        "candidate_label": (
                            "Defensive RP edge 25+ with estimated 1H favorite"
                            if key == "A_DEFENSIVE_FAVORITE"
                            else "Positive offensive RP edge / negative defensive RP edge with estimated 1H underdog"
                        ),
                        "overall_rp_edge": overall_edge,
                        "offense_vs_defense_edge": offense_edge,
                        "defense_vs_offense_edge": defense_edge,
                        "full_game_model_spread": full_game_team_spread,
                        "estimated_1h_spread": estimated_1h_spread,
                        "estimated_1h_role": (
                            "Favorite"
                            if estimated_1h_spread < 0
                            else "Underdog"
                            if estimated_1h_spread > 0
                            else "Pick'em"
                        ),
                        "estimate_method": "full_game_model_spread / 2",
                        "production_status": "Research line watch",
                    }
                )

    frame = pd.DataFrame(rows)

    if not frame.empty:
        frame.sort_values(
            ["week", "date", "candidate_key", "signal_team"],
            inplace=True,
        )

    return frame


def main() -> None:
    print("Validating standalone 1H RP candidates and identifying 2026 matches")
    print("Estimated 1H spread = full-game model spread / 2")

    hist = historical_base()

    validation_rows = []
    season_rows = []

    sensitivity_plan = {
        "A_DEFENSIVE_FAVORITE": [20, 25, 30],
        "B_OFFENSIVE_UNDERDOG": [0.0001, 5, 10, 15],
    }

    for candidate, thresholds in sensitivity_plan.items():
        for threshold in thresholds:
            result = summarize_historical(hist, candidate, threshold)
            validation_rows.append(
                {k: v for k, v in result.items() if k != "season_rows"}
            )
            season_rows.extend(result["season_rows"])

    validation = pd.DataFrame(validation_rows)
    seasons = pd.DataFrame(season_rows)

    primary_validation = validation[
        (
            (validation["candidate_key"] == "A_DEFENSIVE_FAVORITE")
            & (validation["threshold"] == 25)
        )
        |
        (
            (validation["candidate_key"] == "B_OFFENSIVE_UNDERDOG")
            & (validation["threshold"] < 1)
        )
    ].copy()

    db, rp_lookup, games = load_2026()
    matches = build_2026_matches(rp_lookup, games)

    history_lookup = {}
    for _, row in primary_validation.iterrows():
        history_lookup[row["candidate_key"]] = {
            "historical_games": int(row["games"]),
            "historical_wins": int(row["wins"]),
            "historical_losses": int(row["losses"]),
            "historical_pushes": int(row["pushes"]),
            "historical_ats_pct": (
                round(float(row["ats_pct"]) * 100, 1)
                if pd.notna(row["ats_pct"])
                else None
            ),
            "historical_avg_ats_margin": (
                round(float(row["avg_ats_margin"]), 2)
                if pd.notna(row["avg_ats_margin"])
                else None
            ),
            "historical_median_ats_margin": (
                round(float(row["median_ats_margin"]), 2)
                if pd.notna(row["median_ats_margin"])
                else None
            ),
        }

    if not matches.empty:
        for key, values in history_lookup.items():
            mask = matches["candidate_key"].eq(key)
            for column, value in values.items():
                matches.loc[mask, column] = value

    for path in [
        OUT_VALIDATION,
        OUT_SEASON,
        OUT_SENSITIVITY,
        OUT_2026,
        OUT_JSON,
        OUT_AUDIT,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)

    primary_validation.to_csv(OUT_VALIDATION, index=False)
    seasons.to_csv(OUT_SEASON, index=False)
    validation.to_csv(OUT_SENSITIVITY, index=False)
    matches.to_csv(OUT_2026, index=False)

    json_payload = {
        "meta": {
            "season": 2026,
            "weeks": "1-4",
            "estimated_1h_spread_method": "full_game_model_spread / 2",
            "warning": (
                "Estimated 1H spreads are research approximations, not sportsbook prices."
            ),
            "candidates": history_lookup,
        },
        "matches": (
            matches.replace({np.nan: None}).to_dict("records")
            if not matches.empty
            else []
        ),
    }
    OUT_JSON.write_text(
        json.dumps(json_payload, indent=2),
        encoding="utf-8",
    )

    audit = pd.DataFrame(
        [
            {"metric": "historical_unique_games", "value": hist["game_id"].nunique()},
            {"metric": "2026_schedule_games_scanned", "value": len(games)},
            {"metric": "2026_rp_teams_available", "value": len(rp_lookup)},
            {"metric": "2026_candidate_rows", "value": len(matches)},
            {
                "metric": "2026_unique_candidate_games",
                "value": matches["game_id"].nunique() if not matches.empty else 0,
            },
            {
                "metric": "candidate_a_rows",
                "value": int(
                    matches["candidate_key"].eq("A_DEFENSIVE_FAVORITE").sum()
                ) if not matches.empty else 0,
            },
            {
                "metric": "candidate_b_rows",
                "value": int(
                    matches["candidate_key"].eq("B_OFFENSIVE_UNDERDOG").sum()
                ) if not matches.empty else 0,
            },
            {
                "metric": "estimate_warning",
                "value": "Replace estimated 1H spreads with actual 1H openers before betting.",
            },
        ]
    )
    audit.to_csv(OUT_AUDIT, index=False)

    print()
    print("HISTORICAL CANDIDATE VALIDATION")
    print("=" * 110)

    display = primary_validation.copy()
    display["ats_pct"] = (display["ats_pct"] * 100).round(1)
    display["avg_ats_margin"] = display["avg_ats_margin"].round(2)
    display["median_ats_margin"] = display["median_ats_margin"].round(2)

    print(
        display[
            [
                "candidate_key",
                "threshold",
                "games",
                "wins",
                "losses",
                "pushes",
                "ats_pct",
                "avg_ats_margin",
                "median_ats_margin",
                "positive_seasons",
            ]
        ].to_string(index=False)
    )

    print()
    print("2026 ESTIMATED 1H RP CANDIDATE MATCHES")
    print("=" * 140)

    if matches.empty:
        print("No 2026 games matched the two candidate rules using model spread / 2.")
    else:
        printable = matches.copy()
        for column in [
            "overall_rp_edge",
            "offense_vs_defense_edge",
            "defense_vs_offense_edge",
            "full_game_model_spread",
            "estimated_1h_spread",
        ]:
            printable[column] = pd.to_numeric(
                printable[column],
                errors="coerce",
            ).round(1)

        print(
            printable[
                [
                    "week",
                    "date",
                    "away_team",
                    "home_team",
                    "signal_team",
                    "candidate_key",
                    "overall_rp_edge",
                    "offense_vs_defense_edge",
                    "defense_vs_offense_edge",
                    "full_game_model_spread",
                    "estimated_1h_spread",
                    "historical_games",
                    "historical_ats_pct",
                ]
            ].to_string(index=False)
        )

    print()
    print("THRESHOLD SENSITIVITY")
    print("=" * 110)

    sensitivity_display = validation.copy()
    sensitivity_display["ats_pct"] = (
        sensitivity_display["ats_pct"] * 100
    ).round(1)
    sensitivity_display["avg_ats_margin"] = (
        sensitivity_display["avg_ats_margin"].round(2)
    )
    sensitivity_display["median_ats_margin"] = (
        sensitivity_display["median_ats_margin"].round(2)
    )

    print(
        sensitivity_display[
            [
                "candidate_key",
                "threshold",
                "games",
                "wins",
                "losses",
                "pushes",
                "ats_pct",
                "avg_ats_margin",
                "median_ats_margin",
                "positive_seasons",
            ]
        ].to_string(index=False)
    )

    print()
    print("Created:")
    print(OUT_VALIDATION)
    print(OUT_SEASON)
    print(OUT_SENSITIVITY)
    print(OUT_2026)
    print(OUT_JSON)
    print(OUT_AUDIT)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
