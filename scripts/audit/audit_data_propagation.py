#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path(os.environ.get("NCAAF_MAIN_REPO", "/Users/jameslindesmith/NCAAF_MAIN_REPO"))
OUT = ROOT / "data/audits/data_propagation_audit.json"
MD = ROOT / "data/audits/data_propagation_audit.md"
MMD = ROOT / "data/audits/data_flow_market_ratings.mmd"


def digest(path: Path):
    if not path.exists(): return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(path: Path):
    if not path.exists(): return []
    with path.open(newline="", encoding="utf-8-sig") as f: return list(csv.DictReader(f))


def load(path: Path):
    try: return json.loads(path.read_text())
    except Exception: return {}


def num(value):
    try: return float(value)
    except Exception: return None


def main():
    checks=[]; mismatches=[]
    paths={
      "runtime_odds":ROOT/"data/site/odds_screen_v2.json",
      "public_odds":ROOT/"build/public_site/data/site/odds_screen_v2.json",
      "main_odds":MAIN/"data/site/odds_screen_v2.json",
      "runtime_matchups":ROOT/"data/site/matchups_view.json",
      "public_matchups":ROOT/"build/public_site/data/site/matchups_view.json",
      "main_matchups":MAIN/"data/site/matchups_view.json",
      "canonical_game_projections":ROOT/"data/site/current_game_projection_contract.json",
      "history":ROOT/"data/site/matchup_line_history.json",
      "ratings_latest":ROOT/"data/ratings/ratings_latest.csv",
      "ratings_status":ROOT/"data/ratings/ratings_source_status.csv"
    }
    for name,path in paths.items():
        checks.append({"area":"file","name":name,"status":"PASS" if path.exists() else "MISSING_OUTPUT","path":str(path),"sha256":digest(path)})
    for a,b,name in [
      ("runtime_odds","public_odds","runtime_to_public_odds"),
      ("public_odds","main_odds","public_to_main_odds"),
      ("runtime_matchups","public_matchups","runtime_to_public_matchups"),
      ("public_matchups","main_matchups","public_to_main_matchups")]:
        checks.append({"area":"publishing","name":name,"status":"PASS" if digest(paths[a]) and digest(paths[a])==digest(paths[b]) else "PUBLISH_MISMATCH"})
    latest_date=max((r.get("snapshot_date","") for r in rows(paths["ratings_latest"])),default="")
    status_date=max((r.get("snapshot_date","") for r in rows(paths["ratings_status"])),default="")
    checks.append({"area":"ratings","name":"ratings_status_freshness","status":"PASS" if latest_date==status_date else "STALE_DERIVED_ARTIFACT","ratings_latest":latest_date,"ratings_status":status_date})
    projections=load(paths["canonical_game_projections"]); projection_games=projections.get("games",[])
    required_models={"standard_spread_4src_equal_v1","standard_total_sp_massey_dratings_v1","standard_spread_5src_legacy_v1","standard_total_40_40_20_sagarin_legacy_v1","total_sp50_massey50_v1","standard_spread_degraded_v1","standard_total_degraded_v1","shadow_spread_sp_sagarin_v1","shadow_total_enhanced_spplus_od_v1"}
    projection_ids=[str(x.get("game_id")) for x in projection_games]
    projection_ok=(
        projections.get("schema_version")=="current-game-projection-contract-v1"
        and projections.get("canonical_game_count")==len(projection_games)
        and len(projection_ids)==len(set(projection_ids))
        and all(set(x.get("projections",{}))==required_models for x in projection_games)
    )
    resolver_ok = (
        projection_ok
        and projections.get("policy", {}).get("resolver_policy") == "STRICT_CANONICAL_ONLY_NO_FALLBACK_SUBSTITUTIONS"
        and all(
            set(x.get("resolved_projections", {})) == required_models
            and all(
                result.get("fallback_used") is False
                and result.get("selection_status") in {"AVAILABLE", "UNAVAILABLE"}
                for result in x.get("resolved_projections", {}).values()
            )
            for x in projection_games
        )
        and all(
            set(x.get("operational_projections", {})) == {"spread", "total"}
            for x in projection_games
        )
    )
    checks.append({"area":"projections","name":"canonical_game_projection_contract","status":"PASS" if resolver_ok else "CONTRACT_MISMATCH","games":len(projection_games),"consumer_status":"PRODUCTION_RESOLVER_ACTIVE"})
    hist=load(paths["history"]); mv=load(paths["runtime_matchups"])
    byid={str(x.get("game",{}).get("game_id")):x for x in mv.get("games",[])}
    for gid,points in hist.items():
        if gid not in byid or not points: continue
        last=max(points,key=lambda x:str(x.get("snapshot_ts") or x.get("snapshot_date") or ""))
        market=byid[gid].get("market",{})
        hs,ms=num(last.get("market_spread_home")),num(market.get("spread",{}).get("home_line"))
        ht,mt=num(last.get("market_total")),num(market.get("total",{}).get("line"))
        if hs is not None and ms is not None and abs(hs-ms)>.01: mismatches.append({"game_id":gid,"field":"spread","history":hs,"matchups_view":ms})
        if ht is not None and mt is not None and abs(ht-mt)>.01: mismatches.append({"game_id":gid,"field":"total","history":ht,"matchups_view":mt})
    checks.append({"area":"market","name":"latest_history_vs_matchups_view","status":"PASS" if not mismatches else "VALUE_MISMATCH","count":len(mismatches)})
    status="PASS" if all(x["status"]=="PASS" for x in checks) else "WARN"
    payload={"generated_at":datetime.now(timezone.utc).isoformat(),"status":status,"checks":checks,"market_mismatches":mismatches[:200]}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2)+"\n")
    MD.write_text("# Data Propagation Audit\n\n| Area | Check | Status |\n|---|---|---|\n"+"\n".join(f"| {x['area']} | {x['name']} | {x['status']} |" for x in checks)+f"\n\nMarket mismatches: {len(mismatches)}\n")
    MMD.write_text("""flowchart LR
SGO[SportsGameOdds] --> ODDSPAYLOAD[odds_screen_v2.json]
SGO --> HISTORY[matchup_line_history.json]
ODDSPAYLOAD --> MATCHUPPAYLOAD[matchups_view.json]
MATCHUPPAYLOAD --> OPENERS[Openers]
MATCHUPPAYLOAD --> MATCHUPS[Matchups]
MATCHUPPAYLOAD --> HOME[War Room Home]
ODDSPAYLOAD --> ODDS[Odds]
RATINGS[ratings_latest.csv] --> STATUS[ratings_source_status.csv]
RATINGS --> RATINGSVIEW[ratings_view.json]
STATUS --> RATINGSVIEW
RATINGSVIEW --> RATINGSPAGE[Ratings]
SOURCES[Normalized game projection sources] --> PROJECTIONS[current_game_projection_contract.json]
PROJECTIONS --> RESOLVER[Strict canonical projection resolver]
RESOLVER -->|AVAILABLE or explicit UNAVAILABLE| MATCHUPPAYLOAD
RESOLVER --> SHADOWLINES[saturday_shadow_lines.json]
PUBLIC[build/public_site] --> MAIN[NCAAF_MAIN_REPO]
MAIN --> GITHUB[GitHub Pages]
""")
    print(json.dumps({"status":status,"market_mismatches":len(mismatches),"report":str(MD),"diagram":str(MMD)},indent=2))

if __name__=="__main__": main()
