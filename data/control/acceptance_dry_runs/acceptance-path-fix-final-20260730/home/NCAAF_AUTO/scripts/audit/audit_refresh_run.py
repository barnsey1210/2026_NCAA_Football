#!/usr/bin/env python3
"""Audit controller outputs without contacting providers or publishing."""
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parents[2]
control = ROOT / "data/control"
required = [control/"latest_refresh_status.json", control/"refresh_run_history.json", control/"refresh_runs.jsonl"]
errors=[]
for p in required:
    if not p.exists(): errors.append(f"missing {p.relative_to(ROOT)}")
latest={}
if required[0].exists():
    try: latest=json.loads(required[0].read_text())
    except Exception as e: errors.append(f"invalid latest JSON: {e}")
for k in ("run_id","requested_mode","status","start_timestamp","completion_timestamp"):
    if latest and k not in latest: errors.append(f"latest missing {k}")
all_text="\n".join(p.read_text(errors="ignore") for p in required if p.exists())
if re.search(r"(?i)(api[_-]?key|password|authorization|bearer)\s*[:=]\s*(?!\[REDACTED\])\S+", all_text):
    errors.append("possible secret in controller output")
shells=["index.html","dashboard_v2.html","openers_v2.html","matchups_v2.html","schedule_v2.html","odds_v2.html","ratings_v2.html"]
if latest and latest.get("validation_results",{}).get("v2_shell_hashes_unchanged") is False:
    errors.append("V2 shell hash check failed")
print(f"Controller audit: {'FAILED' if errors else 'PASSED'}")
print(f"Latest run: {latest.get('run_id','—')} {latest.get('status','—')}")
print(f"Canonical shells monitored: {len([x for x in shells if (ROOT/x).exists()])}")
for e in errors: print(f"ERROR: {e}")
raise SystemExit(1 if errors else 0)
