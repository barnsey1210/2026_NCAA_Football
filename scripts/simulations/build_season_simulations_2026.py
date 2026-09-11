#!/usr/bin/env python3
"""Build current 2026 season/conference simulations from the canonical runtime DB."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import argparse, json, sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import rerun_conference_sims_2026 as engine

DB_PATH = ROOT / "data/snapshots/preseason/preseason_db.json"
RESULTS_PATH = ROOT / "data/canonical/game_results_2026.json"
OUT_PATH = ROOT / "data/site/season_simulations_2026.json"
OVERRIDES_PATH = ROOT / "conference_game_overrides_2026.csv"
RATINGS_PATH = ROOT / "data/ratings/ratings_master_latest.csv"
PROJECTION_BLEND_PATH = ROOT / "data/projections/game_projection_blend_2026.csv"
SIM_FIELDS = [
    "team","conference","avg_total_wins","avg_conference_wins","bowl_eligibility_pct",
    "make_title_game_pct","conference_title_pct","lose_title_game_pct","win_distribution",
    "conference_title_ineligible","conference_title_ineligible_note",
]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--sims",type=int,default=20000); ap.add_argument("--seed",type=int,default=20260511); ap.add_argument("--sigma",type=float,default=14.0); ap.add_argument("--title-sigma",type=float,default=14.0); args=ap.parse_args()
    if not DB_PATH.exists(): raise SystemExit(f"Missing canonical DB: {DB_PATH}")
    db=deepcopy(json.loads(DB_PATH.read_text()))
    results=json.loads(RESULTS_PATH.read_text()) if RESULTS_PATH.exists() else {"games":[]}
    finals_applied=engine.apply_canonical_results(db, results.get("games",[]))
    current_inputs=engine.apply_current_simulation_inputs(db, RATINGS_PATH, PROJECTION_BLEND_PATH)
    overrides=engine.load_game_overrides(OVERRIDES_PATH); changed=engine.apply_game_overrides(db, overrides)
    db=engine.rerun_sims(db,args.sims,args.seed,args.sigma,args.title_sigma)
    teams=[{k:t.get(k) for k in SIM_FIELDS if k in t} for t in db.get("teams",[])]
    conferences=[{"conference":c.get("conference"),"num_teams":c.get("num_teams",len(c.get("teams",[]))),"average_strength":c.get("average_strength"),"championship_game":c.get("championship_game")} for c in db.get("conferences",[])]
    projection_meta=db.get("projection_model_metadata") or db.get("meta",{}).get("projection_model_metadata") or {}
    out={"schema_version":"season-simulations-2026-v1","built_at":datetime.now(timezone.utc).isoformat(),"season":2026,"trials":args.sims,"seed":args.seed,"sigma":args.sigma,"title_sigma":args.title_sigma,"source_db":"data/snapshots/preseason/preseason_db.json","results_source":"data/canonical/game_results_2026.json","ratings_source":"data/ratings/ratings_master_latest.csv","projection_source":"data/projections/game_projection_blend_2026.csv","simulation_input_rating_date":current_inputs.get("rating_date"),"current_ratings_applied":current_inputs.get("ratings_applied"),"remaining_projections_applied":current_inputs.get("remaining_projections_applied"),"completed_finals_frozen":finals_applied,"conference_game_overrides_applied":changed,"projection_model_metadata":projection_meta,"simulation_model":db.get("meta",{}).get("conference_sims_model"),"teams":teams,"conferences":conferences}
    OUT_PATH.parent.mkdir(parents=True,exist_ok=True); OUT_PATH.write_text(json.dumps(out,indent=2)+"\n")
    print(f"Wrote {OUT_PATH}"); print(f"Teams: {len(teams)}"); print(f"Conferences: {len(conferences)}"); print(f"Trials: {args.sims}"); print(f"Game override changes: {changed}")
if __name__=="__main__": main()
