#!/usr/bin/env python3
"""Diagnose and rebuild 2026 estimated 1H RP candidates from current site data.

This version fixes two likely issues from the prior audit:
1. Returning-production values may be nested or use different field names.
2. The model spread field is confirmed as projection_spread_home.

It recursively inspects RP records, identifies the most likely overall/offense/
defense percentage fields, calculates team-side matchup edges, estimates the
1H spread as projection_spread_home / 2, and identifies Candidate A/B matches.

Read-only except for CSV/JSON outputs.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import unicodedata
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")
INDEX_HTML = BASE / "index.html"

OUT_FIELD_AUDIT = BASE / "data/audits/rp_2026_field_structure_audit.csv"
OUT_ALL_SIDES = BASE / "data/research/rp_1h_2026_all_team_sides_estimated.csv"
OUT_MATCHES = BASE / "data/signals/rp_1h_candidate_matches_2026_estimated_v2.csv"
OUT_JSON = BASE / "data/site/rp_1h_candidate_matches_2026_estimated_v2.json"
OUT_SUMMARY = BASE / "data/audits/rp_1h_candidate_matches_2026_estimated_v2_audit.csv"


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
        n = float(value)
        return n if np.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def embedded_db(text: str) -> dict[str, Any]:
    m = re.search(
        r'<script[^>]+id=["\']db["\'][^>]*>(.*?)</script>',
        text,
        flags=re.S | re.I,
    )
    if not m:
        raise KeyError("Could not find embedded <script id='db'>")
    return json.loads(m.group(1))


def js_object(text: str, const_name: str) -> Any:
    m = re.search(rf"const\s+{re.escape(const_name)}\s*=\s*", text)
    if not m:
        raise KeyError(f"Could not find JavaScript constant {const_name}")

    start = m.end()
    while start < len(text) and text[start].isspace():
        start += 1

    opener = text[start]
    if opener not in "[{":
        raise ValueError(f"{const_name} does not begin with object/array")

    closer = "}" if opener == "{" else "]"
    depth = 0
    in_string = False
    quote = ""
    escaped = False

    for i in range(start, len(text)):
        ch = text[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                in_string = False
            continue

        if ch in {"'", '"', "`"}:
            in_string = True
            quote = ch
            continue

        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])

    raise ValueError(f"Could not parse {const_name}")


def flatten_numeric(obj: Any, prefix: str = "") -> dict[str, float]:
    out: dict[str, float] = {}

    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            n = numeric(value)
            if n is not None:
                out[path] = n
            elif isinstance(value, (dict, list)):
                out.update(flatten_numeric(value, path))

    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            path = f"{prefix}[{idx}]"
            if isinstance(value, (dict, list)):
                out.update(flatten_numeric(value, path))
            else:
                n = numeric(value)
                if n is not None:
                    out[path] = n

    return out


def field_score(path: str, metric: str) -> int:
    p = path.lower()
    score = 0

    if metric == "overall":
        if "overall" in p:
            score += 100
        if "total" in p:
            score += 20

    elif metric == "offense":
        if "offense" in p or re.search(r"(^|[._])off([._]|$)", p):
            score += 100
        if "offensive" in p:
            score += 20

    elif metric == "defense":
        if "defense" in p or re.search(r"(^|[._])def([._]|$)", p):
            score += 100
        if "defensive" in p:
            score += 20

    if "pct" in p or "percent" in p:
        score += 40
    if "return" in p or "production" in p or "rp" in p:
        score += 30

    if "rank" in p:
        score -= 100
    if "year" in p or "season" in p:
        score -= 50

    return score


def choose_metric(flat: dict[str, float], metric: str) -> tuple[str, float | None]:
    candidates = []

    for path, value in flat.items():
        score = field_score(path, metric)

        # Returning-production percentages are normally in a 0-100 range.
        if 0 <= value <= 100:
            score += 10
        else:
            score -= 20

        if score > 0:
            candidates.append((score, path, value))

    if not candidates:
        return "", None

    candidates.sort(reverse=True)
    _, path, value = candidates[0]
    return path, value


def model_home_spread(game: dict[str, Any]) -> tuple[str, float | None]:
    preferred = [
        "projection_spread_home",
        "site_spread_home",
        "blend_spread_home",
        "projected_margin_home",
    ]

    for key in preferred:
        n = numeric(game.get(key))
        if n is not None:
            return key, n

    for container_name in ["projection", "model", "projections"]:
        container = game.get(container_name)
        if not isinstance(container, dict):
            continue
        for key in preferred + ["spread_home", "home_spread"]:
            n = numeric(container.get(key))
            if n is not None:
                return f"{container_name}.{key}", n

    return "", None


def oriented_spread(
    home_spread: float,
    signal_team: str,
    home_team: str,
    away_team: str,
) -> float | None:
    if signal_team == home_team:
        return home_spread
    if signal_team == away_team:
        return -home_spread
    return None


def main() -> None:
    text = INDEX_HTML.read_text(encoding="utf-8", errors="ignore")
    db = embedded_db(text)
    rp_raw = js_object(text, "RETURNING_PRODUCTION_2026")

    if not isinstance(rp_raw, dict):
        raise TypeError("RETURNING_PRODUCTION_2026 is not a dictionary")

    rp_lookup: dict[str, dict[str, Any]] = {}
    field_rows = []
    field_counter = Counter()

    for team_name, record in rp_raw.items():
        if not isinstance(record, dict):
            continue

        flat = flatten_numeric(record)
        overall_path, overall = choose_metric(flat, "overall")
        offense_path, offense = choose_metric(flat, "offense")
        defense_path, defense = choose_metric(flat, "defense")

        rp_lookup[normalize_team(team_name)] = {
            "team_name": team_name,
            "overall": overall,
            "offense": offense,
            "defense": defense,
            "overall_path": overall_path,
            "offense_path": offense_path,
            "defense_path": defense_path,
            "all_numeric_fields": flat,
        }

        for path in flat:
            field_counter[path] += 1

        field_rows.append(
            {
                "team": team_name,
                "overall_path": overall_path,
                "overall_value": overall,
                "offense_path": offense_path,
                "offense_value": offense,
                "defense_path": defense_path,
                "defense_value": defense,
                "numeric_field_count": len(flat),
                "all_numeric_fields": json.dumps(flat, sort_keys=True),
            }
        )

    field_audit = pd.DataFrame(field_rows)
    OUT_FIELD_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    field_audit.to_csv(OUT_FIELD_AUDIT, index=False)

    side_rows = []
    games = db.get("games", [])

    for game in games:
        week = numeric(game.get("week"))
        if week is None or not (1 <= week <= 4):
            continue

        away = str(game.get("away_team", "")).strip()
        home = str(game.get("home_team", "")).strip()

        away_rp = rp_lookup.get(normalize_team(away))
        home_rp = rp_lookup.get(normalize_team(home))

        if not away_rp or not home_rp:
            continue

        needed = [
            away_rp["offense"],
            away_rp["defense"],
            home_rp["offense"],
            home_rp["defense"],
        ]
        if any(value is None for value in needed):
            continue

        spread_field, home_model_spread = model_home_spread(game)
        if home_model_spread is None:
            continue

        for signal_team, opponent, side in [
            (away, home, "away"),
            (home, away, "home"),
        ]:
            if side == "away":
                team_rp = away_rp
                opp_rp = home_rp
            else:
                team_rp = home_rp
                opp_rp = away_rp

            overall_edge = None
            if (
                team_rp["overall"] is not None
                and opp_rp["overall"] is not None
            ):
                overall_edge = team_rp["overall"] - opp_rp["overall"]

            offense_edge = team_rp["offense"] - opp_rp["defense"]
            defense_edge = team_rp["defense"] - opp_rp["offense"]

            team_full_game_spread = oriented_spread(
                home_model_spread,
                signal_team,
                home,
                away,
            )
            estimated_1h_spread = (
                team_full_game_spread / 2
                if team_full_game_spread is not None
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

            side_rows.append(
                {
                    "game_id": game.get("game_id"),
                    "week": int(week),
                    "date": game.get("date"),
                    "away_team": away,
                    "home_team": home,
                    "signal_team": signal_team,
                    "signal_opponent": opponent,
                    "signal_side": side,
                    "overall_rp": team_rp["overall"],
                    "offense_rp": team_rp["offense"],
                    "defense_rp": team_rp["defense"],
                    "opponent_overall_rp": opp_rp["overall"],
                    "opponent_offense_rp": opp_rp["offense"],
                    "opponent_defense_rp": opp_rp["defense"],
                    "overall_rp_edge": overall_edge,
                    "offense_vs_defense_edge": offense_edge,
                    "defense_vs_offense_edge": defense_edge,
                    "model_spread_field": spread_field,
                    "full_game_model_spread": team_full_game_spread,
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

    sides = pd.DataFrame(side_rows)
    OUT_ALL_SIDES.parent.mkdir(parents=True, exist_ok=True)
    sides.to_csv(OUT_ALL_SIDES, index=False)

    matches = []

    if not sides.empty:
        for _, row in sides.iterrows():
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
            "estimate_method": "projection_spread_home / 2",
            "warning": (
                "Estimated 1H spreads are model approximations and must be "
                "replaced with actual sportsbook 1H prices before betting."
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

    summary = pd.DataFrame(
        [
            {"metric": "rp_records_total", "value": len(rp_lookup)},
            {
                "metric": "rp_records_with_complete_components",
                "value": int(
                    (
                        field_audit["offense_value"].notna()
                        & field_audit["defense_value"].notna()
                    ).sum()
                ),
            },
            {"metric": "weeks_1_4_games_total", "value": int(sum(
                1 for g in games
                if numeric(g.get("week")) is not None
                and 1 <= numeric(g.get("week")) <= 4
            ))},
            {
                "metric": "team_side_rows_with_rp_and_model_spread",
                "value": len(sides),
            },
            {
                "metric": "candidate_a_matches",
                "value": int(
                    sides["candidate_a_defensive_favorite"].sum()
                ) if not sides.empty else 0,
            },
            {
                "metric": "candidate_b_matches",
                "value": int(
                    sides["candidate_b_offensive_underdog"].sum()
                ) if not sides.empty else 0,
            },
            {
                "metric": "unique_candidate_games",
                "value": (
                    match_frame["game_id"].nunique()
                    if not match_frame.empty
                    else 0
                ),
            },
        ]
    )

    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_SUMMARY, index=False)

    print("2026 RP FIELD EXTRACTION")
    print("=" * 110)
    print(summary.to_string(index=False))

    print()
    print("MOST COMMON RP NUMERIC FIELD PATHS")
    print("=" * 110)
    for path, count in field_counter.most_common(25):
        print(f"{count:>4}  {path}")

    print()
    print("2026 ESTIMATED 1H RP CANDIDATE MATCHES")
    print("=" * 150)

    if match_frame.empty:
        print("No matches after robust RP extraction.")
        print()
        print("First 15 extracted RP records:")
        print(
            field_audit[
                [
                    "team",
                    "overall_path",
                    "overall_value",
                    "offense_path",
                    "offense_value",
                    "defense_path",
                    "defense_value",
                ]
            ].head(15).to_string(index=False)
        )
    else:
        printable = match_frame.copy()
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
                    "offense_vs_defense_edge",
                    "defense_vs_offense_edge",
                    "full_game_model_spread",
                    "estimated_1h_spread",
                    "historical_record",
                    "historical_ats_pct",
                ]
            ].to_string(index=False)
        )

    print()
    print("Created:")
    print(OUT_FIELD_AUDIT)
    print(OUT_ALL_SIDES)
    print(OUT_MATCHES)
    print(OUT_JSON)
    print(OUT_SUMMARY)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
