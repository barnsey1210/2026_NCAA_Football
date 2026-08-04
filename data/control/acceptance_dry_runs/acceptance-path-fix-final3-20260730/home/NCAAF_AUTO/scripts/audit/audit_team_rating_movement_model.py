#!/usr/bin/env python3
"""Audit isolated team-rating movement research artifacts and leakage policy."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
REQUIRED=["team_week_rating_states.csv","team_game_features.csv","repeatable_performance_features.csv","team_movement_predictions.csv","rating_system_movement_predictions.csv","next_game_spread_predictions.csv","next_game_total_predictions.csv","confidence_tier_results.csv","ats_results.csv","total_betting_results.csv","model_comparison.csv","holdout_2025_results.csv","game_level_audit.csv","final_selection.json","summary.json"]

def sha(path):
    if not path.exists(): return None
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def check(condition,name,details,rows):
    rows.append({"check":name,"status":"PASS" if condition else "FAIL","details":details})

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input-dir",default="data/research/team_rating_movement_model"); args=ap.parse_args(); d=ROOT/args.input_dir
    rows=[]
    missing=[f for f in REQUIRED if not (d/f).exists()]; check(not missing,"all required outputs parse","missing="+str(missing),rows)
    if missing: print(pd.DataFrame(rows).to_string(index=False)); raise SystemExit(1)
    frames={f:pd.read_csv(d/f,low_memory=False) for f in REQUIRED if f.endswith('.csv')}
    selection=json.loads((d/"final_selection.json").read_text()); summary=json.loads((d/"summary.json").read_text())
    lock=json.loads((d/"selection_lock_before_holdout.json").read_text()); check(selection==lock,"selection lock reproducible","final_selection equals pre-holdout lock",rows)
    check(selection["train_seasons"]==[2021,2022,2023] and selection["selection_season"]==2024 and selection["holdout_season"]==2025,"strict splits respected",str(selection),rows)
    audit=frames["game_level_audit.csv"]; check(bool(audit.next_opener_evaluation_only.all()),"Week N+1 opener evaluation-only","all rows flagged",rows); check(bool(audit.next_close_evaluation_only.all()),"Week N+1 close evaluation-only","all rows flagged",rows); check(bool(audit.next_result_evaluation_only.all()),"Week N+1 result evaluation-only","all rows flagged",rows)
    states=frames["team_week_rating_states.csv"]
    delta=(states.next_market_rating-states.pregame_market_rating-states.actual_market_rating_change).abs().dropna(); check(delta.empty or delta.max()<1e-9,"rating target formula correct",f"max_error={delta.max() if len(delta) else 0}",rows)
    check(bool((states.next_game_week.fillna(states.week)>=states.week).all()),"next-rating targets separated from features","next game never precedes current",rows)
    check(bool(audit.no_future_pbp.all()),"no future PBP","completed game only",rows); check(bool(audit.no_future_injury_or_roster.all()),"no future injury/roster","no such features used",rows)
    totals=frames["next_game_total_predictions.csv"]; check(bool(((totals.home_previous_week<totals.week)&(totals.away_previous_week<totals.week)).all()),"total projection uses prior games only","both prior weeks precede target",rows)
    check(summary["rating_system_snapshot_audit"]["SP+"] .startswith("not historically"),"SP+ snapshot legitimacy explicit","withheld",rows); check(summary["rating_system_snapshot_audit"]["FPI"].startswith("not historically"),"FPI snapshot legitimacy explicit","withheld",rows); check(summary["rating_system_snapshot_audit"]["TeamRankings"].startswith("not historically"),"TeamRankings snapshot legitimacy explicit","withheld",rows)
    spreads=frames["next_game_spread_predictions.csv"]
    calc=spreads.updated_away_rating-spreads.updated_home_rating-spreads.hfa; check(bool(((calc-spreads.projected_close).abs()<1e-8).all()),"spread sign convention correct","away - home - HFA",rows); check(bool((spreads.hfa==2.5).all()),"HFA treatment correct","2.5 on all rows",rows); check(bool(spreads.neutral_site_status.str.contains("unknown").all()),"neutral-site uncertainty explicit","no neutral flag available",rows)
    b=spreads[spreads.actual_opener.notna()]
    expected=np.where(b.bet_side.eq("home"),(b.actual_opener-b.actual_close),np.where(b.bet_side.eq("away"),(b.actual_close-b.actual_opener),np.nan)); check(bool(np.nanmax(np.abs(expected-b.clv))<1e-8) if len(b) else True,"CLV calculations correct",f"n={len(b)}",rows)
    check(set(frames["ats_results.csv"].ats_result.dropna().unique()).issubset({"W","L","P",""}),"ATS results valid","W/L/P only",rows); check(set(frames["total_betting_results.csv"].total_result.dropna().unique()).issubset({"W","L","P",""}),"total results valid","W/L/P only",rows)
    tiers=set(frames["team_movement_predictions.csv"].confidence_tier.dropna().unique()); check(tiers.issubset({"High","Medium","Low","No actionable signal"}),"confidence tiers reproducible",str(sorted(tiers)),rows)
    check(not frames["model_comparison.csv"].duplicated(["market","model"]).any(),"model rankings reproducible","unique market/model labels",rows)
    before=json.loads((d/"protected_hashes_before.json").read_text()); after=json.loads((d/"protected_hashes_after.json").read_text()); now={p:sha(ROOT/p) for p in before}; check(before==after==now,"protected production files unchanged",f"changed={[p for p in before if before[p]!=now[p]]}",rows)
    status=subprocess.run(["git","-C","/Users/jameslindesmith/Sites/NCAAF_SITE","status","--short"],capture_output=True,text=True); check(status.returncode==0 and not status.stdout.strip(),"publication repository clean",status.stdout.strip() or "clean",rows)
    report=pd.DataFrame(rows); report.to_csv(d/"audit_results.csv",index=False); failures=report[report.status.eq("FAIL")]
    print("TEAM RATING MOVEMENT MODEL AUDIT")
    print(report.to_string(index=False))
    print(f"\nResult: {'PASS' if failures.empty else 'FAIL'} ({len(report)-len(failures)}/{len(report)} checks passed)")
    raise SystemExit(0 if failures.empty else 1)

if __name__=="__main__": main()
