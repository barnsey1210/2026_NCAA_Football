from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from immutable_tracking import append_unique, stable_id

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data/model_tracking/v2"

RATINGS_HISTORY = ROOT / "data/ratings/ratings_history.csv"
MARKET_HISTORY = ROOT / "data/odds/game_book_line_history.csv"
PROJECTION_CONTRACT = ROOT / "data/site/current_game_projection_contract.json"
PRESEASON_DB = ROOT / "data/snapshots/preseason/preseason_db.json"

HFA = 2.6

MODEL_SOURCES = {
    "SP+": ("sp_plus_spread", "v1"),
    "FPI": ("fpi_spread", "v1"),
    "TeamRankings": ("teamrankings_spread", "v1"),
    "Sagarin Rating": ("sagarin_spread", "v1"),
}

CHECKPOINTS = {
    "W0_SUNDAY_9PM_ET": {
        "week": 0,
        "checkpoint": "SUNDAY_9PM_ET",
        "at": "2026-08-24T01:00:00+00:00",
    },
    "W0_TUESDAY_9PM_ET": {
        "week": 0,
        "checkpoint": "TUESDAY_9PM_ET",
        "at": "2026-08-26T01:00:00+00:00",
    },
    "W1_SUNDAY_9PM_ET": {
        "week": 1,
        "checkpoint": "SUNDAY_9PM_ET",
        "at": "2026-08-31T01:00:00+00:00",
    },
    "W1_TUESDAY_9PM_ET": {
        "week": 1,
        "checkpoint": "TUESDAY_9PM_ET",
        "at": "2026-09-02T01:00:00+00:00",
    },
}


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def number(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def norm(value):
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        str(value or "").lower(),
    ).strip()


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_games():
    contract = json.loads(PROJECTION_CONTRACT.read_text())
    preseason = json.loads(PRESEASON_DB.read_text())

    games = {
        str(g.get("game_id")): dict(g)
        for g in contract.get("games", [])
        if g.get("game_id")
    }

    for g in preseason.get("games", []):
        gid = str(g.get("game_id") or "")
        if not gid:
            continue

        target = games.setdefault(gid, {})

        for key in [
            "game_id",
            "season",
            "week",
            "date",
            "kickoff_at",
            "away_team",
            "home_team",
            "neutral_site",
        ]:
            if target.get(key) in (None, "") and g.get(key) not in (None, ""):
                target[key] = g.get(key)

    return games


def game_date(game):
    value = (
        game.get("date")
        or game.get("kickoff_at")
        or ""
    )
    return str(value)[:10]


def latest_rating_snapshot(rating_rows, source, cutoff):
    eligible = [
        r
        for r in rating_rows
        if r.get("source") == source
        and parse_dt(r.get("pulled_at"))
        and parse_dt(r.get("pulled_at")) <= cutoff
    ]

    if not eligible:
        return None, {}

    latest = max(
        parse_dt(r["pulled_at"])
        for r in eligible
    )

    rows = [
        r
        for r in eligible
        if parse_dt(r.get("pulled_at")) == latest
    ]

    by_team = {
        str(r.get("team")): r
        for r in rows
        if r.get("team")
    }

    return latest, by_team


def market_match(row, game):
    gid = str(game.get("game_id") or "")

    if str(row.get("canonical_game_id") or "") == gid:
        return True

    return (
        str(row.get("date") or "")[:10] == game_date(game)
        and norm(row.get("away_team")) == norm(game.get("away_team"))
        and norm(row.get("home_team")) == norm(game.get("home_team"))
    )


def latest_pinnacle_pair(market_rows, game, cutoff):
    rows = [
        r
        for r in market_rows
        if str(r.get("market") or "").lower() == "spread"
        and "pinnacle" in str(r.get("book") or "").lower()
        and parse_dt(r.get("snapshot_ts"))
        and parse_dt(r.get("snapshot_ts")) <= cutoff
        and market_match(r, game)
    ]

    if not rows:
        return None

    latest = max(
        parse_dt(r["snapshot_ts"])
        for r in rows
    )

    snapshot = [
        r
        for r in rows
        if parse_dt(r.get("snapshot_ts")) == latest
    ]

    by_side = {
        str(r.get("side") or "").lower(): r
        for r in snapshot
    }

    home = by_side.get("home")
    away = by_side.get("away")

    if not home or not away:
        return None

    if number(home.get("line")) is None:
        return None

    if number(away.get("line")) is None:
        return None

    return {
        "snapshot_at": latest,
        "home": home,
        "away": away,
    }


