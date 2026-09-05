#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from immutable_tracking import append_unique, stable_id

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data/model_tracking/v2"

RATINGS = ROOT / "data/ratings/ratings_history.csv"
PROJECTIONS = ROOT / "data/site/current_game_projection_contract.json"
MARKETS = ROOT / "data/site/current_market_contract.json"

HFA = 2.6

MODELS = {
    "SP+": ("sp_plus_spread", "v1"),
    "FPI": ("fpi_spread", "v1"),
    "TeamRankings": ("teamrankings_spread", "v1"),
    "Sagarin Rating": ("sagarin_spread", "v1"),
}


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_csv(path):
    with path.open(
        newline="",
        encoding="utf-8-sig",
    ) as handle:
        return list(csv.DictReader(handle))


def latest_source_snapshot(rows, source, cutoff):
    eligible = [
        row
        for row in rows
        if row.get("source") == source
        and parse_dt(row.get("pulled_at"))
        and parse_dt(row.get("pulled_at")) < cutoff
    ]

    if not eligible:
        return None, {}

    latest = max(
        parse_dt(row["pulled_at"])
        for row in eligible
    )

    snapshot = [
        row
        for row in eligible
        if parse_dt(row.get("pulled_at")) == latest
    ]

    return latest, {
        row.get("team"): row
        for row in snapshot
        if row.get("team")
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accept", action="store_true")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)

    rating_rows = read_csv(RATINGS)

    projection_payload = json.loads(
        PROJECTIONS.read_text()
    )
    market_payload = json.loads(
        MARKETS.read_text()
    )

    projection_games = {
        str(game["game_id"]): game
        for game in projection_payload.get("games", [])
        if game.get("game_id")
    }

    market_games = {
        str(game["game_id"]): game
        for game in market_payload.get("games", [])
        if game.get("game_id")
    }

    predictions = []
    markets = []
    checkpoints = []

    coverage = {}

    for source, (model_id, version) in MODELS.items():
        coverage[model_id] = {
            "eligible_games": 0,
            "rating_available": 0,
            "frozen_close_available": 0,
            "official_candidates": 0,
        }

    for game_id, market_game in market_games.items():
        week = market_game.get("week")

        if week not in {0, 1}:
            continue

        kickoff = parse_dt(
            market_game.get("kickoff_at")
        )

        if kickoff is None:
            continue

        projection_game = projection_games.get(
            game_id,
            {}
        )

        neutral = bool(
            projection_game.get("neutral_site")
        )

        away_team = (
            projection_game.get("away_team")
            or market_game.get("away_team")
        )
        home_team = (
            projection_game.get("home_team")
            or market_game.get("home_team")
        )

        reference = market_game.get("reference") or {}
        spread = reference.get("spread") or {}

        home_close = spread.get("home") or {}
        away_close = spread.get("away") or {}

        frozen_ok = (
            home_close.get("line") is not None
            and away_close.get("line") is not None
            and str(
                home_close.get("freshness_status") or ""
            ).upper() == "FROZEN_CLOSE"
            and str(
                away_close.get("freshness_status") or ""
            ).upper() == "FROZEN_CLOSE"
        )

        for source, (model_id, version) in MODELS.items():
            bucket = coverage[model_id]
            bucket["eligible_games"] += 1

            source_pull, teams = latest_source_snapshot(
                rating_rows,
                source,
                kickoff,
            )

            if source_pull is None:
                continue

            away = teams.get(away_team)
            home = teams.get(home_team)

            if away is None or home is None:
                continue

            away_rating = number(away.get("rating"))
            home_rating = number(home.get("rating"))

            if away_rating is None or home_rating is None:
                continue

            bucket["rating_available"] += 1

            if not frozen_ok:
                continue

            bucket["frozen_close_available"] += 1

            hfa = 0.0 if neutral else HFA
            projection = (
                home_rating
                - away_rating
                + hfa
            )

            prediction_id = stable_id(
                "historical_close_prediction",
                game_id,
                model_id,
                version,
                source_pull.isoformat(),
                away_rating,
                home_rating,
                hfa,
                projection,
            )

            prediction = {
                "observation_id": prediction_id,
                "season": 2026,
                "week": week,
                "canonical_game_id": game_id,
                "away_team": away_team,
                "home_team": home_team,
                "kickoff_at": kickoff.isoformat(),
                "model_id": model_id,
                "model_version": version,
                "market_type": "spread",
                "observed_at": source_pull.isoformat(),
                "model_calculated_at": source_pull.isoformat(),
                "source_updated_at": source_pull.isoformat(),
                "source_snapshot_timestamps": {
                    source: source_pull.isoformat()
                },
                "projection": round(
                    projection,
                    6,
                ),
                "component_values": {
                    source: round(
                        projection,
                        6,
                    )
                },
                "component_weights": {
                    source: 1.0
                },
                "component_availability": {
                    source: "PRESENT"
                },
                "missing_components": [],
                "lifecycle_state": (
                    "HISTORICAL_CLOSE_RECONSTRUCTION"
                ),
                "source_artifacts": [
                    "data/ratings/ratings_history.csv"
                ],
                "contract_id": None,
                "formula_version": version,
                "availability_status": "AVAILABLE",
                "provenance_flags": {
                    "historical_reconstruction": True,
                    "rating_source": source,
                    "away_rating": away_rating,
                    "home_rating": home_rating,
                    "hfa": hfa,
                    "neutral_site": neutral,
                    "cutoff_policy": (
                        "strictly_before_kickoff"
                    ),
                },
            }

            market_rows = {}

            for side, quote in [
                ("home", home_close),
                ("away", away_close),
            ]:
                market_id = stable_id(
                    "historical_close_market",
                    game_id,
                    "spread",
                    side,
                    quote.get("sportsbook"),
                    quote.get("line"),
                    quote.get("price"),
                    quote.get("source_updated_at"),
                    "FROZEN_CLOSE",
                )

                market_row = {
                    "observation_id": market_id,
                    "canonical_game_id": game_id,
                    "market_type": "spread",
                    "sportsbook": (
                        quote.get("sportsbook")
                        or spread.get("sportsbook")
                    ),
                    "side": side,
                    "observed_at": (
                        quote.get("source_updated_at")
                        or kickoff.isoformat()
                    ),
                    "source_updated_at": (
                        quote.get("source_updated_at")
                    ),
                    "line": float(
                        quote["line"]
                    ),
                    "price": quote.get("price"),
                    "source": quote.get("source"),
                    "freshness_status": "FROZEN_CLOSE",
                    "lifecycle_state": (
                        quote.get(
                            "market_lifecycle_state"
                        )
                    ),
                    "kickoff_at": kickoff.isoformat(),
                    "contract_id": market_payload.get(
                        "built_at"
                    ),
                    "provenance_flags": {
                        "historical_reconstruction": True,
                        "close_authority": (
                            "CURRENT_MARKET_CONTRACT_"
                            "FROZEN_CLOSE"
                        ),
                    },
                }

                market_rows[side] = market_row
                markets.append(market_row)

            home_line = float(
                market_rows["home"]["line"]
            )

            side = (
                "home"
                if projection + home_line >= 0
                else "away"
            )

            chosen_market = market_rows[side]

            edge = abs(
                projection
                + float(chosen_market["line"])
            )

            checkpoint_id = stable_id(
                "official_checkpoint",
                game_id,
                model_id,
                version,
                "spread",
                "CLOSE",
            )

            checkpoints.append({
                "checkpoint_id": checkpoint_id,
                "canonical_game_id": game_id,
                "season": 2026,
                "week": week,
                "away_team": away_team,
                "home_team": home_team,
                "kickoff_at": kickoff.isoformat(),
                "model_id": model_id,
                "model_version": version,
                "market_type": "spread",
                "checkpoint": "CLOSE",
                "checkpoint_at": kickoff.isoformat(),
                "prediction_observation_id": prediction_id,
                "prediction": round(
                    projection,
                    6,
                ),
                "prediction_observed_at": (
                    source_pull.isoformat()
                ),
                "prediction_source_updated_at": (
                    source_pull.isoformat()
                ),
                "prediction_age_hours": round(
                    (
                        kickoff - source_pull
                    ).total_seconds() / 3600,
                    3,
                ),
                "market_observation_id": (
                    chosen_market["observation_id"]
                ),
                "market_line": (
                    chosen_market["line"]
                ),
                "market_price": (
                    chosen_market["price"]
                ),
                "market_book": (
                    chosen_market["sportsbook"]
                ),
                "market_source": (
                    chosen_market["source"]
                ),
                "market_observed_at": (
                    chosen_market["observed_at"]
                ),
                "market_source_updated_at": (
                    chosen_market[
                        "source_updated_at"
                    ]
                ),
                "market_age_hours": None,
                "market_benchmark": (
                    "FROZEN_CLOSE"
                ),
                "bet_side": side,
                "edge": round(
                    edge,
                    6,
                ),
                "decision_id": None,
                "selection_status": "OFFICIAL",
                "selection_origin": (
                    "HISTORICAL_CLOSE_"
                    "RECONSTRUCTION"
                ),
                "created_at": now.isoformat(),
            })

            predictions.append(prediction)
            bucket["official_candidates"] += 1

    predictions = list({
        row["observation_id"]: row
        for row in predictions
    }.values())

    markets = list({
        row["observation_id"]: row
        for row in markets
    }.values())

    checkpoints = list({
        row["checkpoint_id"]: row
        for row in checkpoints
    }.values())

    report = {
        "schema_version": (
            "historical-close-reconstruction-v1"
        ),
        "generated_at": now.isoformat(),
        "accept_requested": args.accept,
        "weeks": [0, 1],
        "checkpoint": "CLOSE",
        "market_type": "spread",
        "models": [
            model_id
            for model_id, _ in MODELS.values()
        ],
        "projection_policy": (
            "latest archived rating source pull "
            "strictly before kickoff"
        ),
        "hfa_policy": (
            "2.6 non-neutral, 0 neutral using "
            "projection contract neutral_site"
        ),
        "close_authority": (
            "current_market_contract FROZEN_CLOSE"
        ),
        "coverage": coverage,
        "predictions": append_unique(
            D / "prediction_observations.jsonl",
            predictions,
            "observation_id",
            args.accept,
        ),
        "markets": append_unique(
            D / "market_observations.jsonl",
            markets,
            "observation_id",
            args.accept,
        ),
        "checkpoints": append_unique(
            D / "checkpoint_observations.jsonl",
            checkpoints,
            "checkpoint_id",
            args.accept,
        ),
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
