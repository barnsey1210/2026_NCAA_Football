#!/usr/bin/env python3
"""Focused no-look-ahead audit for the market/SP+ Shadow bridge."""
from __future__ import annotations

import importlib.util
import json
import math
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
COMPONENTS = ROOT / "data/site/saturday_shadow_component_predictions.json"
LINES = ROOT / "data/site/saturday_shadow_lines.json"
ARTIFACT = ROOT / "data/research/shadow_component_bridge_v1/model_artifacts.json"
PARITY = ROOT / "data/research/shadow_component_bridge_v1/parity_report.json"
OUT = ROOT / "data/audits/saturday_shadow_production_integration.json"
FIXTURES = ROOT / "data/fixtures/shadow_activation_cases.json"
PRODUCTION_MODELS = {
    "market_rating_movement", "sp_plus_overall_movement",
    "sp_plus_offense_movement", "sp_plus_defense_improvement",
}


def close(a, b, tol=1e-8):
    return a is not None and b is not None and math.isclose(float(a), float(b), abs_tol=tol)


def iso(value):
    if not value:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def load_component_module():
    path = ROOT / "scripts/site/build_saturday_shadow_component_predictions.py"
    spec = importlib.util.spec_from_file_location("shadow_component_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    payload = json.loads(COMPONENTS.read_text())
    lines = json.loads(LINES.read_text())
    artifact = json.loads(ARTIFACT.read_text())
    parity = json.loads(PARITY.read_text())
    rows = payload["games"]
    checks = []

    def check(name, passed, detail=""):
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    check("frozen artifacts not refit", payload.get("frozen_models_loaded_without_refit") is True)
    check("FPI and TeamRankings excluded", payload.get("fpi_teamrankings_used") is False and not ({"fpi_next_game_spread", "teamrankings_next_game_spread"} & PRODUCTION_MODELS))
    check("targeted parity passed", parity.get("status") == "PASS")
    check("fixture isolation", payload.get("fixture_only") is False and all(r.get("fixture_only") is False for r in rows))
    check("no dry-run source paths", all("dry_run" not in " ".join(r.get("feature_sources") or []).lower() for r in rows))
    check("production rejects fixture rows", payload.get("fixture_only") is False and not any(r.get("fixture_only") for r in rows))

    baseline_sides = []
    postgame_sides = []
    snapshot_order = []
    for row in rows:
        for side in ("away", "home"):
            status = row.get(f"{side}_component_status")
            if status == "preseason_baseline":
                baseline_sides.append((row, side))
                check(
                    f"zero baseline {row['game_id']} {side}",
                    row.get(f"{side}_movement_estimator_invoked") is False
                    and close(row.get(f"{side}_predicted_sp_plus_change"), 0.0)
                    and close(row.get(f"{side}_predicted_sp_plus_offense_change"), 0.0)
                    and close(row.get(f"{side}_predicted_sp_plus_defense_change"), 0.0),
                )
            elif status == "postgame_model_update":
                postgame_sides.append((row, side))
                check(f"completed team invokes estimator {row['game_id']} {side}", row.get(f"{side}_movement_estimator_invoked") is True)
            stamp = iso(row.get(f"{side}_sp_plus_snapshot_timestamp"))
            cutoff = iso(row.get("generated_at"))
            if stamp and cutoff:
                snapshot_order.append(stamp <= cutoff)
    check("entering SP+ snapshots precede cutoff", all(snapshot_order) and all(snapshot_order), f"checked={len(snapshot_order)}")

    for row in rows:
        if row.get("predicted_updated_sp_plus_spread") is not None:
            hfa = 0.0 if row.get("neutral_site") else 2.5
            expected = -(row["home_sp_plus_updated"] - row["away_sp_plus_updated"] + hfa)
            check(f"HFA once {row['game_id']}", close(expected, row["predicted_updated_sp_plus_spread"]))
        if row.get("internal_shadow_total_baseline") is not None:
            expected = .60 * row["predicted_sp_plus_component_total"] + .40 * row["existing_projected_total"] - 1.1573
            check(f"total correction once {row['game_id']}", close(expected, row["internal_shadow_total_baseline"]))
        if row.get("market_readiness_state") == "independent_market_ready" and row.get("shadow_display_ready"):
            check(f"target excluded {row['game_id']}", row.get("target_game_excluded") is True)
            expected = .5 * row["predicted_market_rating_spread"] + .5 * row["predicted_updated_sp_plus_spread"]
            check(f"50/50 arithmetic {row['game_id']}", close(expected, row["shadow_spread"]))
        elif row.get("shadow_display_ready") and row.get("shadow_spread") is not None:
            check(f"SP+ fallback {row['game_id']}", close(row["shadow_spread"], row["predicted_updated_sp_plus_spread"]) and row.get("shadow_spread_formula") == "SP+ Fallback")
        if row.get("completed_team_update_count") == 0:
            check(
                f"preseason gate {row['game_id']}",
                row.get("has_genuine_postgame_update") is False
                and row.get("shadow_display_ready") is False
                and row.get("shadow_spread") is None
                and row.get("shadow_total") is None
                and row.get("spread_impact") is None
                and row.get("total_impact") is None
                and row.get("spread_value_label") == "Unavailable"
                and row.get("total_value_label") == "Unavailable",
            )
            if row.get("internal_shadow_spread_baseline") is not None:
                check(f"Current Model spread retained {row['game_id']}", row.get("current_model_spread") is not None)
            if row.get("internal_shadow_total_baseline") is not None:
                check(f"Current Model total retained {row['game_id']}", row.get("existing_projected_total") is not None)

    # In-memory mixed-state contract: one frozen postgame row and one canonical
    # preseason baseline. It never enters a production artifact.
    component = load_component_module()
    feature = pd.read_csv(ROOT / "data/research/sp_plus_total_movement/sp_plus_component_features.csv", low_memory=False).iloc[0].to_dict()
    baseline = next(iter(component.latest_sp_plus_rows().values()))
    probe = {"_models": artifact["models"]}
    component.apply_sp_plus_state(probe, "away", feature, None)
    component.apply_sp_plus_state(probe, "home", None, baseline)
    check("mixed-state fixture", probe["away_component_status"] == "postgame_model_update" and probe["home_component_status"] == "preseason_baseline" and probe["away_movement_estimator_invoked"] is True and probe["home_movement_estimator_invoked"] is False)

    fixture_payload = json.loads(FIXTURES.read_text())
    check("fixture file isolated", fixture_payload.get("fixture_only") is True and all(x.get("fixture_only") is True for x in fixture_payload.get("cases", [])))
    fixture_results = []
    for case in fixture_payload.get("cases", []):
        updates = sum(case.get(f"{side}_update_state") == "postgame_updated" for side in ("away", "home"))
        has_update = updates > 0
        spread_ready = has_update and case.get("spread_inputs_ready") is True
        total_ready = has_update and case.get("total_inputs_ready") is True
        display_ready = spread_ready or total_ready
        actual = {
            "completed_team_update_count": updates,
            "has_genuine_postgame_update": has_update,
            "shadow_display_ready": display_ready,
            "spread_active": spread_ready,
            "total_active": total_ready,
            "spread_impact_display": "0.0" if spread_ready and case.get("spread_impact") == 0 else ("—" if not spread_ready else "numeric"),
            "total_value_tier": case.get("total_value_tier") if total_ready and case.get("market_total_available") else None,
        }
        expected = case.get("expected", {})
        passed = all(actual.get(k) == v for k, v in expected.items())
        fixture_results.append({"name": case.get("name"), "passed": passed, "actual": actual, "expected": expected})
        check(f"activation fixture: {case.get('name')}", passed)

    summary = {
        "games": len(rows),
        "internal_baseline_games": sum(r.get("internal_shadow_spread_baseline") is not None or r.get("internal_shadow_total_baseline") is not None for r in rows),
        "displayed_shadow_games": sum(r.get("shadow_display_ready") is True for r in rows),
        "postgame_updated_games": sum(r.get("away_component_status") == "postgame_model_update" or r.get("home_component_status") == "postgame_model_update" for r in rows),
        "independent_50_50_games": sum(r.get("market_readiness_state") == "independent_market_ready" for r in rows),
        "unavailable_games": sum(r.get("shadow_spread") is None for r in rows),
        "populated_totals": sum(r.get("shadow_total") is not None for r in rows),
        "line_rows": len(lines.get("games", [])),
        "baseline_team_sides": len(baseline_sides),
        "postgame_team_sides": len(postgame_sides),
    }
    report = {"status": "PASS" if all(c["passed"] for c in checks) else "FAIL", "summary": summary, "fixture_results": fixture_results, "checks": checks}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], **summary, "failed_checks": [c["check"] for c in checks if not c["passed"]]}, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
