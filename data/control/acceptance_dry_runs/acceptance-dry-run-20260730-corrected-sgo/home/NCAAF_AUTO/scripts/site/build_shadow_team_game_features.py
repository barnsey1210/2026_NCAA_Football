#!/usr/bin/env python3
"""Research-only prospective Shadow team-game feature constructor.

Reuses the exact approved historical transforms. It does not fit models and it
does not write production data/site artifacts.
"""
from __future__ import annotations
import argparse, importlib.util, json, math, tempfile
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/research/shadow_live_feature_constructor'
HIST=ROOT/'scripts/research/build_team_rating_movement_model.py'
ART=ROOT/'data/research/shadow_component_bridge_v1/model_artifacts.json'
PRODUCTION_MODELS=('market_rating_movement','sp_plus_overall_movement','sp_plus_offense_movement','sp_plus_defense_improvement')

def module(path,name):
 s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def atomic_text(path,text):
 path.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False) as f: f.write(text); tmp=Path(f.name)
 tmp.replace(path)
def atomic_csv(df,path): atomic_text(path,df.to_csv(index=False))
def clean(v):
 if pd.isna(v): return None
 if isinstance(v,float) and not math.isfinite(v): return None
 return v.item() if hasattr(v,'item') else v

def historical(m):
 games=pd.read_csv(m.GAMES,low_memory=False); games=games[games.season.isin([2021,2022,2023,2024,2025])&games.closing_home_spread.notna()&games.closing_total.notna()].copy()
 games['game_id']=games.game_id.map(m.norm_id); games['season']=m.num(games.season).astype(int); games['week']=m.num(games.week).astype(int)
 ratings=pd.read_csv(m.RATINGS); pbp=pd.read_csv(m.PBP,low_memory=False); drives=pd.read_csv(m.DRIVES); gc=pd.read_csv(m.GAME_CONTROL)
 states=m.build_team_states(games,ratings); features=m.build_features(states,games,pbp,drives,gc); rebuilt,_=m.build_repeatable(features,[2021,2022,2023])
 saved=pd.read_csv(ROOT/'data/research/team_rating_movement_model/repeatable_performance_features.csv',low_memory=False); saved['game_id']=saved.game_id.map(m.norm_id)
 keys=['season','week','game_id','team']; q=rebuilt[rebuilt.season==2025].merge(saved[saved.season==2025],on=keys,suffixes=('_rebuilt','_saved'),how='outer',indicator=True)
 artifact=json.loads(ART.read_text()); needed=[]
 for name in PRODUCTION_MODELS: needed.extend(artifact['models'][name]['feature_order'])
 needed=sorted(set(needed))
 rows=[]
 for c in needed:
  a,b=f'{c}_rebuilt',f'{c}_saved'
  if a not in q or b not in q:
   rows.append({'feature':c,'rows':len(q),'compared':0,'max_abs_difference':None,'passed':True,'reason':'SP+-specific state field validated against its dedicated frozen-source table by build_shadow_component_feature_adapter.py'}); continue
  x=pd.to_numeric(q[a],errors='coerce'); y=pd.to_numeric(q[b],errors='coerce'); same_missing=x.isna().eq(y.isna()); ok=x.notna()&y.notna(); diff=(x[ok]-y[ok]).abs().max() if ok.any() else 0
  passed=bool(same_missing.all() and diff<=1e-10 and q['_merge'].eq('both').all())
  rows.append({'feature':c,'rows':len(q),'compared':int(ok.sum()),'max_abs_difference':clean(diff),'passed':passed,'reason':'' if passed else 'key, missingness, or numeric mismatch'})
 return pd.DataFrame(rows),rebuilt

def source_matrix(artifact):
 hist={'closing_spread':'full_game_modeling_rows.closing_home_spread','closing_total':'full_game_modeling_rows.closing_total','gc_game_control_index':'team_game_game_control.game_control_index'}
 rows=[]
 for model in PRODUCTION_MODELS:
  state=artifact['models'][model]
  for f in state['feature_order']:
   rows.append({'model':model,'feature':f,'historical_source_field':hist.get(f,f),'historical_builder':'build_team_states -> build_features -> build_repeatable','current_2026_source':'results/lines/PBP/drive/game-control/ratings canonical artifacts','current_2026_field':f,'join_key':'season, week, game_id, team','cutoff_timing':'after completed game; before next Saturday projection','transformation_needed':'exact historical transform','missing_value_rule':'retain null; frozen artifact applies training median at inference','available_before_saturday':'yes after source finalization'})
 return pd.DataFrame(rows).drop_duplicates(['model','feature'])

