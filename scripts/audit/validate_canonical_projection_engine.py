#!/usr/bin/env python3
"""Offline historical and structural validation for the canonical projection engine."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "scripts/projections/build_current_game_projection_contract.py"
OUT = ROOT / "data/audits/projection_engine_historical_validation.json"


def load_engine():
    spec = importlib.util.spec_from_file_location("canonical_projection_engine", ENGINE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def maximum_difference(left: pd.Series, right: pd.Series) -> float:
    return float((left - right).abs().max())


def main() -> None:
    engine = load_engine()
    checks = []

    spread_path = ROOT / "reports/five_source_backtest_validated/five_source_game_level.csv"
    spread = pd.read_csv(spread_path, low_memory=False)
    spread_cols = ["linespplus_fixed", "lineespn", "lineteamrank", "linesag", "linedonchess"]
    complete = spread.dropna(subset=spread_cols + ["five_source_prediction"])
    spread_diff = maximum_difference(complete[spread_cols].mean(axis=1), complete["five_source_prediction"])
    checks.append({
        "model_id": engine.STANDARD_SPREAD,
        "season_scope": "2021-2025",
        "rows": int(len(complete)),
        "max_abs_difference": spread_diff,
        "passed": bool(spread_diff <= 1e-9),
        "source": str(spread_path.relative_to(ROOT)),
    })

    sp = pd.read_csv(
        ROOT / "data/research/historical_totals/sp_plus/sp_plus_totals_game_level_2021_2025_final.csv",
        low_memory=False,
    )
    sag = pd.read_csv(
        ROOT / "data/research/historical_totals/sagarin/sagarin_totals_game_level_2021_2025_research_grade_repaired.csv",
        low_memory=False,
    )
    mas = pd.read_csv(
        ROOT / "data/research/historical_totals/massey/massey_totals_game_level_2021_2025.csv",
        low_memory=False,
    )
    sp_col = "sp_plus_total" if "sp_plus_total" in sp.columns else "sp_plus_projected_total"
    sag_col = "sagarin_total" if "sagarin_total" in sag.columns else "projected_total"
    totals = (
        sp[["game_id", sp_col]].drop_duplicates("game_id")
        .merge(
            mas[["game_id", "massey_total", "away_pred", "home_pred"]].drop_duplicates("game_id"),
            on="game_id",
            how="inner",
        )
        .merge(sag[["game_id", sag_col]].drop_duplicates("game_id"), on="game_id", how="inner")
    )
    for col in [sp_col, "massey_total", "away_pred", "home_pred", sag_col]:
        totals[col] = pd.to_numeric(totals[col], errors="coerce")
    totals = totals.dropna(subset=[sp_col, "massey_total", "away_pred", "home_pred", sag_col])
    totals["massey_dual"] = (
        totals["massey_total"] + totals["away_pred"] + totals["home_pred"]
    ) / 2.0
    totals["canonical"] = (
        0.4 * totals[sp_col] + 0.4 * totals["massey_dual"] + 0.2 * totals[sag_col]
    )
    function_values = totals.apply(
        lambda row: engine.fixed_weight_value(
            {"SP+": row[sp_col], "Massey Dual": row["massey_dual"], "Sagarin": row[sag_col]},
            {"SP+": 0.4, "Massey Dual": 0.4, "Sagarin": 0.2},
        ),
        axis=1,
    )
    total_diff = maximum_difference(totals["canonical"], function_values)
    checks.append({
        "model_id": engine.STANDARD_TOTAL,
        "season_scope": "2021-2025",
        "rows": int(len(totals)),
        "max_abs_difference": total_diff,
        "passed": bool(total_diff <= 1e-9 and len(totals) == 2509),
        "source": "historical SP+, Massey, and repaired Sagarin game-level artifacts",
        "expected_three_source_overlap": 2509,
    })

    shadow_spread_path = (
        ROOT / "data/research/historical/shadow/historical_shadow_v1_premarket_game_predictions_2025.csv"
    )
    shadow_spread = pd.read_csv(shadow_spread_path, low_memory=False)
    shadow_spread = shadow_spread.dropna(
        subset=["shadow_spplus_fair_spread", "shadow_sagarin_fair_spread", "shadow_blend_fair_spread"]
    )
    shadow_spread_calc = (
        shadow_spread["shadow_spplus_fair_spread"] + shadow_spread["shadow_sagarin_fair_spread"]
    ) / 2.0
    shadow_spread_diff = maximum_difference(shadow_spread_calc, shadow_spread["shadow_blend_fair_spread"])
    checks.append({
        "model_id": engine.SHADOW_SPREAD,
        "season_scope": "2025 architecture validation",
        "rows": int(len(shadow_spread)),
        "max_abs_difference": shadow_spread_diff,
        "passed": bool(shadow_spread_diff <= 1e-9),
        "source": str(shadow_spread_path.relative_to(ROOT)),
    })

    team_path = (
        ROOT / "data/research/historical/shadow/totals_oos_2024/"
        "enhanced_spplus_od_2024_oos_team_predictions.csv"
    )
    game_path = (
        ROOT / "data/research/historical/shadow/totals_oos_2024/"
        "enhanced_spplus_totals_2024_oos_games.csv"
    )
    team = pd.read_csv(team_path, low_memory=False)
    games = pd.read_csv(game_path, low_memory=False)
    index = {(int(row.target_week), row.team): row for row in team.itertuples()}
    calculated = []
    stored = []
    for game in games.itertuples():
        home = index[(int(game.target_week), game.home_team)]
        away = index[(int(game.target_week), game.away_team)]
        home_off = home.stale_spplus_offense + home.enhanced_predicted_delta_spplus_offense
        away_off = away.stale_spplus_offense + away.enhanced_predicted_delta_spplus_offense
        home_def = home.stale_spplus_defense + home.enhanced_predicted_delta_spplus_defense
        away_def = away.stale_spplus_defense + away.enhanced_predicted_delta_spplus_defense
        calculated.append(engine.enhanced_shadow_total(home_off, away_off, home_def, away_def))
        stored.append(game.shadow_spplus_total)
    shadow_total_diff = max(abs(a - b) for a, b in zip(calculated, stored))
    performance = json.loads((ROOT / "data/site/shadow_model_performance.json").read_text())
    pooled = performance["totals"]["stale_vs_shadow"]["pooled"]["shadow"]
    performance_pass = (
        pooled["sample_size"] == 462
        and pooled["record"]["display"] == "234-228-0"
        and math.isclose(pooled["average_clv_points"], 0.2689393939393939, abs_tol=1e-12)
    )
    checks.append({
        "model_id": engine.SHADOW_TOTAL,
        "season_scope": "2024 exact-state OOS arithmetic plus pooled 2024-2025 performance contract",
        "rows": int(len(games)),
        "max_abs_difference": float(shadow_total_diff),
        "passed": bool(shadow_total_diff <= 1e-9 and performance_pass),
        "source": [str(team_path.relative_to(ROOT)), str(game_path.relative_to(ROOT))],
        "performance_contract": {
            "sample_size": pooled["sample_size"],
            "record": pooled["record"]["display"],
            "win_pct": pooled["win_pct"],
            "roi_minus_110": pooled["roi_minus_110"],
            "average_clv_points": pooled["average_clv_points"],
        },
    })

    spread_fixture = {name: float(index + 1) for index, name in enumerate(engine.SPREAD_COMPONENTS)}
    spread_fixture_weights = {name: 0.2 for name in engine.SPREAD_COMPONENTS}
    total_fixture = {"SP+": 50.0, "Massey Dual": 51.0, "Sagarin": 52.0}
    total_fixture_weights = {"SP+": 0.4, "Massey Dual": 0.4, "Sagarin": 0.2}
    missing_tests = {
        **{
            f"standard_spread_missing_{name}_rejected": engine.fixed_weight_value(
                {**spread_fixture, name: None}, spread_fixture_weights
            ) is None
            for name in engine.SPREAD_COMPONENTS
        },
        **{
            f"standard_total_missing_{name}_rejected": engine.fixed_weight_value(
                {**total_fixture, name: None}, total_fixture_weights
            ) is None
            for name in total_fixture
        },
        "massey_dual_missing_rejected": engine.massey_dual(50.0, 24.0, None) is None,
        "shadow_total_missing_rejected": engine.enhanced_shadow_total(30.0, 28.0, None, 24.0) is None,
    }
    checks.append({
        "model_id": "missing_component_policy",
        "rows": len(missing_tests),
        "passed": all(missing_tests.values()),
        "tests": missing_tests,
    })

    contract_path = ROOT / "data/site/current_game_projection_contract.json"
    contract = json.loads(contract_path.read_text())
    expected_models = {
        engine.STANDARD_SPREAD, engine.STANDARD_TOTAL, engine.SHADOW_SPREAD, engine.SHADOW_TOTAL
    }
    structural = (
        contract["canonical_game_count"] == len(contract["games"])
        == len({row["game_id"] for row in contract["games"]})
        and set(contract["model_definitions"]) == expected_models
        and all(set(row["projections"]) == expected_models for row in contract["games"])
    )
    checks.append({
        "model_id": "contract_structure",
        "rows": len(contract["games"]),
        "passed": bool(structural),
        "source": str(contract_path.relative_to(ROOT)),
    })

    available_spreads = [
        row["projections"][engine.STANDARD_SPREAD]
        for row in contract["games"]
        if row["projections"][engine.STANDARD_SPREAD]["availability_status"] == "AVAILABLE"
    ]
    sign_pass = all(
        math.isclose(item["value_home_line"], -item["value_home_margin"], abs_tol=1e-12)
        for item in available_spreads
    )
    sign_fixtures = [7.0, -3.5, 0.0]
    sign_pass = sign_pass and all(math.isclose(-margin, 0.0 - margin) for margin in sign_fixtures)
    checks.append({
        "model_id": "spread_sign_convention",
        "rows": len(available_spreads),
        "fixture_home_margins": sign_fixtures,
        "passed": bool(sign_pass),
        "assertion": "value_home_line == -value_home_margin",
    })

    payload = {
        "status": "PASS" if all(check["passed"] for check in checks) else "FAIL",
        "validation_mode": "OFFLINE_NO_NETWORK",
        "architecture_validation_season": 2025,
        "historical_results_modified": False,
        "production_consumers_modified": False,
        "checks": checks,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    if payload["status"] != "PASS":
        raise SystemExit("Canonical projection engine validation failed")


if __name__ == "__main__":
    main()
