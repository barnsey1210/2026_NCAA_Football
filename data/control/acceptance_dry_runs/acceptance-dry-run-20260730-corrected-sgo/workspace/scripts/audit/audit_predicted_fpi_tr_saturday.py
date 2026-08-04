#!/usr/bin/env python3
"""Independent integrity audit for predicted FPI/TR Saturday research outputs."""
import json, subprocess, sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'data/research/predicted_fpi_tr_saturday'; PUB=Path('/Users/jameslindesmith/Sites/NCAAF_SITE')
def main():
 required=['source_target_rows.csv','feature_audit.csv','predicted_fpi.csv','predicted_teamrankings.csv','source_model_comparison.csv','predicted_ensemble_comparison.csv','oracle_comparison.csv','holdout_2025_results.csv','game_level_audit.csv','final_selection.json','summary.json']
 checks={f'{x}_exists':(OUT/x).exists() for x in required}; s=json.loads((OUT/'summary.json').read_text()); a=s['audit']; f=pd.read_csv(OUT/'feature_audit.csv'); h=pd.read_csv(OUT/'holdout_2025_results.csv'); p=pd.read_csv(OUT/'predicted_ensemble_comparison.csv'); o=pd.read_csv(OUT/'oracle_comparison.csv')
 checks.update({'genuine_lineespn_target':a['target_columns']['FPI'].startswith('lineespn'),'genuine_lineteamrank_target':a['target_columns']['TeamRankings'].startswith('lineteamrank'),'features_strictly_pre_target':bool((f.loc[f.cutoff_valid==True,'home_completed_week']<f.loc[f.cutoff_valid==True,'week']).all() and (f.loc[f.cutoff_valid==True,'away_completed_week']<f.loc[f.cutoff_valid==True,'week']).all()),'holdout_only_2025':set(h.season)=={2025},'oracle_not_in_saturday_table':not p.model.str.contains('oracle').any(),'oracle_explicitly_labeled':(o.availability=='oracle_only_not_saturday_available').any(),'identical_game_rows':not h[['season','week','game_id']].duplicated().any(),'protected_unchanged':a['protected_unchanged'],'publication_repo_clean':a['publication_repo_clean']})
 checks={k:bool(v) for k,v in checks.items()}; status='PASS' if all(checks.values()) else 'FAIL'; print(json.dumps({'status':status,'checks':checks,'eligible_rows_by_season':a['eligible_rows_by_season'],'recommendation':s['recommendation']},indent=2)); return 0 if status=='PASS' else 1
if __name__=='__main__': sys.exit(main())
