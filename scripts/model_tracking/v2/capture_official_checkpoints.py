#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from immutable_tracking import append_unique, stable_id
from normalized_checkpoint_reader import (
    build_normalized_context,
    choose_reference_fallback as choose_normalized_reference_fallback,
    semantic_market,
)

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
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


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
    ap.add_argument(
        "--normalized-shadow",
        action="store_true",
    )
    ap.add_argument(
        "--require-normalized-parity",
        action="store_true",
    )
    ap.add_argument(
        "--normalized-authority",
        action="store_true",
        help=(
            "Use normalized Sunday/Tuesday checkpoint selection "
            "while preserving legacy downstream reference IDs."
        ),
    )
    args = ap.parse_args()

    if args.normalized_authority:
        args.normalized_shadow = True

    if (
        args.require_normalized_parity
        and not args.normalized_shadow
    ):
        ap.error(
            "--require-normalized-parity requires "
            "--normalized-shadow"
        )

    now = datetime.now(timezone.utc)

    predictions = load_jsonl("prediction_observations.jsonl")
    markets = load_jsonl("market_observations.jsonl")
    decisions = load_jsonl("decision_observations.jsonl")

    normalized = (
        build_normalized_context(D)
        if args.normalized_shadow
        else None
    )

    normalized_shadow = {
        "enabled": bool(args.normalized_shadow),
        "compared": 0,
        "mismatches": 0,
        "missing_normalized_market": 0,
        "superseded_market_confirmations": (
            normalized["superseded_market_confirmations"]
            if normalized
            else 0
        ),
        "unresolved_market_states": (
            normalized["unresolved_market_states"]
            if normalized
            else 0
        ),
        "first_mismatches": [],
    }

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

                if args.normalized_shadow:
                    (
                        normalized_market,
                        normalized_benchmark,
                    ) = choose_pinnacle_market(
                        normalized["markets_by_game"].get(
                            game_id,
                            [],
                        ),
                        prediction["projection"],
                        market_type,
                        checkpoint_at,
                    )

                    normalized_decision = None

                    if normalized_market is None:
                        (
                            normalized_market,
                            normalized_decision,
                            normalized_benchmark,
                        ) = choose_normalized_reference_fallback(
                            normalized,
                            prediction["observation_id"],
                            checkpoint_at,
                        )

                    normalized_shadow["compared"] += 1

                    if normalized_market is None:
                        normalized_side = None
                        normalized_edge = None
                        normalized_shadow[
                            "missing_normalized_market"
                        ] += 1
                        mismatch = True

                    else:
                        if normalized_decision is not None:
                            normalized_side = (
                                normalized_decision.get(
                                    "bet_side"
                                )
                            )
                            normalized_edge = (
                                normalized_decision.get(
                                    "edge"
                                )
                            )

                        else:
                            normalized_line = float(
                                normalized_market["line"]
                            )

                            if market_type == "spread":
                                normalized_side = (
                                    "home"
                                    if float(
                                        prediction["projection"]
                                    ) + normalized_line >= 0
                                    else "away"
                                )
                                normalized_edge = abs(
                                    float(
                                        prediction["projection"]
                                    ) + normalized_line
                                )

                            else:
                                normalized_side = (
                                    "over"
                                    if float(
                                        prediction["projection"]
                                    ) - normalized_line >= 0
                                    else "under"
                                )
                                normalized_edge = abs(
                                    float(
                                        prediction["projection"]
                                    ) - normalized_line
                                )

                        mismatch = not (
                            semantic_market(market)
                            == semantic_market(normalized_market)
                            and benchmark == normalized_benchmark
                            and side == normalized_side
                            and edge == normalized_edge
                        )

                    if mismatch:
                        normalized_shadow["mismatches"] += 1

                        if len(
                            normalized_shadow["first_mismatches"]
                        ) < 10:
                            normalized_shadow[
                                "first_mismatches"
                            ].append({
                                "game_id": game_id,
                                "checkpoint": checkpoint_name,
                                "model_id": model_id,
                                "model_version": model_version,
                                "market_type": market_type,
                                "legacy_market":
                                    semantic_market(market),
                                "normalized_market":
                                    semantic_market(
                                        normalized_market
                                    ),
                                "legacy_benchmark":
                                    benchmark,
                                "normalized_benchmark":
                                    normalized_benchmark,
                                "legacy_side": side,
                                "normalized_side":
                                    normalized_side,
                                "legacy_edge": edge,
                                "normalized_edge":
                                    normalized_edge,
                            })

                if args.normalized_authority:
                    if normalized_market is None:
                        raise RuntimeError(
                            "normalized authority missing market "
                            f"{game_id} {checkpoint_name} "
                            f"{model_id} {market_type}"
                        )

                    compatibility_market_id = (
                        normalized_market.get(
                            "legacy_market_observation_id"
                        )
                    )

                    if not compatibility_market_id:
                        raise RuntimeError(
                            "normalized authority market lacks "
                            "legacy compatibility observation id"
                        )

                    market = dict(normalized_market)
                    market["observation_id"] = (
                        compatibility_market_id
                    )

                    benchmark = normalized_benchmark
                    side = normalized_side
                    edge = normalized_edge

                    if normalized_decision is not None:
                        compatibility_decision_id = (
                            normalized_decision.get(
                                "decision_id"
                            )
                        )

                        if not compatibility_decision_id:
                            raise RuntimeError(
                                "normalized fallback decision lacks "
                                "legacy compatibility id"
                            )

                        decision = dict(
                            normalized_decision
                        )
                        decision["decision_id"] = (
                            compatibility_decision_id
                        )
                    else:
                        decision = None

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
        "normalized_shadow": normalized_shadow,
        "selection_authority": (
            "NORMALIZED"
            if args.normalized_authority
            else "LEGACY"
        ),
        "compatibility_policy": (
            "normalized selection with legacy observation IDs"
            if args.normalized_authority
            else "legacy observation selection"
        ),
        "checkpoints": append_unique(
            D / "checkpoint_observations.jsonl",
            checkpoint_rows,
            "checkpoint_id",
            args.accept,
        ),
    }

    print(json.dumps(report, indent=2))

    if (
        args.require_normalized_parity
        and (
            normalized_shadow["mismatches"] != 0
            or normalized_shadow[
                "missing_normalized_market"
            ] != 0
            or normalized_shadow[
                "unresolved_market_states"
            ] != 0
        )
    ):
        raise SystemExit(
            "normalized checkpoint parity failed"
        )


if __name__ == "__main__":
    main()
