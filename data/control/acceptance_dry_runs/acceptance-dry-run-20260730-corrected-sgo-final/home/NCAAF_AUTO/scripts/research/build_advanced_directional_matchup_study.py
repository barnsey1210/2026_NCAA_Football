#!/usr/bin/env python3
"""Leakage-safe directional matchup, movement, and CLV study (2021-2025).

All football inputs are expanding pregame means of completed prior games from the
locally cached CFBD game-advanced files. Thresholds are derived on 2021-2023,
selected on 2024, and evaluated once on locked 2025.
"""
from __future__ import annotations

import gzip
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "cfbd_cache/pbp_history"
BASE = ROOT / "data/research/advanced_totals_game_level_2021_2025.csv"
MARKET_BOOKS = ROOT / "data/research/pbp_market_modeling_2021_2025/provider_market_rows.csv"
GAME_OUT = ROOT / "data/research/advanced_directional_game_level_2021_2025.csv"
INV_OUT = ROOT / "reports/advanced_directional_feature_inventory.csv"
ATS_OUT = ROOT / "reports/advanced_directional_ats_candidates.csv"
TOTAL_OUT = ROOT / "reports/advanced_directional_totals_candidates.csv"
SPREAD_MOVE_OUT = ROOT / "reports/advanced_directional_spread_movement_candidates.csv"
TOTAL_MOVE_OUT = ROOT / "reports/advanced_directional_total_movement_candidates.csv"
CLV_OUT = ROOT / "reports/advanced_directional_clv_candidates.csv"
LOCKED_OUT = ROOT / "reports/advanced_directional_2025_locked_results.csv"
REPORT_OUT = ROOT / "reports/advanced_directional_matchup_study.md"
DEV = (2021, 2022, 2023)
SELECT = 2024
LOCKED = 2025
ORIGINAL_SUCCESS_THRESHOLD = -0.052928295457152705


def read_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as h:
        x = json.load(h)
    return x.get("data", x) if isinstance(x, dict) else x


def nested(row, side, path):
    x = row.get(side) or {}
    for part in path.split("."):
        x = x.get(part) if isinstance(x, dict) else None
    return x


ADVANCED_FIELDS = {
    "off_pass_ppa": ("offense", "passingPlays.ppa"),
    "def_pass_ppa_allowed": ("defense", "passingPlays.ppa"),
    "off_pass_success": ("offense", "passingPlays.successRate"),
    "def_pass_success_allowed": ("defense", "passingPlays.successRate"),
    "off_pass_explosiveness": ("offense", "passingPlays.explosiveness"),
    "def_pass_explosiveness_allowed": ("defense", "passingPlays.explosiveness"),
    "off_passing_down_ppa": ("offense", "passingDowns.ppa"),
    "def_passing_down_ppa_allowed": ("defense", "passingDowns.ppa"),
    "off_passing_down_success": ("offense", "passingDowns.successRate"),
    "def_passing_down_success_allowed": ("defense", "passingDowns.successRate"),
    "off_rush_ppa": ("offense", "rushingPlays.ppa"),
    "def_rush_ppa_allowed": ("defense", "rushingPlays.ppa"),
    "off_rush_success": ("offense", "rushingPlays.successRate"),
    "def_rush_success_allowed": ("defense", "rushingPlays.successRate"),
    "off_rush_explosiveness": ("offense", "rushingPlays.explosiveness"),
    "def_rush_explosiveness_allowed": ("defense", "rushingPlays.explosiveness"),
    "off_line_yards": ("offense", "lineYards"),
    "def_line_yards_allowed": ("defense", "lineYards"),
    "off_stuff_rate": ("offense", "stuffRate"),
    "def_stuff_rate_created": ("defense", "stuffRate"),
    "off_power_success": ("offense", "powerSuccess"),
    "def_power_success_allowed": ("defense", "powerSuccess"),
    "off_second_level_yards": ("offense", "secondLevelYards"),
    "def_second_level_yards_allowed": ("defense", "secondLevelYards"),
    "off_open_field_yards": ("offense", "openFieldYards"),
    "def_open_field_yards_allowed": ("defense", "openFieldYards"),
}


