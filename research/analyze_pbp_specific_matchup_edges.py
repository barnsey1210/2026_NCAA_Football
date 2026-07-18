#!/usr/bin/env python3
"""Validate a frozen set of specific PBP matchup features without using 2025."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


SPECS = [
    ("ats_rush_success_mismatch", "ATS", "away", "home", "Difference in expected rush success"),
    ("ats_pass_success_mismatch", "ATS", "away", "home", "Difference in expected pass success"),
    ("ats_explosive_rush_mismatch", "ATS", "away", "home", "Difference in expected explosive rush rate"),
    ("ats_explosive_pass_mismatch", "ATS", "away", "home", "Difference in expected explosive pass rate"),
    ("ats_qb_run_stress_mismatch", "ATS", "away", "home", "Difference in QB-run stress on opposing rush defense"),
    ("ats_disruption_mismatch", "ATS", "away", "home", "Difference in expected defensive havoc"),
    ("total_rush_success_environment", "TOTAL", "under", "over", "Combined expected rush success"),
    ("total_pass_success_environment", "TOTAL", "under", "over", "Combined expected pass success"),
    ("total_explosive_rush_environment", "TOTAL", "under", "over", "Combined expected explosive rush rate"),
    ("total_explosive_pass_environment", "TOTAL", "under", "over", "Combined expected explosive pass rate"),
    ("total_qb_run_stress_environment", "TOTAL", "under", "over", "Combined QB-run stress"),
    ("total_low_disruption_environment", "TOTAL", "under", "over", "Inverse combined expected havoc"),
]


def mean_pair(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a + b) / 2


def add_features(d: pd.DataFrame) -> pd.DataFrame:
    x = d.copy()
    # Each expectation pairs the offense's pregame rate with the opposing defense's
    # pregame rate allowed. Both inputs contain only games before the current game.
    for side, opp in (("home", "away"), ("away", "home")):
        x[f"{side}_exp_rush_success"] = mean_pair(
            x[f"{side}_pregame_off_rush_success_rate"], x[f"{opp}_pregame_def_rush_success_allowed"])
        x[f"{side}_exp_pass_success"] = mean_pair(
            x[f"{side}_pregame_off_pass_success_rate"], x[f"{opp}_pregame_def_pass_success_allowed"])
        x[f"{side}_exp_explosive_rush"] = mean_pair(
            x[f"{side}_pregame_off_explosive_rush_rate"], x[f"{opp}_pregame_def_explosive_rush_allowed"])
        x[f"{side}_exp_explosive_pass"] = mean_pair(
            x[f"{side}_pregame_off_explosive_pass_rate"], x[f"{opp}_pregame_def_explosive_pass_allowed"])
        x[f"{side}_qb_run_stress"] = (
            x[f"{side}_pregame_off_qb_run_share"]
            * x[f"{opp}_pregame_def_rush_success_allowed"]
        )
        # The existing adjusted value represents this defense against the game's offense.
        x[f"{side}_expected_def_havoc"] = x[f"{side}_matchup_expected_def_havoc"]

    x["ats_rush_success_mismatch"] = x.home_exp_rush_success - x.away_exp_rush_success
    x["ats_pass_success_mismatch"] = x.home_exp_pass_success - x.away_exp_pass_success
    x["ats_explosive_rush_mismatch"] = x.home_exp_explosive_rush - x.away_exp_explosive_rush
    x["ats_explosive_pass_mismatch"] = x.home_exp_explosive_pass - x.away_exp_explosive_pass
    x["ats_qb_run_stress_mismatch"] = x.home_qb_run_stress - x.away_qb_run_stress
    x["ats_disruption_mismatch"] = x.home_expected_def_havoc - x.away_expected_def_havoc
    x["total_rush_success_environment"] = x.home_exp_rush_success + x.away_exp_rush_success
    x["total_pass_success_environment"] = x.home_exp_pass_success + x.away_exp_pass_success
    x["total_explosive_rush_environment"] = x.home_exp_explosive_rush + x.away_exp_explosive_rush
    x["total_explosive_pass_environment"] = x.home_exp_explosive_pass + x.away_exp_explosive_pass
    x["total_qb_run_stress_environment"] = x.home_qb_run_stress + x.away_qb_run_stress
    x["total_low_disruption_environment"] = -(x.home_expected_def_havoc + x.away_expected_def_havoc)
    return x


def summarize(values: pd.Series) -> dict:
    v = pd.to_numeric(values, errors="coerce").dropna().to_numpy(float)
    wins, losses, pushes = int((v > 0).sum()), int((v < 0).sum()), int((v == 0).sum())
    decisions = wins + losses
    mean = float(v.mean()) if len(v) else np.nan
    std = float(v.std(ddof=1)) if len(v) > 1 else np.nan
    se = std / math.sqrt(len(v)) if len(v) > 1 and std > 0 else np.nan
    z = mean / se if se and not np.isnan(se) else np.nan
    return {
        "n": len(v), "wins": wins, "losses": losses, "pushes": pushes,
        "raw_win_rate": wins / decisions if decisions else np.nan,
        "shrunk_win_rate": (wins + 10) / (decisions + 20) if decisions else np.nan,
        "mean_market_residual": mean, "std_market_residual": std,
        "one_sided_positive_p": 0.5 * math.erfc(z / math.sqrt(2)) if not np.isnan(z) else np.nan,
    }


def bh(pvalues: list[float]) -> list[float]:
    out = [np.nan] * len(pvalues)
    ordered = sorted(((i, p) for i, p in enumerate(pvalues) if not pd.isna(p)), key=lambda z: z[1])
    running = 1.0
    for reverse_rank, (idx, p) in enumerate(reversed(ordered), 1):
        rank = len(ordered) - reverse_rank + 1
        running = min(running, p * len(ordered) / rank)
        out[idx] = min(1.0, running)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/research/pbp_specific_matchup_edges_2021_2024"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    fields = ["season", "split", "eligible_week5_plus", "closing_spread_residual", "closing_total_residual"]
    for side in ("home", "away"):
        fields += [
            f"{side}_pregame_off_rush_success_rate", f"{side}_pregame_off_pass_success_rate",
            f"{side}_pregame_off_explosive_rush_rate", f"{side}_pregame_off_explosive_pass_rate",
            f"{side}_pregame_off_qb_run_share", f"{side}_pregame_def_rush_success_allowed",
            f"{side}_pregame_def_pass_success_allowed", f"{side}_pregame_def_explosive_rush_allowed",
            f"{side}_pregame_def_explosive_pass_allowed", f"{side}_matchup_expected_def_havoc",
        ]
    d = pd.read_csv(args.input, usecols=fields, low_memory=False)
    d = d[d.eligible_week5_plus.astype(str).str.lower().eq("true") & d.season.le(2024)].copy()
    d = add_features(d)
    dev, val = d[d.split.eq("development")], d[d.split.eq("validation")]

    rows = []
    for key, market, low_action, high_action, description in SPECS:
        low, high = dev[key].quantile([0.2, 0.8]).tolist()
        for tail, threshold, action in (("low", low, low_action), ("high", high, high_action)):
            dm = dev[key].le(threshold) if tail == "low" else dev[key].ge(threshold)
            vm = val[key].le(threshold) if tail == "low" else val[key].ge(threshold)
            outcome = "closing_spread_residual" if market == "ATS" else "closing_total_residual"
            dv, vv = dev.loc[dm, outcome], val.loc[vm, outcome]
            if action in ("away", "under"):
                dv, vv = -dv, -vv
            positive_seasons = sum(
                int(((-1 if action in ("away", "under") else 1) * dev.loc[dm & dev.season.eq(s), outcome]).mean() > 0)
                for s in (2021, 2022, 2023)
            )
            row = {"feature": key, "description": description, "market": market, "tail": tail,
                   "threshold": threshold, "action": action, "development_positive_seasons": positive_seasons}
            row.update({f"development_{k}": v for k, v in summarize(dv).items()})
            row.update({f"validation_{k}": v for k, v in summarize(vv).items()})
            rows.append(row)

    report = pd.DataFrame(rows)
    report["validation_q_value"] = bh(report.validation_one_sided_positive_p.tolist())
    report["evidence_grade"] = "rejected_or_inconclusive"
    promising = (
        report.development_mean_market_residual.ge(0.5)
        & report.validation_mean_market_residual.ge(0.5)
        & report.development_shrunk_win_rate.ge(0.51)
        & report.validation_shrunk_win_rate.ge(0.51)
        & report.validation_n.ge(30)
        & report.development_positive_seasons.ge(2)
    )
    report.loc[promising, "evidence_grade"] = "promising_unconfirmed"
    validated = promising & report.validation_q_value.le(0.10) & report.validation_shrunk_win_rate.ge(0.53)
    report.loc[validated, "evidence_grade"] = "validated_2024"
    report = report.sort_values(["evidence_grade", "validation_q_value", "feature", "tail"])
    report.to_csv(args.output_dir / "feature_edge_validation.csv", index=False)
    summary = {
        "protocol": "Frozen specific features; 2021-2023 development; 2024 validation; 2025 excluded",
        "feature_families": len(SPECS), "tail_tests": len(report),
        "development_rows": len(dev), "validation_rows": len(val),
        "validated_2024": int(report.evidence_grade.eq("validated_2024").sum()),
        "promising_unconfirmed": int(report.evidence_grade.eq("promising_unconfirmed").sum()),
        "rejected_or_inconclusive": int(report.evidence_grade.eq("rejected_or_inconclusive").sum()),
    }
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(report[["feature", "tail", "action", "development_n", "development_mean_market_residual",
                  "validation_n", "validation_mean_market_residual", "validation_shrunk_win_rate",
                  "validation_q_value", "evidence_grade"]].to_string(index=False))


if __name__ == "__main__":
    main()
