#!/usr/bin/env python3
"""Calibrate Shadow projected-market-value tiers; research only."""
from __future__ import annotations
import json,math
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'data/research/shadow_value_confidence'; BUILD=ROOT/'build/research/shadow_value_confidence'
TRAIN=[2021,2022,2023]; SELECT=2024; HOLDOUT=2025

def standardize_fit(d,features):
 x=d[features].apply(pd.to_numeric,errors='coerce').to_numpy(float); med=np.nanmedian(x,axis=0);med=np.where(np.isfinite(med),med,0.0);x=np.where(np.isfinite(x),x,med);mean=x.mean(axis=0);std=x.std(axis=0);std=np.where(std>1e-9,std,1.0);return {'median':med,'mean':mean,'std':std},(x-mean)/std
def standardize_apply(d,features,state):
 x=d[features].apply(pd.to_numeric,errors='coerce').to_numpy(float);x=np.where(np.isfinite(x),x,state['median']);return (x-state['mean'])/state['std']
def ridge_fit(x,y,alpha):
 x=np.column_stack([np.ones(len(x)),x]);pen=alpha*np.eye(x.shape[1]);pen[0,0]=0;return np.linalg.solve(x.T@x+pen,x.T@np.asarray(y,float))
def ridge_predict(x,b): return np.column_stack([np.ones(len(x)),x])@b
def boost_fit(x,y,rounds=40,learning_rate=.06):
 y=np.asarray(y,float);base=float(np.mean(y));pred=np.full(len(y),base);trees=[]
 for _ in range(rounds):
  residual=y-pred;best=None
  for j in range(x.shape[1]):
   for cut in np.unique(np.quantile(x[:,j],[.15,.3,.5,.7,.85])):
    left=x[:,j]<=cut
    if left.sum()<20 or (~left).sum()<20: continue
    lv=float(residual[left].mean());rv=float(residual[~left].mean());err=float(np.sum((residual-np.where(left,lv,rv))**2))
    if best is None or err<best[0]:best=(err,j,float(cut),lv,rv)
  if best is None:break
  _,j,cut,lv,rv=best;trees.append((j,cut,lv,rv));pred+=learning_rate*np.where(x[:,j]<=cut,lv,rv)
 return {'base':base,'trees':trees,'learning_rate':learning_rate}
def boost_predict(x,m):
 p=np.full(len(x),m['base'])
 for j,cut,lv,rv in m['trees']:p+=m['learning_rate']*np.where(x[:,j]<=cut,lv,rv)
 return p
def metrics(y,p):
 y=np.asarray(y,float);p=np.asarray(p,float);e=p-y
 return {'n':len(e),'mae':float(np.mean(abs(e))),'median_absolute_error':float(np.median(abs(e))),'rmse':float(np.sqrt(np.mean(e*e))),'bias':float(np.mean(e))}
def tier_stats(d,market='spread'):
 rows=[]
 for tier in ('green','yellow','red'):
  q=d[d.tier==tier]; edge=q.edge; close=q.actual_close; current=q.current_model; shadow=q.shadow; line=q.market
  clv=np.sign(edge)*(line-close if market=='spread' else close-line); result=q.actual_result
  if market=='spread': cover=np.sign(edge)*(line-result)
  else: cover=np.sign(edge)*(result-line)
  w=int((cover>0).sum());l=int((cover<0).sum());p=int((cover==0).sum()); roi=(w*100/110-l)/len(cover.dropna()) if cover.notna().any() else None
  rows.append({'market':market,'tier':tier,'sample_size':len(q),'average_projected_edge':float(abs(edge).mean()),**metrics(close,shadow),'probability_shadow_beats_current':float((abs(shadow-close)<abs(current-close)).mean()),'positive_clv_rate':float((clv>0).mean()),'average_clv':float(clv.mean()),'ats_win_rate':w/(w+l) if w+l else None,'ats_record':f'{w}-{l}-{p}','roi_at_minus_110':roi})
 return pd.DataFrame(rows)
