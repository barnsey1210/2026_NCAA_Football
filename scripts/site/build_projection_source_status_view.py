#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from scripts.ratings.freshness_evidence import recover_projection_accepted_updates

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/snapshots/preseason/preseason_db.json"
CONTRACT = ROOT / "data/site/current_game_projection_contract.json"
SOURCES = ROOT / "data/projections/game_projection_sources_2026.csv"
OUT = ROOT / "data/site/projection_source_status_view.json"
PROJECTION_CHANGE_STATE = ROOT / "data/ratings/live_projection_change_status.json"

SPREAD_ID = "standard_spread_five_source_v1"
TOTAL_ID = "standard_total_sp_massey_sagarin_v1"
DEGRADED_SPREAD_ID = "standard_spread_degraded_v1"
DEGRADED_TOTAL_ID = "standard_total_degraded_v1"

SPREAD_COMPONENTS = [
    ("SP+", "SP+"),
    ("FPI", "FPI"),
    ("TeamRankings", "TeamRankings"),
    ("Sagarin Rating", "Sagarin Rating"),
    ("DRatings", "DRatings Game Predictions"),
]
SPREAD_WEIGHTS = {
    "SP+": 0.20,
    "FPI": 0.20,
    "TeamRankings": 0.20,
    "Sagarin Rating": 0.20,
    "DRatings": 0.20,
}

TOTAL_COMPONENTS = [
    ("SP+", "SP+"),
    ("Massey Dual", "Massey Dual"),
    ("Sagarin Total", "Sagarin Total"),
]
TOTAL_WEIGHTS = {
    "SP+": 0.40,
    "Massey Dual": 0.40,
    "Sagarin Total": 0.20,
}


