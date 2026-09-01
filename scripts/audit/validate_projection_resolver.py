#!/usr/bin/env python3
"""Validate canonical projection formulas, strict resolution and page adapters."""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projections.projection_resolver import (
    DEGRADED_SPREAD,
    DEGRADED_TOTAL,
    SHADOW_SPREAD,
    SHADOW_TOTAL,
    STANDARD_SPREAD,
    STANDARD_TOTAL,
    index_contract,
    load_contract,
    resolve_game,
    resolve_operational_game,
    resolve_operational_projection,
    resolve_projection,
)

CONTRACT = ROOT / "data/site/current_game_projection_contract.json"
MATCHUPS = ROOT / "data/site/matchups_view.json"
SHADOW_LINES = ROOT / "data/site/saturday_shadow_lines.json"
OUT = ROOT / "data/audits/projection_resolver_validation.json"


def close(a, b):
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a), float(b), abs_tol=1e-10)


def main():
    contract = load_contract(CONTRACT)
    index = index_contract(contract)
    definitions = contract["model_definitions"]
    checks = []

    expected = {
        STANDARD_SPREAD: {
            "required_components": ["SP+", "FPI", "TeamRankings", "DRatings"],
            "weights": {"SP+": .25, "FPI": .25, "TeamRankings": .25, "DRatings": .25},
        },
        STANDARD_TOTAL: {
            "required_components": ["SP+", "Massey Dual", "DRatings Total"],
            "weights": {"SP+": .4, "Massey Dual": .4, "DRatings Total": .2},
        },
        DEGRADED_SPREAD: {
            "required_components": ["SP+", "FPI", "TeamRankings", "DRatings"],
            "nominal_weights": {"SP+": .25, "FPI": .25, "TeamRankings": .25, "DRatings": .25},
        },
        DEGRADED_TOTAL: {
            "required_components": ["SP+", "Massey Dual", "DRatings Total"],
            "nominal_weights": {"SP+": .4, "Massey Dual": .4, "DRatings Total": .2},
        },
        SHADOW_SPREAD: {
            "required_components": ["Shadow SP+", "Shadow Sagarin"],
            "weights": {"Shadow SP+": .5, "Shadow Sagarin": .5},
        },
    }
    for model_id, wanted in expected.items():
        actual = definitions.get(model_id, {})
        checks.append({
            "check": f"definition:{model_id}",
            "passed": actual.get("required_components") == wanted["required_components"]
            and actual.get("weights", actual.get("nominal_weights"))
            == wanted.get("weights", wanted.get("nominal_weights")),
        })
    checks.append({
        "check": "definition:shadow_total_spplus_od_only",
        "passed": definitions.get(SHADOW_TOTAL, {}).get("required_components") == [
            "updated home SP+ offense", "updated away SP+ offense",
            "updated home SP+ defense", "updated away SP+ defense",
        ],
    })

    synthetic = resolve_projection({"projections": {STANDARD_SPREAD: {
        "availability_status": "MISSING_COMPONENT",
        "component_status": {"DRatings": "MISSING"},
    }}}, STANDARD_SPREAD)
    checks.append({
        "check": "unavailable_never_falls_back",
        "passed": synthetic["selection_status"] == "UNAVAILABLE"
        and synthetic["fallback_used"] is False
        and synthetic["value_home_margin"] is None,
    })

    degraded_under_official_id = resolve_projection({"projections": {STANDARD_SPREAD: {
        "availability_status": "AVAILABLE_DEGRADED",
        "value_home_margin": 3.5,
        "value_home_line": -3.5,
        "component_status": {"DRatings": "MISSING"},
    }}}, STANDARD_SPREAD)
    checks.append({
        "check": "official_model_rejects_available_degraded",
        "passed": degraded_under_official_id["selection_status"] == "UNAVAILABLE"
        and degraded_under_official_id["value_home_margin"] is None,
    })

    separated = {
        "projections": {
            STANDARD_SPREAD: {
                "availability_status": "MISSING_COMPONENT",
                "component_status": {"DRatings": "MISSING"},
            },
            DEGRADED_SPREAD: {
                "availability_status": "DEGRADED",
                "authority": "OPERATIONAL_DEGRADED",
                "value_home_margin": 3.5,
                "value_home_line": -3.5,
                "component_status": {"DRatings": "MISSING"},
            },
        }
    }
    degraded = resolve_operational_projection(separated, STANDARD_SPREAD)
    checks.append({
        "check": "separate_degraded_operational_path",
        "passed": degraded["selection_status"] == "AVAILABLE"
        and degraded["model_id"] == DEGRADED_SPREAD
        and degraded["authority"] == "OPERATIONAL_DEGRADED"
        and degraded["operational_degraded_used"] is True
        and degraded["value_home_margin"] == 3.5,
    })

    checks.append({
        "check": "all_contract_resolutions_strict",
        "passed": all(
            resolved.get("fallback_used") is False
            and resolved.get("selection_status") in {"AVAILABLE", "UNAVAILABLE"}
            and (
                resolved.get("selection_status") == "AVAILABLE"
                or all(resolved.get(k) is None for k in ("value_home_margin", "value_home_line", "value_total"))
            )
            for game in contract["games"]
            for resolved in game.get("resolved_projections", {}).values()
        ),
    })
    checks.append({
        "check": "official_models_never_available_degraded",
        "passed": all(
            game.get("projections", {})
            .get(model_id, {})
            .get("availability_status") != "AVAILABLE_DEGRADED"
            for game in contract["games"]
            for model_id in (STANDARD_SPREAD, STANDARD_TOTAL)
        ),
    })

    matchups = json.loads(MATCHUPS.read_text(encoding="utf-8"))
    matchup_ok = True
    for row in matchups.get("games", []):
        game_id = row.get("game", {}).get("game_id")
        spread = resolve_operational_game(index, game_id, STANDARD_SPREAD)
        total = resolve_operational_game(index, game_id, STANDARD_TOTAL)
        model = row.get("model", {})
        matchup_ok &= close(model.get("home_spread"), spread.get("value_home_line"))
        matchup_ok &= close(model.get("total"), total.get("value_total"))
        matchup_ok &= model.get("resolver", {}).get("spread", {}).get("fallback_used") is False
        matchup_ok &= model.get("resolver", {}).get("total", {}).get("fallback_used") is False
    checks.append({"check": "matchups_adapter_parity", "passed": bool(matchup_ok)})

    shadow_payload = json.loads(SHADOW_LINES.read_text(encoding="utf-8"))
    shadow_ok = True
    for row in shadow_payload.get("games", []):
        spread = resolve_game(index, row.get("game_id"), SHADOW_SPREAD)
        total = resolve_game(index, row.get("game_id"), SHADOW_TOTAL)
        shadow_ok &= close(row.get("saturday_shadow_spread"), spread.get("value_home_line"))
        shadow_ok &= close(row.get("saturday_shadow_total"), total.get("value_total"))
    checks.append({"check": "shadow_adapter_parity", "passed": bool(shadow_ok)})

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all(x["passed"] for x in checks) else "FAIL",
        "canonical_games": len(index),
        "checks": checks,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if payload["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
