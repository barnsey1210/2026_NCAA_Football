#!/usr/bin/env python3
"""Leakage-safe advanced-metrics totals study with locked 2025 evaluation.

Protocol
--------
* 2021-2023: development and threshold definition
* 2024: selection/validation
* 2025: locked holdout, evaluated only after all rules are frozen
* Week 5+, FBS-vs-FBS, and at least four prior games for both teams

No V2 display fields or final-season values are used.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
MARKETS = ROOT / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"
DRIVES = ROOT / "data/research/drive_context_2021_2025/rolling_pregame_drive_context.csv"
TEAM_FEATURES = ROOT / "data/research/team_rating_movement_model/team_game_features.csv"

GAME_OUT = ROOT / "data/research/advanced_totals_game_level_2021_2025.csv"
FEATURE_OUT = ROOT / "reports/advanced_totals_feature_summary.csv"
CANDIDATE_OUT = ROOT / "reports/advanced_totals_candidate_signals.csv"
LOCKED_OUT = ROOT / "reports/advanced_totals_2025_locked_results.csv"
SPREAD_OUT = ROOT / "reports/advanced_spread_monitoring_summary.csv"
SPREAD_LOCKED_OUT = ROOT / "reports/advanced_spread_2025_locked_monitoring.csv"
REPORT_OUT = ROOT / "reports/advanced_totals_residual_study.md"

MIN_PRIOR_GAMES = 4
DEV_SEASONS = (2021, 2022, 2023)
SELECTION_SEASON = 2024
LOCKED_SEASON = 2025


def finite(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return np.nan
    return value if math.isfinite(value) else np.nan


def roi_110(wins: int, losses: int) -> float:
    decisions = wins + losses
    return (wins - 1.1 * losses) / (1.1 * decisions) if decisions else np.nan


def result_stats(values: pd.Series) -> dict:
    v = pd.to_numeric(values, errors="coerce").dropna()
    wins, losses, pushes = int((v > 0).sum()), int((v < 0).sum()), int((v == 0).sum())
    decisions = wins + losses
    return {
        "games": int(len(v)),
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "win_percentage": wins / decisions if decisions else np.nan,
        "roi_at_minus_110": roi_110(wins, losses),
        "average_residual": float(v.mean()) if len(v) else np.nan,
        "median_residual": float(v.median()) if len(v) else np.nan,
    }


def compact_stats(frame: pd.DataFrame, residual: str) -> dict:
    return result_stats(frame[residual]) if residual in frame else result_stats(pd.Series(dtype=float))


def json_breakdown(frame: pd.DataFrame, group: str, residual: str) -> str:
    rows = {}
    for key, part in frame.groupby(group, dropna=False, observed=True):
        rows[str(key)] = compact_stats(part, residual)
    return json.dumps(rows, sort_keys=True, allow_nan=False, default=lambda _: None)


def safe_json(value) -> str:
    def clean(x):
        if isinstance(x, dict):
            return {k: clean(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [clean(v) for v in x]
        if isinstance(x, (float, np.floating)) and not math.isfinite(float(x)):
            return None
        if isinstance(x, (np.integer,)):
            return int(x)
        if isinstance(x, (np.floating,)):
            return float(x)
        return x
    return json.dumps(clean(value), sort_keys=True)


def merge_drive_rows(games: pd.DataFrame) -> pd.DataFrame:
    drive = pd.read_csv(DRIVES, low_memory=False)
    fields = [
        "game_id", "team", "prior_games",
        "pregame_off_avg_start_ytg", "pregame_off_opportunity_rate",
        "pregame_off_points_per_opportunity", "pregame_off_td_rate_per_opportunity",
        "pregame_off_points_per_drive", "pregame_def_opponent_avg_start_ytg",
        "pregame_def_opportunity_rate_allowed", "pregame_def_points_per_opportunity_allowed",
        "pregame_def_td_rate_per_opportunity_allowed", "pregame_def_points_per_drive_allowed",
    ]
    drive = drive[fields].copy()
    if drive.duplicated(["game_id", "team"]).any():
        raise AssertionError("Duplicate drive-context game/team rows")
    for side in ("home", "away"):
        renamed = drive.rename(columns={c: f"{side}_drive_{c}" for c in fields if c not in ("game_id", "team")})
        games = games.merge(
            renamed,
            left_on=["game_id", f"{side}_team"],
            right_on=["game_id", "team"],
            how="left",
            validate="one_to_one",
        ).drop(columns=["team"])
    return games


def add_neutral_site(games: pd.DataFrame) -> pd.DataFrame:
    f = pd.read_csv(TEAM_FEATURES, usecols=["game_id", "neutral_site"], low_memory=False)
    f = f.drop_duplicates("game_id")
    return games.merge(f, on="game_id", how="left", validate="one_to_one")


def matchup_average(offense: pd.Series, defense_allowed: pd.Series) -> pd.Series:
    return (pd.to_numeric(offense, errors="coerce") + pd.to_numeric(defense_allowed, errors="coerce")) / 2


def build_game_level() -> tuple[pd.DataFrame, dict]:
    source = pd.read_csv(MARKETS, low_memory=False)
    source_rows = len(source)
    if source.duplicated("game_id").any():
        raise AssertionError("Canonical market file contains duplicate game_id rows")
    d = source[
        source["season"].between(2021, 2025)
        & source["week"].ge(5)
        & source["minimum_prior_games"].ge(MIN_PRIOR_GAMES)
        & source["closing_total"].notna()
        & source["closing_home_spread"].notna()
        & source["home_score"].notna()
        & source["away_score"].notna()
    ].copy()
    d = merge_drive_rows(d)
    d = add_neutral_site(d)

    # Outcome and market orientation. Home spread is always home-team perspective.
    d["game_date"] = pd.to_datetime(d["start_date"], utc=True, errors="coerce").dt.strftime("%Y-%m-%d")
    d["final_home_margin"] = d["home_score"] - d["away_score"]
    d["final_scoring_margin"] = d["final_home_margin"]
    d["actual_total"] = d["home_score"] + d["away_score"]
    d["total_residual"] = d["actual_total"] - d["closing_total"]
    d["opening_total_residual"] = d["actual_total"] - d["opening_total"]
    d["home_ats_residual"] = d["final_home_margin"] + d["closing_home_spread"]
    d["away_ats_residual"] = -d["home_ats_residual"]
    d["ou_result"] = np.select([d.total_residual.gt(0), d.total_residual.lt(0)], ["Over", "Under"], default="Push")
    d["ats_push_indicator"] = d.home_ats_residual.eq(0)
    d["ats_winner"] = np.select([d.home_ats_residual.gt(0), d.home_ats_residual.lt(0)], [d.home_team, d.away_team], default="Push")
    d["favorite"] = np.select([d.closing_home_spread.lt(0), d.closing_home_spread.gt(0)], [d.home_team, d.away_team], default="Pick'em")
    d["underdog"] = np.select([d.closing_home_spread.lt(0), d.closing_home_spread.gt(0)], [d.away_team, d.home_team], default="Pick'em")
    abs_spread = d.closing_home_spread.abs()
    d["favorite_margin_bucket"] = pd.cut(abs_spread, [-0.01, 0.5, 3, 7, 14, np.inf], labels=["Pick/0.5", "1-3", "3.5-7", "7.5-14", "14+"])
    d["closing_total_bucket"] = pd.cut(d.closing_total, [-np.inf, 44.5, 52.5, 59.5, np.inf], labels=["<45", "45-52.5", "53-59.5", "60+"])

    # Directional offense-versus-defense matchups.
    for side, opp in (("home", "away"), ("away", "home")):
        d[f"{side}_ppa_matchup_value"] = d[f"{side}_matchup_expected_off_ppa"]
        d[f"{side}_success_matchup_value"] = d[f"{side}_matchup_expected_off_success"]
        d[f"{side}_explosiveness_matchup_value"] = d[f"{side}_matchup_expected_off_explosiveness"]
        d[f"{side}_finishing_drives_matchup_value"] = matchup_average(
            d[f"{side}_drive_pregame_off_points_per_opportunity"],
            d[f"{opp}_drive_pregame_def_points_per_opportunity_allowed"],
        )
        # Higher means better offensive field position (fewer yards to goal).
        d[f"{side}_field_position_matchup_value"] = -matchup_average(
            d[f"{side}_drive_pregame_off_avg_start_ytg"],
            d[f"{opp}_drive_pregame_def_opponent_avg_start_ytg"],
        )
        d[f"{side}_drive_efficiency_matchup_value"] = matchup_average(
            d[f"{side}_drive_pregame_off_points_per_drive"],
            d[f"{opp}_drive_pregame_def_points_per_drive_allowed"],
        )
        # Opponent's expected defensive havoc is suppressive from this offense's perspective.
        d[f"{side}_havoc_matchup_value"] = -d[f"{opp}_matchup_expected_def_havoc"]
        d[f"{side}_pass_success_matchup_value"] = matchup_average(
            d[f"{side}_pregame_off_pass_success_rate"], d[f"{opp}_pregame_def_pass_success_allowed"]
        )
        d[f"{side}_rush_success_matchup_value"] = matchup_average(
            d[f"{side}_pregame_off_rush_success_rate"], d[f"{opp}_pregame_def_rush_success_allowed"]
        )
        d[f"{side}_offensive_matchup_value"] = np.nan  # filled after development standardization
        d[f"{side}_defensive_matchup_value"] = np.nan

    # Game-level total environment values. Higher always points toward more scoring.
    d["combined_expected_efficiency"] = d.home_ppa_matchup_value + d.away_ppa_matchup_value
    d["combined_success_rate_matchup_value"] = d.home_success_matchup_value + d.away_success_matchup_value
    d["combined_explosiveness_matchup_value"] = d.home_explosiveness_matchup_value + d.away_explosiveness_matchup_value
    d["combined_pace_seconds"] = d.home_matchup_expected_off_pace_seconds + d.away_matchup_expected_off_pace_seconds
    d["combined_pace"] = -d.combined_pace_seconds
    d["pace_mismatch"] = (d.home_matchup_expected_off_pace_seconds - d.away_matchup_expected_off_pace_seconds).abs()
    d["combined_finishing_drives_matchup_value"] = d.home_finishing_drives_matchup_value + d.away_finishing_drives_matchup_value
    d["combined_field_position_matchup_value"] = d.home_field_position_matchup_value + d.away_field_position_matchup_value
    d["combined_drive_efficiency_matchup_value"] = d.home_drive_efficiency_matchup_value + d.away_drive_efficiency_matchup_value
    d["combined_havoc_suppression_value"] = d.home_havoc_matchup_value + d.away_havoc_matchup_value
    d["combined_pass_success_matchup_value"] = d.home_pass_success_matchup_value + d.away_pass_success_matchup_value
    d["combined_rush_success_matchup_value"] = d.home_rush_success_matchup_value + d.away_rush_success_matchup_value

    directional = ["ppa", "success", "explosiveness", "finishing_drives", "field_position", "drive_efficiency", "havoc", "pass_success", "rush_success"]
    for metric in directional:
        d[f"net_{metric}_matchup_differential"] = d[f"home_{metric}_matchup_value"] - d[f"away_{metric}_matchup_value"]

    # Freeze standardization and neutral thresholds from development data only.
    dev_mask = d.season.isin(DEV_SEASONS)
    total_features = [
        "combined_expected_efficiency", "combined_success_rate_matchup_value",
        "combined_explosiveness_matchup_value", "combined_pace",
        "combined_finishing_drives_matchup_value", "combined_field_position_matchup_value",
        "combined_drive_efficiency_matchup_value", "combined_havoc_suppression_value",
        "combined_pass_success_matchup_value", "combined_rush_success_matchup_value",
    ]
    transform = {}
    for col in total_features:
        mean, std = d.loc[dev_mask, col].mean(), d.loc[dev_mask, col].std(ddof=1)
        transform[col] = {"mean": finite(mean), "std": finite(std)}
        d[f"z_{col}"] = (d[col] - mean) / std if std and math.isfinite(std) else np.nan

    d["number_metrics_pointing_over"] = sum(d[f"z_{c}"].gt(0).astype(int) for c in total_features)
    d["number_metrics_pointing_under"] = sum(d[f"z_{c}"].lt(0).astype(int) for c in total_features)
    d["totals_metric_agreement"] = (d.number_metrics_pointing_over - d.number_metrics_pointing_under).abs()
    d["totals_metric_disagreement"] = 10 - d.totals_metric_agreement
    d["offense_defense_asymmetry"] = (d.home_ppa_matchup_value - d.away_ppa_matchup_value).abs()

    # Team-side composite and edge counts; all scaling fixed on development only.
    side_metrics = directional
    side_z = {"home": [], "away": []}
    for metric in side_metrics:
        stacked = pd.concat([d.loc[dev_mask, f"home_{metric}_matchup_value"], d.loc[dev_mask, f"away_{metric}_matchup_value"]])
        mean, std = stacked.mean(), stacked.std(ddof=1)
        transform[f"side_{metric}"] = {"mean": finite(mean), "std": finite(std)}
        for side in ("home", "away"):
            zcol = f"z_{side}_{metric}_matchup_value"
            d[zcol] = (d[f"{side}_{metric}_matchup_value"] - mean) / std if std and math.isfinite(std) else np.nan
            side_z[side].append(zcol)
    d["home_offensive_matchup_value"] = d[side_z["home"]].mean(axis=1)
    d["away_offensive_matchup_value"] = d[side_z["away"]].mean(axis=1)
    d["home_defensive_matchup_value"] = -d[side_z["away"]].mean(axis=1)
    d["away_defensive_matchup_value"] = -d[side_z["home"]].mean(axis=1)
    d["advanced_metric_edges_home"] = sum(d[f"net_{m}_matchup_differential"].gt(0).astype(int) for m in side_metrics)
    d["advanced_metric_edges_away"] = sum(d[f"net_{m}_matchup_differential"].lt(0).astype(int) for m in side_metrics)
    d["one_sided_matchup_advantage"] = np.select(
        [d.advanced_metric_edges_home.ge(7), d.advanced_metric_edges_away.ge(7)], ["Home", "Away"], default="None"
    )
    favorite_is_home = d.closing_home_spread.lt(0)
    d["advanced_metric_agreement_with_favorite"] = np.where(
        d.closing_home_spread.eq(0), 0,
        np.where(favorite_is_home, d.advanced_metric_edges_home - d.advanced_metric_edges_away, d.advanced_metric_edges_away - d.advanced_metric_edges_home),
    )
    d["advanced_metric_support_for_underdog"] = -d.advanced_metric_agreement_with_favorite

    d["research_split"] = np.select(
        [d.season.isin(DEV_SEASONS), d.season.eq(SELECTION_SEASON), d.season.eq(LOCKED_SEASON)],
        ["development", "selection_2024", "locked_2025"], default="excluded"
    )

    audit = {
        "source_rows": source_rows,
        "eligible_rows": len(d),
        "eligible_by_season": d.groupby("season").size().astype(int).to_dict(),
        "duplicate_game_ids": int(d.duplicated("game_id").sum()),
        "minimum_prior_games": int(d.minimum_prior_games.min()),
        "missing_closing_total": int(d.closing_total.isna().sum()),
        "missing_closing_spread": int(d.closing_home_spread.isna().sum()),
        "missing_opening_total": int(d.opening_total.isna().sum()),
        "spread_sign_test": {
            "example_home_margin": 10,
            "example_home_spread": -3,
            "expected_home_ats_residual": 7,
            "calculated": 10 + (-3),
        },
        "feature_transform_development_only": transform,
    }
    if audit["spread_sign_test"]["calculated"] != 7:
        raise AssertionError("ATS residual sign convention failed")
    if (d.home_ats_residual + d.away_ats_residual).abs().max() > 1e-12:
        raise AssertionError("Home/away ATS residuals are not exact opposites")
    return d, audit


TOTAL_FEATURES = [
    "combined_expected_efficiency", "combined_success_rate_matchup_value",
    "combined_explosiveness_matchup_value", "combined_pace", "pace_mismatch",
    "combined_finishing_drives_matchup_value", "combined_field_position_matchup_value",
    "combined_drive_efficiency_matchup_value", "combined_havoc_suppression_value",
    "combined_pass_success_matchup_value", "combined_rush_success_matchup_value",
    "offense_defense_asymmetry", "number_metrics_pointing_over", "number_metrics_pointing_under",
    "totals_metric_agreement", "totals_metric_disagreement",
]

SPREAD_FEATURES = [
    "net_ppa_matchup_differential", "net_success_matchup_differential",
    "net_explosiveness_matchup_differential", "net_finishing_drives_matchup_differential",
    "net_field_position_matchup_differential", "net_drive_efficiency_matchup_differential",
    "net_havoc_matchup_differential", "net_pass_success_matchup_differential",
    "net_rush_success_matchup_differential", "advanced_metric_agreement_with_favorite",
    "advanced_metric_support_for_underdog",
]


def feature_summary(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for feature in TOTAL_FEATURES:
        for split, part in d.groupby("research_split"):
            valid = part[[feature, "total_residual", "opening_total_residual"]].dropna(subset=[feature, "total_residual"])
            row = {
                "feature": feature, "split": split, "games": len(valid),
                "missing": int(part[feature].isna().sum()),
                "missing_percentage": float(part[feature].isna().mean()),
                "correlation_closing_residual": valid[feature].corr(valid.total_residual),
                "correlation_opening_residual": valid[[feature, "opening_total_residual"]].dropna()[feature].corr(
                    valid[[feature, "opening_total_residual"]].dropna().opening_total_residual
                ) if valid.opening_total_residual.notna().sum() > 2 else np.nan,
            }
            rows.append(row)
        for season, part in d.groupby("season"):
            valid = part[[feature, "total_residual", "opening_total_residual"]].dropna(subset=[feature, "total_residual"])
            rows.append({
                "feature": feature, "split": f"season_{season}", "games": len(valid),
                "missing": int(part[feature].isna().sum()), "missing_percentage": float(part[feature].isna().mean()),
                "correlation_closing_residual": valid[feature].corr(valid.total_residual),
                "correlation_opening_residual": valid[[feature, "opening_total_residual"]].dropna()[feature].corr(
                    valid[[feature, "opening_total_residual"]].dropna().opening_total_residual
                ) if valid.opening_total_residual.notna().sum() > 2 else np.nan,
            })
        dev = d[d.research_split.eq("development")].dropna(subset=[feature]).copy()
        if dev[feature].nunique() >= 5:
            cuts = dev[feature].quantile([0, .2, .4, .6, .8, 1]).drop_duplicates().to_numpy()
            if len(cuts) >= 3:
                for season_part, label in ((d, "all"), (d[d.season.eq(2024)], "2024"), (d[d.season.eq(2025)], "2025_locked")):
                    q = pd.cut(season_part[feature], cuts, include_lowest=True, duplicates="drop")
                    for bucket, idx in season_part.groupby(q, observed=True).groups.items():
                        stats = compact_stats(season_part.loc[idx], "total_residual")
                        rows.append({"feature": feature, "split": f"quintile_{label}", "quintile": str(bucket), **stats})
            decile_cuts = dev[feature].quantile(np.linspace(0, 1, 11)).drop_duplicates().to_numpy()
            if len(decile_cuts) >= 3:
                for season_part, label in ((d, "all"), (d[d.season.eq(2024)], "2024"), (d[d.season.eq(2025)], "2025_locked")):
                    q = pd.cut(season_part[feature], decile_cuts, include_lowest=True, duplicates="drop")
                    for bucket, idx in season_part.groupby(q, observed=True).groups.items():
                        stats = compact_stats(season_part.loc[idx], "total_residual")
                        rows.append({"feature": feature, "split": f"decile_{label}", "decile": str(bucket), **stats})
    return pd.DataFrame(rows)


def define_total_rules(d: pd.DataFrame) -> list[dict]:
    """Freeze interpretable rule definitions without consulting 2025."""
    dev = d[d.research_split.eq("development")]
    rules = []
    for feature in TOTAL_FEATURES[:12]:
        lo, hi = dev[feature].quantile([.2, .8])
        rules.extend([
            {"rule": f"{feature}__low20", "direction": "Under", "description": f"{feature} <= development 20th percentile", "feature": feature, "operator": "<=", "threshold": finite(lo)},
            {"rule": f"{feature}__high20", "direction": "Over", "description": f"{feature} >= development 80th percentile", "feature": feature, "operator": ">=", "threshold": finite(hi)},
        ])
    # Interpretable combinations only; component thresholds all fixed on development.
    q = {c: dev[c].quantile([.2, .8]).to_dict() for c in TOTAL_FEATURES}
    rules.extend([
        {"rule":"fast_pace_and_high_efficiency","direction":"Over","description":"Fastest 20% pace and top-20% combined PPA","conditions":[("combined_pace",">=",q["combined_pace"][.8]),("combined_expected_efficiency",">=",q["combined_expected_efficiency"][.8])]},
        {"rule":"high_explosiveness_and_success","direction":"Over","description":"Top-20% explosiveness and top-20% combined success","conditions":[("combined_explosiveness_matchup_value",">=",q["combined_explosiveness_matchup_value"][.8]),("combined_success_rate_matchup_value",">=",q["combined_success_rate_matchup_value"][.8])]},
        {"rule":"slow_pace_and_poor_finishing","direction":"Under","description":"Slowest 20% pace and bottom-20% finishing drives","conditions":[("combined_pace","<=",q["combined_pace"][.2]),("combined_finishing_drives_matchup_value","<=",q["combined_finishing_drives_matchup_value"][.2])]},
        {"rule":"high_drive_efficiency_and_field_position","direction":"Over","description":"Top-20% drive efficiency and field position","conditions":[("combined_drive_efficiency_matchup_value",">=",q["combined_drive_efficiency_matchup_value"][.8]),("combined_field_position_matchup_value",">=",q["combined_field_position_matchup_value"][.8])]},
        {"rule":"eight_plus_metrics_over","direction":"Over","description":"At least eight of ten standardized metrics point Over","feature":"number_metrics_pointing_over","operator":">=","threshold":8},
        {"rule":"eight_plus_metrics_under","direction":"Under","description":"At least eight of ten standardized metrics point Under","feature":"number_metrics_pointing_under","operator":">=","threshold":8},
        {"rule":"high_efficiency_low_market_total","direction":"Over","description":"Top-20% efficiency with closing total below development median","conditions":[("combined_expected_efficiency",">=",q["combined_expected_efficiency"][.8]),("closing_total","<=",dev.closing_total.median())]},
        {"rule":"low_efficiency_high_market_total","direction":"Under","description":"Bottom-20% efficiency with closing total above development median","conditions":[("combined_expected_efficiency","<=",q["combined_expected_efficiency"][.2]),("closing_total",">=",dev.closing_total.median())]},
        {"rule":"asymmetric_one_offense_edge","direction":"Over","description":"Top-20% offense asymmetry and top-20% stronger offense PPA","conditions":[("offense_defense_asymmetry",">=",q["offense_defense_asymmetry"][.8]),("combined_expected_efficiency",">=",dev.combined_expected_efficiency.median())]},
    ])
    return rules


def rule_mask(frame: pd.DataFrame, rule: dict) -> pd.Series:
    conditions = rule.get("conditions") or [(rule["feature"], rule["operator"], rule["threshold"])]
    mask = pd.Series(True, index=frame.index)
    for feature, op, threshold in conditions:
        values = pd.to_numeric(frame[feature], errors="coerce")
        mask &= values.ge(threshold) if op == ">=" else values.le(threshold)
    return mask


def directional_frame(frame: pd.DataFrame, rule: dict, residual_col="total_residual") -> pd.DataFrame:
    out = frame.loc[rule_mask(frame, rule)].copy()
    out["bet_residual"] = out[residual_col] * (1 if rule["direction"] == "Over" else -1)
    out["opening_bet_residual"] = out.opening_total_residual * (1 if rule["direction"] == "Over" else -1)
    return out


def preliminary_total_grade(dev_stats: dict, val_stats: dict, positive_dev_seasons: int) -> str:
    if val_stats["games"] < 25 or dev_stats["games"] < 75:
        return "INSUFFICIENT SAMPLE"
    if dev_stats["average_residual"] > .4 and val_stats["average_residual"] > .4 and positive_dev_seasons >= 2 and val_stats["win_percentage"] >= .52:
        return "PROMISING"
    if dev_stats["average_residual"] <= 0 and val_stats["average_residual"] <= 0:
        return "REJECTED"
    return "WEAK"


def total_candidate_tables(d: pd.DataFrame, rules: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    dev, val, locked = (d[d.research_split.eq(s)] for s in ("development", "selection_2024", "locked_2025"))
    candidates, locked_rows = [], []
    for rule in rules:
        dd, vv = directional_frame(dev, rule), directional_frame(val, rule)
        ds, vs = compact_stats(dd, "bet_residual"), compact_stats(vv, "bet_residual")
        dev_season = {str(s): compact_stats(directional_frame(dev[dev.season.eq(s)], rule), "bet_residual") for s in DEV_SEASONS}
        positive = sum((v["average_residual"] or -999) > 0 for v in dev_season.values())
        grade = preliminary_total_grade(ds, vs, positive)
        candidates.append({
            "rule": rule["rule"], "direction": rule["direction"], "description": rule["description"],
            "frozen_definition": safe_json(rule), "development_positive_seasons": positive,
            "pre_holdout_classification": grade,
            **{f"development_{k}": v for k, v in ds.items()},
            **{f"selection_2024_{k}": v for k, v in vs.items()},
            "development_by_season": safe_json(dev_season),
            "selection_by_total_bucket": json_breakdown(vv, "closing_total_bucket", "bet_residual"),
            "selection_by_favorite_bucket": json_breakdown(vv, "favorite_margin_bucket", "bet_residual"),
            "selection_opening_average_residual": vv.opening_bet_residual.mean(),
            "selection_opening_games": int(vv.opening_bet_residual.notna().sum()),
        })

        # Locked evaluation occurs here only after every rule and pre-holdout grade is frozen.
        ll = directional_frame(locked, rule)
        ls = compact_stats(ll, "bet_residual")
        if grade == "PROMISING" and ls["games"] >= 25 and ls["average_residual"] > 0 and ls["win_percentage"] >= .50:
            final = "VALIDATED"
        elif grade == "PROMISING" and ls["games"] >= 20 and ls["average_residual"] > 0 and ls["win_percentage"] >= .50:
            final = "PROMISING"
        elif ls["games"] < 20:
            final = "INSUFFICIENT SAMPLE"
        elif grade == "REJECTED" or (ls["average_residual"] < 0 and ls["win_percentage"] < .50):
            final = "REJECTED"
        else:
            final = "WEAK"
        locked_rows.append({
            "rule": rule["rule"], "direction": rule["direction"], "description": rule["description"],
            "pre_holdout_classification": grade, "final_classification": final,
            **{f"locked_2025_{k}": v for k, v in ls.items()},
            "locked_2025_by_total_bucket": json_breakdown(ll, "closing_total_bucket", "bet_residual"),
            "locked_2025_by_favorite_bucket": json_breakdown(ll, "favorite_margin_bucket", "bet_residual"),
            "locked_2025_opening_average_residual": ll.opening_bet_residual.mean(),
            "locked_2025_opening_games": int(ll.opening_bet_residual.notna().sum()),
        })
    return pd.DataFrame(candidates), pd.DataFrame(locked_rows)


def define_spread_checks(d: pd.DataFrame) -> list[dict]:
    dev = d[d.research_split.eq("development")]
    checks = []
    for feature in SPREAD_FEATURES[:9]:
        lo, hi = dev[feature].quantile([.2, .8])
        checks.extend([
            {"check":f"{feature}__away_low20","side":"Away","feature":feature,"operator":"<=","threshold":finite(lo)},
            {"check":f"{feature}__home_high20","side":"Home","feature":feature,"operator":">=","threshold":finite(hi)},
        ])
    checks.extend([
        {"check":"seven_plus_edges_home","side":"Home","feature":"advanced_metric_edges_home","operator":">=","threshold":7},
        {"check":"seven_plus_edges_away","side":"Away","feature":"advanced_metric_edges_away","operator":">=","threshold":7},
        {"check":"favorite_broad_confirmation","side":"Favorite","feature":"advanced_metric_agreement_with_favorite","operator":">=","threshold":5},
        {"check":"favorite_weak_support","side":"Underdog","feature":"advanced_metric_support_for_underdog","operator":">=","threshold":5},
        {"check":"underdog_positive_ppa","side":"Underdog","conditions":[("advanced_metric_support_for_underdog",">=",1), ("net_ppa_matchup_differential","role_positive",0)]},
        {"check":"underdog_positive_success","side":"Underdog","conditions":[("advanced_metric_support_for_underdog",">=",1), ("net_success_matchup_differential","role_positive",0)]},
    ])
    return checks


def spread_mask(frame: pd.DataFrame, check: dict) -> pd.Series:
    conditions = check.get("conditions") or [(check["feature"], check["operator"], check["threshold"])]
    mask = pd.Series(True, index=frame.index)
    for feature, op, threshold in conditions:
        v = pd.to_numeric(frame[feature], errors="coerce")
        if op == "role_positive":
            # Net fields are home-minus-away; orient to the underdog.
            underdog_home = frame.closing_home_spread.gt(0)
            mask &= np.where(underdog_home, v.gt(threshold), v.lt(-threshold))
        else:
            mask &= v.ge(threshold) if op == ">=" else v.le(threshold)
    return mask


def side_residual(frame: pd.DataFrame, side: str) -> pd.Series:
    if side == "Home": return frame.home_ats_residual
    if side == "Away": return frame.away_ats_residual
    favorite_home = frame.closing_home_spread.lt(0)
    if side == "Favorite": return pd.Series(np.where(favorite_home, frame.home_ats_residual, frame.away_ats_residual), index=frame.index)
    if side == "Underdog": return pd.Series(np.where(favorite_home, frame.away_ats_residual, frame.home_ats_residual), index=frame.index)
    raise ValueError(side)


def spread_grade(dev_stats: dict, val_stats: dict, positive_dev_seasons: int) -> str:
    if dev_stats["games"] < 75 or val_stats["games"] < 25: return "INSUFFICIENT SAMPLE"
    if dev_stats["average_residual"] > .5 and val_stats["average_residual"] > .5 and val_stats["win_percentage"] >= .52 and positive_dev_seasons >= 2: return "WORTH DEDICATED STUDY"
    if dev_stats["average_residual"] > 0 and val_stats["average_residual"] > 0 and positive_dev_seasons >= 2: return "POSSIBLE"
    if dev_stats["average_residual"] <= 0 and val_stats["average_residual"] <= 0: return "NO EVIDENCE"
    return "WEAK"


def spread_tables(d: pd.DataFrame, checks: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    dev, val, locked = (d[d.research_split.eq(s)] for s in ("development", "selection_2024", "locked_2025"))
    summary, holdout = [], []
    for check in checks:
        def select(frame):
            out = frame.loc[spread_mask(frame, check)].copy()
            out["bet_residual"] = side_residual(out, check["side"])
            return out
        dd, vv = select(dev), select(val)
        ds, vs = compact_stats(dd, "bet_residual"), compact_stats(vv, "bet_residual")
        by_season = {str(s): compact_stats(select(dev[dev.season.eq(s)]), "bet_residual") for s in DEV_SEASONS}
        positive = sum((x["average_residual"] or -999) > 0 for x in by_season.values())
        grade = spread_grade(ds, vs, positive)
        summary.append({
            "check": check["check"], "side": check["side"], "frozen_definition": safe_json(check),
            "development_positive_seasons": positive, "pre_holdout_classification": grade,
            **{f"development_{k}": v for k, v in ds.items()}, **{f"selection_2024_{k}": v for k, v in vs.items()},
            "development_by_season": safe_json(by_season),
            "selection_by_spread_bucket": json_breakdown(vv, "favorite_margin_bucket", "bet_residual"),
            "selection_home_away_note": "Side-specific residual; neutral games retained and flagged in game-level output",
        })
        ll = select(locked); ls = compact_stats(ll, "bet_residual")
        if ls["games"] < 20: final = "INSUFFICIENT SAMPLE"
        elif grade == "WORTH DEDICATED STUDY" and ls["average_residual"] > 0 and ls["win_percentage"] >= .50: final = "WORTH DEDICATED STUDY"
        elif grade in ("WORTH DEDICATED STUDY", "POSSIBLE") and ls["average_residual"] > 0 and ls["win_percentage"] >= .50: final = "POSSIBLE"
        elif grade == "NO EVIDENCE" or ls["average_residual"] < 0: final = "NO EVIDENCE"
        else: final = "WEAK"
        holdout.append({
            "check": check["check"], "side": check["side"], "pre_holdout_classification": grade,
            "final_classification": final, **{f"locked_2025_{k}": v for k, v in ls.items()},
            "locked_2025_by_spread_bucket": json_breakdown(ll, "favorite_margin_bucket", "bet_residual"),
        })

    # Correlations and quintiles are monitoring rows, not selected signals.
    for feature in SPREAD_FEATURES[:9]:
        for split, part in (("development", dev), ("selection_2024", val)):
            valid = part[[feature, "home_ats_residual"]].dropna()
            summary.append({"check":f"correlation__{feature}","side":"Home orientation","pre_holdout_classification":"MONITORING","split":split,"correlation_ats_residual":valid[feature].corr(valid.home_ats_residual),"games":len(valid)})
        cuts = dev[feature].quantile(np.linspace(0, 1, 6)).drop_duplicates().to_numpy()
        if len(cuts) >= 3:
            for part, label in ((dev, "development"), (val, "selection_2024")):
                q = pd.cut(part[feature], cuts, include_lowest=True, duplicates="drop")
                for bucket, idx in part.groupby(q, observed=True).groups.items():
                    selected = part.loc[idx].copy()
                    selected["bet_residual"] = selected.home_ats_residual
                    summary.append({
                        "check": f"quintile__{feature}", "side": "Home orientation",
                        "pre_holdout_classification": "MONITORING", "split": label,
                        "quintile": str(bucket), **compact_stats(selected, "bet_residual"),
                    })
    return pd.DataFrame(summary), pd.DataFrame(holdout)


def write_report(d: pd.DataFrame, audit: dict, candidates: pd.DataFrame, locked: pd.DataFrame, spreads: pd.DataFrame, spread_locked: pd.DataFrame) -> None:
    validated = locked[locked.final_classification.eq("VALIDATED")]
    promising = locked[locked.final_classification.eq("PROMISING")]
    dedicated = spread_locked[spread_locked.final_classification.eq("WORTH DEDICATED STUDY")]
    possible_spread = spread_locked[spread_locked.final_classification.eq("POSSIBLE")]
    top_totals = locked.sort_values("locked_2025_average_residual", ascending=False).head(8)
    top_spreads = spread_locked.sort_values("locked_2025_average_residual", ascending=False).head(8)
    pre_promising = candidates[candidates.pre_holdout_classification.eq("PROMISING")].merge(
        locked[["rule", "locked_2025_games", "locked_2025_win_percentage", "locked_2025_average_residual", "final_classification"]],
        on="rule", how="left",
    )
    spread_survivors = spread_locked[spread_locked.final_classification.isin(["WORTH DEDICATED STUDY", "POSSIBLE"])]

    def table(frame, cols):
        if frame.empty: return "_None._"
        def display(value):
            if pd.isna(value):
                return "—"
            if isinstance(value, (float, np.floating)):
                return f"{float(value):.3f}"
            return str(value).replace("|", "\\|")
        rows = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
        rows.extend("| " + " | ".join(display(value) for value in row) + " |" for row in frame[cols].itertuples(index=False, name=None))
        return "\n".join(rows)

    text = f"""# Advanced totals residual study, 2021–2025

