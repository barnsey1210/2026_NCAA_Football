#!/usr/bin/env python3
"""Apply the frozen Bovada movement rules to other providers without tuning."""

from pathlib import Path
import pandas as pd
from analyze_pbp_line_movement import data, signed_stats

OUT=Path("data/research/pbp_line_movement_2021_2024/provider_robustness_2024.csv")
RULES=[
 ("spread_away_upgrade_favorite", "spread_move", -1,
  [("home_overall_success_adv","<=",-0.0001814671671235002),("opening_home_spread","<=",-3.0)]),
 ("total_down_low_success_slow", "total_move", -1,
  [("combined_overall_success","<=",0.9310875830918766),("combined_field_position",">",-139.80758013111537),("combined_fast_pace","<=",-26.013869254679115)]),
]

def mask(d,conditions):
 m=pd.Series(True,index=d.index)
 for f,op,t in conditions:m &= d[f].le(t) if op=="<=" else d[f].gt(t)
 return m

def main():
 rows=[]
 for provider in ("Bovada","DraftKings","ESPN Bet"):
  d=data(provider=provider);d=d[d.season.eq(2024)]
  for rule,target,direction,conditions in RULES:
   s=signed_stats(d.loc[mask(d,conditions),target],direction)
   rows.append({"provider":provider,"rule_id":rule,**s})
 q=pd.DataFrame(rows);q.to_csv(OUT,index=False);print(q.to_string(index=False))
if __name__=="__main__":main()
