#!/usr/bin/env python3
"""Build the isolated market/SP+ blended Shadow candidate.

This script consumes only completed research artifacts.  It never writes a
production/site artifact; all output is restricted to data/research and
build/research.
"""
from __future__ import annotations

import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SPREAD = ROOT / "data/research/sp_plus_movement_alignment/game_level_audit.csv"
TOTAL = ROOT / "data/research/sp_plus_total_movement/game_level_audit.csv"
PROTECTED = [
    "config/market_shadow_production.json",
    "scripts/site/build_saturday_shadow_lines.py",
    "scripts/site/build_postgame_shadow_updates.py",
    "scripts/site/build_market_shadow_production_layer.py",
    "scripts/research/build_team_rating_movement_model.py",
    "scripts/research/build_sp_plus_movement_alignment.py",
    "scripts/research/build_sp_plus_total_movement.py",
    "openers_v2.html", "schedule_v2.html",
    "build/public_site/openers.html", "build/public_site/schedule.html",
    "data/site/postgame_shadow_updates.json",
    "data/site/saturday_shadow_lines.json",
    "data/site/schedule_live_enrichment.json",
    "daily_market_update.sh", "scripts/publish/publish_site.sh",
    "data/ratings/ratings_latest.csv",
]


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def metrics(actual, pred):
    a, p = np.asarray(actual, float), np.asarray(pred, float)
    ok = np.isfinite(a) & np.isfinite(p); a, p = a[ok], p[ok]
    e = p-a
    return {"n": int(len(e)), "mae": float(np.mean(abs(e))),
            "median_absolute_error": float(np.median(abs(e))),
            "rmse": float(np.sqrt(np.mean(e*e))),
            "signed_bias": float(np.mean(e))}


def choose_total_correction(d: pd.DataFrame):
    eligible=d.identical_sample.fillna(False).astype(bool) if "identical_sample" in d else pd.Series(True,index=d.index)
    sel = d[d.season.eq(2024)&eligible].dropna(subset=["optimized_fixed_blend", "actual_close"]).copy()
    hold = d[d.season.eq(2025)&eligible].dropna(subset=["optimized_fixed_blend", "actual_close"]).copy()
    sel["stage"] = pd.cut(sel.week, [-1, 4, 9, 99], labels=["early", "middle", "late"])
    hold["stage"] = pd.cut(hold.week, [-1, 4, 9, 99], labels=["early", "middle", "late"])
    q = sel.existing_total_projection.quantile([.33, .67]).tolist()
    bins = [-np.inf, q[0], q[1], np.inf]
    sel["band"] = pd.cut(sel.existing_total_projection, bins, labels=["low", "middle", "high"])
    hold["band"] = pd.cut(hold.existing_total_projection, bins, labels=["low", "middle", "high"])
    fixed = -float((sel.optimized_fixed_blend-sel.actual_close).mean())
    candidates = {"none": (sel.optimized_fixed_blend, hold.optimized_fixed_blend, {"intercept": 0.0})}
    candidates["fixed_intercept"] = (sel.optimized_fixed_blend+fixed,
                                      hold.optimized_fixed_blend+fixed,
                                      {"intercept": fixed})
    for name, group in [("season_stage", "stage"), ("projected_total_band", "band")]:
        counts = sel.groupby(group, observed=True).size()
        stable = len(counts) == 3 and int(counts.min()) >= 40
        if stable:
            corr = (sel.actual_close-sel.optimized_fixed_blend).groupby(sel[group], observed=True).mean().to_dict()
            candidates[name] = (sel.optimized_fixed_blend+sel[group].map(corr).astype(float),
                                hold.optimized_fixed_blend+hold[group].map(corr).astype(float),
                                {"corrections": {str(k): float(v) for k,v in corr.items()}, "stable": True})
    rows=[]
    for name,(sp,hp,detail) in candidates.items():
        rows.append({"candidate":name,"sample":"selection_2024",**metrics(sel.actual_close,sp),"detail":json.dumps(detail,sort_keys=True)})
        rows.append({"candidate":name,"sample":"locked_2025",**metrics(hold.actual_close,hp),"detail":json.dumps(detail,sort_keys=True)})
    comp=pd.DataFrame(rows)
    pick=(comp[comp["sample"].eq("selection_2024")]
          .sort_values(["mae","median_absolute_error","signed_bias"],key=lambda s:abs(s) if s.name=="signed_bias" else s)
          .iloc[0].candidate)
    detail=candidates[pick][2]
    def correction(row):
        if pick == "none": return 0.0
        if pick == "fixed_intercept": return float(detail["intercept"])
        group="stage" if pick=="season_stage" else "band"
        if group=="stage": key=str(pd.cut(pd.Series([row.week]),[-1,4,9,99],labels=["early","middle","late"]).iloc[0])
        else: key=str(pd.cut(pd.Series([row.existing_total_projection]),bins,labels=["low","middle","high"]).iloc[0])
        return float(detail["corrections"].get(key,0))
    d["selected_bias_correction"] = d.apply(correction,axis=1)
    d["final_shadow_total"] = d.optimized_fixed_blend+d.selected_bias_correction
    return d, comp, pick, detail


