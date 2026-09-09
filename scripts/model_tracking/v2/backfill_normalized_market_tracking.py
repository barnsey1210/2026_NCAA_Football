#!/usr/bin/env python3
"""Backfill normalized prospective market tracking from immutable legacy ledgers.

Additive compatibility migration only.

Reads:
- market_observations.jsonl
- decision_observations.jsonl

Writes only with --accept:
- market_states.jsonl
- market_confirmations.jsonl
- decision_states.jsonl

Never modifies, rewrites, truncates, compacts, or deletes legacy tracking data.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from immutable_tracking import append_unique
from market_identity import (
    decision_confirmation_row,
    decision_state_row,
    market_confirmation_row,
    market_state_row,
)


def parse_dt(value):
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []

    return [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def earliest_row(existing: dict, candidate: dict, field: str) -> dict:
    a = parse_dt(existing.get(field))
    b = parse_dt(candidate.get(field))

    if a is None and b is None:
        return existing
    if a is None:
        return candidate
    if b is None:
        return existing

    return candidate if b < a else existing


def unique_market_states(markets: list[dict]) -> list[dict]:
    rows = {}

    for market in markets:
        row = market_state_row(market)
        key = row["market_state_id"]

        if key not in rows:
            rows[key] = row
            continue

        if rows[key] != row:
            raise RuntimeError(
                f"market_state_id collision with conflicting payload: {key}"
            )

    return list(rows.values())


def unique_market_confirmations(markets: list[dict]) -> list[dict]:
    rows = {}

    for market in markets:
        state = market_state_row(market)
        row = market_confirmation_row(
            market,
            state["market_state_id"],
        )
        key = row["confirmation_id"]

        if key not in rows:
            rows[key] = row
        else:
            # Same provider evidence may have been polled repeatedly.
            # Preserve the earliest time that exact evidence was observed.
            rows[key] = earliest_row(
                rows[key],
                row,
                "observed_at",
            )

    return list(rows.values())


def unique_decision_confirmations(
    decisions: list[dict],
    markets_by_id: dict[str, dict],
) -> tuple[list[dict], int]:
    rows = {}
    unresolved = 0

    for decision in decisions:
        market = markets_by_id.get(
            decision.get("market_observation_id")
        )

        if market is None:
            unresolved += 1
            continue

        state = decision_state_row(decision, market)
        row = decision_confirmation_row(
            decision,
            market,
            state["decision_state_id"],
        )
        key = row["confirmation_id"]

        if key not in rows:
            rows[key] = row
        else:
            rows[key] = earliest_row(
                rows[key],
                row,
                "created_at",
            )

    return list(rows.values()), unresolved


def unique_decision_states(
    decisions: list[dict],
    markets_by_id: dict[str, dict],
) -> tuple[list[dict], int]:
    rows = {}
    unresolved = 0

    for decision in decisions:
        market = markets_by_id.get(
            decision.get("market_observation_id")
        )

        if market is None:
            unresolved += 1
            continue

        row = decision_state_row(decision, market)
        key = row["decision_state_id"]

        if key not in rows:
            rows[key] = row
        else:
            # Preserve earliest known occurrence of this material decision.
            rows[key] = earliest_row(
                rows[key],
                row,
                "first_observed_at",
            )

    return list(rows.values()), unresolved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runtime-root",
        default=str(Path(__file__).resolve().parents[3]),
        help="Repository/runtime root containing data/model_tracking/v2",
    )
    parser.add_argument(
        "--accept",
        action="store_true",
        help="Append missing normalized rows. Default is preview only.",
    )
    args = parser.parse_args()

    runtime_root = Path(args.runtime_root).resolve()
    data_dir = runtime_root / "data/model_tracking/v2"

    market_path = data_dir / "market_observations.jsonl"
    decision_path = data_dir / "decision_observations.jsonl"

    markets = load_jsonl(market_path)
    decisions = load_jsonl(decision_path)

    markets_by_id = {
        row["observation_id"]: row
        for row in markets
    }

    states = unique_market_states(markets)
    confirmations = unique_market_confirmations(markets)
    decision_states, unresolved = unique_decision_states(
        decisions,
        markets_by_id,
    )

    decision_confirmations, unresolved_confirmations = (
        unique_decision_confirmations(
            decisions,
            markets_by_id,
        )
    )

    if unresolved != unresolved_confirmations:
        raise RuntimeError(
            "decision state/confirmation reference counts disagree"
        )

    if unresolved:
        raise RuntimeError(
            f"{unresolved} legacy decisions reference missing market observations"
        )

    report = {
        "schema_version": "normalized-market-backfill-v1",
        "runtime_root": str(runtime_root),
        "accept_requested": args.accept,
        "legacy": {
            "market_observations": len(markets),
            "decision_observations": len(decisions),
        },
        "normalized_from_legacy": {
            "unique_market_states": len(states),
            "unique_market_confirmations": len(confirmations),
            "unique_decision_states": len(decision_states),
            "unique_decision_confirmations":
                len(decision_confirmations),
            "unresolved_market_references": unresolved,
        },
        "market_states": append_unique(
            data_dir / "market_states.jsonl",
            states,
            "market_state_id",
            args.accept,
        ),
        "market_confirmations": append_unique(
            data_dir / "market_confirmations.jsonl",
            confirmations,
            "confirmation_id",
            args.accept,
        ),
        "decision_states": append_unique(
            data_dir / "decision_states.jsonl",
            decision_states,
            "decision_state_id",
            args.accept,
        ),
        "decision_confirmations": append_unique(
            data_dir / "decision_confirmations.jsonl",
            decision_confirmations,
            "confirmation_id",
            args.accept,
        ),
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
