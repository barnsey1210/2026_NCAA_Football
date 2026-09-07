#!/usr/bin/env python3
"""Build the compact 2026 performance view from immutable v2 evidence."""
from __future__ import annotations

import json
import math
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "data/model_tracking/v2"
OUT = ROOT / "data/site/model_performance_view.json"

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


def main():
    registry = json.loads(
        (STORE / "model_registry.json").read_text()
    )["models"]

    predictions = load("prediction_observations.jsonl")
    decisions = load("decision_observations.jsonl")
    scores_all = load("scores.jsonl")
    scores = authoritative_scores(scores_all)

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

    for score in scores:
        grouped[
            (
                score.get("model_id"),
                score.get("model_version"),
            )
        ].append(score)

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
            for row in rows
            if row.get("absolute_error") is not None
        ]

        squared_error = [
            row["squared_error"]
            for row in rows
            if row.get("squared_error") is not None
        ]

        signed_error = [
            row["signed_error"]
            for row in rows
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
                if n < 30
                else "ELIGIBLE"
            ),
            "games": n,
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
                if row["games"] >= 30
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

    opportunities = []

    for decision in decisions:
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

    def score_metrics(rows, checkpoint=None):
        wins = sum(row.get("result") == 1 for row in rows)
        losses = sum(row.get("result") == -1 for row in rows)
        pushes = sum(row.get("result") == 0 for row in rows)

        ae = [
            float(row["absolute_error"])
            for row in rows
            if row.get("absolute_error") is not None
        ]

        signed = [
            float(row["signed_error"])
            for row in rows
            if row.get("signed_error") is not None
        ]

        squared = [
            float(row["squared_error"])
            for row in rows
            if row.get("squared_error") is not None
        ]

        clv = [
            float(row["clv"])
            for row in rows
            if row.get("clv") is not None
        ]

        n = len(rows)

        if checkpoint == "CLOSE":
            avg_clv = None
            median_point_clv = None
            positive_clv_pct = None
            beat_close_pct = None
        else:
            avg_clv = (
                sum(clv) / len(clv)
                if clv
                else None
            )
            median_point_clv = median(clv)

            positive_clv_pct = (
                sum(value > 0 for value in clv)
                / len(clv)
                if clv
                else None
            )

            beat_rows = [
                row
                for row in rows
                if row.get("beat_close") is not None
            ]

            beat_close_pct = (
                sum(
                    bool(row.get("beat_close"))
                    for row in beat_rows
                ) / len(beat_rows)
                if beat_rows
                else None
            )

        return {
            "games": n,
            "record": f"{wins}-{losses}-{pushes}",
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "ats_or_ou_pct": (
                wins / (wins + losses)
                if wins + losses
                else None
            ),
            "roi": (
                sum(
                    float(row.get("profit") or 0)
                    for row in rows
                ) / n
                if n
                else None
            ),
            "mae": (
                sum(ae) / len(ae)
                if ae
                else None
            ),
            "bias": (
                sum(signed) / len(signed)
                if signed
                else None
            ),
            "rmse": (
                math.sqrt(
                    sum(squared) / len(squared)
                )
                if squared
                else None
            ),
            "average_point_clv": avg_clv,
            "median_clv": median_point_clv,
            "positive_clv_pct": positive_clv_pct,
            "beat_close_pct": beat_close_pct,
        }

    checkpoint_order = [
        "SUNDAY_9PM_ET",
        "TUESDAY_9PM_ET",
        "CLOSE",
    ]

    periods = (
        ["W0"]
        + [f"W{i}" for i in range(1, 15)]
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
            else:
                week = int(period[1:])

                period_rows = [
                    row
                    for row in scores
                    if row.get("market_type") == market_type
                    and row.get("week") == week
                ]

            model_rows = []

            for spec in market_specs:
                model_id = spec["model_id"]
                model_version = spec["model_version"]

                row = {
                    "model_id": model_id,
                    "model_version": model_version,
                    "display_name": (
                        model_id
                        .replace("_", " ")
                        .title()
                    ),
                    "role": spec.get("role"),
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

                    row["checkpoints"][checkpoint] = score_metrics(
                        selected_rows,
                        checkpoint=checkpoint,
                    )

                model_rows.append(row)

            tracker[market_type][period] = model_rows

    payload = {
        "schema_version": "model-performance-view-v5",
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
            "opportunities": len(decisions),
            "predictions": len(predictions),
            "score_rows_all_versions": len(
                scores_all
            ),
            "settled": len(scores),
            "spread": {
                "opportunities": sum(
                    row.get("market_type")
                    == "spread"
                    for row in decisions
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
                    for row in decisions
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
                "newest scoring version per "
                "official checkpoint"
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
                for i in range(1, 15)
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