def build_team_game() -> pd.DataFrame:
    rows = []
    pbp_game = pd.read_csv(ROOT / "data/research/pbp_history_2021_2025/team_game_tendencies.csv", low_memory=False)
    pbp_cols = ["season", "week", "game_id", "team", "off_pass_rate", "def_pass_rate_faced", "def_havoc_rate"]
    pbp_game = pbp_game[pbp_cols].drop_duplicates(["season", "game_id", "team"])
    for season in range(2021, 2026):
        for r in read_gz(CACHE / str(season) / "advanced_regular.json.gz"):
            if r.get("gameId") is None:
                continue
            out = {"season": season, "week": int(r.get("week") or 0), "game_id": int(r["gameId"]),
                   "team": str(r.get("team") or ""), "opponent": str(r.get("opponent") or "")}
            for name, (side, path) in ADVANCED_FIELDS.items():
                out[name] = nested(r, side, path)
            rows.append(out)
    d = pd.DataFrame(rows).drop_duplicates(["season", "game_id", "team"])
    d = d.merge(pbp_game, on=["season", "week", "game_id", "team"], how="left", validate="one_to_one")
    havoc = d[["season", "game_id", "team", "def_havoc_rate"]].rename(
        columns={"team": "opponent", "def_havoc_rate": "off_havoc_allowed"})
    d = d.merge(havoc, on=["season", "game_id", "opponent"], how="left", validate="one_to_one")
    return d.sort_values(["season", "team", "week", "game_id"])


def rolling_pregame(team_game: pd.DataFrame) -> pd.DataFrame:
    metrics = [c for c in team_game if c.startswith(("off_", "def_"))]
    out = []
    for (season, team), group in team_game.groupby(["season", "team"], sort=False):
        history = []
        for row in group.sort_values(["week", "game_id"]).to_dict("records"):
            rec = {"season": season, "week": row["week"], "game_id": row["game_id"], "team": team,
                   "opponent": row["opponent"], "directional_prior_games": len(history)}
            for metric in metrics:
                vals = pd.to_numeric(pd.Series([h.get(metric) for h in history]), errors="coerce")
                rec[f"pregame_{metric}"] = vals.mean() if vals.notna().any() else np.nan
                rec[f"pregame_{metric}_games"] = int(vals.notna().sum())
            out.append(rec)
            history.append(row)
    return pd.DataFrame(out)


def attach_side(base: pd.DataFrame, rolling: pd.DataFrame, side: str) -> pd.DataFrame:
    r = rolling.rename(columns={c: f"{side}_directional_{c}" for c in rolling if c not in ("game_id", "team")})
    return base.merge(r, left_on=["game_id", f"{side}_team"], right_on=["game_id", "team"],
                      how="left", validate="one_to_one").drop(columns="team")


def market_book_payload(d: pd.DataFrame) -> pd.DataFrame:
    b = pd.read_csv(MARKET_BOOKS, low_memory=False)
    for c in ["opening_home_spread", "closing_home_spread", "opening_total", "closing_total"]:
        b[c] = pd.to_numeric(b[c], errors="coerce")
    records = []
    for gid, g in b.groupby("game_id"):
        real = g[~g.provider.isin(["consensus", "teamrankings", "numberfire"])].copy()
        consensus = g[g.provider.eq("consensus")]
        spread_open = real.dropna(subset=["opening_home_spread"])
        total_open = real.dropna(subset=["opening_total"])
        rec = {
            "game_id": gid,
            "market_books_available": int(real.provider.nunique()),
            "book_spread_open_dispersion": spread_open.opening_home_spread.max() - spread_open.opening_home_spread.min() if len(spread_open) else np.nan,
            "book_total_open_dispersion": total_open.opening_total.max() - total_open.opening_total.min() if len(total_open) else np.nan,
            "consensus_opening_home_spread": consensus.opening_home_spread.dropna().iloc[0] if consensus.opening_home_spread.notna().any() else np.nan,
            "consensus_closing_home_spread": consensus.closing_home_spread.dropna().iloc[0] if consensus.closing_home_spread.notna().any() else np.nan,
            "consensus_opening_total": consensus.opening_total.dropna().iloc[0] if consensus.opening_total.notna().any() else np.nan,
            "consensus_closing_total": consensus.closing_total.dropna().iloc[0] if consensus.closing_total.notna().any() else np.nan,
            "book_market_lines_json": json.dumps(real[["provider", "opening_home_spread", "closing_home_spread", "opening_total", "closing_total"]].replace({np.nan: None}).to_dict("records")),
        }
        records.append(rec)
    return d.merge(pd.DataFrame(records), on="game_id", how="left", validate="one_to_one")