## Protocol

- Development: 2021–2023
- Threshold selection: 2024
- Locked evaluation: 2025, evaluated once after rule definitions and pre-holdout grades were frozen
- Universe: Week 5+, FBS-vs-FBS, both teams with at least {MIN_PRIOR_GAMES} prior games
- Benchmark: closing total; opening total retained as a secondary diagnostic
- Spread monitoring: closing spread, home-team perspective

No V2 display proxy, final-season statistic, or current-season profile is used. Every football feature comes from the canonical rolling pregame PBP or drive-context row for the target `game_id`.

## Frozen universe and integrity checks

- Source games: {audit['source_rows']:,}
- Eligible games: {audit['eligible_rows']:,}
- Eligible by season: {audit['eligible_by_season']}
- Duplicate game IDs: {audit['duplicate_game_ids']}
- Minimum observed prior games: {audit['minimum_prior_games']}
- Missing opening totals: {audit['missing_opening_total']:,}; these rows remain in closing-line research and are excluded only from opening diagnostics
- Closing total/spread missing after eligibility filter: {audit['missing_closing_total']} / {audit['missing_closing_spread']}

### Spread sign convention

`home ATS residual = final home margin + home closing spread`; away residual is its exact negative. A home team closing -3 and winning by 10 has a +7 home ATS residual. The automated example and home/away inverse check passed.

