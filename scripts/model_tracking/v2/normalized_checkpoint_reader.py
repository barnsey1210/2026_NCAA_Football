#!/usr/bin/env python3
"""Read normalized market/decision tracking for checkpoint shadow parity.

This module is read-only. It does not write tracking data and does not
replace the legacy checkpoint path by itself.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from immutable_tracking import stable_id


def load_jsonl(path: Path) -> list[dict]:
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
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def expected_market_confirmation_id(row: dict) -> str:
    evidence_timestamp = (
        row.get("source_updated_at")
        or row.get("observed_at")
    )

    return stable_id(
        "market_confirmation_v1",
        row.get("market_state_id"),
        evidence_timestamp,
    )


def is_canonical_market_confirmation(row: dict) -> bool:
    return (
        row.get("confirmation_id")
        == expected_market_confirmation_id(row)
    )


def build_normalized_context(data_dir: Path) -> dict:
    market_states = {
        row["market_state_id"]: row
        for row in load_jsonl(
            data_dir / "market_states.jsonl"
        )
    }

    all_market_confirmations = load_jsonl(
        data_dir / "market_confirmations.jsonl"
    )

    market_confirmations = [
        row
        for row in all_market_confirmations
        if is_canonical_market_confirmation(row)
    ]

    decision_states = {
        row["decision_state_id"]: row
        for row in load_jsonl(
            data_dir / "decision_states.jsonl"
        )
    }

    decision_confirmations = load_jsonl(
        data_dir / "decision_confirmations.jsonl"
    )

    markets = []
    markets_by_confirmation = {}
    markets_by_game = defaultdict(list)

    unresolved_market_states = 0

    for confirmation in market_confirmations:
        state = market_states.get(
            confirmation.get("market_state_id")
        )

        if state is None:
            unresolved_market_states += 1
            continue

        row = {
            **state,
            "observation_id":
                confirmation["confirmation_id"],
            "observed_at":
                confirmation.get("observed_at"),
            "source_updated_at":
                confirmation.get("source_updated_at"),
            "kickoff_at":
                confirmation.get("kickoff_at"),
            "contract_id":
                confirmation.get("contract_id"),
            "market_confirmation_id":
                confirmation["confirmation_id"],
            "legacy_market_observation_id":
                confirmation.get(
                    "legacy_market_observation_id"
                ),
        }

        markets.append(row)
        markets_by_confirmation[
            confirmation["confirmation_id"]
        ] = row

        markets_by_game[
            row.get("canonical_game_id")
        ].append(row)

    return {
        "market_states": market_states,
        "market_confirmations":
            market_confirmations,
        "all_market_confirmations":
            all_market_confirmations,
        "markets": markets,
        "markets_by_confirmation":
            markets_by_confirmation,
        "markets_by_game":
            markets_by_game,
        "decision_states":
            decision_states,
        "decision_confirmations":
            decision_confirmations,
        "unresolved_market_states":
            unresolved_market_states,
        "superseded_market_confirmations":
            len(all_market_confirmations)
            - len(market_confirmations),
    }


def choose_reference_fallback(
    context: dict,
    prediction_id: str,
    cutoff,
):
    candidates = []

    for confirmation in context[
        "decision_confirmations"
    ]:
        state = context["decision_states"].get(
            confirmation.get("decision_state_id")
        )

        if state is None:
            continue

        if (
            state.get("prediction_observation_id")
            != prediction_id
        ):
            continue

        stamp = parse_dt(
            confirmation.get("created_at")
        )

        if stamp is None or stamp > cutoff:
            continue

        market = context[
            "markets_by_confirmation"
        ].get(
            confirmation.get(
                "market_confirmation_id"
            )
        )

        if market is None:
            continue

        if market.get("line") is None:
            continue

        candidates.append(
            (
                stamp,
                state,
                confirmation,
                market,
            )
        )

    if not candidates:
        return None, None, None

    _, state, confirmation, market = max(
        candidates,
        key=lambda x: x[0],
    )

    decision = {
        **state,
        "decision_id":
            confirmation.get("legacy_decision_id"),
        "created_at":
            confirmation.get("created_at"),
        "decision_confirmation_id":
            confirmation.get("confirmation_id"),
    }

    return (
        market,
        decision,
        "CANONICAL_REFERENCE_FALLBACK",
    )


def semantic_market(row):
    if row is None:
        return None

    return (
        row.get("canonical_game_id"),
        row.get("market_type"),
        row.get("sportsbook"),
        row.get("side"),
        row.get("line"),
        row.get("price"),
        row.get("source"),
        row.get("freshness_status"),
        row.get("lifecycle_state"),
        row.get("observed_at"),
        row.get("source_updated_at"),
    )
