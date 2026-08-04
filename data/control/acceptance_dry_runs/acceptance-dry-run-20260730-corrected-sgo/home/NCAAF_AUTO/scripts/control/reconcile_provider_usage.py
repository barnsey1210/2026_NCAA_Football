#!/usr/bin/env python3
"""Record a manual provider-dashboard reconciliation without secrets or calls."""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EVENTS=ROOT/"data/control/provider_usage.jsonl"
SUMMARY=ROOT/"data/control/provider_usage_summary.json"

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("provider")
    p.add_argument("--period", required=True, help="Provider billing day/month or dashboard period")
    p.add_argument("--actual-cost", type=float)
    p.add_argument("--remaining", type=float)
    p.add_argument("--reset")
    p.add_argument("--note", default="manual provider dashboard reconciliation")
    a=p.parse_args()
    if a.actual_cost is None and a.remaining is None:
        p.error("provide --actual-cost or --remaining")
    event={"provider":a.provider,"timestamp":datetime.now(timezone.utc).isoformat(),
           "period":a.period,"actual_cost":a.actual_cost,"remaining":a.remaining,
           "reset":a.reset,"reconciliation":"manual_provider_dashboard","note":a.note[:240]}
    EVENTS.parent.mkdir(parents=True,exist_ok=True)
    with EVENTS.open("a") as fh: fh.write(json.dumps(event,sort_keys=True)+"\n")
    rows=[json.loads(x) for x in EVENTS.read_text().splitlines() if x.strip()]
    by_provider={}
    for row in rows:
        state=by_provider.setdefault(row.get("provider","unknown"),{"events":0})
        state["events"]+=1
        if row.get("remaining") is not None: state["latest_remaining"]=row["remaining"]
        if row.get("reset") is not None: state["latest_reset"]=row["reset"]
        if row.get("reconciliation") == "manual_provider_dashboard":
            state["last_reconciled_period"]=row.get("period")
            state["last_reconciled_actual_cost"]=row.get("actual_cost")
            state["last_reconciled_at"]=row.get("timestamp")
    payload={"schema_version":2,"generated_at":datetime.now(timezone.utc).isoformat(),"providers":by_provider}
    tmp=SUMMARY.with_suffix(".tmp"); tmp.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n"); tmp.replace(SUMMARY)
    print(json.dumps(event,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
