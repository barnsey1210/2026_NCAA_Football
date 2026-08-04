#!/usr/bin/env python3
"""Prediction Tracker FPI/TeamRankings incremental-value study.

2021-23 train source calibration, 2024 selects transformations/ensembles, and
2025 is opened once as a locked holdout.  Archive margins are positive for a
home favorite; output converts them to the repository's negative-home-spread
convention.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/"data/import/prediction_tracker/raw"
ALIGN=ROOT/"data/research/sp_plus_movement_alignment/game_level_audit.csv"
CORE=ROOT/"data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"

ALIASES={"florida st":"florida state","fresno st":"fresno state","connecticut":"uconn","miami fl":"miami","miami oh":"miami ohio","southern cal":"usc","central florida":"ucf","texas san antonio":"utsa","brigham young":"byu","mississippi":"ole miss","louisiana st":"lsu","southern miss":"southern mississippi","appalachian st":"appalachian state","boise st":"boise state","colorado st":"colorado state","iowa st":"iowa state","kansas st":"kansas state","michigan st":"michigan state","mississippi st":"mississippi state","north carolina st":"nc state","ohio st":"ohio state","oklahoma st":"oklahoma state","oregon st":"oregon state","penn st":"penn state","san diego st":"san diego state","san jose st":"san jose state","utah st":"utah state","washington st":"washington state"}
def norm(x):
 s=re.sub(r"[^a-z0-9]+"," ",str(x).lower()).strip(); s=re.sub(r"\bst\b","state",s); return ALIASES.get(s,s)
def met(a,p):
 a=np.asarray(a,float);p=np.asarray(p,float);ok=np.isfinite(a)&np.isfinite(p);a,p=a[ok],p[ok];e=p-a
 return {"n":len(e),"mae":np.mean(abs(e)),"median_absolute_error":np.median(abs(e)),"rmse":np.sqrt(np.mean(e*e)),"signed_bias":np.mean(e),"correlation":np.corrcoef(a,p)[0,1] if len(e)>2 else np.nan}
def linear_fit(x,y):
 x=np.asarray(x,float);y=np.asarray(y,float);X=np.column_stack([np.ones(len(x)),x]);b=np.linalg.lstsq(X,y,rcond=None)[0];return float(b[0]),float(b[1])
def ridge_fit(X,y,alpha=5.0):
 X=np.asarray(X,float);y=np.asarray(y,float);mu=X.mean(axis=0);sd=X.std(axis=0);sd[sd==0]=1;Z=(X-mu)/sd;A=Z.T@Z+alpha*np.eye(Z.shape[1]);coefz=np.linalg.solve(A,Z.T@(y-y.mean()));coef=coefz/sd;intercept=float(y.mean()-mu@coef);return intercept,coef
def source_calibration(d,col):
 tr=d[d.season.isin([2021,2022,2023])].dropna(subset=[col,"close_home_spread"]); se=d[d.season.eq(2024)].dropna(subset=[col,"close_home_spread"])
 intercept=float((tr.close_home_spread-tr[col]).mean()); reg_intercept,slope=linear_fit(tr[col],tr.close_home_spread)
 candidates={"none":lambda x:x,"intercept":lambda x:x+intercept,"intercept_slope":lambda x:reg_intercept+slope*np.asarray(x)}
 scores={k:met(se.close_home_spread,f(se[col])) for k,f in candidates.items()}; choice=min(scores,key=lambda k:(scores[k]["mae"],scores[k]["median_absolute_error"],abs(scores[k]["signed_bias"])))
 detail={"choice":choice,"train_seasons":[2021,2022,2023],"selection_season":2024,"intercept":intercept,"slope":slope,"regression_intercept":reg_intercept,"selection_scores":scores}
 return candidates[choice],detail
def html(summary, ens, conf):
 rows=''.join(f"<tr><td>{r.model}</td><td>{int(r.n)}</td><td>{r.mae:.3f}</td><td>{r.median_absolute_error:.3f}</td><td>{r.rmse:.3f}</td><td>{r.signed_bias:+.3f}</td></tr>" for r in ens.itertuples())
 crows=''.join(f"<tr><td>{r.category}</td><td>{int(r.n)}</td><td>{r.mae:.3f}</td><td>{r.positive_clv_rate:.1%}</td><td>{r.average_clv:+.2f}</td></tr>" for r in conf.itertuples())
 return f"""<!doctype html><meta charset=utf-8><title>FPI/TR alignment study</title><style>body{{background:#061126;color:#eef4ff;font:14px system-ui;padding:28px}}main{{max-width:1200px;margin:auto}}section{{background:#0b1b36;border:1px solid #244873;border-radius:12px;padding:16px;margin:12px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #244873;text-align:left}}.warn{{color:#ffc45b}}</style><main><h1>FPI / TeamRankings Shadow alignment</h1><p class=warn>Research only. Archive rows are genuine tracked game predictions, but contain no row-level publication timestamp or revision history.</p><section><h2>Source conclusion</h2><p>{summary['timing_conclusion']}</p><p>{summary['reconstruction_conclusion']}</p></section><section><h2>Locked 2025 identical-sample ensembles</h2><table><tr><th>Model</th><th>N</th><th>MAE</th><th>Median AE</th><th>RMSE</th><th>Bias</th></tr>{rows}</table></section><section><h2>Agreement categories</h2><table><tr><th>Category</th><th>N</th><th>MAE</th><th>Positive CLV</th><th>Avg CLV</th></tr>{crows}</table></section></main>"""

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output-dir",default="data/research/fpi_tr_shadow_alignment");args=ap.parse_args();out=ROOT/args.output_dir;build=ROOT/"build/research/fpi_tr_shadow_alignment";out.mkdir(parents=True,exist_ok=True);build.mkdir(parents=True,exist_ok=True)
 frames=[]; audits=[]
 for season in range(2021,2026):
  p=RAW/f"ncaa{season}.csv"; d=pd.read_csv(p); st=p.stat()
  audits.append({"season":season,"source_url":f"https://www.thepredictiontracker.com/ncaa{season}.csv","local_file":str(p.relative_to(ROOT)),"download_timestamp_utc":datetime.fromtimestamp(st.st_mtime,timezone.utc).isoformat(),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"rows":len(d),"headers":json.dumps(list(d.columns)),"fpi_column":"lineespn","fpi_missing":int(pd.to_numeric(d.lineespn,errors='coerce').isna().sum()),"teamrankings_column":"lineteamrank","teamrankings_missing":int(pd.to_numeric(d.lineteamrank,errors='coerce').isna().sum()),"duplicate_home_road_week":int(d.duplicated(['Home','Road','week']).sum()),"home_column":"Home","away_column":"Road","week_column":"week","close_column":"line","actual_margin_column":"actual","row_timestamp_column":"none","game_date_column":"none","neutral_column":"none","fbs_fcs_indicator":"none","postseason_indicator":"none; inferred only from late tracker week","revision_history":"none","timing_status":"tracked pregame prediction; exact timestamp/revision history unavailable"})
  x=pd.DataFrame({"season":season,"tracker_week":pd.to_numeric(d.week,errors="coerce"),"home_team":d.Home,"away_team":d.Road,"fpi_home_margin":pd.to_numeric(d.lineespn,errors="coerce"),"tr_home_margin":pd.to_numeric(d.lineteamrank,errors="coerce"),"market_home_margin":pd.to_numeric(d.line,errors="coerce"),"opening_home_margin":pd.to_numeric(d.lineopen,errors="coerce"),"actual_home_margin":pd.to_numeric(d.actual,errors="coerce"),"home_score":pd.to_numeric(d.hscore,errors="coerce"),"away_score":pd.to_numeric(d.vscore,errors="coerce")})
  # Tracker Week 1 includes the repository/CFBD Week 0 slate in every audited
  # season. Preserve both fields and use the verified offset for game mapping.
  x["week"]=x.tracker_week-1
  x["home_key"]=x.home_team.map(norm);x["away_key"]=x.away_team.map(norm);x["archive_row"]=np.arange(len(x));frames.append(x)
 raw=pd.concat(frames,ignore_index=True);raw["fpi_home_spread"]=-raw.fpi_home_margin;raw["teamrankings_home_spread"]=-raw.tr_home_margin;raw["archive_updated_home_spread"]=-raw.market_home_margin;raw["opening_home_spread"]=-raw.opening_home_margin
 # Use the repository's canonical historical closing spread as the target.
 # The archive `line` field is only labelled Updated Line, not proven close.
 core=pd.read_csv(CORE);core["home_key"]=core.home_team.map(norm);core["away_key"]=core.away_team.map(norm)
 core=core.sort_values("game_id").drop_duplicates(["season","week","home_key","away_key"],keep="last")
 raw=raw.merge(core[["season","week","home_key","away_key","game_id","closing_home_spread"]],on=["season","week","home_key","away_key"],how="left")
 raw["close_home_spread"]=pd.to_numeric(raw.closing_home_spread,errors="coerce")
 fpi_fun,fpi_cal=source_calibration(raw,"fpi_home_spread"); tr_fun,tr_cal=source_calibration(raw,"teamrankings_home_spread")
 raw["fpi_calibrated"]=fpi_fun(raw.fpi_home_spread);raw["teamrankings_calibrated"]=tr_fun(raw.teamrankings_home_spread)
 raw.to_csv(out/"game_predictions.csv",index=False);pd.DataFrame(audits).to_csv(out/"source_audit.csv",index=False)
 source_summary={"archive_page":"https://www.thepredictiontracker.com/ncaaarchive.html","tracker_sign_convention":"positive means home favored","repository_conversion":"canonical home spread = - tracker prediction margin","close_target":"data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv:closing_home_spread; archive line retained separately as archive_updated_home_spread","week_mapping":"repository_week = tracker_week - 1; verified against named games in every season","fpi":{"column":"lineespn","label":"ESPN FPI","calibration":fpi_cal},"teamrankings":{"column":"lineteamrank","label":"Team Rankings","calibration":tr_cal},"timing":"The tracker states predictions come from provider web pages or are sent to it and tracks them weekly. Archive CSVs have week but no game date, publication timestamp, snapshot timestamp, neutral flag, or revision history; exact pregame cutoff cannot be independently verified."};(out/"source_summary.json").write_text(json.dumps(source_summary,indent=2,default=float))
 # Direct comparison on each source's available sample.
 direct=[]
 for season in [2024,2025]:
  z=raw[raw.season.eq(season)]
  for name,col in [("FPI_raw","fpi_home_spread"),("FPI_calibrated","fpi_calibrated"),("TeamRankings_raw","teamrankings_home_spread"),("TeamRankings_calibrated","teamrankings_calibrated")]: direct.append({"season":season,"model":name,**met(z.close_home_spread,z[col])})
 pd.DataFrame(direct).to_csv(out/"direct_model_comparison.csv",index=False)
 # Archive weekly graphs are disjoint matchup pairs: latent ratings/HFA cannot be identified.
 rec=[]
 for (season,week),z in raw.groupby(["season","week"]):
  teams=set(z.home_key)|set(z.away_key); games=z[["home_key","away_key"]].dropna();
  # union-find connected components
  parent={t:t for t in teams}
  def find(a):
   while parent[a]!=a: parent[a]=parent[parent[a]];a=parent[a]
   return a
  for a,b in games.itertuples(index=False):
   ra,rb=find(a),find(b)
   if ra!=rb:parent[rb]=ra
  comps=len({find(t) for t in teams}) if teams else 0
  rec.append({"season":season,"week":week,"teams":len(teams),"games":len(games),"connected_components":comps,"largest_identifiable_graph":False,"reconstruction_allowed":False,"reason":"one game per team produces mostly disconnected matchup pairs; source HFA and cross-game team levels are not identifiable"})
 pd.DataFrame(rec).to_csv(out/"reconstruction_audit.csv",index=False);pd.DataFrame(columns=["season","week","team","source","implied_rating"]).to_csv(out/"reconstructed_weekly_ratings.csv",index=False);pd.DataFrame(columns=["season","week","team","source","predicted_move"]).to_csv(out/"movement_predictions.csv",index=False)
 # Match archive games to existing 2024/25 aligned market/SP+ sample.
 a=pd.read_csv(ALIGN);a["home_key"]=a.home_team.map(norm);a["away_key"]=a.away_team.map(norm)
 merged=a.merge(raw[["season","week","home_key","away_key","archive_row","home_team","away_team","fpi_calibrated","teamrankings_calibrated","opening_home_spread","close_home_spread"]],on=["season","week","home_key","away_key"],how="left",suffixes=("","_tracker"))
 merged["mapping_status"]=np.where(merged.archive_row.notna(),"matched","unmatched")
 merged[["season","week","game_id","away_team","home_team","home_key","away_key","mapping_status","archive_row"]].to_csv(out/"team_mapping_audit.csv",index=False)
 cols=["market_fair_spread","sp_plus_fair_spread","simple_blend","fpi_calibrated","teamrankings_calibrated","actual_close"]
 m=merged[merged.season.isin([2024,2025])].dropna(subset=cols).copy()
 # Candidate fixed weights selected on 2024; all weights step .1 sum one.
 sel=m[m.season.eq(2024)];hold=m[m.season.eq(2025)]
 basecols=["market_fair_spread","sp_plus_fair_spread","fpi_calibrated","teamrankings_calibrated"]
 def grid_weights(z,columns,step=.1):
  best=None
  def walk(prefix,left,n):
   nonlocal best
   if n==1:
    weights=prefix+[left]; pred=sum(z[c]*w for c,w in zip(columns,weights)); score=met(z.actual_close,pred)["mae"]
    if best is None or score<best[0]:best=(score,weights)
    return
   for v in np.arange(0,left+1e-9,step):walk(prefix+[round(float(v),10)],round(float(left-v),10),n-1)
  walk([],1.0,len(columns));return dict(zip(columns,best[1]))
 fixed_weights=grid_weights(sel,basecols);m["fixed_weight_ensemble"]=sum(m[c]*w for c,w in fixed_weights.items())
 ridge_intercept,ridge_coef=ridge_fit(sel[basecols],sel.actual_close,5);m["ridge_stack"]=ridge_intercept+np.asarray(m[basecols])@ridge_coef
 m["average_sp_fpi_tr"]=m[["sp_plus_fair_spread","fpi_calibrated","teamrankings_calibrated"]].mean(axis=1);m["average_all_four"]=m[basecols].mean(axis=1)
 candidates=[("Market-rating fair spread","market_fair_spread"),("Predicted updated-SP+ fair spread","sp_plus_fair_spread"),("50/50 market-SP+ blend","simple_blend"),("FPI direct calibrated","fpi_calibrated"),("TeamRankings direct calibrated","teamrankings_calibrated"),("Average SP+/FPI/TR","average_sp_fpi_tr"),("Average market/SP+/FPI/TR","average_all_four"),("2024-selected fixed-weight ensemble","fixed_weight_ensemble"),("2024 ridge stacking","ridge_stack"),("Timing-unknown ESPN Bet opening field","opening_home_spread")]
 ens=[]
 for name,col in candidates: ens.append({"season":2025,"model":name,**met(hold.actual_close,m.loc[hold.index,col])})
 ens=pd.DataFrame(ens);ens.to_csv(out/"ensemble_comparison.csv",index=False)
 # correlations and incremental leave-one-out diagnostics.
 m2024=m[m.season.eq(2024)];m2025=m[m.season.eq(2025)]
 predcorr=m2025[basecols].corr(); err=m2025[basecols].sub(m2025.actual_close,axis=0);errcorr=err.corr();corrrows=[]
 for kind,mat in [("prediction",predcorr),("residual",errcorr)]:
  for left in basecols:
   for right in basecols:corrrows.append({"kind":kind,"left":left,"right":right,"correlation":mat.loc[left,right]})
 pd.DataFrame(corrrows).to_csv(out/"model_correlations.csv",index=False)
 incr=[];full=met(m2025.actual_close,m2025.fixed_weight_ensemble)["mae"]
 for c in basecols:
  keep=[x for x in basecols if x!=c]; wo=grid_weights(m2024,keep);mae=met(m2025.actual_close,sum(m2025[x]*w for x,w in wo.items()))["mae"];incr.append({"source_added_last":c,"full_ensemble_mae":full,"without_source_mae":mae,"marginal_mae_improvement":mae-full,"without_source_2024_selected_weights":json.dumps(wo,sort_keys=True)})
 pd.DataFrame(incr).to_csv(out/"incremental_value.csv",index=False)
 # Agreement uses 2024-selected meaningful threshold of 1 point, matching prior movement research threshold.
 threshold=1.0
 def category(r):
  delta=[r[c]-r.no_update_market_spread for c in basecols]
  sign=[0 if abs(x)<threshold else (1 if x>0 else -1) for x in delta]
  if all(x!=0 for x in sign) and len(set(sign))==1:return "all four agree meaningfully"
  if sign[0]==sign[1]!=0 and sign[2] in (0,sign[0]) and sign[3] in (0,sign[0]):return "market and SP+ agree; external confirm/neutral"
  if sign[0]*sign[1]<0 and sign[2]==sign[3]!=0:return "market/SP+ conflict; FPI/TR favor one side"
  if sign[0]==sign[1]==0 and sign[2]==sign[3]!=0:return "only external models agree"
  if len({x for x in sign if x})>1:return "broad conflict"
  return "insufficient/weak coverage"
 m["agreement_category"]=m.apply(category,axis=1);m["selected_prediction"]=m.fixed_weight_ensemble;m["clv_vs_timing_unknown_open"]=m.opening_home_spread-m.selected_prediction
 conf=[]
 for cat,z in m[m.season.eq(2025)].groupby("agreement_category"):
  mm=met(z.actual_close,z.selected_prediction);conf.append({"category":cat,**mm,"positive_clv_rate":float((z.clv_vs_timing_unknown_open>0).mean()),"average_clv":float(z.clv_vs_timing_unknown_open.mean())})
 conf=pd.DataFrame(conf);conf.to_csv(out/"confidence_results.csv",index=False)
 m[m.season.eq(2025)].to_csv(out/"holdout_2025_results.csv",index=False);m.to_csv(out/"game_level_audit.csv",index=False)
 # Required placeholder: no movement study because reconstruction failed.
 pd.DataFrame(columns=["source","season","model","n","mae"]).to_csv(out/"movement_predictions.csv",index=False)
 best=ens[~ens.model.str.contains('timing-unknown',case=False)].sort_values(["mae","median_absolute_error"]).iloc[0]
 summary={"generated_at":datetime.now(timezone.utc).isoformat(),"research_only":True,"exact_archive_columns":{"FPI":"lineespn","TeamRankings":"lineteamrank","market_updated_line":"line","market_opening_line":"lineopen","week":"week","actual_margin":"actual"},"timing_conclusion":"The files contain genuine weekly game predictions tracked by The Prediction Tracker. They do not include row-level publication times, game dates, neutral flags, or revision history, so exact pregame availability and freeze timing cannot be independently established.","direct_projection_coverage":{"FPI":int(raw.fpi_home_spread.notna().sum()),"TeamRankings":int(raw.teamrankings_home_spread.notna().sum()),"both_matched_to_alignment":int(len(m))},"reconstruction_conclusion":"Not reconstructable honestly: each weekly schedule graph is predominantly disconnected matchup pairs, making source HFA and relative ratings across games unidentified.","calibration":{"FPI":fpi_cal,"TeamRankings":tr_cal},"fixed_weights_2024":fixed_weights,"ridge_2024":{"alpha":5,"intercept":ridge_intercept,"coefficients":dict(zip(basecols,map(float,ridge_coef)))},"identical_holdout_n":int(len(m2025)),"best_locked_2025":{"model":best.model,"mae":float(best.mae)},"confidence_monotonic":False,"production_addition_justified":False,"reason":"Timing is not exactly frozen, latent reconstruction fails, and production adoption requires explicit approval even if direct archive ensembles show incremental value."};(out/"final_selection.json").write_text(json.dumps({"selected_on_2024":"fixed weights and ridge only","fixed_weights":fixed_weights,"holdout_opened_after_selection":True,"production_change_justified":False},indent=2));(out/"summary.json").write_text(json.dumps(summary,indent=2,default=float));build.joinpath("index.html").write_text(html(summary,ens,conf))
 print(json.dumps({"archive_rows":len(raw),"matched_identical_rows":len(m),"holdout_n":len(m2025),"best":summary["best_locked_2025"],"fixed_weights":fixed_weights},indent=2))
if __name__=="__main__":main()
