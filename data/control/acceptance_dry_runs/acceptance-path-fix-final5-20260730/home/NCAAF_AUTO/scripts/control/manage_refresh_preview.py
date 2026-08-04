#!/usr/bin/env python3
"""Create/approve/discard private refresh previews without publishing."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,shutil,uuid
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/"data/control"; PREV=BASE/"previews"
ASSETS=["data/site/odds_screen_v2.json","data/site/odds_futures_v2.json","data/site/matchups_view.json","data/site/matchup_line_history.json","data/ratings/ratings_latest.csv","data/ratings/ratings_master_latest.csv","data/projections/game_projection_blend_2026.csv"]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def atomic(p,v): p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix('.tmp'); q.write_text(json.dumps(v,indent=2)+"\n"); q.replace(p)
def main():
 p=argparse.ArgumentParser(); p.add_argument("action",choices=["create","show","approve","discard"]); p.add_argument("--preview-id"); p.add_argument("--run-id"); a=p.parse_args()
 if a.action=="create":
  pid=a.preview_id or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
  stage=BASE/"staging"/(a.run_id or pid); manifest=stage/"manifest.json"; staged=json.loads(manifest.read_text()) if manifest.exists() else {}
  current={x:sha(ROOT/x) for x in ASSETS}; proposed=staged.get("proposed_assets",{})
  changed=[x for x in ASSETS if proposed.get(x,{}).get("hash") not in (None,current[x])]
  doc={"schema_version":1,"preview_id":pid,"run_id":a.run_id,"created_at":datetime.now(timezone.utc).isoformat(),"status":"PREVIEW_ONLY","raw_observations_preserved":True,
   "market":staged.get("market",{"observations_added":0,"games_changed":0,"sportsbooks_changed":0,"spreads_changed":0,"totals_changed":0,"moneylines_changed":0,"largest_spread_moves":[],"largest_total_moves":[],"suspended_or_removed":[]}),
   "ratings":staged.get("ratings",{"sources_checked":[],"sources_changed":[],"accepted":[],"rejected":[],"teams_changed":0,"largest_moves":[],"source_date_changes":[]}),
   "downstream":staged.get("downstream",{"blended_ratings_changed":False,"projections_changed":0,"largest_projection_moves":[],"new_edges":[],"removed_edges":[],"edge_direction_changes":[],"assets_to_rebuild":[]}),
   "files_to_publish":changed,"current_hashes":current,"proposed_assets":proposed,"approval_required":True,"publication_performed":False}
  atomic(PREV/f"{pid}.json",doc); print(json.dumps(doc,indent=2)); return
 if not a.preview_id: raise SystemExit("--preview-id required")
 path=PREV/f"{a.preview_id}.json"; doc=json.loads(path.read_text())
 if a.action=="show": print(json.dumps(doc,indent=2)); return
 if a.action=="approve": doc["status"]="APPROVED_NOT_PUBLISHED"; doc["approved_at"]=datetime.now(timezone.utc).isoformat(); atomic(path,doc); print(json.dumps(doc,indent=2)); return
 # Discard only promotable staging; raw captures and append-only observations are separate and untouched.
 run=doc.get("run_id")
 if run and (BASE/"staging"/run).exists(): shutil.rmtree(BASE/"staging"/run)
 doc["status"]="DISCARDED"; doc["discarded_at"]=datetime.now(timezone.utc).isoformat(); doc["raw_observations_preserved"]=True; atomic(path,doc); print(json.dumps(doc,indent=2))
if __name__=="__main__": main()