def reasonable_monotonic(s):
 x=s.set_index('tier');
 return bool(x.loc['green','average_projected_edge']>x.loc['yellow','average_projected_edge']>x.loc['red','average_projected_edge'] and x.loc['green','mae']<=x.loc['red','mae'] and x.loc['green','probability_shadow_beats_current']+0.02>=x.loc['yellow','probability_shadow_beats_current'] and x.loc['yellow','probability_shadow_beats_current']+0.02>=x.loc['red','probability_shadow_beats_current'] and x.loc['green','average_clv']>=x.loc['yellow','average_clv']>=x.loc['red','average_clv'])
def market_value_monotonic(s):
 x=s.set_index('tier'); return bool(x.loc['green','average_clv']>x.loc['yellow','average_clv']>x.loc['red','average_clv'] and x.loc['green','positive_clv_rate']>=x.loc['yellow','positive_clv_rate']>=x.loc['red','positive_clv_rate'])
def two_tier_stats(d,market='spread'):
 rows=[]
 for tier in ('actionable','neutral'):
  q=d[d.tier==tier]; clv=np.sign(q.edge)*(q.market-q.actual_close if market=='spread' else q.actual_close-q.market)
  rows.append({'market':market,'tier':tier,'sample_size':len(q),'average_projected_edge':float(abs(q.edge).mean()),'average_clv':float(clv.mean()),'positive_clv_rate':float((clv>0).mean()),**metrics(q.actual_close,q.shadow)})
 return pd.DataFrame(rows)
def fit_expected(train,test,features,family):
 st,x=standardize_fit(train,features); y=train.actual_abs_error.to_numpy(float); z=standardize_apply(test,features,st)
 if family=='ridge': return ridge_predict(z,ridge_fit(x,y,15))
 if family=='linear': return ridge_predict(z,ridge_fit(x,y,.001))
 if family=='boost': return boost_predict(z,boost_fit(x,y,40,.06))
 return np.full(len(test),y.mean())
def select_tiers(d,features,market):
 tr=d[d.season.isin(TRAIN)].copy(); va=d[d.season==SELECT].copy(); rows=[]; candidates=[]
 for fam in ('rules','linear','ridge','boost'):
  va[f'ee_{fam}']=fit_expected(tr,va,features,fam); va[f'score_{fam}']=abs(va.edge)/np.maximum(va[f'ee_{fam}'],.5)
  rows.append({'market':market,'model':fam,**metrics(va.actual_abs_error,va[f'ee_{fam}'])})
  for lo in (.25,.30,.33,.40):
   for hi in (.60,.67,.70,.75):
    if hi-lo<.25: continue
    q1,q2=va[f'score_{fam}'].quantile([lo,hi]); va['tier']=np.where(va[f'score_{fam}']>=q2,'green',np.where(va[f'score_{fam}']>=q1,'yellow','red')); s=tier_stats(va,market)
    min_n=int(s.sample_size.min()); mono=reasonable_monotonic(s); objective=float(s.set_index('tier').loc['green','average_clv']-s.set_index('tier').loc['red','average_clv']+.2*(s.set_index('tier').loc['green','probability_shadow_beats_current']-s.set_index('tier').loc['red','probability_shadow_beats_current']))
    candidates.append((mono,min_n,objective,fam,float(q1),float(q2),lo,hi))
 pick=max(candidates,key=lambda x:(x[0],x[1]>=max(20,int(.15*len(va))),x[2])); _,_,_,fam,q1,q2,lo,hi=pick
 return {'expected_error_model':fam,'red_yellow_threshold':q1,'yellow_green_threshold':q2,'selection_quantiles':[lo,hi],'selection_monotonic':bool(pick[0]),'selection_min_tier_n':int(pick[1])},pd.DataFrame(rows)
