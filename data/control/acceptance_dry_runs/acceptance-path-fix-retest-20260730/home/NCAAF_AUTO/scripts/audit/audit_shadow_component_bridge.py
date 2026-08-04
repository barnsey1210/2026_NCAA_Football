#!/usr/bin/env python3
"""Fail-fast integrity audit for the research-only Shadow component bridge."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/research/shadow_component_bridge_v1"


def main() -> None:
    failures: list[str] = []
    artifact = json.loads((OUT / "model_artifacts.json").read_text())
    parity = json.loads((OUT / "parity_report.json").read_text())
    current = json.loads((OUT / "current_2026_adapter_status.json").read_text())

    if artifact.get("fit_seasons") != [2021, 2022, 2023, 2024]:
        failures.append("artifact fit seasons are not exactly 2021-2024")
    if artifact.get("holdout_excluded") != [2025, 2026]:
        failures.append("2025/2026 holdout exclusion is not explicit")

    states = dict(artifact.get("models", {}))
    states["sp_plus_component_total"] = artifact.get("sp_plus_component_total", {})
    required = {"feature_order", "imputation", "scaling", "intercept", "coefficients"}
    for name, state in states.items():
        missing = sorted(required - set(state))
        if missing:
            failures.append(f"{name}: missing state {', '.join(missing)}")
            continue
        n = len(state["feature_order"])
        if len(state["coefficients"]) != n:
            failures.append(f"{name}: coefficient count does not match feature order")
        for label, values in (
            ("imputation", state["imputation"].get("values", [])),
            ("scaling mean", state["scaling"].get("mean", [])),
            ("scaling std", state["scaling"].get("std", [])),
        ):
            if len(values) != n:
                failures.append(f"{name}: {label} length does not match feature order")

    source = (ROOT / "scripts/research/build_predicted_fpi_tr_saturday.py").read_text()
    forbidden = "[['fpi_target','tr_target']].notna().mean"
    if forbidden in source:
        failures.append("FPI/TR source_coverage still depends on target availability")
    for expected in (
        "home_prior_fpi_team_margin", "away_prior_fpi_team_margin",
        "home_prior_tr_team_margin", "away_prior_tr_team_margin",
        "predicted_market_spread", "predicted_updated_sp_spread",
    ):
        if expected not in source:
            failures.append(f"prospective source_coverage input absent: {expected}")

    if parity.get("status") != "PASS":
        failures.append("locked-2025 replay parity did not pass")
    expected_components = {
        "market", "sp_plus", "sp_offense", "sp_defense_improvement",
        "fpi", "teamrankings", "final_spread_ensemble",
        "sp_plus_component_total", "final_corrected_total",
    }
    observed = {row.get("component") for row in parity.get("checks", []) if row.get("passed")}
    if observed != expected_components:
        failures.append(f"parity component coverage mismatch: {sorted(observed)}")

    if current.get("status") != "ready_zero_completed_games" or current.get("rows") != []:
        failures.append("zero-completed-game 2026 behavior is not clean")

    matrix = pd.read_csv(OUT / "canonical_pipeline_matrix.csv")
    if matrix.empty or matrix["required_model_feature"].isna().any():
        failures.append("canonical pipeline matrix is empty or malformed")

    report = {
        "status": "FAIL" if failures else "PASS",
        "artifact_models_checked": len(states),
        "parity_components_checked": len(observed),
        "fit_seasons": artifact.get("fit_seasons"),
        "zero_game_2026_status": current.get("status"),
        "failures": failures,
    }
    (OUT / "bridge_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