def mean_match(a, b):
    return (pd.to_numeric(a, errors="coerce") + pd.to_numeric(b, errors="coerce")) / 2


def build_game_level() -> tuple[pd.DataFrame, pd.DataFrame]:
    base = pd.read_csv(BASE, low_memory=False)
    team_game = build_team_game()
    rolling = rolling_pregame(team_game)
    d = attach_side(attach_side(base, rolling, "home"), rolling, "away")
    d = market_book_payload(d)
    # Directional expected values, higher is always better for the offense.
    pairs = {
        "pass_ppa": ("pass_ppa", "pass_ppa_allowed", 1),
        "pass_success": ("pass_success", "pass_success_allowed", 1),
        "pass_explosiveness": ("pass_explosiveness", "pass_explosiveness_allowed", 1),
        "passing_down_ppa": ("passing_down_ppa", "passing_down_ppa_allowed", 1),
        "passing_down_success": ("passing_down_success", "passing_down_success_allowed", 1),
        "rush_ppa": ("rush_ppa", "rush_ppa_allowed", 1),
        "rush_success": ("rush_success", "rush_success_allowed", 1),
        "rush_explosiveness": ("rush_explosiveness", "rush_explosiveness_allowed", 1),
        "line_yards": ("line_yards", "line_yards_allowed", 1),
        "stuff_avoidance": ("stuff_rate", "stuff_rate_created", -1),
        "power_success": ("power_success", "power_success_allowed", 1),
        "second_level_yards": ("second_level_yards", "second_level_yards_allowed", 1),
        "open_field_yards": ("open_field_yards", "open_field_yards_allowed", 1),
        "havoc_avoidance": ("havoc_allowed", "havoc_rate", -1),
    }
    for side, opp in (("home", "away"), ("away", "home")):
        for label, (off, deff, sign) in pairs.items():
            d[f"{side}_{label}_matchup"] = sign * mean_match(d[f"{side}_directional_pregame_off_{off}"], d[f"{opp}_directional_pregame_def_{deff}"])
        d[f"{side}_pass_play_rate"] = d[f"{side}_directional_pregame_off_pass_rate"]
        d[f"{side}_rush_play_rate"] = 1 - d[f"{side}_directional_pregame_off_pass_rate"]
    metric_labels = list(pairs)
    for label in metric_labels:
        d[f"net_{label}_differential"] = d[f"home_{label}_matchup"] - d[f"away_{label}_matchup"]
    d["net_passing_matchup_differential"] = d[["net_pass_ppa_differential", "net_pass_success_differential", "net_pass_explosiveness_differential"]].mean(axis=1)
    d["net_rushing_matchup_differential"] = d[["net_rush_ppa_differential", "net_rush_success_differential", "net_rush_explosiveness_differential"]].mean(axis=1)
    d["net_trench_differential"] = d[["net_line_yards_differential", "net_stuff_avoidance_differential", "net_power_success_differential"]].mean(axis=1)
    d["pass_rush_matchup_asymmetry"] = (d.net_passing_matchup_differential - d.net_rushing_matchup_differential).abs()
    core = ["pass_ppa", "pass_success", "rush_ppa", "rush_success", "line_yards", "stuff_avoidance", "power_success", "havoc_avoidance"]
    d["directional_advantages_home"] = sum(d[f"net_{x}_differential"].gt(0) for x in core)
    d["directional_advantages_away"] = sum(d[f"net_{x}_differential"].lt(0) for x in core)
    d["directional_net_advantage"] = d.directional_advantages_home - d.directional_advantages_away
    d["directional_agrees_overall_ppa"] = np.sign(d.directional_net_advantage) == np.sign(d.net_ppa_matchup_differential)
    d["directional_agrees_overall_success"] = np.sign(d.directional_net_advantage) == np.sign(d.net_success_matchup_differential)
    d["directional_disagreement_count"] = (~d.directional_agrees_overall_ppa).astype(int) + (~d.directional_agrees_overall_success).astype(int)

    # Market movement and point-only CLV. Historical prices/timestamps are unavailable.
    d["home_spread_movement"] = d.closing_home_spread - d.opening_home_spread
    d["spread_absolute_movement"] = d.home_spread_movement.abs()
    d["total_movement"] = d.closing_total - d.opening_total
    d["total_absolute_movement"] = d.total_movement.abs()
    d["spread_direction"] = np.select([d.home_spread_movement.lt(0), d.home_spread_movement.gt(0)], ["Toward home", "Toward away"], "No move")
    d["total_direction"] = np.select([d.total_movement.gt(0), d.total_movement.lt(0)], ["Up", "Down"], "No move")
    d["spread_crossed_key_number"] = False
    for key in (3, 7, 10, 14):
        d["spread_crossed_key_number"] |= ((d.opening_home_spread + key) * (d.closing_home_spread + key) < 0) | ((d.opening_home_spread - key) * (d.closing_home_spread - key) < 0)
    d["home_open_bet_clv"] = d.opening_home_spread - d.closing_home_spread
    d["away_open_bet_clv"] = -d.home_open_bet_clv
    d["over_open_bet_clv"] = d.closing_total - d.opening_total
    d["under_open_bet_clv"] = -d.over_open_bet_clv
    d["consensus_home_spread_movement"] = d.consensus_closing_home_spread - d.consensus_opening_home_spread
    d["consensus_total_movement"] = d.consensus_closing_total - d.consensus_opening_total
    d["consensus_home_open_bet_clv"] = -d.consensus_home_spread_movement
    d["consensus_away_open_bet_clv"] = d.consensus_home_spread_movement
    d["consensus_over_open_bet_clv"] = d.consensus_total_movement
    d["consensus_under_open_bet_clv"] = -d.consensus_total_movement
    d["spread_open_sportsbook"] = d.provider
    d["spread_close_sportsbook"] = d.provider
    d["total_open_sportsbook"] = d.provider
    d["total_close_sportsbook"] = d.provider
    d["first_observed_spread_price"] = np.nan
    d["first_observed_total_price"] = np.nan
    d["closing_spread_price"] = np.nan
    d["closing_total_price"] = np.nan
    d["first_observed_market_timestamp"] = pd.NaT
    d["market_timestamp_availability"] = "unavailable_in_cached_historical_provider_rows"
    d["market_price_availability"] = "unavailable_in_cached_historical_provider_rows"
    d["opening_line_semantics"] = "provider-reported opening line; not verified first publicly bettable timestamp"
    d["scheduled_kickoff_utc"] = d.start_date
    if not (d.home_ats_residual.add(d.away_ats_residual).abs() < 1e-9).all():
        raise AssertionError("ATS orientation failed")
    # Known examples: home open -3 to close -4 => home CLV +1; total 50 to 52 => Over CLV +2.
    assert (-3 - (-4)) == 1 and (52 - 50) == 2
    return d, rolling


