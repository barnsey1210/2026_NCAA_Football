#!/usr/bin/env python3
"""Capture prospective immutable CLOSE checkpoints from canonical FROZEN_CLOSE."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from immutable_tracking import append_unique, stable_id

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data/model_tracking/v2"
MARKET_CONTRACT = ROOT / "data/site/current_market_contract.json"

CLOSE_AUTOMATION_START = datetime(
    2026, 9, 5, 0, 0, tzinfo=timezone.utc
)


def load_jsonl(name):
    path = D / name
    if not path.exists():
        return []

    return [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def parse_dt(value):
    if not value:
        return None

    try:
        value = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def canonical(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def latest_before(rows, cutoff):
    eligible = []

    for row in rows:
        observed = parse_dt(row.get("observed_at"))

        if observed is not None and observed <= cutoff:
            eligible.append((observed, row))

    if not eligible:
        return None

    return max(eligible, key=lambda item: item[0])[1]


def frozen_quote(reference_market, side):
    quote = reference_market.get(side) or {}

    if quote.get("line") is None:
        return None

    if (
        str(quote.get("freshness_status") or "").upper()
        != "FROZEN_CLOSE"
    ):
        return None

    try:
        line = float(quote["line"])
    except (TypeError, ValueError):
        return None

    return quote, line


def close_timestamp(quote, kickoff):
    source_updated = parse_dt(quote.get("source_updated_at"))

    if source_updated is not None:
        return source_updated

    return kickoff


def market_observation(
    game_id,
    market_type,
    sportsbook,
    side,
    quote,
    close_at,
    contract_id,
):
    state = [
        quote.get("source_updated_at"),
        quote.get("line"),
        quote.get("price"),
        quote.get("freshness_status"),
        quote.get("market_lifecycle_state"),
    ]

    observation_id = stable_id(
        "market",
        game_id,
        market_type,
        sportsbook,
        side,
        canonical(state),
    )

    return {
        "observation_id": observation_id,
        "canonical_game_id": game_id,
        "market_type": market_type,
        "sportsbook": sportsbook,
        "side": side,
        "observed_at": close_at.isoformat(),
        "source_updated_at": quote.get("source_updated_at"),
        "line": quote.get("line"),
        "price": quote.get("price"),
        "source": quote.get("source"),
        "freshness_status": quote.get("freshness_status"),
        "lifecycle_state": quote.get("market_lifecycle_state"),
        "kickoff_at": quote.get("kickoff_at"),
        "contract_id": contract_id,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--accept", action="store_true")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)

    market_payload = json.loads(MARKET_CONTRACT.read_text())

    predictions = load_jsonl("prediction_observations.jsonl")
    existing_checkpoints = load_jsonl(
        "checkpoint_observations.jsonl"
    )

    predictions_by_game = defaultdict(list)

    for row in predictions:
        game_id = str(row.get("canonical_game_id") or "")

        if game_id:
            predictions_by_game[game_id].append(row)

    existing_close_keys = {
        (
            str(row.get("canonical_game_id") or ""),
            row.get("model_id"),
            row.get("model_version"),
            row.get("market_type"),
        )
        for row in existing_checkpoints
        if row.get("checkpoint") == "CLOSE"
        and row.get("selection_status") == "OFFICIAL"
    }

    market_rows = []
    checkpoint_rows = []
    skipped = defaultdict(int)

    games_seen = 0
    frozen_games = 0

    for game in market_payload.get("games", []):
        game_id = str(game.get("game_id") or "")

        if not game_id:
            continue

        games_seen += 1

        game_predictions = predictions_by_game.get(game_id, [])

        if not game_predictions:
            skipped["missing_prediction_history"] += 1
            continue

        kickoff_values = [
            parse_dt(row.get("kickoff_at"))
            for row in game_predictions
            if row.get("kickoff_at")
        ]

        kickoff_values = [
            value
            for value in kickoff_values
            if value is not None
        ]

        if not kickoff_values:
            skipped["missing_kickoff"] += 1
            continue

        kickoff = min(kickoff_values)

        if kickoff < CLOSE_AUTOMATION_START:
            skipped["before_close_automation_start"] += 1
            continue

        reference = game.get("reference") or {}

        frozen_market_types = []

        for market_type, base_side in (
            ("spread", "home"),
            ("total", "over"),
        ):
            reference_market = reference.get(market_type) or {}

            base = frozen_quote(reference_market, base_side)

            if base is not None:
                frozen_market_types.append(market_type)

        if not frozen_market_types:
            skipped["no_frozen_close"] += 1
            continue

        frozen_games += 1

        identities = {
            (
                row.get("model_id"),
                row.get("model_version"),
                row.get("market_type"),
            )
            for row in game_predictions
            if row.get("model_id")
            and row.get("market_type") in {"spread", "total"}
            and row.get("projection") is not None
        }

        for model_id, model_version, market_type in identities:
            if market_type not in frozen_market_types:
                continue

            close_key = (
                game_id,
                model_id,
                model_version,
                market_type,
            )

            if close_key in existing_close_keys:
                skipped["close_already_exists"] += 1
                continue

            reference_market = reference.get(market_type) or {}

            base_side = (
                "home"
                if market_type == "spread"
                else "over"
            )

            base_result = frozen_quote(
                reference_market,
                base_side,
            )

            if base_result is None:
                skipped["missing_frozen_base_quote"] += 1
                continue

            base_quote, base_line = base_result

            close_at = close_timestamp(
                base_quote,
                kickoff,
            )

            prediction_cutoff = min(kickoff, close_at)

            model_rows = [
                row
                for row in game_predictions
                if row.get("model_id") == model_id
                and row.get("model_version") == model_version
                and row.get("market_type") == market_type
                and row.get("projection") is not None
            ]

            prediction = latest_before(
                model_rows,
                prediction_cutoff,
            )

            if prediction is None:
                skipped[
                    "missing_prediction_before_close"
                ] += 1
                continue

            projection = float(prediction["projection"])

            if market_type == "spread":
                side = (
                    "home"
                    if projection + base_line >= 0
                    else "away"
                )
            else:
                side = (
                    "over"
                    if projection - base_line >= 0
                    else "under"
                )

            selected_result = frozen_quote(
                reference_market,
                side,
            )

            if selected_result is None:
                skipped[
                    "missing_selected_frozen_quote"
                ] += 1
                continue

            selected_quote, selected_line = selected_result

            sportsbook = (
                selected_quote.get("sportsbook")
                or reference_market.get("sportsbook")
            )

            if not sportsbook:
                skipped["missing_close_sportsbook"] += 1
                continue

            selected_close_at = close_timestamp(
                selected_quote,
                kickoff,
            )

            market_row = market_observation(
                game_id,
                market_type,
                sportsbook,
                side,
                selected_quote,
                selected_close_at,
                market_payload.get("built_at"),
            )

            market_rows.append(market_row)

            if market_type == "spread":
                edge = abs(
                    projection + base_line
                )
            else:
                edge = abs(
                    projection - base_line
                )

            prediction_observed = parse_dt(
                prediction.get("observed_at")
            )

            prediction_age_hours = None

            if prediction_observed is not None:
                prediction_age_hours = round(
                    (
                        prediction_cutoff
                        - prediction_observed
                    ).total_seconds()
                    / 3600,
                    3,
                )

            checkpoint_id = stable_id(
                "official_checkpoint",
                game_id,
                model_id,
                model_version,
                market_type,
                "CLOSE",
            )

            checkpoint_rows.append({
                "checkpoint_id": checkpoint_id,
                "canonical_game_id": game_id,
                "season": prediction.get("season"),
                "week": prediction.get("week"),
                "away_team": prediction.get("away_team"),
                "home_team": prediction.get("home_team"),
                "kickoff_at": prediction.get("kickoff_at"),
                "model_id": model_id,
                "model_version": model_version,
                "market_type": market_type,
                "checkpoint": "CLOSE",
                "checkpoint_at": selected_close_at.isoformat(),
                "prediction_observation_id": (
                    prediction["observation_id"]
                ),
                "prediction": prediction.get("projection"),
                "prediction_observed_at": (
                    prediction.get("observed_at")
                ),
                "prediction_source_updated_at": (
                    prediction.get("source_updated_at")
                ),
                "prediction_age_hours": (
                    prediction_age_hours
                ),
                "market_observation_id": (
                    market_row["observation_id"]
                ),
                "market_line": selected_line,
                "market_price": (
                    selected_quote.get("price")
                ),
                "market_book": sportsbook,
                "market_source": (
                    selected_quote.get("source")
                ),
                "market_observed_at": (
                    selected_close_at.isoformat()
                ),
                "market_source_updated_at": (
                    selected_quote.get("source_updated_at")
                ),
                "market_age_hours": 0.0,
                "market_benchmark": (
                    "CANONICAL_FROZEN_CLOSE"
                ),
                "bet_side": side,
                "edge": edge,
                "decision_id": None,
                "selection_status": "OFFICIAL",
                "created_at": now.isoformat(),
                "capture_policy": (
                    "PROSPECTIVE_FROZEN_CLOSE_V1"
                ),
            })

    report = {
        "schema_version": (
            "official-close-checkpoint-capture-v1"
        ),
        "generated_at": now.isoformat(),
        "accept_requested": args.accept,
        "automation_start": (
            CLOSE_AUTOMATION_START.isoformat()
        ),
        "policy": {
            "trigger": (
                "canonical reference quote "
                "freshness_status == FROZEN_CLOSE"
            ),
            "prediction": (
                "latest accepted immutable prediction "
                "at or before min(kickoff, close timestamp)"
            ),
            "market": (
                "canonical FROZEN_CLOSE reference quote"
            ),
            "immutability": (
                "one CLOSE row per "
                "game/model/version/market"
            ),
            "historical_backfill": False,
        },
        "games_seen": games_seen,
        "frozen_games": frozen_games,
        "skipped": dict(skipped),
        "markets": append_unique(
            D / "market_observations.jsonl",
            market_rows,
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
