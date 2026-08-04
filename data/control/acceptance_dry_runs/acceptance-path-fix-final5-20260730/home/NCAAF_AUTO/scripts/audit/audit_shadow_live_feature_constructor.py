#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'data/research/shadow_live_feature_constructor'; PUB=Path('/Users/jameslindesmith/Sites/NCAAF_SITE')
def main():
 failures=[]; p=json.loads((OUT/'feature_parity_summary.json').read_text()); cur=json.loads((OUT/'team_game_features_2026.json').read_text()); src=json.loads((OUT/'feature_source_summary.json').read_text())
 if p.get('status')!='PASS': failures.append('historical parity failed')
 if cur.get('rows')!=[] or cur.get('status')!='awaiting_finalized_2026_games': failures.append('zero-row 2026 behavior failed')
 if cur.get('fixture_only') is not False: failures.append('fixture guard absent')
 if src.get('production_files_modified') is not False: failures.append('production modification flag')
 pub=subprocess.run(['git','-C',str(PUB),'status','--porcelain'],capture_output=True,text=True)
 if pub.returncode or pub.stdout.strip(): failures.append('publication repository not clean')
 report={'status':'FAIL' if failures else 'PASS','historical_parity':p,'current_2026_rows':len(cur.get('rows',[])),'no_future_data_leakage':'exact historical cutoff transforms reused; no 2026 rows without final games','week_0_1':'explicitly unavailable until a prior finalized game exists','byes':'historical next_game_id uses chronological shift, not week+1','fbs_fcs':'retained when canonical identities exist; classification unavailable historically','neutral_site':'historical source lacks flag and records this limitation','publication_repo_clean':not bool(pub.stdout.strip()),'failures':failures}
 (OUT/'constructor_audit.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2)); raise SystemExit(1 if failures else 0)
if __name__=='__main__': main()