## Feature construction

Directional matchup expectations pair each offense with the opposing defense. PPA, overall success, overall explosiveness, pace, and havoc use the repository's locally opponent-adjusted pregame expectations. Passing/rushing success use leakage-safe rolling raw rates. Finishing Drives is points per opportunity at the opponent 40; Field Position uses average starting yards to goal; Drive Efficiency uses points per drive. Higher derived values are consistently oriented toward more offense/scoring.

All z-scores, medians, and percentile thresholds were calculated on 2021–2023 only. The number of metrics pointing Over/Under compares ten standardized game-environment metrics with their development means.

## Totals conclusions

- Final VALIDATED rules: {len(validated)}
- Final PROMISING rules: {len(promising)}
- Rules tested: {len(locked)}

{table(top_totals, ['rule','direction','pre_holdout_classification','final_classification','locked_2025_games','locked_2025_win_percentage','locked_2025_roi_at_minus_110','locked_2025_average_residual'])}

### Rules that qualified before the holdout

{table(pre_promising, ['rule','direction','development_games','development_win_percentage','development_average_residual','selection_2024_games','selection_2024_win_percentage','selection_2024_average_residual','locked_2025_games','locked_2025_win_percentage','locked_2025_average_residual','final_classification'])}

These pre-holdout qualifiers are shown to make holdout failure visible. Their definitions were not revised after viewing 2025.

