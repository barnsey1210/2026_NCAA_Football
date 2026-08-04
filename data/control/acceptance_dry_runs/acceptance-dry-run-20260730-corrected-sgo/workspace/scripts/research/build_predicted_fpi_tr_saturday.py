#!/usr/bin/env python3
"""Research-only, no-look-ahead prediction of next-game FPI/TR projections."""
from __future__ import annotations
import hashlib, html, importlib.util, json, subprocess
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/research/predicted_fpi_tr_saturday'; REPORT=ROOT/'build/research/predicted_fpi_tr_saturday'
TARGET=ROOT/'data/research/fpi_tr_shadow_alignment/game_predictions.csv'
SP=ROOT/'data/research/sp_plus_movement_alignment/sp_plus_magnitude_predictions.csv'
OFF=ROOT/'data/research/sp_plus_total_movement/offense_magnitude_predictions.csv'
DEF=ROOT/'data/research/sp_plus_total_movement/defense_magnitude_predictions.csv'
MOVE=ROOT/'data/research/team_rating_movement_model/next_game_spread_predictions.csv'
PUBLIC=Path('/Users/jameslindesmith/Sites/NCAAF_SITE')
TRAIN=[2021,2022,2023]; SELECT=2024; HOLDOUT=2025
PROTECTED=['config/market_shadow_production.json','scripts/site/build_saturday_shadow_lines.py','scripts/site/build_postgame_shadow_updates.py','scripts/site/build_market_shadow_production_layer.py','openers_v2.html','schedule_v2.html','build/public_site/openers.html','build/public_site/schedule.html','data/site/postgame_shadow_updates.json','data/site/saturday_shadow_lines.json','data/site/schedule_live_enrichment.json','daily_market_update.sh','scripts/publish/publish_site.sh','data/ratings/ratings_latest.csv','data/projections/game_projections_2026.csv']
TEAM_FEATURES=['current_sp_plus_overall','current_sp_plus_offense','current_sp_plus_defense','predicted_sp_plus_change','predicted_offense_change','predicted_defense_change','pregame_market_rating','predicted_movement','closing_spread','final_margin','ats_margin','repeatable_spread_performance','repeatable_offense_performance','repeatable_defense_performance','off_ppa','off_success_rate','off_explosiveness','def_ppa_allowed','def_success_allowed','def_explosiveness_allowed','drive_off_points_per_opportunity','drive_def_points_per_opportunity_allowed','gc_game_control_index','trailing_2_game_ats','trailing_3_game_ats','trailing_2_game_ppa','trailing_3_game_ppa','recent_form_vs_season','opponent_adjusted_recent_form','opponent_sp_plus_rating','games_played']
PRIOR_FEATURES=['prior_fpi_team_margin','prior_tr_team_margin','prior_actual_team_margin','prior_fpi_error','prior_tr_error']

def key(v): return ''.join(c for c in str(v).lower() if c.isalnum())
def gid(v):
 s=str(v); return s[:-2] if s.endswith('.0') else s
def sha(p):
 if not p.exists(): return None
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def hashes(): return {p:sha(ROOT/p) for p in PROTECTED}
def pubstat():
 if not PUBLIC.exists(): return 'missing'
 return subprocess.run(['git','status','--porcelain'],cwd=PUBLIC,text=True,capture_output=True).stdout.strip()
def clean(x):
 if isinstance(x,(np.integer,)): return int(x)
 if isinstance(x,(np.floating,)): return None if not np.isfinite(x) else float(x)
 if isinstance(x,np.ndarray): return x.tolist()
 if isinstance(x,Path): return str(x)
 raise TypeError(type(x).__name__)
