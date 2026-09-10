#!/usr/bin/env python3
"""Build the auditable 2026 team-game Model Fit contract.

Historical reconstruction is deliberately input-driven.  A model observation is
eligible only when every source timestamp and the observation itself precede the
game's exact kickoff.  Market history is treated as an accepted observation
ledger, never as proof that an original CLOSE lifecycle event existed.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import tempfile
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cfbd_equivalent_margin_v1 import (  # noqa: E402
    CFBD_EQUIVALENT_MARGIN_ANCHORS,
    CFBD_EQUIVALENT_MARGIN_PROVENANCE,
    CFBD_EQUIVALENT_MARGIN_VERSION,
    cfbd_equivalent_margin_v1,
)
sys.path.insert(0, str(ROOT))
from scripts.site.team_identity import canonical_team_key  # noqa: E402
MODEL_ID = "standard_spread_4src_equal_v1"
COMPONENTS = ("SP+", "FPI", "TeamRankings", "DRatings")
WEIGHTS = {name: 0.25 for name in COMPONENTS}
RECONSTRUCTED_CONTRACT_PATH = "data/model_tracking/reconstructed/week1_standard_spread_contract_2026.json"
COMPONENT_SNAPSHOT_PATH = "data/model_tracking/reconstructed/week0_standard_spread_component_snapshots_2026.json"
CONTRACT_PROVENANCE = "RECONSTRUCTED_FROM_PREKICKOFF_PROJECTION_CONTRACT"
SNAPSHOT_PROVENANCE = "RECONSTRUCTED_FROM_PREKICKOFF_COMPONENT_SNAPSHOTS"
FLOAT_TOLERANCE = 1e-9
SP_PLUS_SOURCE_ALIASES = {"usf": "south florida"}


def sp_plus_team_key(value):
    key = canonical_team_key(value)
    return canonical_team_key(SP_PLUS_SOURCE_ALIASES.get(key, value))


def dt(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def num(value):
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    except (TypeError, ValueError):
        return None


def load_json(path):
    return json.loads(Path(path).read_text())


def load_jsonl(path):
    if not Path(path).exists():
        return []
    rows = []
    for line in Path(path).read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def exact_kickoff(game):
    return dt(game.get("start_date") or game.get("kickoff_at"))


def timestamps_pre_kickoff(values, kickoff):
    parsed = [dt(value) for value in values]
    return bool(parsed) and all(value is not None and value < kickoff for value in parsed)


def reconstructed_contract_model(game, payload):
    kickoff = exact_kickoff(game)
    if not kickoff:
        return None, "missing_exact_kickoff"
    candidates = []
    for row in payload.get("games", []):
        if str(row.get("game_id")) != str(game["game_id"]):
            continue
        projection = row.get("projection") or {}
        if projection.get("model_id") != MODEL_ID:
            continue
        if projection.get("authority") != "OFFICIAL":
            continue
        if projection.get("formula_status") != "PRODUCTION_VALIDATED":
            continue
        if projection.get("formula_version") != "v1":
            continue
        values = projection.get("component_values") or {}
        statuses = projection.get("component_status") or {}
        weights = projection.get("weights") or {}
        timestamps = projection.get("component_source_timestamps") or {}
        selected = {name: num(values.get(name)) for name in COMPONENTS}
        if any(value is None for value in selected.values()):
            continue
        if any(statuses.get(name) != "PRESENT" for name in COMPONENTS):
            continue
        if any(num(weights.get(name)) != WEIGHTS[name] for name in COMPONENTS):
            continue
        if set(weights) != set(COMPONENTS):
            continue
        build_timestamp = projection.get("build_timestamp")
        if not timestamps_pre_kickoff([build_timestamp, *[timestamps.get(name) for name in COMPONENTS]], kickoff):
            continue
        margin = num(projection.get("value_home_margin"))
        arithmetic_mean = sum(selected.values()) / len(COMPONENTS)
        if margin is None or not math.isclose(margin, arithmetic_mean, rel_tol=FLOAT_TOLERANCE, abs_tol=FLOAT_TOLERANCE):
            continue
        candidates.append({
            "model_margin_home": margin,
            "component_values": selected,
            "component_snapshot_timestamps": {name: timestamps[name] for name in COMPONENTS},
            "model_observed_at": build_timestamp,
            "source_artifacts": [payload.get("artifact_path", RECONSTRUCTED_CONTRACT_PATH)],
            "model_provenance": CONTRACT_PROVENANCE,
            "source_git_commit": payload.get("source_git_commit"),
            "source_artifact": payload.get("source_path"),
            "source_commit_timestamp": payload.get("source_commit_timestamp"),
        })
    if not candidates:
        return None, "no_valid_prekickoff_projection_contract"
    return max(candidates, key=lambda x: dt(x["model_observed_at"])), None


def component_snapshot_model(game, payload):
    kickoff = exact_kickoff(game)
    if not kickoff:
        return None, "missing_exact_kickoff"
    candidates = []
    for row in payload.get("games", []):
        if str(row.get("game_id")) != str(game["game_id"]):
            continue
        values = row.get("component_values") or {}
        selected = {name: num(values.get(name)) for name in COMPONENTS}
        if any(value is None for value in selected.values()):
            continue
        source_ts = row.get("component_source_timestamps") or {}
        selected_ts = {name: source_ts.get(name) for name in COMPONENTS}
        observed_at = row.get("observed_at")
        if not timestamps_pre_kickoff([observed_at, *selected_ts.values()], kickoff):
            continue
        candidates.append({
            "model_margin_home": sum(selected.values()) / 4.0,
            "component_values": selected,
            "component_snapshot_timestamps": selected_ts,
            "model_observed_at": observed_at,
            "source_artifacts": [payload.get("artifact_path", COMPONENT_SNAPSHOT_PATH)],
            "model_provenance": SNAPSHOT_PROVENANCE,
            "source_git_commit": row.get("source_git_commit"),
            "source_artifact": row.get("source_path"),
            "source_commit_timestamp": row.get("source_commit_timestamp"),
        })
    if not candidates:
        return None, "no_complete_prekickoff_four_component_snapshot"
    return max(candidates, key=lambda x: dt(x["model_observed_at"])), None


def captured_model(game, observations):
    kickoff = exact_kickoff(game)
    candidates = []
    for row in observations:
        if str(row.get("canonical_game_id")) != str(game["game_id"]) or row.get("model_id") != MODEL_ID:
            continue
        if (row.get("provenance_flags") or {}).get("authority") != "OFFICIAL":
            continue
        if row.get("lifecycle_state") != "PRODUCTION_VALIDATED" or row.get("formula_version") != "v1":
            continue
        values = row.get("component_values") or {}
        ts = row.get("source_snapshot_timestamps") or {}
        if row.get("projection") is None or any(num(values.get(name)) is None for name in COMPONENTS):
            continue
        if not kickoff or not timestamps_pre_kickoff([row.get("observed_at"), *[ts.get(x) for x in COMPONENTS]], kickoff):
            continue
        candidates.append(row)
    if not candidates:
        return None, "no_complete_prekickoff_official_observation"
    row = max(candidates, key=lambda x: dt(x.get("observed_at")))
    return {
        "model_margin_home": num(row["projection"]),
        "component_values": {name: num(row["component_values"][name]) for name in COMPONENTS},
        "component_snapshot_timestamps": {name: row["source_snapshot_timestamps"][name] for name in COMPONENTS},
        "model_observed_at": row.get("observed_at"),
        "source_artifacts": ["data/model_tracking/v2/prediction_observations.jsonl"],
        "model_provenance": "CAPTURED",
        "model_observation_id": row.get("observation_id"),
    }, None


def recover_model(game, observations, reconstructed_contract, component_snapshots):
    """Apply the fixed historical model hierarchy without consulting Git history."""
    model, gap = captured_model(game, observations)
    if model:
        return model, None
    model, gap = reconstructed_contract_model(game, reconstructed_contract)
    if model:
        return model, None
    return component_snapshot_model(game, component_snapshots)


def read_market(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def market_close(game, rows):
    kickoff = exact_kickoff(game)
    candidates = []
    for row in rows:
        if str(row.get("canonical_game_id")) != str(game["game_id"]):
            continue
        observed = dt(row.get("snapshot_ts"))
        if not kickoff or not observed or observed >= kickoff or str(row.get("market", "")).lower() != "spread":
            continue
        if str(row.get("side", "")).lower() != "home" or num(row.get("line")) is None:
            continue
        if str(row.get("available", "true")).lower() in {"false", "0", "no"}:
            continue
        candidates.append(row)
    if not candidates:
        return None, "no_valid_prekickoff_market_snapshot"
    latest_at = max(dt(row["snapshot_ts"]) for row in candidates)
    latest = [row for row in candidates if dt(row["snapshot_ts"]) == latest_at]
    latest.sort(key=lambda r: (0 if "pinnacle" in str(r.get("book", "")).lower() else 1, str(r.get("book"))))
    row = latest[0]
    return {
        "market_margin_home": -num(row["line"]),
        "close_book": row.get("book"),
        "close_provider": row.get("source"),
        "close_timestamp": row.get("snapshot_ts"),
        "close_source_updated_at": row.get("source_updated_at"),
        "close_provenance": "RECONSTRUCTED_FROM_PREKICKOFF_MARKET_SNAPSHOT",
        "market_source_artifact": "data/odds/game_book_line_history.csv",
    }, None


def captured_close(game, checkpoints):
    kickoff = exact_kickoff(game)
    candidates = []
    for row in checkpoints:
        if str(row.get("canonical_game_id")) != str(game["game_id"]):
            continue
        if row.get("market_type") != "spread" or row.get("checkpoint") != "CLOSE" or row.get("selection_status") != "OFFICIAL":
            continue
        if row.get("market_benchmark") not in {"FROZEN_CLOSE", "CANONICAL_FROZEN_CLOSE"}:
            continue
        observed = dt(row.get("market_observed_at") or row.get("close_timestamp"))
        if not kickoff or not observed or observed >= kickoff or num(row.get("market_line")) is None:
            continue
        candidates.append(row)
    if not candidates:
        return None
    row = max(candidates, key=lambda x: dt(x.get("market_observed_at") or x.get("close_timestamp")))
    # A checkpoint stores the selected side's bookmaker line. Normalize it to
    # home expected-margin orientation before producing team perspectives.
    selected_line = num(row["market_line"])
    home_line = selected_line if row.get("bet_side") == "home" else -selected_line
    return {"market_margin_home": -home_line, "close_book": row.get("market_book"), "close_provider": row.get("market_source"),
        "close_timestamp": row.get("market_observed_at") or row.get("close_timestamp"), "close_source_updated_at": row.get("market_source_updated_at"),
        "close_provenance": "CAPTURED", "market_source_artifact": "data/model_tracking/v2/checkpoint_observations.jsonl"}


def pgwe_index(payload):
    rows = payload if isinstance(payload, list) else payload.get("games", [])
    out = {}
    for row in rows:
        game_id = row.get("cfbd_game_id") or row.get("id") or row.get("game_id")
        home = num(row.get("home_postgame_win_probability", row.get("homePostgameWinProbability")))
        away = num(row.get("away_postgame_win_probability", row.get("awayPostgameWinProbability")))
        if game_id is None or home is None or away is None or not (0 <= home <= 1 and 0 <= away <= 1):
            continue
        if abs((home + away) - 1.0) > 1e-6:
            continue
        out[str(game_id)] = (home, away, row.get("pulled_at") or (payload.get("pulled_at") if isinstance(payload, dict) else None))
    return out


def sp_plus_index(payload, games):
    """Deterministically match SP+ team rows to canonical games with an audit."""
    source_rows = payload.get("rows", payload if isinstance(payload, list) else [])
    candidates = defaultdict(list)
    for row in source_rows:
        key = (str(row.get("date") or "")[:10], sp_plus_team_key(row.get("team")), sp_plus_team_key(row.get("opponent")))
        candidates[key].append(row)
    matched = {}; unmatched = []; ambiguous = []
    for game in games:
        date = str(game.get("date") or game.get("start_date") or "")[:10]
        pair = []
        for side in ("home", "away"):
            team = game[f"{side}_team"]
            opponent = game["away_team" if side == "home" else "home_team"]
            found = candidates.get((date, sp_plus_team_key(team), sp_plus_team_key(opponent)), [])
            if len(found) != 1:
                target = ambiguous if len(found) > 1 else unmatched
                target.append({"game_id": str(game["game_id"]), "date": date, "team": team,
                               "opponent": opponent, "candidate_rows": len(found)})
            else:
                pair.append(found[0])
        if len(pair) == 2:
            home, away = pair
            if (not math.isclose(home["sp_plus_pgwe"] + away["sp_plus_pgwe"], 1.0, abs_tol=1e-6)
                    or not math.isclose(home["sp_plus_adjusted_margin"], -away["sp_plus_adjusted_margin"], abs_tol=1e-6)):
                ambiguous.append({"game_id": str(game["game_id"]), "date": date,
                                  "reason": "mirrored_rows_not_complementary_or_symmetric"})
                continue
            matched[str(game["game_id"])] = {sp_plus_team_key(row["team"]): row for row in pair}
    return matched, {"source_team_rows": len(source_rows), "matched_games": len(matched),
                     "matched_team_rows": 2 * len(matched), "unmatched": unmatched,
                     "ambiguous": ambiguous}


def grade(team, opponent, side, game, model, market, pgwe, sp_plus=None):
    sign = 1 if side == "home" else -1
    model_margin = sign * model["model_margin_home"] if model else None
    market_margin = sign * market["market_margin_home"] if market else None
    actual = sign * num(game["home_margin_actual"])
    edge = model_margin - market_margin if model_margin is not None and market_margin is not None else None
    model_error = abs(actual - model_margin) if model_margin is not None else None
    market_error = abs(actual - market_margin) if market_margin is not None else None
    residual = actual - market_margin if market_margin is not None else None
    qualified = edge is not None and abs(edge) >= 2.0
    edge_result = None
    if qualified:
        selected_residual = residual if edge > 0 else -residual
        edge_result = "WIN" if selected_residual > 0 else "LOSS" if selected_residual < 0 else "PUSH"
    pg_for = pgwe[0] if side == "home" and pgwe else pgwe[1] if pgwe else None
    pg_against = pgwe[1] if side == "home" and pgwe else pgwe[0] if pgwe else None
    try:
        cfbd_margin = cfbd_equivalent_margin_v1(pg_for) if pg_for is not None else None
    except ValueError:
        cfbd_margin = None
    sp_margin = num(sp_plus.get("sp_plus_adjusted_margin")) if sp_plus else None
    model_error_sp = abs(sp_margin - model_margin) if sp_margin is not None and model_margin is not None else None
    market_error_sp = abs(sp_margin - market_margin) if sp_margin is not None and market_margin is not None else None
    model_error_cfbd = abs(cfbd_margin - model_margin) if cfbd_margin is not None and model_margin is not None else None
    market_error_cfbd = abs(cfbd_margin - market_margin) if cfbd_margin is not None and market_margin is not None else None
    return {
        "game_id": str(game["game_id"]), "cfbd_game_id": game.get("cfbd_game_id"), "season": 2026,
        "week": game.get("week"), "kickoff": game.get("start_date"), "team": team, "opponent": opponent,
        "home_away": side.upper(), "provenance_state": "CAPTURED" if model and model["model_provenance"] == "CAPTURED" and market and market.get("close_provenance") == "CAPTURED" else "RECONSTRUCTED",
        "model_margin": model_margin, "model_formula": "0.25*SP+ + 0.25*FPI + 0.25*TeamRankings + 0.25*DRatings", "model_version": MODEL_ID,
        "component_values": ({name: sign * value for name, value in model.get("component_values", {}).items()} if model else None), "component_snapshot_timestamps": model.get("component_snapshot_timestamps") if model else None,
        "model_observed_at": model.get("model_observed_at") if model else None, "model_provenance": model.get("model_provenance") if model else None,
        "model_source_git_commit": model.get("source_git_commit") if model else None, "model_source_artifact": model.get("source_artifact") if model else None,
        "model_source_commit_timestamp": model.get("source_commit_timestamp") if model else None,
        "market_margin": market_margin, "close_book": market.get("close_book") if market else None, "close_provider": market.get("close_provider") if market else None,
        "close_timestamp": market.get("close_timestamp") if market else None, "close_provenance": market.get("close_provenance") if market else None,
        "actual_margin": actual, "team_score": game.get(f"{side}_score"), "opponent_score": game.get("away_score" if side == "home" else "home_score"),
        "result_provenance": game.get("source"), "model_market_edge": edge, "model_abs_error_actual": model_error,
        "market_abs_error_actual": market_error, "model_advantage_vs_market_actual": market_error - model_error if model_error is not None and market_error is not None else None,
        "directional_bias_actual": actual - model_margin if model_margin is not None else None, "qualified_edge": qualified,
        "qualified_edge_side": team if qualified and edge > 0 else opponent if qualified else None, "qualified_edge_result": edge_result,
        "qualified_edge_push": edge_result == "PUSH", "realized_market_residual": residual,
        "sp_plus_pgwe": num(sp_plus.get("sp_plus_pgwe")) if sp_plus else None,
        "sp_plus_adjusted_margin": sp_margin,
        "model_abs_error_sp_plus_margin": model_error_sp, "market_abs_error_sp_plus_margin": market_error_sp,
        "model_advantage_vs_market_sp_plus": market_error_sp - model_error_sp if model_error_sp is not None and market_error_sp is not None else None,
        "directional_bias_sp_plus": sp_margin - model_margin if sp_margin is not None and model_margin is not None else None,
        "model_delta_vs_sp_plus_margin": model_margin - sp_margin if sp_margin is not None and model_margin is not None else None,
        "sp_plus_source": sp_plus.get("source") if sp_plus else None, "sp_plus_collected_at": sp_plus.get("collected_at") if sp_plus else None,
        "cfbd_postgame_win_probability": pg_for, "cfbd_opponent_postgame_win_probability": pg_against,
        "cfbd_equivalent_margin": cfbd_margin,
        "model_abs_error_cfbd_margin": model_error_cfbd, "market_abs_error_cfbd_margin": market_error_cfbd,
        "model_advantage_vs_market_cfbd": market_error_cfbd - model_error_cfbd if model_error_cfbd is not None and market_error_cfbd is not None else None,
        "directional_bias_cfbd": cfbd_margin - model_margin if cfbd_margin is not None and model_margin is not None else None,
        "model_delta_vs_cfbd_margin": model_margin - cfbd_margin if cfbd_margin is not None and model_margin is not None else None,
        "cfbd_pgwe_source": "CollegeFootballData /games", "cfbd_pgwe_source_timestamp": pgwe[2] if pgwe else None,
        "source_artifacts": sorted(set((model.get("source_artifacts", []) if model else []) + ([market["market_source_artifact"]] if market else []) + ["data/canonical/game_results_2026.json"] + (["data/canonical/sp_plus_postgame_2026.json"] if sp_plus else []))),
    }


def aggregate(rows):
    by_team = defaultdict(list)
    for row in rows:
        by_team[row["team"]].append(row)
    output = []
    for team, games in sorted(by_team.items()):
        gradeable = [g for g in games if g["model_abs_error_actual"] is not None and g["market_abs_error_actual"] is not None]
        qualified = [g for g in gradeable if g["qualified_edge"]]
        wins = sum(g["qualified_edge_result"] == "WIN" for g in qualified); losses = sum(g["qualified_edge_result"] == "LOSS" for g in qualified); pushes = sum(g["qualified_edge_result"] == "PUSH" for g in qualified)
        n = len(gradeable); model_beats = sum(g["model_advantage_vs_market_actual"] > 0 for g in gradeable); market_beats = sum(g["model_advantage_vs_market_actual"] < 0 for g in gradeable)
        mean = lambda key, sample=gradeable: sum(g[key] for g in sample) / len(sample) if sample else None
        sp = [g for g in gradeable if g["sp_plus_adjusted_margin"] is not None]
        cfbd = [g for g in gradeable if g["cfbd_equivalent_margin"] is not None]
        lens_counts = lambda sample, key: (sum(g[key] > 0 for g in sample), sum(g[key] < 0 for g in sample))
        sp_model_beats, sp_market_beats = lens_counts(sp, "model_advantage_vs_market_sp_plus")
        cfbd_model_beats, cfbd_market_beats = lens_counts(cfbd, "model_advantage_vs_market_cfbd")
        output.append({"team": team, "games_evaluated": n, "model_mae_vs_actual": mean("model_abs_error_actual"), "market_mae_vs_actual": mean("market_abs_error_actual"),
            "model_advantage_vs_market_actual": mean("model_advantage_vs_market_actual"), "advantage_actual": mean("model_advantage_vs_market_actual"), "model_beat_market_games": model_beats, "market_beat_model_games": market_beats, "ties": n-model_beats-market_beats,
            "model_beat_market_rate": model_beats/n if n else None, "directional_bias_actual": mean("directional_bias_actual"), "bias_actual": mean("directional_bias_actual"), "mean_abs_model_market_edge": sum(abs(g["model_market_edge"]) for g in gradeable)/n if n else None,
            "qualified_edge_games": len(qualified), "qualified_edge_record": f"{wins}-{losses}-{pushes}", "qualified_edge_pushes": pushes, "qualified_edge_win_rate": wins/(wins+losses) if wins+losses else None,
            "qualified_edge_avg_projected_edge": sum(abs(g["model_market_edge"]) for g in qualified)/len(qualified) if qualified else None,
            "qualified_edge_avg_realized_market_residual": mean("realized_market_residual", qualified),
            "sp_plus_games_available": len(sp), "model_mae_vs_sp_plus_margin": mean("model_abs_error_sp_plus_margin", sp),
            "market_mae_vs_sp_plus_margin": mean("market_abs_error_sp_plus_margin", sp),
            "model_advantage_vs_market_sp_plus": mean("model_advantage_vs_market_sp_plus", sp), "directional_bias_sp_plus": mean("directional_bias_sp_plus", sp),
            "model_beat_market_sp_plus_games": sp_model_beats, "market_beat_model_sp_plus_games": sp_market_beats,
            "sp_plus_ties": len(sp)-sp_model_beats-sp_market_beats, "model_beat_market_sp_plus_rate": sp_model_beats/len(sp) if sp else None,
            "cfbd_games_available": len(cfbd), "model_mae_vs_cfbd_margin": mean("model_abs_error_cfbd_margin", cfbd),
            "market_mae_vs_cfbd_margin": mean("market_abs_error_cfbd_margin", cfbd),
            "model_advantage_vs_market_cfbd": mean("model_advantage_vs_market_cfbd", cfbd), "directional_bias_cfbd": mean("directional_bias_cfbd", cfbd),
            "model_beat_market_cfbd_games": cfbd_model_beats, "market_beat_model_cfbd_games": cfbd_market_beats,
            "cfbd_ties": len(cfbd)-cfbd_model_beats-cfbd_market_beats, "model_beat_market_cfbd_rate": cfbd_model_beats/len(cfbd) if cfbd else None,
            "sample_state": "UNAVAILABLE" if n == 0 else "LOW_SAMPLE" if n <= 2 else "DEVELOPING" if n <= 4 else "ESTABLISHED"})
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="data/canonical/game_results_2026.json")
    parser.add_argument("--predictions", default="data/model_tracking/v2/prediction_observations.jsonl")
    parser.add_argument("--reconstructed-contract", default=RECONSTRUCTED_CONTRACT_PATH)
    parser.add_argument("--component-snapshots", default=COMPONENT_SNAPSHOT_PATH)
    parser.add_argument("--market-history", default="data/odds/game_book_line_history.csv")
    parser.add_argument("--checkpoints", default="data/model_tracking/v2/checkpoint_observations.jsonl")
    parser.add_argument("--pgwe", default="data/canonical/cfbd_schedule_2026.json")
    parser.add_argument("--sp-plus-postgame", default="data/canonical/sp_plus_postgame_2026.json")
    parser.add_argument("--output", default="data/site/team_game_evaluations_2026.json")
    parser.add_argument("--allow-empty-output", action="store_true", help="explicitly permit replacing a populated artifact with zero team-game rows")
    args = parser.parse_args()
    results = load_json(args.results).get("games", []); observations = load_jsonl(args.predictions); markets = read_market(args.market_history); checkpoints = load_jsonl(args.checkpoints)
    pgwe = pgwe_index(load_json(args.pgwe)) if Path(args.pgwe).exists() else {}
    eligible_games = [game for game in results if num(game.get("closing_home_spread")) is not None]
    sp_plus, sp_plus_audit = sp_plus_index(load_json(args.sp_plus_postgame), eligible_games) if Path(args.sp_plus_postgame).exists() else ({}, {"source_team_rows": 0, "matched_games": 0, "matched_team_rows": 0, "unmatched": [], "ambiguous": []})
    reconstructed_contract = load_json(args.reconstructed_contract) if Path(args.reconstructed_contract).exists() else {"games": []}
    component_snapshots = load_json(args.component_snapshots) if Path(args.component_snapshots).exists() else {"games": []}
    rows = []; gaps = []; coverage = defaultdict(lambda: {"eligible": 0, "model_reconstructable": 0, "market_reconstructable": 0, "result_available": 0, "all_three": 0, "sp_plus_available": 0, "cfbd_pgwe_available": 0})
    # A non-null result closing spread defines the established 51-game FBS-v-FBS evaluation universe; it is never used as close lifecycle proof.
    for game in results:
        if num(game.get("closing_home_spread")) is None:
            continue
        week = str(game["week"]); coverage[week]["eligible"] += 1; coverage[week]["result_available"] += 1
        model, model_gap = recover_model(game, observations, reconstructed_contract, component_snapshots)
        market = captured_close(game, checkpoints)
        market_gap = None
        if not market:
            market, market_gap = market_close(game, markets)
        if model: coverage[week]["model_reconstructable"] += 1
        if market: coverage[week]["market_reconstructable"] += 1
        if model and market: coverage[week]["all_three"] += 1
        probability = pgwe.get(str(game.get("cfbd_game_id")))
        sp_game = sp_plus.get(str(game["game_id"]), {})
        if sp_game: coverage[week]["sp_plus_available"] += 1
        if probability: coverage[week]["cfbd_pgwe_available"] += 1
        if model_gap or market_gap: gaps.append({"game_id": game["game_id"], "week": game["week"], "away_team": game["away_team"], "home_team": game["home_team"], "model_gap": model_gap, "market_gap": market_gap})
        for side in ("home", "away"):
            rows.append(grade(game[f"{side}_team"], game["away_team" if side == "home" else "home_team"], side, game, model, market, probability, sp_game.get(sp_plus_team_key(game[f"{side}_team"]))))
    payload = {"schema_version": "team-game-evaluations-2026-v3", "built_at": datetime.now(timezone.utc).isoformat(), "policy": {"positive_margin": "team expected or actual to win", "positive_advantage": "model closer than market under the named lens", "positive_bias": "performance or actual margin minus model margin; model underrated team", "benchmarks": "score, SP+ adjusted performance margin, and CFBD equivalent margin remain separate; no blended consensus", "sp_plus_adjusted_margin": "direct source truth from the SP+ POSTGAME WIN EXPECTANCY table", "cfbd_equivalent_margin": {"version": CFBD_EQUIVALENT_MARGIN_VERSION, "anchors_percent_to_margin": [list(anchor) for anchor in CFBD_EQUIVALENT_MARGIN_ANCHORS], "interpolation": "linear between anchors with exact sign symmetry below 50%", "provenance": CFBD_EQUIVALENT_MARGIN_PROVENANCE, "endpoint_policy": "0 maps to -65.0 and 1 maps to +65.0 under the approved reference tail"}, "deprecated_public_model_fit_conversion": "pgwe_adjusted_margin_v1 is research-only and does not feed this contract", "fbs_universe_note": "result closing_home_spread selects the established FBS-v-FBS universe only; market reconstruction comes exclusively from pre-kickoff history"}, "coverage_by_week": dict(coverage), "sp_plus_match_audit": sp_plus_audit, "gaps": gaps, "team_games": rows, "team_aggregates": aggregate(rows)}
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    if not rows and output.exists() and not args.allow_empty_output:
        prior = load_json(output)
        if prior.get("team_games"):
            raise SystemExit("refusing to replace a populated Model Fit artifact with zero rows; pass --allow-empty-output only for an intentional reset")
    with tempfile.NamedTemporaryFile("w", dir=output.parent, delete=False) as handle:
        json.dump(payload, handle, indent=2, allow_nan=False); handle.write("\n"); tmp = Path(handle.name)
    tmp.replace(output); print(json.dumps({"output": str(output), "team_game_rows": len(rows), "coverage_by_week": payload["coverage_by_week"], "gaps": len(gaps)}, indent=2))


if __name__ == "__main__": main()
