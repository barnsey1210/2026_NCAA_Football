#!/usr/bin/env python3
"""Normalized market-state identity helpers for prospective tracking v2.

Stage A is additive only:
- legacy market/decision observation ledgers remain unchanged;
- material market state excludes observation/source timestamps;
- confirmation evidence retains observation/source timestamps;
- decision state references material market state.

No historical ledger migration or deletion is performed here.
"""
from __future__ import annotations

import json

from immutable_tracking import stable_id


MATERIAL_MARKET_FIELDS = (
    "canonical_game_id",
    "market_type",
    "sportsbook",
    "side",
    "line",
    "price",
    "source",
    "freshness_status",
    "lifecycle_state",
)


def canonical(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def market_state_payload(row: dict) -> dict:
    return {
        field: row.get(field)
        for field in MATERIAL_MARKET_FIELDS
    }


def market_state_id(row: dict) -> str:
    return stable_id(
        "market_state_v1",
        canonical(market_state_payload(row)),
    )


def market_state_row(row: dict) -> dict:
    state_id = market_state_id(row)
    return {
        "market_state_id": state_id,
        **market_state_payload(row),
    }


def market_confirmation_id(
    row: dict,
    state_id: str | None = None,
) -> str:
    state_id = state_id or market_state_id(row)
    return stable_id(
        "market_confirmation_v1",
        state_id,
        row.get("observed_at"),
        row.get("source_updated_at"),
        row.get("contract_id"),
    )


def market_confirmation_row(
    row: dict,
    state_id: str | None = None,
) -> dict:
    state_id = state_id or market_state_id(row)
    return {
        "confirmation_id": market_confirmation_id(row, state_id),
        "market_state_id": state_id,
        "observed_at": row.get("observed_at"),
        "source_updated_at": row.get("source_updated_at"),
        "contract_id": row.get("contract_id"),
        "kickoff_at": row.get("kickoff_at"),
        "legacy_market_observation_id": row.get("observation_id"),
    }


def decision_state_id(
    prediction_observation_id: str,
    market_state_id_value: str,
    bet_side: str,
    edge: object,
) -> str:
    return stable_id(
        "decision_state_v1",
        prediction_observation_id,
        market_state_id_value,
        bet_side,
        edge,
    )


def decision_state_row(
    decision: dict,
    market_row: dict,
) -> dict:
    state_id = market_state_id(market_row)
    decision_id = decision_state_id(
        decision.get("prediction_observation_id"),
        state_id,
        decision.get("bet_side"),
        decision.get("edge"),
    )

    return {
        "decision_state_id": decision_id,
        "prediction_observation_id":
            decision.get("prediction_observation_id"),
        "market_state_id": state_id,
        "canonical_game_id": decision.get("canonical_game_id"),
        "market_type": decision.get("market_type"),
        "checkpoint": decision.get("checkpoint"),
        "bet_side": decision.get("bet_side"),
        "edge": decision.get("edge"),
        "market_provenance": decision.get("market_provenance"),
        "first_observed_at": decision.get("created_at"),
        "legacy_decision_id": decision.get("decision_id"),
        "legacy_market_observation_id":
            decision.get("market_observation_id"),
    }
