#!/usr/bin/env python3
"""Audit the isolated Saturday Shadow season-stage calibration outputs."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/research/shadow_season_stage_calibration"
REPORT = ROOT / "build/research/shadow_season_stage_calibration/index.html"
PUBLIC = Path("/Users/jameslindesmith/Sites/NCAAF_SITE")
FILES = [
    "market_movement_by_week.csv", "market_movement_by_stage.csv", "market_movement_summary.json",
    "weekly_results.csv", "model_grid_results.csv", "stage_results.csv", "holdout_2025_results.csv",
    "game_level_audit.csv", "final_selection.json", "adjustment_size_results.csv",
    "tolerance_sensitivity.csv", "signal_confidence_results.csv",
]
STAGES = {1:"Weeks 1-3",2:"Weeks 1-3",3:"Weeks 1-3",4:"Weeks 4-6",5:"Weeks 4-6",6:"Weeks 4-6",7:"Weeks 7-9",8:"Weeks 7-9",9:"Weeks 7-9",10:"Weeks 10-12",11:"Weeks 10-12",12:"Weeks 10-12"}


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()


def fail(msg):
    raise SystemExit("FAIL: "+msg)


def main():
    for name in FILES:
        path=OUT/name
        if not path.exists() or path.stat().st_size==0: fail(f"missing/empty {path}")
        if path.suffix==".csv": pd.read_csv(path,low_memory=False)
        else: json.loads(path.read_text())
    if not REPORT.exists(): fail("local HTML report missing")
    final=json.loads((OUT/"final_selection.json").read_text())
    if final["split"] != {**final["split"],"training":[2021,2022,2023],"selection":2024,"locked_holdout":2025}: fail("data split changed")
    lock=hashlib.sha256(json.dumps(final["selected_formula"],sort_keys=True).encode()).hexdigest()
    if lock!=final["split"]["selection_lock_sha256"]: fail("selection lock hash is not reproducible")
    audit=pd.read_csv(OUT/"game_level_audit.csv",low_memory=False)
    if set(audit.selection_partition.unique())!={"training","validation","locked_holdout"}: fail("partition labels incomplete")
    if (audit.max_input_week != audit.week-1).any(): fail("look-ahead cutoff violation")
    if not (audit[audit.season==2025].selection_partition=="locked_holdout").all(): fail("2025 used outside locked holdout")
    expected=audit.week.map(lambda w:STAGES.get(int(w),"Weeks 13+"))
    if not (expected==audit.stage).all(): fail("stage assignment error")
    # Reproduce applied impact and cap order for every selected game row.
    specs=final["selected_formula"]
    for market,z in audit.groupby("market"):
        spec=specs[market]
        scaled=z.raw_impact*z.coefficient
        if spec.get("cap") is None: reproduced=scaled
        elif spec.get("cap_type")=="smooth": reproduced=spec["cap"]*scaled.map(lambda x:math.tanh(x/spec["cap"]))
        else: reproduced=scaled.clip(-spec["cap"],spec["cap"])
        if (reproduced-z.applied_impact).abs().max()>1e-8: fail(f"{market} coefficient/cap application mismatch")
        if ((z.baseline+z.applied_impact-z.projected_close).abs().max()>1e-8): fail(f"{market} projected close not reproducible")
    if final["formula_audit"]["spread"]["sign"]!="negative home spread means home favored": fail("spread sign convention missing")
    if final["formula_audit"]["total"]["separate_team_impacts"] is not False: fail("fabricated total team impacts")
    if final["location_audit"]["uncertain_games"]<=0 or final["location_audit"]["resolved_neutral_games"]!=0: fail("neutral uncertainty not explicit")
    if final["protected_before"]!=final["protected_after"] or not final["protected_unchanged"]: fail("protected files changed")
    current={p:sha(ROOT/p) for p in final["protected_before"]}
    if current!=final["protected_before"]: fail("protected hashes changed after calibration")
    status=subprocess.run(["git","-C",str(PUBLIC),"status","--short"],check=True,text=True,capture_output=True).stdout.strip()
    head=subprocess.run(["git","-C",str(PUBLIC),"rev-parse","HEAD"],check=True,text=True,capture_output=True).stdout.strip()
    if status or head!=final["publication_before"]["head"]: fail("publication repository changed or dirty")
    hold=pd.read_csv(OUT/"holdout_2025_results.csv")
    if set(hold.model)!={"no_adjustment","current_benchmark","selected"} or len(hold)!=6: fail("locked holdout comparison incomplete")
    tol=pd.read_csv(OUT/"tolerance_sensitivity.csv")
    if set(tol.tolerance)!={.25,.5,1.0}: fail("movement tolerance sensitivity incomplete")
    print("PASS: shadow season-stage calibration audit")
    print(f"game audit rows={len(audit)} candidates={final['candidate_count']}")
    print(f"selected spread={json.dumps(specs['spread'],sort_keys=True)}")
    print(f"selected total={json.dumps(specs['total'],sort_keys=True)}")
    print("no-look-ahead split and selection lock verified")
    print("neutral-site uncertainty explicitly flagged")
    print("protected production files unchanged")
    print("publication repository unchanged and clean")


if __name__=="__main__":main()
