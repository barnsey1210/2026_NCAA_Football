#!/usr/bin/env python3
"""Forensically reconstruct provable W0/W1 Standard, DRatings, and Total checkpoints."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from immutable_tracking import append_unique, stable_id

ROOT = Path(__file__).resolve().parents[3]
SOURCE_COMMIT = "cad503f9754f4ee057ef2040e5c297e8fdae08e7"
SOURCE_PATH = "data/site/current_game_projection_contract.json"
MARKET_HISTORY = ROOT / "data/odds/game_book_line_history.csv"
CLOSE_CONTRACT = ROOT / "data/site/current_market_contract.json"
MANIFEST = ROOT / "data/model_tracking/v2/historical_reconstruction_w0_w1_2026.json"
CHECKPOINTS = {
    "SUNDAY_9PM_ET": {0: "2026-08-24T01:00:00+00:00", 1: "2026-08-31T01:00:00+00:00"},
    "TUESDAY_9PM_ET": {0: "2026-08-26T01:00:00+00:00", 1: "2026-09-02T01:00:00+00:00"},
}
MODELS = {
    "standard_spread_4src_equal_v1": ("spread", "direct", "standard_spread_4src_equal_v1"),
    "dratings_spread": ("spread", "component", "DRatings"),
    "sp_plus_total": ("total", "component", "SP+"),
    "massey_dual_total": ("total", "component", "Massey Dual"),
    "dratings_total": ("total", "component", "DRatings Total"),
    "standard_total_sp_massey_dratings_v1": ("total", "direct", "standard_total_sp_massey_dratings_v1"),
}


def parse_dt(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def file_evidence(path, evidence_type, status="SUPPORTING_NOT_USED"):
    if not path.exists():
        return {"artifact": str(path), "evidence_type": evidence_type, "status": "UNAVAILABLE"}
    raw = path.read_bytes()
    return {"artifact": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "sha256": sha256(raw), "bytes": len(raw), "evidence_type": evidence_type, "status": status}


def read_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def source_contract():
    raw = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"], cwd=ROOT,
        check=True, capture_output=True,
    ).stdout
    payload = json.loads(raw)
    return payload, raw


def market_rows():
    raw = MARKET_HISTORY.read_bytes()
    with MARKET_HISTORY.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle)), raw


def game_match(row, game):
    if str(row.get("canonical_game_id") or "") == str(game.get("game_id") or ""):
        return True
    norm = lambda x: " ".join(str(x or "").lower().replace("&", "and").split())
    return (str(row.get("date") or "")[:10] == str(game.get("date") or "")[:10]
            and norm(row.get("away_team")) == norm(game.get("away_team"))
            and norm(row.get("home_team")) == norm(game.get("home_team")))


def archived_pair(rows, game, market_type, cutoff):
    eligible = [row for row in rows if str(row.get("market") or "").lower() == market_type
                and "pinnacle" in str(row.get("book") or "").lower()
                and parse_dt(row.get("snapshot_ts")) and parse_dt(row.get("snapshot_ts")) <= cutoff
                and parse_dt(row.get("source_updated_at") or row.get("book_last_updated") or row.get("snapshot_ts"))
                and parse_dt(row.get("source_updated_at") or row.get("book_last_updated") or row.get("snapshot_ts")) <= cutoff
                and game_match(row, game)]
    if not eligible:
        return None
    latest = max(parse_dt(row["snapshot_ts"]) for row in eligible)
    snapshot = {str(row.get("side") or "").lower(): row for row in eligible if parse_dt(row["snapshot_ts"]) == latest}
    sides = ("home", "away") if market_type == "spread" else ("over", "under")
    if not all(side in snapshot and snapshot[side].get("line") not in (None, "") for side in sides):
        return None
    return latest, snapshot


def projection_value(game, model_id):
    market_type, method, key = MODELS[model_id]
    owner = "standard_spread_4src_equal_v1" if market_type == "spread" else "standard_total_sp_massey_dratings_v1"
    projection = (game.get("projections") or {}).get(owner) or {}
    if method == "direct":
        value = projection.get("value_home_margin" if market_type == "spread" else "value_total")
    else:
        value = (projection.get("component_values") or {}).get(key)
    if value is None:
        return None, projection
    return float(value), projection


def pair_orientation_valid(market_type, sides):
    try:
        if market_type == "spread":
            return abs(float(sides["home"]["line"]) + float(sides["away"]["line"])) < 1e-9
        return abs(float(sides["over"]["line"]) - float(sides["under"]["line"])) < 1e-9
    except (KeyError, TypeError, ValueError):
        return False


def reject(record, reason):
    record.update(status="REJECTED", rejection_reason=reason)
    return record


def timing_rejection(model_at, market_at, checkpoint_at, kickoff, close=False):
    if kickoff is None:
        return "kickoff_unresolved"
    if model_at is None:
        return "model_source_unproven"
    if model_at > checkpoint_at:
        return "model_after_checkpoint"
    if model_at > kickoff:
        return "model_after_kickoff"
    if market_at is None:
        return "market_source_unproven"
    if market_at > checkpoint_at:
        return "market_after_checkpoint"
    if market_at > kickoff:
        return "market_after_kickoff"
    if close and model_at > min(checkpoint_at, kickoff):
        return "close_model_after_bound"
    return None


def make_prediction(game, model_id, market_type, value, projection, evidence_at, source_hash):
    observation_id = stable_id("forensic_prediction", game["game_id"], model_id, "v1", evidence_at.isoformat(), value)
    return {
        "observation_id": observation_id, "season": 2026, "week": game.get("week"),
        "canonical_game_id": game["game_id"], "away_team": game.get("away_team"),
        "home_team": game.get("home_team"), "kickoff_at": game.get("kickoff_at") or game.get("date"),
        "model_id": model_id, "model_version": "v1", "market_type": market_type,
        "observed_at": evidence_at.isoformat(), "model_calculated_at": evidence_at.isoformat(),
        "source_updated_at": evidence_at.isoformat(), "source_snapshot_timestamps": projection.get("component_source_timestamps") or {},
        "projection": value, "component_values": projection.get("component_values") or {},
        "component_weights": projection.get("weights") or {}, "component_availability": projection.get("component_status") or {},
        "missing_components": projection.get("missing_sources") or [], "lifecycle_state": "HISTORICAL_FORENSIC_RECONSTRUCTION",
        "source_artifacts": [f"git:{SOURCE_COMMIT}:{SOURCE_PATH}"], "contract_id": projection.get("contract_build_id"),
        "formula_version": projection.get("formula_version"), "availability_status": "AVAILABLE",
        "provenance_flags": {"historical_reconstruction": True, "source_commit": SOURCE_COMMIT, "source_sha256": source_hash},
    }


def market_observation(game, market_type, side, raw, source_hash, frozen=False):
    observed = raw.get("source_updated_at") or raw.get("snapshot_ts") or raw.get("book_last_updated")
    book = raw.get("sportsbook") or raw.get("book") or "Pinnacle"
    line = float(raw["line"])
    oid = stable_id("forensic_market", game["game_id"], market_type, book, side, observed, line, raw.get("price"))
    return {"observation_id": oid, "canonical_game_id": game["game_id"], "market_type": market_type,
            "sportsbook": book, "side": side, "observed_at": observed, "source_updated_at": observed,
            "line": line, "price": float(raw["price"]) if raw.get("price") not in (None, "") else None,
            "source": raw.get("source") or "Historical market archive",
            "freshness_status": "FROZEN_CLOSE" if frozen else "HISTORICAL_ARCHIVE",
            "lifecycle_state": raw.get("market_lifecycle_state") or ("CLOSED" if frozen else "HISTORICAL_CHECKPOINT"),
            "kickoff_at": game.get("kickoff_at") or game.get("date"), "contract_id": None,
            "provenance_flags": {"historical_reconstruction": True, "source_sha256": source_hash}}


def accepted_checkpoint(game, model_id, market_type, checkpoint, target, prediction, pair, source_hash, frozen=False):
    _, sides = pair
    base_side = "home" if market_type == "spread" else "over"
    base_line = float(sides[base_side]["line"])
    side = ("home" if prediction["projection"] + base_line >= 0 else "away") if market_type == "spread" else ("over" if prediction["projection"] - base_line >= 0 else "under")
    markets = [market_observation(game, market_type, s, raw, source_hash, frozen) for s, raw in sides.items() if s in ({"home", "away"} if market_type == "spread" else {"over", "under"})]
    chosen = next(row for row in markets if row["side"] == side)
    checkpoint_id = stable_id("official_checkpoint", game["game_id"], model_id, "v1", market_type, checkpoint)
    row = {"checkpoint_id": checkpoint_id, "canonical_game_id": game["game_id"], "season": 2026,
           "week": game.get("week"), "away_team": game.get("away_team"), "home_team": game.get("home_team"),
           "kickoff_at": game.get("kickoff_at") or game.get("date"), "model_id": model_id, "model_version": "v1",
           "market_type": market_type, "checkpoint": checkpoint, "checkpoint_at": target.isoformat(),
           "prediction_observation_id": prediction["observation_id"], "prediction": prediction["projection"],
           "prediction_observed_at": prediction["observed_at"], "prediction_source_updated_at": prediction["source_updated_at"],
           "market_observation_id": chosen["observation_id"], "market_line": chosen["line"], "market_price": chosen["price"],
           "market_book": chosen["sportsbook"], "market_source": chosen["source"], "market_observed_at": chosen["observed_at"],
           "market_source_updated_at": chosen["source_updated_at"], "market_benchmark": "FROZEN_CLOSE" if frozen else "PINNACLE",
           "bet_side": side, "edge": abs(prediction["projection"] + chosen["line"] if market_type == "spread" else prediction["projection"] - chosen["line"]),
           "decision_id": None, "selection_status": "OFFICIAL", "selection_origin": "HISTORICAL_FORENSIC_RECONSTRUCTION",
           "created_at": target.isoformat()}
    return markets, row, side


def build(ledger_root):
    contract, contract_raw = source_contract(); history, history_raw = market_rows()
    evidence_at = parse_dt(contract.get("built_at")); source_hash = sha256(contract_raw); history_hash = sha256(history_raw)
    games = [game for game in contract.get("games", []) if game.get("week") in {0, 1} and game.get("game_id")]
    close_by_id = {str(row.get("game_id")): row for row in load_close_games() if row.get("game_id")}
    for game in games:
        if not game.get("kickoff_at"):
            game["kickoff_at"] = (close_by_id.get(str(game["game_id"])) or {}).get("kickoff_at")
    predictions_existing = read_jsonl(ledger_root / "prediction_observations.jsonl")
    manifest_rows=[]; predictions=[]; markets=[]; checkpoints=[]
    for game in games:
        kickoff = parse_dt(game.get("kickoff_at") or game.get("date"))
        for model_id, (market_type, _, _) in MODELS.items():
            value, projection = projection_value(game, model_id)
            for checkpoint, weeks in CHECKPOINTS.items():
                target=parse_dt(weeks[game["week"]]); rec={"game_id":game["game_id"],"matchup":f"{game.get('away_team')} at {game.get('home_team')}","week":game["week"],"kickoff":game.get("kickoff_at") or game.get("date"),"market_type":market_type,"model_id":model_id,"model_version":"v1","checkpoint":checkpoint,"target_checkpoint_timestamp":target.isoformat(),"model_value":value,"model_evidence_artifact":f"git:{SOURCE_COMMIT}:{SOURCE_PATH}","model_evidence_timestamp":evidence_at.isoformat(),"model_evidence_sha256":source_hash,"market_evidence_artifact":str(MARKET_HISTORY.relative_to(ROOT)),"market_evidence_sha256":history_hash,"reconstruction_method":"PRESERVED_CANONICAL_CONTRACT_PLUS_ARCHIVED_PINNACLE"}
                timing_reason = timing_rejection(evidence_at, target, target, kickoff)
                if timing_reason: manifest_rows.append(reject(rec,timing_reason)); continue
                if value is None: manifest_rows.append(reject(rec,"incomplete_components")); continue
                if model_id.startswith("standard_") and projection.get("formula_version") != "v1": manifest_rows.append(reject(rec,"formula_version_unproven")); continue
                if model_id=="standard_spread_4src_equal_v1" and set((projection.get("weights") or {})) != {"SP+","FPI","TeamRankings","DRatings"}: manifest_rows.append(reject(rec,"incomplete_components")); continue
                if model_id=="standard_total_sp_massey_dratings_v1" and set((projection.get("weights") or {})) != {"SP+","Massey Dual","DRatings Total"}: manifest_rows.append(reject(rec,"incomplete_components")); continue
                pair=archived_pair(history,game,market_type,target)
                if pair is None: manifest_rows.append(reject(rec,"no_market_pair")); continue
                if not pair_orientation_valid(market_type,pair[1]): manifest_rows.append(reject(rec,"orientation_unproven")); continue
                timing_reason = timing_rejection(evidence_at, pair[0], target, kickoff)
                if timing_reason: manifest_rows.append(reject(rec,timing_reason)); continue
                prediction=make_prediction(game,model_id,market_type,value,projection,evidence_at,source_hash)
                market_set, checkpoint_row, side=accepted_checkpoint(game,model_id,market_type,checkpoint,target,prediction,pair,history_hash)
                rec.update(status="ACCEPTED",rejection_reason=None,market_line=checkpoint_row["market_line"],price=checkpoint_row["market_price"],selected_market_book=checkpoint_row["market_book"],market_evidence_timestamp=checkpoint_row["market_observed_at"],orientation_normalization={"canonical_orientation":"home_margin" if market_type=="spread" else "combined_points","selected_side":side},prediction_observation_id=prediction["observation_id"],checkpoint_id=checkpoint_row["checkpoint_id"])
                manifest_rows.append(rec); predictions.append(prediction); markets.extend(market_set); checkpoints.append(checkpoint_row)
        # Close uses the latest already-accepted prediction at the frozen timestamp bound.
        close_game=close_by_id.get(str(game["game_id"]))
        if close_game:
            for model_id,(market_type,_,_) in MODELS.items():
                reference=(close_game.get("reference") or {}).get(market_type) or {}; base=reference.get("home" if market_type=="spread" else "over") or {}
                rec={"game_id":game["game_id"],"matchup":f"{game.get('away_team')} at {game.get('home_team')}","week":game["week"],"kickoff":game.get("kickoff_at") or game.get("date"),"market_type":market_type,"model_id":model_id,"model_version":"v1","checkpoint":"CLOSE","target_checkpoint_timestamp":base.get("source_updated_at"),"reconstruction_method":"LATEST_ACCEPTED_PREDICTION_PLUS_CANONICAL_FROZEN_CLOSE"}
                if str(base.get("freshness_status") or "").upper()!="FROZEN_CLOSE": manifest_rows.append(reject(rec,"no_frozen_close")); continue
                close_at=parse_dt(base.get("source_updated_at")); bound=min(x for x in (close_at,kickoff) if x)
                if close_at is None: manifest_rows.append(reject(rec,"no_frozen_close")); continue
                eligible=[p for p in predictions_existing+predictions if p.get("canonical_game_id")==game["game_id"] and p.get("model_id")==model_id and p.get("model_version")=="v1" and p.get("formula_version")=="v1" and p.get("market_type")==market_type and p.get("projection") is not None and parse_dt(p.get("observed_at")) and parse_dt(p.get("observed_at"))<=bound]
                if not eligible: manifest_rows.append(reject(rec,"model_source_unproven")); continue
                prediction=max(eligible,key=lambda p:parse_dt(p["observed_at"])); sides={s:reference.get(s) or {} for s in (("home","away") if market_type=="spread" else ("over","under"))}
                if not all(str(q.get("freshness_status") or "").upper()=="FROZEN_CLOSE" and q.get("line") is not None for q in sides.values()): manifest_rows.append(reject(rec,"no_frozen_close")); continue
                if not pair_orientation_valid(market_type,sides): manifest_rows.append(reject(rec,"orientation_unproven")); continue
                timing_reason = timing_rejection(parse_dt(prediction.get("observed_at")), close_at, close_at, kickoff, close=True)
                if timing_reason: manifest_rows.append(reject(rec,timing_reason)); continue
                pair=(close_at,sides); market_set,checkpoint_row,side=accepted_checkpoint(game,model_id,market_type,"CLOSE",close_at,prediction,pair,sha256(CLOSE_CONTRACT.read_bytes()),True)
                rec.update(status="ACCEPTED",rejection_reason=None,model_value=prediction.get("projection"),model_evidence_artifact=(prediction.get("source_artifacts") or [None])[0],model_evidence_timestamp=prediction.get("observed_at"),model_evidence_sha256=(prediction.get("provenance_flags") or {}).get("source_sha256"),market_line=checkpoint_row["market_line"],price=checkpoint_row["market_price"],selected_market_book=checkpoint_row["market_book"],market_evidence_artifact=str(CLOSE_CONTRACT.relative_to(ROOT)),market_evidence_timestamp=checkpoint_row["market_observed_at"],market_evidence_sha256=sha256(CLOSE_CONTRACT.read_bytes()),orientation_normalization={"canonical_orientation":"home_margin" if market_type=="spread" else "combined_points","selected_side":side},prediction_observation_id=prediction["observation_id"],checkpoint_id=checkpoint_row["checkpoint_id"])
                manifest_rows.append(rec); markets.extend(market_set); checkpoints.append(checkpoint_row)
    ledger_inventory={}
    for name in ("prediction_observations.jsonl","market_observations.jsonl","checkpoint_observations.jsonl","settlements.jsonl","scores.jsonl"):
        path=ledger_root/name; entry=file_evidence(path,"RUNTIME_LEDGER_ONLY","INPUT_PRESERVED")
        if path.exists(): entry["rows"]=sum(1 for line in path.open() if line.strip())
        ledger_inventory[name]=entry
    backup_inventory=[file_evidence(path,"EXACT_ACCEPTED_BACKUP") for path in sorted((ROOT/"data/ratings/accepted_backups").glob("*")) if path.is_file()]
    inventory={"projection_contract":{"artifact":f"git:{SOURCE_COMMIT}:{SOURCE_PATH}","sha256":source_hash,"built_at":contract.get("built_at"),"games":len(contract.get("games",[])),"models_components":list(MODELS),"evidence_type":"EXACT_GIT_OBJECT","status":"USED"},"ratings_history":file_evidence(ROOT/"data/ratings/ratings_history.csv","EXACT_ARCHIVE"),"accepted_rating_backups":backup_inventory,"market_history":{"artifact":str(MARKET_HISTORY.relative_to(ROOT)),"sha256":history_hash,"rows":len(history),"evidence_type":"EXACT_ARCHIVE","status":"USED"},"frozen_close":{**file_evidence(CLOSE_CONTRACT,"CANONICAL_FROZEN_CLOSE","USED"),"built_at":json.loads(CLOSE_CONTRACT.read_text()).get("built_at")},"schedule_kickoffs":file_evidence(ROOT/"data/site/current_game_projection_contract.json","CANONICAL_SCHEDULE_CONTRACT","USED_FOR_KICKOFF_ENRICHMENT"),"prior_reconstruction_manifests":[file_evidence(path,"EXACT_RECONSTRUCTION_MANIFEST") for path in sorted((ROOT/"data/model_tracking/reconstructed").glob("*")) if path.is_file()],"runtime_ledgers":{"path":str(ledger_root),"evidence_type":"RUNTIME_LEDGER_ONLY","ledgers":ledger_inventory}}
    summary={}
    for row in manifest_rows:
        key=f"W{row['week']}|{row['model_id']}|{row['checkpoint']}"; bucket=summary.setdefault(key,{"candidates":0,"accepted":0,"rejected":0,"rejection_reasons":{}}); bucket["candidates"]+=1; bucket[row["status"].lower()]+=1
        if row.get("rejection_reason"): bucket["rejection_reasons"][row["rejection_reason"]]=bucket["rejection_reasons"].get(row["rejection_reason"],0)+1
    for bucket in summary.values(): bucket["scheduled_games"]=bucket["candidates"]
    return {"schema_version":"historical-reconstruction-w0-w1-2026-v1","generated_at":json.loads(CLOSE_CONTRACT.read_text()).get("built_at"),"policy":{"no_lookahead":True,"source_commit":SOURCE_COMMIT,"sunday_from_source_contract":"REJECTED_MODEL_AFTER_CHECKPOINT"},"inventory":inventory,"summary":summary,"records":manifest_rows},predictions,markets,checkpoints


_close_cache=None
def load_close_games():
    global _close_cache
    if _close_cache is None: _close_cache=json.loads(CLOSE_CONTRACT.read_text()).get("games",[])
    return _close_cache


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--accept",action="store_true"); parser.add_argument("--ledger-root",type=Path,default=ROOT/"data/model_tracking/v2"); parser.add_argument("--manifest",type=Path,default=MANIFEST); args=parser.parse_args()
    manifest,predictions,markets,checkpoints=build(args.ledger_root)
    args.manifest.parent.mkdir(parents=True,exist_ok=True); args.manifest.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    report={"manifest":str(args.manifest),"summary":manifest["summary"],"predictions":append_unique(args.ledger_root/"prediction_observations.jsonl",predictions,"observation_id",args.accept),"markets":append_unique(args.ledger_root/"market_observations.jsonl",markets,"observation_id",args.accept),"checkpoints":append_unique(args.ledger_root/"checkpoint_observations.jsonl",checkpoints,"checkpoint_id",args.accept)}
    print(json.dumps(report,indent=2,sort_keys=True))


if __name__ == "__main__": main()
