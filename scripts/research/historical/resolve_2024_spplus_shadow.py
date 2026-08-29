#!/usr/bin/env python3
"""Resolve 2024 SP+ state semantics and apply the 2025 Shadow model OOS."""
from pathlib import Path
import gzip, importlib.util, json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'data/research/historical/shadow/strict_2024_readiness';OUT.mkdir(parents=True,exist_ok=True)
SP=ROOT/'data/import/sp_plus/espn_sp_plus_weekly_2021_2024.csv'
MATRIX=ROOT/'data/research/historical/historical_game_model_market_matrix_2021_2025.csv'
NEUTRAL=ROOT/'data/research/historical/stale_ratings/historical_canonical_neutral_site_flags_2021_2025.csv'
SAG=ROOT/'data/research/historical/stale_ratings/historical_sagarin_stale_pilot.csv'
F25=ROOT/'data/research/historical/shadow/historical_shadow_team_week_features_2025.csv'
ADV=Path('/Users/jameslindesmith/NCAAF_AUTO/cfbd_cache/pbp_history/2024/advanced_regular.json.gz')
FPIINV=ROOT/'data/research/historical/stale_ratings/fpi_2024_recovery/fpi_2024_panel_inventory.csv'
HFA=2.5;TARGET_WEEKS=[6,8,10]
SP_FEATURES=['margin_surprise_team','scoring_surprise_team','success_rate','ppa','explosiveness','def_success_rate_allowed','def_ppa_allowed','def_explosiveness_allowed']
SAG_FEATURES=['margin_surprise_team','scoring_surprise_team']

