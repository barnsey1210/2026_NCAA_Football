#!/usr/bin/env python3
"""Correct 2026 estimated 1H RP candidate roles using model margin convention.

Important convention fix
------------------------
The current site field `projection_spread_home` is a projected HOME MARGIN:
    positive = home team projected to win by that amount
    negative = away team projected to win by that amount

A sportsbook-style home spread is therefore:
    home_betting_spread = -projection_spread_home

Estimated first-half line:
    estimated_home_1h_spread = home_betting_spread / 2

This script rebuilds Candidate A and Candidate B with the corrected sign.

Candidate A:
    Defense RP minus opponent offense RP >= 25
    Signal team is an estimated 1H favorite

Candidate B:
    Offense RP minus opponent defense RP > 0
    Defense RP minus opponent offense RP < 0
    Signal team is an estimated 1H underdog
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import unicodedata
from typing import Any

import numpy as np
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")
INDEX_HTML = BASE / "index.html"

OUT_ALL = BASE / "data/research/rp_1h_2026_all_team_sides_estimated_corrected.csv"
OUT_MATCHES = BASE / "data/signals/rp_1h_candidate_matches_2026_estimated_corrected.csv"
OUT_JSON = BASE / "data/site/rp_1h_candidate_matches_2026_estimated_corrected.json"
OUT_AUDIT = BASE / "data/audits/rp_1h_candidate_matches_2026_estimated_corrected_audit.csv"


ALIASES = {
    "texas a m": "texas a&m",
    "app st": "appalachian state",
    "app state": "appalachian state",
    "wku": "western kentucky",
    "va tech": "virginia tech",
    "fau": "florida atlantic",
    "fiu": "florida international",
    "so miss": "southern miss",
    "miss st": "mississippi state",
    "nc st": "nc state",
    "ohio st": "ohio state",
    "wash st": "washington state",
}


def normalize_team(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return ALIASES.get(text, text)


def numeric(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        value = float(value)
        return value if np.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def embedded_db(text: str) -> dict[str, Any]:
    match = re.search(
        r'<script[^>]+id=["\']db["\'][^>]*>(.*?)</script>',
        text,
        flags=re.S | re.I,
    )
    if not match:
        raise KeyError("Could not find embedded <script id='db'>")
    return json.loads(match.group(1))


def js_object(text: str, const_name: str) -> Any:
    match = re.search(rf"const\s+{re.escape(const_name)}\s*=\s*", text)
    if not match:
        raise KeyError(f"Could not find JavaScript constant {const_name}")

    start = match.end()
    while start < len(text) and text[start].isspace():
        start += 1

    opener = text[start]
    closer = "}" if opener == "{" else "]"
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

        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return json.loads(text[start:index + 1])

    raise ValueError(f"Could not parse {const_name}")


def rp_values(record: dict[str, Any]) -> tuple[float | None, float | None, float | None]:
    overall = numeric(record.get("overall"))
    offense = numeric(record.get("off"))
    defense = numeric(record.get("def"))
    return overall, offense, defense


def projected_home_margin(game: dict[str, Any]) -> tuple[str, float | None]:
    for key in [
        "projection_spread_home",
        "projected_margin_home",
        "site_spread_home",
        "blend_spread_home",
    ]:
        value = numeric(game.get(key))
        if value is not None:
            return key, value
    return "", None


def team_betting_spread(
    projected_margin_home: float,
    team: str,
    home_team: str,
    away_team: str,
) -> float | None:
    # Convert projected home margin to sportsbook-style home spread.
    home_betting_spread = -projected_margin_home

    if team == home_team:
        return home_betting_spread
    if team == away_team:
        return -home_betting_spread
    return None


def main() -> None:
    text = INDEX_HTML.read_text(encoding="utf-8", errors="ignore")
    db = embedded_db(text)
    rp_raw = js_object(text, "RETURNING_PRODUCTION_2026")

    if not isinstance(rp_raw, dict):
        raise TypeError("RETURNING_PRODUCTION_2026 is not a dictionary")

    rp_lookup = {
        normalize_team(team): record
        for team, record in rp_raw.items()
        if isinstance(record, dict)
    }

    rows = []

    for game in db.get("games", []):
        week = numeric(game.get("week"))
        if week is None or not 1 <= week <= 4:
            continue

        away = str(game.get("away_team", "")).strip()
        home = str(game.get("home_team", "")).strip()

        away_record = rp_lookup.get(normalize_team(away))
        home_record = rp_lookup.get(normalize_team(home))

        if not away_record or not home_record:
            continue

        away_overall, away_offense, away_defense = rp_values(away_record)
        home_overall, home_offense, home_defense = rp_values(home_record)

        required = [
            away_offense,
            away_defense,
            home_offense,
            home_defense,
        ]
        if any(value is None for value in required):
            continue

        model_field, home_margin = projected_home_margin(game)
        if home_margin is None:
            continue

        for signal_team, opponent, side in [
            (away, home, "away"),
            (home, away, "home"),
        ]:
            if side == "away":
                team_overall = away_overall
                team_offense = away_offense
                team_defense = away_defense
                opponent_overall = home_overall
                opponent_offense = home_offense
                opponent_defense = home_defense
            else:
                team_overall = home_overall
                team_offense = home_offense
                team_defense = home_defense
                opponent_overall = away_overall
                opponent_offense = away_offense
                opponent_defense = away_defense

            overall_edge = (
                None
                if team_overall is None or opponent_overall is None
                else team_overall - opponent_overall
            )
            offense_edge = team_offense - opponent_defense
            defense_edge = team_defense - opponent_offense

            full_game_betting_spread = team_betting_spread(
                home_margin,
                signal_team,
                home,
                away,
            )
            estimated_1h_spread = (
                full_game_betting_spread / 2
                if full_game_betting_spread is not None
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

            rows.append(
                {
                    "game_id": game.get("game_id"),
                    "week": int(week),
                    "date": game.get("date"),
                    "away_team": away,
                    "home_team": home,
                    "signal_team": signal_team,
                    "signal_opponent": opponent,
                    "signal_side": side,
                    "overall_rp_edge": overall_edge,
                    "offense_vs_defense_edge": offense_edge,
                    "defense_vs_offense_edge": defense_edge,
                    "model_field": model_field,
                    "projected_home_margin": home_margin,
                    "full_game_model_betting_spread": full_game_betting_spread,
                    "estimated_1h_spread": estimated_1h_spread,
                    "estimated_1h_role": (
                        "Favorite"
                        if estimated_1h_spread < 0
                        else "Underdog"
                        if estimated_1h_spread > 0
                        else "Pick'em"
                    ),
                    "candidate_a_defensive_favorite": candidate_a,
                    "candidate_b_offensive_underdog": candidate_b,
                }
            )

    all_sides = pd.DataFrame(rows)
    OUT_ALL.parent.mkdir(parents=True, exist_ok=True)
    all_sides.to_csv(OUT_ALL, index=False)

    matches = []

    for _, row in all_sides.iterrows():
        if bool(row["candidate_a_defensive_favorite"]):
            item = row.to_dict()
            item.update(
                {
                    "candidate_key": "A_DEFENSIVE_FAVORITE",
                    "candidate_label": (
                        "Defensive RP edge 25+ with estimated 1H favorite"
                    ),
                    "historical_record": "22-10",
                    "historical_ats_pct": 68.8,
                    "historical_avg_ats_margin": 3.84,
                    "historical_median_ats_margin": 5.50,
                }
            )
            matches.append(item)

        if bool(row["candidate_b_offensive_underdog"]):
            item = row.to_dict()
            item.update(
                {
                    "candidate_key": "B_OFFENSIVE_UNDERDOG",
                    "candidate_label": (
                        "Positive offensive RP edge and negative defensive "
                        "RP edge with estimated 1H underdog"
                    ),
                    "historical_record": "13-6",
                    "historical_ats_pct": 68.4,
                    "historical_avg_ats_margin": 2.34,
                    "historical_median_ats_margin": 4.50,
                }
            )
            matches.append(item)

    match_frame = pd.DataFrame(matches)

    if not match_frame.empty:
        match_frame.sort_values(
            ["week", "date", "candidate_key", "signal_team"],
            inplace=True,
        )

    OUT_MATCHES.parent.mkdir(parents=True, exist_ok=True)
    match_frame.to_csv(OUT_MATCHES, index=False)

    payload = {
        "meta": {
            "model_field": "projection_spread_home",
            "model_field_interpretation": (
                "Positive means projected home winning margin."
            ),
            "home_betting_spread_conversion": (
                "home_betting_spread = -projection_spread_home"
            ),
            "estimated_1h_method": (
                "team full-game model betting spread / 2"
            ),
            "warning": (
                "Estimated 1H spreads are research approximations, not sportsbook prices."
            ),
        },
        "matches": (
            match_frame.replace({np.nan: None}).to_dict("records")
            if not match_frame.empty
            else []
        ),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    audit = pd.DataFrame(
        [
            {"metric": "team_side_rows", "value": len(all_sides)},
            {
                "metric": "candidate_a_matches",
                "value": int(
                    all_sides["candidate_a_defensive_favorite"].sum()
                ),
            },
            {
                "metric": "candidate_b_matches",
                "value": int(
                    all_sides["candidate_b_offensive_underdog"].sum()
                ),
            },
            {
                "metric": "unique_candidate_games",
                "value": (
                    match_frame["game_id"].nunique()
                    if not match_frame.empty
                    else 0
                ),
            },
            {
                "metric": "sign_fix",
                "value": (
                    "projection_spread_home treated as projected home margin; "
                    "converted to betting spread by multiplying by -1."
                ),
            },
        ]
    )

    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(OUT_AUDIT, index=False)

    print("CORRECTED 2026 ESTIMATED 1H RP CANDIDATES")
    print("=" * 155)
    print(audit.to_string(index=False))

    print()
    if match_frame.empty:
        print("No matches after correcting the model-spread sign.")
    else:
        printable = match_frame.copy()

        for column in [
            "overall_rp_edge",
            "offense_vs_defense_edge",
            "defense_vs_offense_edge",
            "projected_home_margin",
            "full_game_model_betting_spread",
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
                    "offense_vs_defense_edge",
                    "defense_vs_offense_edge",
                    "full_game_model_betting_spread",
                    "estimated_1h_spread",
                    "historical_record",
                    "historical_ats_pct",
                ]
            ].to_string(index=False)
        )

    print()
    print("Created:")
    print(OUT_ALL)
    print(OUT_MATCHES)
    print(OUT_JSON)
    print(OUT_AUDIT)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