def historical_prediction_row(
    game,
    checkpoint_name,
    checkpoint_at,
    source,
    model_id,
    model_version,
    source_pull,
    away_row,
    home_row,
):
    away_rating = number(away_row.get("rating"))
    home_rating = number(home_row.get("rating"))

    if away_rating is None or home_rating is None:
        return None

    neutral = bool(game.get("neutral_site"))
    hfa = 0.0 if neutral else HFA

    projection = home_rating - away_rating + hfa

    observation_id = stable_id(
        "historical_prediction",
        game["game_id"],
        model_id,
        model_version,
        checkpoint_name,
        source_pull.isoformat(),
        away_rating,
        home_rating,
        hfa,
        projection,
    )

    return {
        "observation_id": observation_id,
        "season": 2026,
        "week": game.get("week"),
        "canonical_game_id": game["game_id"],
        "away_team": game.get("away_team"),
        "home_team": game.get("home_team"),
        "kickoff_at": (
            game.get("kickoff_at")
            or game.get("date")
        ),
        "model_id": model_id,
        "model_version": model_version,
        "market_type": "spread",
        "observed_at": source_pull.isoformat(),
        "model_calculated_at": source_pull.isoformat(),
        "source_updated_at": source_pull.isoformat(),
        "source_snapshot_timestamps": {
            source: source_pull.isoformat(),
        },
        "projection": round(projection, 6),
        "component_values": {
            source: round(projection, 6),
        },
        "component_weights": {
            source: 1.0,
        },
        "component_availability": {
            source: "PRESENT",
        },
        "missing_components": [],
        "lifecycle_state": "HISTORICAL_ARCHIVE_RECONSTRUCTION",
        "source_artifacts": [
            "data/ratings/ratings_history.csv",
        ],
        "contract_id": None,
        "formula_version": model_version,
        "availability_status": "AVAILABLE",
        "provenance_flags": {
            "authority": "HISTORICAL_SOURCE_OBSERVATION",
            "validation_status": "ARCHIVED_PRECHECKPOINT_SOURCE",
            "historical_reconstruction": True,
            "rating_source": source,
            "away_rating": away_rating,
            "home_rating": home_rating,
            "hfa": hfa,
            "neutral_site": neutral,
            "checkpoint": checkpoint_name,
            "checkpoint_at": checkpoint_at.isoformat(),
        },
    }


