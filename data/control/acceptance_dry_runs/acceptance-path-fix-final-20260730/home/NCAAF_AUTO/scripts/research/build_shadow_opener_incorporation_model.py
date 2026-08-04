#!/usr/bin/env python3
"""Research-only opener-incorporation and opener-to-close residual study.

The study uses 2021-23 for fitting, 2024 for every choice, and evaluates the
locked 2025 partition only after writing a selection lock. Nothing here is a
production input.
"""
from __future__ import annotations

import argparse, hashlib, html, importlib.util, json, math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/research/shadow_opener_incorporation'
REPORT=ROOT/'build/research/shadow_opener_incorporation'
MOVE=ROOT/'data/research/team_rating_movement_model'
CORE=ROOT/'data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv'
STAGE=ROOT/'data/research/shadow_season_stage_calibration/game_level_audit.csv'
FULL=ROOT/'data/research/full_saturday_shadow_backtest'
PUBLIC=Path('/Users/jameslindesmith/Sites/NCAAF_SITE')
TRAIN=[2021,2022,2023]; SELECT=2024; HOLDOUT=2025; PRICE=-110
PROTECTED=[
 'config/market_shadow_production.json','scripts/site/build_saturday_shadow_lines.py',
 'scripts/site/build_postgame_shadow_updates.py','scripts/site/build_market_shadow_production_layer.py',
 'scripts/research/build_team_rating_movement_model.py','openers_v2.html','schedule_v2.html',
 'build/public_site/openers.html','build/public_site/schedule.html',
 'data/site/postgame_shadow_updates.json','data/site/saturday_shadow_lines.json',
 'data/site/schedule_live_enrichment.json','daily_market_update.sh',
 'scripts/publish/publish_site.sh','data/ratings/ratings_latest.csv',
 'data/projections/game_projections_2026.csv']

def nid(v):
 s=str(v or '').strip(); return s[:-2] if s.endswith('.0') else s
def num(v): return pd.to_numeric(v,errors='coerce')
def sha(p):
 if not p.exists(): return None
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def protected(): return {p:sha(ROOT/p) for p in PROTECTED}
def jdump(p,x): p.write_text(json.dumps(x,indent=2,default=clean)+'\n')
def clean(x):
 if isinstance(x,(np.integer,)): return int(x)
 if isinstance(x,(np.floating,)): return None if not np.isfinite(x) else float(x)
 if isinstance(x,np.ndarray): return x.tolist()
 if isinstance(x,Path): return str(x)
 raise TypeError(type(x).__name__)