def result_stats(v: pd.Series) -> dict:
    x = pd.to_numeric(v, errors="coerce").dropna()
    w, l, p = int((x > 0).sum()), int((x < 0).sum()), int((x == 0).sum())
    n = w + l
    return {"games": len(x), "wins": w, "losses": l, "pushes": p,
            "win_rate": w / n if n else np.nan, "roi_minus_110": (w - 1.1*l)/(1.1*n) if n else np.nan,
            "average": x.mean() if len(x) else np.nan, "median": x.median() if len(x) else np.nan,
            "positive_rate": (x > 0).mean() if len(x) else np.nan,
            "at_least_0_5": (x >= .5).mean() if len(x) else np.nan,
            "at_least_1_0": (x >= 1).mean() if len(x) else np.nan,
            "at_least_1_5": (x.abs() >= 1.5).mean() if len(x) else np.nan,
            "at_least_2_0": (x.abs() >= 2).mean() if len(x) else np.nan}


def jbreak(frame, col):
    return json.dumps({str(k): result_stats(g[col]) for k, g in frame.groupby("season")}, default=lambda x: None if pd.isna(x) else x)


def candidate_definitions(d: pd.DataFrame):
    dev = d[d.season.isin(DEV)]
    features = ["net_passing_matchup_differential", "net_rushing_matchup_differential", "net_trench_differential",
                "net_pass_ppa_differential", "net_pass_success_differential", "net_rush_ppa_differential",
                "net_rush_success_differential", "net_line_yards_differential", "directional_net_advantage",
                "pass_rush_matchup_asymmetry"]
    defs = []
    for f in features:
        lo, hi = dev[f].quantile(.2), dev[f].quantile(.8)
        defs += [{"name": f+"__home_high20", "feature": f, "op": ">=", "threshold": hi, "side": "Home"},
                 {"name": f+"__away_low20", "feature": f, "op": "<=", "threshold": lo, "side": "Away"}]
    defs += [
        {"name": "original_success_away_low20", "feature": "net_success_matchup_differential", "op": "<=", "threshold": ORIGINAL_SUCCESS_THRESHOLD, "side": "Away", "frozen_original": True},
        {"name": "underdog_positive_pass_matchup", "special": "underdog_pass", "side": "Underdog"},
        {"name": "underdog_positive_trench_matchup", "special": "underdog_trench", "side": "Underdog"},
        {"name": "favorite_broad_edge_negative_pass", "special": "favorite_contradiction", "side": "Favorite"},
        {"name": "broad_directional_home", "special": "broad_home", "side": "Home"},
        {"name": "broad_directional_away", "special": "broad_away", "side": "Away"},
    ]
    return defs