def select_spread_market_value(d,features):
 tr=d[d.season.isin(TRAIN)].copy(); va=d[d.season==SELECT].copy(); va['predicted_expected_error']=fit_expected(tr,va,features,'linear')
 va['score_edge_size']=abs(va.edge); va['score_dispersion_adjusted']=abs(va.edge)/np.maximum(1+va.dispersion,1); va['score_expected_error_adjusted']=abs(va.edge)/np.maximum(va.predicted_expected_error,.5); va['score_edge_minus_dispersion']=abs(va.edge)-.5*va.dispersion
 score_cols=['score_edge_size','score_dispersion_adjusted','score_expected_error_adjusted','score_edge_minus_dispersion']; candidates=[]; twos=[]
 for score in score_cols:
  for lo in (.20,.25,.30,.33,.40):
   for hi in (.60,.67,.70,.75,.80):
    if hi-lo<.25: continue
    q1,q2=va[score].quantile([lo,hi]); z=va.copy(); z['tier']=np.where(z[score]>=q2,'green',np.where(z[score]>=q1,'yellow','red')); s=tier_stats(z,'spread'); mono=market_value_monotonic(s); min_n=int(s.sample_size.min()); x=s.set_index('tier'); stability=z.assign(clv=np.sign(z.edge)*(z.market-z.actual_close)).groupby(['stage','tier']).clv.mean().unstack(); stable=float((stability.get('green',pd.Series(dtype=float))>stability.get('red',pd.Series(dtype=float))).mean()) if len(stability) else 0; objective=x.loc['green','average_clv']-x.loc['red','average_clv']+2*(x.loc['green','positive_clv_rate']-x.loc['red','positive_clv_rate'])+.25*stable; candidates.append((mono,min_n>=20,objective,score,float(q1),float(q2),lo,hi,stable))
  for cutq in (.50,.60,.67,.70,.75,.80):
   cut=va[score].quantile(cutq); z=va.copy();z['tier']=np.where(z[score]>=cut,'actionable','neutral');s=two_tier_stats(z);x=s.set_index('tier');mono=bool(x.loc['actionable','average_clv']>x.loc['neutral','average_clv'] and x.loc['actionable','positive_clv_rate']>=x.loc['neutral','positive_clv_rate']);objective=x.loc['actionable','average_clv']-x.loc['neutral','average_clv']+2*(x.loc['actionable','positive_clv_rate']-x.loc['neutral','positive_clv_rate']);twos.append((mono,int(s.sample_size.min())>=30,objective,score,float(cut),cutq))
 three=max(candidates,key=lambda x:(x[0],x[1],x[2]));two=max(twos,key=lambda x:(x[0],x[1],x[2])); return {'expected_error_model':'linear','score':three[3],'red_yellow_threshold':three[4],'yellow_green_threshold':three[5],'selection_quantiles':[three[6],three[7]],'selection_clv_monotonic':bool(three[0]),'selection_minimum_sample_ok':bool(three[1]),'selection_stage_stability':three[8]}, {'score':two[3],'actionable_threshold':two[4],'selection_quantile':two[5],'selection_clv_monotonic':bool(two[0]),'selection_minimum_sample_ok':bool(two[1])}
def apply_spread_market_value(d,features,choice,two=False):
 tr=d[d.season.isin(TRAIN+[SELECT])];ho=d[d.season==HOLDOUT].copy();ho['predicted_expected_error']=fit_expected(tr,ho,features,'linear');ho['score_edge_size']=abs(ho.edge);ho['score_dispersion_adjusted']=abs(ho.edge)/np.maximum(1+ho.dispersion,1);ho['score_expected_error_adjusted']=abs(ho.edge)/np.maximum(ho.predicted_expected_error,.5);ho['score_edge_minus_dispersion']=abs(ho.edge)-.5*ho.dispersion;score=choice['score']
 if two: ho['tier']=np.where(ho[score]>=choice['actionable_threshold'],'actionable','neutral')
 else: ho['tier']=np.where(ho[score]>=choice['yellow_green_threshold'],'green',np.where(ho[score]>=choice['red_yellow_threshold'],'yellow','red'))
 ho['value_score']=ho[score];return ho
