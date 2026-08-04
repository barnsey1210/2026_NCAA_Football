#!/usr/bin/env python3
"""Test whether an outlier book opener moves toward the cross-book median."""
from pathlib import Path
import json,numpy as np,pandas as pd
from analyze_pbp_line_movement import signed_stats,bh
P=Path("data/research/pbp_market_modeling_2021_2025/provider_market_rows.csv");O=Path("data/research/cross_book_opener_movement_2023_2024")
def sample(d,market,threshold):
 op="opening_home_spread" if market=="spread" else "opening_total";cl="closing_home_spread" if market=="spread" else "closing_total";z=d[d[op].notna()&d[cl].notna()].copy();z["median_open"]=z.groupby("game_id")[op].transform("median");z["deviation"]=z[op]-z.median_open;z=z[z.groupby("game_id").provider.transform("count")>=2];z=z.loc[z.groupby("game_id").deviation.transform(lambda s:s.abs().max()).eq(z.deviation.abs())].sort_values(["game_id","provider"]).drop_duplicates("game_id");z=z[z.deviation.abs()>=threshold].copy();z["direction"]=np.sign(z.median_open-z[op]);z["toward_consensus_move"]=z.direction*(z[cl]-z[op]);return z
def main():
 O.mkdir(parents=True,exist_ok=True);d=pd.read_csv(P,low_memory=False);d=d[d.season.between(2023,2024)];rows=[]
 for market,threshold,minimum in [("spread",1.,.5),("total",1.5,.75)]:
  z=sample(d,market,threshold)
  for season,label in [(2023,"development"),(2024,"validation")]:
   s=signed_stats(z.loc[z.season==season,"toward_consensus_move"],1);rows.append({"market":market,"sample":label,"threshold":threshold,**s})
 q=pd.DataFrame(rows);wide=q.pivot(index="market",columns="sample");out=[]
 for market in ["spread","total"]:
  r={"market":market,"threshold":1. if market=="spread" else 1.5}
  for sample_name in ["development","validation"]:
   for metric in ["n","signed_mean_move","direction_accuracy","one_sided_p"]:r[f"{sample_name}_{metric}"]=wide.loc[market,(metric,sample_name)]
  out.append(r)
 out=pd.DataFrame(out);out["validation_q_value"]=bh(out.validation_one_sided_p.tolist());out["evidence_grade"]="rejected_or_inconclusive";mins=out.market.map({"spread":.5,"total":.75});ok=out.validation_n.ge(30)&out.development_signed_mean_move.gt(0)&out.validation_signed_mean_move.ge(mins)&out.validation_direction_accuracy.gt(.5)&out.validation_q_value.le(.10);out.loc[ok,"evidence_grade"]="validated_2024";out.to_csv(O/"validation.csv",index=False)
 s={"validated_2024":int(ok.sum()),"rules":2,"holdout_2025":"not used"};(O/"summary.json").write_text(json.dumps(s,indent=2)+"\n");print(json.dumps(s,indent=2));print(out.to_string(index=False))
if __name__=="__main__":main()
