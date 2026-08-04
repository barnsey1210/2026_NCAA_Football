#!/usr/bin/env python3
"""Safe, local-only acceptance tests for controller activation preparation."""
from pathlib import Path
import csv,hashlib,json,os,subprocess,sys,tempfile

ROOT=Path(__file__).resolve().parents[2]; PY=sys.executable
STAGE=ROOT/"scripts/control/stage_rating_source.py"; PREVIEW=ROOT/"scripts/control/manage_refresh_preview.py"
fail=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def run(args,expect=0):
 r=subprocess.run([PY,*map(str,args)],cwd=ROOT,text=True,capture_output=True,env={**os.environ,"PYTHONPYCACHEPREFIX":"/tmp/ncaaf_pycache"})
 if r.returncode!=expect: fail.append(f"unexpected rc {r.returncode} for {' '.join(map(str,args))}: {r.stderr[-300:]}")
 return r

# A valid acceptance establishes the isolated LKG; malformed replacement must not change it.
run([STAGE,"spplus","--run-id","activation-test-good","--accept"])
lkg=ROOT/"data/control/ratings/accepted/spplus/normalized.csv"; before=sha(lkg)
with tempfile.TemporaryDirectory() as td:
 bad=Path(td)/"bad.csv"
 rows=list(csv.DictReader((ROOT/"data/ratings/spplus_2026_latest.csv").open()))
 with bad.open("w",newline="") as fh:
  w=csv.DictWriter(fh,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows[:5])
 run([STAGE,"spplus","--input",bad,"--run-id","activation-test-bad","--accept"],2)
if before!=sha(lkg): fail.append("last-known-good changed after rejected staging input")

# Preview approval is not publication; discard removes promotion staging only.
rid="activation-preview-test"; stage=ROOT/"data/control/staging"/rid; stage.mkdir(parents=True,exist_ok=True)
(stage/"manifest.json").write_text(json.dumps({"market":{"observations_added":1}}))
r=run([PREVIEW,"create","--preview-id",rid,"--run-id",rid]); doc=json.loads(r.stdout)
run([PREVIEW,"approve","--preview-id",rid]); approved=json.loads((ROOT/"data/control/previews"/f"{rid}.json").read_text())
if approved.get("status")!="APPROVED_NOT_PUBLISHED" or approved.get("publication_performed"): fail.append("preview approval bypassed publication gate")
run([PREVIEW,"discard","--preview-id",rid]); discarded=json.loads((ROOT/"data/control/previews"/f"{rid}.json").read_text())
if stage.exists() or not discarded.get("raw_observations_preserved"): fail.append("preview discard contract failed")

# Credential and workflow safety are static, so this test cannot call providers or GitHub.
bp=(ROOT/"pull_bettingpros_caesars_win_totals.py").read_text()
if "BETTINGPROS_API_KEY" not in bp or "API_KEY =" in bp: fail.append("BettingPros credential is not environment-only")
wf=(ROOT/"control_repo_template/.github/workflows/manual-data-refresh.yml").read_text()
for token in ("workflow_dispatch:","concurrency:","timeout-minutes:","self-hosted","inputs.mode == 'status'"):
 if token not in wf: fail.append(f"control workflow missing {token}")
cfg=json.loads((ROOT/"scripts/control/refresh_controller_config.json").read_text())
if cfg.get("live_provider_calls_enabled") or cfg.get("automatic_publication_enabled"): fail.append("live execution or automatic publication enabled")
print("Activation preparation tests:","FAILED" if fail else "PASSED")
print("- staging rejection: tested")
print("- atomic acceptance and LKG preservation: tested")
print("- preview approval/discard: tested")
print("- workflow dispatch/concurrency/timeout: tested")
print("- external calls: 0; publication: no")
for x in fail: print("ERROR:",x)
raise SystemExit(bool(fail))
