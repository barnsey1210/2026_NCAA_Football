#!/usr/bin/env python3
"""Strict selector for canonical scheduled-game projections.

This module owns projection selection, not projection formulas. Official
models are strict: only ``AVAILABLE`` is selectable. Explicit operational
selectors may choose a separately identified degraded estimate; they never
relabel that estimate as the official model or substitute another data source.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STANDARD_SPREAD = "standard_spread_five_source_v1"
STANDARD_TOTAL = "standard_total_sp_massey_sagarin_v1"
DEGRADED_SPREAD = "standard_spread_degraded_v1"
DEGRADED_TOTAL = "standard_total_degraded_v1"
SHADOW_SPREAD = "shadow_spread_sp_sagarin_v1"
SHADOW_TOTAL = "shadow_total_enhanced_spplus_od_v1"

MODEL_VALUE_FIELDS = {
    STANDARD_SPREAD: ("value_home_margin", "value_home_line"),
    STANDARD_TOTAL: ("value_total",),
    DEGRADED_SPREAD: ("value_home_margin", "value_home_line"),
    DEGRADED_TOTAL: ("value_total",),
    SHADOW_SPREAD: ("value_home_margin", "value_home_line"),
    SHADOW_TOTAL: ("value_total",),
}

DEGRADED_MODEL_BY_OFFICIAL = {
    STANDARD_SPREAD: DEGRADED_SPREAD,
    STANDARD_TOTAL: DEGRADED_TOTAL,
}


def load_contract(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    games = payload.get("games")
    if not isinstance(games, list):
        raise ValueError(f"Projection contract has no games list: {path}")
    return payload


def index_contract(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for game in payload.get("games", []):
        game_id = str(game.get("game_id") or "").removesuffix(".0")
        if not game_id:
            raise ValueError("Projection contract contains an empty game_id")
        if game_id in index:
            raise ValueError(f"Duplicate game_id in projection contract: {game_id}")
        index[game_id] = game
    return index


def unavailable(model_id: str, reason: str, projection: dict[str, Any] | None = None) -> dict[str, Any]:
    projection = projection or {}
    return {
        "model_id": model_id,
        "selection_status": "UNAVAILABLE",
        "selection_reason": reason,
        "source_type": "CANONICAL_GAME_PROJECTION",
        "fallback_used": False,
        "authority": projection.get("authority", "UNAVAILABLE"),
        "value_home_margin": None,
        "value_home_line": None,
        "value_total": None,
        "availability_status": projection.get("availability_status", "MISSING_MODEL"),
        "component_status": projection.get("component_status", {}),
        "formula_version": projection.get("formula_version"),
        "freshness_timestamp": projection.get("freshness_timestamp"),
        "resolution_mode": (projection.get("resolution") or {}).get("resolution_mode"),
        "available_components": (projection.get("resolution") or {}).get("available_components"),
        "missing_components": (projection.get("resolution") or {}).get("missing_components"),
        "weights_used": (projection.get("resolution") or {}).get("weights_used"),
    }


def resolve_projection(game: dict[str, Any] | None, model_id: str) -> dict[str, Any]:
    """Return one canonical model or an explicit unavailable result."""
    if model_id not in MODEL_VALUE_FIELDS:
        raise ValueError(f"Unknown canonical model_id: {model_id}")
    if not game:
        return unavailable(model_id, "SCHEDULED_GAME_NOT_IN_CANONICAL_CONTRACT")

    projection = (game.get("projections") or {}).get(model_id)
    if not isinstance(projection, dict):
        return unavailable(model_id, "MODEL_NOT_DEFINED_FOR_GAME")
    required_availability = (
        "DEGRADED"
        if model_id in {DEGRADED_SPREAD, DEGRADED_TOTAL}
        else "AVAILABLE"
    )
    if projection.get("availability_status") != required_availability:
        return unavailable(
            model_id,
            f"CANONICAL_MODEL_{projection.get('availability_status') or 'UNAVAILABLE'}",
            projection,
        )

    required_value_fields = MODEL_VALUE_FIELDS[model_id]
    if any(projection.get(field) is None for field in required_value_fields):
        return unavailable(model_id, "AVAILABLE_MODEL_MISSING_REQUIRED_VALUE", projection)

    return {
        "model_id": model_id,
        "selection_status": "AVAILABLE",
        "selection_reason": (
            "OPERATIONAL_DEGRADED_MODEL_AVAILABLE"
            if required_availability == "DEGRADED"
            else "CANONICAL_MODEL_AVAILABLE"
        ),
        "source_type": "CANONICAL_GAME_PROJECTION",
        "fallback_used": False,
        "authority": projection.get(
            "authority",
            "OPERATIONAL_DEGRADED"
            if required_availability == "DEGRADED"
            else "OFFICIAL",
        ),
        "value_home_margin": projection.get("value_home_margin"),
        "value_home_line": projection.get("value_home_line"),
        "value_total": projection.get("value_total"),
        "availability_status": projection.get("availability_status"),
        "component_status": projection.get("component_status", {}),
        "formula_version": projection.get("formula_version"),
        "freshness_timestamp": projection.get("freshness_timestamp"),
        "resolution_mode": (projection.get("resolution") or {}).get("resolution_mode"),
        "available_components": (projection.get("resolution") or {}).get("available_components"),
        "missing_components": (projection.get("resolution") or {}).get("missing_components"),
        "weights_used": (projection.get("resolution") or {}).get("weights_used"),
    }


def resolve_game(index: dict[str, dict[str, Any]], game_id: Any, model_id: str) -> dict[str, Any]:
    normalized_id = str(game_id or "").removesuffix(".0")
    return resolve_projection(index.get(normalized_id), model_id)


def resolve_operational_projection(
    game: dict[str, Any] | None,
    official_model_id: str,
) -> dict[str, Any]:
    """Select strict official first, then its explicit degraded estimate."""
    if official_model_id not in DEGRADED_MODEL_BY_OFFICIAL:
        raise ValueError(
            f"No degraded operational path for model_id: {official_model_id}"
        )

    official = resolve_projection(game, official_model_id)
    if official.get("selection_status") == "AVAILABLE":
        return {
            **official,
            "official_model_id": official_model_id,
            "operational_model_id": official_model_id,
            "operational_degraded_used": False,
        }

    degraded_model_id = DEGRADED_MODEL_BY_OFFICIAL[official_model_id]
    degraded = resolve_projection(game, degraded_model_id)
    if degraded.get("selection_status") == "AVAILABLE":
        return {
            **degraded,
            "official_model_id": official_model_id,
            "operational_model_id": degraded_model_id,
            "operational_degraded_used": True,
            "official_selection_reason": official.get("selection_reason"),
        }

    return {
        **official,
        "official_model_id": official_model_id,
        "operational_model_id": None,
        "operational_degraded_used": False,
        "degraded_selection_reason": degraded.get("selection_reason"),
    }


def resolve_operational_game(
    index: dict[str, dict[str, Any]],
    game_id: Any,
    official_model_id: str,
) -> dict[str, Any]:
    normalized_id = str(game_id or "").removesuffix(".0")
    return resolve_operational_projection(
        index.get(normalized_id),
        official_model_id,
    )
