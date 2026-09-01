#!/usr/bin/env python3
"""Run the locked Phase 1A lifecycle scenarios without production actions."""

from __future__ import annotations

import json
from dataclasses import asdict

from lifecycle import Event, canonical_json, reduce_events


def event(number, event_type, entity="game-1", payload=None):
    return Event(
        event_id=f"event-{number:02d}",
        event_type=event_type,
        timestamp=f"2026-08-30T{number:02d}:00:00Z",
        cycle_id="2026_WK2_PREP",
        entity_id=entity,
        payload=payload or {},
        source="offline_fixture",
    )


def main() -> int:
    base = [
        event(1, "GAME_FINAL", payload={"source_week": 1, "target_week": 2}),
        event(2, "POSTGAME_READY"),
        event(
            3,
            "SHADOW_READY",
            payload={
                "models": {"spread": "shadow_spread_sp_sagarin_v1", "total": "shadow_total_enhanced_spplus_od_v1"},
                "values": {"spread": -3.5, "total": 52.5},
            },
        ),
    ]
    shadow = reduce_events(base)

    hybrid_events = base + [
        event(4, "RATING_SOURCE_UPDATED", "SP+", {"provider": "SP+", "version": "sp-v2"}),
        event(5, "RATING_SOURCE_UPDATED", "FPI", {"provider": "FPI", "version": "fpi-v2"}),
        event(
            6,
            "AUTHORITY_CHANGED",
            payload={
                "domain": "spread",
                "authority": "HYBRID",
                "model_id": "hybrid_spread_updated_sources_v1",
                "selected_value": -4.0,
                "updated_sources": ["SP+", "FPI"],
                "updated_source_count": 2,
                "required_source_count": 4,
                "weights_used": {"SP+": 0.5, "FPI": 0.5},
            },
        ),
    ]
    hybrid = reduce_events(hybrid_events)

    official_events = hybrid_events + [
        event(7, "RATING_SOURCE_UPDATED", "TeamRankings", {"provider": "TeamRankings", "version": "tr-v2"}),
        event(9, "RATING_SOURCE_UPDATED", "DRatings", {"provider": "DRatings", "version": "dr-v2"}),
        event(
            10,
            "AUTHORITY_CHANGED",
            payload={
                "domain": "spread",
                "authority": "OFFICIAL",
                "model_id": "standard_spread_4src_equal_v1",
                "selected_value": -4.25,
                "updated_sources": ["SP+", "FPI", "TeamRankings", "DRatings"],
                "updated_source_count": 4,
                "required_source_count": 4,
            },
        ),
    ]
    official = reduce_events(official_events)

    carry_events = official_events + [
        event(
            11,
            "AUTHORITY_CHANGED",
            payload={
                "domain": "spread",
                "authority": "OFFICIAL",
                "model_id": "standard_spread_4src_equal_v1",
                "selected_value": None,
                "preserve_last_valid": True,
                "updated_source_count": 4,
                "required_source_count": 4,
            },
        )
    ]
    carry = reduce_events(carry_events)
    replay = reduce_events(carry_events)

    assert shadow["authorities"]["spread"]["state"] == "SHADOW"
    assert hybrid["authorities"]["spread"]["state"] == "HYBRID"
    assert official["authorities"]["spread"]["state"] == "OFFICIAL"
    assert carry["authorities"]["spread"]["value_state"] == "CARRY_FORWARD"
    assert canonical_json(carry) == canonical_json(replay)

    print("PHASE 1A: PASS")
    for name, state in [
        ("Shadow lifecycle", shadow),
        ("Hybrid transition", hybrid),
        ("Official transition", official),
        ("Carry-forward", carry),
        ("Deterministic replay", replay),
    ]:
        spread = state["authorities"]["spread"]
        print(
            f"{name}: authority={spread['state']} "
            f"value_state={spread['value_state']} "
            f"value={spread['selected_value']} tasks={len(state['tasks'])}"
        )
    print("No tasks were executed; no publication was attempted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
