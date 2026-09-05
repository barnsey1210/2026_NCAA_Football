#!/usr/bin/env python3
"""Settle verified finals and score official checkpoints against canonical FROZEN_CLOSE."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from immutable_tracking import append_unique, stable_id

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accept", action="store_true")
    args = ap.parse_args()

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

    predictions = {
        row["observation_id"]: row
        for row in load_jsonl("prediction_observations.jsonl")
    }

    markets = {
        row["observation_id"]: row
        for row in load_jsonl("market_observations.jsonl")
    }

    raw_decisions = load_jsonl("decision_observations.jsonl")
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

        canonical_market_game = market_games.get(game_id, {})

        for checkpoint in checkpoints_by_game.get(game_id, []):
            prediction = predictions.get(
                checkpoint.get("prediction_observation_id")
            )

            checkpoint_market = markets.get(
                checkpoint.get("market_observation_id")
            )

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

    report = {
        "schema_version": "settlement-preview-v4",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verified_games": len(games),
        "raw_decision_rows": len(raw_decisions),
        "checkpoint_rows_total": len(checkpoint_rows_all),
        "official_checkpoint_rows": len(checkpoints),
        "scoring_authority": (
            "checkpoint_observations.jsonl OFFICIAL rows only"
        ),
        "closing_authority": (
            "data/site/current_market_contract.json "
            "FROZEN_CLOSE only"
        ),
        "frozen_close_available": frozen_close_available,
        "frozen_close_missing": frozen_close_missing,
        "skipped": skipped,
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
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
