#!/usr/bin/env python3
from pathlib import Path
import json,pandas as pd
from analyze_cross_book_opener_movement import sample
from analyze_pbp_line_movement import signed_stats
P=Path("data/research/pbp_market_modeling_2021_2025/provider_market_rows.csv");O=Path("data/research/cross_book_opener_movement_2025_holdout")
def main():
 O.mkdir(parents=True,exist_ok=True);d=pd.read_csv(P,low_memory=False);d=d[d.season==2025];rows=[]
 for market,threshold,minimum in [("spread",1.,.5),("total",1.5,.75)]:
  z=sample(d,market,threshold);s=signed_stats(z.toward_consensus_move,1);confirmed=s["n"]>=30 and s["signed_mean_move"]>=minimum and s["direction_accuracy"]>.5 and s["one_sided_p"]<=.05
  rows.append({"market":market,"threshold":threshold,"minimum_mean_move":minimum,**s,"confirmed_2025":confirmed})
 q=pd.DataFrame(rows);q.to_csv(O/"final_holdout.csv",index=False);summary={"confirmed":int(q.confirmed_2025.sum()),"rules":2,"status":"2025 consumed"};(O/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps(summary,indent=2));print(q.to_string(index=False))
if __name__=="__main__":main()
