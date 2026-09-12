#!/usr/bin/env python3
"""Build the compact 2026 performance view from immutable v2 evidence."""
from __future__ import annotations

import json
import math
import hashlib
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "data/model_tracking/v2"
OUT = ROOT / "data/site/model_performance_view.json"
PROJECTION_CONTRACT = ROOT / "data/site/current_game_projection_contract.json"
PRESEASON_DB = ROOT / "data/snapshots/preseason/preseason_db.json"

SCORE_PRIORITY = {
    "settlement_v4_frozen_close": 4,
    "settlement_v3_official_checkpoint": 3,
}


def load(name):
    path = STORE / name

    if not path.exists():
        return []

    return [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def load_json(path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, TypeError, ValueError):
        return default


def ledger_audit(names):
    evidence = {}
    for name in names:
        path = STORE / name
        if not path.exists():
            evidence[name] = {"status": "UNAVAILABLE", "rows": None, "sha256": None}
            continue
        raw = path.read_bytes()
        evidence[name] = {
            "status": "AVAILABLE",
            "rows": sum(bool(line.strip()) for line in raw.splitlines()),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    return {"status": "AVAILABLE" if any(v["status"] == "AVAILABLE" for v in evidence.values()) else "UNAVAILABLE", "ledgers": evidence}


def omission_reasons(*, schedule_n, projection_n, captured_n, settled_n,
                     market_n, period, checkpoint, model_id, market_type):
    reasons = {}
    historical = period in {"W0", "W1"}
    known_uncaptured_history = historical and captured_n == 0 and (
        model_id.startswith("standard_")
        or model_id.startswith("dratings_")
        or market_type == "total"
    )
    if known_uncaptured_history and schedule_n:
        reasons["model_projection_not_historically_captured"] = schedule_n
    elif historical and projection_n == 0 and schedule_n:
        reasons["not_projection_eligible"] = schedule_n
    elif projection_n < schedule_n:
        reasons["model_source_missing"] = schedule_n - projection_n
    if projection_n and captured_n < projection_n and not known_uncaptured_history:
        reasons["market_checkpoint_missing"] = projection_n - captured_n
    if checkpoint == "CLOSE" and historical and captured_n == 0:
        reasons["close_capture_not_active"] = schedule_n
    if captured_n > settled_n:
        reasons["settlement_pending"] = captured_n - settled_n
    if market_n < captured_n:
        reasons["no_valid_pre_checkpoint_market"] = captured_n - market_n
    if model_id.startswith("standard_") and projection_n < schedule_n and not historical:
        reasons["component_incomplete"] = schedule_n - projection_n
    return reasons


def coverage_metrics(rows, *, accuracy_rows=None, checkpoint, schedule_n, projection_n,
                     captured_rows, model_id, market_type, period):
    accuracy_rows = rows if accuracy_rows is None else accuracy_rows
    wins = sum(row.get("result") == 1 for row in rows)
    losses = sum(row.get("result") == -1 for row in rows)
    pushes = sum(row.get("result") == 0 for row in rows)
    ae = [float(row["absolute_error"]) for row in accuracy_rows if row.get("absolute_error") is not None]
    signed = [float(row["signed_error"]) for row in accuracy_rows if row.get("signed_error") is not None]
    squared = [float(row["squared_error"]) for row in accuracy_rows if row.get("squared_error") is not None]
    clv = [float(row["clv"]) for row in rows if row.get("clv") is not None]
    captured_n = len({row.get("checkpoint_id") or row.get("checkpoint_observation_id") for row in captured_rows})
    market_n = len({row.get("checkpoint_id") or row.get("checkpoint_observation_id") for row in captured_rows if row.get("market_line") is not None or row.get("market_observation_id")})
    settled_n = len(rows)
    primary_n = wins + losses + pushes
    provenance_rows = captured_rows
    market_books = sorted({str(row.get("market_book")) for row in provenance_rows if row.get("market_book")})
    market_sources = sorted({str(row.get("market_source")) for row in provenance_rows if row.get("market_source")})
    target_times = sorted({str(row.get("checkpoint_at")) for row in provenance_rows if row.get("checkpoint_at")})
    close = checkpoint == "CLOSE"
    return {
        "games": len(accuracy_rows), "record": f"{wins}-{losses}-{pushes}",
        "wins": wins, "losses": losses, "pushes": pushes,
        "schedule_eligible_n": schedule_n, "projection_eligible_n": projection_n,
        "prediction_n": projection_n, "settled_prediction_n": len(accuracy_rows),
        "market_n": market_n, "market_eligible_n": market_n, "captured_n": captured_n,
        "settled_n": settled_n,
        "ats_n": wins + losses if market_type == "spread" else None,
        "ou_n": wins + losses if market_type == "total" else None,
        "roi_n": settled_n, "mae_n": len(ae), "rmse_n": len(squared),
        "bias_n": len(signed), "clv_n": None if close else len(clv),
        "ats_or_ou_pct": wins / (wins + losses) if wins + losses else None,
        "roi": sum(float(row.get("profit") or 0) for row in rows) / settled_n if settled_n else None,
        "mae": sum(ae) / len(ae) if ae else None,
        "bias": sum(signed) / len(signed) if signed else None,
        "rmse": math.sqrt(sum(squared) / len(squared)) if squared else None,
        "average_point_clv": None if close else (sum(clv) / len(clv) if clv else None),
        "median_clv": None if close else median(clv),
        "positive_clv_pct": None if close else (sum(value > 0 for value in clv) / len(clv) if clv else None),
        "beat_close_pct": None if close else (
            sum(bool(row.get("beat_close")) for row in rows if row.get("beat_close") is not None)
            / sum(row.get("beat_close") is not None for row in rows)
            if any(row.get("beat_close") is not None for row in rows) else None
        ),
        "omission_reasons": omission_reasons(schedule_n=schedule_n, projection_n=projection_n, captured_n=captured_n, settled_n=settled_n, market_n=market_n, period=period, checkpoint=checkpoint, model_id=model_id, market_type=market_type),
        "provenance": {
            "checkpoint": checkpoint,
            "checkpoint_target_timestamps": target_times,
            "market_timestamp_semantics": "EXACT_FROZEN_CLOSE" if close else "LATEST_VALID_AT_OR_BEFORE_TARGET",
            "market_books": market_books,
            "market_sources": market_sources,
            "evidence_status": "AVAILABLE" if provenance_rows else "UNAVAILABLE",
        },
    }


def atomic(payload):
    OUT.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        "w",
        dir=OUT.parent,
        delete=False,
        encoding="utf-8",
    ) as handle:
        json.dump(
            payload,
            handle,
            separators=(",", ":"),
            allow_nan=False,
        )
        handle.write("\n")
        temp = Path(handle.name)

    temp.replace(OUT)


def median(values):
    if not values:
        return None

    values = sorted(values)
    n = len(values)

    if n % 2:
        return values[n // 2]

    return (
        values[n // 2 - 1]
        + values[n // 2]
    ) / 2


def authoritative_scores(scores_all):
    selected = {}

    for row in scores_all:
        key = (
            row.get("checkpoint_observation_id")
            or row.get("score_id")
        )

        priority = SCORE_PRIORITY.get(
            row.get("scoring_version"),
            0,
        )

        current = selected.get(key)

        if current is None:
            selected[key] = row
            continue

        current_priority = SCORE_PRIORITY.get(
            current.get("scoring_version"),
            0,
        )

        if priority > current_priority:
            selected[key] = row

    return list(selected.values())


def authoritative_prediction_scores(rows):
    selected = {}
    for row in rows:
        key = (
            row.get("canonical_game_id"), row.get("model_id"),
            row.get("model_version"), row.get("market_type"),
        )
        prior = selected.get(key)
        if prior is None or str(row.get("frozen_at") or "") > str(prior.get("frozen_at") or ""):
            selected[key] = row
    return list(selected.values())



def normalized_decisions():
    states = {
        row["decision_state_id"]: row
        for row in load("decision_states.jsonl")
    }

    confirmations = load(
        "decision_confirmations.jsonl"
    )

    rows = []

    for confirmation in confirmations:
        state = states.get(
            confirmation.get("decision_state_id")
        )

        if state is None:
            continue

        rows.append({
            **state,
            "decision_id": (
                confirmation.get("legacy_decision_id")
                or state.get("decision_state_id")
            ),
            "market_observation_id": (
                confirmation.get(
                    "legacy_market_observation_id"
                )
            ),
            "created_at": confirmation.get(
                "created_at"
            ),
            "decision_state_id": state.get(
                "decision_state_id"
            ),
            "decision_confirmation_id": (
                confirmation.get("confirmation_id")
            ),
            "market_confirmation_id": (
                confirmation.get(
                    "market_confirmation_id"
                )
            ),
        })

    return rows



def main():
    registry = json.loads(
        (STORE / "model_registry.json").read_text()
    )["models"]

    predictions = load("prediction_observations.jsonl")
    checkpoints = load("checkpoint_observations.jsonl")
    decisions = normalized_decisions()
    scores_all = load("scores.jsonl")
    scores = authoritative_scores(scores_all)
    prediction_scores_all = load("prediction_scores.jsonl")
    prediction_scores = authoritative_prediction_scores(prediction_scores_all)
    fbs_teams = {
        str(row.get("team"))
        for row in load_json(PRESEASON_DB, {}).get("teams", [])
        if row.get("team")
    }
    schedule_games = [
        game
        for game in load_json(PROJECTION_CONTRACT, {}).get("games", [])
        if game.get("away_team") in fbs_teams
        and game.get("home_team") in fbs_teams
    ]
    fbs_game_ids = {
        str(game.get("game_id"))
        for game in schedule_games
        if game.get("game_id")
    }
    predictions = [row for row in predictions if str(row.get("canonical_game_id")) in fbs_game_ids]
    fbs_prediction_ids = {str(row.get("observation_id")) for row in predictions}
    checkpoints = [row for row in checkpoints if str(row.get("canonical_game_id")) in fbs_game_ids]
    decisions = [row for row in decisions if str(row.get("canonical_game_id")) in fbs_game_ids]
    scores = [row for row in scores if str(row.get("prediction_observation_id")) in fbs_prediction_ids]
    prediction_scores = [row for row in prediction_scores if str(row.get("canonical_game_id")) in fbs_game_ids]

    latest = {}

    for prediction in predictions:
        latest[
            (
                prediction["model_id"],
                prediction.get("model_version"),
            )
        ] = prediction

    predictions_by_id = {
        row["observation_id"]: row
        for row in predictions
    }

    grouped = defaultdict(list)
    accuracy_grouped = defaultdict(list)

    for score in scores:
        grouped[
            (
                score.get("model_id"),
                score.get("model_version"),
            )
        ].append(score)

    for score in prediction_scores:
        accuracy_grouped[(score.get("model_id"), score.get("model_version"))].append(score)

    matrices = {
        "spread": [],
        "total": [],
    }

    for spec in registry:
        key = (
            spec["model_id"],
            spec["model_version"],
        )

        rows = grouped[key]
        accuracy_rows = accuracy_grouped[key]
        latest_prediction = latest.get(key, {})

        wins = sum(
            row.get("result") == 1
            for row in rows
        )
        losses = sum(
            row.get("result") == -1
            for row in rows
        )
        pushes = sum(
            row.get("result") == 0
            for row in rows
        )

        clv = [
            row["clv"]
            for row in rows
            if row.get("clv") is not None
        ]

        absolute_error = [
            row["absolute_error"]
            for row in accuracy_rows
            if row.get("absolute_error") is not None
        ]

        squared_error = [
            row["squared_error"]
            for row in accuracy_rows
            if row.get("squared_error") is not None
        ]

        signed_error = [
            row["signed_error"]
            for row in accuracy_rows
            if row.get("signed_error") is not None
        ]

        observed = [
            row
            for row in predictions
            if row["model_id"] == spec["model_id"]
            and row.get("model_version")
            == spec["model_version"]
        ]

        available = [
            row
            for row in observed
            if row.get("availability_status")
            == "AVAILABLE"
        ]

        role = spec.get("role", "individual")

        if role == "individual":
            model_type = "individual"
        elif "shadow" in role:
            model_type = "shadow"
        else:
            model_type = "composite"

        n = len(rows)
        prediction_n = len({row.get("canonical_game_id") for row in available})
        settled_prediction_n = len(accuracy_rows)

        beat_close_rows = [
            row
            for row in rows
            if row.get("beat_close") is not None
        ]

        won_move_rows = [
            row
            for row in rows
            if row.get("won_line_move") is not None
        ]

        matrices[spec["market_type"]].append({
            "model": spec["model_id"],
            "model_id": spec["model_id"],
            "model_version": spec["model_version"],
            "display_name": (
                spec["model_id"]
                .replace("_", " ")
                .title()
            ),
            "market_type": spec["market_type"],
            "model_type": model_type,
            "role": role,
            "status": latest_prediction.get(
                "availability_status",
                "NOT_YET_CAPTURED",
            ),
            "tracking_status": "ACTIVE_PROSPECTIVE_V2",
            "latest_source_timestamp": (
                latest_prediction.get(
                    "source_updated_at"
                )
            ),
            "default_visible": role in {
                "active_standard_authority",
                "prospective_challenger",
                "shadow_production_unchanged",
            },
            "rank": None,
            "ranking_status": (
                "UNRANKED — SMALL SAMPLE"
                if settled_prediction_n < 30
                else "ELIGIBLE"
            ),
            "games": settled_prediction_n,
            "prediction_n": prediction_n,
            "settled_prediction_n": settled_prediction_n,
            "mae_n": len(absolute_error),
            "rmse_n": len(squared_error),
            "bias_n": len(signed_error),
            "market_n": n,
            "ats_n": wins + losses if spec["market_type"] == "spread" else None,
            "ou_n": wins + losses if spec["market_type"] == "total" else None,
            "roi_n": n,
            "clv_n": len(clv),
            "availability_pct": (
                len(available) / len(observed)
                if observed
                else None
            ),
            "record": f"{wins}-{losses}-{pushes}",
            "win_pct": (
                wins / (wins + losses)
                if wins + losses
                else None
            ),
            "ats_or_ou_pct": (
                wins / (wins + losses)
                if wins + losses
                else None
            ),
            "roi": (
                sum(
                    row.get("profit") or 0
                    for row in rows
                ) / n
                if n
                else None
            ),
            "average_point_clv": (
                sum(clv) / len(clv)
                if clv
                else None
            ),
            "median_clv": median(clv),
            "positive_clv_pct": (
                sum(value > 0 for value in clv)
                / len(clv)
                if clv
                else None
            ),
            "beat_close_pct": (
                sum(
                    bool(row.get("beat_close"))
                    for row in beat_close_rows
                )
                / len(beat_close_rows)
                if beat_close_rows
                else None
            ),
            "won_line_move_pct": (
                sum(
                    bool(row.get("won_line_move"))
                    for row in won_move_rows
                )
                / len(won_move_rows)
                if won_move_rows
                else None
            ),
            "mae": (
                sum(absolute_error)
                / len(absolute_error)
                if absolute_error
                else None
            ),
            "bias": (
                sum(signed_error)
                / len(signed_error)
                if signed_error
                else None
            ),
            "rmse": (
                math.sqrt(
                    sum(squared_error)
                    / len(squared_error)
                )
                if squared_error
                else None
            ),
        })

    for market in matrices:
        eligible = sorted(
            [
                row
                for row in matrices[market]
                if row["settled_prediction_n"] >= 30
            ],
            key=lambda row: (
                -(
                    row["roi"]
                    if row["roi"] is not None
                    else -999
                ),
                (
                    row["mae"]
                    if row["mae"] is not None
                    else 999
                ),
            ),
        )

        for rank, row in enumerate(
            eligible,
            1,
        ):
            row["rank"] = rank
            row["ranking_status"] = "RANKED"

    public_decisions_by_key = {}

    for decision in decisions:
        prediction = predictions_by_id.get(
            decision.get(
                "prediction_observation_id"
            ),
            {},
        )

        model_identity = (
            prediction.get("model_id")
            or decision.get(
                "prediction_observation_id"
            )
            or decision.get("decision_id")
        )

        key = (
            decision.get("canonical_game_id"),
            decision.get("market_type"),
            decision.get("checkpoint"),
            model_identity,
        )

        prior = public_decisions_by_key.get(key)

        if (
            prior is None
            or str(decision.get("created_at") or "")
            >= str(prior.get("created_at") or "")
        ):
            public_decisions_by_key[key] = decision

    public_decisions = sorted(
        public_decisions_by_key.values(),
        key=lambda row: (
            str(row.get("created_at") or ""),
            str(row.get("decision_id") or ""),
        ),
    )

    opportunities = []

    for decision in public_decisions:
        prediction = predictions_by_id.get(
            decision.get(
                "prediction_observation_id"
            ),
            {},
        )

        market_provenance = (
            decision.get("market_provenance")
            if isinstance(
                decision.get("market_provenance"),
                dict,
            )
            else {}
        )

        opportunities.append({
            "canonical_game_id":
                decision.get("canonical_game_id"),
            "site_week":
                prediction.get("week"),
            "away_team":
                prediction.get("away_team"),
            "home_team":
                prediction.get("home_team"),
            "market_type":
                decision.get("market_type"),
            "checkpoint":
                decision.get("checkpoint"),
            "consensus_versions": (
                [prediction.get("model_id")]
                if prediction
                and prediction.get("model_id")
                else []
            ),
            "opener_market_observation_id":
                decision.get("market_observation_id"),
            "estimated_ev_pct": None,
            "qualification_status":
                "TRACKED_NOT_QUALIFIED",
            "opener_provenance_grade":
                market_provenance.get(
                    "freshness_status"
                ),
            "bet_side":
                decision.get("bet_side"),
            "edge":
                decision.get("edge"),
            "created_at":
                decision.get("created_at"),
        })

    checkpoint_order = [
        "SUNDAY_9PM_ET",
        "TUESDAY_9PM_ET",
        "CLOSE",
    ]

    periods = (
        ["W0"]
        + [f"W{i}" for i in range(1, 16)]
        + ["Season"]
    )

    tracker = {
        "spread": {},
        "total": {},
    }

    for market_type in ["spread", "total"]:
        market_specs = [
            spec
            for spec in registry
            if spec.get("market_type") == market_type
        ]

        for period in periods:
            period_rows = []

            if period == "Season":
                period_rows = [
                    row
                    for row in scores
                    if row.get("market_type") == market_type
                ]
                period_accuracy_rows = [
                    row for row in prediction_scores
                    if row.get("market_type") == market_type
                ]
            else:
                week = int(period[1:])

                period_rows = [
                    row
                    for row in scores
                    if row.get("market_type") == market_type
                    and row.get("week") == week
                ]
                period_accuracy_rows = [
                    row for row in prediction_scores
                    if row.get("market_type") == market_type
                    and row.get("week") == week
                ]

            model_rows = []

            for spec in market_specs:
                model_id = spec["model_id"]
                model_version = spec["model_version"]
                model_prediction_rows = [
                    prediction for prediction in predictions
                    if prediction.get("model_id") == model_id
                    and prediction.get("model_version") == model_version
                ]
                formula_versions = sorted({
                    str(prediction.get("formula_version"))
                    for prediction in model_prediction_rows
                    if prediction.get("formula_version")
                })

                row = {
                    "model_id": model_id,
                    "model_version": model_version,
                    "display_name": (
                        model_id
                        .replace("_", " ")
                        .title()
                    ),
                    "role": spec.get("role"),
                    "formula_version": formula_versions[-1] if len(formula_versions) == 1 else None,
                    "formula_versions": formula_versions,
                    "weights": spec.get("weights"),
                    "authority_status": (
                        "REFERENCE_ONLY"
                        if model_id.startswith("sagarin_")
                        else "PRODUCTION_AUTHORITY"
                        if spec.get("role") == "active_standard_authority"
                        else "TRACKED_COMPARISON"
                    ),
                    "historical_status": "HISTORICAL_PARTIAL" if period in {"W0", "W1"} else "PROSPECTIVE",
                    "checkpoints": {},
                }

                for checkpoint in checkpoint_order:
                    selected_rows = [
                        score
                        for score in period_rows
                        if score.get("model_id") == model_id
                        and score.get("model_version") == model_version
                        and score.get("checkpoint") == checkpoint
                    ]
                    selected_accuracy_rows = [
                        score for score in period_accuracy_rows
                        if score.get("model_id") == model_id
                        and score.get("model_version") == model_version
                    ]

                    if period == "Season":
                        schedule_n = len({str(game.get("game_id")) for game in schedule_games if game.get("game_id")})
                        prediction_rows = [p for p in predictions if p.get("model_id") == model_id and p.get("model_version") == model_version and p.get("market_type") == market_type and p.get("availability_status") == "AVAILABLE"]
                        captured_rows = [c for c in checkpoints if c.get("model_id") == model_id and c.get("model_version") == model_version and c.get("market_type") == market_type and c.get("checkpoint") == checkpoint and c.get("selection_status") == "OFFICIAL"]
                    else:
                        schedule_n = len({str(game.get("game_id")) for game in schedule_games if game.get("week") == week and game.get("game_id")})
                        prediction_rows = [p for p in predictions if p.get("week") == week and p.get("model_id") == model_id and p.get("model_version") == model_version and p.get("market_type") == market_type and p.get("availability_status") == "AVAILABLE"]
                        captured_rows = [c for c in checkpoints if c.get("week") == week and c.get("model_id") == model_id and c.get("model_version") == model_version and c.get("market_type") == market_type and c.get("checkpoint") == checkpoint and c.get("selection_status") == "OFFICIAL"]

                    row["checkpoints"][checkpoint] = coverage_metrics(
                        selected_rows, accuracy_rows=selected_accuracy_rows,
                        checkpoint=checkpoint,
                        schedule_n=schedule_n,
                        projection_n=len({p.get("canonical_game_id") for p in prediction_rows}),
                        captured_rows=captured_rows, model_id=model_id,
                        market_type=market_type, period=period,
                    )

                model_rows.append(row)

            tracker[market_type][period] = model_rows

    payload = {
        "schema_version": "model-performance-view-v7",
        "built_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "season": 2026,
        "status": (
            "ACTIVE_PROSPECTIVE"
            if predictions
            else "READY_NOT_YET_CAPTURED"
        ),
        "tracking_started": bool(predictions),
        "ranking_minimum": 30,
        "summary": {
            "opportunities": len(public_decisions),
            "predictions": len(predictions),
            "score_rows_all_versions": len(
                scores_all
            ),
            "settled": len(scores),
            "settled_predictions": len(prediction_scores),
            "prediction_score_rows_all_versions": len(prediction_scores_all),
            "spread": {
                "opportunities": sum(
                    row.get("market_type")
                    == "spread"
                    for row in public_decisions
                ),
                "settled_selections": sum(
                    row.get("market_type")
                    == "spread"
                    for row in scores
                ),
            },
            "totals": {
                "opportunities": sum(
                    row.get("market_type")
                    == "total"
                    for row in public_decisions
                ),
                "settled_selections": sum(
                    row.get("market_type")
                    == "total"
                    for row in scores
                ),
            },
        },
        "spread_matrix": matrices["spread"],
        "total_matrix": matrices["total"],
        "spread_checkpoint_tracker": tracker["spread"],
        "total_checkpoint_tracker": tracker["total"],
        "checkpoint_order": checkpoint_order,
        "opportunities": opportunities,
        "audit": ledger_audit([
            "prediction_observations.jsonl", "checkpoint_observations.jsonl",
            "market_states.jsonl", "market_confirmations.jsonl",
            "decision_states.jsonl", "decision_confirmations.jsonl",
            "settlements.jsonl", "scores.jsonl", "prediction_scores.jsonl",
        ]),
        "methodology": {
            "source": "immutable-model-tracking-v2",
            "prediction_contract": (
                "data/site/"
                "current_game_projection_contract.json"
            ),
            "market_contract": (
                "data/site/current_market_contract.json"
            ),
            "results_contract": (
                "data/canonical/"
                "game_results_2026.json"
            ),
            "no_fake_backfill": True,
            "score_authority": (
                "prediction accuracy uses the latest valid pre-kickoff observation per game/model; betting metrics use the newest scoring version per official checkpoint"
            ),
            "closing_authority": (
                "current_market_contract "
                "FROZEN_CLOSE"
            ),
            "checkpoint_contract": (
                "one game x one model x checkpoint; "
                "SUNDAY_9PM_ET, TUESDAY_9PM_ET, CLOSE"
            ),
            "close_clv_policy": (
                "not applicable; CLOSE checkpoint CLV metrics are null"
            ),
            "clv": (
                "checkpoint line versus canonical "
                "FROZEN_CLOSE; null when unavailable"
            ),
            "spread_projection_formula": (
                "named canonical projection "
                "contract models"
            ),
            "hfa": {
                "non_neutral": None,
                "neutral": None,
                "method": (
                    "owned by each named model contract"
                ),
            },
            "spread_core_v1": {
                "models": [
                    "SP+",
                    "FPI",
                    "TeamRankings",
                    "DRatings",
                ],
                "model_id": (
                    "standard_spread_4src_equal_v1"
                ),
            },
            "total": {
                "baseline": (
                    "standard_total_sp_massey_"
                    "dratings_v1"
                ),
                "challenger": (
                    "total_sp50_massey50_v1"
                ),
                "minimum_independent_sources": 2,
            },
        },
        "periods": (
            ["W0"]
            + [
                f"W{i}"
                for i in range(1, 16)
            ]
            + [
                "Conference Championships",
                "Bowl / Playoff",
                "All",
            ]
        ),
    }

    atomic(payload)

    print(
        f"Wrote {OUT} "
        f"({len(predictions)} immutable predictions, "
        f"{len(scores)} authoritative scores, "
        f"{len(scores_all)} total score rows)"
    )


if __name__ == "__main__":
    main()
