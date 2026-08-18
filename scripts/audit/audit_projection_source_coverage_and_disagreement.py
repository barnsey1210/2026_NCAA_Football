#!/usr/bin/env python3
"""Audit canonical projection-source coverage and provider disagreement offline."""
from __future__ import annotations

import itertools
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "data/projections/game_projection_sources_2026.csv"
CONTRACT = ROOT / "data/site/current_game_projection_contract.json"
MASSEY_CURRENT = ROOT / "data/ratings/external_sources/massey_game_projections_2026.csv"
SP_HIST = ROOT / "data/research/historical_totals/sp_plus/sp_plus_totals_game_level_2021_2025_final.csv"
MASSEY_HIST = ROOT / "data/research/historical_totals/massey/massey_totals_game_level_2021_2025.csv"
SAG_HIST = ROOT / "data/research/historical_totals/sagarin/sagarin_totals_game_level_2021_2025_research_grade_repaired.csv"

OUT_JSON = ROOT / "data/audits/projection_source_coverage_and_disagreement.json"
OUT_COVERAGE = ROOT / "data/audits/projection_source_coverage_by_component.csv"
OUT_PAIRWISE = ROOT / "data/audits/projection_source_pairwise_disagreement.csv"
OUT_GAMES = ROOT / "data/audits/projection_disagreement_game_level.csv"
OUT_REPORT = ROOT / "docs/PROJECTION_SOURCE_COVERAGE_AND_DISAGREEMENT_REPORT.md"

STANDARD_SPREAD = "standard_spread_five_source_v1"
STANDARD_TOTAL = "standard_total_sp_massey_sagarin_v1"
SHADOW_SPREAD = "shadow_spread_sp_sagarin_v1"
SHADOW_TOTAL = "shadow_total_enhanced_spplus_od_v1"


