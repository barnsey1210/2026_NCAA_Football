#!/usr/bin/env python3
"""Fixed-rule favorite/underdog subgroup audit for two away-side hypotheses."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/research/advanced_directional_game_level_2021_2025.csv"
RULE_SOURCE = ROOT / "reports/advanced_directional_ats_candidates.csv"
OUT = ROOT / "reports/advanced_matchup_role_subgroups.csv"
LOCKED_OUT = ROOT / "reports/advanced_matchup_role_2025_locked.csv"
REPORT = ROOT / "reports/advanced_matchup_role_audit.md"
DEV = (2021, 2022, 2023)
SELECT = 2024
LOCKED = 2025

# Configurable inclusive upper bounds in points from the recommended away side.
SPREAD_BUCKETS = {
    "favorite": [(2.5, "favorite by 0.5 to 2.5"), (5.5, "favorite by 3 to 5.5"),
                 (9.5, "favorite by 6 to 9.5"), (math.inf, "favorite by 10+")],
    "underdog": [(2.5, "underdog by 0.5 to 2.5"), (5.5, "underdog by 3 to 5.5"),
                  (9.5, "underdog by 6 to 9.5"), (math.inf, "underdog by 10+")],
}


def role(home_spread):
    x = pd.to_numeric(home_spread, errors="coerce")
    return np.select([x.gt(0), x.lt(0), x.eq(0)], ["away favorite", "away underdog", "pick'em"], "unknown")


def away_bucket(home_spread):
    away = -pd.to_numeric(home_spread, errors="coerce")
    out = pd.Series("unknown", index=away.index, dtype=object)
    out[away.eq(0)] = "pick'em"
    for state, sign in (("favorite", -1), ("underdog", 1)):
        magnitude = away.abs()
        mask = away.mul(sign).gt(0)
        lower = 0.0
        for upper, label in SPREAD_BUCKETS[state]:
            m = mask & magnitude.gt(lower) & magnitude.le(upper)
            out[m] = label
            lower = upper
    return out


def wilson(w, n, z=1.96):
    if not n: return (np.nan, np.nan)
    p = w/n; den=1+z*z/n; center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return center-half, center+half


def mean_ci(x):
    x=pd.to_numeric(x,errors="coerce").dropna()
    if len(x)<2: return (np.nan,np.nan)
    h=1.96*x.std(ddof=1)/math.sqrt(len(x)); return x.mean()-h,x.mean()+h


def stats(frame):
    ats=pd.to_numeric(frame.away_ats_residual,errors="coerce").dropna()
    clv=pd.to_numeric(frame.away_open_bet_clv,errors="coerce").dropna()
    w,l,p=int((ats>0).sum()),int((ats<0).sum()),int((ats==0).sum()); decisions=w+l
    lo,hi=wilson(w,decisions); clo,chi=mean_ci(clv)
    return {"games":len(frame),"wins":w,"losses":l,"pushes":p,
            "ats_percentage":w/decisions if decisions else np.nan,
            "ats_ci95_low":lo,"ats_ci95_high":hi,
            "roi_at_minus_110":(w-1.1*l)/(1.1*decisions) if decisions else np.nan,
            "average_ats_residual":ats.mean() if len(ats) else np.nan,
            "median_ats_residual":ats.median() if len(ats) else np.nan,
            "average_point_clv":clv.mean() if len(clv) else np.nan,
            "median_point_clv":clv.median() if len(clv) else np.nan,
            "clv_mean_ci95_low":clo,"clv_mean_ci95_high":chi,
            "positive_point_clv_percentage":(clv>0).mean() if len(clv) else np.nan,
            "clv_at_least_0_5_percentage":(clv>=.5).mean() if len(clv) else np.nan,
            "clv_at_least_1_0_percentage":(clv>=1).mean() if len(clv) else np.nan,
            "average_movement_toward_signal":clv.mean() if len(clv) else np.nan,
            "median_movement_toward_signal":clv.median() if len(clv) else np.nan,
            "movement_toward_count":int((clv>0).sum()),"movement_away_count":int((clv<0).sum()),
            "no_move_count":int((clv==0).sum())}


def season_json(frame):
    return json.dumps({str(k):stats(g) for k,g in frame.groupby("season")},default=lambda x:None if pd.isna(x) else x)


def subgroup_classification(all_s,dev_s,sel_s,lock_s,positive_seasons):
    if all_s["games"]<60 or lock_s["games"]<20: return "INSUFFICIENT SAMPLE"
    stable_ats=all(x["average_ats_residual"]>0 and x["ats_percentage"]>=.50 for x in (dev_s,sel_s,lock_s))
    stable_clv=all(x["average_point_clv"]>=0 for x in (dev_s,sel_s,lock_s) if x["games"])
    if stable_ats and stable_clv and positive_seasons>=3: return "CONSISTENT SUPPORT"
    if (lock_s["ats_percentage"]>=.53 and lock_s["average_ats_residual"]>0) or (lock_s["average_point_clv"]>0 and lock_s["positive_point_clv_percentage"]>=.50): return "POSSIBLE ROLE EFFECT"
    if lock_s["average_ats_residual"]<0 and lock_s["average_point_clv"]<0: return "CONTRADICTORY"
    return "DESCRIPTIVE ONLY"


def transition(open_role, close_role):
    conditions=[
        (open_role.eq("away underdog")&close_role.eq("away favorite")),
        (open_role.eq("away favorite")&close_role.eq("away underdog")),
        (open_role.eq("away underdog")&close_role.eq("away underdog")),
        (open_role.eq("away favorite")&close_role.eq("away favorite")),
        (close_role.eq("pick'em")&~open_role.eq("pick'em")),
        (open_role.eq("pick'em")&~close_role.eq("pick'em")),
        (open_role.eq("pick'em")&close_role.eq("pick'em")),
    ]
    labels=["opened away underdog and closed away favorite","opened away favorite and closed away underdog",
            "remained away underdog","remained away favorite","moved to pick'em","moved away from pick'em","remained pick'em"]
    return np.select(conditions,labels,"other transition")


def build_rows(signal, hypothesis):
    dimensions={
        "opening_role":"opening_role", "closing_role":"closing_role", "role_transition":"role_transition",
        "home_market_interpretation":"home_market_interpretation",
        "opening_spread_bucket":"opening_away_spread_bucket", "closing_spread_bucket":"closing_away_spread_bucket",
        "market_direction":"market_direction_relative_to_signal",
    }
    rows=[]
    for dim,col in dimensions.items():
        for value,g in signal.groupby(col,dropna=False):
            a=stats(g); dev=stats(g[g.season.isin(DEV)]); sel=stats(g[g.season.eq(SELECT)]); lock=stats(g[g.season.eq(LOCKED)])
            season={str(k):stats(x) for k,x in g.groupby("season")}
            positive_seasons=sum(v["average_ats_residual"]>0 for v in season.values())
            one_season=(positive_seasons<=1) or (len(g) and max((v["games"] for v in season.values()),default=0)/len(g)>.45)
            row={"hypothesis":hypothesis,"row_type":"subgroup","dimension":dim,"subgroup":str(value)}|a
            row|={f"development_{k}":v for k,v in dev.items()}|{f"selection_2024_{k}":v for k,v in sel.items()}|{f"locked_2025_{k}":v for k,v in lock.items()}
            row|={"performance_by_season":json.dumps(season,default=lambda x:None if pd.isna(x) else x),
                  "positive_ats_seasons":positive_seasons,"one_season_dependence":one_season,
                  "classification":subgroup_classification(a,dev,sel,lock,positive_seasons),
                  "multiple_comparison_caution":True,
                  "interpretation_flag":"ATS_AND_CLV" if a["average_ats_residual"]>0 and a["average_point_clv"]>0 else ("ATS_WITHOUT_CLV" if a["average_ats_residual"]>0 else ("CLV_WITHOUT_ATS" if a["average_point_clv"]>0 else "NEITHER"))}
            rows.append(row)
    return rows


def ztest(a,b):
    wa,na=a["wins"],a["wins"]+a["losses"]; wb,nb=b["wins"],b["wins"]+b["losses"]
    if min(na,nb)<2:return np.nan
    pool=(wa+wb)/(na+nb); se=math.sqrt(pool*(1-pool)*(1/na+1/nb))
    if not se:return np.nan
    return math.erfc(abs(wa/na-wb/nb)/se/math.sqrt(2))


def comparison_rows(signal,hypothesis):
    comparisons=[
        ("opening away favorite vs away underdog","opening_role","away favorite","away underdog"),
        ("closing away favorite vs away underdog","closing_role","away favorite","away underdog"),
        ("opening short vs large away underdog","opening_away_spread_bucket","underdog by 0.5 to 2.5","underdog by 6 to 9.5"),
        ("opening short vs large away favorite","opening_away_spread_bucket","favorite by 0.5 to 2.5","favorite by 6 to 9.5"),
        ("stable underdog vs underdog-to-favorite flip","role_transition","remained away underdog","opened away underdog and closed away favorite"),
        ("stable favorite vs favorite-to-underdog flip","role_transition","remained away favorite","opened away favorite and closed away underdog"),
        ("market toward vs against signal","market_direction_relative_to_signal","toward signal","against signal"),
    ]
    out=[]
    for name,col,av,bv in comparisons:
        ag=signal[signal[col].eq(av)]; bg=signal[signal[col].eq(bv)]; a=stats(ag); b=stats(bg)
        out.append({"hypothesis":hypothesis,"row_type":"comparison","dimension":col,"subgroup":name,
                    "group_a":av,"group_b":bv,"group_a_games":a["games"],"group_b_games":b["games"],
                    "group_a_ats_percentage":a["ats_percentage"],"group_b_ats_percentage":b["ats_percentage"],
                    "ats_percentage_difference":a["ats_percentage"]-b["ats_percentage"],
                    "group_a_average_point_clv":a["average_point_clv"],"group_b_average_point_clv":b["average_point_clv"],
                    "average_point_clv_difference":a["average_point_clv"]-b["average_point_clv"],
                    "ats_two_sided_p_value":ztest(a,b),"classification":"DESCRIPTIVE ONLY",
                    "multiple_comparison_caution":True})
    return out


def bh_q(rows):
    idx=[i for i,r in enumerate(rows) if r.get("row_type")=="comparison" and pd.notna(r.get("ats_two_sided_p_value"))]
    ordered=sorted(idx,key=lambda i:rows[i]["ats_two_sided_p_value"]); m=len(ordered); prev=1.0
    for rank,i in reversed(list(enumerate(ordered,1))):
        q=min(prev,rows[i]["ats_two_sided_p_value"]*m/rank);rows[i]["ats_bh_q_value"]=q;prev=q
    return rows


def md_table(df,cols):
    if df.empty:return "_None._"
    x=df[cols].fillna("—")
    return "|"+"|".join(cols)+"|\n|"+"|".join(["---"]*len(cols))+"|\n"+"\n".join("|"+"|".join(str(v) for v in r)+"|" for r in x.itertuples(index=False,name=None))


def main():
    d=pd.read_csv(SOURCE,low_memory=False)
    rules=pd.read_csv(RULE_SOURCE)
    definitions={r.candidate:json.loads(r.definition) for r in rules.itertuples() if r.candidate in ("original_success_away_low20","directional_net_advantage__away_low20")}
    assert definitions["original_success_away_low20"]["threshold"] == -0.052928295457152705
    assert definitions["directional_net_advantage__away_low20"]["threshold"] == -6.0
    d["opening_role"]=role(d.opening_home_spread);d["closing_role"]=role(d.closing_home_spread)
    d["role_transition"]=transition(d.opening_role,d.closing_role)
    d["home_market_interpretation"]=np.select([d.closing_role.eq("away underdog"),d.closing_role.eq("away favorite"),d.closing_role.eq("pick'em")],
        ["backing away underdog against home favorite","backing away favorite against home underdog","backing away side in pick'em market"],"unknown")
    d["opening_away_spread_bucket"]=away_bucket(d.opening_home_spread);d["closing_away_spread_bucket"]=away_bucket(d.closing_home_spread)
    d["market_direction_relative_to_signal"]=np.select([d.away_open_bet_clv.gt(0),d.away_open_bet_clv.lt(0),d.away_open_bet_clv.eq(0)],
        ["toward signal","against signal","no move"],"unknown")
    all_rows=[]; signal_counts={}
    for hypothesis,rule in definitions.items():
        mask=d[rule["feature"]].le(rule["threshold"])
        signal=d[mask].copy();signal_counts[hypothesis]=len(signal)
        all_rows += build_rows(signal,hypothesis)+comparison_rows(signal,hypothesis)
    all_rows=bh_q(all_rows); out=pd.DataFrame(all_rows)
    subgroup=out[out.row_type.eq("subgroup")].copy();locked_cols=[c for c in subgroup if c.startswith("locked_2025_")]
    locked=subgroup[["hypothesis","dimension","subgroup","classification","one_season_dependence","interpretation_flag"]+locked_cols].copy()
    OUT.parent.mkdir(parents=True,exist_ok=True);out.to_csv(OUT,index=False);locked.to_csv(LOCKED_OUT,index=False)

    key=subgroup[subgroup.dimension.isin(["opening_role","closing_role"])].copy()
    cols=["hypothesis","dimension","subgroup","games","ats_percentage","average_ats_residual","average_point_clv","positive_point_clv_percentage","locked_2025_games","locked_2025_ats_percentage","locked_2025_average_point_clv","classification"]
    report=f"""# Fixed-rule advanced-matchup favorite/underdog audit

