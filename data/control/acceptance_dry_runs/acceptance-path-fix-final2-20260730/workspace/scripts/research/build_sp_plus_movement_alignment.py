#!/usr/bin/env python3
"""Research-only SP+ weekly movement and market-alignment study."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]; HFA=2.5
SP=[ROOT/'data/import/sp_plus/espn_sp_plus_weekly_2021_2024.csv',ROOT/'data/import/sp_plus/espn_sp_plus_weekly_2025.csv']
MOV=ROOT/'data/research/team_rating_movement_model'; CORE=ROOT/'data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv'
PUB=Path('/Users/jameslindesmith/Sites/NCAAF_SITE')
PROTECTED=['config/market_shadow_production.json','scripts/site/build_saturday_shadow_lines.py','scripts/site/build_postgame_shadow_updates.py','scripts/site/build_market_shadow_production_layer.py','scripts/research/build_team_rating_movement_model.py','openers_v2.html','schedule_v2.html','build/public_site/openers.html','build/public_site/schedule.html','data/site/postgame_shadow_updates.json','data/site/saturday_shadow_lines.json','data/site/schedule_live_enrichment.json','daily_market_update.sh','scripts/publish/publish_site.sh','data/ratings/ratings_latest.csv','data/projections/game_projections_2026.csv']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def hashes(): return {x:sha(ROOT/x) for x in PROTECTED}
def pubstat():
 r=subprocess.run(['git','-C',str(PUB),'status','--short'],capture_output=True,text=True); return r.stdout.strip() if r.returncode==0 else 'git_error'
def norm(x):
 s=re.sub(r'^\s*\d+\.\s*','',str(x or '')).lower().replace('&','and')
 s=re.sub(r'\bst\.?\b','state',s); s=re.sub(r'\bn\.?\b','north',s); s=re.sub(r'\bs\.?\b','south',s)
 return re.sub(r'[^a-z0-9]','',s)
def gid(x):
 s=str(x); return s[:-2] if s.endswith('.0') else s
def load_mod():
 p=ROOT/'scripts/research/build_team_rating_movement_model.py'; spec=importlib.util.spec_from_file_location('movement',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def metric(y,p):
 y=np.asarray(y,float); p=np.asarray(p,float); ok=np.isfinite(y)&np.isfinite(p); y=y[ok]; p=p[ok]; e=p-y
 return {'n':len(y),'mae':np.mean(abs(e)),'median_absolute_error':np.median(abs(e)),'rmse':np.sqrt(np.mean(e*e)),'signed_bias':np.mean(e),'correlation':np.corrcoef(y,p)[0,1] if len(y)>2 and np.std(y)*np.std(p)>0 else np.nan,'overshoot_rate':np.mean(abs(p)>abs(y)),'undershoot_rate':np.mean(abs(p)<abs(y))}
def roi(rs):
 v=[100/110 if x=='W' else -1 if x=='L' else 0 for x in rs]; return np.mean(v) if v else np.nan
def result(line,margin):
 if not np.isfinite(line) or not np.isfinite(margin): return ''
 x=margin+line; return 'W' if x>0 else 'L' if x<0 else 'P'

def targets_and_features(train):
 sp=pd.concat([pd.read_csv(x) for x in SP],ignore_index=True); sp['team_raw']=sp.team; sp['key']=sp.team.map(norm)
 feat=pd.read_csv(MOV/'repeatable_performance_features.csv',low_memory=False); feat['game_id']=feat.game_id.map(gid); feat['key']=feat.team.map(norm)
 # Canonicalize SP keys through the actual feature-team universe; explicit aliases only.
 fmap={norm(t):t for t in feat.team.dropna().unique()}; aliases={'gastate':'georgiastate','louisianalafayette':'louisiana','miamiohio':'miamioh'}
 rows=[]
 for (season,key),z in sp.sort_values('snapshot_week').groupby(['season','key']):
  zz=z.drop_duplicates('snapshot_week').sort_values('snapshot_week')
  for a,b in zip(zz.iloc[:-1].itertuples(),zz.iloc[1:].itertuples()):
   consecutive=int(b.snapshot_week)==int(a.snapshot_week)+1; ck=aliases.get(key,key); team=fmap.get(ck)
   game=feat[(feat.season==season)&(feat.week==int(b.snapshot_week))&(feat.key==ck)].sort_values(['game_date','game_id']).tail(1)
   g=game.iloc[0] if len(game) else None; eligible=bool(consecutive and team and g is not None)
   missing='' if eligible else 'nonconsecutive snapshots' if not consecutive else 'unmatched team name' if not team else 'no completed game in target week (bye or missing feature row)'
   def val(o,c): return getattr(o,c,np.nan)
   rows.append({'season':int(season),'completed_week':int(b.snapshot_week),'target_sp_plus_week':int(b.snapshot_week),'current_snapshot_week':int(a.snapshot_week),'team':team or str(b.team),'current_sp_plus_overall':val(a,'sp_plus'),'next_sp_plus_overall':val(b,'sp_plus'),'actual_sp_plus_change':val(b,'sp_plus')-val(a,'sp_plus'),'current_sp_plus_offense':val(a,'offense'),'next_sp_plus_offense':val(b,'offense'),'actual_sp_plus_offense_change':val(b,'offense')-val(a,'offense'),'current_sp_plus_defense':val(a,'defense'),'next_sp_plus_defense':val(b,'defense'),'actual_sp_plus_defense_change':val(b,'defense')-val(a,'defense'),'current_sp_plus_special_teams':val(a,'special_teams'),'next_sp_plus_special_teams':val(b,'special_teams'),'actual_sp_plus_special_teams_change':val(b,'special_teams')-val(a,'special_teams'),'completed_game_id':g.game_id if g is not None else '','opponent':g.opponent if g is not None else '','game_date':g.game_date if g is not None else '','games_played':g.games_played_after if g is not None else np.nan,'snapshot_provenance':f'{SP[0].relative_to(ROOT) if season<2025 else SP[1].relative_to(ROOT)}; genuine W{int(a.snapshot_week)} to W{int(b.snapshot_week)} observation','sequence_validity':'adjacent_calendar_week' if consecutive else 'invalid_gap_not_bridged','eligibility':eligible,'missing_reason':missing,'join_key':ck})
 t=pd.DataFrame(rows); e=t[t.eligibility].copy()
 f=e.merge(feat,left_on=['season','completed_week','completed_game_id','join_key'],right_on=['season','week','game_id','key'],how='left',suffixes=('','_game'),validate='one_to_one')
 # Opponent SP+ is the prior snapshot, therefore known before the completed game.
 prior={(int(r.season),int(r.snapshot_week),r.key):r.sp_plus for r in sp.itertuples()}
 f['opponent_sp_plus_rating']=[prior.get((int(r.season),int(r.current_snapshot_week),norm(r.opponent)),np.nan) for r in f.itertuples()]
 market=pd.read_csv(MOV/'team_movement_predictions.csv',low_memory=False); market['game_id']=market.game_id.map(gid); market['key']=market.team.map(norm)
 keep=['season','week','game_id','key','predicted_movement','prob_down','prob_no_change','prob_up','predicted_direction','split']
 market=market[keep].rename(columns={c:f'market_{c}' for c in ['prob_down','prob_no_change','prob_up','predicted_direction','split']})
 f=f.merge(market,on=['season','week','game_id','key'],how='left',validate='one_to_one')
 f['feature_cutoff']='completed game final/PBP/drive data; before next genuine weekly SP+ observation'; f['prediction_oos']=False
 return t,f,sp

def fit_and_predict(f,m,train,sel,hold):
 base=json.loads((MOV/'final_selection.json').read_text())['features']; features=[x for x in base if x in f.columns]+['current_sp_plus_overall','opponent_sp_plus_rating','games_played','completed_week']
 d=f.copy(); d['actual_market_rating_change_original']=d.actual_market_rating_change; d['actual_market_rating_change']=d.actual_sp_plus_change
 best,grid=m.select_model(d,features,train,sel); threshold=float(best['threshold'])
 outs=[]
 for season in train+[sel,hold]:
  fit=[x for x in train if x!=season] if season in train else train if season==sel else train+[sel]
  model=m.fit_models(d,features,threshold,fit); z=d[d.season==season].copy(); p=m.predict_models(z,model)
  for k,v in p.items(): z[k]=v
  fam=best['direction_model']
  if fam=='ordinal_ridge_proxy': z['predicted_direction']=m.movement_class(z.ridge,threshold); probs=m.movement_probs_from_score(z.ridge,threshold)
  elif fam=='rules_based': z['predicted_direction']=m.movement_class(z.rules_repeatable_spread,threshold); probs=m.movement_probs_from_score(z.rules_repeatable_spread,threshold)
  elif fam=='gradient_boosted_stumps': z['predicted_direction']=m.movement_class(z.boosted_challenger,threshold); probs=m.movement_probs_from_score(z.boosted_challenger,threshold)
  else: probs=np.c_[z.prob_down,z.prob_no_change,z.prob_up]
  z[['prob_down','prob_no_change','prob_up']]=probs; z['predicted_sp_plus_change']=z[str(best['magnitude_model'])]; z['actual_sp_plus_direction']=m.movement_class(z.actual_sp_plus_change,threshold); z['prediction_oos']=True; z['fit_seasons']=','.join(map(str,fit)); z['split']='train_crossfit' if season in train else 'selection' if season==sel else 'locked_holdout'; outs.append(z)
 p=pd.concat(outs,ignore_index=True); p['actual_market_rating_change']=p.actual_market_rating_change_original
 return p,best,grid,features

def baseline_table(p,m,hold,threshold):
 h=p[p.season==hold].copy(); fit=p[p.season.isin([2021,2022,2023,2024])].copy(); rows=[]
 candidates={'no_change':np.zeros(len(h)),'market_movement_proxy':h.predicted_movement,'selected_SP_plus':h.predicted_sp_plus_change,'gradient_boosted':h.boosted_challenger}
 for name,col in [('raw_ATS','raw_ats_performance'),('raw_PBP','raw_pbp_performance'),('repeatable_performance','repeatable_spread_performance')]:
  ok=fit[col].notna()&fit.actual_sp_plus_change.notna(); x=fit.loc[ok,col].to_numpy(float); y=fit.loc[ok,'actual_sp_plus_change'].to_numpy(float); beta=np.linalg.solve(np.array([[len(x),x.sum()],[x.sum(),(x*x).sum()+1e-6]]),np.array([y.sum(),(x*y).sum()])); candidates[name]=beta[0]+beta[1]*h[col]
 for name,x in candidates.items():
  ok=np.isfinite(h.actual_sp_plus_change.to_numpy(float))&np.isfinite(np.asarray(x,float)); q=metric(h.actual_sp_plus_change,x); cm=m.class_metrics(m.movement_class(h.actual_sp_plus_change.to_numpy(float)[ok],threshold),m.movement_class(np.asarray(x,float)[ok],threshold)); rows.append({'scope':'locked_2025','model':name,**q,'direction_accuracy':cm['accuracy'],'balanced_accuracy':cm['balanced_accuracy'],'macro_f1':cm['macro_f1']})
 return pd.DataFrame(rows)

def alignment(p,m,threshold):
 q=p[p.season.isin([2024,2025])].copy(); mt=.75
 q['predicted_market_direction']=np.where(q.predicted_movement.notna(),m.movement_class(q.predicted_movement.fillna(0),mt),np.nan); q['predicted_sp_plus_direction']=m.movement_class(q.predicted_sp_plus_change,threshold); q['actual_market_direction']=np.where(q.actual_market_rating_change.notna(),m.movement_class(q.actual_market_rating_change.fillna(0),mt),np.nan); q['actual_sp_plus_direction']=m.movement_class(q.actual_sp_plus_change,threshold)
 def cat(r):
  a,b=r.predicted_market_direction,r.predicted_sp_plus_direction
  if pd.isna(a) or pd.isna(b): return 'Missing one model'
  if a==b==1:return 'Both predict upgrade'
  if a==b==-1:return 'Both predict downgrade'
  if a==b==0:return 'Both predict no meaningful change'
  if a==b:return 'Same direction, different magnitude'
  if a!=0 and b==0:return 'Market only meaningful'
  if a==0 and b!=0:return 'SP+ only meaningful'
  return 'Opposite directions'
 q['alignment_category']=q.apply(cat,axis=1); q['direction_agreement']=q.predicted_market_direction==q.predicted_sp_plus_direction; q['signed_magnitude_agreement']=np.sign(q.predicted_movement)==np.sign(q.predicted_sp_plus_change); q['absolute_magnitude_difference']=(q.predicted_movement-q.predicted_sp_plus_change).abs(); q['consensus_movement_estimate']=(q.predicted_movement+q.predicted_sp_plus_change)/2; q['consensus_confidence_score']=np.where(q.direction_agreement,(q[['prob_up','prob_down']].max(axis=1)+.5*np.exp(-q.absolute_magnitude_difference))/1.5,.2*np.exp(-q.absolute_magnitude_difference)); return q

def fairs(a,core,nextpred,sel,hold):
 core=core.copy(); core['game_id']=core.game_id.map(gid); n=nextpred.copy(); n['game_id']=n.game_id.map(gid)
 # Latest completed-game prediction feeding each next game, paired home/away.
 x=a[a.next_game_id.notna() & a.prediction_oos].copy(); x['next_game_id']=x.next_game_id.map(gid)
 rows=[]
 for ng,z in x.groupby(['season','next_game_id']):
  season,game=ng; g=core[(core.season==season)&(core.game_id==game)]
  if g.empty: continue
  g=g.iloc[0]; hz=z[z.team==g.home_team].tail(1); az=z[z.team==g.away_team].tail(1)
  if hz.empty or az.empty: continue
  h,a1=hz.iloc[0],az.iloc[0]
  market=(a1.pregame_market_rating+a1.predicted_movement)-(h.pregame_market_rating+h.predicted_movement)-HFA
  spfair=(a1.current_sp_plus_overall+a1.predicted_sp_plus_change)-(h.current_sp_plus_overall+h.predicted_sp_plus_change)-HFA
  nomove=a1.pregame_market_rating-h.pregame_market_rating-HFA
  old=n[(n.season==season)&(n.game_id==game)]; lam=old.current_lambda_050_projection.iloc[0] if len(old) else np.nan
  rows.append({'game_id':game,'season':int(season),'week':int(g.week),'away_team':g.away_team,'home_team':g.home_team,'frozen_away_market_rating':a1.pregame_market_rating,'frozen_home_market_rating':h.pregame_market_rating,'predicted_away_market_move':a1.predicted_movement,'predicted_home_market_move':h.predicted_movement,'market_fair_spread':market,'current_away_sp_plus':a1.current_sp_plus_overall,'current_home_sp_plus':h.current_sp_plus_overall,'predicted_away_sp_plus_move':a1.predicted_sp_plus_change,'predicted_home_sp_plus_move':h.predicted_sp_plus_change,'sp_plus_fair_spread':spfair,'no_update_market_spread':nomove,'current_lambda_050_spread':lam,'simple_blend':(market+spfair)/2,'historical_espn_bet_opening_field':g.opening_home_spread,'actual_close':g.closing_home_spread,'actual_result':g.home_score-g.away_score,'timing_limitation_flag':'TIMING-UNKNOWN ESPN BET OPENING-FIELD DIAGNOSTIC; not proven Saturday DK/FD','neutral_site_uncertainty':'historical source lacks validated neutral-site treatment','market_history_source':str(CORE.relative_to(ROOT))})
 d=pd.DataFrame(rows); d['market_net_move']=d.predicted_away_market_move-d.predicted_home_market_move; d['sp_plus_net_move']=d.predicted_away_sp_plus_move-d.predicted_home_sp_plus_move
 md=np.where(d.market_net_move.abs()>=.75,np.sign(d.market_net_move),0); sd=np.where(d.sp_plus_net_move.abs()>=1.0,np.sign(d.sp_plus_net_move),0)
 d['alignment_category']=np.where((md==sd)&(md!=0),'Same meaningful direction',np.where((md*sd)<0,'Opposite directions',np.where((md==sd)&(md==0),'Both no meaningful change',np.where(md==0,'SP+ only meaningful','Market only meaningful'))))
 d['confidence_tier']=np.where((md==sd)&(md!=0),'Strong agreement',np.where((md*sd)<0,'Conflict',np.where((md==sd)&(md==0),'No meaningful change','Moderate agreement')))
 # 2024-only blend choice.
 candidates={'simple_average':'simple_blend','market_when_conflict':'market_fair_spread','sp_plus_when_conflict':'sp_plus_fair_spread','suppress_conflict':'no_update_market_spread'}
 scores={k:float((d.loc[d.season==sel,c]-d.loc[d.season==sel,'actual_close']).abs().mean()) for k,c in candidates.items()}; choice=min(scores,key=scores.get); d['aligned_fair_spread']=d[candidates[choice]]; d['confidence']=1/(1+(d.market_fair_spread-d.sp_plus_fair_spread).abs()); return d,choice,scores

def fair_eval(d,sel,hold):
 rows=[]
 models={'no_update':'no_update_market_spread','current_lambda_0.50':'current_lambda_050_spread','market_movement':'market_fair_spread','SP_plus_movement':'sp_plus_fair_spread','aligned_blend':'aligned_fair_spread','historical_ESPN_Bet_opening_field':'historical_espn_bet_opening_field'}
 for season in [sel,hold]:
  for name,c in models.items():
   z=d[(d.season==season)&d[c].notna()&d.actual_close.notna()].copy(); e=z[c]-z.actual_close
   rows.append({'season':season,'model':name,'n':len(z),'mae_vs_close':abs(e).mean(),'median_absolute_error':abs(e).median(),'rmse':np.sqrt(np.mean(e*e)),'signed_bias':e.mean(),'correlation':z[c].corr(z.actual_close)})
 return pd.DataFrame(rows)

def diagnostics(d,hold):
 z=d[d.season==hold].copy(); rows=[]
 for name,c in {'market_movement':'market_fair_spread','SP_plus_movement':'sp_plus_fair_spread','aligned_blend':'aligned_fair_spread'}.items():
  b=z[z.historical_espn_bet_opening_field.notna()&z[c].notna()].copy(); b['side']=np.where(b[c]<b.historical_espn_bet_opening_field,'home','away'); b['clv']=np.where(b.side=='home',b.historical_espn_bet_opening_field-b.actual_close,b.actual_close-b.historical_espn_bet_opening_field); b['line']=np.where(b.side=='home',b.historical_espn_bet_opening_field,-b.historical_espn_bet_opening_field); b['margin']=np.where(b.side=='home',b.actual_result,-b.actual_result); b['ats']=[result(x,y) for x,y in zip(b.line,b.margin)]; rows.append({'model':name,'n':len(b),'positive_clv_rate':(b.clv>0).mean(),'average_clv':b.clv.mean(),'median_clv':b.clv.median(),'ats_win_rate':(b.ats=='W').sum()/max(b.ats.isin(['W','L']).sum(),1),'roi_at_minus_110':roi(b.ats),'label':'TIMING-UNKNOWN ESPN BET OPENING-FIELD DIAGNOSTIC'})
 return pd.DataFrame(rows)

def html(summary,comp,fair,align):
 return f'''<!doctype html><meta charset="utf-8"><title>SP+ Movement Alignment</title><style>body{{font:15px system-ui;background:#07162d;color:#eef4ff;margin:24px}}main{{max-width:1400px;margin:auto}}.card{{background:#102746;border:1px solid #31547c;border-radius:12px;padding:18px;margin:16px 0}}table{{border-collapse:collapse;width:100%;font-size:12px}}th,td{{padding:6px;border-bottom:1px solid #29496d;text-align:right}}th:first-child,td:first-child{{text-align:left}}.warn{{color:#ffc667}}</style><main><h1>SP+ Weekly Movement & Market Alignment</h1><div class="card"><b>Research only.</b> 2021–23 train; 2024 selection; locked 2025 holdout.</div><div class="card"><h2>Target coverage</h2>{pd.DataFrame(summary['team_week_sample_by_season']).to_html(index=False)}</div><div class="card"><h2>Selected model</h2><pre>{json.dumps(summary['selection'],indent=2)}</pre></div><div class="card"><h2>Locked 2025 baselines</h2>{comp.to_html(index=False)}</div><div class="card"><h2>Alignment</h2>{align.to_html(index=False)}</div><div class="card"><h2>Fair spreads</h2>{fair.to_html(index=False)}</div><div class="card warn"><h2>Timing limitation</h2><p>Historical opening fields are timing-unknown ESPN Bet diagnostics. They are not proven Saturday-night DraftKings/FanDuel lines.</p></div><div class="card"><h2>Recommendation</h2><p>{summary['recommendation']}</p></div></main>'''

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--train-seasons',nargs='+',type=int,default=[2021,2022,2023]); ap.add_argument('--selection-season',type=int,default=2024); ap.add_argument('--holdout-season',type=int,default=2025); ap.add_argument('--team-movement-dir',default=str(MOV.relative_to(ROOT))); ap.add_argument('--output-dir',default='data/research/sp_plus_movement_alignment'); ap.add_argument('--strict',action='store_true'); args=ap.parse_args()
 out=ROOT/args.output_dir; build=ROOT/'build/research/sp_plus_movement_alignment'; out.mkdir(parents=True,exist_ok=True); build.mkdir(parents=True,exist_ok=True); before=hashes(); pb=pubstat(); m=load_mod()
 t,f,sp=targets_and_features(args.train_seasons); p,best,grid,features=fit_and_predict(f,m,args.train_seasons,args.selection_season,args.holdout_season); comp=baseline_table(p,m,args.holdout_season,float(best['threshold'])); a=alignment(p,m,float(best['threshold'])); core=pd.read_csv(CORE,low_memory=False); nxt=pd.read_csv(MOV/'next_game_spread_predictions.csv'); fair,blend,blend_scores=fairs(a,core,nxt,args.selection_season,args.holdout_season); fe=fair_eval(fair,args.selection_season,args.holdout_season); diag=diagnostics(fair,args.holdout_season)
 ac=[]
 for (season,c),z in a.groupby(['season','alignment_category']): ac.append({'season':season,'alignment_category':c,'team_rows':len(z),'matchup_rows':0,'actual_market_direction_accuracy':(z.predicted_market_direction==z.actual_market_direction).mean(),'actual_sp_plus_direction_accuracy':(z.predicted_sp_plus_direction==z.actual_sp_plus_direction).mean(),'market_movement_mae':(z.predicted_movement-z.actual_market_rating_change).abs().mean(),'sp_plus_movement_mae':(z.predicted_sp_plus_change-z.actual_sp_plus_change).abs().mean()})
 acr=pd.DataFrame(ac)
 for (season,c),z in fair.groupby(['season','alignment_category']):
  b=z[z.historical_espn_bet_opening_field.notna()].copy(); b['side']=np.where(b.aligned_fair_spread<b.historical_espn_bet_opening_field,'home','away'); b['clv']=np.where(b.side=='home',b.historical_espn_bet_opening_field-b.actual_close,b.actual_close-b.historical_espn_bet_opening_field); b['line']=np.where(b.side=='home',b.historical_espn_bet_opening_field,-b.historical_espn_bet_opening_field); b['margin']=np.where(b.side=='home',b.actual_result,-b.actual_result); b['ats']=[result(x,y) for x,y in zip(b.line,b.margin)]
  acr=pd.concat([acr,pd.DataFrame([{'season':season,'alignment_category':c,'team_rows':0,'matchup_rows':len(z),'projected_close_spread_mae':(z.aligned_fair_spread-z.actual_close).abs().mean(),'movement_direction_toward_close':(b.clv>0).mean(),'positive_clv_rate':(b.clv>0).mean(),'average_clv':b.clv.mean(),'ats_win_rate':(b.ats=='W').sum()/max(b.ats.isin(['W','L']).sum(),1),'roi_at_minus_110':roi(b.ats)}])],ignore_index=True)
 # Confidence locked from 2024: direct semantic tiers, no holdout selection.
 a['confidence_tier']=np.where(a.alignment_category.str.startswith('Both predict'),'Strong agreement',np.where(a.alignment_category=='Opposite directions','Conflict',np.where(a.alignment_category=='Both predict no meaningful change','No meaningful change',np.where(a.direction_agreement,'Moderate agreement','Insufficient data'))))
 conf=[]
 for tier,z in fair[fair.season==args.holdout_season].groupby('confidence_tier'):
  b=z[z.historical_espn_bet_opening_field.notna()].copy(); b['side']=np.where(b.aligned_fair_spread<b.historical_espn_bet_opening_field,'home','away'); b['clv']=np.where(b.side=='home',b.historical_espn_bet_opening_field-b.actual_close,b.actual_close-b.historical_espn_bet_opening_field); b['line']=np.where(b.side=='home',b.historical_espn_bet_opening_field,-b.historical_espn_bet_opening_field); b['margin']=np.where(b.side=='home',b.actual_result,-b.actual_result); b['ats']=[result(x,y) for x,y in zip(b.line,b.margin)]
  conf.append({'confidence':tier,'n':len(z),'fair_spread_mae':(z.aligned_fair_spread-z.actual_close).abs().mean(),'timing_unknown_positive_clv_rate':(b.clv>0).mean(),'average_clv':b.clv.mean(),'ats_win_rate':(b.ats=='W').sum()/max(b.ats.isin(['W','L']).sum(),1),'roi_at_minus_110':roi(b.ats)})
 hold=p[p.season==args.holdout_season]; cm=m.class_metrics(hold.actual_sp_plus_direction,hold.predicted_direction,np.c_[hold.prob_down,hold.prob_no_change,hold.prob_up]); rm=metric(hold.actual_sp_plus_change,hold.predicted_sp_plus_change)
 train_rows=p[p.season.isin(args.train_seasons)]; strongest=[]
 for col in features:
  z=train_rows[[col,'actual_sp_plus_change']].dropna(); corr=z[col].corr(z.actual_sp_plus_change) if len(z)>2 else np.nan
  strongest.append({'feature':col,'train_only_correlation':corr,'absolute_correlation':abs(corr) if pd.notna(corr) else np.nan,'rows':len(z)})
 strongest=sorted(strongest,key=lambda x:-(x['absolute_correlation'] if pd.notna(x['absolute_correlation']) else -1))[:12]
 sample=[{'season':int(s),'all_adjacent_targets':len(z),'eligible_team_games':int(z.eligibility.sum())} for s,z in t.groupby('season')]
 after=hashes(); pa=pubstat(); summary={'generated_at':datetime.now(timezone.utc).isoformat(),'exact_sp_plus_sources':[str(x.relative_to(ROOT)) for x in SP],'observations_genuine_week_to_week':True,'sequence_rule':'target snapshot week must equal current snapshot week + 1; missing calendar weeks never bridged','completed_game_alignment':'completed game week equals target SP+ week','team_week_sample_by_season':sample,'selection':{'threshold':best['threshold'],'direction_model':best['direction_model'],'magnitude_model':best['magnitude_model'],'features':features,'blend':blend,'blend_2024_scores':blend_scores,'selected_without_2025':True},'holdout_2025_direction':cm,'holdout_2025_magnitude':rm,'strongest_predictive_features_train_only':strongest,'market_predictions_out_of_sample':'2024 selection and 2025 locked_holdout rows from existing model; SP+ crossfit/refit provenance stored per row','timing_limit':'Opening field is timing unknown; no claim of actual SP+ availability at sportsbook open','protected_before':before,'protected_after':after,'protected_unchanged':before==after,'publication_repo_before':pb,'publication_repo_after':pa,'publication_repo_clean':pb=='' and pa=='','recommendation':'Do not change production unless locked-2025 improvement is stable across direction, magnitude, fair-spread MAE, and agreement categories.'}
 # Required artifacts.
 t.to_csv(out/'sp_plus_team_week_targets.csv',index=False); f.to_csv(out/'sp_plus_features.csv',index=False); p.to_csv(out/'sp_plus_direction_predictions.csv',index=False); p.to_csv(out/'sp_plus_magnitude_predictions.csv',index=False); pd.concat([grid.assign(scope='selection_2024'),comp],ignore_index=True,sort=False).to_csv(out/'sp_plus_model_comparison.csv',index=False); a.to_csv(out/'team_rating_alignment.csv',index=False); acr.to_csv(out/'alignment_category_results.csv',index=False); fair.to_csv(out/'saturday_fair_spreads.csv',index=False); fe.to_csv(out/'fair_spread_model_comparison.csv',index=False); pd.DataFrame(conf).to_csv(out/'confidence_results.csv',index=False); comp.to_csv(out/'holdout_2025_results.csv',index=False); fair.assign(no_future_market_feature=True,sp_plus_prediction_oos=True,market_prediction_oos=True).to_csv(out/'game_level_audit.csv',index=False)
 final={'status':'COMPLETE_RESEARCH_ONLY','selection':summary['selection'],'holdout_opened_after_selection':True,'production_change_justified':False}; (out/'final_selection.json').write_text(json.dumps(final,indent=2,default=float)+'\n'); summary['timing_unknown_diagnostics']=diag.to_dict('records'); (out/'summary.json').write_text(json.dumps(summary,indent=2,default=float)+'\n'); (build/'index.html').write_text(html(summary,comp,fe,acr))
 print(json.dumps({'targets':len(t),'eligible':len(f),'holdout':len(hold),'selection':summary['selection'],'holdout_direction':cm,'holdout_magnitude':rm,'protected_unchanged':before==after,'publication_repo_clean':summary['publication_repo_clean'],'report':str(build/'index.html')},indent=2,default=float)); return 0
if __name__=='__main__': raise SystemExit(main())