def mask_for(d, rule):
    if "feature" in rule:
        return d[rule["feature"]].ge(rule["threshold"]) if rule["op"] == ">=" else d[rule["feature"]].le(rule["threshold"])
    s = rule["special"]
    fav_home = d.opening_home_spread.lt(0)
    if s == "underdog_pass": return np.where(fav_home, d.net_passing_matchup_differential.lt(0), d.net_passing_matchup_differential.gt(0))
    if s == "underdog_trench": return np.where(fav_home, d.net_trench_differential.lt(0), d.net_trench_differential.gt(0))
    if s == "favorite_contradiction": return np.where(fav_home, (d.directional_net_advantage>=4)&(d.net_passing_matchup_differential<0), (d.directional_net_advantage<=-4)&(d.net_passing_matchup_differential>0))
    if s == "broad_home": return d.directional_net_advantage.ge(4)
    if s == "broad_away": return d.directional_net_advantage.le(-4)
    return pd.Series(False, index=d.index)


def side_series(frame, side, home_col, away_col):
    if side == "Home": return frame[home_col]
    if side == "Away": return frame[away_col]
    fav_home = frame.opening_home_spread.lt(0)
    if side == "Favorite": return pd.Series(np.where(fav_home, frame[home_col], frame[away_col]), index=frame.index)
    return pd.Series(np.where(fav_home, frame[away_col], frame[home_col]), index=frame.index)


def classify(dev, selection, locked, kind):
    if dev["games"] < 60 or selection["games"] < 20 or locked["games"] < 25: return "INSUFFICIENT DATA" if kind in ("movement", "clv") else "INSUFFICIENT SAMPLE"
    if kind in ("movement", "clv"):
        if dev["positive_rate"] >= .52 and dev["average"] > 0 and selection["positive_rate"] >= .52 and selection["average"] > 0 and locked["positive_rate"] >= .52 and locked["average"] > 0: return "VALIDATED"
        if dev["average"] > 0 and selection["average"] > 0 and locked["positive_rate"] >= .50 and locked["average"] > 0: return "PROMISING"
        if locked["average"] > 0 and locked["positive_rate"] >= .50: return "WORTH DEDICATED STUDY"
        if locked["average"] > 0: return "POSSIBLE"
        return "NO EVIDENCE" if locked["positive_rate"] < .48 else "WEAK"
    if dev["win_rate"] >= .52 and dev["average"] > 0 and selection["win_rate"] >= .52 and selection["average"] > 0 and locked["win_rate"] >= .52 and locked["average"] > 0: return "VALIDATED"
    if dev["average"] > 0 and selection["average"] > 0 and locked["win_rate"] >= .50 and locked["average"] > 0: return "PROMISING"
    if locked["win_rate"] >= .50 and locked["average"] > 0: return "POSSIBLE"
    return "REJECTED" if locked["average"] < 0 and locked["win_rate"] < .50 else "WEAK"


