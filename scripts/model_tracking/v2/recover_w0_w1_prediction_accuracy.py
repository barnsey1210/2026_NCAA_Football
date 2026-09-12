#!/usr/bin/env python3
"""Recover provable W0/W1 prediction-only observations from Git contracts."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from immutable_tracking import append_unique, stable_id

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = "data/site/current_game_projection_contract.json"
DEFAULT_RUNTIME = Path("/Users/jameslindesmith/NCAAF_AUTO")
DEFAULT_MANIFEST = ROOT / "data/model_tracking/v2/historical_prediction_recovery_w0_w1_2026.json"

MODEL_SPECS = {
    "standard_spread_4src_equal_v1": ("spread", "standard_spread_4src_equal_v1", "value_home_margin", None),
    "sp_plus_spread": ("spread", "standard_spread_4src_equal_v1", "component_values", "SP+"),
    "fpi_spread": ("spread", "standard_spread_4src_equal_v1", "component_values", "FPI"),
    "teamrankings_spread": ("spread", "standard_spread_4src_equal_v1", "component_values", "TeamRankings"),
    "sagarin_spread": ("spread", "standard_spread_5src_legacy_v1", "component_values", "Sagarin Rating"),
    "dratings_spread": ("spread", "standard_spread_4src_equal_v1", "component_values", "DRatings"),
    "shadow_spread_sp_sagarin_v1": ("spread", "shadow_spread_sp_sagarin_v1", "value_home_margin", None),
    "standard_total_sp_massey_dratings_v1": ("total", "standard_total_sp_massey_dratings_v1", "value_total", None),
    "sp_plus_total": ("total", "standard_total_sp_massey_dratings_v1", "component_values", "SP+"),
    "massey_dual_total": ("total", "standard_total_sp_massey_dratings_v1", "component_values", "Massey Dual"),
    "sagarin_total": ("total", "standard_total_40_40_20_sagarin_legacy_v1", "component_values", "Sagarin Total"),
    "dratings_total": ("total", "standard_total_sp_massey_dratings_v1", "component_values", "DRatings Total"),
    "total_sp50_massey50_v1": ("total", "total_sp50_massey50_v1", "value_total", None),
    "shadow_total_enhanced_spplus_od_v1": ("total", "shadow_total_enhanced_spplus_od_v1", "value_total", None),
}


def parse_dt(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def contract_history(repo):
    commits = git(repo, "log", "--all", "--format=%H", "--", CONTRACT_PATH).decode().splitlines()
    rows = []
    for commit in commits:
        raw = git(repo, "show", f"{commit}:{CONTRACT_PATH}")
        payload = json.loads(raw)
        built_at = parse_dt(payload.get("built_at"))
        if built_at:
            rows.append({"commit": commit, "raw": raw, "payload": payload, "built_at": built_at,
                         "sha256": hashlib.sha256(raw).hexdigest()})
    return sorted(rows, key=lambda row: (row["built_at"], row["commit"]))


def fbs_teams(repo):
    payload = json.loads((repo / "data/snapshots/preseason/preseason_db.json").read_text())
    return {str(row.get("team")) for row in payload.get("teams", []) if row.get("team")}


def result_index(runtime):
    payload = json.loads((runtime / "data/canonical/game_results_2026.json").read_text())
    return {str(row["game_id"]): row for row in payload.get("games", []) if row.get("game_id")}


def projection_value(game, model_id):
    market_type, owner, field, component = MODEL_SPECS[model_id]
    projection = (game.get("projections") or {}).get(owner) or {}
    value = (projection.get(field) or {}).get(component) if component else projection.get(field)
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = None
    return market_type, projection, value


def authority_rejection(model_id, projection):
    if not projection or projection.get("formula_version") != "v1":
        return "formula_version_unproven"
    if model_id == "standard_spread_4src_equal_v1":
        if projection.get("formula_status") != "PRODUCTION_VALIDATED" or projection.get("weights") != {
            "SP+": .25, "FPI": .25, "TeamRankings": .25, "DRatings": .25,
        }:
            return "formula_version_unproven"
    if model_id == "standard_total_sp_massey_dratings_v1":
        if projection.get("formula_status") != "PRODUCTION_AUTHORITY_APPROVED" or projection.get("weights") != {
            "SP+": .4, "Massey Dual": .4, "DRatings Total": .2,
        }:
            return "formula_version_unproven"
    return None


def prediction_row(game, result, model_id, market_type, projection, value, evidence):
    observed_at = evidence["built_at"].isoformat()
    oid = stable_id("forensic_prediction", game["game_id"], model_id, "v1", observed_at, value)
    component = MODEL_SPECS[model_id][3]
    return {
        "observation_id": oid, "season": 2026, "week": game["week"],
        "canonical_game_id": game["game_id"], "away_team": game.get("away_team"),
        "home_team": game.get("home_team"), "kickoff_at": result["start_date"],
        "model_id": model_id, "model_version": "v1", "market_type": market_type,
        "observed_at": observed_at, "model_calculated_at": observed_at,
        "source_updated_at": ((projection.get("component_source_timestamps") or {}).get(component)
                              if component else projection.get("freshness_timestamp")),
        "source_snapshot_timestamps": projection.get("component_source_timestamps") or {},
        "projection": value,
        "component_values": ({component: value} if component else projection.get("component_values") or {}),
        "component_weights": projection.get("weights") or {},
        "component_availability": projection.get("component_status") or {},
        "missing_components": projection.get("missing_sources") or [],
        "lifecycle_state": "HISTORICAL_PREDICTION_ONLY_RECOVERY",
        "source_artifacts": [f"git:{evidence['commit']}:{CONTRACT_PATH}"],
        "contract_id": projection.get("contract_build_id"), "formula_version": "v1",
        "availability_status": "AVAILABLE",
        "provenance_flags": {"historical_prediction_recovery": True, "source_commit": evidence["commit"],
                             "source_sha256": evidence["sha256"], "immutable_prediction_bound": observed_at},
    }


def build(source_repo, runtime):
    history = contract_history(source_repo)
    latest_contract = history[-1]["payload"]
    fbs = fbs_teams(source_repo)
    results = result_index(runtime)
    universe = [game for game in latest_contract.get("games", []) if game.get("week") in {0, 1}
                and game.get("away_team") in fbs and game.get("home_team") in fbs]
    games_by_contract = {row["commit"]: {str(g.get("game_id")): g for g in row["payload"].get("games", [])}
                         for row in history}
    records, predictions = [], []
    for game in sorted(universe, key=lambda g: (g["week"], str(g["game_id"]))):
        game_id = str(game["game_id"])
        result = results.get(game_id)
        kickoff = parse_dt((result or {}).get("start_date"))
        for model_id in MODEL_SPECS:
            candidates = []
            post_kickoff_value = False
            authority_failures = Counter()
            for evidence in history:
                historical_game = games_by_contract[evidence["commit"]].get(game_id)
                if historical_game is None:
                    continue
                market_type, projection, value = projection_value(historical_game, model_id)
                if value is None:
                    continue
                rejection = authority_rejection(model_id, projection)
                if rejection:
                    authority_failures[rejection] += 1
                    continue
                if kickoff is None:
                    continue
                if evidence["built_at"] >= kickoff:
                    post_kickoff_value = True
                    continue
                candidates.append((evidence, historical_game, market_type, projection, value))
            base = {"game_id": game_id, "matchup": f"{game.get('away_team')} at {game.get('home_team')}",
                    "week": game["week"], "kickoff": (result or {}).get("start_date"), "model_id": model_id,
                    "model_version": "v1", "market_type": MODEL_SPECS[model_id][0],
                    "accepted": False, "reconstruction_method": "LATEST_IMMUTABLE_GIT_CONTRACT_BEFORE_KICKOFF"}
            if kickoff is None:
                records.append({**base, "rejection_reason": "game_identity_unresolved"})
            elif not candidates:
                reason = (authority_failures.most_common(1)[0][0] if authority_failures
                          else "prediction_after_kickoff" if post_kickoff_value else "no_pre_kickoff_prediction")
                records.append({**base, "rejection_reason": reason})
            else:
                evidence, historical_game, market_type, projection, value = max(
                    candidates, key=lambda item: (item[0]["built_at"], item[0]["commit"]))
                prediction = prediction_row(historical_game, result, model_id, market_type, projection, value, evidence)
                records.append({**base, "accepted": True, "rejection_reason": None, "prediction_value": value,
                                "prediction_observation_id": prediction["observation_id"],
                                "evidence_artifact": f"git:{evidence['commit']}:{CONTRACT_PATH}",
                                "evidence_commit": evidence["commit"], "evidence_sha256": evidence["sha256"],
                                "evidence_timestamp": evidence["built_at"].isoformat(),
                                "pre_kickoff_validation_result": "PASS"})
                predictions.append(prediction)
    summary = {}
    for record in records:
        key = f"W{record['week']}|{record['model_id']}"
        bucket = summary.setdefault(key, {"scheduled_fbs_vs_fbs": 0, "accepted": 0, "rejected": 0,
                                          "rejection_reasons": {}})
        bucket["scheduled_fbs_vs_fbs"] += 1
        bucket["accepted" if record["accepted"] else "rejected"] += 1
        if record.get("rejection_reason"):
            bucket["rejection_reasons"][record["rejection_reason"]] = bucket["rejection_reasons"].get(record["rejection_reason"], 0) + 1
    inventory = [{"commit": row["commit"], "built_at": row["built_at"].isoformat(),
                  "artifact": f"git:{row['commit']}:{CONTRACT_PATH}", "sha256": row["sha256"],
                  "bytes": len(row["raw"]), "evidence_type": "EXACT_GIT_OBJECT"} for row in history]
    return {"schema_version": "historical-prediction-recovery-w0-w1-2026-v1",
            "generated_at": history[-1]["built_at"].isoformat(),
            "policy": {"population": "FBS_VS_FBS", "market_required": False,
                       "selection": "latest valid immutable contract strictly before verified kickoff",
                       "no_embedded_timestamp_backdating": True},
            "inventory": inventory, "summary": summary, "records": records}, predictions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--accept", action="store_true")
    parser.add_argument("--source-repo", type=Path, default=ROOT)
    parser.add_argument("--runtime-root", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--ledger-root", type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    ledger_root = args.ledger_root or args.runtime_root / "data/model_tracking/v2"
    manifest, predictions = build(args.source_repo.resolve(), args.runtime_root.resolve())
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    report = {"manifest": str(args.manifest), "summary": manifest["summary"],
              "predictions": append_unique(ledger_root / "prediction_observations.jsonl", predictions,
                                           "observation_id", args.accept)}
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
