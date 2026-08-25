#!/usr/bin/env python3
"""Build the canonical, versioned game-projection contract.

This contract is the production source for shared page-data adapters. It does
not modify model formulas or substitute missing canonical components.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projections.projection_resolver import (
    resolve_operational_projection,
    resolve_projection,
)

DEFAULT_GAMES = ROOT / "data/snapshots/preseason/preseason_db.json"
DEFAULT_SOURCES = ROOT / "data/projections/game_projection_sources_2026.csv"
DEFAULT_SHADOW = ROOT / "data/site/saturday_shadow_component_predictions.json"
DEFAULT_SHADOW_SPEC_RELATIVE = "data/research/historical/shadow/totals_oos_2024/enhanced_spplus_od_frozen_model_specification.csv"
DEFAULT_SHADOW_SPEC = ROOT / DEFAULT_SHADOW_SPEC_RELATIVE
DEFAULT_OUT = ROOT / "data/site/current_game_projection_contract.json"
DEFAULT_AUDIT = ROOT / "data/audits/current_game_projection_contract_audit.json"

STANDARD_SPREAD = "standard_spread_five_source_v1"
STANDARD_TOTAL = "standard_total_sp_massey_sagarin_v1"
DEGRADED_SPREAD = "standard_spread_degraded_v1"
DEGRADED_TOTAL = "standard_total_degraded_v1"
SHADOW_SPREAD = "shadow_spread_sp_sagarin_v1"
SHADOW_TOTAL = "shadow_total_enhanced_spplus_od_v1"

SPREAD_COMPONENTS = (
    "SP+",
    "FPI",
    "TeamRankings",
    "Sagarin Rating",
    "DRatings",
)
TOTAL_COMPONENTS = ("SP+", "Massey Dual", "Sagarin Total")
SHADOW_SPREAD_COMPONENTS = ("Shadow SP+", "Shadow Sagarin")
SHADOW_TOTAL_COMPONENTS = (
    "updated home SP+ offense",
    "updated away SP+ offense",
    "updated home SP+ defense",
    "updated away SP+ defense",
)

SOURCE_ALIASES = {
    "SP+": "SP+",
    "FPI": "FPI",
    "TeamRankings": "TeamRankings",
    "Sagarin Rating": "Sagarin Rating",
    "Sagarin Game Total": "Sagarin Total",
    "DRatings Predictions": "DRatings",
    "Massey Games": "Massey",
    "Shadow Sagarin": "Shadow Sagarin",
}


def finite(value: Any) -> float | None:
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def fixed_weight_value(values: dict[str, float | None], weights: dict[str, float]) -> float | None:
    """Return a fixed-weight value only when every declared component exists."""
    if set(values) != set(weights) or any(values[name] is None for name in weights):
        return None
    return sum(float(values[name]) * float(weights[name]) for name in weights)


def renormalized_weight_value(
    values: dict[str, float | None],
    weights: dict[str, float],
    minimum_components: int = 3,
) -> tuple[float | None, dict[str, float], list[str], list[str]]:
    """Gracefully degrade a canonical model when a source is unavailable.

    This preserves the canonical model identity. It never substitutes another
    model or data source.
    """
    available = {name: value for name, value in values.items() if value is not None}
    missing = [name for name, value in values.items() if value is None]

    if len(available) < minimum_components:
        return None, {}, list(available), missing

    total_weight = sum(weights[name] for name in available)
    normalized_weights = {
        name: weights[name] / total_weight
        for name in available
    }
    value = sum(
        float(available[name]) * normalized_weights[name]
        for name in available
    )
    return value, normalized_weights, list(available), missing


def massey_dual(published_total: Any, away_points: Any, home_points: Any) -> float | None:
    published = finite(published_total)
    away = finite(away_points)
    home = finite(home_points)
    if None in (published, away, home):
        return None
    return (published + away + home) / 2.0


def enhanced_shadow_total(
    home_offense: Any,
    away_offense: Any,
    home_defense: Any,
    away_defense: Any,
) -> float | None:
    values = [finite(v) for v in (home_offense, away_offense, home_defense, away_defense)]
    if any(v is None for v in values):
        return None
    home_off, away_off, home_def, away_def = values
    return 0.5 * (home_off + away_def) + 0.5 * (away_off + home_def)


def status(values: dict[str, float | None], *, activated: bool = True) -> str:
    if not activated:
        return "NOT_YET_ACTIVATED"
    return "AVAILABLE" if all(value is not None for value in values.values()) else "MISSING_COMPONENT"


def component_status(values: dict[str, float | None]) -> dict[str, str]:
    return {name: "PRESENT" if value is not None else "MISSING" for name, value in values.items()}


def latest_timestamp(rows: list[dict[str, Any]]) -> str | None:
    timestamps = [str(row.get("pulled_at")) for row in rows if row.get("pulled_at")]
    return max(timestamps) if timestamps else None


def projection(
    *,
    model_id: str,
    formula_status: str,
    values: dict[str, float | None],
    weights: dict[str, float],
    availability: str,
    build_timestamp: str,
    source_artifacts: list[str],
    freshness_timestamp: str | None,
    validation_status: str,
    value_home_margin: float | None = None,
    value_home_line: float | None = None,
    value_total: float | None = None,
    extra_status: dict[str, Any] | None = None,
    authority: str | None = None,
    status_label: str | None = None,
    value: float | None = None,
    method: str | None = None,
    degraded_reason: str | None = None,
    confidence_status: str | None = None,
) -> dict[str, Any]:
    statuses: dict[str, Any] = component_status(values)
    resolution = None
    if extra_status:
        resolution_keys = {
            "resolution_mode",
            "available_components",
            "missing_components",
            "weights_used",
        }
        resolution = {
            key: extra_status[key]
            for key in resolution_keys
            if key in extra_status
        }
        statuses.update({
            key: value
            for key, value in extra_status.items()
            if key not in resolution_keys
        })
    result = {
        "model_id": model_id,
        "formula_version": "v1",
        "formula_status": formula_status,
        "value_home_margin": value_home_margin,
        "value_home_line": value_home_line,
        "value_total": value_total,
        "availability_status": availability,
        "required_components": list(values),
        "weights": weights,
        "component_values": values,
        "component_status": statuses,
        "resolution": resolution,
        "freshness_timestamp": freshness_timestamp,
        "build_timestamp": build_timestamp,
        "source_artifacts": source_artifacts,
        "sign_convention": {
            "value_home_margin": "positive means home team projected to win by that amount",
            "value_home_line": "bookmaker home-spread orientation; negative means home favored",
            "value_total": "projected combined points",
        },
        "validation_status": validation_status,
    }
    if authority is not None:
        result["authority"] = authority
    if status_label is not None:
        result["status"] = status_label
    if value is not None:
        result["value"] = value
    if method is not None:
        result["method"] = method
    if degraded_reason is not None:
        result["degraded_reason"] = degraded_reason
    if confidence_status is not None:
        result["confidence_status"] = confidence_status
    if extra_status:
        result["sources_available"] = list(
            extra_status.get("available_components") or []
        )
        result["missing_sources"] = list(
            extra_status.get("missing_components") or []
        )
    return result


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        handle.write("\n")
        temp = Path(handle.name)
    temp.replace(path)


def load_sources(path: Path) -> dict[str, dict[str, dict[str, Any]]]:
    if not path.is_file() or path.stat().st_size == 0:
        return {}
    frame = pd.read_csv(path, low_memory=False)
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for row in frame.to_dict("records"):
        game_id = str(row.get("game_id") or "").removesuffix(".0")
        source = SOURCE_ALIASES.get(str(row.get("source") or ""))
        if not game_id or not source:
            continue
        result.setdefault(game_id, {})[source] = row
    return result


def load_shadow(path: Path) -> tuple[dict[str, dict[str, Any]], str | None]:
    if not path.is_file():
        return {}, None
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload if isinstance(payload, list) else payload.get("games", [])
    result = {
        str(row.get("game_id") or "").removesuffix(".0"): row
        for row in rows
        if row.get("game_id") is not None
    }
    return result, payload.get("generated_at") if isinstance(payload, dict) else None


def validate_shadow_spec(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"valid": False, "reason": "frozen historical model specification missing"}
    frame = pd.read_csv(path)
    required = {
        "target", "model", "feature", "training_mean", "training_std",
        "standardized_ridge_coefficient", "training_season", "training_rows",
        "ridge_alpha", "validation_freeze", "next_week_market_features_used",
    }
    if not required.issubset(frame.columns):
        return {"valid": False, "reason": "frozen specification columns incomplete"}
    enhanced = frame[frame["model"].eq("ENHANCED_SHADOW")]
    targets = set(enhanced["target"].dropna())
    valid = (
        targets == {"delta_spplus_offense", "delta_spplus_defense"}
        and set(pd.to_numeric(enhanced["ridge_alpha"], errors="coerce").dropna()) == {1.0}
        and set(pd.to_numeric(enhanced["training_season"], errors="coerce").dropna()) == {2025}
        and set(pd.to_numeric(enhanced["next_week_market_features_used"], errors="coerce").dropna()) == {0}
    )
    return {
        "valid": bool(valid),
        "reason": "validated frozen specification" if valid else "frozen specification invariant failed",
        "rows": int(len(enhanced)),
        "targets": sorted(targets),
        "training_season": 2025,
        "ridge_alpha": 1.0,
    }


def build(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    games_payload = json.loads(args.games.read_text(encoding="utf-8"))
    games = games_payload.get("games", [])
    if args.start_date and args.end_date:
        games = [
            game for game in games
            if args.start_date <= str(game.get("date") or "")[:10] <= args.end_date
        ]
    sources = load_sources(args.sources)
    shadow_rows, shadow_timestamp = load_shadow(args.shadow)
    shadow_spec = validate_shadow_spec(args.shadow_spec)
    built_at = args.built_at or datetime.now(timezone.utc).isoformat()
    output_games = []

    spread_weights = {name: 0.20 for name in SPREAD_COMPONENTS}
    total_weights = {"SP+": 0.40, "Massey Dual": 0.40, "Sagarin Total": 0.20}
    shadow_spread_weights = {name: 0.50 for name in SHADOW_SPREAD_COMPONENTS}
    shadow_total_weights = {name: 0.50 for name in SHADOW_TOTAL_COMPONENTS}

    for game in games:
        game_id = str(game.get("game_id") or "").removesuffix(".0")
        game_sources = sources.get(game_id, {})
        spread_source_rows = [game_sources[name] for name in SPREAD_COMPONENTS if name in game_sources]
        total_source_rows = [game_sources[name] for name in ("SP+", "Massey", "Sagarin Total") if name in game_sources]

        spread_values = {
            name: finite(game_sources.get(name, {}).get("spread_home"))
            for name in SPREAD_COMPONENTS
        }
        official_spread_margin = fixed_weight_value(
            spread_values,
            spread_weights,
        )
        if official_spread_margin is not None:
            spread_resolution = {
                "mode": "FULL",
                "available_components": list(spread_values),
                "missing_components": [],
                "weights_used": spread_weights,
            }
            spread_availability = "AVAILABLE"
            degraded_margin = None
            degraded_weights = {}
            degraded_spread_resolution = {
                "mode": "NOT_APPLICABLE_OFFICIAL_AVAILABLE",
                "available_components": list(spread_values),
                "missing_components": [],
                "weights_used": {},
            }
            degraded_spread_availability = "NOT_APPLICABLE"
        else:
            (
                degraded_margin,
                degraded_weights,
                available_components,
                missing_components,
            ) = renormalized_weight_value(spread_values, spread_weights)

            spread_resolution = {
                "mode": "STRICT_REQUIRED_COMPONENTS_MISSING",
                "available_components": available_components,
                "missing_components": missing_components,
                "weights_used": {},
            }
            spread_availability = "MISSING_COMPONENT"
            degraded_spread_resolution = {
                "mode": (
                    "DEGRADED_RENORMALIZED"
                    if degraded_margin is not None
                    else "UNAVAILABLE"
                ),
                "available_components": available_components,
                "missing_components": missing_components,
                "weights_used": degraded_weights,
            }
            degraded_spread_availability = (
                "DEGRADED"
                if degraded_margin is not None
                else "MISSING_COMPONENT"
            )

        sp_total = finite(game_sources.get("SP+", {}).get("total"))
        # Never treat a generic or legacy projected_total field as SP+. It may
        # already contain another blend. Missing explicit SP+ totals stay missing.
        massey = game_sources.get("Massey", {})
        mass_dual = massey_dual(
            massey.get("total"), massey.get("away_score"), massey.get("home_score")
        )
        total_values = {
            "SP+": sp_total,
            "Massey Dual": mass_dual,
            "Sagarin Total": finite(game_sources.get("Sagarin Total", {}).get("total")),
        }
        official_standard_total = fixed_weight_value(
            total_values,
            total_weights,
        )
        if official_standard_total is not None:
            total_resolution = {
                "mode": "FULL",
                "available_components": list(total_values),
                "missing_components": [],
                "weights_used": total_weights,
            }
            total_availability = "AVAILABLE"
            degraded_total = None
            degraded_weights = {}
            degraded_total_resolution = {
                "mode": "NOT_APPLICABLE_OFFICIAL_AVAILABLE",
                "available_components": list(total_values),
                "missing_components": [],
                "weights_used": {},
            }
            degraded_total_availability = "NOT_APPLICABLE"
        else:
            (
                degraded_total,
                degraded_weights,
                available_components,
                missing_components,
            ) = renormalized_weight_value(
                total_values,
                total_weights,
                minimum_components=1,
            )

            total_resolution = {
                "mode": "STRICT_REQUIRED_COMPONENTS_MISSING",
                "available_components": available_components,
                "missing_components": missing_components,
                "weights_used": {},
            }
            total_availability = "MISSING_COMPONENT"
            degraded_total_resolution = {
                "mode": (
                    "DEGRADED_RENORMALIZED"
                    if degraded_total is not None
                    else "UNAVAILABLE"
                ),
                "available_components": available_components,
                "missing_components": missing_components,
                "weights_used": degraded_weights,
            }
            degraded_total_availability = (
                "DEGRADED"
                if degraded_total is not None
                else "MISSING_COMPONENT"
            )

        shadow = shadow_rows.get(game_id, {})
        shadow_spread_values = {
            "Shadow SP+": finite(
                shadow.get("predicted_updated_sp_plus_spread")
            ),
            "Shadow Sagarin": finite(
                shadow.get("predicted_updated_sagarin_spread")
            ),
        }
        # Both inputs are bookmaker home lines. Never substitute Market/SP+ or SP+ fallback.
        shadow_spread_value = fixed_weight_value(shadow_spread_values, shadow_spread_weights)
        shadow_spread_activated = (
            int(
                shadow.get(
                    "shadow_spread_updated_team_count"
                )
                or 0
            )
            >= 2
            and shadow.get(
                "validated_shadow_spread_inputs_validated"
            ) is True
        )

        shadow_spread_availability = status(
            shadow_spread_values,
            activated=shadow_spread_activated,
        )

        shadow_total_values = {
            "updated home SP+ offense": finite(shadow.get("home_sp_plus_offense_updated")),
            "updated away SP+ offense": finite(shadow.get("away_sp_plus_offense_updated")),
            "updated home SP+ defense": finite(shadow.get("home_sp_plus_defense_updated")),
            "updated away SP+ defense": finite(shadow.get("away_sp_plus_defense_updated")),
        }
        exact_shadow_inputs = (
            shadow.get("shadow_total_model_id") == SHADOW_TOTAL
            and shadow.get(
                "enhanced_spplus_od_v1_inputs_validated"
            ) is True
        )
        shadow_total_activated = bool(
            int(
                shadow.get(
                    "shadow_total_updated_team_count"
                )
                or 0
            )
            >= 2
            and shadow.get("no_lookahead_pass")
            and shadow_spec["valid"]
            and exact_shadow_inputs
        )
        shadow_total_value = (
            enhanced_shadow_total(
                shadow_total_values["updated home SP+ offense"],
                shadow_total_values["updated away SP+ offense"],
                shadow_total_values["updated home SP+ defense"],
                shadow_total_values["updated away SP+ defense"],
            )
            if shadow_total_activated
            else None
        )
        shadow_total_availability = status(
            shadow_total_values,
            activated=shadow_total_activated,
        )

        projections = {
            STANDARD_SPREAD: projection(
                model_id=STANDARD_SPREAD,
                formula_status="PRODUCTION_VALIDATED",
                values=spread_values,
                weights=spread_weights,
                availability=spread_availability,
                value_home_margin=official_spread_margin,
                value_home_line=(
                    -official_spread_margin
                    if official_spread_margin is not None
                    else None
                ),
                build_timestamp=built_at,
                freshness_timestamp=latest_timestamp(spread_source_rows),
                source_artifacts=[str(args.sources.relative_to(ROOT))],
                validation_status="HISTORICAL_FORMULA_VALIDATED_2021_2025",
                extra_status={
                    "resolution_mode": spread_resolution["mode"],
                    "available_components": spread_resolution["available_components"],
                    "missing_components": spread_resolution["missing_components"],
                    "weights_used": spread_resolution["weights_used"],
                },
                authority=(
                    "OFFICIAL"
                    if spread_availability == "AVAILABLE"
                    else "UNAVAILABLE"
                ),
            ),
            DEGRADED_SPREAD: projection(
                model_id=DEGRADED_SPREAD,
                formula_status="OPERATIONAL_DEGRADED",
                values=spread_values,
                weights=spread_weights,
                availability=degraded_spread_availability,
                value_home_margin=degraded_margin,
                value_home_line=(
                    -degraded_margin
                    if degraded_margin is not None
                    else None
                ),
                value=(
                    -degraded_margin
                    if degraded_margin is not None
                    else None
                ),
                build_timestamp=built_at,
                freshness_timestamp=latest_timestamp(spread_source_rows),
                source_artifacts=[str(args.sources.relative_to(ROOT))],
                validation_status="OPERATIONAL_ESTIMATE_FORMULA_PRESERVED",
                extra_status={
                    "resolution_mode": degraded_spread_resolution["mode"],
                    "available_components": degraded_spread_resolution["available_components"],
                    "missing_components": degraded_spread_resolution["missing_components"],
                    "weights_used": degraded_spread_resolution["weights_used"],
                },
                authority="OPERATIONAL_DEGRADED",
                status_label=(
                    "DEGRADED"
                    if degraded_spread_availability == "DEGRADED"
                    else "UNAVAILABLE"
                ),
                method="RENORMALIZED_AVAILABLE_CANONICAL_WEIGHTS",
                degraded_reason=(
                    "Missing required official sources: "
                    + ", ".join(degraded_spread_resolution["missing_components"])
                    if degraded_spread_resolution["missing_components"]
                    else "Official five-source projection is available."
                ),
                confidence_status=(
                    "DEGRADED"
                    if degraded_spread_availability == "DEGRADED"
                    else "NOT_APPLICABLE"
                ),
            ),
            STANDARD_TOTAL: projection(
                model_id=STANDARD_TOTAL,
                formula_status="PRODUCTION_VALIDATED",
                values=total_values,
                weights=total_weights,
                availability=total_availability,
                value_total=official_standard_total,
                build_timestamp=built_at,
                freshness_timestamp=latest_timestamp(total_source_rows),
                source_artifacts=[str(args.sources.relative_to(ROOT)), str(args.games.relative_to(ROOT))],
                validation_status="HISTORICAL_FORMULA_VALIDATED_2021_2025",
                extra_status={
                    "resolution_mode": total_resolution["mode"],
                    "available_components": total_resolution["available_components"],
                    "missing_components": total_resolution["missing_components"],
                    "weights_used": total_resolution["weights_used"],
                    "Massey Dual formula": "PUBLISHED_TOTAL_PLUS_POINT_SUM_DIVIDED_BY_TWO",
                },
                authority=(
                    "OFFICIAL"
                    if total_availability == "AVAILABLE"
                    else "UNAVAILABLE"
                ),
            ),
            DEGRADED_TOTAL: projection(
                model_id=DEGRADED_TOTAL,
                formula_status="OPERATIONAL_DEGRADED",
                values=total_values,
                weights=total_weights,
                availability=degraded_total_availability,
                value_total=degraded_total,
                value=degraded_total,
                build_timestamp=built_at,
                freshness_timestamp=latest_timestamp(total_source_rows),
                source_artifacts=[
                    str(args.sources.relative_to(ROOT)),
                    str(args.games.relative_to(ROOT)),
                ],
                validation_status="OPERATIONAL_ESTIMATE_FORMULA_PRESERVED",
                extra_status={
                    "resolution_mode": degraded_total_resolution["mode"],
                    "available_components": degraded_total_resolution["available_components"],
                    "missing_components": degraded_total_resolution["missing_components"],
                    "weights_used": degraded_total_resolution["weights_used"],
                    "Massey Dual formula": "PUBLISHED_TOTAL_PLUS_POINT_SUM_DIVIDED_BY_TWO",
                },
                authority="OPERATIONAL_DEGRADED",
                status_label=(
                    "DEGRADED"
                    if degraded_total_availability == "DEGRADED"
                    else "UNAVAILABLE"
                ),
                method="RENORMALIZED_AVAILABLE_CANONICAL_WEIGHTS",
                degraded_reason=(
                    "Missing required official sources: "
                    + ", ".join(degraded_total_resolution["missing_components"])
                    if degraded_total_resolution["missing_components"]
                    else "Official three-source projection is available."
                ),
                confidence_status=(
                    "DEGRADED"
                    if degraded_total_availability == "DEGRADED"
                    else "NOT_APPLICABLE"
                ),
            ),
            SHADOW_SPREAD: projection(
                model_id=SHADOW_SPREAD,
                formula_status="PRODUCTION_VALIDATED",
                values=shadow_spread_values,
                weights=shadow_spread_weights,
                availability=shadow_spread_availability,
                value_home_line=shadow_spread_value,
                value_home_margin=-shadow_spread_value if shadow_spread_value is not None else None,
                build_timestamp=built_at,
                freshness_timestamp=shadow.get("feature_cutoff") or shadow_timestamp,
                source_artifacts=[
                    str(args.shadow.relative_to(ROOT))
                ],
                validation_status="HISTORICAL_FORMULA_VALIDATED_2024_2025",
                extra_status={
                    "activation": (
                        "PRESENT"
                        if shadow_spread_activated
                        else "NOT_YET_ACTIVATED"
                    ),
                    "forbidden_fallbacks_rejected": "MARKET_SPPLUS_AND_SPPLUS_ONLY",
                },
            ),
            SHADOW_TOTAL: projection(
                model_id=SHADOW_TOTAL,
                formula_status="PRODUCTION_VALIDATED",
                values=shadow_total_values,
                weights=shadow_total_weights,
                availability=shadow_total_availability,
                value_total=shadow_total_value,
                build_timestamp=built_at,
                freshness_timestamp=shadow.get("feature_cutoff") or shadow_timestamp,
                source_artifacts=[str(args.shadow_spec.relative_to(ROOT)), str(args.shadow.relative_to(ROOT))],
                validation_status=(
                    "HISTORICAL_FORMULA_VALIDATED_LIVE_EXACT_INPUTS_PENDING"
                    if not shadow_total_activated
                    else "HISTORICAL_AND_LIVE_INPUT_PARITY_VALIDATED"
                ),
                extra_status={
                    "frozen_model_specification": "PRESENT" if shadow_spec["valid"] else "MISSING",
                    "exact_live_input_identity": "PRESENT" if exact_shadow_inputs else "MISSING",
                    "current_60_40_bridge_rejected": "YES",
                },
            ),
        }
        output_game = {
            "game_id": game_id,
            "season": game.get("season", games_payload.get("meta", {}).get("season", 2026)),
            "week": game.get("week"),
            "date": game.get("date"),
            "away_team": game.get("away_team"),
            "home_team": game.get("home_team"),
            "neutral_site": bool(game.get("neutral_site")),
            "projections": projections,
        }
        output_game["resolved_projections"] = {
            model_id: resolve_projection(output_game, model_id)
            for model_id in projections
        }
        output_game["operational_projections"] = {
            "spread": resolve_operational_projection(
                output_game,
                STANDARD_SPREAD,
            ),
            "total": resolve_operational_projection(
                output_game,
                STANDARD_TOTAL,
            ),
        }
        output_games.append(output_game)

    definitions = {
        STANDARD_SPREAD: {
            "formula": "(SP+ + FPI + TeamRankings + Sagarin Rating + DRatings) / 5",
            "required_components": list(SPREAD_COMPONENTS),
            "weights": spread_weights,
        },
        STANDARD_TOTAL: {
            "formula": "0.40 * SP+ + 0.40 * Massey Dual + 0.20 * Sagarin",
            "massey_dual_formula": "(published total + away predicted points + home predicted points) / 2",
            "required_components": list(TOTAL_COMPONENTS),
            "weights": total_weights,
        },
        DEGRADED_SPREAD: {
            "formula": "Renormalize the available weights from the official five-source spread model",
            "official_model_id": STANDARD_SPREAD,
            "required_components": list(SPREAD_COMPONENTS),
            "nominal_weights": spread_weights,
            "authority": "OPERATIONAL_DEGRADED_ONLY",
        },
        DEGRADED_TOTAL: {
            "formula": "Renormalize the available weights from the official 40/40/20 total model",
            "official_model_id": STANDARD_TOTAL,
            "required_components": list(TOTAL_COMPONENTS),
            "nominal_weights": total_weights,
            "authority": "OPERATIONAL_DEGRADED_ONLY",
        },
        SHADOW_SPREAD: {
            "formula": "(Shadow SP+ home fair spread + Shadow Sagarin home fair spread) / 2",
            "required_components": list(SHADOW_SPREAD_COMPONENTS),
            "weights": shadow_spread_weights,
        },
        SHADOW_TOTAL: {
            "formula": "0.5 * (updated home offense + updated away defense) + 0.5 * (updated away offense + updated home defense)",
            "updated_component_formula": "stale SP+ component + predicted provider delta",
            "required_components": list(SHADOW_TOTAL_COMPONENTS),
            "weights": shadow_total_weights,
            "frozen_specification": shadow_spec,
        },
    }
    if args.start_date and args.end_date and args.output.is_file():
        previous = json.loads(args.output.read_text(encoding="utf-8"))
        window_ids = {game["game_id"] for game in output_games}
        preserved = [
            game for game in previous.get("games", [])
            if str(game.get("game_id") or "") not in window_ids
        ]
        output_games = preserved + output_games
        output_games.sort(key=lambda game: (str(game.get("date") or ""), str(game.get("game_id") or "")))

    payload = {
        "schema_version": "current-game-projection-contract-v1",
        "built_at": built_at,
        "season": games_payload.get("meta", {}).get("season", 2026),
        "canonical_game_count": len(output_games),
        "policy": {
            "historical_betting_studies_are_formula_authority": True,
            "fixed_required_components": True,
            "official_missing_source_renormalization": False,
            "separate_operational_degraded_models": True,
            "minimum_components_for_degraded_projection": {
                DEGRADED_SPREAD: 3,
                DEGRADED_TOTAL: 1,
            },
            "page_local_projection_calculation_allowed": False,
            "resolver_policy": "STRICT_CANONICAL_ONLY_NO_FALLBACK_SUBSTITUTIONS",
            "unavailable_models_remain_unavailable": True,
            "degraded_models_preserve_official_formula_inputs_but_use_separate_identity": True,
        },
        "model_definitions": definitions,
        "games": output_games,
    }
    counts = {
        model_id: {
            state: sum(
                game["projections"][model_id]["availability_status"] == state
                for game in output_games
            )
            for state in (
                "AVAILABLE",
                "DEGRADED",
                "MISSING_COMPONENT",
                "NOT_APPLICABLE",
                "NOT_YET_ACTIVATED",
            )
        }
        for model_id in definitions
    }
    audit = {
        "status": "PASS",
        "schema_version": payload["schema_version"],
        "canonical_games": len(output_games),
        "unique_game_ids": len({game["game_id"] for game in output_games}),
        "model_ids": list(definitions),
        "availability_counts": counts,
        "shadow_total_frozen_specification": shadow_spec,
        "resolver_policy": "STRICT_CANONICAL_ONLY_NO_FALLBACK_SUBSTITUTIONS",
        "page_consumers_migrated": True,
        "network_requests": 0,
    }
    if audit["unique_game_ids"] != audit["canonical_games"]:
        raise SystemExit("Duplicate canonical game_id values in game projection contract")
    return payload, audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=Path, default=DEFAULT_GAMES)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--shadow", type=Path, default=DEFAULT_SHADOW)
    parser.add_argument("--shadow-spec", type=Path, default=DEFAULT_SHADOW_SPEC)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--built-at")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for required in (args.games, args.sources, args.shadow_spec):
        if not required.is_file():
            raise SystemExit(f"Missing required input: {required}")
    payload, audit = build(args)
    atomic_json(args.output, payload)
    atomic_json(args.audit, audit)
    print(json.dumps(audit, indent=2))
    print(f"Wrote {args.output}")
    print(f"Wrote {args.audit}")


if __name__ == "__main__":
    main()
