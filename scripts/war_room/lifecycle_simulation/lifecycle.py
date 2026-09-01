#!/usr/bin/env python3
"""Deterministic, offline War Room lifecycle reducer.

This module never calls providers, production builders, publishers, projection
formulas, authority formulas, or edge calculations. It consumes explicit
events and emits simulated task requests for validation/rehearsal only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_EVENTS = {
    "GAME_ACTIVE",
    "GAME_FINAL",
    "POSTGAME_READY",
    "SHADOW_PARTIAL",
    "SHADOW_READY",
    "RATING_SOURCE_UPDATED",
    "RATING_SOURCE_CHECKED",
    "RATING_SOURCE_REJECTED",
    "PROVIDER_PANEL_CHANGED",
    "OFFICIAL_PROJECTION_READY",
    "AUTHORITY_CHANGED",
    "MARKET_FIRST_SEEN",
    "MARKET_QUOTE_ACCEPTED",
    "MARKET_CLOSE",
    "BUILD_COMPLETED",
    "VALIDATION_PASSED",
    "PUBLICATION_COMPLETED",
    "TASK_FAILED",
    "TASK_RETRY",
    "TASK_COMPLETED",
}

AUTHORITY_STATES = {"SHADOW", "HYBRID", "OFFICIAL"}
VALUE_STATES = {"CURRENT", "STALE", "CARRY_FORWARD", "UNAVAILABLE"}


@dataclass(frozen=True)
class Event:
    event_id: str
    event_type: str
    timestamp: str
    cycle_id: str
    entity_id: str
    payload: dict[str, Any]
    source: str

    def validate(self) -> None:
        if not self.event_id:
            raise ValueError("event_id is required")
        if self.event_type not in SUPPORTED_EVENTS:
            raise ValueError(f"unsupported event_type: {self.event_type}")
        if not self.timestamp or not self.cycle_id or not self.entity_id:
            raise ValueError("timestamp, cycle_id, and entity_id are required")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be an object")
        if not self.source:
            raise ValueError("source is required")

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "Event":
        event = cls(
            event_id=str(row.get("event_id") or ""),
            event_type=str(row.get("event_type") or ""),
            timestamp=str(row.get("timestamp") or ""),
            cycle_id=str(row.get("cycle_id") or ""),
            entity_id=str(row.get("entity_id") or ""),
            payload=dict(row.get("payload") or {}),
            source=str(row.get("source") or ""),
        )
        event.validate()
        return event


class EventLedger:
    """Append-only JSONL ledger used only at a caller-selected simulation path."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def read(self) -> list[Event]:
        if not self.path.exists():
            return []
        events: list[Event] = []
        for line_number, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                events.append(Event.from_dict(json.loads(line)))
            except (ValueError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"invalid lifecycle ledger row {line_number}: {exc}"
                ) from exc
        return events

    def append(self, event: Event) -> bool:
        event.validate()
        if any(existing.event_id == event.event_id for existing in self.read()):
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")
        return True


def _initial_authority() -> dict[str, Any]:
    return {
        "state": "SHADOW",
        "model_id": None,
        "selected_value": None,
        "value_state": "UNAVAILABLE",
        "updated_sources": [],
        "updated_source_count": 0,
        "required_source_count": None,
        "edge_projection_source": None,
        "last_event_id": None,
    }


def initial_state() -> dict[str, Any]:
    return {
        "schema_version": "war-room-lifecycle-simulation-state-v1",
        "simulation_only": True,
        "processed_event_ids": [],
        "ignored_duplicate_event_ids": [],
        "cycles": {},
        "games": {},
        "providers": {},
        "projections": {},
        "authorities": {
            "spread": _initial_authority(),
            "total": _initial_authority(),
        },
        "authority_transitions": [],
        "markets": {},
        "builds": {},
        "publications": {},
        "tasks": {},
        "audit": [],
    }