def helper():
 p=ROOT/'scripts/research/historical/build_stale_rating_recovery_pilot.py';s=importlib.util.spec_from_file_location('h',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def ridge(X,y,a=1):
 X=np.asarray(X,float);y=np.asarray(y,float);q=np.eye(X.shape[1])*a;q[0,0]=0;return np.linalg.solve(X.T@X+q,X.T@y)
def fit(d,target,features):
 q=d.dropna(subset=[target]+features);mu=q[features].mean();sd=q[features].std().replace(0,1).fillna(1);b=ridge(np.c_[np.ones(len(q)),((q[features]-mu)/sd)],q[target]);return mu,sd,b,len(q)
def predict(row,fit,features):
 mu,sd,b,n=fit
 if any(pd.isna(row.get(c)) for c in features):return np.nan
 return float(np.r_[1,[(row[c]-mu[c])/sd[c] for c in features]]@b)

def main():
 h=helper();sp=pd.read_csv(SP);sp=sp[sp.season.eq(2024)].copy();m=pd.read_csv(MATRIX,low_memory=False);m=m[m.season.eq(2024)].copy();neu=pd.read_csv(NEUTRAL)[['game_id','neutral_site']];m=m.merge(neu,on='game_id')
 # Each weekly article's records establish that state N incorporates Week N.
 inventory=[]
 for week,q in sp.groupby('snapshot_week'):
  records=q.record.dropna().astype(str);wins=pd.to_numeric(records.str.split('-').str[0],errors='coerce');losses=pd.to_numeric(records.str.split('-').str[1],errors='coerce')
  inventory.append({'season':2024,'state_week':int(week),'team_count':q.team.nunique(),'rating_columns':'sp_plus|offense|defense|special_teams','source_url':q.source_url.iloc[0],
   'archive_timestamp':'','publication_metadata':'ESPN article week label in source URL','teams_with_record':records.size,'median_games_in_record':(wins+losses).median() if len(records) else 0,
   'same_week_role':'POST_RESULTS_UPDATED' if week>0 else 'PRESEASON_BASELINE','following_week_role':'PRE_RESULTS_STALE','state_mapping_confidence':'DETERMINISTIC_STATE_MAPPING',
   'reasoning':'State Week N team records include results through repository Week N; sequential ratings change into N and the table is stale immediately before Week N+1 results.'})
 inv=pd.DataFrame(inventory).sort_values('state_week');inv.to_csv(OUT/'spplus_2024_state_inventory.csv',index=False)
 maps={int(w):{h.norm(r.team):r for r in q.itertuples()} for w,q in sp.groupby('snapshot_week')}
 # Formula diagnostic against Prediction Tracker's explicit state-week reference.
 diag=[]
 for g in m.dropna(subset=['pt_spplus_snapshot_week','pt_linespplus']).itertuples():
  sw=int(g.pt_spplus_snapshot_week);hm=maps.get(sw,{}).get(h.norm(g.home_team));am=maps.get(sw,{}).get(h.norm(g.away_team))
  if not hm or not am:continue
  pred=hm.sp_plus-am.sp_plus+(0 if g.neutral_site else HFA);err=pred-g.pt_linespplus
  diag.append({'game_id':g.game_id,'game_week':g.week,'state_week':sw,'home_team':g.home_team,'away_team':g.away_team,'neutral_site':g.neutral_site,'home_rating':hm.sp_plus,'away_rating':am.sp_plus,'formula_prediction':pred,'prediction_tracker_spplus':g.pt_linespplus,'error':err,'absolute_error':abs(err),'diagnostic_status':'STATE_IDENTITY_MATCH' if abs(err)<=0.11 else 'ROUNDING_OR_MAPPING_DIFFERENCE'})
 dd=pd.DataFrame(diag);dd.to_csv(OUT/'spplus_2024_prediction_tracker_formula_diagnostic.csv',index=False)
 # Dual-role mapping: the state two weeks behind a target is stale immediately
 # before the intervening Saturday whose update Shadow predicts.
 selections=[]
 for tw in range(2,17):
  sw=tw-2
  selections.append({'target_week':tw,'required_performance_week':tw-1,'stale_state_week':sw if sw in maps else np.nan,'updated_state_week':tw-1 if tw-1 in maps else np.nan,
   'stale_status':'PRE_RESULTS_STALE' if sw in maps else 'MISSING','updated_status':'POST_RESULTS_UPDATED' if tw-1 in maps else 'MISSING',
   'confidence':'DETERMINISTIC_STATE_MAPPING' if sw in maps else 'AMBIGUOUS'})
 pd.DataFrame(selections).to_csv(OUT/'spplus_2024_target_week_state_mapping.csv',index=False)

 # Freeze full-2025 provider-update models, then apply without any 2024 refit.
 train=pd.read_csv(F25);spfit=fit(train,'delta_spplus',SP_FEATURES);sagfit=fit(train,'delta_sagarin_predictor',SAG_FEATURES)
 with gzip.open(ADV,'rt') as f:adata=json.load(f)['data']
 advanced={(str(x['gameId']),h.norm(x['team'])):x for x in adata}
 sag=pd.read_csv(SAG);sag=sag[(sag.target_season==2024)&sag.target_week.isin(TARGET_WEEKS)]
 sagmaps={int(w):{r.team_key:r for r in q.itertuples()} for w,q in sag.groupby('target_week')}
 features=[]
 for g in m[m.week.isin([w-1 for w in TARGET_WEEKS])].itertuples():
  market_margin=-g.closing_home_spread;expected_home=(g.closing_total+market_margin)/2;expected_away=(g.closing_total-market_margin)/2
  for side,other in [('home','away'),('away','home')]:
   team=getattr(g,f'{side}_team');opp=getattr(g,f'{other}_team');score=getattr(g,f'{side}_score');oscore=getattr(g,f'{other}_score');actual=score-oscore;expected=market_margin if side=='home' else -market_margin
   a=advanced.get((str(g.game_id),h.norm(team)),{});off=a.get('offense',{});de=a.get('defense',{})
   row={'row_id':f'{g.game_id}:{team}','game_id':g.game_id,'team':team,'opponent':opp,'performance_week':int(g.week),'target_week':int(g.week)+1,
    'margin_surprise_team':actual-expected,'scoring_surprise_team':score-(expected_home if side=='home' else expected_away),
    'success_rate':off.get('successRate',np.nan),'ppa':off.get('ppa',np.nan),'explosiveness':off.get('explosiveness',np.nan),
    'def_success_rate_allowed':de.get('successRate',np.nan),'def_ppa_allowed':de.get('ppa',np.nan),'def_explosiveness_allowed':de.get('explosiveness',np.nan)}
   row['predicted_delta_spplus']=predict(row,spfit,SP_FEATURES);row['predicted_delta_sagarin_predictor']=predict(row,sagfit,SAG_FEATURES);features.append(row)
 feat=pd.DataFrame(features);feat['model_training_season']=2025;feat['model_refit_on_2024']=0;feat.to_csv(OUT/'shadow_2024_oos_team_predictions.csv',index=False)
 fidx={(int(r.target_week),h.norm(r.team)):r for r in feat.itertuples()};games=[]
 for g in m[m.week.isin(TARGET_WEEKS)].itertuples():
  tw=int(g.week);sw=tw-2;sm=maps.get(sw,{});sg=sagmaps.get(tw,{});hr=sm.get(h.norm(g.home_team));ar=sm.get(h.norm(g.away_team));hs=sg.get(h.norm(g.home_team));ass=sg.get(h.norm(g.away_team));hf=fidx.get((tw,h.norm(g.home_team)));af=fidx.get((tw,h.norm(g.away_team)))
  if not all([hr,ar,hs,ass,hf,af]):continue
  home=0 if g.neutral_site else HFA;shfa=0 if g.neutral_site else hs.provider_hfa
  stale_sp=-(hr.sp_plus-ar.sp_plus+home);shadow_sp=-((hr.sp_plus+hf.predicted_delta_spplus)-(ar.sp_plus+af.predicted_delta_spplus)+home)
  stale_sag=-(hs.predictor_rating-ass.predictor_rating+shfa);shadow_sag=-((hs.predictor_rating+hf.predicted_delta_sagarin_predictor)-(ass.predictor_rating+af.predicted_delta_sagarin_predictor)+shfa)
  games.append({'game_id':g.game_id,'season':2024,'target_week':tw,'home_team':g.home_team,'away_team':g.away_team,'neutral_site':g.neutral_site,'spplus_stale_state_week':sw,'sagarin_snapshot_id':hs.snapshot_id,
   'stale_spplus_fair_spread':stale_sp,'shadow_spplus_fair_spread':shadow_sp,'stale_sagarin_fair_spread':stale_sag,'shadow_sagarin_fair_spread':shadow_sag,
   'stale_spplus_sagarin':(stale_sp+stale_sag)/2,'shadow_spplus_sagarin':(shadow_sp+shadow_sag)/2,'model_training_season':2025,'model_refit_on_2024':0,'timing_status':'DETERMINISTIC_SPPLUS_AND_VERIFIED_SAGARIN'})
 out=pd.DataFrame(games);out.to_csv(OUT/'strict_2024_stale_shadow_spplus_sagarin.csv',index=False)
 summary={'distinct_spplus_states':int(inv.state_week.nunique()),'formula_diagnostic_games':len(dd),'formula_mae':float(dd.absolute_error.mean()),'formula_exact_within_0_11':int((dd.absolute_error<=.11).sum()),
  'deterministic_spplus_stale_target_weeks':pd.DataFrame(selections).query("stale_status=='PRE_RESULTS_STALE'").target_week.tolist(),'oos_shadow_games':len(out),'oos_shadow_weeks':sorted(out.target_week.unique().tolist()) if len(out) else [],
  'spplus_training_rows':spfit[3],'sagarin_training_rows':sagfit[3],'refit_on_2024':False}
 (OUT/'spplus_2024_semantics_shadow_audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