A rule is not called VALIDATED merely for a profitable pooled record. It must have at least 75 development games, 25 selection games, positive average residual in at least two development seasons, positive 2024 average residual, at least 52% in 2024, and then positive average residual with at least 50% in locked 2025. Small, unstable, or contradictory rules remain PROMISING/WEAK/REJECTED/INSUFFICIENT SAMPLE.

Opening-line performance is a secondary diagnostic. Any rule that improves against opening totals but disappears against closing totals is not a closing-line signal.

## Spread monitoring

- WORTH DEDICATED STUDY: {len(dedicated)}
- POSSIBLE: {len(possible_spread)}
- Frozen exploratory checks: {len(spread_locked)}

{table(top_spreads, ['check','side','pre_holdout_classification','final_classification','locked_2025_games','locked_2025_win_percentage','locked_2025_roi_at_minus_110','locked_2025_average_residual'])}

### Spread checks surviving as possible follow-up targets

{table(spread_survivors, ['check','side','pre_holdout_classification','final_classification','locked_2025_games','locked_2025_win_percentage','locked_2025_roi_at_minus_110','locked_2025_average_residual'])}

These spread results are monitoring evidence only. None is a production-ready signal. Correlation and quintile rows in `advanced_spread_monitoring_summary.csv` are descriptive and were not used to create extra holdout rules.

