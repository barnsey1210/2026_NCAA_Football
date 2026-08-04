#!/usr/bin/env python3
"""Stage, validate, and atomically accept normalized rating CSVs.

Acceptance writes only to the controller's isolated last-known-good store. It
does not replace production rating inputs; source-specific promotion remains a
separate activation step.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re, shutil, tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/"scripts/control/rating_source_profiles.json").read_text())
BASE=ROOT/"data/control/ratings"

def norm(s): return re.sub(r"[^a-z0-9]+","",str(s or "").lower())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic_json(p,v):
 p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+'.tmp'); q.write_text(json.dumps(v,indent=2)+"\n"); q.replace(p)

def validate(path, profile):
 rows=list(csv.DictReader(path.open(newline="",errors="ignore")))
 tc=profile["team_column"]; rc=profile["rating_column"]; sc=profile.get("season_column")
 teams=[norm(x.get(tc)) for x in rows if x.get(tc)]; unique=set(teams)
 errors=[]; warnings=[]; values=[]
 master=ROOT/"data/ratings/ratings_master_latest.csv"
 expected=set()
 if master.exists():
  expected={norm(x.get("team")) for x in csv.DictReader(master.open(newline="",errors="ignore")) if x.get("team")}
 missing=sorted(expected-unique)
 if len(unique)<profile["min_teams"]: errors.append(f"team count {len(unique)} below {profile['min_teams']}")
 duplicates=len(teams)-len(unique)
 if duplicates: errors.append(f"duplicate normalized teams: {duplicates}")
 if missing: errors.append(f"missing canonical teams: {len(missing)}")
 if sc:
  seasons={str(x.get(sc)) for x in rows if x.get(sc)}
  if seasons!={str(profile['season'])}: errors.append(f"unexpected seasons: {sorted(seasons)}")
 for row in rows:
  try:
   v=float(row.get(rc,""))
   if not math.isfinite(v): raise ValueError
   values.append(v)
  except Exception: errors.append(f"non-numeric {rc} for {row.get(tc) or 'unknown'}")
 lo,hi=profile["range"]
 bad=sum(not lo<=v<=hi for v in values)
 if bad: errors.append(f"{bad} values outside {lo}..{hi}")
 accepted=BASE/"accepted"/profile["key"]/"normalized.csv"
 old=[]
 if accepted.exists():
  try: old=[float(x.get(rc,"nan")) for x in csv.DictReader(accepted.open())]
  except Exception: old=[]
 if old and values:
  by_old={norm(x.get(tc)):float(x[rc]) for x in csv.DictReader(accepted.open()) if x.get(tc) and x.get(rc)}
  moves=[abs(float(x[rc])-by_old[norm(x[tc])]) for x in rows if norm(x.get(tc)) in by_old and x.get(rc)]
  mass=sum(m>=10 for m in moves)
  if moves and mass/max(1,len(moves))>.25: errors.append(f"implausible mass movement: {mass}/{len(moves)} teams moved >=10")
 source_date=max((x.get(profile.get("date_column",""),"") for x in rows),default="") or None
 prior_status=BASE/"status"/f"{profile['key']}.json"
 prior=json.loads(prior_status.read_text()) if prior_status.exists() else {}
 if source_date and prior.get("source_date") and source_date < prior["source_date"]:
  errors.append(f"stale source date {source_date} before accepted {prior['source_date']}")
 return {"source":profile["display_name"],"checked_at":datetime.now(timezone.utc).isoformat(),"rows":len(rows),"teams":len(unique),"duplicates":duplicates,"missing_team_rows":len(rows)-len(teams),"missing_canonical_teams":missing,"numeric_values":len(values),"source_date":source_date,"content_hash":sha(path),"errors":errors,"warnings":warnings,"passed":not errors,"accepted_before_hash":sha(accepted) if accepted.exists() else None}

def main():
 p=argparse.ArgumentParser(); p.add_argument("source",choices=sorted(CFG["sources"])); p.add_argument("--input"); p.add_argument("--raw-input"); p.add_argument("--accept",action="store_true"); p.add_argument("--run-id",default=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')); a=p.parse_args()
 profile=dict(CFG["sources"][a.source]); profile["key"]=a.source
 src=Path(a.input) if a.input else ROOT/profile["input"]
 if not src.is_absolute(): src=ROOT/src
 stage=BASE/"staging"/a.run_id/a.source; stage.mkdir(parents=True,exist_ok=True)
 if a.raw_input:
  raw=Path(a.raw_input); raw=raw if raw.is_absolute() else ROOT/raw
  raw_dir=stage/"raw"; raw_dir.mkdir(exist_ok=True); shutil.copy2(raw,raw_dir/raw.name)
 staged=stage/"normalized.csv"; shutil.copy2(src,staged)
 audit=validate(staged,profile); audit["classification"]=profile["classification"]; audit["accepted"]=False
 if a.accept and audit["passed"]:
  dest=BASE/"accepted"/a.source/"normalized.csv"; dest.parent.mkdir(parents=True,exist_ok=True)
  with tempfile.NamedTemporaryFile(dir=dest.parent,delete=False) as f: tmp=Path(f.name)
  shutil.copy2(staged,tmp); tmp.replace(dest); audit["accepted"]=True; audit["accepted_after_hash"]=sha(dest)
 atomic_json(stage/"validation.json",audit); atomic_json(BASE/"status"/f"{a.source}.json",audit)
 print(json.dumps(audit,indent=2)); raise SystemExit(0 if audit["passed"] else 2)
if __name__=="__main__": main()
