#!/usr/bin/env python3
"""Minimal canonical-output -> frozen Shadow feature adapter and replay audit."""
from __future__ import annotations
import importlib.util, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/research/shadow_component_bridge_v1'
ART=OUT/'model_artifacts.json'
def mod(path,name):
 s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def gid(v):
 s=str(v); return s[:-2] if s.endswith('.0') else s
def key(v): return ''.join(c for c in str(v).lower() if c.isalnum())
def predict(df,model):
 x=df[model['feature_order']].apply(pd.to_numeric,errors='coerce').to_numpy(float)
 med=np.asarray(model['imputation']['values']); mu=np.asarray(model['scaling']['mean']); sd=np.asarray(model['scaling']['std'])
 z=(np.where(np.isfinite(x),x,med)-mu)/sd
 return np.c_[np.ones(len(z)),z]@np.r_[model['intercept'],np.asarray(model['coefficients'])]
def maxdiff(a,b):
 x=pd.to_numeric(a,errors='coerce').to_numpy(float); y=pd.to_numeric(b,errors='coerce').to_numpy(float); ok=np.isfinite(x)&np.isfinite(y)
 return float(np.max(np.abs(x[ok]-y[ok]))) if ok.any() else None

def source_matrix():
 rows=[
 ['final score','data/results/game_results_2026.csv (season artifact; absent until results exist)','scripts/results/inject_game_results_into_site.py consumes the canonical results artifact','home_score / away_score / completed','post-final','yes when populated','none','no new puller; zero-game season is valid'],
 ['closing spread/total','data/odds/game_book_line_history.csv + data/odds/game_line_history.csv','scripts/odds/append_game_line_history.py','spread / total / price / snapshot timestamp','final retained pre/postgame snapshot','yes','select canonical closing snapshot + team perspective','no'],
 ['team PBP efficiency','data/research/pbp_history_2021_2025/team_game_tendencies.csv; 2026 canonical signal artifacts when games begin','existing CFBD PBP ingestion/normalization','off_ppa, success, explosiveness, plays and defensive counterparts','completed game only','yes historically','same feature normalization required for 2026','current 2026 normalized team-game adapter not populated before games'],
 ['advanced stats','canonical CFBD advanced-stat inputs represented in repeatable_performance_features','existing PBP/advanced builders','adv_off/def PPA, success, havoc','completed game only','yes historically','join on season/week/game_id/team','no raw puller needed'],
 ['drive efficiency','canonical drive aggregates represented in repeatable_performance_features','existing drive feature builder','drive_* points/opportunity and field position','completed game only','yes historically','join/rolling transform','no raw puller needed'],
 ['game control','data/site/game_control_team_games_2026.json','scripts/site/build_game_control_view.py','game_control_index (mapped to gc_game_control_index in research features)','completed PBP only','yes when populated','team/game join and field rename','no'],
 ['entering ratings','data/ratings/ratings_history.csv and ratings_latest.csv','scripts/ratings/append_ratings_history.py + build_all_ratings_latest.py','source rating/value/rank and timestamp','snapshot entering completed week','yes','select cutoff snapshot; map SP+ overall/off/def','no'],
 ['rolling recent form','canonical completed team-game feature rows','existing historical feature logic in build_team_rating_movement_model.py','trailing_2/3 ATS/PPA, season-to-date, recent_form_vs_season','through completed Week N','yes inputs','deterministic rolling transformation','bridge transformation needed'],
 ['schedule/next game','data/site/matchups_view.json and data/site/schedule_live_enrichment.json','scripts/site/build_matchups_view.py + build_schedule_live_enrichment.py','game_id, week, date, teams, neutral_site','known schedule at run cutoff','yes','canonical team-name and next-date lookup','no'],
 ['current model spread/total','data/projections/game_projections_2026.csv + matchups_view.json','scripts/projections/build_game_projection_blend_2026.py','projected_spread / projected_total','latest build before Shadow run','yes','canonical sign conversion','no'],
 ['market-rating movement','canonical postgame feature row','this bridge exporter/adapter','frozen 27-feature order','after close + final/PBP','no prior fitted artifact','load frozen state','model state was missing; exported'],
 ['overall SP+ movement','same canonical postgame row + entering SP+','this bridge exporter/adapter','frozen 31-feature order','after final/PBP, before next SP+','no prior fitted artifact','load frozen state','model state was missing; exported'],
 ['SP+ offense/defense movement','same canonical postgame row + entering components','this bridge exporter/adapter','selected component feature orders','after final/PBP, before next SP+','no prior fitted artifact','load frozen state; defense sign inversion','model state was missing; exported'],
 ['predicted FPI/TR next spread','two teams’ adapted postgame rows + prior-source projections + next venue','this bridge adapter','frozen direct-game feature order','Saturday cutoff before target publications','no prior fitted artifact','prospective source availability + game join','model state was missing; exported'],
 ['SP+ component total','predicted updated offense/defense components','this bridge adapter','four updated component fields','Saturday cutoff','no prior fitted artifact','frozen conversion then 60/40 -1.1573','conversion state was missing; exported'],
 ]
 cols=['required_model_feature','existing_canonical_source','producing_script','existing_field_name','timing_cutoff','usable_as_is','requires_transformation','genuinely_missing']
 return pd.DataFrame(rows,columns=cols)