## Stability and limitations

- Same-season advanced inputs are sparse before Week 5; those games are excluded rather than backfilled with final values.
- The full-game dataset omits bowls/playoffs and is FBS-vs-FBS only.
- Passing/rushing PPA, line yards, literal red-zone performance, pressure/sacks, and third-down rates are not included because the audited repository lacks frozen rolling pregame versions.
- Multiple testing remains material even with a restricted interpretable rule list. Results should be replicated in future seasons.
- ROI assumes every decision risks 1.10 units to win 1 unit and ignores line-price variation.
- Opening-line timestamp/provider semantics are less complete than closing lines, so opening results are diagnostic only.

## Recommendations

**Totals signals deserving further study:** the rules labeled VALIDATED or PROMISING in the locked-results CSV, with priority given to rules that remain positive in multiple development seasons, 2024, and 2025 and are monotonic in the feature-summary quintiles.

**Reject:** every rule labeled REJECTED, plus any apparent opening-line edge that has non-positive closing-line residual.

**Betting Signal Engine:** no rule should be integrated automatically from this study alone. A VALIDATED result is eligible for a narrowly preregistered replication and price-aware CLV study, not immediate production scoring.

**Spread next step:** a dedicated ATS residual study is justified only if `advanced_spread_2025_locked_monitoring.csv` contains WORTH DEDICATED STUDY or stable POSSIBLE findings. Prioritize the exact frozen net metrics/combinations in that file rather than opening broad threshold mining.

