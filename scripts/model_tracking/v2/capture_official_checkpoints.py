#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from immutable_tracking import append_unique, stable_id

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data/model_tracking/v2"
ET = ZoneInfo("America/New_York")

CHECKPOINTS = (
    ("SUNDAY_9PM_ET", 0),
    ("TUESDAY_9PM_ET", 2),
)


def load_jsonl(name):
    p = D / name
    if not p.exists():
        return []
    return [
        json.loads(line)
        for line in p.read_text().splitlines()
        if line.strip()
    ]


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None


def game_checkpoints(kickoff_value):
    kickoff = parse_dt(kickoff_value)
    if kickoff is None:
        return {}

    kickoff_et = kickoff.astimezone(ET)
    days_since_sunday = (kickoff_et.weekday() + 1) % 7
    sunday_date = (
        kickoff_et - timedelta(days=days_since_sunday)
    ).date()

    sunday = datetime.combine(
        sunday_date,
        time(21, 0),
        tzinfo=ET,
    )

    if sunday >= kickoff_et:
        sunday -= timedelta(days=7)

    values = {}

    for name, offset in CHECKPOINTS:
        checkpoint = sunday + timedelta(days=offset)
        if checkpoint < kickoff_et:
            values[name] = checkpoint.astimezone(timezone.utc)

    return values


def latest_before(rows, cutoff, timestamp_field):
    eligible = []

    for row in rows:
        stamp = parse_dt(row.get(timestamp_field))
        if stamp is not None and stamp <= cutoff:
            eligible.append((stamp, row))

    if not eligible:
        return None

    return max(eligible, key=lambda x: x[0])[1]


def choose_pinnacle_market(
    market_rows,
    prediction,
    market_type,
    cutoff,
):
    books = defaultdict(list)

    for row in market_rows:
        if row.get("market_type") != market_type:
            continue

        stamp = parse_dt(row.get("observed_at"))
        if stamp is None or stamp > cutoff:
            continue

        book = str(row.get("sportsbook") or "")
        if "pinnacle" not in book.lower():
            continue

        books[book].append(row)

    for book in sorted(books):
        rows = books[book]

        base_side = "home" if market_type == "spread" else "over"
        base = latest_before(
            [r for r in rows if r.get("side") == base_side],
            cutoff,
            "observed_at",
        )

        if not base or base.get("line") is None:
            continue

        line = float(base["line"])

        if market_type == "spread":
            side = (
                "home"
                if float(prediction) + line >= 0
                else "away"
            )
        else:
            side = (
                "over"
                if float(prediction) - line >= 0
                else "under"
            )

        chosen = latest_before(
            [r for r in rows if r.get("side") == side],
            cutoff,
            "observed_at",
        )

        if chosen and chosen.get("line") is not None:
            return chosen, "PINNACLE"

    return None, None


