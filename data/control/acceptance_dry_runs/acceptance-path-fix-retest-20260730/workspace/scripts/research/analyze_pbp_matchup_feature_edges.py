#!/usr/bin/env python3
"""Test a preregistered set of PBP matchup feature tails; never reads 2025 outcomes."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd


FEATURE_SPECS = [
    {"key": "ats_success_advantage", "market": "ATS", "high_bet": "home", "low_bet": "away", "description": "Home minus away matchup-adjusted offensive success"},
    {"key": "ats_ppa_advantage", "market": "ATS", "high_bet": "home", "low_bet": "away", "description": "Home minus away matchup-adjusted PPA"},
    {"key": "ats_explosiveness_advantage", "market": "ATS", "high_bet": "home", "low_bet": "away", "description": "Home minus away matchup-adjusted explosiveness"},
    {"key": "ats_havoc_advantage", "market": "ATS", "high_bet": "home", "low_bet": "away", "description": "Home defensive havoc matchup minus away defensive havoc matchup"},
    {"key": "total_success_environment", "market": "TOTAL", "high_bet": "over", "low_bet": "under", "description": "Sum of both matchup-adjusted offensive success expectations"},
    {"key": "total_ppa_environment", "market": "TOTAL", "high_bet": "over", "low_bet": "under", "description": "Sum of both matchup-adjusted offensive PPA expectations"},
    {"key": "total_explosiveness_environment", "market": "TOTAL", "high_bet": "over", "low_bet": "under", "description": "Sum of both matchup-adjusted explosiveness expectations"},
    {"key": "total_fast_environment", "market": "TOTAL", "high_bet": "over", "low_bet": "under", "description": "Negative average matchup pace seconds; higher means faster"},
    {"key": "total_pass_environment", "market": "TOTAL", "high_bet": "over", "low_bet": "under", "description": "Average expected neutral pass rate"},
    {"key": "total_low_disruption_environment", "market": "TOTAL", "high_bet": "over", "low_bet": "under", "description": "Negative average expected defensive havoc; higher means less disruption"},
]


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    d = frame.copy()
    d["ats_success_advantage"] = d["home_matchup_expected_off_success"] - d["away_matchup_expected_off_success"]
    d["ats_ppa_advantage"] = d["home_matchup_expected_off_ppa"] - d["away_matchup_expected_off_ppa"]
    d["ats_explosiveness_advantage"] = d["home_matchup_expected_off_explosiveness"] - d["away_matchup_expected_off_explosiveness"]
    d["ats_havoc_advantage"] = d["home_matchup_expected_def_havoc"] - d["away_matchup_expected_def_havoc"]
    d["total_success_environment"] = d["home_matchup_expected_off_success"] + d["away_matchup_expected_off_success"]
    d["total_ppa_environment"] = d["home_matchup_expected_off_ppa"] + d["away_matchup_expected_off_ppa"]
    d["total_explosiveness_environment"] = d["home_matchup_expected_off_explosiveness"] + d["away_matchup_expected_off_explosiveness"]
    d["total_fast_environment"] = -(d["home_matchup_expected_off_pace_seconds"] + d["away_matchup_expected_off_pace_seconds"]) / 2
    d["total_pass_environment"] = (d["home_matchup_expected_off_neutral_pass"] + d["away_matchup_expected_off_neutral_pass"]) / 2
    d["total_low_disruption_environment"] = -(d["home_matchup_expected_def_havoc"] + d["away_matchup_expected_def_havoc"]) / 2
    return d


def summarize(values: pd.Series) -> Dict[str, Any]:
    x = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    wins, losses, pushes = int((x > 0).sum()), int((x < 0).sum()), int((x == 0).sum())
    decisions = wins + losses
    shrunk = (wins + 10) / (decisions + 20) if decisions else np.nan
    mean = float(x.mean()) if len(x) else np.nan
    std = float(x.std(ddof=1)) if len(x) > 1 else np.nan
    se = std / math.sqrt(len(x)) if len(x) > 1 and std > 0 else np.nan
    z = mean / se if se and not np.isnan(se) else np.nan
    p = 0.5 * math.erfc(z / math.sqrt(2)) if not np.isnan(z) else np.nan
    return {
        "n": len(x), "wins": wins, "losses": losses, "pushes": pushes,
        "raw_win_rate": wins / decisions if decisions else np.nan,
        "shrunk_win_rate": shrunk, "mean_market_residual": mean,
        "std_market_residual": std, "one_sided_positive_p": p,
    }


def bh_qvalues(pvalues: List[float]) -> List[float]:
    result = [np.nan] * len(pvalues)
    valid = [(i, p) for i, p in enumerate(pvalues) if not pd.isna(p)]
    ordered = sorted(valid, key=lambda item: item[1])
    running = 1.0
    for reverse_rank, (idx, p) in enumerate(reversed(ordered), start=1):
        rank = len(ordered) - reverse_rank + 1
        running = min(running, p * len(ordered) / rank)
        result[idx] = min(1.0, running)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path,
        default=Path("data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("data/research/pbp_matchup_edges_2021_2024"),
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    needed = [
        "season", "split", "eligible_week5_plus", "closing_spread_residual", "closing_total_residual",
        "home_matchup_expected_off_success", "away_matchup_expected_off_success",
        "home_matchup_expected_off_ppa", "away_matchup_expected_off_ppa",
        "home_matchup_expected_off_explosiveness", "away_matchup_expected_off_explosiveness",
        "home_matchup_expected_def_havoc", "away_matchup_expected_def_havoc",
        "home_matchup_expected_off_pace_seconds", "away_matchup_expected_off_pace_seconds",
        "home_matchup_expected_off_neutral_pass", "away_matchup_expected_off_neutral_pass",
    ]
    data = pd.read_csv(args.input, usecols=needed, low_memory=False)
    data = data[data["eligible_week5_plus"].astype(str).str.lower().eq("true")]
    data = data[~data["split"].eq("locked_test")].copy()
    data = add_features(data)
    development = data[data["split"].eq("development")]
    validation = data[data["split"].eq("validation")]
    rows: List[Dict[str, Any]] = []

    for spec in FEATURE_SPECS:
        key = spec["key"]
        low, high = development[key].quantile([0.2, 0.8]).tolist()
        for tail, threshold, operator in [("low", low, "<="), ("high", high, ">=")]:
            dev_mask = development[key].le(threshold) if tail == "low" else development[key].ge(threshold)
            val_mask = validation[key].le(threshold) if tail == "low" else validation[key].ge(threshold)
            action = spec[f"{tail}_bet"]
            if spec["market"] == "ATS":
                dev_margin = development.loc[dev_mask, "closing_spread_residual"]
                val_margin = validation.loc[val_mask, "closing_spread_residual"]
                if action == "away":
                    dev_margin, val_margin = -dev_margin, -val_margin
            else:
                dev_margin = development.loc[dev_mask, "closing_total_residual"]
                val_margin = validation.loc[val_mask, "closing_total_residual"]
                if action == "under":
                    dev_margin, val_margin = -dev_margin, -val_margin
            dev_stats, val_stats = summarize(dev_margin), summarize(val_margin)
            season_positive = 0
            for season in sorted(development["season"].unique()):
                season_mask = development["season"].eq(season) & dev_mask
                residual = development.loc[season_mask, "closing_spread_residual" if spec["market"] == "ATS" else "closing_total_residual"]
                if action in ("away", "under"):
                    residual = -residual
                season_positive += int(residual.mean() > 0)
            row = {
                "feature": key, "description": spec["description"], "market": spec["market"],
                "tail": tail, "operator": operator, "threshold": threshold, "action": action,
                "development_positive_seasons": season_positive,
            }
            row.update({f"development_{k}": v for k, v in dev_stats.items()})
            row.update({f"validation_{k}": v for k, v in val_stats.items()})
            rows.append(row)

    report = pd.DataFrame(rows)
    report["validation_q_value"] = bh_qvalues(report["validation_one_sided_positive_p"].tolist())
    report["evidence_grade"] = "rejected_or_inconclusive"
    promising = (
        report["development_mean_market_residual"].ge(0.5)
        & report["validation_mean_market_residual"].ge(0.5)
        & report["development_shrunk_win_rate"].ge(0.51)
        & report["validation_shrunk_win_rate"].ge(0.51)
        & report["validation_n"].ge(30)
        & report["development_positive_seasons"].ge(2)
    )
    report.loc[promising, "evidence_grade"] = "promising_unconfirmed"
    validated = promising & report["validation_q_value"].le(0.10) & report["validation_shrunk_win_rate"].ge(0.53)
    report.loc[validated, "evidence_grade"] = "validated_2024"
    report = report.sort_values(["evidence_grade", "validation_q_value", "feature", "tail"])
    report_path = args.output_dir / "feature_edge_validation.csv"
    summary_path = args.output_dir / "summary.json"
    report.to_csv(report_path, index=False)
    summary = {
        "protocol": "2021-2023 thresholds; 2024 validation; 2025 never read into analysis",
        "feature_families": len(FEATURE_SPECS), "tail_tests": len(report),
        "development_rows": len(development), "validation_rows": len(validation),
        "validated_2024": int(report["evidence_grade"].eq("validated_2024").sum()),
        "promising_unconfirmed": int(report["evidence_grade"].eq("promising_unconfirmed").sum()),
        "rejected_or_inconclusive": int(report["evidence_grade"].eq("rejected_or_inconclusive").sum()),
        "notes": [
            "Thresholds are fixed development 20th/80th percentiles.",
            "ATS high tails bet home and low tails bet away; totals high/low actions are preregistered by football direction.",
            "Win rates use a 20-decision 50% shrinkage prior.",
            "Validation q-values use Benjamini-Hochberg correction across all tail tests.",
            "No favorite/underdog, home/away subdivision, or feature permutations are searched.",
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(report[["feature", "tail", "action", "development_n", "development_mean_market_residual", "validation_n", "validation_mean_market_residual", "validation_shrunk_win_rate", "validation_q_value", "evidence_grade"]].to_string(index=False))


if __name__ == "__main__":
    main()