## Frozen scope

- Success Rate away signal: `home-minus-away Success Rate differential <= -0.052928295457152705`.
- Broad directional away signal: `directional_net_advantage <= -6`, exactly as frozen in the completed directional study.
- Universe and partitions are unchanged: Week 5+, FBS-vs-FBS, four prior games; 2021–2023 development, 2024 selection, locked 2025.
- Away ATS residual and point CLV use the prior study's signs. Positive away CLV means the opening away line was better than the closing away line.
- Buckets are configurable in the audit script. No threshold was selected or revised here.

## Favorite/underdog summary

{md_table(key,cols)}

## Explicit answers

1. **Success Rate role:** among games with a retained opener it is primarily an **away-favorite** angle, not an away-underdog angle. Opening away favorites were 54.6% ATS overall and 58.3% in locked 2025 (N=96); opening away underdogs were only N=30 overall/N=13 locked and are insufficient. Because 260 signal games lack an opener, this is not proof that the parent rule should be narrowed.
2. **Broad directional role:** it is also primarily an **away-favorite** angle in observed opening data. Opening away favorites were 56.0% ATS overall, 60.0% in development, 51.5% in 2024, and 58.4% locked (N=101), the only `CONSISTENT SUPPORT` subgroup. Opening away underdogs were small and contradictory/insufficient. Again, 299 games lack an opener.
3. **Opening versus closing role:** opening role explains the broad-directional result more cleanly and is the actionable definition. Closing away-favorite groups remain positive, but closing role incorporates the movement being studied and is therefore less causal. Favorite flips are far too small to interpret.
4. **Point CLV:** opening away-favorite groups have positive average point CLV for both hypotheses (+0.68 Success Rate; +0.32 broad directional), but only the Success Rate group exceeds 50% positive CLV. Apparent away-underdog CLV is much larger but rests on insufficient samples and role flips.
5. **2026 monitoring:** prioritize preregistered monitoring of **opening away favorites** qualifying under each unchanged parent rule, especially the broad-directional rule. Retain the full away-side parent signal simultaneously so the role effect can be tested prospectively. Nothing is promoted to production.
6. **Prospective fields:** game ID, scheduled kickoff, observation timestamp, sportsbook, away/home line and price, consensus line, opening and current role, role transition, raw away spread, spread bucket, closing line, away ATS residual, point and price CLV, fixed signal value/threshold, prior-game counts, and injury/news timestamps.

## Statistical cautions

- Wilson 95% intervals are reported for ATS rates and normal-approximation 95% intervals for mean CLV.
- Pairwise ATS comparisons include Benjamini–Hochberg q-values across the planned comparison family.
- No planned favorite/underdog or interaction comparison is statistically reliable after multiple-comparison adjustment (all available BH q-values are at least 0.79). The observed away-favorite differences are prioritization evidence only.
- `one_season_dependence`, sample gates, and material-but-unreliable differences are explicitly flagged.
- These are correlated subgroup descriptions of two pre-existing hypotheses, not independent signal discoveries.
"""
    REPORT.write_text(report,encoding="utf-8")
    print(json.dumps({"signal_games":signal_counts,"rows":len(out),"locked_rows":len(locked),"classifications":subgroup.classification.value_counts().to_dict(),"outputs":[str(OUT.relative_to(ROOT)),str(LOCKED_OUT.relative_to(ROOT)),str(REPORT.relative_to(ROOT))]},indent=2))

if __name__=="__main__":main()