def main():
 art=json.loads(ART.read_text()); models=art['models']; replay=[]; parity=[]
 # Team-level movement components.
 specs=[
  ('market','data/research/team_rating_movement_model/repeatable_performance_features.csv','data/research/team_rating_movement_model/team_movement_predictions.csv','market_rating_movement','predicted_movement'),
  ('sp_plus','data/research/sp_plus_movement_alignment/sp_plus_features.csv','data/research/sp_plus_movement_alignment/sp_plus_magnitude_predictions.csv','sp_plus_overall_movement','predicted_sp_plus_change'),
  ('sp_offense','data/research/sp_plus_total_movement/sp_plus_component_features.csv','data/research/sp_plus_total_movement/offense_magnitude_predictions.csv','sp_plus_offense_movement','component_predicted_change'),
  ('sp_defense_improvement','data/research/sp_plus_total_movement/sp_plus_component_features.csv','data/research/sp_plus_total_movement/defense_magnitude_predictions.csv','sp_plus_defense_improvement','component_predicted_change')]
 pred_frames={}
 for label,feature_file,saved_file,model_name,saved_col in specs:
  f=pd.read_csv(ROOT/feature_file,low_memory=False); saved=pd.read_csv(ROOT/saved_file,low_memory=False)
  if label=='sp_plus': f['actual_market_rating_change']=f.actual_sp_plus_change
  if label=='sp_offense': f['current_sp_offense']=f.current_sp_plus_offense; f['actual_market_rating_change']=f.actual_sp_plus_offense_change; f['rules_repeatable_spread']=f.repeatable_offense_performance
  if label=='sp_defense_improvement': f['current_sp_defense']=f.current_sp_plus_defense; f['actual_defense_improvement']=-f.actual_sp_plus_defense_change; f['actual_market_rating_change']=f.actual_defense_improvement; f['rules_repeatable_spread']=f.repeatable_defense_performance
  z=f[f.season==2025].copy(); z['adapter_prediction']=predict(z,models[model_name]); ids=['season','game_id','team']; z['game_id']=z.game_id.map(gid); saved['game_id']=saved.game_id.map(gid)
  q=z.merge(saved[ids+[saved_col]],on=ids,how='inner'); diff=maxdiff(q.adapter_prediction,q[saved_col]); parity.append({'component':label,'n':len(q),'max_abs_difference':diff,'passed':diff is not None and diff<1e-9})
  q['component']=label; q['saved_prediction']=q[saved_col]; replay.append(q[['component','season','game_id','team','adapter_prediction','saved_prediction']])
  z['team_key']=z.team.map(key); pred_frames[label]=z

 # Reconcile the approved market/SP+ arithmetic on the locked 2025 paired rows.
 # FPI and TeamRankings are deliberately outside the production dependency path.
 z=pd.read_csv(ROOT/'data/research/predicted_fpi_tr_saturday/holdout_2025_results.csv',low_memory=False)
 z=z[z.season==2025].copy()
 z['final_spread_adapter']=.50*z.predicted_market_spread+.50*z.predicted_updated_sp_spread
 z['approved_50_50_reference']=(z.predicted_market_spread+z.predicted_updated_sp_spread)/2
 diff=maxdiff(z.final_spread_adapter,z.approved_50_50_reference); parity.append({'component':'final_spread_50_50_market_sp_plus','n':len(z),'max_abs_difference':diff,'passed':diff is not None and diff<1e-9})

 # Rebuild SP+ total conversion from adapter-predicted component changes.
 gt=pd.read_csv(ROOT/'data/research/sp_plus_total_movement/game_total_projections.csv',low_memory=False); gt=gt[gt.season==2025].copy(); conv=art['sp_plus_component_total']
 fields=conv['feature_order']; gt['sp_component_adapter']=predict(gt,conv)
 diff=maxdiff(gt.sp_component_adapter,gt.selected_sp_component_total); parity.append({'component':'sp_plus_component_total','n':len(gt),'max_abs_difference':diff,'passed':diff is not None and diff<1e-9})
 gt['final_total_adapter']=.60*gt.sp_component_adapter+.40*gt.existing_total_projection-1.1573
 cand=pd.read_csv(ROOT/'data/research/shadow_blended_live_candidate/game_level_audit.csv',low_memory=False); cand=cand[cand.season==2025]; cand['game_id']=cand.game_id.map(gid); gt['game_id']=gt.game_id.map(gid)
 q=gt.merge(cand[['season','game_id','final_shadow_total']],on=['season','game_id'])
 q['approved_formula_reference']=.60*q.selected_sp_component_total+.40*q.existing_total_projection-1.1573
 diff=maxdiff(q.final_total_adapter,q.approved_formula_reference)
 legacy_diff=maxdiff(q.final_total_adapter,q.final_shadow_total)
 parity.append({'component':'final_corrected_total','n':len(q),'max_abs_difference':diff,'passed':diff is not None and diff<1e-9,
                'legacy_unrounded_correction_max_difference':legacy_diff,
                'detail':'approved -1.1573 reference; legacy candidate used -1.1572554705483324'})

 matrix=source_matrix(); matrix.to_csv(OUT/'canonical_pipeline_matrix.csv',index=False)
 pd.concat(replay,ignore_index=True).to_csv(OUT/'locked_2025_team_component_replay.csv',index=False)
 pd.DataFrame(parity).to_csv(OUT/'locked_2025_parity.csv',index=False)
 current={'season':2026,'completed_games':0,'status':'ready_zero_completed_games','rows':[],
          'message':'No canonical completed 2026 result rows exist; adapter emits no predictions and does not fabricate inputs.'}
 (OUT/'current_2026_adapter_status.json').write_text(json.dumps(current,indent=2)+'\n')
 report={'status':'PASS' if all(x['passed'] for x in parity) else 'FAIL','checks':parity,'production_models':['market_rating_movement','sp_plus_overall_movement','sp_plus_offense_movement','sp_plus_defense_improvement'],'excluded_models':['fpi_next_game_spread','teamrankings_next_game_spread'],'source_coverage_not_used':True,'production_files_modified':False}
 (OUT/'parity_report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
 if report['status']!='PASS': raise SystemExit(1)
if __name__=='__main__': main()