def choose_reference_fallback(
    decisions,
    markets_by_id,
    prediction_id,
    cutoff,
):
    candidates = []

    for row in decisions:
        if row.get("prediction_observation_id") != prediction_id:
            continue

        stamp = parse_dt(row.get("created_at"))
        if stamp is None or stamp > cutoff:
            continue

        market = markets_by_id.get(row.get("market_observation_id"))
        if not market or market.get("line") is None:
            continue

        candidates.append((stamp, row, market))

    if not candidates:
        return None, None, None

    _, decision, market = max(
        candidates,
        key=lambda x: x[0],
    )

    return market, decision, "CANONICAL_REFERENCE_FALLBACK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accept", action="store_true")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)

    predictions = load_jsonl("prediction_observations.jsonl")
    markets = load_jsonl("market_observations.jsonl")
    decisions = load_jsonl("decision_observations.jsonl")

    markets_by_id = {
        row["observation_id"]: row
        for row in markets
    }

    predictions_by_game = defaultdict(list)
    markets_by_game = defaultdict(list)

    for row in predictions:
        predictions_by_game[row.get("canonical_game_id")].append(row)

    for row in markets:
        markets_by_game[row.get("canonical_game_id")].append(row)

    checkpoint_rows = []
    skipped = defaultdict(int)

    for game_id, game_predictions in predictions_by_game.items():
        kickoff_values = [
            row.get("kickoff_at")
            for row in game_predictions
            if row.get("kickoff_at")
        ]

        if not kickoff_values:
            skipped["missing_kickoff"] += 1
            continue

        kickoff = min(
            (
                parse_dt(value)
                for value in kickoff_values
                if parse_dt(value)
            ),
            default=None,
        )

        if kickoff is None:
            skipped["invalid_kickoff"] += 1
            continue

        checkpoints = game_checkpoints(kickoff.isoformat())

        for checkpoint_name, checkpoint_at in checkpoints.items():
            if now < checkpoint_at:
                continue

            identities = {
                (
                    row.get("model_id"),
                    row.get("model_version"),
                    row.get("market_type"),
                )
                for row in game_predictions
                if row.get("model_id")
                and row.get("market_type") in {"spread", "total"}
            }

            for model_id, model_version, market_type in identities:
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
                    checkpoint_at,
                    "observed_at",
                )

                if prediction is None:
                    skipped["missing_prediction_before_checkpoint"] += 1
                    continue

                market, benchmark = choose_pinnacle_market(
                    markets_by_game.get(game_id, []),
                    prediction["projection"],
                    market_type,
                    checkpoint_at,
                )

                decision = None

                if market is None:
                    market, decision, benchmark = choose_reference_fallback(
                        decisions,
                        markets_by_id,
                        prediction["observation_id"],
                        checkpoint_at,
                    )

                if market is None:
                    skipped["missing_market_before_checkpoint"] += 1
                    continue

                if decision is not None:
                    side = decision.get("bet_side")
                    edge = decision.get("edge")
                else:
                    line = float(market["line"])

                    if market_type == "spread":
                        side = (
                            "home"
                            if float(prediction["projection"]) + line >= 0
                            else "away"
                        )
                        edge = abs(
                            float(prediction["projection"]) + line
                        )
                    else:
                        side = (
                            "over"
                            if float(prediction["projection"]) - line >= 0
                            else "under"
                        )
                        edge = abs(
                            float(prediction["projection"]) - line
                        )

                prediction_observed = parse_dt(
                    prediction.get("observed_at")
                )
                market_observed = parse_dt(
                    market.get("observed_at")
                )

                checkpoint_id = stable_id(
                    "official_checkpoint",
                    game_id,
                    model_id,
                    model_version,
                    market_type,
                    checkpoint_name,
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
                    "checkpoint": checkpoint_name,
                    "checkpoint_at": checkpoint_at.isoformat(),
                    "prediction_observation_id": prediction["observation_id"],
                    "prediction": prediction.get("projection"),
                    "prediction_observed_at": prediction.get("observed_at"),
                    "prediction_source_updated_at": prediction.get(
                        "source_updated_at"
                    ),
                    "prediction_age_hours": round(
                        (
                            checkpoint_at - prediction_observed
                        ).total_seconds() / 3600,
                        3,
                    ),
                    "market_observation_id": market["observation_id"],
                    "market_line": market.get("line"),
                    "market_price": market.get("price"),
                    "market_book": market.get("sportsbook"),
                    "market_source": market.get("source"),
                    "market_observed_at": market.get("observed_at"),
                    "market_source_updated_at": market.get(
                        "source_updated_at"
                    ),
                    "market_age_hours": round(
                        (
                            checkpoint_at - market_observed
                        ).total_seconds() / 3600,
                        3,
                    ),
                    "market_benchmark": benchmark,
                    "bet_side": side,
                    "edge": edge,
                    "decision_id": (
                        decision.get("decision_id")
                        if decision
                        else None
                    ),
                    "selection_status": "OFFICIAL",
                    "created_at": now.isoformat(),
                })

    report = {
        "schema_version": "official-checkpoint-capture-v1",
        "generated_at": now.isoformat(),
        "accept_requested": args.accept,
        "checkpoint_policy": [
            "SUNDAY_9PM_ET",
            "TUESDAY_9PM_ET",
        ],
        "selection_policy": {
            "prediction": "latest raw accepted observation at or before checkpoint",
            "market_primary": "latest Pinnacle observation at or before checkpoint",
            "market_fallback": "canonical reference decision at or before checkpoint",
            "immutability": "one row per game/model/version/market/checkpoint",
        },
        "skipped": dict(skipped),
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
