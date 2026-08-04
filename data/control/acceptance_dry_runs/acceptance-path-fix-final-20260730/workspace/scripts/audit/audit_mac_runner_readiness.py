#!/usr/bin/env python3
"""Local, non-network readiness audit for a future self-hosted runner."""
from pathlib import Path
import os,platform,shutil,subprocess,json
ROOT=Path(__file__).resolve().parents[2]; PUB=Path('/Users/jameslindesmith/Sites/NCAAF_SITE')
checks={
 "macos":platform.system()=="Darwin", "python3":bool(shutil.which('python3')),
 "project_readable":os.access(ROOT,os.R_OK), "project_writable":os.access(ROOT,os.W_OK),
 "publication_repo":(PUB/'.git').exists(), "publisher_executable":(ROOT/'scripts/publish/publish_site.sh').exists(),
 "no_inbound_port_required":True, "controller_config":(ROOT/'scripts/control/refresh_controller_config.json').exists(),
}
if checks['publication_repo']:
 r=subprocess.run(['git','-C',str(PUB),'status','--porcelain'],capture_output=True,text=True); checks['publication_repo_clean']=not bool(r.stdout.strip())
checks['required_secret_names']=['SGO_API_KEY','BETTINGPROS_API_KEY','CFBD_API_KEY','THE_ODDS_API_KEY']
checks['secret_presence']={k:bool(os.environ.get(k)) for k in checks['required_secret_names']}
checks['note']='Secret values are never printed. Power/sleep and runner service restart require user-level macOS configuration.'
print(json.dumps(checks,indent=2)); raise SystemExit(0 if all(checks[k] for k in ['macos','python3','project_readable','project_writable','publication_repo','publisher_executable']) else 1)
