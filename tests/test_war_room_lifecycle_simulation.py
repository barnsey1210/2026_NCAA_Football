import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "scripts/war_room/lifecycle_simulation"
sys.path.insert(0, str(SIM))

from lifecycle import Event, EventLedger, canonical_json, reduce_events  # noqa: E402
from simulate_week1_week2_rehearsal import build_rehearsal_events  # noqa: E402


def event(number, event_type, payload=None, entity="game-1"):
    return Event(
        event_id=f"evt-{number:03d}",
        event_type=event_type,
        timestamp=f"2026-08-30T00:{number:02d}:00Z",
        cycle_id="2026_WK2_PREP",
        entity_id=entity,
        payload=payload or {},
        source="unit_fixture",
    )


class LifecycleSimulationTests(unittest.TestCase):
    def base_events(self):
        return [
            event(1, "GAME_FINAL", {"source_week": 1, "target_week": 2}),
            event(2, "POSTGAME_READY"),
            event(
                3,
                "SHADOW_READY",
                {
                    "models": {
                        "spread": "shadow_spread_sp_sagarin_v1",
                        "total": "shadow_total_enhanced_spplus_od_v1",
                    },
                    "values": {"spread": -3.5, "total": 52.5},
                },
            ),
        ]

    def test_shadow_lifecycle_and_cycle_creation(self):
        state = reduce_events(self.base_events())
        self.assertIn("2026_WK2_PREP", state["cycles"])
        self.assertEqual(state["games"]["game-1"]["state"], "POSTGAME_READY")
        self.assertEqual(state["authorities"]["spread"]["state"], "SHADOW")
        self.assertEqual(state["authorities"]["spread"]["selected_value"], -3.5)
        task_types = {task["task_type"] for task in state["tasks"].values()}
        self.assertIn("RUN_POSTGAME_PROCESSING", task_types)
        self.assertIn("BUILD_SHADOW_PROJECTIONS", task_types)
        self.assertIn("REFRESH_PROJECTION_CONTRACT", task_types)
        self.assertIn("REBUILD_WAR_ROOM", task_types)

    def test_game_active_does_not_open_next_preparation_cycle(self):
        active = event(1, "GAME_ACTIVE")
        state = reduce_events([active])
        cycle = state["cycles"][active.cycle_id]
        self.assertEqual(cycle["status"], "PENDING_FIRST_FINAL")
        self.assertIsNone(cycle["created_at"])

        final = event(2, "GAME_FINAL", {"source_week": 1, "target_week": 2})
        state = reduce_events([active, final])
        cycle = state["cycles"][active.cycle_id]
        self.assertEqual(cycle["status"], "PREPARING")
        self.assertEqual(cycle["created_by_event_id"], final.event_id)

    def test_rating_events_do_not_calculate_authority(self):
        events = self.base_events() + [
            event(4, "RATING_SOURCE_UPDATED", {"provider": "SP+", "version": "v2"}, "SP+"),
            event(5, "RATING_SOURCE_UPDATED", {"provider": "FPI", "version": "v2"}, "FPI"),
        ]
        state = reduce_events(events)
        self.assertEqual(state["authorities"]["spread"]["state"], "SHADOW")

        events.append(
            event(
                6,
                "AUTHORITY_CHANGED",
                {
                    "domain": "spread",
                    "authority": "HYBRID",
                    "model_id": "hybrid_spread_updated_sources_v1",
                    "selected_value": -4.0,
                    "updated_sources": ["SP+", "FPI"],
                    "updated_source_count": 2,
                    "required_source_count": 5,
                    "weights_used": {"SP+": 0.5, "FPI": 0.5},
                },
            )
        )
        state = reduce_events(events)
        self.assertEqual(state["authorities"]["spread"]["state"], "HYBRID")
        self.assertEqual(state["authorities"]["spread"]["edge_projection_source"], "hybrid_spread_updated_sources_v1")

    def test_unchanged_and_rejected_provider_checks_request_no_rebuild(self):
        checked = event(1, "RATING_SOURCE_CHECKED", {
            "provider": "TeamRankings", "result": "UNCHANGED", "version": "baseline"
        }, "TeamRankings")
        rejected = event(2, "RATING_SOURCE_REJECTED", {
            "provider": "DRatings", "candidate_version": "bad-v2", "reason": "coverage"
        }, "DRatings")
        state = reduce_events([checked, rejected])
        self.assertEqual(state["tasks"], {})
        self.assertEqual(state["providers"]["TeamRankings"]["last_check_result"], "UNCHANGED")
        self.assertEqual(state["providers"]["DRatings"]["last_check_result"], "REJECTED")

    def test_provider_correction_preserves_versions_and_requests_rebuild(self):
        events = [
            event(1, "RATING_SOURCE_UPDATED", {"provider": "SP+", "version": "sp-v2"}, "SP+"),
            event(2, "PROVIDER_PANEL_CHANGED", {
                "provider": "SP+", "version": "sp-v3-correction", "correction_of": "sp-v2"
            }, "SP+"),
        ]
        state = reduce_events(events)
        self.assertEqual(state["providers"]["SP+"]["versions"], ["sp-v2", "sp-v3-correction"])
        refreshes = [t for t in state["tasks"].values() if t["task_type"] == "REFRESH_PROJECTION_CONTRACT"]
        self.assertEqual(len(refreshes), 2)

    def test_official_transition_is_consumed_not_calculated(self):
        events = self.base_events() + [
            event(
                4,
                "AUTHORITY_CHANGED",
                {
                    "domain": "spread",
                    "authority": "OFFICIAL",
                    "model_id": "standard_spread_five_source_v1",
                    "selected_value": -4.25,
                    "updated_source_count": 5,
                    "required_source_count": 5,
                },
            )
        ]
        state = reduce_events(events)
        self.assertEqual(state["authorities"]["spread"]["state"], "OFFICIAL")
        self.assertEqual(state["authorities"]["spread"]["selected_value"], -4.25)

    def test_same_identity_carry_forward(self):
        events = self.base_events() + [
            event(
                4,
                "AUTHORITY_CHANGED",
                {
                    "domain": "spread",
                    "authority": "OFFICIAL",
                    "model_id": "standard_spread_five_source_v1",
                    "selected_value": -4.25,
                },
            ),
            event(
                5,
                "AUTHORITY_CHANGED",
                {
                    "domain": "spread",
                    "authority": "OFFICIAL",
                    "model_id": "standard_spread_five_source_v1",
                    "selected_value": None,
                    "preserve_last_valid": True,
                },
            ),
        ]
        state = reduce_events(events)
        spread = state["authorities"]["spread"]
        self.assertEqual(spread["selected_value"], -4.25)
        self.assertEqual(spread["value_state"], "CARRY_FORWARD")

    def test_different_identity_never_carries_forward(self):
        events = self.base_events() + [
            event(
                4,
                "AUTHORITY_CHANGED",
                {
                    "domain": "spread",
                    "authority": "OFFICIAL",
                    "model_id": "standard_spread_five_source_v1",
                    "selected_value": None,
                    "preserve_last_valid": True,
                },
            )
        ]
        state = reduce_events(events)
        self.assertIsNone(state["authorities"]["spread"]["selected_value"])
        self.assertEqual(state["authorities"]["spread"]["value_state"], "UNAVAILABLE")

    def test_duplicate_event_does_not_duplicate_tasks(self):
        events = self.base_events()
        baseline = reduce_events(events)
        duplicate = reduce_events(events + [events[0]])
        self.assertEqual(set(baseline["tasks"]), set(duplicate["tasks"]))
        self.assertEqual(duplicate["ignored_duplicate_event_ids"], [events[0].event_id])

    def test_out_of_order_input_replays_identically(self):
        events = self.base_events()
        self.assertEqual(
            canonical_json(reduce_events(events)),
            canonical_json(reduce_events(reversed(events))),
        )

    def test_ledger_is_append_only_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EventLedger(Path(tmp) / "events.jsonl")
            first = self.base_events()[0]
            self.assertTrue(ledger.append(first))
            self.assertFalse(ledger.append(first))
            self.assertEqual(ledger.read(), [first])

    def test_failed_task_retry_and_completion(self):
        state = reduce_events(self.base_events()[:1])
        task_id = next(iter(state["tasks"]))
        events = self.base_events()[:1] + [
            event(4, "TASK_FAILED", {"task_id": task_id, "reason": "late PBP"}, task_id),
            event(5, "TASK_RETRY", {"task_id": task_id}, task_id),
            event(6, "TASK_COMPLETED", {"task_id": task_id}, task_id),
        ]
        state = reduce_events(events)
        self.assertEqual(state["tasks"][task_id]["status"], "COMPLETED")
        self.assertEqual(state["tasks"][task_id]["attempts"], 1)

    def test_partial_shadow_does_not_become_ready_or_authoritative(self):
        events = self.base_events()[:2] + [
            event(3, "SHADOW_PARTIAL", {"missing_components": ["Sagarin"]})
        ]
        state = reduce_events(events)
        self.assertEqual(state["projections"]["game-1"]["shadow"]["status"], "PARTIAL")
        self.assertIsNone(state["authorities"]["spread"]["selected_value"])

    def test_validation_requests_review_but_never_publishes(self):
        events = [
            event(1, "BUILD_COMPLETED", {"artifacts": ["war-room.html"]}, "build-1"),
            event(2, "VALIDATION_PASSED", {}, "build-1"),
        ]
        state = reduce_events(events)
        task_types = {task["task_type"] for task in state["tasks"].values()}
        self.assertIn("RUN_VALIDATION", task_types)
        self.assertIn("REQUEST_PUBLICATION_REVIEW", task_types)
        self.assertEqual(state["publications"], {})

    def test_full_weekend_rehearsal_sequence(self):
        source_games = [
            {"game_id": "w1-a", "away_team": "A", "home_team": "B"},
            {"game_id": "w1-b", "away_team": "C", "home_team": "D"},
            {"game_id": "w1-c", "away_team": "E", "home_team": "F"},
        ]
        target = {"game_id": "w2-a", "away_team": "G", "home_team": "H"}
        events = build_rehearsal_events(source_games, target)
        state = reduce_events(events)
        replay = reduce_events(reversed(events))
        self.assertEqual(canonical_json(state), canonical_json(replay))
        self.assertEqual(state["cycles"]["2026_WK2_PREP"]["created_by_event_id"], "e006")
        self.assertEqual(state["authorities"]["spread"]["state"], "OFFICIAL")
        self.assertEqual(state["authorities"]["total"]["state"], "OFFICIAL")
        self.assertIn("sp-v3-correction", state["providers"]["SP+"]["versions"])
        self.assertEqual(state["providers"]["DRatings"]["last_check_result"], "UPDATED")
        transitions = state["authority_transitions"]
        self.assertTrue(any(row["value_state"] == "STALE" for row in transitions))
        self.assertTrue(any(row["value_state"] == "CARRY_FORWARD" for row in transitions))
        first_market = next(e for e in events if e.event_id == "e010")
        shadow_ready = next(e for e in events if e.event_id == "e017")
        self.assertLess(first_market.timestamp, shadow_ready.timestamp)
        unique = {e.event_id: e for e in events}
        for final_id, ready_id in (("e006", "e012"), ("e007", "e014"), ("e008", "e016")):
            self.assertLess(unique[final_id].timestamp, unique[ready_id].timestamp)
        self.assertTrue(state["ignored_duplicate_event_ids"])
        self.assertEqual(state["publications"], {})


if __name__ == "__main__":
    unittest.main()