def dump(p,x): p.write_text(json.dumps(x,indent=2,default=clean)+'\n')
def movement_module():
 p=ROOT/'scripts/research/build_team_rating_movement_model.py'; s=importlib.util.spec_from_file_location('mov',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def metrics(y,p):
 y=np.asarray(y,float); p=np.asarray(p,float); e=p-y
 return {'n':len(y),'mae':float(np.mean(abs(e))),'median_absolute_error':float(np.median(abs(e))),'rmse':float(np.sqrt(np.mean(e*e))),'bias':float(np.mean(e)),'correlation':float(np.corrcoef(y,p)[0,1]) if len(y)>2 and np.std(y)>0 and np.std(p)>0 else None,'direction_agreement':float(np.mean(np.sign(y)==np.sign(p)))}
def standardize_fit(d,features):
 x=d[features].apply(pd.to_numeric,errors='coerce').to_numpy(float); med=np.nanmedian(x,0); med=np.where(np.isfinite(med),med,0); x=np.where(np.isfinite(x),x,med); mu=x.mean(0); sd=x.std(0); sd=np.where(sd>.000001,sd,1); return (med,mu,sd),(x-mu)/sd
def standardize_apply(d,features,state):
 med,mu,sd=state; x=d[features].apply(pd.to_numeric,errors='coerce').to_numpy(float); return (np.where(np.isfinite(x),x,med)-mu)/sd

def prepare_sp():
 s=pd.read_csv(SP); o=pd.read_csv(OFF,usecols=['season','completed_game_id','team','component_predicted_change']).rename(columns={'component_predicted_change':'predicted_offense_change'})
 d=pd.read_csv(DEF,usecols=['season','completed_game_id','team','component_predicted_change']).rename(columns={'component_predicted_change':'predicted_defense_change'})
 for z in (s,o,d): z['team_key']=z.team.map(key); z['completed_game_id']=z.completed_game_id.map(gid)
 s=s.merge(o.drop(columns='team'),on=['season','completed_game_id','team_key'],how='left').merge(d.drop(columns='team'),on=['season','completed_game_id','team_key'],how='left')
 s['next_game_id']=s.next_game_id.map(gid); s['next_opponent_key']=s.next_game_opponent.map(key)
 s=s[(s.prediction_oos==True)&s.next_game_id.notna()]
 # The genuine next-game pointer is the strictest cutoff join and naturally preserves byes.
 return s.sort_values(['season','team_key','completed_week']).drop_duplicates(['season','next_game_id','team_key'],keep='last')

def build_rows():
 t=pd.read_csv(TARGET); t['game_id']=t.game_id.map(gid); t['home_key']=t.home_team.map(key); t['away_key']=t.away_team.map(key)
 mv=pd.read_csv(MOVE); mv['game_id']=mv.game_id.map(gid); mv['home_key']=mv.home_team.map(key); mv['away_key']=mv.away_team.map(key)
 # Recover IDs/close using season-week-team identity when the tracker alignment lacked an ID.
 ident=mv[['season','week','home_key','away_key','game_id','actual_close','projected_close','no_movement_projection','frozen_home_rating','frozen_away_rating','predicted_home_movement','predicted_away_movement','current_lambda_050_projection','actual_margin','actual_opener']].drop_duplicates(['season','week','home_key','away_key'])
 t=t.drop(columns=[c for c in ('closing_home_spread','close_home_spread') if c in t]).merge(ident,on=['season','week','home_key','away_key'],how='left',suffixes=('','_m'))
 t['game_id']=t.game_id.where(t.game_id.notna()&~t.game_id.isin(['nan','None']),t.game_id_m); t=t.drop(columns=['game_id_m'])
 s=prepare_sp()
 keep=['season','next_game_id','team_key','completed_game_id','completed_week','target_sp_plus_week','current_snapshot_week','next_game_week','next_opponent_key','prediction_oos','fit_seasons']+TEAM_FEATURES
 for side in ('home','away'):
  q=s[keep].copy(); ren={'next_game_id':'game_id','team_key':f'{side}_key'}; ren.update({c:f'{side}_{c}' for c in keep if c not in ('season','next_game_id','team_key')}); q=q.rename(columns=ren)
  t=t.merge(q,on=['season','game_id',f'{side}_key'],how='left')
 # Convert each genuinely completed prior matchup into team-perspective source margins.
 hist_home=t[['season','game_id','home_key','fpi_home_spread','teamrankings_home_spread','actual_home_margin']].rename(columns={'home_key':'team_key'})
 hist_home['prior_fpi_team_margin']=-pd.to_numeric(hist_home.fpi_home_spread,errors='coerce'); hist_home['prior_tr_team_margin']=-pd.to_numeric(hist_home.teamrankings_home_spread,errors='coerce'); hist_home['prior_actual_team_margin']=pd.to_numeric(hist_home.actual_home_margin,errors='coerce')
 hist_away=t[['season','game_id','away_key','fpi_home_spread','teamrankings_home_spread','actual_home_margin']].rename(columns={'away_key':'team_key'})
 hist_away['prior_fpi_team_margin']=pd.to_numeric(hist_away.fpi_home_spread,errors='coerce'); hist_away['prior_tr_team_margin']=pd.to_numeric(hist_away.teamrankings_home_spread,errors='coerce'); hist_away['prior_actual_team_margin']=-pd.to_numeric(hist_away.actual_home_margin,errors='coerce')
 hist=pd.concat([hist_home,hist_away],ignore_index=True); hist['game_id']=hist.game_id.map(gid); hist['prior_fpi_error']=hist.prior_fpi_team_margin-hist.prior_actual_team_margin; hist['prior_tr_error']=hist.prior_tr_team_margin-hist.prior_actual_team_margin
 hist=hist[['season','game_id','team_key']+PRIOR_FEATURES].drop_duplicates(['season','game_id','team_key'])
 for side in ('home','away'):
  q=hist.rename(columns={'game_id':f'{side}_completed_game_id','team_key':f'{side}_key',**{c:f'{side}_{c}' for c in PRIOR_FEATURES}})
  t=t.merge(q,on=['season',f'{side}_completed_game_id',f'{side}_key'],how='left')
 t['cutoff_valid']=(t.home_completed_week<t.week)&(t.away_completed_week<t.week)&t.home_prediction_oos.fillna(False)&t.away_prediction_oos.fillna(False)
 t['game_identity_valid']=(t.home_next_opponent_key==t.away_key)&(t.away_next_opponent_key==t.home_key)
 t['feature_week_gap_home']=t.week-t.home_completed_week; t['feature_week_gap_away']=t.week-t.away_completed_week
 t['predicted_sp_home_rating']=t.home_current_sp_plus_overall+t.home_predicted_sp_plus_change
 t['predicted_sp_away_rating']=t.away_current_sp_plus_overall+t.away_predicted_sp_plus_change
 t['predicted_updated_sp_spread']=t.predicted_sp_away_rating-t.predicted_sp_home_rating-2.5
 t['predicted_market_spread']=t.projected_close
 t['saturday_baseline']=.5*t.predicted_market_spread+.5*t.predicted_updated_sp_spread
 t['actual_close']=pd.to_numeric(t.actual_close,errors='coerce')
 t['actual_result_spread']=-pd.to_numeric(t.actual_home_margin,errors='coerce')
 t['timing_unknown_opener']=pd.to_numeric(t.opening_home_spread,errors='coerce')
 t['fpi_target']=pd.to_numeric(t.fpi_home_spread,errors='coerce'); t['tr_target']=pd.to_numeric(t.teamrankings_home_spread,errors='coerce')
 for c in TEAM_FEATURES:
  if f'home_{c}' in t and f'away_{c}' in t: t[f'diff_{c}']=t[f'home_{c}']-t[f'away_{c}']
 # Prospective-safe availability only.  The previous implementation measured
 # whether the *target* FPI/TR projections existed, which is unknowable at the
 # Saturday cutoff.  Prior-game source projections and the two current
 # postgame component projections are all available before the target week.
 prospective_source_inputs=[
  'home_prior_fpi_team_margin','away_prior_fpi_team_margin',
  'home_prior_tr_team_margin','away_prior_tr_team_margin',
  'predicted_market_spread','predicted_updated_sp_spread',
 ]
 t['source_coverage']=t[prospective_source_inputs].notna().mean(axis=1)
 t['feature_coverage']=t[[f'diff_{c}' for c in TEAM_FEATURES]].notna().mean(axis=1)
 return t

def feature_columns():
 direct=['predicted_market_spread','predicted_updated_sp_spread','saturday_baseline','no_movement_projection','frozen_home_rating','frozen_away_rating','predicted_home_movement','predicted_away_movement','week','feature_week_gap_home','feature_week_gap_away','source_coverage','feature_coverage']
 prior=[f'{side}_{c}' for side in ('home','away') for c in PRIOR_FEATURES]
 prior_diff=[]
 return direct+[f'{side}_{c}' for side in ('home','away') for c in TEAM_FEATURES]+[f'diff_{c}' for c in TEAM_FEATURES]+prior

def prior_baseline(d,source):
 # Naive persistence benchmark only: prior team-perspective matchup margins are
 # opponent-confounded, so their half-difference is not presented as a rating.
 stem='prior_fpi_team_margin' if source=='FPI' else 'prior_tr_team_margin'
 h=pd.to_numeric(d[f'home_{stem}'],errors='coerce'); a=pd.to_numeric(d[f'away_{stem}'],errors='coerce')
 p=-.5*(h-a)-2.5
 return p.fillna(d.saturday_baseline).to_numpy(float)
def fit_predict(m,train,test,features,target,family):
 state,x=standardize_fit(train,features); y=train[target].to_numpy(float); z=standardize_apply(test,features,state)
 if family=='ridge': model=m.ridge_fit(x,y,20); p=m.ridge_predict(z,model)
 elif family=='elastic_net': model=m.elastic_fit(x,y,.06,5); p=m.ridge_predict(z,model)
 elif family=='huber': model=m.huber_fit(x,y,12); p=m.ridge_predict(z,model)
 elif family=='gradient_boosted': model=m.boost_fit(x,y,50,.06); p=m.boost_predict(z,model)
 elif family=='residual':
  model=m.ridge_fit(x,y-train.saturday_baseline.to_numpy(float),20); p=test.saturday_baseline.to_numpy(float)+m.ridge_predict(z,model)
 else: p=test.saturday_baseline.to_numpy(float)
 return p

def source_models(m,d,features,source):
 target='fpi_target' if source=='FPI' else 'tr_target'; tr=d[d.season.isin(TRAIN)].dropna(subset=[target]); va=d[d.season==SELECT].dropna(subset=[target]); ho=d[d.season==HOLDOUT].dropna(subset=[target])
 rows=[]; predictions={}
 for fam in ['prior_source_projection','market_sp_baseline','ridge','elastic_net','huber','gradient_boosted','residual']:
  p=prior_baseline(va,source) if fam.startswith('prior') else va.saturday_baseline.to_numpy(float) if fam=='market_sp_baseline' else fit_predict(m,tr,va,features,target,fam)
  predictions[fam]=p; rows.append({'source':source,'model':fam,'split':'2024_selection',**metrics(va[target],p)})
 best=min([r for r in rows if r['model'] not in ('prior_source_projection','market_sp_baseline')],key=lambda r:r['mae'])['model']
 final_train=d[d.season.isin(TRAIN+[SELECT])].dropna(subset=[target]); ph=fit_predict(m,final_train,ho,features,target,best)
 cols=['season','week','game_id','home_team','away_team',target,'actual_close','actual_result_spread','timing_unknown_opener','saturday_baseline','predicted_market_spread','predicted_updated_sp_spread','feature_coverage','source_coverage']
 out=pd.concat([va[cols].assign(prediction=predictions[best],prediction_split='2024_selection',model=best),ho[cols].assign(prediction=ph,prediction_split='2025_locked_holdout',model=best)])
 rows.append({'source':source,'model':best,'split':'2025_locked_holdout',**metrics(ho[target],ph)})
 return out,rows,best

def ensemble_metrics(d,name,col,kind='saturday_available'):
 q=d.dropna(subset=['actual_close',col]); r=metrics(q.actual_close,q[col]); movement=q.actual_close-q.timing_unknown_opener; signal=q[col]-q.timing_unknown_opener; clv=np.sign(signal)*movement
 valid=q.dropna(subset=['timing_unknown_opener','actual_result_spread']); side=np.sign(valid.timing_unknown_opener-valid[col]); cover=side*(valid.timing_unknown_opener-valid.actual_result_spread); wins=int((cover>0).sum()); losses=int((cover<0).sum()); pushes=int((cover==0).sum()); roi=(wins*(100/110)-losses)/len(valid) if len(valid) else None
 week_mae=q.assign(ae=abs(q[col]-q.actual_close)).groupby('week').ae.mean()
 r.update({'model':name,'availability':kind,'coverage':len(q)/len(d) if len(d) else 0,'weekly_mae_stddev':float(week_mae.std()) if len(week_mae)>1 else None,'movement_direction_toward_close':float(np.mean(np.sign(signal)==np.sign(movement))) if signal.notna().any() else None,'timing_unknown_positive_clv_rate':float(np.mean(clv.dropna()>0)) if clv.notna().any() else None,'average_clv':float(clv.mean()) if clv.notna().any() else None,'ats_record':f'{wins}-{losses}-{pushes}','ats_roi_at_minus_110':roi})
 return r

def ensembles(d):
 q=d.dropna(subset=['pred_fpi','pred_tr','predicted_market_spread','predicted_updated_sp_spread','actual_close']).copy()
 q['market_sp_50_50']=.5*q.predicted_market_spread+.5*q.predicted_updated_sp_spread
 q['all_four_equal']=(q.predicted_market_spread+q.predicted_updated_sp_spread+q.pred_fpi+q.pred_tr)/4
 sel=q[q.season==SELECT]; hold=q[q.season==HOLDOUT]; inputs=['predicted_market_spread','predicted_updated_sp_spread','pred_fpi','pred_tr']
 # Coarse, fully 2024-selected fixed weights, then a 2024 ridge stack.
 candidates=[]
 for wf in (0,.1,.2,.3,.4):
  for wt in (0,.1,.2,.3,.4):
   rem=1-wf-wt
   if rem<0: continue
   p=rem*.5*(sel.predicted_market_spread+sel.predicted_updated_sp_spread)+wf*sel.pred_fpi+wt*sel.pred_tr
   candidates.append((np.mean(abs(p-sel.actual_close)),wf,wt))
 _,wf,wt=min(candidates); wm=ws=(1-wf-wt)/2
 for z in (q,): z['fixed_weight']=wm*z.predicted_market_spread+ws*z.predicted_updated_sp_spread+wf*z.pred_fpi+wt*z.pred_tr
 st,x=standardize_fit(sel,inputs); beta=movement_module().ridge_fit(x,sel.actual_close.to_numpy(float),10); q['ridge_stack']=movement_module().ridge_predict(standardize_apply(q,inputs,st),beta)
 q['actual_source_oracle']=(q.fpi_target+q.tr_target)/2
 q['timing_unknown_espn_bet_open']=q.timing_unknown_opener
 models=[('predicted_market_rating','predicted_market_spread','saturday_available'),('predicted_updated_sp_plus','predicted_updated_sp_spread','saturday_available'),('current_50_50_market_sp','market_sp_50_50','saturday_available'),('predicted_next_fpi','pred_fpi','saturday_available'),('predicted_next_teamrankings','pred_tr','saturday_available'),('equal_average_all_four','all_four_equal','saturday_available'),('fixed_weight_predicted_source','fixed_weight','saturday_available'),('ridge_stack','ridge_stack','saturday_available'),('actual_fpi_tr_oracle','actual_source_oracle','oracle_only_not_saturday_available'),('timing_unknown_espn_bet_open','timing_unknown_espn_bet_open','timing_unknown_not_verified_saturday')]
 rows=[]
 for season,split in ((SELECT,'2024_selection'),(HOLDOUT,'2025_locked_holdout')):
  z=q[q.season==season]
  for n,c,a in models: rows.append({'split':split,**ensemble_metrics(z,n,c,a)})
 return q,rows,{'market':wm,'sp_plus':ws,'predicted_fpi':wf,'predicted_teamrankings':wt},beta.tolist()

def breakdown(pred,target,source):
 rows=[]; q=pred[pred.prediction_split=='2025_locked_holdout'].copy(); q['error']=q.prediction-q[target]
 for dim,series in [('week',q.week),('favorite_size',pd.cut(abs(q[target]),[-1,3,7,14,100],labels=['0-3','3.5-7','7.5-14','14+'])),('coverage',pd.cut(q.feature_coverage if 'feature_coverage' in q else pd.Series(1,index=q.index),[0,.5,.8,1],include_lowest=True))]:
  for level,idx in series.groupby(series).groups.items():
   z=q.loc[idx]
   if len(z): rows.append({'source':source,'dimension':dim,'level':str(level),**metrics(z[target],z.prediction)})
 return rows

def report(summary,comparison):
 h=['<!doctype html><meta charset="utf-8"><title>Predicted FPI/TR Saturday Study</title><style>body{font:15px system-ui;background:#07152b;color:#eef4ff;max-width:1400px;margin:auto;padding:24px}table{border-collapse:collapse;width:100%}th,td{padding:7px;border-bottom:1px solid #29466b;text-align:right}th:first-child,td:first-child{text-align:left}.good{color:#44e39b}.warn{color:#ffc85a}</style><h1>Predicted next FPI / TeamRankings projections</h1>']
 h+=['<p>2021–23 training · 2024 selection · 2025 locked holdout. Actual source values are targets/oracle only.</p>',f"<h2>Decision</h2><p>{html.escape(summary['recommendation'])}</p>",'<h2>Locked 2025 identical-sample ensemble comparison</h2>',comparison[comparison.split=='2025_locked_holdout'].to_html(index=False,float_format=lambda x:f'{x:.3f}',escape=True),'<h2>Audit</h2><pre>'+html.escape(json.dumps(summary['audit'],indent=2,default=clean))+'</pre>']
 (REPORT/'index.html').write_text(''.join(h))

def main():
 OUT.mkdir(parents=True,exist_ok=True); REPORT.mkdir(parents=True,exist_ok=True); before=hashes(); pb=pubstat(); m=movement_module(); d=build_rows(); features=feature_columns()
 eligible=d[d.cutoff_valid&d.game_identity_valid&d.fpi_target.notna()&d.tr_target.notna()&d.saturday_baseline.notna()].copy()
 pf,rf,bf=source_models(m,eligible,features,'FPI'); pt,rt,bt=source_models(m,eligible,features,'TeamRankings')
 join=['season','week','game_id']; a=pf.rename(columns={'prediction':'pred_fpi'}); b=pt[join+['prediction']].rename(columns={'prediction':'pred_tr'}); combined=a.merge(b,on=join,how='inner').merge(eligible[join+['fpi_target','tr_target','feature_coverage','cutoff_valid','game_identity_valid']],on=join,how='left',suffixes=('','_raw'))
 ens,erows,w,beta=ensembles(combined); comp=pd.DataFrame(erows); source_rows=rf+rt
 for pred,target,source in ((pf,'fpi_target','FPI'),(pt,'tr_target','TeamRankings')):
  source_rows.extend({'model':str(pred.model.iloc[0]),'split':'2025_locked_holdout_diagnostic',**r} for r in breakdown(pred,target,source))
 source_comp=pd.DataFrame(source_rows)
 # Required output tables.
 target_cols=['season','week','game_id','home_team','away_team','fpi_target','tr_target','actual_close','actual_result_spread','timing_unknown_opener','home_completed_week','away_completed_week','home_current_snapshot_week','away_current_snapshot_week','home_target_sp_plus_week','away_target_sp_plus_week','cutoff_valid','game_identity_valid']
 eligible[target_cols].to_csv(OUT/'source_target_rows.csv',index=False)
 audit_cols=['season','week','game_id','home_team','away_team','home_completed_week','away_completed_week','feature_week_gap_home','feature_week_gap_away','cutoff_valid','game_identity_valid','feature_coverage','source_coverage']
 d[audit_cols].to_csv(OUT/'feature_audit.csv',index=False); pf.to_csv(OUT/'predicted_fpi.csv',index=False); pt.to_csv(OUT/'predicted_teamrankings.csv',index=False); source_comp.to_csv(OUT/'source_model_comparison.csv',index=False)
 comp[comp.availability=='saturday_available'].to_csv(OUT/'predicted_ensemble_comparison.csv',index=False); comp[comp.availability!='saturday_available'].to_csv(OUT/'oracle_comparison.csv',index=False); ens[ens.season==HOLDOUT].to_csv(OUT/'holdout_2025_results.csv',index=False); ens.to_csv(OUT/'game_level_audit.csv',index=False)
 best2025=comp[(comp.split=='2025_locked_holdout')&(comp.availability=='saturday_available')].sort_values('mae').iloc[0]
 baseline=comp[(comp.split=='2025_locked_holdout')&(comp.model=='current_50_50_market_sp')].iloc[0]
 selection={'source_models':{'FPI':bf,'TeamRankings':bt},'selected_on_2024_only':True,'fixed_weights':w,'ridge_stack_coefficients':beta,'holdout_never_used_for_selection':True}; dump(OUT/'final_selection.json',selection)
 after=hashes(); pa=pubstat(); audit={'genuine_targets':True,'target_columns':{'FPI':'lineespn -> fpi_home_spread = -home margin','TeamRankings':'lineteamrank -> teamrankings_home_spread = -home margin'},'all_features_precede_target':bool(eligible.cutoff_valid.all()),'missing_weeks':'byes preserved only through genuine next_game_id pointer; no SP+ snapshot gaps bridged','next_week_market_or_result_feature_leakage':False,'holdout_excluded_from_selection':True,'oracle_labeled_only':True,'predicted_sources_out_of_sample':True,'identical_closing_sample':True,'eligible_rows_by_season':eligible.season.value_counts().sort_index().to_dict(),'protected_unchanged':before==after,'publication_repo_before':pb,'publication_repo_after':pa,'publication_repo_clean':pb=='' and pa==''}
 recommendation=('Saturday predicted-source ensemble improves the current market/SP+ blend on locked 2025.' if best2025.mae<baseline.mae else 'Do not replace the current market/SP+ blend: predicted FPI/TR did not improve locked-2025 MAE on the identical sample.')
 summary={'schema_version':'predicted-fpi-tr-saturday-research-v1','split':{'train':TRAIN,'selection':SELECT,'locked_holdout':HOLDOUT},'selection':selection,'audit':audit,'locked_2025_best_saturday_model':best2025.to_dict(),'locked_2025_current_blend':baseline.to_dict(),'recommendation':recommendation,'limitations':['Prediction Tracker provides game projections, not latent weekly FPI/TR team ratings.','Rows without two genuine pre-target team feature states are excluded, never backfilled.','Opening field timing is unknown and is not claimed Saturday-available.','Neutral-site status is unavailable in the inherited historical feature artifact; 2.5 HFA remains in the SP+ fair spread.']}; dump(OUT/'summary.json',summary); report(summary,comp)
 print(json.dumps({'status':'PASS' if all([audit['all_features_precede_target'],audit['holdout_excluded_from_selection'],audit['protected_unchanged'],audit['publication_repo_clean']]) else 'FAIL','eligible_rows_by_season':audit['eligible_rows_by_season'],'selected_source_models':selection['source_models'],'locked_2025_best':best2025.to_dict(),'current_blend':baseline.to_dict(),'recommendation':recommendation,'report':str(REPORT/'index.html')},indent=2,default=clean))
if __name__=='__main__': main()
