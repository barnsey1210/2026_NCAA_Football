#!/usr/bin/env python3
"""Use historical rating-system game forecasts to predict opener-to-close movement."""
from itertools import product
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2];SRC=ROOT/"data/import/prediction_tracker";OUT=ROOT/"data/research/prediction_tracker_close_movement_blend_2021_2025"
SYSTEMS={"FPI":"lineespn","TeamRankings":"lineteamrank","Sagarin Predictor":"linesagpred","Massey":"linemass"}

def weight_grid(step=.05):
 u=round(1/step)
 for a,b,c in product(range(u+1),repeat=3):
  if a+b+c<=u:yield np.array([a,b,c,u-a-b-c],float)/u

def predict(d,cols,w,k):
 blend=d[cols].to_numpy(float)@w;op=d.lineopen.to_numpy(float)
 return op+k*(blend-op)

def metrics(d,p):
 close=d.line.to_numpy(float);op=d.lineopen.to_numpy(float);actual_move=close-op;pred_move=p-op;e=p-close
 moved=np.abs(actual_move)>=.5;called=np.abs(pred_move)>=.25
 eligible=moved&called
 return {"n":len(d),"close_mae":float(np.mean(np.abs(e))),"close_rmse":float(np.sqrt(np.mean(e*e))),"mean_predicted_move":float(np.mean(np.abs(pred_move))),"mean_actual_move":float(np.mean(np.abs(actual_move))),"movement_direction_accuracy_all_moved":float(np.mean(np.sign(pred_move[moved])==np.sign(actual_move[moved]))) if moved.any() else None,"direction_n_all_moved":int(moved.sum()),"movement_direction_accuracy_called":float(np.mean(np.sign(pred_move[eligible])==np.sign(actual_move[eligible]))) if eligible.any() else None,"direction_n_called":int(eligible.sum())}

def main():
 OUT.mkdir(parents=True,exist_ok=True);parts=[]
 for season in range(2021,2026):
  z=pd.read_csv(SRC/f"ncaa{season}.csv");z["season"]=season;parts.append(z)
 d=pd.concat(parts,ignore_index=True);cols=list(SYSTEMS.values());needed=cols+["lineopen","linemidweek","line"];d[needed]=d[needed].apply(pd.to_numeric,errors="coerce");d=d.dropna(subset=needed);train=d[d.season<=2023];val=d[d.season==2024];hold=d[d.season==2025]
 best=None
 for w in weight_grid():
  for k in np.arange(0,1.5001,.05):
   p=predict(train,cols,w,k);loss=np.mean(np.abs(p-train.line.to_numpy()))
   if best is None or loss<best[0]:best=(loss,w,float(k))
 _,w,k=best
 summary={"design":{"development":"2021-23","validation":"2024","holdout":"2025 untouched","target":"Prediction Tracker closing home line","formula":"open + response * (weighted system projection - open)","system_weight_grid":"5-point increments; nonnegative; sums to 1","response_grid":"0.00 to 1.50 in 0.05 increments"},"selected_weights":{name:float(x) for name,x in zip(SYSTEMS,w)},"selected_response":k,"results":{}}
 equal=np.ones(4)/4
 for label,z in [("development",train),("validation",val),("holdout",hold)]:
  summary["results"][label]={"frozen_model":metrics(z,predict(z,cols,w,k)),"opener_no_change":metrics(z,z.lineopen.to_numpy()),"equal_system_full_adjustment":metrics(z,predict(z,cols,equal,1.0)),"midweek_timing_benchmark":metrics(z,z.linemidweek.to_numpy())}
 q=hold[["season","week","Home","Road","lineopen","linemidweek","line"]].copy();q["weighted_system_projection"]=hold[cols].to_numpy()@w;q["predicted_close"]=predict(hold,cols,w,k);q["predicted_move"]=q.predicted_close-q.lineopen;q["actual_move"]=q.line-q.lineopen;q.to_csv(OUT/"holdout_2025_predictions.csv",index=False)
 (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");(OUT/"README.md").write_text("# Rating-system blend for opener-to-close movement\n\nThe opener is market-history data and remains the starting price. FPI, TeamRankings, Sagarin Predictor, and Massey game forecasts are blended to estimate the direction and fraction of convergence by close. Weights were frozen on 2021-23, validated on 2024, and evaluated unchanged on 2025. Prediction Tracker does not timestamp each system forecast, so this supports use once the weekly system forecasts are posted; it does not prove all inputs were available at the Sunday opener.\n\n```json\n"+json.dumps(summary,indent=2)+"\n```\n");print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