def historical_market_row(game, raw):
    snapshot_at = parse_dt(raw.get("snapshot_ts"))
    side = str(raw.get("side") or "").lower()
    line = number(raw.get("line"))
    price = number(raw.get("price"))

    observation_id = stable_id(
        "historical_market",
        game["game_id"],
        "spread",
        "Pinnacle",
        side,
        snapshot_at.isoformat(),
        line,
        price,
    )

    return {
        "observation_id": observation_id,
        "canonical_game_id": game["game_id"],
        "market_type": "spread",
        "sportsbook": "Pinnacle",
        "side": side,
        "observed_at": snapshot_at.isoformat(),
        "source_updated_at": (
            raw.get("source_updated_at")
            or raw.get("book_last_updated")
            or raw.get("snapshot_ts")
        ),
        "line": line,
        "price": price,
        "source": (
            raw.get("source")
            or "Historical market archive"
        ),
        "freshness_status": "HISTORICAL_ARCHIVE",
        "lifecycle_state": "HISTORICAL_CHECKPOINT",
        "kickoff_at": (
            game.get("kickoff_at")
            or game.get("date")
        ),
        "contract_id": None,
        "provenance_flags": {
            "historical_reconstruction": True,
            "source_artifact": "data/odds/game_book_line_history.csv",
            "raw_snapshot_ts": raw.get("snapshot_ts"),
            "raw_source_updated_at": raw.get("source_updated_at"),
            "raw_game_key": raw.get("game_key"),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accept", action="store_true")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)

    games = load_games()
    rating_rows = read_csv(RATINGS_HISTORY)
    market_rows = read_csv(MARKET_HISTORY)

    prediction_rows = []
    market_observation_rows = []
    checkpoint_rows = []

    coverage = defaultdict(lambda: {
        "canonical_games": 0,
        "prediction_projectable": 0,
        "pinnacle_available": 0,
        "official_candidates": 0,
    })

    source_snapshot_cache = {}

    for label, spec in CHECKPOINTS.items():
        week = spec["week"]
        checkpoint_name = spec["checkpoint"]
        checkpoint_at = parse_dt(spec["at"])

        week_games = [
            g
            for g in games.values()
            if int(g.get("week")) == week
        ]

        for source, (model_id, model_version) in MODEL_SOURCES.items():
            key = (source, checkpoint_at.isoformat())

            if key not in source_snapshot_cache:
                source_snapshot_cache[key] = latest_rating_snapshot(
                    rating_rows,
                    source,
                    checkpoint_at,
                )

            source_pull, source_teams = source_snapshot_cache[key]

            bucket = coverage[
                f"{label}|{model_id}"
            ]

            bucket["canonical_games"] = len(week_games)

            if source_pull is None:
                continue

            for game in week_games:
                away = source_teams.get(
                    str(game.get("away_team"))
                )
                home = source_teams.get(
                    str(game.get("home_team"))
                )

                if away is None or home is None:
                    continue

                prediction = historical_prediction_row(
                    game,
                    checkpoint_name,
                    checkpoint_at,
                    source,
                    model_id,
                    model_version,
                    source_pull,
                    away,
                    home,
                )

                if prediction is None:
                    continue

                bucket["prediction_projectable"] += 1

                market_pair = latest_pinnacle_pair(
                    market_rows,
                    game,
                    checkpoint_at,
                )

                if market_pair is None:
                    continue

                bucket["pinnacle_available"] += 1

                home_market = historical_market_row(
                    game,
                    market_pair["home"],
                )
                away_market = historical_market_row(
                    game,
                    market_pair["away"],
                )

                home_line = float(home_market["line"])
                projection_value = float(
                    prediction["projection"]
                )

                side = (
                    "home"
                    if projection_value + home_line >= 0
                    else "away"
                )

                chosen_market = (
                    home_market
                    if side == "home"
                    else away_market
                )

                edge = abs(
                    projection_value
                    + float(chosen_market["line"])
                )

                checkpoint_id = stable_id(
                    "official_checkpoint",
                    game["game_id"],
                    model_id,
                    model_version,
                    "spread",
                    checkpoint_name,
                )

                checkpoint_rows.append({
                    "checkpoint_id": checkpoint_id,
                    "canonical_game_id": game["game_id"],
                    "season": 2026,
                    "week": game.get("week"),
                    "away_team": game.get("away_team"),
                    "home_team": game.get("home_team"),
                    "kickoff_at": (
                        game.get("kickoff_at")
                        or game.get("date")
                    ),
                    "model_id": model_id,
                    "model_version": model_version,
                    "market_type": "spread",
                    "checkpoint": checkpoint_name,
                    "checkpoint_at": checkpoint_at.isoformat(),
                    "prediction_observation_id": prediction["observation_id"],
                    "prediction": prediction["projection"],
                    "prediction_observed_at": prediction["observed_at"],
                    "prediction_source_updated_at": prediction[
                        "source_updated_at"
                    ],
                    "prediction_age_hours": round(
                        (
                            checkpoint_at
                            - parse_dt(prediction["observed_at"])
                        ).total_seconds() / 3600,
                        3,
                    ),
                    "market_observation_id": chosen_market[
                        "observation_id"
                    ],
                    "market_line": chosen_market["line"],
                    "market_price": chosen_market["price"],
                    "market_book": "Pinnacle",
                    "market_source": chosen_market["source"],
                    "market_observed_at": chosen_market["observed_at"],
                    "market_source_updated_at": chosen_market[
                        "source_updated_at"
                    ],
                    "market_age_hours": round(
                        (
                            checkpoint_at
                            - parse_dt(chosen_market["observed_at"])
                        ).total_seconds() / 3600,
                        3,
                    ),
                    "market_benchmark": "PINNACLE",
                    "bet_side": side,
                    "edge": round(edge, 6),
                    "decision_id": None,
                    "selection_status": "OFFICIAL",
                    "selection_origin": (
                        "HISTORICAL_ARCHIVE_RECONSTRUCTION"
                    ),
                    "prediction_archive": (
                        "data/ratings/ratings_history.csv"
                    ),
                    "market_archive": (
                        "data/odds/game_book_line_history.csv"
                    ),
                    "created_at": now.isoformat(),
                })

                prediction_rows.append(prediction)
                market_observation_rows.extend([
                    home_market,
                    away_market,
                ])

                bucket["official_candidates"] += 1

    prediction_rows = list({
        row["observation_id"]: row
        for row in prediction_rows
    }.values())

    market_observation_rows = list({
        row["observation_id"]: row
        for row in market_observation_rows
    }.values())

    checkpoint_rows = list({
        row["checkpoint_id"]: row
        for row in checkpoint_rows
    }.values())

    report = {
        "schema_version": (
            "historical-checkpoint-reconstruction-preview-v1"
        ),
        "generated_at": now.isoformat(),
        "accept_requested": args.accept,
        "season": 2026,
        "weeks": [0, 1],
        "markets": ["spread"],
        "models": list(MODEL_SOURCES.values()),
        "checkpoint_policy": [
            "SUNDAY_9PM_ET",
            "TUESDAY_9PM_ET",
        ],
        "prediction_policy": (
            "latest archived source pull at or before checkpoint; "
            "home rating minus away rating plus 2.6 HFA unless neutral"
        ),
        "market_policy": (
            "latest archived Pinnacle spread pair at or before checkpoint"
        ),
        "standard_spread_backfill": (
            "DEFERRED_UNTIL_HISTORICAL_MODEL_VERSION_AUTHORITY_IS_PROVEN"
        ),
        "coverage": dict(coverage),
        "predictions": append_unique(
            D / "prediction_observations.jsonl",
            prediction_rows,
            "observation_id",
            args.accept,
        ),
        "markets": append_unique(
            D / "market_observations.jsonl",
            market_observation_rows,
            "observation_id",
            args.accept,
        ),
        "checkpoints": append_unique(
            D / "checkpoint_observations.jsonl",
            checkpoint_rows,
            "checkpoint_id",
            args.accept,
        ),
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