class LifecycleReducer:
    """Pure event reducer plus deterministic simulated task-request generation."""

    def __init__(self) -> None:
        self.state = initial_state()

    @staticmethod
    def ordered(events: Iterable[Event]) -> list[Event]:
        return sorted(events, key=lambda event: (event.timestamp, event.event_id))

    @staticmethod
    def task_id(event: Event, task_type: str, entity_id: str) -> str:
        raw = f"{event.event_id}|{task_type}|{entity_id}".encode("utf-8")
        return "task_" + hashlib.sha256(raw).hexdigest()[:16]

    def request_task(
        self,
        event: Event,
        task_type: str,
        entity_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        entity = entity_id or event.entity_id
        task_id = self.task_id(event, task_type, entity)
        self.state["tasks"].setdefault(
            task_id,
            {
                "task_id": task_id,
                "task_type": task_type,
                "entity_id": entity,
                "cycle_id": event.cycle_id,
                "requested_by_event_id": event.event_id,
                "status": "REQUESTED",
                "attempts": 0,
                "requested_at": event.timestamp,
                "attempt_history": [],
                "simulation_only": True,
                "payload": payload or {},
            },
        )

    def _cycle(self, event: Event) -> dict[str, Any]:
        return self.state["cycles"].setdefault(
            event.cycle_id,
            {
                "cycle_id": event.cycle_id,
                "status": "PENDING_FIRST_FINAL",
                "created_at": None,
                "created_by_event_id": None,
                "source_week": event.payload.get("source_week"),
                "target_week": event.payload.get("target_week"),
                "events": [],
            },
        )

    def _authority_changed(self, event: Event) -> None:
        domain = str(event.payload.get("domain") or "").lower()
        authority = str(event.payload.get("authority") or "").upper()
        if domain not in {"spread", "total"}:
            raise ValueError("AUTHORITY_CHANGED requires spread or total domain")
        if authority not in AUTHORITY_STATES:
            raise ValueError(f"invalid authority state: {authority}")

        current = self.state["authorities"][domain]
        model_id = event.payload.get("model_id")
        value_supplied = event.payload.get("selected_value") is not None
        same_identity = bool(model_id and model_id == current.get("model_id"))
        preserve = event.payload.get("preserve_last_valid") is True

        if value_supplied:
            selected_value = event.payload["selected_value"]
            value_state = str(event.payload.get("value_state") or "CURRENT").upper()
        elif preserve and same_identity and current.get("selected_value") is not None:
            selected_value = current["selected_value"]
            value_state = "CARRY_FORWARD"
        else:
            selected_value = None
            value_state = str(event.payload.get("value_state") or "UNAVAILABLE").upper()

        if value_state not in VALUE_STATES:
            raise ValueError(f"invalid value state: {value_state}")

        self.state["authorities"][domain] = {
            "state": authority,
            "model_id": model_id,
            "selected_value": selected_value,
            "value_state": value_state,
            "updated_sources": list(event.payload.get("updated_sources") or []),
            "updated_source_count": event.payload.get("updated_source_count"),
            "required_source_count": event.payload.get("required_source_count"),
            "weights_used": dict(event.payload.get("weights_used") or {}),
            "edge_projection_source": model_id if selected_value is not None else None,
            "last_event_id": event.event_id,
        }
        self.state["authority_transitions"].append(
            {
                "event_id": event.event_id,
                "timestamp": event.timestamp,
                "domain": domain,
                "prior_authority": current.get("state"),
                "authority": authority,
                "model_id": model_id,
                "value_state": value_state,
                "selected_value": selected_value,
            }
        )
        self.request_task(event, "REBUILD_WAR_ROOM")

    def apply(self, event: Event) -> None:
        event.validate()
        if event.event_id in self.state["processed_event_ids"]:
            self.state["ignored_duplicate_event_ids"].append(event.event_id)
            return

        cycle = self._cycle(event)
        cycle["events"].append(event.event_id)
        self.state["processed_event_ids"].append(event.event_id)
        self.state["audit"].append(
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "entity_id": event.entity_id,
            }
        )

        payload = event.payload
        event_type = event.event_type

        if event_type == "GAME_ACTIVE":
            self.state["games"][event.entity_id] = {
                "state": "GAME_ACTIVE",
                "started_at": event.timestamp,
                "last_event_id": event.event_id,
            }

        elif event_type == "GAME_FINAL":
            if cycle["created_at"] is None:
                cycle.update(
                    {
                        "status": "PREPARING",
                        "created_at": event.timestamp,
                        "created_by_event_id": event.event_id,
                        "source_week": payload.get("source_week"),
                        "target_week": payload.get("target_week"),
                    }
                )
            self.state["games"][event.entity_id] = {
                "state": "GAME_FINAL",
                "final_score": payload.get("final_score"),
                "final_at": event.timestamp,
                "last_event_id": event.event_id,
            }
            self.request_task(event, "RUN_POSTGAME_PROCESSING")

        elif event_type == "POSTGAME_READY":
            game = self.state["games"].setdefault(event.entity_id, {})
            game.update(
                {
                    "state": "POSTGAME_READY",
                    "postgame_ready_at": event.timestamp,
                    "last_event_id": event.event_id,
                }
            )
            self.request_task(event, "BUILD_SHADOW_PROJECTIONS")

        elif event_type in {"SHADOW_PARTIAL", "SHADOW_READY"}:
            status = "PARTIAL" if event_type == "SHADOW_PARTIAL" else "READY"
            self.state["projections"].setdefault(event.entity_id, {})["shadow"] = {
                "status": status,
                "models": dict(payload.get("models") or {}),
                "values": dict(payload.get("values") or {}),
                "missing_components": list(payload.get("missing_components") or []),
                "observed_at": event.timestamp,
                "last_event_id": event.event_id,
            }
            self.request_task(event, "REFRESH_PROJECTION_CONTRACT")
            if event_type == "SHADOW_READY":
                for domain in ("spread", "total"):
                    authority = self.state["authorities"][domain]
                    value = (payload.get("values") or {}).get(domain)
                    model_id = (payload.get("models") or {}).get(domain)
                    if authority["state"] == "SHADOW" and value is not None:
                        authority.update(
                            {
                                "model_id": model_id,
                                "selected_value": value,
                                "value_state": "CURRENT",
                                "edge_projection_source": model_id,
                                "last_event_id": event.event_id,
                            }
                        )
                self.request_task(event, "REBUILD_WAR_ROOM")

        elif event_type == "RATING_SOURCE_CHECKED":
            provider = str(payload.get("provider") or event.entity_id)
            provider_state = self.state["providers"].setdefault(
                provider, {"versions": [], "checks": [], "rejections": []}
            )
            provider_state.setdefault("checks", []).append(
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp,
                    "result": str(payload.get("result") or "UNCHANGED"),
                    "observed_version": payload.get("version"),
                }
            )
            provider_state.update(
                {
                    "last_check_result": str(payload.get("result") or "UNCHANGED"),
                    "last_event_id": event.event_id,
                }
            )

        elif event_type == "RATING_SOURCE_REJECTED":
            provider = str(payload.get("provider") or event.entity_id)
            provider_state = self.state["providers"].setdefault(
                provider, {"versions": [], "checks": [], "rejections": []}
            )
            provider_state.setdefault("rejections", []).append(
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp,
                    "candidate_version": payload.get("candidate_version"),
                    "reason": payload.get("reason"),
                }
            )
            provider_state.update(
                {"last_check_result": "REJECTED", "last_event_id": event.event_id}
            )

        elif event_type in {"RATING_SOURCE_UPDATED", "PROVIDER_PANEL_CHANGED"}:
            provider = str(payload.get("provider") or event.entity_id)
            version = str(payload.get("version") or payload.get("fingerprint") or "")
            provider_state = self.state["providers"].setdefault(
                provider, {"versions": [], "checks": [], "rejections": []}
            )
            versions = provider_state["versions"]
            if version and version not in versions:
                versions.append(version)
            provider_state.update(
                {
                    "latest_version": version or None,
                    "last_check_result": "UPDATED",
                    "last_event_id": event.event_id,
                }
            )
            self.request_task(event, "REFRESH_PROJECTION_CONTRACT")

        elif event_type == "OFFICIAL_PROJECTION_READY":
            self.state["projections"].setdefault(event.entity_id, {})["official"] = {
                "status": "READY",
                "models": dict(payload.get("models") or {}),
                "values": dict(payload.get("values") or {}),
                "observed_at": event.timestamp,
                "last_event_id": event.event_id,
            }
            self.request_task(event, "REBUILD_WAR_ROOM")

        elif event_type == "AUTHORITY_CHANGED":
            self._authority_changed(event)

        elif event_type in {"MARKET_FIRST_SEEN", "MARKET_QUOTE_ACCEPTED"}:
            market = self.state["markets"].setdefault(event.entity_id, {})
            if event_type == "MARKET_FIRST_SEEN":
                market.setdefault("first_seen_at", event.timestamp)
            market.update(
                {
                    "state": "OPEN",
                    "latest": dict(payload),
                    "last_event_id": event.event_id,
                }
            )
            self.request_task(event, "REBUILD_WAR_ROOM")

        elif event_type == "MARKET_CLOSE":
            market = self.state["markets"].setdefault(event.entity_id, {})
            market.update(
                {
                    "state": "CLOSED",
                    "close": dict(payload),
                    "closed_at": event.timestamp,
                    "last_event_id": event.event_id,
                }
            )
            self.request_task(event, "REBUILD_WAR_ROOM")

        elif event_type == "BUILD_COMPLETED":
            self.state["builds"][event.entity_id] = {
                "state": "BUILD_COMPLETED",
                "artifacts": list(payload.get("artifacts") or []),
                "last_event_id": event.event_id,
            }
            self.request_task(event, "RUN_VALIDATION")

        elif event_type == "VALIDATION_PASSED":
            build = self.state["builds"].setdefault(event.entity_id, {})
            build.update({"state": "VALIDATION_PASSED", "last_event_id": event.event_id})
            self.request_task(event, "REQUEST_PUBLICATION_REVIEW")

        elif event_type == "PUBLICATION_COMPLETED":
            self.state["publications"][event.entity_id] = {
                "state": "PUBLICATION_COMPLETED",
                "simulation_only": True,
                "last_event_id": event.event_id,
            }

        elif event_type in {"TASK_FAILED", "TASK_RETRY", "TASK_COMPLETED"}:
            task_id = str(payload.get("task_id") or event.entity_id)
            task = self.state["tasks"].setdefault(
                task_id,
                {
                    "task_id": task_id,
                    "task_type": payload.get("task_type"),
                    "entity_id": payload.get("entity_id"),
                    "cycle_id": event.cycle_id,
                    "status": "UNKNOWN",
                    "attempts": 0,
                    "requested_at": None,
                    "attempt_history": [],
                    "simulation_only": True,
                    "payload": {},
                },
            )
            if event_type == "TASK_FAILED":
                task.update({"status": "FAILED", "failure": payload.get("reason")})
                task.setdefault("attempt_history", []).append(
                    {
                        "event_id": event.event_id,
                        "timestamp": event.timestamp,
                        "outcome": "FAILED",
                        "reason": payload.get("reason"),
                        "retryable": payload.get("retryable") is True,
                    }
                )
            elif event_type == "TASK_RETRY":
                task.update({"status": "RETRY_REQUESTED", "failure": None})
                task["attempts"] = int(task.get("attempts") or 0) + 1
                task.setdefault("attempt_history", []).append(
                    {
                        "event_id": event.event_id,
                        "timestamp": event.timestamp,
                        "outcome": "RETRY_REQUESTED",
                    }
                )
            else:
                task.update({"status": "COMPLETED", "failure": None})
                task.setdefault("attempt_history", []).append(
                    {
                        "event_id": event.event_id,
                        "timestamp": event.timestamp,
                        "outcome": "COMPLETED",
                    }
                )

    def reduce(self, events: Iterable[Event]) -> dict[str, Any]:
        for event in self.ordered(events):
            self.apply(event)
        return self.state


def reduce_events(events: Iterable[Event]) -> dict[str, Any]:
    return LifecycleReducer().reduce(events)


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
