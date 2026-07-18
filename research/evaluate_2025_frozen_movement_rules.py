#!/usr/bin/env python3
"""Final 2025 holdout for two frozen opening-line movement rules."""
from pathlib import Path
import json,pandas as pd
from analyze_pbp_line_movement import data,signed_stats

OUT=Path("data/research/pbp_line_movement_2025_holdout")
RULES=[
 ("away_dog_unsupported_home_favorite","spread_move",-1,.50,[("home_overall_success_adv","<=",-0.0001814671671235002),("opening_home_spread","<=",-3.0)]),
 ("under_low_success_slow","total_move",-1,.75,[("combined_overall_success","<=",0.9310875830918766),("combined_field_position",">",-139.80758013111537),("combined_fast_pace","<=",-26.013869254679115)]),
]
def mask(d,c):
 m=pd.Series(True,index=d.index)
 for f,op,t in c:m &= d[f].le(t) if op=="<=" else d[f].gt(t)
 return m
def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for provider in ("Bovada","DraftKings","ESPN Bet"):
  d=data(provider=provider,max_season=2025);d=d[d.season.eq(2025)]
  for rule,target,direction,minimum,c in RULES:
   s=signed_stats(d.loc[mask(d,c),target],direction);confirmed=provider=="Bovada" and s["n"]>=30 and s["signed_mean_move"]>=minimum and s["direction_accuracy"]>.5 and s["one_sided_p"]<=.05
   rows.append({"provider":provider,"rule_id":rule,"minimum_mean_clv":minimum,**s,"primary_confirmed":confirmed})
 q=pd.DataFrame(rows);q.to_csv(OUT/"final_holdout_results.csv",index=False)
 primary=q[q.provider.eq("Bovada")];summary={"season":2025,"primary_provider":"Bovada","rules_tested":2,"rules_confirmed":int(primary.primary_confirmed.sum()),"holdout_status":"consumed for movement research"}
 (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps(summary,indent=2));print(q.to_string(index=False))
if __name__=="__main__":main()