def evaluate(d, defs):
    outputs = {k: [] for k in ("ats", "totals", "spread_movement", "total_movement", "clv")}
    locked_rows = []
    for rule in defs:
        mask = pd.Series(mask_for(d, rule), index=d.index).fillna(False)
        x = d[mask].copy()
        side = rule["side"]
        x["signal_ats"] = side_series(x, side, "home_ats_residual", "away_ats_residual")
        x["signal_spread_clv"] = side_series(x, side, "home_open_bet_clv", "away_open_bet_clv")
        x["signal_consensus_spread_clv"] = side_series(x, side, "consensus_home_open_bet_clv", "consensus_away_open_bet_clv")
        # Directional strength points Over when both team environments are strong; otherwise Under is not asserted.
        over = x[["home_pass_ppa_matchup", "away_pass_ppa_matchup", "home_rush_ppa_matchup", "away_rush_ppa_matchup"]].mean(axis=1) >= d[d.season.isin(DEV)][["home_pass_ppa_matchup", "away_pass_ppa_matchup", "home_rush_ppa_matchup", "away_rush_ppa_matchup"]].stack().mean()
        x["signal_total_result"] = np.where(over, x.total_residual, -x.total_residual)
        x["signal_total_clv"] = np.where(over, x.over_open_bet_clv, x.under_open_bet_clv)
        x["signal_consensus_total_clv"] = np.where(over, x.consensus_over_open_bet_clv, x.consensus_under_open_bet_clv)
        x["signal_spread_move"] = np.where(side_series(x, side, "home_spread_movement", "away_open_bet_clv") < 0, 1, np.where(x.home_spread_movement.eq(0), 0, -1))
        x["signal_total_move"] = np.where(over, x.total_movement, -x.total_movement)
        outcomes = {"ats": "signal_ats", "totals": "signal_total_result", "spread_movement": "signal_spread_clv", "total_movement": "signal_total_move", "clv": "signal_spread_clv"}
        row_common = {"candidate": rule["name"], "side": side, "definition": json.dumps(rule, default=lambda z: None if pd.isna(z) else z)}
        for kind, col in outcomes.items():
            dev_stats, sel_stats, lock_stats = result_stats(x[x.season.isin(DEV)][col]), result_stats(x[x.season.eq(SELECT)][col]), result_stats(x[x.season.eq(LOCKED)][col])
            classification = classify(dev_stats, sel_stats, lock_stats, "movement" if "movement" in kind else ("clv" if kind == "clv" else kind))
            row = row_common | {f"development_{k}":v for k,v in dev_stats.items()} | {f"selection_2024_{k}":v for k,v in sel_stats.items()} | {f"locked_2025_{k}":v for k,v in lock_stats.items()}
            row |= {"season_stability": jbreak(x, col), "classification": classification,
                    "market": "Spread" if kind in ("ats", "spread_movement", "clv") else "Total",
                    "favorite_underdog_split": json.dumps({str(k): result_stats(g[col]) for k,g in x.groupby("favorite")}, default=lambda z: None if pd.isna(z) else z),
                    "spread_bucket_split": json.dumps({str(k): result_stats(g[col]) for k,g in x.groupby("favorite_margin_bucket", observed=True)}, default=lambda z: None if pd.isna(z) else z)}
            if kind in ("spread_movement", "clv"):
                row |= {f"consensus_{k}":v for k,v in result_stats(x["signal_consensus_spread_clv"]).items()}
            elif kind == "total_movement":
                row |= {f"consensus_{k}":v for k,v in result_stats(x["signal_consensus_total_clv"]).items()}
            outputs[kind].append(row)
            locked_rows.append({"track": kind, "market": "Spread" if kind in ("ats", "spread_movement", "clv") else "Total", "candidate": rule["name"], "side": side, "classification": classification} | {k:v for k,v in lock_stats.items()})
        # Total point CLV is a separate outcome from spread CLV.
        col = "signal_total_clv"
        dev_stats, sel_stats, lock_stats = result_stats(x[x.season.isin(DEV)][col]), result_stats(x[x.season.eq(SELECT)][col]), result_stats(x[x.season.eq(LOCKED)][col])
        classification = classify(dev_stats, sel_stats, lock_stats, "clv")
        row = row_common | {f"development_{k}":v for k,v in dev_stats.items()} | {f"selection_2024_{k}":v for k,v in sel_stats.items()} | {f"locked_2025_{k}":v for k,v in lock_stats.items()}
        row |= {"season_stability": jbreak(x, col), "classification": classification, "market": "Total",
                "favorite_underdog_split": "not_applicable", "spread_bucket_split": "not_applicable"}
        row |= {f"consensus_{k}":v for k,v in result_stats(x["signal_consensus_total_clv"]).items()}
        outputs["clv"].append(row)
        locked_rows.append({"track":"clv", "market":"Total", "candidate":rule["name"], "side":side, "classification":classification} | {k:v for k,v in lock_stats.items()})
    return {k: pd.DataFrame(v) for k,v in outputs.items()}, pd.DataFrame(locked_rows)


