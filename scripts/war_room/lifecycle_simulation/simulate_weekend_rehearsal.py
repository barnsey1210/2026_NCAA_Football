#!/usr/bin/env python3
"""Offline upcoming-2026 War Room weekend lifecycle rehearsal."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lifecycle import Event, canonical_json, reduce_events


ROOT = Path(__file__).resolve().parents[3]
SCHEDULE = ROOT / "data/snapshots/preseason/preseason_db.json"
PROJECTIONS = ROOT / "data/site/current_game_projection_contract.json"
MATRIX = ROOT / "data/site/war_room_market_matrix.json"
HEALTH = ROOT / "data/site/war_room_health.json"
MARKET = ROOT / "data/site/current_market_contract.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--max-games", type=int, default=2)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def make_event(index, event_type, cycle_id, entity_id, payload, source):
    timestamp = datetime(2026, 8, 30, tzinfo=timezone.utc) + timedelta(minutes=index)
    return Event(
        event_id=f"rehearsal-{index:03d}-{event_type.lower()}",
        event_type=event_type,
        timestamp=timestamp.isoformat().replace("+00:00", "Z"),
        cycle_id=cycle_id,
        entity_id=str(entity_id),
        payload=payload,
        source=source,
    )


def main() -> int:
    args = parse_args()
    schedule = load(SCHEDULE)
    projection = load(PROJECTIONS)
    matrix = load(MATRIX)
    health = load(HEALTH)
    market = load(MARKET)

    matrix_by_id = {str(g.get("game_id")): g for g in matrix.get("games", [])}

    def is_fbs_vs_fbs(game_id):
        scope = matrix_by_id.get(str(game_id), {}).get("scope") or {}
        return scope.get("fbs_vs_fbs") is True

    source_games = [
        g
        for g in schedule.get("games", [])
        if int(g.get("week")) == args.week and is_fbs_vs_fbs(g.get("game_id"))
    ]
    if not source_games:
        raise SystemExit(f"No 2026 schedule games found for week {args.week}")
    source_games = source_games[: max(1, args.max_games)]
    target_week = args.week + 1
    cycle_id = f"2026_WK{target_week}_PREP"

    projection_by_id = {str(g.get("game_id")): g for g in projection.get("games", [])}
    target_games = [g for g in projection.get("games", []) if int(g.get("week")) == target_week]
    target = next((g for g in target_games if is_fbs_vs_fbs(g.get("game_id"))), None)
    if not target:
        raise SystemExit(f"No target games found for week {target_week}")
    target_id = str(target["game_id"])
    matrix_target = matrix_by_id.get(target_id, {})

    events = []
    index = 1
    for game in source_games:
        events.append(
            make_event(
                index,
                "GAME_FINAL",
                cycle_id,
                game["game_id"],
                {
                    "source_week": args.week,
                    "target_week": target_week,
                    "away_team": game.get("away_team"),
                    "home_team": game.get("home_team"),
                    "final_score": {"away": 24 + index, "home": 27 + index},
                    "simulation_only": True,
                },
                "preseason_db_schedule_fixture",
            )
        )
        index += 1
        events.append(make_event(index, "POSTGAME_READY", cycle_id, game["game_id"], {"simulation_only": True}, "postgame_fixture"))
        index += 1

    # Values are explicit simulation fixture outputs. They are not calculated
    # by the reducer and are never written into production artifacts.
    shadow_values = {"spread": -3.5, "total": 52.5}
    events.append(
        make_event(
            index,
            "SHADOW_READY",
            cycle_id,
            target_id,
            {
                "models": {
                    "spread": "shadow_spread_sp_sagarin_v1",
                    "total": "shadow_total_enhanced_spplus_od_v1",
                },
                "values": shadow_values,
                "simulation_only": True,
                "numeric_values_are_fixture_only": True,
            },
            "shadow_projection_fixture",
        )
    )
    index += 1

    market_payload = {
        "captured_at": matrix.get("fast_market_refresh", {}).get("pull_completed_at"),
        "market": matrix_target.get("market") or {},
        "current_market_contract_built_at": market.get("built_at"),
        "simulation_only": True,
    }
    events.append(make_event(index, "MARKET_FIRST_SEEN", cycle_id, target_id, market_payload, "current_market_artifact"))
    index += 1

    for provider in ["SP+", "FPI"]:
        events.append(make_event(index, "RATING_SOURCE_UPDATED", cycle_id, provider, {"provider": provider, "version": f"simulated-{cycle_id}-{provider}", "simulation_only": True}, "rating_acceptance_fixture"))
        index += 1
    events.append(
        make_event(
            index,
            "AUTHORITY_CHANGED",
            cycle_id,
            target_id,
            {
                "domain": "spread",
                "authority": "HYBRID",
                "model_id": "hybrid_spread_updated_sources_v1",
                "selected_value": -4.0,
                "value_state": "CURRENT",
                "updated_sources": ["SP+", "FPI"],
                "updated_source_count": 2,
                "required_source_count": 4,
                "weights_used": {"SP+": 0.5, "FPI": 0.5},
                "simulation_only": True,
            },
            "authority_fixture_not_reducer_calculation",
        )
    )
    index += 1

    for provider in ["TeamRankings", "DRatings"]:
        events.append(make_event(index, "RATING_SOURCE_UPDATED", cycle_id, provider, {"provider": provider, "version": f"simulated-{cycle_id}-{provider}", "simulation_only": True}, "rating_acceptance_fixture"))
        index += 1
    events.append(
        make_event(
            index,
            "OFFICIAL_PROJECTION_READY",
            cycle_id,
            target_id,
            {
                "models": {"spread": "standard_spread_4src_equal_v1"},
                "values": {"spread": -4.25},
                "simulation_only": True,
            },
            "projection_contract_fixture",
        )
    )
    index += 1
    events.append(
        make_event(
            index,
            "AUTHORITY_CHANGED",
            cycle_id,
            target_id,
            {
                "domain": "spread",
                "authority": "OFFICIAL",
                "model_id": "standard_spread_4src_equal_v1",
                "selected_value": -4.25,
                "value_state": "CURRENT",
                "updated_sources": ["SP+", "FPI", "TeamRankings", "DRatings"],
                "updated_source_count": 4,
                "required_source_count": 4,
                "simulation_only": True,
            },
            "authority_fixture_not_reducer_calculation",
        )
    )
    index += 1

    # Total transitions are independent and explicitly supplied.
    for provider in ["SP+ Total", "Massey Dual"]:
        events.append(make_event(index, "RATING_SOURCE_UPDATED", cycle_id, provider, {"provider": provider, "version": f"simulated-{cycle_id}-{provider}", "simulation_only": True}, "rating_acceptance_fixture"))
        index += 1
    events.append(make_event(index, "AUTHORITY_CHANGED", cycle_id, target_id, {"domain": "total", "authority": "HYBRID", "model_id": "hybrid_total_updated_sources_v1", "selected_value": 53.0, "value_state": "CURRENT", "updated_sources": ["SP+ Total", "Massey Dual"], "updated_source_count": 2, "required_source_count": 3, "weights_used": {"SP+ Total": 0.5, "Massey Dual": 0.5}, "simulation_only": True}, "authority_fixture_not_reducer_calculation"))
    index += 1
    events.append(make_event(index, "RATING_SOURCE_UPDATED", cycle_id, "DRatings Total", {"provider": "DRatings Total", "version": f"simulated-{cycle_id}-DRatings-Total", "simulation_only": True}, "rating_acceptance_fixture"))
    index += 1
    events.append(make_event(index, "OFFICIAL_PROJECTION_READY", cycle_id, target_id, {"models": {"total": "standard_total_sp_massey_dratings_v1"}, "values": {"total": 53.25}, "simulation_only": True}, "projection_contract_fixture"))
    index += 1
    events.append(make_event(index, "AUTHORITY_CHANGED", cycle_id, target_id, {"domain": "total", "authority": "OFFICIAL", "model_id": "standard_total_sp_massey_dratings_v1", "selected_value": 53.25, "value_state": "CURRENT", "updated_sources": ["SP+ Total", "Massey Dual", "DRatings Total"], "updated_source_count": 3, "required_source_count": 3, "simulation_only": True}, "authority_fixture_not_reducer_calculation"))
    index += 1

    events.append(make_event(index, "BUILD_COMPLETED", cycle_id, "war-room-build-sim", {"artifacts": ["war-room.html", "war_room_health.json", "war_room_market_matrix.json"], "simulation_only": True}, "public_build_fixture"))
    index += 1
    events.append(make_event(index, "VALIDATION_PASSED", cycle_id, "war-room-build-sim", {"simulation_only": True}, "validation_fixture"))
    index += 1
    events.append(make_event(index, "MARKET_CLOSE", cycle_id, target_id, {"simulation_only": True, "close_rule": "fixture_pre_kick_close"}, "market_history_fixture"))

    state = reduce_events(events)
    replay = reduce_events(list(reversed(events)))
    assert canonical_json(state) == canonical_json(replay)
    assert state["authorities"]["spread"]["state"] == "OFFICIAL"
    assert state["authorities"]["total"]["state"] == "OFFICIAL"
    assert state["markets"][target_id]["first_seen_at"]
    assert state["markets"][target_id]["state"] == "CLOSED"
    assert all(task.get("simulation_only") for task in state["tasks"].values())

    print("PHASE 1B UPCOMING 2026 WEEKEND REHEARSAL: PASS")
    print(f"Cycle: {cycle_id}")
    source_week_fbs_games = [
        g
        for g in schedule["games"]
        if int(g.get("week")) == args.week and is_fbs_vs_fbs(g.get("game_id"))
    ]
    print(f"Source week FBS-vs-FBS games simulated final: {len(source_games)} of {len(source_week_fbs_games)}")
    print(f"Target game: {target_id} | {target.get('away_team')} at {target.get('home_team')}")
    print(f"Projection artifact state: {projection.get('built_at')} | game present={target_id in projection_by_id}")
    print(f"War Room artifact state: {matrix.get('built_at')} | health={health.get('built_at')}")
    print(f"First market timestamp captured: {state['markets'][target_id]['first_seen_at']}")
    print(f"SPREAD MODEL: {state['authorities']['spread']['model_id']} | authority={state['authorities']['spread']['state']} | value={state['authorities']['spread']['selected_value']}")
    print(f"TOTAL MODEL: {state['authorities']['total']['model_id']} | authority={state['authorities']['total']['state']} | value={state['authorities']['total']['selected_value']}")
    print(f"Edge projection sources: spread={state['authorities']['spread']['edge_projection_source']} total={state['authorities']['total']['edge_projection_source']}")
    print(f"Simulated task requests: {len(state['tasks'])}")
    for task in state["tasks"].values():
        print(f"  {task['task_type']} | {task['entity_id']} | {task['status']}")
    print("Production actions executed: 0")
    print("Provider/API calls: 0")
    print("Publication attempted: no")

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "events.json").write_text(json.dumps([event.__dict__ for event in events], indent=2) + "\n", encoding="utf-8")
        (args.output_dir / "state.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Simulation outputs: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