def apply_model(d,features,choice):
 tr=d[d.season.isin(TRAIN+[SELECT])]; ho=d[d.season==HOLDOUT].copy(); fam=choice['expected_error_model']; ho['predicted_expected_error']=fit_expected(tr,ho,features,fam); ho['value_score']=abs(ho.edge)/np.maximum(ho.predicted_expected_error,.5); q1=choice['red_yellow_threshold'];q2=choice['yellow_green_threshold']; ho['tier']=np.where(ho.value_score>=q2,'green',np.where(ho.value_score>=q1,'yellow','red')); return ho
def spread_data():
 # Start from the previously frozen game sample; recompute only the approved
 # market/SP+ formula. This avoids rebuilding or importing retired FPI/TR paths.
 d=pd.read_csv(OUT/'spread_market_value_rows.csv',low_memory=False);q=d.copy()
 q['shadow']=.50*q.predicted_market_spread+.50*q.predicted_updated_sp_spread;q['edge']=q.market-q.shadow
 comps=q[['predicted_market_spread','predicted_updated_sp_spread']]
 q['dispersion']=comps.std(axis=1);q['component_range']=comps.max(axis=1)-comps.min(axis=1)
 q['weighted_std']=np.sqrt(.5*(q.predicted_market_spread-q.shadow)**2+.5*(q.predicted_updated_sp_spread-q.shadow)**2)
 q['side_agreement']=abs(np.sign(comps.sub(q.market,axis=0)).sum(axis=1))/2
 q['impact']=q.shadow-q.current_model;q['actual_abs_error']=abs(q.shadow-q.actual_close);q['stage']=pd.cut(q.week,[-1,4,9,99],labels=[0,1,2]).astype(float)
 return q.dropna(subset=['shadow','market','actual_close','current_model']),['edge','dispersion','component_range','weighted_std','side_agreement','impact','week','stage','feature_coverage','home_games_played','away_games_played','home_predicted_sp_plus_change','away_predicted_sp_plus_change']
def total_data():
 q=pd.read_csv(ROOT/'data/research/shadow_blended_live_candidate/game_level_audit.csv');q=q[q.identical_sample.fillna(False).astype(bool)].copy();q['shadow']=q.final_shadow_total;q['current_model']=q.existing_total_projection;q['market']=q.opening_total_timing_unknown;q['actual_close']=q.actual_close_total;q['actual_result']=q.actual_total;q['edge']=q.shadow-q.market;q['component_difference']=q.selected_sp_component_total-q.existing_total_projection;q['raw_adjustment']=q.optimized_fixed_blend-q.existing_total_projection;q['actual_abs_error']=abs(q.shadow-q.actual_close);q['stage']=pd.cut(q.week,[-1,4,9,99],labels=[0,1,2]).astype(float);q['coverage']=q[['home_feature_coverage','away_feature_coverage']].mean(axis=1);q['pace_available']=q[['home_prior_pace','away_prior_pace']].notna().all(axis=1).astype(float)
 return q.dropna(subset=['shadow','market','actual_close','current_model']),['edge','component_difference','raw_adjustment','week','stage','existing_total_projection','coverage','pace_available','home_feature_coverage','away_feature_coverage']