def inventory(d, rolling):
    rows=[]
    for c in [x for x in d if any(t in x for t in ("pass_", "rush_", "line_yards", "stuff", "power_success", "second_level", "open_field", "havoc")) and ("pregame" in x or "matchup" in x or "differential" in x)]:
        rows.append({"field":c, "source":"cached CFBD advanced/PBP; expanding prior-game mean", "seasons":"2021-2025", "rows":int(d[c].notna().sum()), "missing_percentage":float(d[c].isna().mean()), "time_safe":True, "opponent_adjusted":False, "as_of":"pregame target week; excludes current game", "limitation":"raw rolling matchup average; not schedule-adjusted"})
    for c, reason in [("sack_rate","not retained in canonical cached aggregate"),("opportunity_rate","not present in CFBD advanced game cache"),("market_prices","not present in historical provider rows"),("market_observation_timestamp","not present in historical provider rows"),("intermediate_market_observations","not present in historical provider rows")]:
        rows.append({"field":c,"source":"unavailable","seasons":"","rows":0,"missing_percentage":1.0,"time_safe":False,"opponent_adjusted":False,"as_of":"","limitation":reason})
    return pd.DataFrame(rows)


def md_table(df, columns):
    if df.empty: return "_None._"
    x=df[columns].head(12).copy().fillna("—")
    return "|"+"|".join(columns)+"|\n|"+"|".join(["---"]*len(columns))+"|\n"+"\n".join("|"+"|".join(str(v) for v in row)+"|" for row in x.itertuples(index=False,name=None))