def finite(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def source_summary(games, model_id, components):
    counts = Counter()
    labels = dict(components)
    keys = [key for key, _ in components]

    for game in games:
        projection = game.get("projections", {}).get(model_id, {})
        values = projection.get("component_values") or {}
        for key in keys:
            if finite(values.get(key)) is not None:
                counts[key] += 1

    total = len(games)
    rows = []
    for key in keys:
        n = counts[key]
        state = "FULL" if total and n == total else "PARTIAL" if n else "MISSING"
        rows.append({
            "key": key,
            "name": labels[key],
            "games_available": n,
            "production_games": total,
            "coverage_pct": round((100.0 * n / total), 1) if total else 0.0,
            "state": state,
        })
    return rows


def model_summary(
    games,
    model_id,
    degraded_model_id,
    components,
    nominal_weights,
):
    keys = [key for key, _ in components]
    statuses = Counter()
    mixes = Counter()

    for game in games:
        projection = game.get("projections", {}).get(model_id, {})
        degraded_projection = game.get("projections", {}).get(
            degraded_model_id,
            {},
        )
        status = projection.get("availability_status") or "UNKNOWN"
        statuses[status] += 1
        resolution = (
            projection.get("resolution")
            if status == "AVAILABLE"
            else degraded_projection.get("resolution")
        ) or {}
        present = set(resolution.get("available_components") or [])
        mix = tuple(key for key in keys if key in present)
        if (
            status == "AVAILABLE"
            or degraded_projection.get("availability_status") == "DEGRADED"
        ):
            mixes[mix] += 1

    full = statuses.get("AVAILABLE", 0)
    degraded = sum(
        game.get("projections", {})
        .get(degraded_model_id, {})
        .get("availability_status") == "DEGRADED"
        for game in games
    )
    displayable = full + degraded

    if full and degraded:
        current_mode = "MIXED_FULL_AND_DEGRADED"
    elif full:
        current_mode = "FULL"
    elif degraded:
        current_mode = "DEGRADED_RENORMALIZED"
    else:
        current_mode = "UNAVAILABLE"

    labels = dict(components)
    return {
        "model_id": model_id,
        "degraded_model_id": degraded_model_id,
        "production_games": len(games),
        "full_available": full,
        "degraded_available": degraded,
        "displayable": displayable,
        "coverage_pct": round(100.0 * displayable / len(games), 1) if games else 0.0,
        "current_mode": current_mode,
        "nominal_weights": nominal_weights,
        "sources": source_summary(games, model_id, components),
        "source_mixes": [
            {
                "components": [labels.get(key, key) for key in mix],
                "games": count,
                "effective_weights": {
                    labels.get(key, key): round(
                        nominal_weights[key] /
                        sum(nominal_weights[x] for x in mix),
                        6,
                    )
                    for key in mix
                } if mix else {},
            }
            for mix, count in mixes.most_common()
        ],
    }


def latest_nonblank(series):
    vals = [str(x) for x in series if pd.notna(x) and str(x).strip()]
    return max(vals) if vals else None


def game_prediction_feed_status(production_game_ids):
    if not SOURCES.is_file():
        return []

    df = pd.read_csv(SOURCES, low_memory=False)
    if df.empty:
        return []

    df["game_id"] = df["game_id"].astype(str).str.replace(r"\.0$", "", regex=True)
    df = df[df["game_id"].isin(production_game_ids)].copy()

    specs = [
        {
            "source": "DRatings Predictions",
            "name": "DRatings Game Predictions",
            "role": "Standard Spread game-prediction input",
            "value_fields": ["spread_home"],
        },
        {
            "source": "Massey Games",
            "name": "Massey Game Predictions",
            "role": "Supplies projected total + team scores used to build Massey Dual",
            "value_fields": ["total", "away_score", "home_score"],
        },
        {
            "source": "Sagarin Game Total",
            "name": "Sagarin Game Total",
            "role": "Standard Total Sagarin game-total input",
            "value_fields": ["total"],
        },
        ]

    out = []
    change_sources = {}
    if PROJECTION_CHANGE_STATE.exists():
        try:
            change_sources = json.loads(PROJECTION_CHANGE_STATE.read_text()).get("sources") or {}
        except (OSError, ValueError, TypeError):
            change_sources = {}
    recovered = recover_projection_accepted_updates(ROOT)
    total = len(production_game_ids)

    for spec in specs:
        rows = df[df["source"].eq(spec["source"])].copy()
        valid = rows.copy()
        for field in spec["value_fields"]:
            valid = valid[pd.to_numeric(valid[field], errors="coerce").notna()]

        matched_ids = set(valid["game_id"].astype(str))
        n = len(matched_ids)
        state = "FULL" if total and n == total else "PARTIAL" if n else "MISSING"

        change = change_sources.get(spec["source"]) or {}
        accepted_update_at = change.get("latest_accepted_update_at") or recovered.get(spec["source"])
        out.append({
            "name": spec["name"],
            "source_key": spec["source"],
            "role": spec["role"],
            "games_available": n,
            "production_games": total,
            "coverage_pct": round(100.0 * n / total, 1) if total else 0.0,
            "state": state,
            "latest_pulled_at": latest_nonblank(rows.get("pulled_at", pd.Series(dtype=str))),
            "latest_snapshot_date": latest_nonblank(rows.get("snapshot_date", pd.Series(dtype=str))),
            "latest_check_status": change.get("latest_check_status"),
            "latest_accepted_update_at": accepted_update_at,
            "comparison_available": bool(change.get("comparison_available") or accepted_update_at),
            "first_game_date": latest_nonblank(
                pd.Series([rows["date"].dropna().astype(str).min()]) if "date" in rows and not rows.empty else pd.Series(dtype=str)
            ),
            "last_game_date": latest_nonblank(
                pd.Series([rows["date"].dropna().astype(str).max()]) if "date" in rows and not rows.empty else pd.Series(dtype=str)
            ),
        })

    return out


def main():
    db = json.loads(DB.read_text())
    contract = json.loads(CONTRACT.read_text())

    fbs = {
        str(team.get("team")).strip()
        for team in db.get("teams", [])
        if team.get("team")
    }

    production = [
        game for game in contract.get("games", [])
        if game.get("away_team") in fbs and game.get("home_team") in fbs
    ]
    production_ids = {str(game.get("game_id")) for game in production}

    payload = {
        "schema_version": "projection-source-status-view-v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "production_scope": "FBS_VS_FBS",
        "production_games": len(production),
        "standard_spread": model_summary(
            production,
            SPREAD_ID,
            DEGRADED_SPREAD_ID,
            SPREAD_COMPONENTS,
            SPREAD_WEIGHTS,
        ),
        "standard_total": model_summary(
            production,
            TOTAL_ID,
            DEGRADED_TOTAL_ID,
            TOTAL_COMPONENTS,
            TOTAL_WEIGHTS,
        ),
        "game_prediction_feeds": game_prediction_feed_status(production_ids),
        "source_library_note": (
            "The cards below are team-rating/reference feeds. Brad Powers, "
            "Donchess Overall, Massey Power and Market-Derived are retained for "
            "history, research and future model testing. Donchess/DRatings game "
            "predictions and Massey game predictions are separate matchup-level "
            "feeds and their coverage is shown above."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print(json.dumps({
        "status": "PASS",
        "production_scope": payload["production_scope"],
        "production_games": payload["production_games"],
        "spread_displayable": (
            f'{payload["standard_spread"]["displayable"]}/'
            f'{payload["standard_spread"]["production_games"]}'
        ),
        "total_displayable": (
            f'{payload["standard_total"]["displayable"]}/'
            f'{payload["standard_total"]["production_games"]}'
        ),
        "game_prediction_feeds": [
            {
                "name": row["name"],
                "coverage": f'{row["games_available"]}/{row["production_games"]}',
                "latest_pulled_at": row["latest_pulled_at"],
            }
            for row in payload["game_prediction_feeds"]
        ],
        "output": str(OUT.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
