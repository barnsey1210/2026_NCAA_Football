#!/usr/bin/env python3
"""Build an isolated historical replay of the market-based Saturday Shadow."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GAMES = ROOT / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"
SPREAD = ROOT / "data/research/postgame_pbp_market_rating_update_2021_2024/holdout_2025_predictions.csv"
TOTAL = ROOT / "data/research/postgame_total_market_update_baseline_aware_2021_2025/holdout_2025_predictions_baseline_aware.csv"
CONFIG = ROOT / "config/market_shadow_production.json"
PUBLIC_REPO = Path("/Users/jameslindesmith/Sites/NCAAF_SITE")
TOLERANCE = 1e-9


def finite(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def norm_id(value):
    text = str(value or "").strip()
    return text[:-2] if text.endswith(".0") else text


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_json(v) for v in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    return value


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def protected_paths():
    fixed = [
        ROOT / "openers_v2.html",
        ROOT / "build/public_site/openers.html",
        ROOT / "data/site/postgame_shadow_updates.json",
        ROOT / "data/site/saturday_shadow_lines.json",
        ROOT / "data/site/schedule_live_enrichment.json",
        ROOT / "daily_market_update.sh",
        ROOT / "scripts/publish/publish_site.sh",
    ]
    dynamic = []
    for folder in (ROOT / "data/ratings", ROOT / "data/projections"):
        for path in folder.glob("*"):
            if path.is_file() and (
                "2026" in path.name
                or path.name in {"ratings_latest.csv", "ratings_trend_latest.csv"}
            ):
                dynamic.append(path)
    return sorted(set(fixed + dynamic))


def repo_state():
    status = subprocess.run(
        ["git", "-C", str(PUBLIC_REPO), "status", "--short"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    head = subprocess.run(
        ["git", "-C", str(PUBLIC_REPO), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return {"path": str(PUBLIC_REPO), "head": head, "status_short": status}


def metric_summary(rows, prefix):
    eligible = [r for r in rows if r.get(f"baseline_{prefix}_error_to_later_market") is not None]
    if not eligible:
        return {"games": 0}
    base = [r[f"baseline_{prefix}_error_to_later_market"] for r in eligible]
    shadow = [r[f"shadow_{prefix}_error_to_later_market"] for r in eligible]
    improved = [r[f"shadow_improved_later_{prefix}_estimate"] for r in eligible]
    agreements = [r[f"{prefix}_direction_agreement"] for r in eligible if r[f"{prefix}_direction_agreement"] is not None]
    bmae, smae = sum(base) / len(base), sum(shadow) / len(shadow)
    return {
        "games": len(eligible),
        "baseline_mae_to_later_market": bmae,
        "shadow_mae_to_later_market": smae,
        "mae_improvement": bmae - smae,
        "mae_improvement_pct": 100 * (bmae - smae) / bmae if bmae else None,
        "games_improved": sum(v is True for v in improved),
        "games_worsened": sum(v is False for v in improved),
        "games_tied": sum(v is None for v in improved),
        "games_improved_pct": 100 * sum(v is True for v in improved) / len(improved),
        "direction_agreement_n": len(agreements),
        "direction_agreement_pct": 100 * sum(agreements) / len(agreements) if agreements else None,
    }


def actual_summary(rows, prefix):
    eligible = [r for r in rows if r.get(f"baseline_{prefix}_error_to_actual") is not None and r.get(f"shadow_{prefix}_error_to_actual") is not None]
    if not eligible:
        return {"games": 0}
    base = [r[f"baseline_{prefix}_error_to_actual"] for r in eligible]
    shadow = [r[f"shadow_{prefix}_error_to_actual"] for r in eligible]
    improved = [r[f"shadow_improved_actual_{prefix}_diagnostic"] for r in eligible]
    bmae, smae = sum(base) / len(base), sum(shadow) / len(shadow)
    return {
        "games": len(eligible),
        "baseline_mae_to_actual": bmae,
        "shadow_mae_to_actual": smae,
        "mae_improvement": bmae - smae,
        "mae_improvement_pct": 100 * (bmae - smae) / bmae if bmae else None,
        "games_improved_pct": 100 * sum(v is True for v in improved) / len(improved),
    }


def direction(delta):
    if delta is None:
        return None
    if abs(delta) <= TOLERANCE:
        return "unchanged"
    return "up" if delta > 0 else "down"


def compare_error(base_error, shadow_error):
    if base_error is None or shadow_error is None:
        return None
    change = base_error - shadow_error
    if abs(change) <= TOLERANCE:
        return None
    return change > 0


def preview_html(meta):
    return f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>Historical Market Shadow Dry Run</title>
<style>
:root{{--bg:#07152c;--panel:#102746;--panel2:#091d38;--line:#28517c;--text:#f4f7ff;--muted:#9db0cf;--green:#40e39a;--amber:#ffc45c;--purple:#b57cff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif}} main{{max-width:1900px;margin:auto;padding:18px}}
.banner{{border:2px solid #ffb347;background:#38270d;color:#ffe4ad;padding:14px 18px;border-radius:12px;font-weight:900;letter-spacing:.04em}}
h1{{font-size:42px;margin:22px 0 4px}} .muted{{color:var(--muted)}} .meta{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}} .chip,.tab{{border:1px solid var(--line);background:var(--panel2);padding:9px 14px;border-radius:999px;color:var(--text)}}
.tabs{{display:flex;gap:10px;margin:18px 0}} .tab{{cursor:pointer;font-weight:800}} .tab.active{{background:#1767b8;border-color:#67b4ff}} details{{border:1px solid #267a58;background:#0b302d;padding:12px 16px;border-radius:12px;margin:14px 0}} summary{{cursor:pointer;font-weight:800}}
.wrap{{overflow:auto;border:1px solid var(--line);border-radius:14px}} table{{width:100%;border-collapse:collapse;min-width:1420px}} th{{position:sticky;top:0;background:#19365d;color:#bcd0ef;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.06em}} th,td{{padding:11px 10px;border-bottom:1px solid #21466f;white-space:nowrap}} tbody tr:nth-child(even){{background:#0b1f3a}} .shadow{{color:var(--green);font-weight:900}} .later{{color:var(--purple);font-weight:800}} .impact{{font-weight:800}} .good{{color:var(--green)}} .bad{{color:#ff7383}} .pending{{color:var(--amber)}} .hidden{{display:none}}
.impactRow{{display:flex;gap:7px;align-items:center}} .teamDot{{width:22px;height:22px;border-radius:50%;background:#214b77;display:inline-grid;place-items:center;font-size:10px;font-weight:900}}
@media(max-width:700px){{main{{padding:10px}}h1{{font-size:30px}}.banner{{font-size:13px}}th,td{{padding:9px 7px}}}}
</style></head><body><main>
<div class=\"banner\">HISTORICAL MARKET SHADOW DRY RUN — NOT LIVE DATA</div>
<h1>Openers · Saturday Shadow Replay</h1><p class=\"muted\">2025 Week 13 completed results → 2025 Week 14 target market</p>
<div class=\"meta\"><span class=\"chip\">Built {meta['built_at']}</span><span class=\"chip\">Baseline: Week 14 opening consensus</span><span class=\"chip\">Later market: Week 14 closing consensus</span><span class=\"chip\" id=\"count\">Loading…</span></div>
<details id=\"status\"><summary>Saturday Shadow status</summary><div id=\"statusBody\" class=\"muted\">Loading dry-run provenance…</div></details>
<div class=\"tabs\"><button class=\"tab active\" data-view=\"shadow\">Shadow</button><button class=\"tab\" data-view=\"standard\">Standard market baseline</button></div>
<div class=\"wrap\"><table><thead><tr><th>Kickoff</th><th>Matchup</th><th class=\"shadowCol\">Shadow Spread</th><th>Market Baseline</th><th class=\"shadowCol\">Later Market</th><th class=\"shadowCol\">Spread Impacts</th><th class=\"shadowCol\">Shadow Total</th><th>Baseline Total</th><th class=\"shadowCol\">Later Total</th><th class=\"shadowCol\">Total Impact</th><th>Status</th></tr></thead><tbody id=\"rows\"></tbody></table></div>
<script>
const base='../../data/site/dry_run/'; const n=v=>v==null?'—':Number(v).toFixed(1); const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}}[c]));
Promise.all(['postgame_shadow_updates.json','saturday_shadow_lines.json','schedule_live_enrichment.json'].map(f=>fetch(base+f).then(r=>{{if(!r.ok)throw Error(f+' '+r.status);return r.json()}}))).then(([post,lines,sched])=>{{
 const games=lines.games||[]; const updated=games.filter(g=>g.updated_game_eligible).length; document.querySelector('#count').textContent=`${{updated}}/${{games.length}} games updated`;
 document.querySelector('#status summary').textContent=`Saturday Shadow · ${{post.status.replaceAll('_',' ')}} · ${{post.summary.teams_receiving_spread_impacts}} team spread updates · ${{post.summary.target_games_receiving_combined_total_update}} game total updates`;
 document.querySelector('#statusBody').innerHTML=`<p><b>Inputs:</b> Week 13 completed results and closing-game features. <b>Application:</b> Week 14 opening market + production adjustment. Week 14 closing market and results are evaluation only.</p><p>${{esc((post.warnings||[]).join(' · ')||'No warnings.')}}</p>`;
 document.querySelector('#rows').innerHTML=games.map(g=>{{ const kickoff=new Date(g.date).toLocaleString([],{{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}}); const s=[g.away_spread_impact,g.home_spread_impact].map((v,i)=>`<span class=\"teamDot\">${{esc((i?g.home_team:g.away_team).slice(0,2).toUpperCase())}}</span>${{n(v)}}`).join(' '); return `<tr><td>${{kickoff}}</td><td><b>${{esc(g.away_team)}} at ${{esc(g.home_team)}}</b></td><td class=\"shadow shadowCol\">${{n(g.shadow_spread)}}</td><td>${{n(g.historical_market_baseline_spread)}}</td><td class=\"later shadowCol\">${{n(g.later_market_spread)}}</td><td class=\"impact shadowCol\"><div class=\"impactRow\">${{s}}</div></td><td class=\"shadow shadowCol\">${{n(g.shadow_total)}}</td><td>${{n(g.historical_market_baseline_total)}}</td><td class=\"later shadowCol\">${{n(g.later_market_total)}}</td><td class=\"impact shadowCol\">${{g.raw_total_impact==null?'—':'combined '+n(g.raw_total_impact)}}</td><td class=\"${{g.updated_game_eligible?'good':'pending'}}\">${{g.updated_game_eligible?'Updated':'Baseline only'}}</td></tr>`}}).join('');
}}).catch(e=>{{document.querySelector('#rows').innerHTML=`<tr><td colspan=\"11\" class=\"bad\">${{esc(e.message)}}</td></tr>`;console.error(e)}});
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x===b));document.querySelectorAll('.shadowCol').forEach(x=>x.classList.toggle('hidden',b.dataset.view==='standard'))}});
</script></main></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2025)
    ap.add_argument("--completed-week", type=int, default=13)
    ap.add_argument("--target-week", type=int, default=14)
    ap.add_argument("--output-dir", default="data/site/dry_run")
    ap.add_argument("--preview-html", default="build/dry_run/openers_shadow_dry_run.html")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    output_dir = (ROOT / args.output_dir).resolve()
    preview = (ROOT / args.preview_html).resolve()
    allowed_output = (ROOT / "data/site/dry_run").resolve()
    allowed_preview = (ROOT / "build/dry_run").resolve()
    if not output_dir.is_relative_to(allowed_output) or not preview.is_relative_to(allowed_preview):
        raise SystemExit("Dry-run outputs must remain under data/site/dry_run and build/dry_run")
    if args.target_week != args.completed_week + 1:
        raise SystemExit("Target week must immediately follow completed week")
    for path in (GAMES, SPREAD, TOTAL, CONFIG):
        if not path.exists():
            raise SystemExit(f"Missing required real input: {path}")
    initial_repo = repo_state()
    if initial_repo["status_short"]:
        raise SystemExit("Publication repository is not clean; refusing dry run")
    output_dir.mkdir(parents=True, exist_ok=True)
    preview.parent.mkdir(parents=True, exist_ok=True)
    protected = {str(p.relative_to(ROOT)): sha256(p) for p in protected_paths() if p.exists()}
    safety = {"captured_at": datetime.now(timezone.utc).isoformat(), "protected_sha256": protected, "publication_repo": initial_repo}
    (output_dir / "protected_files_before.json").write_text(json.dumps(safety, indent=2) + "\n")

    cfg = json.loads(CONFIG.read_text())
    games = pd.read_csv(GAMES, low_memory=False)
    completed = games[(games.season == args.season) & (games.week == args.completed_week)].copy()
    target = games[(games.season == args.season) & (games.week == args.target_week)].copy()
    spread = pd.read_csv(SPREAD, low_memory=False)
    spread = spread[(spread.season == args.season) & (spread.week == args.completed_week)].copy()
    total = pd.read_csv(TOTAL, low_memory=False)
    total = total[(total.season == args.season) & (total.week == args.target_week)].copy()
    if args.strict and (len(completed) != 60 or len(target) != 67):
        raise SystemExit(f"Strict coverage failed: completed={len(completed)}, target={len(target)}")

    completed_by_id = {norm_id(r.game_id): r for r in completed.itertuples(index=False)}
    spread_by_team = {}
    for r in spread.itertuples(index=False):
        raw = finite(r.score_prediction)
        if raw is None:
            continue
        spread_by_team[str(r.team)] = {"raw": raw, "source_game_id": norm_id(r.game_id), "opponent": str(r.opponent)}
    total_by_game = {norm_id(r.game_id): r for r in total.itertuples(index=False)}

    team_updates = []
    for team, info in sorted(spread_by_team.items()):
        source = completed_by_id.get(info["source_game_id"])
        team_updates.append({
            "team": team, "opponent": info["opponent"], "completed_game_id": info["source_game_id"],
            "completed_game": f"{source.away_team} at {source.home_team}" if source else None,
            "final_score": f"{int(source.away_score)}-{int(source.home_score)}" if source else None,
            "raw_spread_impact": info["raw"], "spread_impact_status": "eligible",
            "spread_provenance": str(SPREAD.relative_to(ROOT)),
            "raw_total_impact": None, "total_impact_status": "not_separately_attributable",
            "total_provenance": "Validated total model emits one combined target-game adjustment, not team components.",
        })

    rows, audit_rows, schedule_rows = [], [], []
    for g in target.sort_values(["start_date", "game_id"]).itertuples(index=False):
        gid = norm_id(g.game_id)
        baseline_spread, later_spread = finite(g.opening_home_spread), finite(g.closing_home_spread)
        baseline_total, later_total = finite(g.opening_total), finite(g.closing_total)
        home_info, away_info = spread_by_team.get(str(g.home_team)), spread_by_team.get(str(g.away_team))
        home_raw = home_info["raw"] if home_info else None
        away_raw = away_info["raw"] if away_info else None
        home_contrib = -cfg["spread_lambda"] * home_raw if home_raw is not None else None
        away_contrib = cfg["spread_lambda"] * away_raw if away_raw is not None else None
        applied_spread_delta = (home_contrib or 0.0) + (away_contrib or 0.0) if home_info or away_info else None
        shadow_spread = baseline_spread + applied_spread_delta if baseline_spread is not None and applied_spread_delta is not None else None

        tr = total_by_game.get(gid)
        total_state = str(tr.prior_data_state) if tr is not None else "missing"
        total_source_ids = [norm_id(tr.home_prev_game_id), norm_id(tr.away_prev_game_id)] if tr is not None else []
        total_uses_completed_week = bool(total_source_ids) and all(source_id in completed_by_id for source_id in total_source_ids)
        raw_total = finite(tr.score_plus_pbp_prediction) if tr is not None and total_state == "both_prior" and total_uses_completed_week else None
        applied_total_delta = cfg["total_lambda_both_prior"] * raw_total if raw_total is not None else None
        shadow_total = baseline_total + applied_total_delta if baseline_total is not None and applied_total_delta is not None else None
        updated = applied_spread_delta is not None or applied_total_delta is not None
        actual_margin = finite(g.home_score) - finite(g.away_score) if finite(g.home_score) is not None and finite(g.away_score) is not None else None
        actual_total = finite(g.home_score) + finite(g.away_score) if finite(g.home_score) is not None and finite(g.away_score) is not None else None

        def errors(base, shadow, later):
            if None in (base, shadow, later): return (None, None, None, None)
            be, se = abs(base - later), abs(shadow - later)
            return be, se, be - se, compare_error(be, se)
        bs, ss, si, simp = errors(baseline_spread, shadow_spread, later_spread)
        bt, st, ti, timp = errors(baseline_total, shadow_total, later_total)
        spread_shadow_dir = direction(shadow_spread - baseline_spread) if shadow_spread is not None and baseline_spread is not None else None
        spread_later_dir = direction(later_spread - baseline_spread) if later_spread is not None and baseline_spread is not None else None
        total_shadow_dir = direction(shadow_total - baseline_total) if shadow_total is not None and baseline_total is not None else None
        total_later_dir = direction(later_total - baseline_total) if later_total is not None and baseline_total is not None else None

        bsa = abs(baseline_spread + actual_margin) if baseline_spread is not None and actual_margin is not None else None
        ssa = abs(shadow_spread + actual_margin) if shadow_spread is not None and actual_margin is not None else None
        bta = abs(baseline_total - actual_total) if baseline_total is not None and actual_total is not None else None
        sta = abs(shadow_total - actual_total) if shadow_total is not None and actual_total is not None else None
        # Spread values are sportsbook home lines: predicted home margin is -spread.
        row = {
            "dry_run": True, "season": args.season, "week": args.target_week, "game_id": gid,
            "date": str(g.start_date), "away_team": str(g.away_team), "home_team": str(g.home_team),
            "historical_market_baseline_spread": baseline_spread, "market_baseline_spread_field": "opening_home_spread",
            "historical_market_baseline_total": baseline_total, "market_baseline_total_field": "opening_total",
            "away_spread_impact": away_contrib, "home_spread_impact": home_contrib,
            "away_raw_postgame_spread_impact": away_raw, "home_raw_postgame_spread_impact": home_raw,
            "applied_spread_delta": applied_spread_delta, "shadow_spread": shadow_spread,
            "away_total_impact": None, "home_total_impact": None, "raw_total_impact": raw_total,
            "applied_total_delta": applied_total_delta, "shadow_total": shadow_total,
            "opening_spread": baseline_spread, "later_market_spread": later_spread, "closing_spread": later_spread,
            "opening_total": baseline_total, "later_market_total": later_total, "closing_total": later_total,
            "actual_home_margin": actual_margin, "actual_total": actual_total,
            "spread_status": "updated" if shadow_spread is not None else "missing_input",
            "total_status": "updated_combined_both_week13_prior" if shadow_total is not None else f"baseline_only_{total_state}_outside_completed_week",
            "updated_game_eligible": updated,
            "team_update_eligibility": {"away_spread": away_info is not None, "home_spread": home_info is not None, "total": raw_total is not None},
            "provenance": {
                "market_and_results": str(GAMES.relative_to(ROOT)), "spread_impacts": str(SPREAD.relative_to(ROOT)),
                "total_impact": str(TOTAL.relative_to(ROOT)), "total_source_game_ids": total_source_ids,
                "total_sources_match_completed_week": total_uses_completed_week, "coefficients": str(CONFIG.relative_to(ROOT)),
                "later_market_used_as_input": False, "actual_result_used_as_input": False,
                "total_team_attribution": "unavailable; production-validated value is combined at game level",
            },
        }
        rows.append(row)
        schedule_rows.append({
            "dry_run": True, "season": args.season, "week": args.target_week, "game_id": gid, "date": str(g.start_date),
            "kickoff_time": str(g.start_date), "away_team": str(g.away_team), "home_team": str(g.home_team),
            "fbs_fcs_status": "unknown_in_historical_source", "away_spread_impact": away_contrib,
            "home_spread_impact": home_contrib, "away_total_impact": None, "home_total_impact": None,
            "combined_total_impact": raw_total, "historical_market_baseline_spread": baseline_spread,
            "historical_market_baseline_total": baseline_total, "later_market_spread": later_spread,
            "later_market_total": later_total, "updated_game_eligible": updated,
        })
        audit_rows.append({
            "season": args.season, "completed_week": args.completed_week, "target_week": args.target_week,
            "game_id": gid, "date": str(g.start_date), "away_team": str(g.away_team), "home_team": str(g.home_team),
            "baseline_market_spread": baseline_spread, "shadow_spread": shadow_spread, "later_market_spread": later_spread,
            "baseline_spread_error_to_later_market": bs, "shadow_spread_error_to_later_market": ss,
            "spread_market_error_improvement": si, "shadow_improved_later_spread_estimate": simp,
            "baseline_market_total": baseline_total, "shadow_total": shadow_total, "later_market_total": later_total,
            "baseline_total_error_to_later_market": bt, "shadow_total_error_to_later_market": st,
            "total_market_error_improvement": ti, "shadow_improved_later_total_estimate": timp,
            "shadow_spread_movement_direction": spread_shadow_dir, "later_spread_movement_direction": spread_later_dir,
            "spread_direction_agreement": spread_shadow_dir == spread_later_dir if None not in (spread_shadow_dir, spread_later_dir) else None,
            "shadow_total_movement_direction": total_shadow_dir, "later_total_movement_direction": total_later_dir,
            "total_direction_agreement": total_shadow_dir == total_later_dir if None not in (total_shadow_dir, total_later_dir) else None,
            "actual_home_margin": actual_margin, "baseline_spread_error_to_actual": bsa,
            "shadow_spread_error_to_actual": ssa, "shadow_improved_actual_spread_diagnostic": compare_error(bsa, ssa),
            "actual_total": actual_total, "baseline_total_error_to_actual": bta,
            "shadow_total_error_to_actual": sta, "shadow_improved_actual_total_diagnostic": compare_error(bta, sta),
            "eligibility_notes": "combined total effect; team-level total attribution unavailable" if raw_total is not None else "missing eligible total adjustment",
            "provenance": f"baseline/open={GAMES.relative_to(ROOT)}; spread={SPREAD.relative_to(ROOT)}; total={TOTAL.relative_to(ROOT)}; later/close=evaluation only",
        })

    now = datetime.now(timezone.utc).isoformat()
    warnings = ["Validated total adjustment is a combined game value; separate home/away total impacts are unavailable and remain null.", "Historical source does not include an explicit FBS/FCS classification field."]
    postgame = {
        "dry_run": True, "schema_version": "historical-market-shadow-postgame-v1", "season": args.season,
        "completed_week": args.completed_week, "target_week": args.target_week, "built_at": now, "status": "historical_market_replay_ready",
        "source_files": [str(p.relative_to(ROOT)) for p in (GAMES, SPREAD, TOTAL, CONFIG)],
        "production_coefficients": {"spread_lambda": cfg["spread_lambda"], "total_lambda_both_prior": cfg["total_lambda_both_prior"]},
        "warnings": warnings, "updates": team_updates,
        "summary": {"completed_games_used": len(completed), "teams_evaluated": len(set(completed.home_team) | set(completed.away_team)),
                    "teams_receiving_spread_impacts": len(team_updates), "teams_receiving_total_impacts": 0,
                    "target_games_receiving_combined_total_update": sum(r["raw_total_impact"] is not None for r in rows)},
    }
    lines_payload = {
        "dry_run": True, "schema_version": "historical-market-shadow-lines-v1", "built_at": now,
        "season": args.season, "completed_week": args.completed_week, "target_week": args.target_week,
        "baseline_definition": "opening_home_spread and opening_total from the frozen historical game/market dataset",
        "later_market_definition": "closing_home_spread and closing_total; evaluation only",
        "production_coefficients": postgame["production_coefficients"], "games": rows,
    }
    schedule_payload = {"dry_run": True, "schema_version": "historical-market-shadow-schedule-v1", "built_at": now, "season": args.season, "week": args.target_week, "games": schedule_rows}

    spread_metrics, total_metrics = metric_summary(audit_rows, "spread"), metric_summary(audit_rows, "total")
    adjustments = lambda key: [abs(r[key]) for r in rows if r.get(key) is not None]
    ranked_spread = sorted(
        (r for r in audit_rows if r["spread_market_error_improvement"] is not None),
        key=lambda r: r["spread_market_error_improvement"],
        reverse=True,
    )
    ranked_total = sorted(
        (r for r in audit_rows if r["total_market_error_improvement"] is not None),
        key=lambda r: r["total_market_error_improvement"],
        reverse=True,
    )
    short = lambda r, p: {"game_id": r["game_id"], "game": f"{r['away_team']} at {r['home_team']}", "improvement": r[f"{p}_market_error_improvement"]}
    summary = {
        "dry_run": True, "schema_version": "historical-market-shadow-summary-v1", "built_at": now,
        "season": args.season, "completed_week": args.completed_week, "target_week": args.target_week,
        "selection_reason": "Week 13→14 has 60 completed source games, 67 target games, 118 shared-team spread inputs, and complete opening/closing spread, total, and result coverage.",
        "completed_games_used": len(completed), "teams_evaluated": len(set(completed.home_team) | set(completed.away_team)),
        "teams_with_spread_updates": len(team_updates), "teams_with_separable_total_updates": 0,
        "target_games_with_combined_total_updates": sum(r["raw_total_impact"] is not None for r in rows),
        "target_games": len(rows), "target_games_with_shadow_spread": sum(r["shadow_spread"] is not None for r in rows),
        "target_games_with_shadow_total": sum(r["shadow_total"] is not None for r in rows),
        "target_games_counted_as_updated": sum(r["updated_game_eligible"] for r in rows),
        "spread_market_evaluation": spread_metrics, "total_market_evaluation": total_metrics,
        "average_absolute_shadow_spread_adjustment": sum(adjustments("applied_spread_delta")) / len(adjustments("applied_spread_delta")),
        "average_absolute_shadow_total_adjustment": sum(adjustments("applied_total_delta")) / len(adjustments("applied_total_delta")),
        "largest_spread_improvements": [short(r, "spread") for r in ranked_spread[:5]],
        "largest_spread_regressions": [short(r, "spread") for r in ranked_spread[-5:][::-1]],
        "largest_total_improvements": [short(r, "total") for r in ranked_total[:5]],
        "largest_total_regressions": [short(r, "total") for r in ranked_total[-5:][::-1]],
        "actual_result_diagnostic": {"spread": actual_summary(audit_rows, "spread"), "total": actual_summary(audit_rows, "total")},
        "missing_data_counts": {"separable_team_total_impacts": len(rows) * 2, "explicit_fbs_fcs_classification": len(rows),
                                "baseline_spread": sum(r["historical_market_baseline_spread"] is None for r in rows),
                                "baseline_total": sum(r["historical_market_baseline_total"] is None for r in rows)},
        "look_ahead_assessment": "Opening lines are the only market baselines used. Closing lines and final results are joined after Shadow calculation and used only for evaluation.",
        "limitations": warnings + ["Opening consensus is the earliest frozen line field, but the source does not provide snapshot timestamps proving the exact simulated Saturday availability time."],
        "interpretation": "One historical week is a functional replay, not proof of long-term predictive value.",
    }

    for name, payload in (("postgame_shadow_updates.json", postgame), ("saturday_shadow_lines.json", lines_payload), ("schedule_live_enrichment.json", schedule_payload), ("shadow_market_replay_summary.json", summary)):
        (output_dir / name).write_text(json.dumps(clean_json(payload), indent=2) + "\n")
    with (output_dir / "shadow_market_replay_game_audit.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0]))
        writer.writeheader(); writer.writerows(clean_json(audit_rows))
    preview.write_text(preview_html({"built_at": now}))
    print(json.dumps({"completed_games": len(completed), "spread_team_updates": len(team_updates), "target_games": len(rows), "updated_games": sum(r["updated_game_eligible"] for r in rows), "spread": spread_metrics, "total": total_metrics, "preview": str(preview.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
