#!/usr/bin/env python3
"""Build rating-system comparisons and honest value-change provenance."""
import csv,json
from collections import defaultdict
from datetime import date,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
rows=list(csv.DictReader((ROOT/'data/ratings/ratings_latest.csv').open())); dates=sorted({r['snapshot_date'] for r in rows if r.get('snapshot_date')}); latest=dates[-1]
active={'SP+':'spplus','FPI':'fpi','TeamRankings':'teamrankings','Brad Powers':'bradpowers'}; vectors=defaultdict(dict)
for r in rows:
 if r.get('source') in active and r.get('snapshot_date'):
  try:vectors[(r['snapshot_date'],r['source'])][r['team']]=float(r['rating'])
  except (ValueError,TypeError):pass
source_meta={}
for label,key in active.items():
 available=[d for d in dates if vectors.get((d,label))]; last_change=None
 for previous,current in zip(available,available[1:]):
  if vectors[(previous,label)]!=vectors[(current,label)]:last_change=current
 current_rows=[r for r in rows if r.get('snapshot_date')==latest and r.get('source')==label]; previous=available[-2] if len(available)>1 else None
 changed=sum(vectors[(previous,label)].get(t)!=v for t,v in vectors[(latest,label)].items()) if previous else 0
 pulls=sorted({r.get('pulled_at') for r in current_rows if r.get('pulled_at')}); provider=sorted({r.get('source_updated_at') for r in current_rows if r.get('source_updated_at')})
 source_meta[key]={'label':label,'latest_snapshot':latest,'latest_pull':pulls[-1] if pulls else None,'provider_updated_at':provider[-1] if provider else None,'last_observed_value_change':last_change,'changed_teams_from_prior':changed,'previous_snapshot':previous}
# Build daily equal-weight composites from preserved source history. These power
# the frozen preseason and recent-form columns without mutating production ratings.
history=defaultdict(dict)
for r in csv.DictReader((ROOT/'data/ratings/ratings_history.csv').open()):
 if r.get('season')!='2026' or r.get('source') not in active or not r.get('snapshot_date'):continue
 try:history[(r['team'],r['snapshot_date'])][active[r['source']]]=float(r['rating'])
 except (ValueError,TypeError):pass
team_series=defaultdict(list)
for (team,d),sources in history.items():
 if len(sources)>=3:team_series[team].append((d,sum(sources.values())/len(sources)))
for series in team_series.values():series.sort()
def at_or_before(series,target):
 eligible=[x for x in series if x[0]<=target]
 return eligible[-1][1] if eligible else None
by_team={}
for r in rows:
 if r.get('snapshot_date')!=latest or r.get('source') not in active:continue
 try:rating=float(r['rating']);rank=int(float(r['rank']))
 except (ValueError,TypeError):continue
 by_team.setdefault(r['team'],{})[active[r['source']]]={'rating':rating,'rank':rank,'pulled_at':r.get('pulled_at')}
out=[]
for team,sources in by_team.items():
 vals=[x['rating'] for x in sources.values()]
 if len(vals)<3:continue
 current=sum(vals)/len(vals)
 out.append({'team':team,'rating':current,'sources':sources,'variance':max(vals)-min(vals),'high_source':max(sources,key=lambda k:sources[k]['rating']),'low_source':min(sources,key=lambda k:sources[k]['rating'])})
# Freeze the 2026 preseason composite once, after all four active sources are
# wired. Before kickoff, current and preseason are intentionally identical and
# recent-form changes are zero rather than historical ingestion artifacts.
baseline_path=ROOT/'data/ratings/ratings_preseason_2026.csv'
if baseline_path.exists():
 baseline={r['team']:{'rating':float(r['rating']),'rank':int(r['rank'])} for r in csv.DictReader(baseline_path.open())}
else:
 ranked=sorted(out,key=lambda x:x['rating'],reverse=True)
 baseline={x['team']:{'rating':x['rating'],'rank':i} for i,x in enumerate(ranked,1)}
 with baseline_path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['team','rating','rank','snapshot_date']);w.writeheader()
  for x in ranked:w.writerow({'team':x['team'],'rating':x['rating'],'rank':baseline[x['team']]['rank'],'snapshot_date':latest})
for x in out:
 b=baseline.get(x['team'],{'rating':x['rating'],'rank':None});x['preseason_rating']=b['rating'];x['preseason_rank']=b['rank'];x['preseason_delta']=x['rating']-b['rating']
 series=team_series.get(x['team'],[]);d=date.fromisoformat(latest);l2=at_or_before(series,(d-timedelta(days=14)).isoformat());l4=at_or_before(series,(d-timedelta(days=28)).isoformat())
 preseason_mode=date.today()<date(2026,8,29)
 x['l2_change']=0.0 if preseason_mode else (x['rating']-l2 if l2 is not None else None);x['l4_change']=0.0 if preseason_mode else (x['rating']-l4 if l4 is not None else None)
payload={'snapshot_date':latest,'weights':{k:.25 for k in active.values()},'source_meta':source_meta,'teams':out};target=ROOT/'data/site/ratings_view.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(payload,separators=(',',':'))+'\n');print(target,len(out))
if len(out)<130:raise SystemExit('ratings view coverage below 130')