def agreement(row):
    c=str(row.get("alignment_category", ""))
    return {"Same meaningful direction":"green","Opposite directions":"red",
            "Both no meaningful change":"yellow","Market only meaningful":"yellow",
            "SP+ only meaningful":"yellow"}.get(c,"gray")


def fmt(v, n=2):
    return "—" if pd.isna(v) else f"{float(v):.{n}f}"


def render_html(rows, summary):
    openers=[]
    for _,r in rows.head(40).iterrows():
        openers.append(f"<tr><td>W{int(r.week)}</td><td>{r.away_team} at {r.home_team}</td><td>{fmt(r.get('current_model_spread'),1)}</td><td class='{agreement(r)}'>{fmt(r.get('simple_blend'),1)}</td><td>{fmt(r.get('spread_impact'),1)}</td><td>{fmt(r.get('current_model_total'),1)}</td><td>{fmt(r.get('final_shadow_total'),1)}</td><td>{fmt(r.get('total_impact'),1)}</td></tr>")
    cards=[]
    for _,r in rows.head(120).iterrows():
        color=agreement(r); ready="Ready" if pd.notna(r.get("simple_blend")) else "Insufficient data"
        cards.append(f"""<details><summary>W{int(r.week)} · {r.away_team} at {r.home_team} · <b class='{color}'>{fmt(r.get('simple_blend'),1)}</b> · Total {fmt(r.get('final_shadow_total'),1)}</summary>
<div class='grid'><section><h3>Spread details</h3><table>
<tr><td>Frozen pregame market ratings</td><td>{fmt(r.get('frozen_away_market_rating'))} / {fmt(r.get('frozen_home_market_rating'))}</td></tr>
<tr><td>Predicted away/home market change</td><td>{fmt(r.get('predicted_away_market_move'))} / {fmt(r.get('predicted_home_market_move'))}</td></tr>
<tr><td>Predicted market fair spread</td><td>{fmt(r.get('market_fair_spread'))}</td></tr>
<tr><td>Current away/home SP+</td><td>{fmt(r.get('current_away_sp_plus'))} / {fmt(r.get('current_home_sp_plus'))}</td></tr>
<tr><td>Predicted away/home SP+ change</td><td>{fmt(r.get('predicted_away_sp_plus_move'))} / {fmt(r.get('predicted_home_sp_plus_move'))}</td></tr>
<tr><td>Predicted SP+ fair spread</td><td>{fmt(r.get('sp_plus_fair_spread'))}</td></tr>
<tr><td>Blended Shadow spread</td><td class='{color}'>{fmt(r.get('simple_blend'))}</td></tr>
<tr><td>Spread impact vs Current Model</td><td>{fmt(r.get('spread_impact'))}</td></tr>
<tr><td>Agreement / confidence</td><td>{r.get('alignment_category','—')} / {r.get('confidence_tier','—')}</td></tr>
<tr><td>Blend method</td><td>2024-selected simple average</td></tr><tr><td>Projection readiness</td><td>{ready}</td></tr>
</table></section><section><h3>Total details</h3><table>
<tr><td>Away offense current / Δ / updated</td><td>{fmt(r.get('current_away_sp_offense'))} / {fmt(r.get('predicted_away_off_change'))} / {fmt(r.get('predicted_updated_away_offense'))}</td></tr>
<tr><td>Away defense current / Δ / updated</td><td>{fmt(r.get('current_away_sp_defense'))} / {fmt(r.get('predicted_away_def_change'))} / {fmt(r.get('predicted_updated_away_defense'))}</td></tr>
<tr><td>Home offense current / Δ / updated</td><td>{fmt(r.get('current_home_sp_offense'))} / {fmt(r.get('predicted_home_off_change'))} / {fmt(r.get('predicted_updated_home_offense'))}</td></tr>
<tr><td>Home defense current / Δ / updated</td><td>{fmt(r.get('current_home_sp_defense'))} / {fmt(r.get('predicted_home_def_change'))} / {fmt(r.get('predicted_updated_home_defense'))}</td></tr>
<tr><td>Predicted SP+ component total</td><td>{fmt(r.get('selected_sp_component_total'))}</td></tr><tr><td>Existing projected total</td><td>{fmt(r.get('existing_total_projection'))}</td></tr>
<tr><td>Raw 60/40 blend</td><td>{fmt(r.get('optimized_fixed_blend'))}</td></tr><tr><td>Selected bias correction</td><td>{fmt(r.get('selected_bias_correction'))}</td></tr>
<tr><td>Final Shadow total</td><td>{fmt(r.get('final_shadow_total'))}</td></tr><tr><td>Total impact vs Current Model</td><td>{fmt(r.get('total_impact'))}</td></tr>
<tr><td>Status / method</td><td>{'Ready' if pd.notna(r.get('final_shadow_total')) else 'Insufficient data'} / 60% SP+ + 40% existing + 2024 correction</td></tr>
</table></section></div></details>""")
    return f"""<!doctype html><meta charset='utf-8'><title>Blended Shadow candidate</title><style>
body{{background:#061126;color:#eef4ff;font:14px system-ui;margin:0;padding:28px}}main{{max-width:1480px;margin:auto}}.banner{{background:#0b2940;border:1px solid #267657;padding:14px;border-radius:12px}}details{{background:#0b1b36;border:1px solid #244873;border-radius:10px;margin:10px 0}}summary{{padding:14px;cursor:pointer}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:0 14px 14px}}section{{background:#081932;padding:12px;border-radius:8px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:6px;border-bottom:1px solid #18385d}}th{{color:#9eb4d4;text-align:left}}td:last-child{{text-align:right}}.green{{color:#43df96}}.yellow{{color:#ffc45b}}.red{{color:#ff7280}}.gray{{color:#91a6c6}}.openers{{overflow:auto;margin:16px 0;background:#0b1b36;padding:10px;border-radius:10px}}.openers table{{min-width:950px}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}</style><main><h1>Local blended Shadow candidate</h1><div class='banner'>Research only · no production JSON or page changed.<br>Spread: 50% market fair + 50% updated SP+ fair. Total: 60% SP+ component + 40% existing total + {summary['total_correction']}.</div><div class='openers'><h2>Openers Shadow fields</h2><table><tr><th>Week</th><th>Matchup</th><th>Current Model</th><th>Shadow Spread</th><th>Spread Impact</th><th>Current Total</th><th>Shadow Total</th><th>Total Impact</th></tr>{''.join(openers)}</table></div><h2>Schedule expanded-detail preview</h2>{''.join(cards)}</main>"""


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output-dir",default="data/research/shadow_blended_live_candidate"); args=ap.parse_args()
    out=ROOT/args.output_dir; build=ROOT/"build/research/shadow_blended_live_candidate"; out.mkdir(parents=True,exist_ok=True); build.mkdir(parents=True,exist_ok=True)
    before={p:sha(ROOT/p) for p in PROTECTED}
    s=pd.read_csv(SPREAD); t=pd.read_csv(TOTAL); t, correction, pick, detail=choose_total_correction(t)
    keys=["season","week","game_id","away_team","home_team"]
    d=s.merge(t,on=keys,how="outer",suffixes=("","_total"))
    d["current_model_spread"]=d.no_update_market_spread
    d["spread_impact"]=d.simple_blend-d.current_model_spread
    d["current_model_total"]=d.existing_total_projection
    d["total_impact"]=d.final_shadow_total-d.current_model_total
    d["spread_confidence_color"]=d.apply(agreement,axis=1)
    d["projection_readiness"]=np.where(d.simple_blend.notna(),"Ready","Insufficient data")
    d["missing_data_reason"]=np.where(d.simple_blend.notna(),"", "market and/or SP+ component unavailable")
    d.to_csv(out/"game_level_audit.csv",index=False)
    (out/"candidate_games.json").write_text(d.replace({np.nan:None}).to_json(orient="records"))
    correction.to_csv(out/"total_bias_correction_comparison.csv",index=False)
    common=d[(d.season==2025)&d[["no_update_market_spread","current_lambda_050_spread","market_fair_spread","sp_plus_fair_spread","simple_blend","actual_close"]].notna().all(axis=1)]
    recon=[]
    for name,col in [("frozen_no_update","no_update_market_spread"),("current_lambda_0.50","current_lambda_050_spread"),("predicted_market","market_fair_spread"),("predicted_SP+","sp_plus_fair_spread"),("aligned_simple_average","simple_blend"),("timing_unknown_ESPN_Bet_open","historical_espn_bet_opening_field")]:
        recon.append({"model":name,**metrics(common.actual_close,common[col])})
    pd.DataFrame(recon).to_csv(out/"spread_lambda_reconciliation.csv",index=False)
    hold=t[(t.season==2025)&t.identical_sample.fillna(False).astype(bool)&t.actual_close.notna()&t.final_shadow_total.notna()]
    summ={"generated_at":datetime.now(timezone.utc).isoformat(),"research_only":True,
          "spread_formula":"0.50 * predicted market-rating fair home spread + 0.50 * predicted updated-SP+ fair home spread",
          "total_formula":"0.60 * predicted SP+ component total + 0.40 * existing projected total + selected 2024 correction",
          "total_correction_selection":pick,"total_correction":detail,"locked_2025_corrected_total":metrics(hold.actual_close,hold.final_shadow_total),
          "lambda_reconciliation_cause":"The old lambda=0.50 artifact applies 50% of raw prior-game ATS movement independently to each team. It is an unregularized team-level adjustment, not the 50/50 average of reconstructed market and SP+ matchup fair spreads; no HFA duplication or sign reversal was found.",
          "spread_confidence_colors":{"green":"Same meaningful direction","yellow":"Valid projection without same-direction meaningful agreement","red":"Opposite meaningful directions","gray":"Pending/incomplete"},
          "protected_hashes_before":before}
    (out/"summary.json").write_text(json.dumps(summ,indent=2))
    (build/"index.html").write_text(render_html(d[d.season.eq(2025)].sort_values(["week","game_id"]),summ))
    after={p:sha(ROOT/p) for p in PROTECTED}; summ["protected_hashes_after"]=after; summ["protected_unchanged"]=before==after
    (out/"summary.json").write_text(json.dumps(summ,indent=2))
    print(json.dumps({"rows":len(d),"correction":pick,"holdout":summ["locked_2025_corrected_total"],"protected_unchanged":before==after},indent=2))

if __name__ == "__main__": main()
