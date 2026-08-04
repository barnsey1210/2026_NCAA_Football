#!/usr/bin/env python3
"""Freeze spread blend weights on 2021-23, validate 2024, hold out 2025."""
from itertools import product
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/"data/import/prediction_tracker";OUT=ROOT/"data/research/prediction_tracker_spread_blend_2021_2025"
SYSTEMS={"FPI":"lineespn","TeamRankings":"lineteamrank","Sagarin Predictor":"linesagpred","Massey":"linemass"}

def weights(n,step=.05):
 units=round(1/step)
 for x in product(range(units+1),repeat=n-1):
  if sum(x)<=units:yield np.array(list(x)+[units-sum(x)],float)/units

def metrics(y,p):
 e=p-y
 return {"n":len(y),"mae":float(np.mean(np.abs(e))),"rmse":float(np.sqrt(np.mean(e*e))),"bias":float(np.mean(e)),"winner_accuracy":float(np.mean(np.sign(p)==np.sign(y)))}

def best(train,cols,target):
 x=train[cols].to_numpy(float);y=train[target].to_numpy(float);winner=None
 for w in weights(len(cols)):
  loss=np.mean(np.abs(x@w-y))
  if winner is None or loss<winner[0]:winner=(loss,w)
 return winner[1]

def main():
 OUT.mkdir(parents=True,exist_ok=True);parts=[]
 for season in range(2021,2026):
  d=pd.read_csv(SRC/f"ncaa{season}.csv");d["season"]=season;d["actual_margin"]=pd.to_numeric(d.hscore,errors="coerce")-pd.to_numeric(d.vscore,errors="coerce");parts.append(d)
 d=pd.concat(parts,ignore_index=True);base=list(SYSTEMS.values());needed=base+["lineopen","linemidweek","line","actual_margin"];d[needed]=d[needed].apply(pd.to_numeric,errors="coerce");d=d.dropna(subset=needed)
 train=d[d.season<=2023];val=d[d.season==2024];hold=d[d.season==2025]
 specs={"external_only":base,"external_plus_open":base+["lineopen"],"external_plus_midweek":base+["linemidweek"]};summary={"design":{"development":"2021-23","validation":"2024","holdout":"2025 untouched","weight_grid":"nonnegative, sum to 1, 5-point increments","line_convention":"positive means home favored"},"models":{}}
 predictions=[]
 for name,cols in specs.items():
  w=best(train,cols,"actual_margin");entry={"columns":cols,"weights":{c:float(v) for c,v in zip(cols,w)}}
  for label,z in [("development",train),("validation",val),("holdout",hold)]:
   p=z[cols].to_numpy(float)@w;entry[label+"_actual_margin"]=metrics(z.actual_margin.to_numpy(float),p);entry[label+"_closing_line"]=metrics(z.line.to_numpy(float),p)
   if label=="holdout":
    q=z[["season","week","Home","Road","lineopen","linemidweek","line","actual_margin"]].copy();q["model"]=name;q["prediction"]=p;predictions.append(q)
  summary["models"][name]=entry
 # Equal-weight external benchmark.
 for label,z in [("validation",val),("holdout",hold)]:
  p=z[base].mean(axis=1).to_numpy();summary.setdefault("equal_external_benchmark",{})[label+"_actual_margin"]=metrics(z.actual_margin.to_numpy(),p);summary["equal_external_benchmark"][label+"_closing_line"]=metrics(z.line.to_numpy(),p)
 pd.concat(predictions).to_csv(OUT/"holdout_2025_predictions.csv",index=False);(OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");(OUT/"README.md").write_text("# Prediction Tracker spread blend\n\nWeights were selected only on 2021-23 using contemporaneous game predictions, validated on 2024, and then evaluated on untouched 2025. The opening-line model is market-informed; the midweek model is included only as a timing benchmark and is not an early-week forecast.\n\n```json\n"+json.dumps(summary,indent=2)+"\n```\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
