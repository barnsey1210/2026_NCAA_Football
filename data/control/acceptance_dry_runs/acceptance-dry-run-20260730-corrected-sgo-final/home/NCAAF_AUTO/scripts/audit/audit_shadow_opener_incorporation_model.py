#!/usr/bin/env python3
"""Strict audit for the isolated Shadow opener-incorporation research study."""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/research/shadow_opener_incorporation'
REPORT=ROOT/'build/research/shadow_opener_incorporation/index.html'
PUBLIC=Path('/Users/jameslindesmith/Sites/NCAAF_SITE')
REQUIRED=['benchmark_reconciliation.csv','benchmark_reconciliation_summary.json','opener_incorporation_game_audit.csv','opener_incorporation_categories.csv','opener_incorporation_summary.json','residual_direction_predictions.csv','residual_magnitude_predictions.csv','spread_signal_grid.csv','total_signal_grid.csv','confidence_tier_results.csv','holdout_2025_results.csv','model_comparison.csv','game_level_audit.csv','final_selection.json','summary.json']

def sha(p):
 if not p.exists(): return None
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def check(ok,name,detail,rows): rows.append({'status':'PASS' if ok else 'FAIL','check':name,'detail':detail}); print(f"{'PASS' if ok else 'FAIL'} | {name} | {detail}")

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--strict',action='store_true'); a=ap.parse_args(); rows=[]
 check(all((D/f).exists() for f in REQUIRED),'required artifacts present',f"{sum((D/f).exists() for f in REQUIRED)}/{len(REQUIRED)}",rows)
 summary=json.loads((D/'summary.json').read_text()); lock=json.loads((D/'final_selection.json').read_text()); rec=json.loads((D/'benchmark_reconciliation_summary.json').read_text())
 check(summary['split']=={'train':[2021,2022,2023],'selection':2024,'holdout':2025},'strict temporal split declared',str(summary['split']),rows)
 check(lock.get('choices_locked_before_holdout') is True,'selection lock precedes holdout','true',rows)
 prov=summary['team_prediction_provenance']; oos=all(not x['same_season_rows_in_fit'] and x['prediction_season'] not in x['fit_seasons'] for x in prov)
 check(oos,'team movement predictions genuinely out of sample',json.dumps(prov),rows)
 audit=pd.read_csv(D/'opener_incorporation_game_audit.csv',dtype={'game_id':str}); eligible=audit.dropna(subset=['home_predicted_movement','away_predicted_movement'])
 check(eligible.home_prediction_oos.fillna(False).all() and eligible.away_prediction_oos.fillna(False).all(),'game rows use cross-fitted movement predictions',f'n={len(eligible)}',rows)
 spread_sign=np.nanmax(np.abs(audit.preopener_projected_close-(audit.no_movement_projection-audit.home_predicted_movement+audit.away_predicted_movement)))<1e-8
 check(spread_sign,'spread sign formula exact','baseline - home change + away change',rows)
 gap_ok=np.nanmax(np.abs(audit.spread_pricing_gap-(audit.preopener_projected_close-audit.spread_opener)))<1e-8
 check(gap_ok,'spread pricing gap exact','projected close - opener',rows)
 total_ok=np.nanmax(np.abs(audit.preopener_projected_total-(audit.frozen_combined_total_baseline+audit.predicted_combined_total_adjustment)))<1e-8
 check(total_ok,'combined total formula exact','baseline + one combined adjustment',rows)
 totals=pd.read_csv(ROOT/'data/research/team_rating_movement_model/next_game_total_predictions.csv',dtype={'game_id':str,'home_previous_game_id':str,'away_previous_game_id':str}); feat=pd.read_csv(ROOT/'data/research/team_rating_movement_model/repeatable_performance_features.csv',dtype={'game_id':str})
 def norm(s): return s.astype(str).str.replace(r'\.0$','',regex=True)
 totals['game_id']=norm(totals.game_id); totals['home_previous_game_id']=norm(totals.home_previous_game_id); totals['away_previous_game_id']=norm(totals.away_previous_game_id); feat['game_id']=norm(feat.game_id)
 hp=feat[['season','game_id','team','total_residual']].rename(columns={'game_id':'home_previous_game_id','team':'home_team','total_residual':'home_prior_total_residual'}); ap=feat[['season','game_id','team','total_residual']].rename(columns={'game_id':'away_previous_game_id','team':'away_team','total_residual':'away_prior_total_residual'})
 z=totals.merge(hp,on=['season','home_previous_game_id','home_team'],how='left').merge(ap,on=['season','away_previous_game_id','away_team'],how='left'); expected=z.frozen_combined_total_baseline+.85*(z.home_prior_total_residual.fillna(0)+z.away_prior_total_residual.fillna(0))/2
 reproduced=(z.current_lambda_085_projection-expected).abs().max()<1e-8
 check(reproduced,'lambda 0.85 total benchmark reproduced','baseline + .85 * mean(prior team total residuals)',rows)
 check(not any(c.startswith('predicted_home_total') or c.startswith('predicted_away_total') for c in audit.columns),'no fabricated team-side total movement','combined only',rows)
 b=pd.read_csv(D/'benchmark_reconciliation.csv'); identical=all(g.sample_size.nunique()==1 and int(g['n'].iloc[0])==int(g.sample_size.iloc[0]) for _,g in b.groupby('market'))
 check(identical,'benchmark models use identical rows',str(b.groupby('market').sample_size.unique().to_dict()),rows)
 check(all(rec['identical_samples'][m]['n']==int(b[b.market==m].sample_size.iloc[0]) for m in ('spread','total')),'benchmark sample manifest matches metrics','spread/total',rows)
 check(len(rec.get('discrepancies',[]))>=6,'prior discrepancies explicitly reconciled',f"{len(rec.get('discrepancies',[]))} causes",rows)
 gl=pd.read_csv(D/'game_level_audit.csv',dtype={'game_id':str}); dupe=gl.duplicated(['season','game_id','market']).sum()
 check(dupe==0,'no duplicate residual predictions',f'duplicates={dupe}',rows)
 check(set(gl.selection_partition.unique())=={'selection','locked_holdout'},'prediction partitions explicit',str(sorted(gl.selection_partition.unique())),rows)
 check(not ((gl.season==2025)&(gl.selection_partition!='locked_holdout')).any(),'2025 used only as locked holdout',f"rows={(gl.season==2025).sum()}",rows)
 sg=pd.read_csv(D/'spread_signal_grid.csv'); tg=pd.read_csv(D/'total_signal_grid.csv'); expected_edges={.25,.5,.75,1,1.5,2}; expected_prob={.525,.55,.575,.6,.625,.65}
 check(set(sg.edge_threshold)==expected_edges and set(tg.edge_threshold)==expected_edges,'all edge thresholds evaluated',str(sorted(expected_edges)),rows)
 check(set(sg.probability_threshold)==expected_prob and set(tg.probability_threshold)==expected_prob,'all probability thresholds evaluated',str(sorted(expected_prob)),rows)
 comp=pd.read_csv(D/'model_comparison.csv'); check({'spread','total'}==set(comp.market) and 'actual_opener_no_move' in set(comp.model),'locked model comparison complete',f'rows={len(comp)}',rows)
 conf=pd.read_csv(D/'confidence_tier_results.csv'); check(set(conf.season)=={2024,2025},'confidence selected then held out','2024 and 2025',rows)
 check(REPORT.exists() and REPORT.stat().st_size>2000,'local HTML report present',str(REPORT),rows)
 before=summary['protected_hashes_before']; after=summary['protected_hashes_after']; now={p:sha(ROOT/p) for p in before}; changed=[p for p in before if before[p]!=after[p] or before[p]!=now[p]]
 check(not changed,'protected production files unchanged',str(changed or 'none'),rows)
 status=subprocess.run(['git','-C',str(PUBLIC),'status','--short'],capture_output=True,text=True)
 check(status.returncode==0 and not status.stdout.strip(),'publication repository clean',status.stdout.strip() or 'clean',rows)
 check(summary['recommendation']['spread']['high_tier_recommended'] is False and summary['recommendation']['total']['high_tier_recommended'] is False,'no unsupported confidence recommendation','both false',rows)
 pd.DataFrame(rows).to_csv(D/'audit_results.csv',index=False)
 fails=sum(r['status']=='FAIL' for r in rows); print(f"\nAUDIT {'PASS' if fails==0 else 'FAIL'}: {len(rows)-fails}/{len(rows)} checks passed")
 raise SystemExit(1 if fails and a.strict else 0)
if __name__=='__main__': main()