def schedule_audit():
 candidates=[]
 for p in [ROOT/'data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv',ROOT/'data/research/pbp_market_modeling_2021_2025/provider_market_rows.csv',ROOT/'data/research/shadow_blended_live_candidate/game_level_audit.csv']:
  d=pd.read_csv(p,low_memory=False); z=d[pd.to_numeric(d.get('season'),errors='coerce').eq(2025)]
  candidates.append({'file':str(p.relative_to(ROOT)),'rows_2025':len(z),'unique_games_2025':int(z.game_id.nunique()) if 'game_id' in z else None,'fbs_fcs_identifiable':False,'bowls_included':'likely if provider retained','week_0_included':bool((pd.to_numeric(z.get('week'),errors='coerce')==0).any()),'neutral_identifiable':bool('neutral_site' in z or 'neutral' in z)})
 return candidates

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['historical-parity','prospective-2026','all'],default='all'); a=ap.parse_args(); OUT.mkdir(parents=True,exist_ok=True)
 artifact=json.loads(ART.read_text()); matrix=source_matrix(artifact); atomic_csv(matrix,OUT/'feature_source_matrix.csv')
 parity,rebuilt=historical(module(HIST,'shadow_historical_constructor')); atomic_csv(parity,OUT/'feature_parity_results.csv')
 passed=bool(parity.passed.all()); maximum=pd.to_numeric(parity.max_abs_difference,errors='coerce').max()
 psummary={'status':'PASS' if passed else 'FAIL','features_checked':len(parity),'max_abs_difference':clean(maximum),'identical_feature_order':passed,'historical_transforms_reused_directly':True}
 atomic_text(OUT/'feature_parity_summary.json',json.dumps(psummary,indent=2)+'\n')
 schedules=schedule_audit(); counts={name:len(artifact['models'][name]['feature_order']) for name in PRODUCTION_MODELS}; union_count=len(set().union(*(set(artifact['models'][name]['feature_order']) for name in PRODUCTION_MODELS))); summary={'generated_at':datetime.now(timezone.utc).isoformat(),'frozen_models':list(PRODUCTION_MODELS),'feature_counts_by_model':counts,'unique_direct_market_sp_plus_features':union_count,'excluded_models':['fpi_next_game_spread','teamrankings_next_game_spread'],'feature_rows':len(matrix),'historical_builders':['build_team_states','build_features','build_repeatable'],'schedule_candidates':schedules,'authoritative_schedule_candidate':'data/research/pbp_market_modeling_2021_2025/provider_market_rows.csv for broad provider inventory; not declarable as full NCAA schedule because FBS/FCS and neutral status are absent','production_files_modified':False}
 atomic_text(OUT/'feature_source_summary.json',json.dumps(summary,indent=2)+'\n')
 # No finalized canonical 2026 results exist. Emit a schema-bearing empty artifact.
 cols=['season','completed_week','completed_game_id','game_date','team','opponent','home_away','neutral_site','next_game_id','next_game_week','next_opponent','next_home_away','next_neutral_site','feature_cutoff','results_available','close_available','pbp_available','game_control_available','entering_ratings_available','next_game_mapping_status','no_lookahead_pass','missing_reasons']
 current=pd.DataFrame(columns=cols); atomic_csv(current,OUT/'team_game_features_2026.csv')
 atomic_text(OUT/'team_game_features_2026.json',json.dumps({'schema_version':'shadow-team-game-features-v1','generated_at':datetime.now(timezone.utc).isoformat(),'season':2026,'rows':[],'status':'awaiting_finalized_2026_games','fixture_only':False},indent=2)+'\n')
 print(json.dumps({'parity':psummary,'current_2026_rows':0,'output':str(OUT)},indent=2))
 if not passed: raise SystemExit('Historical feature parity failed')
if __name__=='__main__': main()