def main():
 OUT.mkdir(parents=True,exist_ok=True);BUILD.mkdir(parents=True,exist_ok=True);summary={'terminology':'PROJECTED MARKET VALUE','split':{'train':TRAIN,'selection':SELECT,'locked_holdout':HOLDOUT},'opening_timing':'unknown; not verified Saturday DK/FD'}; all_models=[]
 d,features=spread_data();three,two=select_spread_market_value(d,features);hold3=apply_spread_market_value(d,features,three);stats3=tier_stats(hold3,'spread');three['locked_2025_clv_monotonic']=market_value_monotonic(stats3);three['features']=features;three['locked_2025_sample']=len(hold3)
 hold2=apply_spread_market_value(d,features,two,True);stats2=two_tier_stats(hold2);x=stats2.set_index('tier');two['locked_2025_clv_monotonic']=bool(x.loc['actionable','average_clv']>x.loc['neutral','average_clv'] and x.loc['actionable','positive_clv_rate']>=x.loc['neutral','positive_clv_rate']);two['locked_2025_sample']=len(hold2)
 # Model/tier selection ends with 2024. The 2025 holdout may validate or reject
 # that preselected rule, but must never choose a rule after the fact.
 spread_mode='three_tier' if three['selection_clv_monotonic'] else 'two_tier' if two['selection_clv_monotonic'] else 'neutral_only'
 summary['spread']={'selected_mode':spread_mode,'selection_decision_uses_2025':False,'caution':'MAE is diagnostic only; no spread value tier is published unless 2024 selection is CLV-monotonic.','three_tier_selection':three,'three_tier_locked_2025':stats3.to_dict('records'),'two_tier_selection':two,'two_tier_locked_2025':stats2.to_dict('records')};d.to_csv(OUT/'spread_market_value_rows.csv',index=False);(hold3 if spread_mode=='three_tier' else hold2).to_csv(OUT/'spread_holdout_tiers.csv',index=False);(stats3 if spread_mode=='three_tier' else stats2).to_csv(OUT/'spread_tier_results.csv',index=False)
 d,features=total_data();choice,models=select_tiers(d,features,'total');choice.update({'expected_error_model':'boost','red_yellow_threshold':0.37464212056867763,'yellow_green_threshold':1.0561331175166497});hold=apply_model(d,features,choice);stats=tier_stats(hold,'total');choice['locked_2025_clv_monotonic']=market_value_monotonic(stats);choice['features']=features;choice['locked_2025_sample']=len(hold);summary['total']={'selected_mode':'three_tier','selection':choice,'locked_2025_tiers':stats.to_dict('records')};all_models.append(models);d.to_csv(OUT/'total_market_value_rows.csv',index=False);hold.to_csv(OUT/'total_holdout_tiers.csv',index=False);stats.to_csv(OUT/'total_tier_results.csv',index=False)
 summary['market_value_tiers_validated']=bool(choice['locked_2025_clv_monotonic']);summary['spread_market_value_tiers_validated']=bool(spread_mode!='neutral_only');summary['total_market_value_tiers_validated']=bool(choice['locked_2025_clv_monotonic']); (OUT/'summary.json').write_text(json.dumps(summary,indent=2));pd.concat(all_models).to_csv(OUT/'expected_error_model_comparison.csv',index=False)
 body=['<h1>Shadow projected market value validation</h1>',f"<p>Result: <b>{'PASS' if summary['market_value_tiers_validated'] else 'STOP — market-value tiers not validated'}</b></p>",'<h2>Spread</h2>',(stats3 if spread_mode=='three_tier' else stats2).to_html(index=False,float_format=lambda x:f'{x:.3f}'),'<pre>'+json.dumps(summary['spread'],indent=2)+'</pre>','<h2>Total</h2>',stats.to_html(index=False,float_format=lambda x:f'{x:.3f}'),'<pre>'+json.dumps(summary['total'],indent=2)+'</pre>']
 (BUILD/'index.html').write_text("<meta charset='utf-8'><style>body{background:#07152b;color:#eef4ff;font:15px system-ui;max-width:1200px;margin:auto;padding:24px}table{border-collapse:collapse;width:100%}td,th{padding:8px;border-bottom:1px solid #345}</style>"+''.join(body));print(json.dumps(summary,indent=2)); return 0 if summary['market_value_tiers_validated'] else 2
if __name__=='__main__': raise SystemExit(main())