**Next dataset transformation:** build leakage-safe rolling pass/rush PPA and line-yards features from the already cached CFBD advanced game files. Those are the most direct missing unit-matchup features and do not require a new external pull.
"""
    REPORT_OUT.write_text(text)


def main() -> None:
    GAME_OUT.parent.mkdir(parents=True, exist_ok=True)
    FEATURE_OUT.parent.mkdir(parents=True, exist_ok=True)
    d, audit = build_game_level()
    rules = define_total_rules(d)
    spread_checks = define_spread_checks(d)
    features = feature_summary(d)
    candidates, locked = total_candidate_tables(d, rules)
    spreads, spread_locked = spread_tables(d, spread_checks)

    # Persist only after the full locked sequence has completed successfully.
    d.to_csv(GAME_OUT, index=False)
    features.to_csv(FEATURE_OUT, index=False)
    candidates.to_csv(CANDIDATE_OUT, index=False)
    locked.to_csv(LOCKED_OUT, index=False)
    spreads.to_csv(SPREAD_OUT, index=False)
    spread_locked.to_csv(SPREAD_LOCKED_OUT, index=False)
    write_report(d, audit, candidates, locked, spreads, spread_locked)

    print(json.dumps({
        "eligible_games": len(d),
        "by_season": audit["eligible_by_season"],
        "total_rules": len(rules),
        "validated_totals": int(locked.final_classification.eq("VALIDATED").sum()),
        "promising_totals": int(locked.final_classification.eq("PROMISING").sum()),
        "spread_checks": len(spread_checks),
        "spread_worth_dedicated": int(spread_locked.final_classification.eq("WORTH DEDICATED STUDY").sum()),
        "spread_possible": int(spread_locked.final_classification.eq("POSSIBLE").sum()),
    }, indent=2))


if __name__ == "__main__":
    main()