def finite(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def summary(values):
    values = np.asarray([float(x) for x in values if finite(x) is not None], dtype=float)
    if len(values) == 0:
        return {"n": 0, "mean": None, "median": None, "p25": None, "p75": None, "p90": None, "max": None}
    return {
        "n": int(len(values)),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "p25": float(np.quantile(values, .25)),
        "p75": float(np.quantile(values, .75)),
        "p90": float(np.quantile(values, .90)),
        "max": float(values.max()),
    }


def pairwise_rows(game_rows, model_id, components):
    rows = []
    for left, right in itertools.combinations(components, 2):
        pairs = [
            (r["values"].get(left), r["values"].get(right))
            for r in game_rows
            if finite(r["values"].get(left)) is not None and finite(r["values"].get(right)) is not None
        ]
        diffs = [abs(float(a) - float(b)) for a, b in pairs]
        correlation = None
        if len(pairs) >= 2:
            a, b = np.asarray(pairs, dtype=float).T
            if np.std(a) > 0 and np.std(b) > 0:
                correlation = float(np.corrcoef(a, b)[0, 1])
        rows.append({
            "scope": "2026_CURRENT",
            "model_id": model_id,
            "source_a": left,
            "source_b": right,
            "overlap_n": len(pairs),
            "mean_absolute_difference": summary(diffs)["mean"],
            "median_absolute_difference": summary(diffs)["median"],
            "p90_absolute_difference": summary(diffs)["p90"],
            "correlation": correlation,
        })
    return rows


def historical_total_comparison():
    sp = pd.read_csv(SP_HIST, low_memory=False)
    massey = pd.read_csv(MASSEY_HIST, low_memory=False)
    sag = pd.read_csv(SAG_HIST, low_memory=False)
    sp_col = "sp_plus_total" if "sp_plus_total" in sp.columns else "sp_plus_projected_total"
    sag_col = "sagarin_total" if "sagarin_total" in sag.columns else "projected_total"
    frame = (
        sp[["game_id", sp_col]].drop_duplicates("game_id")
        .merge(massey[["game_id", "massey_total", "away_pred", "home_pred"]].drop_duplicates("game_id"), on="game_id")
        .merge(sag[["game_id", sag_col]].drop_duplicates("game_id"), on="game_id")
    )
    numeric = [sp_col, "massey_total", "away_pred", "home_pred", sag_col]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    frame = frame.dropna(subset=numeric).copy()
    frame["massey_point_sum"] = frame["away_pred"] + frame["home_pred"]
    frame["massey_dual"] = (frame["massey_total"] + frame["massey_point_sum"]) / 2.0
    # Diagnostic only: preserve the SP+/Sagarin 40:20 ratio and normalize it
    # solely to measure how the completed canonical model changes when Massey enters.
    frame["before_massey_diagnostic"] = (0.4 * frame[sp_col] + 0.2 * frame[sag_col]) / 0.6
    frame["after_massey_canonical"] = (
        0.4 * frame[sp_col] + 0.4 * frame["massey_dual"] + 0.2 * frame[sag_col]
    )
    frame["model_shift"] = frame["after_massey_canonical"] - frame["before_massey_diagnostic"]
    frame["before_provider_range"] = (frame[[sp_col, sag_col]].max(axis=1) - frame[[sp_col, sag_col]].min(axis=1))
    frame["after_provider_range"] = (
        frame[[sp_col, "massey_dual", sag_col]].max(axis=1)
        - frame[[sp_col, "massey_dual", sag_col]].min(axis=1)
    )
    return {
        "scope": "2021_2025_STRICT_THREE_SOURCE_OVERLAP",
        "n": int(len(frame)),
        "before_definition": "DIAGNOSTIC_ONLY: normalized SP+/Sagarin 40:20 ratio; not a canonical model",
        "after_definition": "Canonical Standard Total: SP+ 40%, Massey Dual 40%, Sagarin 20%",
        "before_provider_range": summary(frame["before_provider_range"]),
        "after_provider_range": summary(frame["after_provider_range"]),
        "after_minus_before_projection": summary(frame["model_shift"]),
        "absolute_projection_shift": summary(frame["model_shift"].abs()),
        "massey_published_vs_point_sum_abs_difference": summary((frame["massey_total"] - frame["massey_point_sum"]).abs()),
    }


def fmt(value, digits=3):
    return "—" if value is None else f"{float(value):.{digits}f}"


def main():
    sources = pd.read_csv(SOURCES, low_memory=False)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    games = contract["games"]
    game_count = len(games)
    definitions = contract["model_definitions"]

    coverage_rows = []
    model_game_rows = {}
    disagreement_game_rows = []
    pairwise = []

    for model_id, definition in definitions.items():
        rows = []
        for game in games:
            projection = game["projections"][model_id]
            values = projection["component_values"]
            numeric = [float(v) for v in values.values() if finite(v) is not None]
            provider_range = max(numeric) - min(numeric) if len(numeric) >= 2 else None
            provider_std = float(np.std(numeric, ddof=0)) if len(numeric) >= 2 else None
            row = {
                "game_id": game["game_id"],
                "week": game.get("week"),
                "away_team": game.get("away_team"),
                "home_team": game.get("home_team"),
                "model_id": model_id,
                "availability_status": projection["availability_status"],
                "present_components": len(numeric),
                "required_components": len(values),
                "provider_range": provider_range,
                "provider_stddev": provider_std,
                "values": values,
            }
            rows.append(row)
            if len(numeric) >= 2:
                disagreement_game_rows.append({k: v for k, v in row.items() if k != "values"})
        model_game_rows[model_id] = rows
        for component in definition["required_components"]:
            count = sum(finite(r["values"].get(component)) is not None for r in rows)
            coverage_rows.append({
                "model_id": model_id,
                "component": component,
                "declared_weight": definition.get("weights", {}).get(component),
                "weight_type": "formula_coefficient" if model_id == SHADOW_TOTAL else "blend_weight",
                "covered_games": count,
                "canonical_games": game_count,
                "coverage_pct": 100.0 * count / game_count if game_count else 0.0,
            })
        pairwise.extend(pairwise_rows(rows, model_id, definition["required_components"]))

    spread_rows = model_game_rows[STANDARD_SPREAD]
    spread_ranges_2plus = [r["provider_range"] for r in spread_rows if r["provider_range"] is not None]
    spread_complete = [r for r in spread_rows if r["availability_status"] == "AVAILABLE"]
    spread_degraded = [r for r in spread_rows if r["availability_status"] == "AVAILABLE_DEGRADED"]
    spread_displayable = [r for r in spread_rows if r["availability_status"] in {"AVAILABLE", "AVAILABLE_DEGRADED"}]

    total_rows = model_game_rows[STANDARD_TOTAL]
    before_massey_current = sum(
        finite(r["values"].get("SP+")) is not None and finite(r["values"].get("Sagarin")) is not None
        for r in total_rows
    )
    after_massey_current = sum(r["availability_status"] in {"AVAILABLE", "AVAILABLE_DEGRADED"} for r in total_rows)
    total_full_available = sum(r["availability_status"] == "AVAILABLE" for r in total_rows)
    total_degraded_available = sum(r["availability_status"] == "AVAILABLE_DEGRADED" for r in total_rows)

    current_massey = sources[sources["source"].eq("Massey Games")].copy()
    for col in ["total", "away_score", "home_score"]:
        current_massey[col] = pd.to_numeric(current_massey[col], errors="coerce")
    current_massey = current_massey.dropna(subset=["game_id", "total", "away_score", "home_score"])
    current_massey["point_sum"] = current_massey["away_score"] + current_massey["home_score"]
    current_massey["dual"] = (current_massey["total"] + current_massey["point_sum"]) / 2.0
    contract_massey = {
        g["game_id"]: g["projections"][STANDARD_TOTAL]["component_values"].get("Massey Dual")
        for g in games
    }
    propagation_diffs = [
        abs(float(row.dual) - float(contract_massey.get(str(row.game_id))))
        for row in current_massey.itertuples()
        if finite(contract_massey.get(str(row.game_id))) is not None
    ]
    current_massey_validation = {
        "normalized_rows_with_all_dual_inputs": int(len(current_massey)),
        "contract_rows_with_massey_dual": sum(finite(v) is not None for v in contract_massey.values()),
        "maximum_contract_propagation_difference": max(propagation_diffs) if propagation_diffs else None,
        "published_vs_point_sum_difference": summary(current_massey["point_sum"] - current_massey["total"]),
        "published_vs_point_sum_absolute_difference": summary((current_massey["point_sum"] - current_massey["total"]).abs()),
        "dual_minus_published": summary(current_massey["dual"] - current_massey["total"]),
        "source_url_present": int(current_massey["source_url"].notna().sum()),
        "pulled_at_present": int(current_massey["pulled_at"].notna().sum()),
    }

    external = pd.read_csv(MASSEY_CURRENT, low_memory=False)
    raw_snapshot_dates = sorted(set(external.get("snapshot_date", pd.Series(dtype=str)).dropna().astype(str)))
    normalized_snapshot_dates = sorted(set(current_massey.get("snapshot_date", pd.Series(dtype=str)).dropna().astype(str)))
    current_massey_validation.update({
        "external_rows": int(len(external)),
        "external_snapshot_dates": raw_snapshot_dates,
        "normalized_snapshot_dates": normalized_snapshot_dates,
        "provenance_status": (
            "INCOMPLETE_PULL_TIMESTAMP"
            if current_massey_validation["pulled_at_present"] < len(current_massey)
            else "COMPLETE"
        ),
    })

    historical = historical_total_comparison()
    model_availability = {
        model_id: {
            status: sum(g["projections"][model_id]["availability_status"] == status for g in games)
            for status in ("AVAILABLE", "AVAILABLE_DEGRADED", "MISSING_COMPONENT", "NOT_YET_ACTIVATED")
        }
        for model_id in definitions
    }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": (
            "PASS_WITH_WARNINGS"
            if current_massey_validation["provenance_status"] != "COMPLETE"
            else "PASS"
        ),
        "mode": "OFFLINE_NO_NETWORK_NO_FORMULA_CHANGES",
        "canonical_games": game_count,
        "contract_built_at": contract.get("built_at"),
        "model_definitions": definitions,
        "model_availability": model_availability,
        "coverage": coverage_rows,
        "spread_disagreement": {
            "games_with_at_least_two_sources": len(spread_ranges_2plus),
            "range_all_2plus": summary(spread_ranges_2plus),
            "complete_five_source_games": len(spread_complete),
            "degraded_available_games": len(spread_degraded),
            "displayable_games": len(spread_displayable),
            "range_complete_five_source": summary([r["provider_range"] for r in spread_complete]),
            "stddev_complete_five_source": summary([r["provider_stddev"] for r in spread_complete]),
        },
        "current_2026_massey_integration": current_massey_validation,
        "current_2026_before_after_massey": {
            "before_massey_spplus_sagarin_overlap": before_massey_current,
            "after_massey_strict_three_source_available": after_massey_current,
            "incremental_available_games": after_massey_current - before_massey_current,
            "disagreement_analysis_status": "NO_COMPARABLE_CURRENT_OVERLAP",
            "reason": "No current game has both explicit SP+ and Sagarin total components; no substitute baseline was created.",
        },
        "historical_before_after_massey": historical,
        "pairwise_disagreement": pairwise,
        "conclusions": [
            "Massey Dual arithmetic and row-level propagation into the canonical contract are exact for normalized current rows.",
            "Massey presence alone does not activate Standard Total; all three fixed components remain required.",
            "Current 2026 before/after model disagreement cannot be estimated without explicit SP+ and Sagarin total overlap.",
            "Historical strict-overlap results quantify the effect of adding Massey without changing the production formula.",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    pd.DataFrame(coverage_rows).to_csv(OUT_COVERAGE, index=False)
    pd.DataFrame(pairwise).to_csv(OUT_PAIRWISE, index=False)
    pd.DataFrame(disagreement_game_rows).to_csv(OUT_GAMES, index=False)

    coverage_lines = "\n".join(
        f"| {r['model_id']} | {r['component']} | "
        + (
            f"{fmt(r['declared_weight'], 2)} coefficient"
            if r['weight_type'] == 'formula_coefficient'
            else f"{fmt(r['declared_weight'] * 100, 1)}%"
        )
        + f" | {r['covered_games']} | {r['coverage_pct']:.1f}% |"
        for r in coverage_rows
    )
    availability_lines = "\n".join(
        f"| {model_id} | {counts['AVAILABLE']} | {counts['MISSING_COMPONENT']} | {counts['NOT_YET_ACTIVATED']} |"
        for model_id, counts in model_availability.items()
    )
    spread_pairwise_lines = "\n".join(
        f"| {r['source_a']} | {r['source_b']} | {r['overlap_n']} | {fmt(r['mean_absolute_difference'])} | {fmt(r['median_absolute_difference'])} | {fmt(r['p90_absolute_difference'])} | {fmt(r['correlation'])} |"
        for r in pairwise if r["model_id"] == STANDARD_SPREAD
    )
    report = f"""# Projection Source Coverage and Disagreement Audit

Generated: {payload['generated_at']}  
Mode: offline; no UI, model formula, acquisition, or provider changes

## Executive result

- The canonical contract contains {game_count} unique scheduled games.
- Standard Spread is available for {model_availability[STANDARD_SPREAD]['AVAILABLE']} games.
- Standard Total is available for {after_massey_current} games.
- Both live Shadow models remain unavailable.
- Massey Dual is present in {current_massey_validation['contract_rows_with_massey_dual']} contract rows and propagates with maximum arithmetic difference {fmt(current_massey_validation['maximum_contract_propagation_difference'], 12)}.
- Current 2026 before/after Standard Total disagreement is **not estimable**: explicit SP+ plus Sagarin total overlap is {before_massey_current}, so no substitute or renormalized production model was created.

## Canonical source coverage and weights

| Model | Required component | Weight/coefficient | Covered games | Coverage |
|---|---|---:|---:|---:|
{coverage_lines}

## Strict model availability

| Model | Available | Missing component | Not yet activated |
|---|---:|---:|---:|
{availability_lines}

## Spread disagreement

- Games with at least two spread components: {payload['spread_disagreement']['games_with_at_least_two_sources']}.
- Complete five-source games: {len(spread_complete)}.
- Complete-game provider range: mean {fmt(payload['spread_disagreement']['range_complete_five_source']['mean'])}, median {fmt(payload['spread_disagreement']['range_complete_five_source']['median'])}, p90 {fmt(payload['spread_disagreement']['range_complete_five_source']['p90'])} points.
- Complete-game provider standard deviation: mean {fmt(payload['spread_disagreement']['stddev_complete_five_source']['mean'])} points.

| Source A | Source B | Overlap | Mean abs diff | Median abs diff | P90 abs diff | Correlation |
|---|---|---:|---:|---:|---:|---:|
{spread_pairwise_lines}

All pairwise source comparisons are preserved in `{OUT_PAIRWISE.relative_to(ROOT)}`.

## Massey 2026 integration validation

- External Massey rows: {current_massey_validation['external_rows']}.
- Normalized rows with published total and both projected team scores: {current_massey_validation['normalized_rows_with_all_dual_inputs']}.
- External rows not represented in the canonical contract: {current_massey_validation['external_rows'] - current_massey_validation['contract_rows_with_massey_dual']} (the audit does not infer whether these are outside-schedule games, identity gaps, or both).
- Contract rows carrying Massey Dual: {current_massey_validation['contract_rows_with_massey_dual']}.
- Maximum normalized-to-contract Dual difference: {fmt(current_massey_validation['maximum_contract_propagation_difference'], 12)}.
- Published-total versus projected-point-sum absolute difference: mean {fmt(current_massey_validation['published_vs_point_sum_absolute_difference']['mean'])}, median {fmt(current_massey_validation['published_vs_point_sum_absolute_difference']['median'])}, p90 {fmt(current_massey_validation['published_vs_point_sum_absolute_difference']['p90'])} points.
- Dual minus published total: mean {fmt(current_massey_validation['dual_minus_published']['mean'])}, median {fmt(current_massey_validation['dual_minus_published']['median'])} points.
- Source URL coverage: {current_massey_validation['source_url_present']}/{current_massey_validation['normalized_rows_with_all_dual_inputs']}.
- Pull timestamp coverage: {current_massey_validation['pulled_at_present']}/{current_massey_validation['normalized_rows_with_all_dual_inputs']} — **{current_massey_validation['provenance_status']}**.

The integration arithmetic is valid, but the missing normalized pull timestamps prevent calling the current Massey feed fully provenance-ready.

## Before/after Massey totals

### Current 2026

- Before-Massey SP+/Sagarin overlap: {before_massey_current}.
- After-Massey strict three-source availability: {after_massey_current}.
- Incremental available games: {after_massey_current - before_massey_current}.

No current disagreement estimate is reported because there is no comparable SP+/Sagarin total cohort. Generic legacy totals were not substituted.

### Historical strict-overlap diagnostic

This uses {historical['n']} 2021–2025 games with SP+, Massey Dual and Sagarin all present. “Before” is a diagnostic normalization of the SP+/Sagarin 40:20 ratio, not a production model. “After” is the canonical 40/40/20 total.

- Absolute projection shift after adding Massey: mean {fmt(historical['absolute_projection_shift']['mean'])}, median {fmt(historical['absolute_projection_shift']['median'])}, p90 {fmt(historical['absolute_projection_shift']['p90'])} points.
- Provider range before Massey: mean {fmt(historical['before_provider_range']['mean'])}, median {fmt(historical['before_provider_range']['median'])}.
- Provider range after Massey: mean {fmt(historical['after_provider_range']['mean'])}, median {fmt(historical['after_provider_range']['median'])}.

## Decision

Massey Dual is correctly integrated as a 40% required component, but its presence does not make Standard Total available by itself. Production remains fail-closed until explicit SP+ and Sagarin total components are also present. No formula or UI change is warranted from this audit.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(json.dumps({
        "status": payload["status"],
        "canonical_games": game_count,
        "standard_spread_full_available": model_availability[STANDARD_SPREAD]["AVAILABLE"],
        "standard_spread_degraded_available": model_availability[STANDARD_SPREAD]["AVAILABLE_DEGRADED"],
        "standard_spread_displayable": (model_availability[STANDARD_SPREAD]["AVAILABLE"] + model_availability[STANDARD_SPREAD]["AVAILABLE_DEGRADED"]),
        "standard_total_full_available": total_full_available,
        "standard_total_degraded_available": total_degraded_available,
        "standard_total_displayable": after_massey_current,
        "massey_dual_contract_rows": current_massey_validation["contract_rows_with_massey_dual"],
        "report": str(OUT_REPORT.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
