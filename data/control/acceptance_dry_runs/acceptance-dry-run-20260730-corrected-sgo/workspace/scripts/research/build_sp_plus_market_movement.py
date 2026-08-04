#!/usr/bin/env python3
"""Build the provenance-gated SP+ / market-movement research package.

This builder intentionally withholds Stages 1-3 when the repository cannot prove
that an SP+ observation preceded the market observation being evaluated.  Empty
downstream artifacts are emitted with stable schemas so the stop is auditable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SP_OLD = ROOT / "data/import/sp_plus/espn_sp_plus_weekly_2021_2024.csv"
SP_OLD_JSON = ROOT / "data/import/sp_plus/espn_sp_plus_weekly_2021_2024.json"
SP_2025 = ROOT / "data/import/sp_plus/espn_sp_plus_weekly_2025.csv"
SP_2025_MANIFEST = ROOT / "data/import/sp_plus/espn_sp_plus_weekly_2025_manifest.json"
JOINED = ROOT / "data/research/prediction_tracker_close_movement_blend_with_spplus_2021_2025/joined_games.csv"
MAPPING = ROOT / "data/research/prediction_tracker_close_movement_blend_with_spplus_2021_2025/team_name_mapping.json"
PUBLIC_REPO = Path("/Users/jameslindesmith/Sites/NCAAF_SITE")
HFA = 2.5

PROTECTED = [
    "config/market_shadow_production.json",
    "scripts/site/build_saturday_shadow_lines.py",
    "scripts/site/build_postgame_shadow_updates.py",
    "scripts/site/build_market_shadow_production_layer.py",
    "scripts/research/build_team_rating_movement_model.py",
    "openers_v2.html", "schedule_v2.html",
    "build/public_site/openers.html", "build/public_site/schedule.html",
    "data/site/postgame_shadow_updates.json", "data/site/saturday_shadow_lines.json",
    "data/site/schedule_live_enrichment.json", "daily_market_update.sh",
    "scripts/publish/publish_site.sh", "data/ratings/ratings_latest.csv",
]

PROJECTION_COLS = ["season","week","game_id","date","away_team","home_team","neutral_site",
 "location_certainty","sp_plus_snapshot_date","sp_plus_snapshot_week","away_sp_plus_rating",
 "home_sp_plus_rating","away_sp_plus_offense","home_sp_plus_offense","away_sp_plus_defense",
 "home_sp_plus_defense","SP+ HFA","published_or_reconstructed","sp_plus_home_margin",
 "sp_plus_home_spread","provenance","eligibility","missing_reason"]
MARKET_COLS = ["game_id","first_opener","first_opener_timestamp","consensus_opener",
 "consensus_opener_timestamp","closing_spread","closing_timestamp","books_at_open",
 "books_at_close","opener_source","close_source","timing_status","eligibility"]
GAME_COLS = ["season","week","game_id","away_team","home_team","sp_plus_home_spread",
 "opening_home_spread","closing_home_spread","sp_plus_gap","actual_market_move",
 "distance_to_sp_plus_at_open","distance_to_sp_plus_at_close","movement_toward_sp_plus_points",
 "incorporation_percentage","directional_agreement","close_crossed_sp_plus","close_overshot_sp_plus",
 "moved_away","no_meaningful_move","actual_home_margin","sp_plus_absolute_error",
 "opener_absolute_error","close_absolute_error","sp_plus_side_ats_result","clv_points",
 "timing_status","eligibility","missing_reason"]

EMPTY_SCHEMAS = {
 "sp_plus_gap_bucket_results.csv":["split","gap_bucket","games","pct_toward","pct_away","pct_no_move","avg_toward_points","median_toward_points","avg_incorporation_pct","positive_clv_rate","avg_clv","median_clv","ats_wins","ats_losses","pushes","ats_win_rate","flat_roi","sp_plus_mae","opener_mae","close_mae"],
 "sp_plus_gap_threshold_results.csv":["split","minimum_gap","games","pct_toward","pct_away","pct_no_move","avg_toward_points","median_toward_points","avg_incorporation_pct","positive_clv_rate","avg_clv","median_clv","ats_wins","ats_losses","pushes","ats_win_rate","flat_roi","sp_plus_mae","opener_mae","close_mae"],
 "sp_plus_context_results.csv":["split","context_type","context_value","games","pct_toward","positive_clv_rate","avg_clv","ats_win_rate","roi"],
 "sp_plus_timing_results.csv":["timing_status","games","median_abs_gap","pct_toward","positive_clv_rate","avg_clv","ats_wins","ats_losses","pushes","actionability"],
 "sp_plus_result_accuracy.csv":["split","games","sp_plus_mae","opener_mae","close_mae","sp_plus_closer_than_opener_pct","sp_plus_closer_than_close_pct"],
 "sp_plus_team_week_changes.csv":["season","team","prior_snapshot_week","next_snapshot_week","prior_sp_plus","next_sp_plus","actual_sp_plus_change","eligibility","missing_reason"],
 "sp_plus_movement_predictions.csv":["season","team","week","actual_change","predicted_change","actual_direction","predicted_direction","confidence","split"],
 "sp_plus_movement_model_results.csv":["model","threshold","split","rows","direction_accuracy","balanced_accuracy","macro_f1","mae","median_ae","rmse","correlation"],
 "predicted_sp_plus_game_projections.csv":["season","week","game_id","home_team","away_team","prior_home_rating","prior_away_rating","predicted_home_change","predicted_away_change","predicted_sp_plus_home_spread","actual_updated_sp_plus_home_spread","opening_home_spread","closing_home_spread","split"],
 "sp_plus_market_alignment.csv":["season","week","game_id","sp_plus_signal","market_rating_signal","alignment_group","closing_move","clv","ats_result","split"],
 "holdout_2025_results.csv":["strategy","bets","positive_clv_rate","average_clv","median_clv","direction_accuracy","ats_win_rate","roi","max_drawdown","longest_losing_streak"],
 "model_comparison.csv":["stage","model","selection_2024_status","holdout_2025_status","primary_metric","value","recommendation"],
}

def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def protected_hashes() -> dict[str,str|None]:
    return {p: sha(ROOT / p) for p in PROTECTED}

def git_status(path: Path) -> str:
    if not path.exists(): return "repository_missing"
    run = subprocess.run(["git","-C",str(path),"status","--short"], text=True, capture_output=True)
    return run.stdout.strip() if run.returncode == 0 else f"git_error:{run.stderr.strip()}"

def norm(value: object) -> str:
    value=str(value).lower().replace("&","and")
    value=re.sub(r"\bst\.?\b","state",value); value=re.sub(r"\bn\.?\b","north",value)
    value=re.sub(r"\bs\.?\b","south",value)
    return re.sub(r"[^a-z0-9]","",value)

SP_KEY_ALIASES={"gastate":"georgiastate","louisianalafayette":"louisiana","miamiohio":"miamioh"}

def snapshot_audit() -> tuple[pd.DataFrame,dict,pd.DataFrame]:
    old=pd.read_csv(SP_OLD); new=pd.read_csv(SP_2025); all_sp=pd.concat([old,new],ignore_index=True)
    old_meta=json.loads(SP_OLD_JSON.read_text()); manifest=json.loads(SP_2025_MANIFEST.read_text())
    old_published={int(s["snapshot_week"]):s.get("published_at") for s in old_meta.get("snapshots",[]) if s.get("season")}
    records=[]
    for (season,week),z in all_sp.groupby(["season","snapshot_week"],sort=True):
        ts=str(z.source_timestamp.iloc[0]) if "source_timestamp" in z and z.source_timestamp.notna().any() else ""
        frozen=bool(season==2025 and ts and (ROOT / "data/import/sp_plus/wayback_2025/raw").exists())
        records.append({
          "season":int(season),"snapshot_week":int(week),"rows":len(z),"unique_teams":z.team.nunique(),
          "duplicate_team_rows":int(z.duplicated("team").sum()),"missing_overall":int(z.sp_plus.isna().sum()),
          "missing_offense":int(z.offense.isna().sum()),"missing_defense":int(z.defense.isna().sum()),
          "missing_special_teams":int(z.special_teams.isna().sum()),"source_url":z.source_url.iloc[0],
          "snapshot_timestamp":ts,"published_at":old_published.get(int(week),"") if season<2025 else ts,
          "historically_frozen":frozen,"state_interpretation":"postgame weekly table" if week>0 else "preseason",
          "opener_timing_verifiable":False,
          "timing_note":"Wayback-frozen, but no market opener timestamp" if frozen else "reconstructed in 2026; source publication timestamp blank",
          "eligible_for_actionable_gap_test":False,
        })
    audit=pd.DataFrame(records)
    summary={
      "generated_at":datetime.now(timezone.utc).isoformat(),
      "sources":[str(SP_OLD.relative_to(ROOT)),str(SP_OLD_JSON.relative_to(ROOT)),str(SP_2025.relative_to(ROOT)),str(SP_2025_MANIFEST.relative_to(ROOT))],
      "seasons":sorted(map(int,all_sp.season.unique())),
      "weeks_by_season":{str(int(s)):sorted(map(int,z.snapshot_week.unique())) for s,z in all_sp.groupby("season")},
      "rows":int(len(all_sp)),"duplicate_team_rows":int(all_sp.duplicated(["season","snapshot_week","team"]).sum()),
      "old_json_generated_at":old_meta.get("generated_at"),"old_snapshots_with_published_at":sum(bool(s.get("published_at")) for s in old_meta.get("snapshots",[])),
      "wayback_2025_snapshots":len(manifest),"historically_frozen_snapshot_count":int(audit.historically_frozen.sum()),
      "opener_timing_verified_snapshot_count":0,
      "published_game_projections_available":False,"projection_method":"reconstructed team-rating differential",
      "formula":"home_margin = home overall SP+ - away overall SP+ + 2.5; home_spread = -home_margin",
      "hfa":{"value":HFA,"status":"repository research convention, not independently verified as the historical ESPN SP+ game-projection HFA"},
      "neutral_site_status":"unavailable in Prediction Tracker joined source; all locations uncertain",
      "fcs_coverage":"SP+ tables contain FBS teams only",
      "stop_conditions":["2021-2024 weekly tables were reconstructed in 2026 and have blank publication timestamps","2025 snapshots are Wayback-frozen but canonical market openers have no timestamps","historical SP+ HFA cannot be independently reconstructed from published game projections"],
      "stage_1_status":"WITHHELD_NO_ACTIONABLE_TIMING","stage_2_status":"WITHHELD_BY_STAGE_1_GATE","stage_3_status":"WITHHELD_BY_STAGE_1_GATE",
    }
    return audit,summary,all_sp

def build_game_files(all_sp: pd.DataFrame) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame,dict]:
    games=pd.read_csv(JOINED,low_memory=False); mapping=json.loads(MAPPING.read_text())
    all_sp=all_sp.copy(); all_sp["key"]=all_sp.team.map(norm)
    snapshots={(int(s),int(w)):z.set_index("key").to_dict("index") for (s,w),z in all_sp.groupby(["season","snapshot_week"])}
    out=[]; market=[]; audit=[]; unmatched=set()
    for i,r in enumerate(games.itertuples(index=False)):
        season=int(r.season); week=int(r.week); sw=int(r.spplus_snapshot_week)
        hkey=SP_KEY_ALIASES.get(mapping.get(r.Home),mapping.get(r.Home)); akey=SP_KEY_ALIASES.get(mapping.get(r.Road),mapping.get(r.Road)); snap=snapshots.get((season,sw),{})
        h=snap.get(hkey); a=snap.get(akey)
        if not h: unmatched.add(str(r.Home))
        if not a: unmatched.add(str(r.Road))
        gid=f"pt-{season}-{week}-{norm(r.Road)}-{norm(r.Home)}"
        hs=-(float(r.linespplus)) if pd.notna(r.linespplus) else np.nan
        hm=-hs if pd.notna(hs) else np.nan
        reason="SP+ publication-to-opener timing cannot be proven; market opener timestamp absent"
        out.append(dict(zip(PROJECTION_COLS,[season,week,gid,"",r.Road,r.Home,"","uncertain","",sw,
          a.get("sp_plus") if a else np.nan,h.get("sp_plus") if h else np.nan,a.get("offense") if a else np.nan,
          h.get("offense") if h else np.nan,a.get("defense") if a else np.nan,h.get("defense") if h else np.nan,
          HFA,"reconstructed",hm,hs,
          f"{SP_OLD.name if season<2025 else SP_2025.name}; latest snapshot <= game week-1",False,reason])))
        opening=-float(r.lineopen) if pd.notna(r.lineopen) else np.nan
        closing=-float(r.line) if pd.notna(r.line) else np.nan
        market.append(dict(zip(MARKET_COLS,[gid,opening,"",opening,"",closing,"",np.nan,np.nan,
          "Prediction Tracker lineopen (provider/method not encoded)","Prediction Tracker line (provider/method not encoded)","timing_uncertain",False])))
        actual=-float(r.actual) if pd.notna(r.actual) else np.nan
        gap=hs-opening if pd.notna(hs) and pd.notna(opening) else np.nan
        move=closing-opening if pd.notna(closing) and pd.notna(opening) else np.nan
        dopen=abs(opening-hs) if pd.notna(gap) else np.nan; dclose=abs(closing-hs) if pd.notna(closing) and pd.notna(hs) else np.nan
        toward=dopen-dclose if pd.notna(dopen) and pd.notna(dclose) else np.nan
        inc=toward/dopen if pd.notna(toward) and dopen else np.nan
        agree=bool(np.sign(gap)==np.sign(move)) if pd.notna(gap) and pd.notna(move) and gap and move else False
        ats_margin=(-actual)-opening if pd.notna(actual) and pd.notna(opening) else np.nan
        side=np.sign(gap) if pd.notna(gap) else np.nan
        ats="P" if pd.notna(ats_margin) and ats_margin==0 else ("W" if pd.notna(ats_margin) and side*ats_margin>0 else ("L" if pd.notna(ats_margin) else ""))
        vals=[season,week,gid,r.Road,r.Home,hs,opening,closing,gap,move,dopen,dclose,toward,inc,agree,
          bool((opening-hs)*(closing-hs)<0) if pd.notna(dclose) else False,
          bool((opening-hs)*(closing-hs)<0 and dclose>0) if pd.notna(dclose) else False,
          bool(pd.notna(toward) and toward<-.25),bool(pd.notna(move) and abs(move)<.5),actual,
          abs((-hs)-actual) if pd.notna(hs) and pd.notna(actual) else np.nan,
          abs((-opening)-actual) if pd.notna(opening) and pd.notna(actual) else np.nan,
          abs((-closing)-actual) if pd.notna(closing) and pd.notna(actual) else np.nan,ats,
          side*move if pd.notna(side) and pd.notna(move) else np.nan,"timing_uncertain",False,reason]
        audit.append(dict(zip(GAME_COLS,vals)))
    return pd.DataFrame(out,columns=PROJECTION_COLS),pd.DataFrame(market,columns=MARKET_COLS),pd.DataFrame(audit,columns=GAME_COLS),{"unmatched_teams":sorted(unmatched),"mapping_rows":len(mapping)}

def html_report(summary: dict, audit: pd.DataFrame, game: pd.DataFrame) -> str:
    cov=audit.groupby("season").agg(snapshots=("snapshot_week","size"),frozen=("historically_frozen","sum"),timing_verified=("opener_timing_verifiable","sum")).reset_index()
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>SP+ Market Movement Research</title>
<style>body{{font:16px system-ui;background:#07162d;color:#eef4ff;margin:0;padding:28px}}main{{max-width:1180px;margin:auto}}.card{{background:#102746;border:1px solid #2e5680;border-radius:14px;padding:20px;margin:16px 0}}.stop{{border-color:#d79a35;background:#342810}}table{{border-collapse:collapse;width:100%}}th,td{{padding:8px;border-bottom:1px solid #36536f;text-align:left}}code{{color:#8de2bd}}h1,h2{{margin:.25em 0}}</style></head><body><main>
<h1>SP+ Gap & Market Movement Research</h1><div class="card stop"><h2>Predictive study withheld</h2><p>The required no-look-ahead timing proof failed. No threshold, feature, or model was selected and the locked 2025 holdout was not used.</p><ul>{''.join('<li>'+x+'</li>' for x in summary['stop_conditions'])}</ul></div>
<div class="card"><h2>Snapshot coverage</h2>{cov.to_html(index=False,border=0)}</div>
<div class="card"><h2>Canonical reconstruction</h2><p><code>{summary['formula']}</code></p><p>{len(game):,} game projections were reconstructed for coverage auditing; all are non-actionable because timing is uncertain.</p></div>
<div class="card"><h2>Stage status</h2><table><tr><th>Stage 1</th><td>{summary['stage_1_status']}</td></tr><tr><th>Stage 2</th><td>{summary['stage_2_status']}</td></tr><tr><th>Stage 3</th><td>{summary['stage_3_status']}</td></tr></table></div>
<div class="card"><h2>What is needed to unlock the study</h2><ol><li>Contemporaneously archived 2021–2024 weekly SP+ tables with publication timestamps.</li><li>Book-level opener snapshots with timestamps and documented first/consensus definitions.</li><li>Published historical SP+ game projections or a documented historical HFA and neutral-site field.</li></ol></div>
<div class="card"><h2>Recommendation</h2><p>No production change is justified. Preserve 2025 as locked until the timing inputs above exist.</p></div></main></body></html>'''

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--train-seasons",nargs="+",type=int,default=[2021,2022,2023]); ap.add_argument("--selection-season",type=int,default=2024); ap.add_argument("--holdout-season",type=int,default=2025); ap.add_argument("--output-dir",default="data/research/sp_plus_market_movement"); ap.add_argument("--strict",action="store_true"); args=ap.parse_args()
    out=(ROOT/args.output_dir).resolve(); build=ROOT/"build/research/sp_plus_market_movement"; out.mkdir(parents=True,exist_ok=True); build.mkdir(parents=True,exist_ok=True)
    before=protected_hashes(); public_before=git_status(PUBLIC_REPO)
    snapshots,summary,all_sp=snapshot_audit(); projections,market,games,map_audit=build_game_files(all_sp)
    snapshots.to_csv(out/"sp_plus_snapshot_audit.csv",index=False); projections.to_csv(out/"sp_plus_game_projections.csv",index=False); market.to_csv(out/"market_line_audit.csv",index=False); games.to_csv(out/"sp_plus_game_audit.csv",index=False)
    timing=pd.DataFrame([{"timing_status":"timing_uncertain","games":len(games),"median_abs_gap":float(games.sp_plus_gap.abs().median()),"pct_toward":None,"positive_clv_rate":None,"avg_clv":None,"ats_wins":None,"ats_losses":None,"pushes":None,"actionability":"descriptive_only_withheld"}])
    for name,cols in EMPTY_SCHEMAS.items():
        if name=="sp_plus_timing_results.csv": timing.to_csv(out/name,index=False)
        else: pd.DataFrame(columns=cols).to_csv(out/name,index=False)
    after=protected_hashes(); public_after=git_status(PUBLIC_REPO)
    summary.update({"split":{"training":args.train_seasons,"selection":args.selection_season,"locked_holdout":args.holdout_season},"game_projection_rows":len(projections),"actionable_game_rows":0,"market_rows":len(market),"mapping_audit":map_audit,"market_definition":{"opener":"Prediction Tracker lineopen","close":"Prediction Tracker line","timestamps":"not present","books":"not present","first_vs_consensus":"cannot distinguish"},"protected_before":before,"protected_after":after,"protected_unchanged":before==after,"publication_repo_status_before":public_before,"publication_repo_status_after":public_after,"publication_repo_clean":public_before=="" and public_after=="","recommendation":"No production change. Acquire contemporaneous frozen snapshots and timestamped book-level market history, then rerun without opening 2025 for tuning."})
    (out/"sp_plus_snapshot_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    final={"status":"WITHHELD","selected_gap_threshold":None,"selected_direction_model":None,"selected_magnitude_model":None,"holdout_2025_opened_for_selection":False,"reason":summary["stop_conditions"],"production_change_justified":False}
    (out/"final_selection.json").write_text(json.dumps(final,indent=2)+"\n"); (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    (build/"index.html").write_text(html_report(summary,snapshots,games))
    print(json.dumps({"status":final["status"],"snapshots":len(snapshots),"projection_audit_rows":len(projections),"actionable_rows":0,"stage_2":"WITHHELD","stage_3":"WITHHELD","protected_unchanged":before==after,"publication_repo_clean":summary["publication_repo_clean"],"report":str(build/"index.html")},indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
