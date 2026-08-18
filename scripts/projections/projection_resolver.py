#!/usr/bin/env python3
"""Strict selector for canonical scheduled-game projections.

This module owns projection selection, not projection formulas. Graceful
degradation, when permitted by a canonical model, is calculated upstream by
the canonical contract builder. This resolver never substitutes a team rating,
market rating, legacy blend, or another model.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STANDARD_SPREAD = "standard_spread_five_source_v1"
STANDARD_TOTAL = "standard_total_sp_massey_sagarin_v1"
SHADOW_SPREAD = "shadow_spread_sp_sagarin_v1"
SHADOW_TOTAL = "shadow_total_enhanced_spplus_od_v1"

MODEL_VALUE_FIELDS = {
    STANDARD_SPREAD: ("value_home_margin", "value_home_line"),
    STANDARD_TOTAL: ("value_total",),
    SHADOW_SPREAD: ("value_home_margin", "value_home_line"),
    SHADOW_TOTAL: ("value_total",),
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
    if projection.get("availability_status") not in {"AVAILABLE", "AVAILABLE_DEGRADED"}:
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
            "CANONICAL_MODEL_AVAILABLE"
            if projection.get("availability_status") == "AVAILABLE"
            else "CANONICAL_MODEL_AVAILABLE_DEGRADED"
        ),
        "source_type": "CANONICAL_GAME_PROJECTION",
        "fallback_used": False,
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
