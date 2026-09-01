#!/usr/bin/env python3
"""Offline 2026 Week 1 -> Week 2 War Room operational rehearsal."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from lifecycle import Event, LifecycleReducer, canonical_json, reduce_events


ROOT = Path(__file__).resolve().parents[3]
SCHEDULE = ROOT / "data/snapshots/preseason/preseason_db.json"
PROJECTIONS = ROOT / "data/site/current_game_projection_contract.json"
MATRIX = ROOT / "data/site/war_room_market_matrix.json"
HEALTH = ROOT / "data/site/war_room_health.json"
CYCLE_ID = "2026_WK2_PREP"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def make_event(
    event_id: str,
    event_type: str,
    timestamp: str,
    entity_id: str,
    payload: dict | None = None,
    source: str = "offline_weekend_fixture",
) -> Event:
    return Event(
        event_id=event_id,
        event_type=event_type,
        timestamp=timestamp,
        cycle_id=CYCLE_ID,
        entity_id=str(entity_id),
        payload=payload or {},
        source=source,
    )


def select_games(schedule: dict, matrix: dict) -> tuple[list[dict], dict]:
    matrix_by_id = {str(g.get("game_id")): g for g in matrix.get("games", [])}

    def fbs_vs_fbs(game: dict) -> bool:
        scope = matrix_by_id.get(str(game.get("game_id")), {}).get("scope") or {}
        return scope.get("fbs_vs_fbs") is True

    week_one = [
        g
        for g in schedule.get("games", [])
        if int(g.get("week", -1)) == 1 and fbs_vs_fbs(g)
    ]
    week_two = [
        g
        for g in schedule.get("games", [])
        if int(g.get("week", -1)) == 2 and fbs_vs_fbs(g)
    ]
    if len(week_one) < 3 or not week_two:
        raise ValueError("Current artifacts lack the required Week 1/Week 2 FBS universe")
    return week_one[:3], week_two[0]


def build_rehearsal_events(source_games: list[dict], target: dict) -> list[Event]:
    target_id = str(target["game_id"])
    events: list[Event] = []

    # Existing same-identity Shadow value is visible but explicitly stale.
    events.append(make_event("e001", "AUTHORITY_CHANGED", "2026-09-05T15:55:00Z", target_id, {
        "domain": "spread", "authority": "SHADOW",
        "model_id": "shadow_spread_sp_sagarin_v1", "selected_value": -3.0,
        "value_state": "STALE", "updated_sources": [],
        "updated_source_count": 0, "required_source_count": 4,
        "fixture_value": True,
    }, "authority_owner_fixture"))
    events.append(make_event("e002", "AUTHORITY_CHANGED", "2026-09-05T15:56:00Z", target_id, {
        "domain": "total", "authority": "SHADOW",
        "model_id": "shadow_total_enhanced_spplus_od_v1", "selected_value": 52.0,
        "value_state": "STALE", "updated_sources": [],
        "updated_source_count": 0, "required_source_count": 3,
        "fixture_value": True,
    }, "authority_owner_fixture"))

    for index, game in enumerate(source_games, start=3):
        events.append(make_event(
            f"e{index:03d}", "GAME_ACTIVE", f"2026-09-05T{16 + index - 3:02d}:00:00Z",
            game["game_id"], {"source_week": 1, "target_week": 2}, "cfbd_tier2_fixture",
        ))

    final_events = []
    final_times = ["20:00:00", "20:30:00", "20:45:00"]
    for offset, game in enumerate(source_games):
        event = make_event(
            f"e{6 + offset:03d}", "GAME_FINAL", f"2026-09-05T{final_times[offset]}Z",
            game["game_id"], {
                "source_week": 1, "target_week": 2,
                "away_team": game.get("away_team"), "home_team": game.get("home_team"),
                "final_score": {"away": 20 + offset, "home": 27 + offset},
                "cfbd_tier": 2, "fixture_score": True,
            }, "cfbd_tier2_fixture",
        )
        final_events.append(event)
        events.append(event)

    delayed_task_id = LifecycleReducer.task_id(
        final_events[0], "RUN_POSTGAME_PROCESSING", str(source_games[0]["game_id"])
    )
    events.extend([
        make_event("e009", "TASK_FAILED", "2026-09-05T20:05:00Z", delayed_task_id, {
            "task_id": delayed_task_id, "reason": "CFBD postgame payload not yet complete",
            "retryable": True,
        }, "postgame_task_fixture"),
        # Market deliberately arrives before POSTGAME_READY/SHADOW_READY.
        make_event("e010", "MARKET_FIRST_SEEN", "2026-09-05T20:10:00Z", target_id, {
            "market": "spread,total", "book": "DraftKings",
            "spread_home": -2.5, "total": 51.5,
            "comparison_model_spread": "shadow_spread_sp_sagarin_v1",
            "comparison_value_state": "STALE", "fixture_quote": True,
        }, "the_odds_api_fixture"),
        make_event("e011", "TASK_RETRY", "2026-09-05T20:20:00Z", delayed_task_id, {
            "task_id": delayed_task_id,
        }, "postgame_task_fixture"),
        make_event("e012", "POSTGAME_READY", "2026-09-05T21:00:00Z", source_games[0]["game_id"], {
            "cfbd_inputs": ["plays", "drives", "havoc", "advanced_game_statistics"],
            "fixture_only": True,
        }, "postgame_fixture"),
        make_event("e013", "TASK_COMPLETED", "2026-09-05T21:01:00Z", delayed_task_id, {
            "task_id": delayed_task_id,
        }, "postgame_task_fixture"),
        make_event("e014", "POSTGAME_READY", "2026-09-05T21:10:00Z", source_games[1]["game_id"], {"fixture_only": True}, "postgame_fixture"),
        make_event("e015", "SHADOW_PARTIAL", "2026-09-05T21:15:00Z", target_id, {
            "models": {"spread": "shadow_spread_sp_sagarin_v1"},
            "values": {"spread": -3.25}, "missing_components": ["second_team_postgame_state"],
            "fixture_value": True,
        }, "shadow_projection_fixture"),
        make_event("e016", "POSTGAME_READY", "2026-09-05T21:30:00Z", source_games[2]["game_id"], {"fixture_only": True}, "postgame_fixture"),
        make_event("e017", "SHADOW_READY", "2026-09-05T22:00:00Z", target_id, {
            "models": {"spread": "shadow_spread_sp_sagarin_v1", "total": "shadow_total_enhanced_spplus_od_v1"},
            "values": {"spread": -3.5, "total": 52.5}, "fixture_value": True,
        }, "shadow_projection_fixture"),
        make_event("e018", "MARKET_QUOTE_ACCEPTED", "2026-09-05T23:00:00Z", target_id, {
            "market": "spread,total", "book": "FanDuel",
            "spread_home": -3.0, "total": 52.0, "fixture_quote": True,
        }, "the_odds_api_fixture"),
    ])

    # Sunday checks: unchanged/rejected checks request no projection rebuild.
    events.extend([
        make_event("e019", "RATING_SOURCE_CHECKED", "2026-09-06T09:00:00Z", "TeamRankings", {
            "provider": "TeamRankings", "result": "UNCHANGED", "version": "tr-baseline",
        }, "ratings_acceptance_fixture"),
        make_event("e020", "RATING_SOURCE_REJECTED", "2026-09-06T09:05:00Z", "DRatings", {
            "provider": "DRatings", "candidate_version": "dr-invalid-v2",
            "reason": "coverage validation failed",
        }, "ratings_acceptance_fixture"),
        make_event("e021", "RATING_SOURCE_UPDATED", "2026-09-06T09:10:00Z", "SP+", {
            "provider": "SP+", "version": "sp-v2",
        }, "ratings_acceptance_fixture"),
        make_event("e022", "RATING_SOURCE_UPDATED", "2026-09-06T09:20:00Z", "FPI", {
            "provider": "FPI", "version": "fpi-v2",
        }, "ratings_acceptance_fixture"),
        make_event("e023", "AUTHORITY_CHANGED", "2026-09-06T09:21:00Z", target_id, {
            "domain": "spread", "authority": "HYBRID",
            "model_id": "hybrid_spread_updated_sources_v1", "selected_value": -4.0,
            "value_state": "CURRENT", "updated_sources": ["SP+", "FPI"],
            "updated_source_count": 2, "required_source_count": 4,
            "weights_used": {"SP+": 0.5, "FPI": 0.5}, "fixture_value": True,
        }, "authority_owner_fixture"),
        make_event("e024", "RATING_SOURCE_UPDATED", "2026-09-06T09:25:00Z", "SP+ Total", {
            "provider": "SP+ Total", "version": "sp-total-v2",
        }, "ratings_acceptance_fixture"),
        make_event("e025", "RATING_SOURCE_UPDATED", "2026-09-06T09:35:00Z", "Massey Dual", {
            "provider": "Massey Dual", "version": "massey-v2",
        }, "ratings_acceptance_fixture"),
        make_event("e026", "AUTHORITY_CHANGED", "2026-09-06T09:36:00Z", target_id, {
            "domain": "total", "authority": "HYBRID",
            "model_id": "hybrid_total_updated_sources_v1", "selected_value": 53.0,
            "value_state": "CURRENT", "updated_sources": ["SP+ Total", "Massey Dual"],
            "updated_source_count": 2, "required_source_count": 3,
            "weights_used": {"SP+ Total": 0.5, "Massey Dual": 0.5}, "fixture_value": True,
        }, "authority_owner_fixture"),
        # Same-identity carry-forward is explicit and labeled.
        make_event("e027", "AUTHORITY_CHANGED", "2026-09-06T09:45:00Z", target_id, {
            "domain": "spread", "authority": "HYBRID",
            "model_id": "hybrid_spread_updated_sources_v1", "selected_value": None,
            "preserve_last_valid": True, "updated_sources": ["SP+", "FPI"],
            "updated_source_count": 2, "required_source_count": 4,
        }, "authority_owner_fixture"),
        # Accepted correction is a new immutable provider version.
        make_event("e028", "PROVIDER_PANEL_CHANGED", "2026-09-06T10:00:00Z", "SP+", {
            "provider": "SP+", "version": "sp-v3-correction", "correction_of": "sp-v2",
        }, "ratings_acceptance_fixture"),
    ])

    for number, provider, minute in [
        (29, "TeamRankings", 10), (31, "DRatings", 30)
    ]:
        events.append(make_event(f"e{number:03d}", "RATING_SOURCE_UPDATED", f"2026-09-06T10:{minute:02d}:00Z", provider, {
            "provider": provider, "version": f"{provider.lower().replace(' ', '-')}-accepted-v2",
        }, "ratings_acceptance_fixture"))

    events.extend([
        make_event("e032", "OFFICIAL_PROJECTION_READY", "2026-09-06T10:35:00Z", target_id, {
            "models": {"spread": "standard_spread_4src_equal_v1"},
            "values": {"spread": -4.25}, "fixture_value": True,
        }, "projection_contract_fixture"),
        make_event("e033", "AUTHORITY_CHANGED", "2026-09-06T10:36:00Z", target_id, {
            "domain": "spread", "authority": "OFFICIAL",
            "model_id": "standard_spread_4src_equal_v1", "selected_value": -4.25,
            "value_state": "CURRENT",
            "updated_sources": ["SP+", "FPI", "TeamRankings", "DRatings"],
            "updated_source_count": 4, "required_source_count": 4, "fixture_value": True,
        }, "authority_owner_fixture"),
        make_event("e034", "RATING_SOURCE_UPDATED", "2026-09-06T10:40:00Z", "DRatings Total", {
            "provider": "DRatings Total", "version": "dratings-total-v2",
        }, "ratings_acceptance_fixture"),
        make_event("e035", "OFFICIAL_PROJECTION_READY", "2026-09-06T10:45:00Z", target_id, {
            "models": {"total": "standard_total_sp_massey_dratings_v1"},
            "values": {"total": 53.25}, "fixture_value": True,
        }, "projection_contract_fixture"),
        make_event("e036", "AUTHORITY_CHANGED", "2026-09-06T10:46:00Z", target_id, {
            "domain": "total", "authority": "OFFICIAL",
            "model_id": "standard_total_sp_massey_dratings_v1", "selected_value": 53.25,
            "value_state": "CURRENT",
            "updated_sources": ["SP+ Total", "Massey Dual", "DRatings Total"],
            "updated_source_count": 3, "required_source_count": 3, "fixture_value": True,
        }, "authority_owner_fixture"),
        make_event("e037", "BUILD_COMPLETED", "2026-09-06T11:00:00Z", "war-room-fast-build", {
            "artifacts": ["war-room.html", "war_room_health.json", "war_room_market_matrix.json"],
            "simulation_only": True,
        }, "fast_publication_fixture"),
        make_event("e038", "VALIDATION_PASSED", "2026-09-06T11:01:00Z", "war-room-fast-build", {
            "simulation_only": True,
        }, "validation_fixture"),
    ])

    # Deliberate duplicate and out-of-order input exercise.
    return [events[17], events[9], *reversed(events), events[5]]


def seconds_between(events: list[Event], start_id: str, end_id: str) -> int:
    by_id = {event.event_id: event for event in events}
    start = datetime.fromisoformat(by_id[start_id].timestamp.replace("Z", "+00:00"))
    end = datetime.fromisoformat(by_id[end_id].timestamp.replace("Z", "+00:00"))
    return int((end - start).total_seconds())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    schedule, projection, matrix, health = map(load, (SCHEDULE, PROJECTIONS, MATRIX, HEALTH))
    source_games, target = select_games(schedule, matrix)
    events = build_rehearsal_events(source_games, target)
    state = reduce_events(events)
    replay = reduce_events(list(reversed(events)))
    assert canonical_json(state) == canonical_json(replay)
    assert state["cycles"][CYCLE_ID]["created_by_event_id"] == "e006"
    assert state["authorities"]["spread"]["state"] == "OFFICIAL"
    assert state["authorities"]["total"]["state"] == "OFFICIAL"
    assert state["publications"] == {}

    ordered_unique = []
    seen = set()
    for event in LifecycleReducer.ordered(events):
        if event.event_id not in seen:
            ordered_unique.append(event)
            seen.add(event.event_id)

    latencies = {
        "first_final_to_postgame_ready_seconds": seconds_between(ordered_unique, "e006", "e012"),
        "first_final_to_shadow_ready_seconds": seconds_between(ordered_unique, "e006", "e017"),
        "first_final_to_market_first_seen_seconds": seconds_between(ordered_unique, "e006", "e010"),
        "first_final_to_spread_hybrid_seconds": seconds_between(ordered_unique, "e006", "e023"),
        "first_final_to_spread_official_seconds": seconds_between(ordered_unique, "e006", "e033"),
        "first_final_to_validation_seconds": seconds_between(ordered_unique, "e006", "e038"),
    }

    print("WEEK 1 -> WEEK 2 OPERATIONAL REHEARSAL: PASS")
    print(f"Source games: {', '.join(str(g['game_id']) for g in source_games)}")
    print(f"Target: {target['game_id']} | {target.get('away_team')} at {target.get('home_team')}")
    print(f"Projection artifact: {projection.get('built_at')}")
    print(f"Matrix artifact: {matrix.get('built_at')} | health={health.get('built_at')}")
    print("\nEVENT TIMELINE")
    for event in ordered_unique:
        print(f"{event.timestamp} | {event.event_id} | {event.event_type} | {event.entity_id}")
    print("\nAUTHORITY TRANSITIONS")
    for row in state["authority_transitions"]:
        print(f"{row['timestamp']} | {row['domain']} | {row['prior_authority']} -> {row['authority']} | {row['model_id']} | {row['value_state']} | {row['selected_value']}")
    print("\nTASK REQUESTS")
    for task in state["tasks"].values():
        print(f"{task['requested_at']} | {task['task_type']} | {task['entity_id']} | {task['status']} | attempts={task['attempts']}")
    print("\nFAILURES / RETRIES")
    failed = [task for task in state["tasks"].values() if task.get("attempt_history")]
    for task in failed:
        print(f"{task['task_id']} | {json.dumps(task['attempt_history'], sort_keys=True)}")
    print("\nLATENCY TIMESTAMPS")
    for name, value in latencies.items():
        print(f"{name}={value}")
    print("\nFINAL REDUCER STATE")
    print(json.dumps({
        "cycle": state["cycles"][CYCLE_ID],
        "spread_authority": state["authorities"]["spread"],
        "total_authority": state["authorities"]["total"],
        "market": state["markets"][str(target["game_id"])],
        "providers": state["providers"],
        "build": state["builds"].get("war-room-fast-build"),
        "ignored_duplicate_event_ids": state["ignored_duplicate_event_ids"],
    }, indent=2, sort_keys=True))
    print("\nProduction actions executed: 0")
    print("Provider/API calls: 0")
    print("Production publication occurred: NO")

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "events.json").write_text(json.dumps([asdict(e) for e in ordered_unique], indent=2) + "\n")
        (args.output_dir / "state.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        (args.output_dir / "latencies.json").write_text(json.dumps(latencies, indent=2, sort_keys=True) + "\n")
        print(f"Isolated simulation output: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