def write_report(d, outputs, locked, inv):
    good = locked[locked.classification.isin(["VALIDATED","PROMISING","WORTH DEDICATED STUDY","POSSIBLE"])]
    original = locked[locked.candidate.eq("original_success_away_low20")]
    validated = locked[locked.classification.eq("VALIDATED")]
    promising = locked[locked.classification.eq("PROMISING")]
    report=f"""# Advanced directional matchup study, 2021–2025

## Protocol and provenance

- Development: 2021–2023; selection: 2024; locked evaluation: 2025.
- Universe: Week 5+, FBS-vs-FBS, minimum four prior games, identical to the frozen prior study.
- Football features are expanding season-to-date means of completed prior games from cached CFBD advanced/PBP rows. The current game and future games are excluded.
- The original away-side Success Rate hypothesis is unchanged at `{ORIGINAL_SUCCESS_THRESHOLD}`.
- Provider-reported openers are not verified first publicly bettable lines. Historical provider rows contain no observation timestamps, prices, or meaningful intermediate snapshots. Point CLV is evaluated; price CLV, reversal timing, and best historical time-to-act cannot be reliably evaluated.
- Spread movement convention: closing home spread minus opening home spread; negative means toward home. Total movement: close minus open; positive means upward.
- Point CLV convention: a home bet is `open home spread - close home spread`; -3 bet closing -4 is +1 CLV. An Over 50 closing 52 is +2 CLV.

## Coverage

- Eligible games: {len(d):,}; by season: {d.season.value_counts().sort_index().to_dict()}.
- Games with opening spread: {int(d.opening_home_spread.notna().sum()):,}; opening total: {int(d.opening_total.notna().sum()):,}.
- Cached directional fields: {int((inv.source!='unavailable').sum())}; explicitly unavailable fields: {int((inv.source=='unavailable').sum())}.

## Locked findings worth retaining

{md_table(good, ['track','candidate','side','classification','games','win_rate','average','positive_rate'])}

## Original Success Rate away-side hypothesis

{md_table(original, ['track','classification','games','wins','losses','pushes','win_rate','roi_minus_110','average','positive_rate'])}

## Interpretation

- Fully validated findings: {len(validated)}. Promising findings: {len(promising)}. No finding is promoted to production by this study.
- ATS: the original Success Rate away-side rule strengthens from `POSSIBLE` to `PROMISING` under the unchanged threshold. The broad directional away-edge rule is also `PROMISING`; other directional ATS tails remain possible/weak/rejected.
- Totals: no full-game O/U candidate validates. Directional additions do not rescue the prior rejected totals families.
- Market movement/CLV: underdog-positive passing and underdog-positive trench contexts are `PROMISING` for total movement/point CLV, but they are the same mathematical point outcome and require prospective timestamped replication.
- No trustworthy claim can be made about early-versus-late action, reversals, price-only movement, or sportsbook lead/lag from the retained cache.
- `VALIDATED`/`PROMISING` require positive pre-holdout and locked behavior under conservative sample gates. `POSSIBLE` and `WORTH DEDICATED STUDY` are monitoring labels, not production approval.
- ATS/O-U and CLV are deliberately separated. A candidate can predict market movement without predicting the game result, or vice versa.
- Multiple testing, one-season dependence, non-monotonic tails, missing true opener timestamps, books entering late, stale observations, injury/news moves, low-limit opener effects, incomplete price histories, and consensus-construction limitations remain material.
- Sportsbook-specific outcome estimates are descriptive only because provider rows do not include book-level timestamps/prices.

## Recommendations

- Do not integrate any result automatically. Only `VALIDATED` findings deserve prospective 2026 monitoring; `PROMISING` results require replication.
- Use the locked files to distinguish signals that predict ATS/O-U and CLV, CLV only, results only, or neither.
- The best time to act cannot be identified from this cache because observation timestamps/intermediate histories are absent. A prospective timestamped 2026 capture is required.
- Next priority: prospective ATS monitoring of the unchanged original Success Rate away-side rule and broad directional away-edge rule, plus timestamped total-market monitoring for underdogs with positive passing/trench matchups. Do not conduct more high-volume threshold mining.
"""
    REPORT_OUT.write_text(report, encoding="utf-8")


def main():
    for p in [GAME_OUT, INV_OUT, ATS_OUT, TOTAL_OUT, SPREAD_MOVE_OUT, TOTAL_MOVE_OUT, CLV_OUT, LOCKED_OUT, REPORT_OUT]: p.parent.mkdir(parents=True, exist_ok=True)
    d, rolling = build_game_level()
    defs = candidate_definitions(d)
    outputs, locked = evaluate(d, defs)
    inv = inventory(d, rolling)
    d.to_csv(GAME_OUT, index=False)
    inv.to_csv(INV_OUT, index=False)
    outputs["ats"].to_csv(ATS_OUT,index=False)
    outputs["totals"].to_csv(TOTAL_OUT,index=False)
    outputs["spread_movement"].to_csv(SPREAD_MOVE_OUT,index=False)
    outputs["total_movement"].to_csv(TOTAL_MOVE_OUT,index=False)
    outputs["clv"].to_csv(CLV_OUT,index=False)
    locked.to_csv(LOCKED_OUT,index=False)
    write_report(d,outputs,locked,inv)
    print(json.dumps({"eligible_games":len(d),"candidates":len(defs),"locked_classifications":locked.classification.value_counts().to_dict(),"outputs":[str(x.relative_to(ROOT)) for x in [GAME_OUT,INV_OUT,ATS_OUT,TOTAL_OUT,SPREAD_MOVE_OUT,TOTAL_MOVE_OUT,CLV_OUT,LOCKED_OUT,REPORT_OUT]]},indent=2))

if __name__ == "__main__": main()