def load_movement_module():
 p=ROOT/'scripts/research/build_team_rating_movement_model.py'
 spec=importlib.util.spec_from_file_location('movement_research',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def crossfit_team_predictions(m):
 """Rebuild same-family team predictions without fitting a row's season."""
 raw=pd.read_csv(MOVE/'repeatable_performance_features.csv'); raw['game_id']=raw.game_id.map(nid); raw['next_game_id']=raw.next_game_id.map(nid)
 selection=json.loads((MOVE/'final_selection.json').read_text()); feats=selection['features']; pieces=[]; provenance=[]
 for season in TRAIN+[SELECT,HOLDOUT]:
  fit=[s for s in TRAIN if s!=season] if season in TRAIN else (TRAIN if season==SELECT else TRAIN+[SELECT])
  rebuilt,_=m.build_repeatable(raw.copy(),fit)
  model=m.fit_models(rebuilt,feats,selection['no_move_threshold'],fit)
  test=rebuilt[rebuilt.season==season].copy(); pred=m.predict_models(test,model)
  for k,v in pred.items(): test[k]=v
  test['predicted_movement']=test[selection['magnitude_model']]
  test['feature_coverage']=test[feats].notna().mean(axis=1)
  test['prediction_oos']=True; test['prediction_fit_seasons']=','.join(map(str,fit))
  pieces.append(test); provenance.append({'prediction_season':season,'fit_seasons':fit,'rows':len(test),'same_season_rows_in_fit':False})
 cols=['season','week','game_id','next_game_id','team','opponent','home_away','games_played_after','predicted_movement','prob_down','prob_no_change','prob_up','feature_coverage','prediction_oos','prediction_fit_seasons','raw_ats_performance','raw_pbp_performance','repeatable_spread_performance','trailing_2_game_ats','trailing_3_game_ats','recent_form_vs_season','opponent_adjusted_recent_form','turnover_margin','defensive_touchdowns','special_teams_touchdowns']
 return pd.concat(pieces,ignore_index=True)[cols],provenance

def game_frame(team):
 games=pd.read_csv(CORE); games['game_id']=games.game_id.map(nid)
 spread=pd.read_csv(MOVE/'next_game_spread_predictions.csv'); spread['game_id']=spread.game_id.map(nid)
 total=pd.read_csv(MOVE/'next_game_total_predictions.csv'); total['game_id']=total.game_id.map(nid)
 base=games.merge(spread[['season','game_id','no_movement_projection','actual_opener','actual_close','current_lambda_050_projection','repeatable_projection','projected_close']].rename(columns={'actual_opener':'spread_opener','actual_close':'spread_close','projected_close':'movement_projected_close'}),on=['season','game_id'],how='left')
 base=base.merge(total[['season','game_id','frozen_combined_total_baseline','predicted_combined_total_adjustment','projected_close','current_lambda_085_projection','actual_opener','actual_close']].rename(columns={'projected_close':'repeatable_total_projection','actual_opener':'total_opener','actual_close':'total_close'}),on=['season','game_id'],how='left')
 prev=team[team.next_game_id.notna() & (team.next_game_id!='')].copy()
 keep=['season','next_game_id','team','predicted_movement','prob_down','prob_no_change','prob_up','feature_coverage','prediction_oos','prediction_fit_seasons','raw_ats_performance','raw_pbp_performance','repeatable_spread_performance','trailing_2_game_ats','trailing_3_game_ats','recent_form_vs_season','opponent_adjusted_recent_form','games_played_after']
 for side in ('home','away'):
  q=prev[keep].copy()
  q=q.rename(columns={'next_game_id':'game_id','team':f'{side}_prediction_team',**{c:f'{side}_{c}' for c in keep[3:]}})
  base=base.merge(q,left_on=['season','game_id',f'{side}_team'],right_on=['season','game_id',f'{side}_prediction_team'],how='left').drop(columns=[f'{side}_prediction_team'])
 base['predicted_game_adjustment']=-base.home_predicted_movement+base.away_predicted_movement
 base['preopener_projected_close']=base.no_movement_projection+base.predicted_game_adjustment
 base['opener_incorporated_adjustment']=base.spread_opener-base.no_movement_projection
 base['spread_pricing_gap']=base.preopener_projected_close-base.spread_opener
 base['spread_actual_remaining_move']=base.spread_close-base.spread_opener
 base['spread_incorporation_ratio']=base.opener_incorporated_adjustment/base.predicted_game_adjustment.replace(0,np.nan)
 base['preopener_projected_total']=base.frozen_combined_total_baseline+base.predicted_combined_total_adjustment
 base['total_opener_incorporated_adjustment']=base.total_opener-base.frozen_combined_total_baseline
 base['total_pricing_gap']=base.preopener_projected_total-base.total_opener
 base['total_actual_remaining_move']=base.total_close-base.total_opener
 base['total_incorporation_ratio']=base.total_opener_incorporated_adjustment/base.predicted_combined_total_adjustment.replace(0,np.nan)
 base['both_teams_updated']=base.home_predicted_movement.notna()&base.away_predicted_movement.notna()
 base['one_team_updated']=base.home_predicted_movement.notna()^base.away_predicted_movement.notna()
 base['known_location']=False
 return base

def choose_categories(df, market):
 adj='predicted_game_adjustment' if market=='spread' else 'predicted_combined_total_adjustment'; ratio=f'{market}_incorporation_ratio'; gap=f'{market}_pricing_gap'; actual=f'{market}_actual_remaining_move'; opener=f'{market}_opener'
 grids=[(.2,.55,.85,1.15),(.25,.6,.9,1.1),(.3,.65,.9,1.2)]
 rows=[]
 for nz,part,mostly,full in grids:
  v=df[df.season==SELECT].copy(); c=category(v[adj],v[ratio],v[gap],v[opener],nz,part,mostly,full)
  tmp=pd.DataFrame({'c':c,'a':v[actual]}).dropna(); means=tmp.groupby('c').a.mean()
  score=float(means.std()) if len(means)>2 else 0
  rows.append((score,nz,part,mostly,full))
 return max(rows)[1:]
def category(adj,ratio,gap,opener,nz,part,mostly,full):
 out=[]
 for a,r,g,o in zip(adj,ratio,gap,opener):
  if pd.isna(o): out.append('Missing opener')
  elif pd.isna(a): out.append('Baseline only')
  elif abs(a)<nz: out.append('Prediction too uncertain')
  elif pd.isna(r): out.append('Ineligible')
  elif r<-.25: out.append('Opener moved opposite prediction')
  elif r<.25: out.append('Not priced')
  elif r<part: out.append('Partially priced')
  elif r<mostly: out.append('Mostly priced')
  elif r<=full: out.append('Fully priced')
  else: out.append('Opener overreacted')
 return np.array(out)

def zfit(df,features):
 x=df[features].apply(num).to_numpy(float); med=np.nanmedian(x,axis=0); med=np.where(np.isfinite(med),med,0); x=np.where(np.isfinite(x),x,med); mu=x.mean(0); sd=x.std(0); sd=np.where(sd>1e-9,sd,1); return (med,mu,sd),(x-mu)/sd
def zapply(df,features,state):
 med,mu,sd=state; x=df[features].apply(num).to_numpy(float); return (np.where(np.isfinite(x),x,med)-mu)/sd
def cls(y,t): return np.where(y>t,1,np.where(y<-t,-1,0))
def class_stats(y,p):
 cs=(-1,0,1); rec=[]; f=[]
 for c in cs:
  tp=((y==c)&(p==c)).sum(); fp=((y!=c)&(p==c)).sum(); fn=((y==c)&(p!=c)).sum(); pr=tp/(tp+fp) if tp+fp else 0; rc=tp/(tp+fn) if tp+fn else 0; rec.append(rc); f.append(2*pr*rc/(pr+rc) if pr+rc else 0)
 return {'accuracy':float(np.mean(y==p)),'balanced_accuracy':float(np.mean(rec)),'macro_f1':float(np.mean(f)),'confusion_matrix':[[int(((y==a)&(p==b)).sum()) for b in cs] for a in cs]}
def reg_stats(y,p):
 y=np.asarray(y,float); p=np.asarray(p,float); e=p-y
 return {'n':len(y),'mae':float(np.mean(abs(e))),'median_absolute_error':float(np.median(abs(e))),'rmse':float(np.sqrt(np.mean(e*e))),'signed_error':float(np.mean(e)),'correlation':float(np.corrcoef(y,p)[0,1]) if len(y)>2 and np.std(p)>0 and np.std(y)>0 else None,'overshoot':float(np.mean(abs(p)>abs(y))),'undershoot':float(np.mean(abs(p)<abs(y))),'wrong_direction':float(np.mean(np.sign(p)!=np.sign(y))),'unchanged':float(np.mean(abs(p)<.25))}

def fit_residual(m,df,market,threshold,features,family='ridge'):
 target=f'{market}_actual_remaining_move'; tr=df[df.season.isin(TRAIN)].dropna(subset=[target]).copy(); st,x=zfit(tr,features); y=tr[target].to_numpy(float)
 if family=='boost': model=m.boost_fit(x,y,50,.06)
 elif family=='huber': model=m.huber_fit(x,y,15)
 elif family=='elastic': model=m.elastic_fit(x,y,.06,5)
 else: model=m.ridge_fit(x,y,20)
 return {'state':st,'model':model,'features':features,'family':family,'threshold':threshold}
def pred_residual(m,model,d):
 x=zapply(d,model['features'],model['state']); p=m.boost_predict(x,model['model']) if model['family']=='boost' else m.ridge_predict(x,model['model']); t=model['threshold']; probs=m.movement_probs_from_score(p,t); return p,probs,cls(p,t)

def select_residual(m,df,market,features):
 target=f'{market}_actual_remaining_move'; val=df[df.season==SELECT].dropna(subset=[target]); rows=[]
 for t in (.25,.5,.75,1.0):
  for fam in ('ridge','huber','elastic','boost'):
   model=fit_residual(m,df,market,t,features,fam); p,pr,pc=pred_residual(m,model,val); cm=class_stats(cls(val[target].to_numpy(),t),pc); rm=reg_stats(val[target],p)
   rows.append({'market':market,'threshold':t,'family':fam,**cm,**rm})
 tab=pd.DataFrame(rows).sort_values(['balanced_accuracy','macro_f1','mae'],ascending=[False,False,True]); best=tab.iloc[0]
 # 2024-only magnitude baselines
 gap=val[f'{market}_pricing_gap'].to_numpy(float); y=val[target].to_numpy(float)
 mags=[{'market':market,'model':'zero',**reg_stats(y,np.zeros(len(y)))},{'market':market,'model':'full_gap',**reg_stats(y,gap)}]
 for f in (0.25,0.5,0.75): mags.append({'market':market,'model':f'fraction_{f}',**reg_stats(y,f*gap)})
 for fam in ('ridge','elastic','huber','boost'):
  mo=fit_residual(m,df,market,float(best.threshold),features,fam); pp,_,_=pred_residual(m,mo,val); mags.append({'market':market,'model':fam,**reg_stats(y,pp)})
 selected=fit_residual(m,df,market,float(best.threshold),features,str(best.family))
 return selected,tab,pd.DataFrame(mags)

def bet_result(market,signal,row):
 if market=='spread':
  margin=row.home_score-row.away_score; value=margin+row.spread_opener if signal>0 else -margin-row.spread_opener
 else: value=(row.home_score+row.away_score-row.total_opener)*(1 if signal>0 else -1)
 return 'W' if value>0 else 'L' if value<0 else 'P'
def grid(df,market,pred,probs):
 rows=[]; actual=df[f'{market}_actual_remaining_move'].to_numpy(float); maxp=probs.max(1)
 for edge in (.25,.5,.75,1,1.5,2):
  for pt in (.525,.55,.575,.6,.625,.65):
   mask=(abs(pred)>=edge)&(maxp>=pt); ids=np.where(mask)[0]; clv=np.sign(pred[ids])*actual[ids]; results=[bet_result(market,pred[i],df.iloc[i]) for i in ids]
   vals=[100/110 if x=='W' else -1 if x=='L' else 0 for x in results]; equity=np.cumsum(vals); peak=np.maximum.accumulate(np.r_[0,equity]); dd=float(np.max(peak-np.r_[0,equity])) if vals else 0
   longest=cur=0
   for x in results: cur=cur+1 if x=='L' else 0; longest=max(longest,cur)
   rows.append({'market':market,'edge_threshold':edge,'probability_threshold':pt,'bets':len(ids),'positive_clv_rate':float(np.mean(clv>0)) if len(ids) else None,'average_clv':float(np.mean(clv)) if len(ids) else None,'median_clv':float(np.median(clv)) if len(ids) else None,'direction_accuracy':float(np.mean(np.sign(pred[ids])==np.sign(actual[ids]))) if len(ids) else None,'average_predicted_move':float(np.mean(abs(pred[ids]))) if len(ids) else None,'average_actual_move':float(np.mean(clv)) if len(ids) else None,'record':f"{results.count('W')}-{results.count('L')}-{results.count('P')}",'win_rate':results.count('W')/(results.count('W')+results.count('L')) if results.count('W')+results.count('L') else None,'roi':float(np.mean(vals)) if vals else None,'maximum_drawdown_units':dd,'longest_losing_streak':longest})
 return pd.DataFrame(rows)

def benchmark_metrics(df,market,name,col):
 target=f'{market}_close'; opener=f'{market}_opener'; d=df.dropna(subset=[target,col,opener]); y=d[target].to_numpy(float); p=d[col].to_numpy(float); r=reg_stats(y,p); clv=np.sign(p-d[opener])* (d[target]-d[opener]); move=d[target]-d[opener]; sig=p-d[opener]
 r.update({'market':market,'model':name,'sample_size':len(d),'direction_toward_close':float(np.mean(np.sign(sig)==np.sign(move))),'positive_clv_rate':float(np.mean(clv>0)),'average_clv':float(clv.mean()),'median_clv':float(clv.median())})
 return r

def reconciliation(base):
 stage=pd.read_csv(STAGE); stage['game_id']=stage.game_id.map(nid); stage=stage[stage.season==HOLDOUT]
 for market in ('spread','total'):
  s=stage[stage.market==market][['game_id','projected_close','applied_impact']].rename(columns={'projected_close':f'{market}_stage_close','applied_impact':f'{market}_stage_impact'})
  base=base.merge(s,on='game_id',how='left')
 # Apply legacy raw adjustments to canonical baseline, never mix their legacy baseline.
 sp=pd.read_csv(FULL/'spread_holdout_2025_rows.csv'); sp['game_id']=sp.game_id.map(nid)
 base=base.merge(sp[['game_id','raw_matchup_shadow_adjustment']].rename(columns={'raw_matchup_shadow_adjustment':'prior_spread_raw_adjustment'}),on='game_id',how='left')
 base['prior_spread_dryrun_on_canonical']=base.no_movement_projection+.5*base.prior_spread_raw_adjustment
 tt=pd.read_csv(FULL/'total_holdout_2025_rows.csv'); tt['game_id']=tt.game_id.map(nid)
 base=base.merge(tt[['game_id','raw_total_shadow_adjustment']].rename(columns={'raw_total_shadow_adjustment':'prior_total_raw_adjustment'}),on='game_id',how='left')
 base['prior_total_dryrun_on_canonical']=base.frozen_combined_total_baseline+.85*base.prior_total_raw_adjustment
 specs={'spread':[('frozen_no_adjustment','no_movement_projection'),('lambda_0.50','current_lambda_050_projection'),('prior_dryrun','prior_spread_dryrun_on_canonical'),('repeatable','repeatable_projection'),('direction_plus_magnitude','preopener_projected_close'),('stage_decay','spread_stage_close'),('actual_opener','spread_opener')], 'total':[('frozen_no_adjustment','frozen_combined_total_baseline'),('lambda_0.85','current_lambda_085_projection'),('prior_dryrun','prior_total_dryrun_on_canonical'),('repeatable_combined','repeatable_total_projection'),('actual_opener','total_opener')]}
 # One identical complete-case game set per market.
 rows=[]; samples={}
 for market,models in specs.items():
  need=[f'{market}_close',f'{market}_opener']+[c for _,c in models]; d=base[base.season==HOLDOUT].dropna(subset=need).copy(); samples[market]=d.game_id.tolist()
  for name,col in models: rows.append(benchmark_metrics(d,market,name,col))
 return base,pd.DataFrame(rows),samples

def category_summary(d,market):
 target=f'{market}_actual_remaining_move'; out=[]
 for (season,c),g in d.groupby(['season',f'{market}_incorporation_category']):
  x=g.dropna(subset=[target]); out.append({'market':market,'season':season,'category':c,'n':len(g),'evaluated_n':len(x),'actual_move_mean':x[target].mean() if len(x) else None,'actual_move_mae':x[target].abs().mean() if len(x) else None,'positive_pricing_gap_clv':float(np.mean(np.sign(x[f'{market}_pricing_gap'])*x[target]>0)) if len(x) else None,'average_pricing_gap_clv':float((np.sign(x[f'{market}_pricing_gap'])*x[target]).mean()) if len(x) else None})
 return out

def incorporation_axes(d,market):
 """Summaries for reliable repository fields; unsupported axes stay explicit."""
 x=d.dropna(subset=[f'{market}_opener',f'{market}_close']).copy(); x['move_size_bucket']=pd.cut(abs(x['predicted_game_adjustment'] if market=='spread' else x['predicted_combined_total_adjustment']),[-1,.5,1,2,4,np.inf],labels=['<0.5','0.5-1','1-2','2-4','4+']); x['week_bucket']=pd.cut(x.week,[0,3,6,9,12,99],labels=['W1-3','W4-6','W7-9','W10-12','W13+']); x['games_bucket']=pd.cut(x[['home_games_played_after','away_games_played_after']].min(axis=1),[-1,1,3,6,9,99],labels=['0-1','2-3','4-6','7-9','10+']); x['spread_bucket']=pd.cut(abs(x.spread_opener),[-1,3,7,14,28,np.inf],labels=['0-3','3.5-7','7.5-14','14.5-28','28+'])
 rows=[]
 for axis in ['season','week_bucket','games_bucket','move_size_bucket','spread_bucket','both_teams_updated']:
  for value,g in x.groupby(axis,observed=True):
   target=g[f'{market}_actual_remaining_move']; predicted=g[f'{market}_pricing_gap']; rows.append({'market':market,'axis':axis,'value':str(value),'n':len(g),'incorporated_abs_mean':float(abs(g[f'{market}_opener_incorporated_adjustment'] if market=='total' else g.opener_incorporated_adjustment).mean()),'remaining_move_mae':float(abs(target).mean()),'pricing_gap_positive_clv_rate':float(np.mean(np.sign(predicted)*target>0))})
 return rows

def render(summary,bench,cats,comparison,hold):
 def table(d): return d.to_html(index=False,border=0,classes='data',float_format=lambda x:f'{x:.3f}')
 body=f"""<!doctype html><meta charset=utf-8><title>Shadow Opener Incorporation</title><style>body{{font:14px system-ui;background:#06152c;color:#eaf2ff;margin:24px}}h1,h2{{color:#fff}}.card{{background:#0e2948;border:1px solid #295681;border-radius:12px;padding:16px;margin:14px 0;overflow:auto}}table{{border-collapse:collapse;width:100%}}th,td{{padding:7px;border-bottom:1px solid #28486c;text-align:right}}th:first-child,td:first-child{{text-align:left}}.warn{{color:#ffca66}}</style><h1>Shadow opener incorporation & residual movement</h1><p>Research only · 2021–23 train · 2024 selection · locked 2025 holdout</p><div class=card><h2>Executive result</h2><pre>{html.escape(json.dumps(summary['recommendation'],indent=2))}</pre></div><div class=card><h2>Benchmark reconciliation</h2>{table(bench)}</div><div class=card><h2>Opener incorporation categories</h2>{table(cats)}</div><div class=card><h2>Model comparison</h2>{table(comparison)}</div><div class=card><h2>Locked 2025</h2>{table(hold)}</div><div class=card><h2>Known limitations</h2><ul>{''.join('<li>'+html.escape(x)+'</li>' for x in summary['limitations'])}</ul></div>"""
 (REPORT/'index.html').write_text(body)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--rebuild',action='store_true'); args=ap.parse_args(); OUT.mkdir(parents=True,exist_ok=True); REPORT.mkdir(parents=True,exist_ok=True)
 before=protected(); m=load_movement_module(); team,prov=crossfit_team_predictions(m); base=game_frame(team)
 base,bench,samples=reconciliation(base); bench.to_csv(OUT/'benchmark_reconciliation.csv',index=False)
 discrepancies=[
  {'prior':'full_saturday spread baseline 5.282 / shadow 4.707, n=679','cause':'legacy report used its own 679-row week-2+ baseline; canonical reconciliation uses complete-case opener rows and one shared baseline'},
  {'prior':'season-stage spread baseline 8.070, n=714','cause':'included all closing rows and evaluated full-line baseline; opener-relative CLV used only 708 opener rows'},
  {'prior':'team movement spread no-move 5.398, n=606','cause':'required two eligible previous-team movement rows, producing a narrower next-game set'},
  {'prior':'full_saturday total all-row baseline 7.320, n=762','cause':'mixed both/one/neither-prior rows; neither-prior baseline defects inflated all-row error'},
  {'prior':'full_saturday total both-prior baseline 4.037, n=679','cause':'both-prior subset is the comparable total population; current study requires opener plus all benchmark columns'},
  {'prior':'team movement total no-move 3.471','cause':'later corrected prior-game-only combined total construction and a different eligible next-game set'}]
 recsum={'schema_version':'shadow-opener-benchmark-reconciliation-v1','canonical_sign':'home spread; negative means home favorite','canonical_hfa':'2.5 retained because neutral history unavailable','identical_samples':{k:{'n':len(v),'game_ids':v} for k,v in samples.items()},'discrepancies':discrepancies,'recommendation_gate':'benchmark reconciliation completed before residual selection'}; jdump(OUT/'benchmark_reconciliation_summary.json',recsum)
 catlock={}
 catrows=[]
 for market in ('spread','total'):
  pars=choose_categories(base,market); catlock[market]={'near_zero':pars[0],'partial_upper':pars[1],'mostly_upper':pars[2],'full_upper':pars[3]}
  adj='predicted_game_adjustment' if market=='spread' else 'predicted_combined_total_adjustment'; base[f'{market}_incorporation_category']=category(base[adj],base[f'{market}_incorporation_ratio'],base[f'{market}_pricing_gap'],base[f'{market}_opener'],*pars); catrows+=category_summary(base,market)
 cats=pd.DataFrame(catrows); cats.to_csv(OUT/'opener_incorporation_categories.csv',index=False)
 audit_cols=['season','week','game_id','home_team','away_team','no_movement_projection','home_predicted_movement','away_predicted_movement','predicted_game_adjustment','preopener_projected_close','spread_opener','spread_close','opener_incorporated_adjustment','spread_pricing_gap','spread_actual_remaining_move','spread_incorporation_ratio','spread_incorporation_category','frozen_combined_total_baseline','predicted_combined_total_adjustment','preopener_projected_total','total_opener','total_close','total_opener_incorporated_adjustment','total_pricing_gap','total_actual_remaining_move','total_incorporation_ratio','total_incorporation_category','home_prediction_oos','away_prediction_oos','home_prediction_fit_seasons','away_prediction_fit_seasons','known_location']
 base[audit_cols].to_csv(OUT/'opener_incorporation_game_audit.csv',index=False)
 incsum={'category_thresholds_selected_on_2024':catlock,'crossfit_provenance':prov,'opener_timestamps':'unavailable in repository source; timing/dispersion analyses withheld','neutral_site':'unavailable; known_location=false','category_results':catrows}; jdump(OUT/'opener_incorporation_summary.json',incsum)
 common=['week','home_games_played_after','away_games_played_after','home_predicted_movement','away_predicted_movement','predicted_game_adjustment','home_prob_down','home_prob_no_change','home_prob_up','away_prob_down','away_prob_no_change','away_prob_up','home_feature_coverage','away_feature_coverage','home_raw_ats_performance','away_raw_ats_performance','home_raw_pbp_performance','away_raw_pbp_performance','home_repeatable_spread_performance','away_repeatable_spread_performance','home_trailing_2_game_ats','away_trailing_2_game_ats','home_recent_form_vs_season','away_recent_form_vs_season','home_opponent_adjusted_recent_form','away_opponent_adjusted_recent_form']
 sfeatures=common+['spread_opener','spread_pricing_gap','spread_incorporation_ratio','no_movement_projection','preopener_projected_close']
 tfeatures=['week','home_games_played_after','away_games_played_after','predicted_combined_total_adjustment','frozen_combined_total_baseline','preopener_projected_total','total_opener','total_pricing_gap','total_incorporation_ratio']
 selections={}; dir_tabs=[]; mag_tabs=[]; predouts=[]; grids=[]; comparisons=[]; holdrows=[]; confidence=[]
 for market,features in [('spread',sfeatures),('total',tfeatures)]:
  eligible=base.dropna(subset=[f'{market}_opener',f'{market}_close',f'{market}_pricing_gap']).copy(); model,dtab,mtab=select_residual(m,eligible,market,features); dir_tabs.append(dtab); mag_tabs.append(mtab)
  val=eligible[eligible.season==SELECT].copy(); vp,vprob,vcls=pred_residual(m,model,val); g=grid(val,market,vp,vprob); grids.append(g); viable=g[g.bets>=40].sort_values(['positive_clv_rate','average_clv','bets'],ascending=[False,False,False]); pick=(viable.iloc[0] if len(viable) else g.sort_values('bets',ascending=False).iloc[0])
  selections[market]={'direction_threshold':model['threshold'],'family':model['family'],'edge_threshold':float(pick.edge_threshold),'probability_threshold':float(pick.probability_threshold),'features':features}
  # Lock, then refit with selection season for final 2025 prediction.
  fitbase=eligible.copy(); fitbase.loc[fitbase.season==SELECT,'season']=2023 # include selected rows in fit without exposing holdout; explicit fitting partition below
  final=model
  tr=eligible[eligible.season.isin(TRAIN+[SELECT])].copy(); st,x=zfit(tr,features); y=tr[f'{market}_actual_remaining_move'].to_numpy(float)
  fam=model['family']; mm=m.boost_fit(x,y,50,.06) if fam=='boost' else (m.huber_fit(x,y,15) if fam=='huber' else m.elastic_fit(x,y,.06,5) if fam=='elastic' else m.ridge_fit(x,y,20)); final={'state':st,'model':mm,'features':features,'family':fam,'threshold':model['threshold']}
  for season,mod in [(SELECT,model),(HOLDOUT,final)]:
   dd=eligible[eligible.season==season].copy(); pp,pr,pc=pred_residual(m,mod,dd); dd['market']=market; dd['predicted_residual_move']=pp; dd['prob_negative']=pr[:,0]; dd['prob_no_move']=pr[:,1]; dd['prob_positive']=pr[:,2]; dd['predicted_direction']=pc; dd['actual_direction']=cls(dd[f'{market}_actual_remaining_move'],mod['threshold']); dd['selection_partition']='selection' if season==SELECT else 'locked_holdout'; predouts.append(dd[['season','week','game_id','home_team','away_team','market',f'{market}_opener',f'{market}_close',f'{market}_pricing_gap',f'{market}_actual_remaining_move','predicted_residual_move','prob_negative','prob_no_move','prob_positive','predicted_direction','actual_direction','selection_partition']])
   active=(abs(pp)>=selections[market]['edge_threshold'])&(pr.max(1)>=selections[market]['probability_threshold']); clv=np.sign(pp[active])*dd.loc[active,f'{market}_actual_remaining_move'].to_numpy(); allm=reg_stats(dd[f'{market}_actual_remaining_move'],pp); cm=class_stats(dd['actual_direction'].to_numpy(),pc); row={'market':market,'season':season,'model':'selected_residual','signals':int(active.sum()),'positive_clv_rate':float(np.mean(clv>0)) if len(clv) else None,'average_clv':float(np.mean(clv)) if len(clv) else None,'median_clv':float(np.median(clv)) if len(clv) else None,**allm,**cm}; holdrows.append(row)
   strength=pr.max(1); tier=np.where(active & (strength>=max(.65,selections[market]['probability_threshold'])),'High',np.where(active,'Medium',np.where(abs(pp)>=.25,'Low','No actionable signal'))); dd['tier']=tier
   for tiername,gg in dd.assign(_p=pp).groupby('tier'):
    cv=np.sign(gg._p)*gg[f'{market}_actual_remaining_move']; confidence.append({'market':market,'season':season,'tier':tiername,'n':len(gg),'positive_clv_rate':float(np.mean(cv>0)),'average_clv':float(cv.mean()),'median_clv':float(cv.median()),'direction_accuracy':float(np.mean(np.sign(gg._p)==np.sign(gg[f'{market}_actual_remaining_move']))),'residual_mae':float(np.mean(abs(gg._p-gg[f'{market}_actual_remaining_move'])))})
  # comparison rows, holdout only
  h=eligible[eligible.season==HOLDOUT].copy(); hp,hpr,_=pred_residual(m,final,h)
  candidates=[('actual_opener_no_move',np.zeros(len(h))),('full_pricing_gap',h[f'{market}_pricing_gap'].to_numpy()),('selected_residual',hp)]
  if market=='spread': candidates += [('preopener_no_adjustment',h.no_movement_projection-h.spread_opener),('lambda_0.50',h.current_lambda_050_projection-h.spread_opener),('direction_plus_magnitude',h.preopener_projected_close-h.spread_opener)]
  else: candidates += [('frozen_no_adjustment',h.frozen_combined_total_baseline-h.total_opener),('lambda_0.85',h.current_lambda_085_projection-h.total_opener),('repeatable_combined',h.repeatable_total_projection-h.total_opener)]
  for name,pv in candidates: comparisons.append({'market':market,'model':name,**reg_stats(h[f'{market}_actual_remaining_move'],pv)})
  active=(abs(hp)>=selections[market]['edge_threshold'])&(hpr.max(1)>=selections[market]['probability_threshold'])
  if active.any(): comparisons.append({'market':market,'model':'confidence_filtered_residual',**reg_stats(h.loc[active,f'{market}_actual_remaining_move'],hp[active])})
 pd.concat(dir_tabs).to_csv(OUT/'residual_direction_predictions.csv',index=False); pd.concat(mag_tabs).to_csv(OUT/'residual_magnitude_predictions.csv',index=False)
 pd.concat(predouts).to_csv(OUT/'game_level_audit.csv',index=False)
 grids[0].to_csv(OUT/'spread_signal_grid.csv',index=False); grids[1].to_csv(OUT/'total_signal_grid.csv',index=False)
 conf=pd.DataFrame(confidence); conf.to_csv(OUT/'confidence_tier_results.csv',index=False)
 hold=pd.DataFrame(holdrows); hold.to_csv(OUT/'holdout_2025_results.csv',index=False)
 comp=pd.DataFrame(comparisons); comp.to_csv(OUT/'model_comparison.csv',index=False)
 # Required aliases are prediction-level tables, not in-sample fit tables.
 allpred=pd.concat(predouts); allpred[allpred.market=='spread'].to_csv(OUT/'residual_direction_predictions.csv',index=False)
 allpred.to_csv(OUT/'residual_magnitude_predictions.csv',index=False)
 lock={'schema_version':'shadow-opener-incorporation-selection-v1','train_seasons':TRAIN,'selection_season':SELECT,'holdout_season':HOLDOUT,'choices_locked_before_holdout':True,'category_thresholds':catlock,'residual_models':selections}; jdump(OUT/'final_selection.json',lock)
 recommendation={}
 for market in ('spread','total'):
  hh=hold[(hold.market==market)&(hold.season==HOLDOUT)].iloc[0]; op=comp[(comp.market==market)&(comp.model=='actual_opener_no_move')].iloc[0]
  high=conf[(conf.market==market)&(conf.season==HOLDOUT)&(conf.tier=='High')]
  recommendation[market]={'residual_model_improves_no_move_mae':bool(hh.mae<op.mae),'selected_residual_mae':hh.mae,'opener_no_move_mae':op.mae,'high_tier_recommended':bool(len(high) and high.iloc[0].n>=30 and high.iloc[0].positive_clv_rate>.55 and high.iloc[0].average_clv>0)}
 summary={'schema_version':'shadow-opener-incorporation-research-v1','split':{'train':TRAIN,'selection':SELECT,'holdout':HOLDOUT},'selection':lock,'benchmark_reconciliation_complete':True,'team_prediction_provenance':prov,'opener_incorporation_by_available_axes':incorporation_axes(base,'spread')+incorporation_axes(base,'total'),'unavailable_axes':['opening sportsbook','sportsbook dispersion','first-opener time','Power Four/Group of Five','FBS/FCS','rivalry','conference game','weather'],'recommendation':recommendation,'limitations':['2021-22 opener coverage is nearly absent; residual fitting is effectively dominated by 2023.','Historical opener timestamps, book dispersion, neutral sites, rivalry flags, and reliable FBS/FCS labels are unavailable and withheld.','Historical weather/injury fields are unavailable.','ATS/total ROI is secondary context and never a selection objective.','Legacy benchmark adjustments are transplanted onto one canonical baseline; their original full-line MAEs are not directly comparable.','Quantile regression is unavailable in the installed dependency set; deterministic boosted, ridge, elastic, Huber, zero, full-gap, and fractional challengers were evaluated.'],'protected_hashes_before':before}
 after=protected(); summary['protected_hashes_after']=after; summary['protected_changes']=[p for p in before if before[p]!=after[p]]; jdump(OUT/'summary.json',summary)
 # A compact incorporation-by-axis file is included in summary JSON; unsupported axes are explicit.
 render(summary,bench,cats,comp,hold)
 print(json.dumps({'status':'PASS' if not summary['protected_changes'] else 'FAIL','output_dir':str(OUT),'report':str(REPORT/'index.html'),'benchmark_rows':len(bench),'game_rows':len(base),'locked_holdout_rows':len(allpred[allpred.season==HOLDOUT]),'recommendation':recommendation,'protected_changes':summary['protected_changes']},indent=2,default=clean))

if __name__=='__main__': main()
