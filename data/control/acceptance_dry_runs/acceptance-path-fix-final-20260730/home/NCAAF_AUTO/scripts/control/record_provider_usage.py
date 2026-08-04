#!/usr/bin/env python3
"""Record private provider usage without copying credentials or response data."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"data/control"
EVENTS=BASE/"provider_usage.jsonl"
SUMMARY=BASE/"provider_usage_summary.json"

def atomic(path,value):
 path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(".tmp")
 tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n"); tmp.replace(path)

def main():
 p=argparse.ArgumentParser(); p.add_argument("provider",choices=["sports_game_odds"]); p.add_argument("--meta",required=True); p.add_argument("--date"); a=p.parse_args()
 meta=json.loads(Path(a.meta).read_text()); ts=a.date or meta.get("pulled_at") or datetime.now(timezone.utc).isoformat()
 event={"provider":a.provider,"timestamp":ts,"day":ts[:10],"month":ts[:7],"estimated_cost":meta.get("estimated_request_cost",1),"actual_cost":meta.get("actual_request_cost"),"remaining":next((v for k,v in meta.get("usage_headers",{}).items() if "remaining" in k),None),"reset":next((v for k,v in meta.get("usage_headers",{}).items() if "reset" in k),None),"reconciliation":"provider_dashboard_required" if meta.get("actual_request_cost") is None else "response_reported"}
 EVENTS.parent.mkdir(parents=True,exist_ok=True)
 with EVENTS.open("a") as fh: fh.write(json.dumps(event,sort_keys=True)+"\n")
 rows=[json.loads(x) for x in EVENTS.read_text().splitlines() if x.strip()]
 out={"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"providers":{}}
 for provider in sorted({x["provider"] for x in rows}):
  subset=[x for x in rows if x["provider"]==provider]; daily={}; monthly={}
  for row in subset:
   for target,key in ((daily,"day"),(monthly,"month")):
    bucket=target.setdefault(row[key],{"requests":0,"estimated_cost":0,"actual_cost":0,"actual_cost_known":True})
    bucket["requests"]+=1; bucket["estimated_cost"]+=row.get("estimated_cost") or 0
    if row.get("actual_cost") is None: bucket["actual_cost_known"]=False
    else: bucket["actual_cost"]+=row["actual_cost"]
  out["providers"][provider]={"daily":daily,"monthly":monthly,"latest_remaining":subset[-1].get("remaining"),"latest_reset":subset[-1].get("reset"),"reconciliation":subset[-1]["reconciliation"]}
 atomic(SUMMARY,out); print(json.dumps(out,indent=2))
if __name__=="__main__": main()
