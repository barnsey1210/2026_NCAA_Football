#!/usr/bin/env python3
"""Settle verified finals and score official checkpoints against canonical FROZEN_CLOSE."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from immutable_tracking import append_unique, stable_id
from normalized_checkpoint_reader import (
    build_normalized_context,
    semantic_market,
)

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data/model_tracking/v2"

RESULTS = ROOT / "data/canonical/game_results_2026.json"
MARKET_CONTRACT = ROOT / "data/site/current_market_contract.json"

OFFICIAL_CHECKPOINTS = {
    "SUNDAY_9PM_ET",
    "TUESDAY_9PM_ET",
    "CLOSE",
}


def load_jsonl(name):
    p = D / name
    if not p.exists():
        return []
    return [
        json.loads(line)
        for line in p.read_text().splitlines()
        if line.strip()
    ]


def profit(result, price):
    if result <= 0:
        return -1.0 if result < 0 else 0.0

    p = float(price or -110)
    return p / 100 if p > 0 else 100 / abs(p)


def frozen_close(game, market_type, side):
    reference = game.get("reference") or {}
    market = reference.get(market_type) or {}

    if market_type == "spread":
        quote = market.get(side) or {}
    elif market_type == "total":
        quote = market.get(side) or {}
    else:
        return None

    if quote.get("line") is None:
        return None

    if str(quote.get("freshness_status") or "").upper() != "FROZEN_CLOSE":
        return None

    try:
        line = float(quote["line"])
    except (TypeError, ValueError):
        return None

    return {
        "line": line,
        "price": quote.get("price"),
        "sportsbook": (
            quote.get("sportsbook")
            or market.get("sportsbook")
        ),
        "source": quote.get("source"),
        "source_updated_at": quote.get("source_updated_at"),
        "freshness_status": quote.get("freshness_status"),
        "market_lifecycle_state": quote.get(
            "market_lifecycle_state"
        ),
    }




def build_normalized_market_lookup():
    context = build_normalized_context(D)
    return context, {}


def checkpoint_market_snapshot(checkpoint):
    """Reconstruct the immutable market used by a frozen checkpoint."""
    if checkpoint.get("market_line") is None:
        return None

    return {
        "observation_id":
            checkpoint.get("market_observation_id"),
        "market_state_id":
            checkpoint.get("market_state_id"),
        "market_confirmation_id":
            checkpoint.get("market_confirmation_id"),
        "canonical_game_id":
            checkpoint.get("canonical_game_id"),
        "market_type":
            checkpoint.get("market_type"),
        "sportsbook":
            checkpoint.get("market_book"),
        "side":
            checkpoint.get("bet_side"),
        "line":
            checkpoint.get("market_line"),
        "price":
            checkpoint.get("market_price"),
        "source":
            checkpoint.get("market_source"),
        "observed_at":
            checkpoint.get("market_observed_at"),
        "source_updated_at":
            checkpoint.get("market_source_updated_at"),
    }


def resolve_normalized_checkpoint_market(
    checkpoint,
    normalized_context,
    normalized_by_legacy_id,
):
    # CLOSE stays on its existing legacy path for this stage.
    if checkpoint.get("checkpoint") == "CLOSE":
        return None

    # New checkpoints can carry their exact normalized
    # confirmation directly.
    confirmation_id = checkpoint.get(
        "market_confirmation_id"
    )

    if confirmation_id:
        row = normalized_context[
            "markets_by_confirmation"
        ].get(confirmation_id)

        if row is not None:
            return row

    # Historical Sunday/Tuesday checkpoints are already
    # immutable market snapshots. Do not depend on a legacy
    # observation ID to score them.
    return checkpoint_market_snapshot(checkpoint)



def market_semantics_match(
    legacy_market,
    authority_market,
):
    if legacy_market is None or authority_market is None:
        return legacy_market is authority_market

    fields = (
        "canonical_game_id",
        "market_type",
        "sportsbook",
        "side",
        "line",
        "price",
        "source",
        "observed_at",
        "source_updated_at",
    )

    return all(
        legacy_market.get(field)
        == authority_market.get(field)
        for field in fields
    )


def parse_time(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None


def frozen_prediction_scores(predictions, games, settlements_by_game):
    """Score the last valid observation before kickoff, without a market gate."""
    selected = {}
    skipped = {"unavailable": 0, "invalid_projection": 0, "not_pre_kickoff": 0}

    for row in predictions:
        game_id = str(row.get("canonical_game_id") or "")
        if game_id not in games or row.get("availability_status") != "AVAILABLE":
            skipped["unavailable"] += 1
            continue
        try:
            float(row["projection"])
        except (KeyError, TypeError, ValueError):
            skipped["invalid_projection"] += 1
            continue
        observed_at = parse_time(row.get("observed_at"))
        kickoff_at = parse_time(row.get("kickoff_at"))
        if observed_at is None or kickoff_at is None or observed_at >= kickoff_at:
            skipped["not_pre_kickoff"] += 1
            continue
        key = (game_id, row.get("model_id"), row.get("model_version"), row.get("market_type"))
        prior = selected.get(key)
        if prior is None or str(row.get("observed_at")) > str(prior.get("observed_at")):
            selected[key] = row

    scores = []
    for key, prediction in selected.items():
        game_id, model_id, model_version, market_type = key
        game = games[game_id]
        actual = game.get("home_margin_actual") if market_type == "spread" else game.get("total_points_actual") if market_type == "total" else None
        try:
            error = float(prediction["projection"]) - float(actual)
        except (TypeError, ValueError):
            continue
        settlement_id = settlements_by_game[game_id]
        score_id = stable_id("prediction_score", prediction["observation_id"], settlement_id, "prediction_accuracy_v1")
        scores.append({
            "prediction_score_id": score_id,
            "prediction_observation_id": prediction["observation_id"],
            "settlement_id": settlement_id,
            "canonical_game_id": game_id,
            "model_id": model_id,
            "model_version": model_version,
            "market_type": market_type,
            "season": prediction.get("season"),
            "week": prediction.get("week"),
            "frozen_at": prediction.get("observed_at"),
            "kickoff_at": prediction.get("kickoff_at"),
            "projection": prediction.get("projection"),
            "actual": actual,
            "absolute_error": abs(error),
            "signed_error": error,
            "squared_error": error * error,
            "scoring_version": "prediction_accuracy_v1",
        })
    return scores, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accept", action="store_true")
    ap.add_argument(
        "--normalized-market-authority",
        action="store_true",
    )
    ap.add_argument(
        "--require-normalized-parity",
        action="store_true",
    )
    args = ap.parse_args()

    if (
        args.require_normalized_parity
        and not args.normalized_market_authority
    ):
        ap.error(
            "--require-normalized-parity requires "
            "--normalized-market-authority"
        )

    results_payload = json.loads(RESULTS.read_text())
    market_payload = json.loads(MARKET_CONTRACT.read_text())

    games = {
        str(row["game_id"]): row
        for row in results_payload.get("games", [])
        if row.get("completed") is True
    }

    market_games = {
        str(row["game_id"]): row
        for row in market_payload.get("games", [])
        if row.get("game_id")
    }

    prediction_rows = load_jsonl("prediction_observations.jsonl")
    predictions = {row["observation_id"]: row for row in prediction_rows}

    markets = {
        row["observation_id"]: row
        for row in load_jsonl("market_observations.jsonl")
    }

    normalized_context = None
    normalized_by_legacy_id = {}

    if args.normalized_market_authority:
        (
            normalized_context,
            normalized_by_legacy_id,
        ) = build_normalized_market_lookup()

    normalized_resolution = {
        "enabled": bool(
            args.normalized_market_authority
        ),
        "compared": 0,
        "resolved_normalized": 0,
        "checkpoint_snapshot_fallback": 0,
        "mismatches": 0,
        "close_legacy": 0,
        "superseded_market_confirmations": (
            normalized_context[
                "superseded_market_confirmations"
            ]
            if normalized_context
            else 0
        ),
        "unresolved_market_states": (
            normalized_context[
                "unresolved_market_states"
            ]
            if normalized_context
            else 0
        ),
        "first_mismatches": [],
    }

    checkpoint_rows_all = load_jsonl(
        "checkpoint_observations.jsonl"
    )

    checkpoints = [
        row
        for row in checkpoint_rows_all
        if row.get("checkpoint") in OFFICIAL_CHECKPOINTS
        and row.get("selection_status") == "OFFICIAL"
    ]

    checkpoints_by_game = {}

    for row in checkpoints:
        game_id = str(row.get("canonical_game_id") or "")
        if game_id:
            checkpoints_by_game.setdefault(game_id, []).append(row)

    settlements = []
    settlements_by_game = {}
    scores = []

    skipped = {
        "missing_prediction": 0,
        "missing_checkpoint_market": 0,
        "invalid_checkpoint_line": 0,
        "invalid_prediction": 0,
        "missing_frozen_close": 0,
    }

    frozen_close_available = 0
    frozen_close_missing = 0

    for game_id, game in games.items():
        settlement_id = stable_id(
            "settlement",
            game_id,
            game.get("home_score"),
            game.get("away_score"),
            game.get("source_updated_at"),
        )

        settlements.append({
            "settlement_id": settlement_id,
            "canonical_game_id": game_id,
            "status": "VERIFIED_FINAL",
            "final_home_score": game["home_score"],
            "final_away_score": game["away_score"],
            "completed_at": (
                game.get("source_updated_at")
                or results_payload.get("generated_at")
            ),
            "source": game.get("source"),
            "source_artifact": (
                "data/canonical/game_results_2026.json"
            ),
            "revision": 1,
        })
        settlements_by_game[game_id] = settlement_id

        canonical_market_game = market_games.get(game_id, {})

        for checkpoint in checkpoints_by_game.get(game_id, []):
            prediction = predictions.get(
                checkpoint.get("prediction_observation_id")
            )

            if (
                args.normalized_market_authority
                and checkpoint.get("checkpoint") != "CLOSE"
            ):
                checkpoint_market = (
                    resolve_normalized_checkpoint_market(
                        checkpoint,
                        normalized_context,
                        normalized_by_legacy_id,
                    )
                )

                normalized_resolution["compared"] += 1

                if checkpoint_market is None:
                    normalized_resolution[
                        "missing_authority_market"
                    ] = (
                        normalized_resolution.get(
                            "missing_authority_market",
                            0,
                        ) + 1
                    )
                elif checkpoint.get(
                    "market_confirmation_id"
                ):
                    normalized_resolution[
                        "resolved_normalized"
                    ] += 1
                else:
                    normalized_resolution[
                        "checkpoint_snapshot_fallback"
                    ] += 1

            else:
                checkpoint_market = markets.get(
                    checkpoint.get("market_observation_id")
                )

                if (
                    args.normalized_market_authority
                    and checkpoint.get("checkpoint") == "CLOSE"
                ):
                    normalized_resolution[
                        "close_legacy"
                    ] += 1

            if prediction is None:
                skipped["missing_prediction"] += 1
                continue

            if checkpoint_market is None:
                skipped["missing_checkpoint_market"] += 1
                continue

            try:
                line = float(checkpoint_market["line"])
            except (TypeError, ValueError, KeyError):
                skipped["invalid_checkpoint_line"] += 1
                continue

            try:
                projection = float(prediction["projection"])
            except (TypeError, ValueError, KeyError):
                skipped["invalid_prediction"] += 1
                continue

            market_type = checkpoint["market_type"]
            side = checkpoint["bet_side"]

            home_margin = float(game["home_margin_actual"])
            actual_total = float(game["total_points_actual"])

            close = frozen_close(
                canonical_market_game,
                market_type,
                side,
            )

            if close is None:
                frozen_close_missing += 1
                skipped["missing_frozen_close"] += 1
            else:
                frozen_close_available += 1

            if market_type == "spread":
                score = (
                    home_margin + line
                    if side == "home"
                    else -home_margin + line
                )

                closing_line = (
                    close["line"]
                    if close is not None
                    else None
                )

                clv = (
                    line - closing_line
                    if closing_line is not None
                    else None
                )

                error = projection - home_margin

            elif market_type == "total":
                score = (
                    (actual_total - line)
                    * (1 if side == "over" else -1)
                )

                closing_line = (
                    close["line"]
                    if close is not None
                    else None
                )

                if closing_line is None:
                    clv = None
                elif side == "over":
                    clv = closing_line - line
                else:
                    clv = line - closing_line

                error = projection - actual_total

            else:
                continue

            result = (
                1 if score > 0
                else -1 if score < 0
                else 0
            )

            score_id = stable_id(
                "score",
                checkpoint["checkpoint_id"],
                settlement_id,
                "settlement_v4_frozen_close",
            )

            scores.append({
                "score_id": score_id,
                "prediction_observation_id": (
                    prediction["observation_id"]
                ),
                "market_observation_id": (
                    checkpoint_market["observation_id"]
                ),
                "market_state_id": (
                    checkpoint_market.get(
                        "market_state_id"
                    )
                ),
                "market_confirmation_id": (
                    checkpoint_market.get(
                        "market_confirmation_id"
                    )
                ),
                "checkpoint_observation_id": (
                    checkpoint["checkpoint_id"]
                ),
                "decision_id": checkpoint.get("decision_id"),
                "settlement_id": settlement_id,
                "model_id": prediction["model_id"],
                "model_version": prediction.get("model_version"),
                "market_type": market_type,
                "season": prediction.get("season"),
                "week": prediction.get("week"),
                "checkpoint": checkpoint.get("checkpoint"),
                "checkpoint_at": checkpoint.get("checkpoint_at"),
                "market_benchmark": checkpoint.get(
                    "market_benchmark"
                ),
                "market_book": checkpoint.get("market_book"),
                "prediction_age_hours": checkpoint.get(
                    "prediction_age_hours"
                ),
                "market_age_hours": checkpoint.get(
                    "market_age_hours"
                ),
                "lifecycle_state": prediction.get(
                    "lifecycle_state"
                ),
                "edge_threshold": checkpoint.get("edge"),
                "closing_line": closing_line,
                "closing_price": (
                    close.get("price")
                    if close is not None
                    else None
                ),
                "closing_book": (
                    close.get("sportsbook")
                    if close is not None
                    else None
                ),
                "closing_source": (
                    close.get("source")
                    if close is not None
                    else None
                ),
                "closing_source_updated_at": (
                    close.get("source_updated_at")
                    if close is not None
                    else None
                ),
                "closing_authority": (
                    "CURRENT_MARKET_CONTRACT_FROZEN_CLOSE"
                    if close is not None
                    else "UNAVAILABLE"
                ),
                "result": result,
                "profit": profit(
                    result,
                    checkpoint_market.get("price"),
                ),
                "clv": clv,
                "median_clv": clv,
                "positive_clv": (
                    clv > 0
                    if clv is not None
                    else None
                ),
                "beat_close": (
                    clv > 0
                    if clv is not None
                    else None
                ),
                "won_line_move": (
                    clv > 0
                    if clv not in (None, 0)
                    else None
                ),
                "absolute_error": abs(error),
                "signed_error": error,
                "squared_error": error * error,
                "clv_implied_ev": None,
                "scoring_version": (
                    "settlement_v4_frozen_close"
                ),
            })

    prediction_scores, prediction_skipped = frozen_prediction_scores(
        prediction_rows, games, settlements_by_game
    )

    report = {
        "schema_version": "settlement-preview-v5",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verified_games": len(games),
        "checkpoint_rows_total": len(checkpoint_rows_all),
        "official_checkpoint_rows": len(checkpoints),
        "normalized_market_resolution": normalized_resolution,
        "scoring_authority": (
            "normalized checkpoint markets for Sunday/Tuesday; "
            "legacy CLOSE"
            if args.normalized_market_authority
            else
            "checkpoint_observations.jsonl OFFICIAL rows only"
        ),
        "legacy_scoring_authority": (
            "checkpoint_observations.jsonl OFFICIAL rows only"
        ),
        "closing_authority": (
            "data/site/current_market_contract.json "
            "FROZEN_CLOSE only"
        ),
        "frozen_close_available": frozen_close_available,
        "frozen_close_missing": frozen_close_missing,
        "skipped": skipped,
        "prediction_accuracy": {
            "policy": "latest valid immutable prediction observed before kickoff; no market required",
            "candidates": len(prediction_scores),
            "skipped": prediction_skipped,
        },
        "settlements": append_unique(
            D / "settlements.jsonl",
            settlements,
            "settlement_id",
            args.accept,
        ),
        "scores": append_unique(
            D / "scores.jsonl",
            scores,
            "score_id",
            args.accept,
        ),
        "prediction_scores": append_unique(
            D / "prediction_scores.jsonl",
            prediction_scores,
            "prediction_score_id",
            args.accept,
        ),
    }

    print(json.dumps(report, indent=2))

    if (
        args.require_normalized_parity
        and (
            normalized_resolution["mismatches"] != 0
            or normalized_resolution.get(
                "missing_authority_market",
                0,
            ) != 0
            or normalized_resolution[
                "unresolved_market_states"
            ] != 0
        )
    ):
        raise SystemExit(
            "normalized settlement market parity failed"
        )


if __name__ == "__main__":
    main()
