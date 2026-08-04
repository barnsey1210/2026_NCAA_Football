#!/usr/bin/env python3
"""Build an isolated, no-look-ahead projected-close Saturday Shadow replay."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
GAMES = ROOT / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"
SPREAD_BASE = ROOT / "data/research/market_implied_ratings/holdout_2025_predictions.csv"
SPREAD_HISTORY = ROOT / "data/ratings/market_implied_ratings_history.csv"
SPREAD_DELTA = ROOT / "data/research/postgame_pbp_market_rating_update_2021_2024/holdout_2025_predictions.csv"
TOTAL_ROWS = ROOT / "data/research/postgame_total_market_update_baseline_aware_2021_2025/holdout_2025_predictions_baseline_aware.csv"
TOTAL_MODEL = ROOT / "scripts/research/analyze_postgame_total_market_update.py"
PBP = ROOT / "data/research/pbp_history_2021_2025/team_game_tendencies.csv"
CONFIG = ROOT / "config/market_shadow_production.json"
POST_OPENER_SUMMARY = ROOT / "data/site/dry_run/shadow_market_replay_summary.json"
PUBLIC_REPO = Path("/Users/jameslindesmith/Sites/NCAAF_SITE")
TOLERANCE = 0.25
HFA = 2.5


def finite(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def norm_id(value):
    text = str(value or "").strip()
    return text[:-2] if text.endswith(".0") else text


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if value is None or (not isinstance(value, (str, bool)) and pd.isna(value)):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def protected_paths():
    fixed = [
        ROOT / "schedule_v2.html",
        ROOT / "build/public_site/schedule.html",
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
            if path.is_file() and ("2026" in path.name or path.name in {"ratings_latest.csv", "ratings_trend_latest.csv"}):
                dynamic.append(path)
    return sorted(set(fixed + dynamic))


def repo_state():
    status = subprocess.run(["git", "-C", str(PUBLIC_REPO), "status", "--short"], check=True, capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", str(PUBLIC_REPO), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    return {"path": str(PUBLIC_REPO), "head": head, "status_short": status}


def load_total_module():
    spec = importlib.util.spec_from_file_location("shadow_total_model", TOTAL_MODEL)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def direction(delta):
    if delta is None:
        return None
    if abs(delta) <= TOLERANCE:
        return "unchanged"
    return "toward_home" if delta < 0 else "toward_away"


def total_direction(delta):
    if delta is None:
        return None
    if abs(delta) <= TOLERANCE:
        return "unchanged"
    return "over" if delta > 0 else "under"


def signal_class(predicted, actual):
    if predicted is None or actual is None:
        return "ineligible"
    if abs(predicted) <= TOLERANCE:
        return "unchanged_tolerance"
    if abs(actual) <= TOLERANCE:
        return "actual_no_move"
    if math.copysign(1, predicted) != math.copysign(1, actual):
        return "wrong_direction"
    if abs(predicted) > abs(actual) + TOLERANCE:
        return "correct_overshot"
    if abs(predicted) < abs(actual) - TOLERANCE:
        return "correct_undershot"
    return "correct_direction"


def clv_for_signal(predicted_move, actual_move):
    if predicted_move is None or actual_move is None or abs(predicted_move) <= TOLERANCE:
        return None
    return (1 if predicted_move > 0 else -1) * actual_move


def market_metrics(rows, prefix):
    eligible = [r for r in rows if r.get(f"projected_{prefix}_close") is not None and r.get(f"actual_{prefix}_close") is not None]
    errors = [abs(r[f"projected_{prefix}_close"] - r[f"actual_{prefix}_close"]) for r in eligible]
    signed = [r[f"projected_{prefix}_close"] - r[f"actual_{prefix}_close"] for r in eligible]
    direction_rows = [r for r in eligible if r.get(f"{prefix}_signal_class") in {"correct_direction", "correct_overshot", "correct_undershot", "wrong_direction"}]
    bet_rows = [r for r in eligible if r.get(f"{prefix}_signal_class") not in {"ineligible", "unchanged_tolerance"}]
    correct = [r for r in direction_rows if str(r[f"{prefix}_signal_class"]).startswith("correct")]
    clv = [r[f"{prefix}_opener_clv"] for r in bet_rows if r.get(f"{prefix}_opener_clv") is not None]
    classes = {}
    for row in eligible:
        key = row.get(f"{prefix}_signal_class") or "ineligible"
        classes[key] = classes.get(key, 0) + 1
    return {
        "eligible_games": len(eligible),
        "projected_close_mae": sum(errors) / len(errors) if errors else None,
        "projected_close_median_absolute_error": statistics.median(errors) if errors else None,
        "average_signed_error": sum(signed) / len(signed) if signed else None,
        "direction_signal_games": len(direction_rows),
        "correct_directional_signals": len(correct),
        "direction_agreement_pct": 100 * len(correct) / len(direction_rows) if direction_rows else None,
        "signal_classes": classes,
        "average_absolute_predicted_move": sum(abs(r[f"projected_{prefix}_move"]) for r in eligible if r.get(f"projected_{prefix}_move") is not None) / max(1, sum(r.get(f"projected_{prefix}_move") is not None for r in eligible)),
        "average_absolute_actual_move": sum(abs(r[f"actual_{prefix}_move"]) for r in eligible if r.get(f"actual_{prefix}_move") is not None) / max(1, sum(r.get(f"actual_{prefix}_move") is not None for r in eligible)),
        "positive_clv_bets": sum(v > TOLERANCE for v in clv),
        "positive_clv_pct": 100 * sum(v > TOLERANCE for v in clv) / len(clv) if clv else None,
        "average_clv_points": sum(clv) / len(clv) if clv else None,
    }


def actual_metrics(rows, prefix):
    errors = [r.get(f"{prefix}_actual_result_error") for r in rows]
    errors = [v for v in errors if v is not None]
    return {"games": len(errors), "mae": sum(errors) / len(errors) if errors else None}


def label_spread(home_team, away_team, home_spread):
    if home_spread is None:
        return "—"
    if abs(home_spread) <= 0.05:
        return "Pick'em"
    return f"{home_team if home_spread < 0 else away_team} {(-abs(home_spread)):+.1f}"


def common_css(min_width=1450):
    return f"""
:root{{--bg:#07152c;--panel:#102746;--panel2:#091d38;--line:#28517c;--text:#f4f7ff;--muted:#9db0cf;--green:#40e39a;--amber:#ffc45c;--red:#ff7383;--purple:#b57cff}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif}}main{{max-width:1900px;margin:auto;padding:18px}}h1{{font-size:40px;margin:20px 0 4px}}.muted{{color:var(--muted)}}
.banner{{border:2px solid #ffb347;background:#38270d;color:#ffe4ad;padding:14px 18px;border-radius:12px;font-weight:900;letter-spacing:.04em}}.meta{{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}}.chip{{border:1px solid var(--line);background:var(--panel2);padding:8px 12px;border-radius:999px}}
details{{border:1px solid #267a58;background:#0b302d;padding:10px 14px;border-radius:11px;margin:12px 0}}summary{{cursor:pointer;font-weight:800}}.wrap{{overflow:auto;border:1px solid var(--line);border-radius:14px}}table{{width:100%;border-collapse:collapse;min-width:{min_width}px}}th{{position:sticky;top:0;background:#19365d;color:#bcd0ef;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;z-index:2}}th,td{{padding:10px 9px;border-bottom:1px solid #21466f;white-space:nowrap}}tbody tr:nth-child(even){{background:#0b1f3a}}.good{{color:var(--green);font-weight:800}}.bad{{color:var(--red);font-weight:800}}.warn{{color:var(--amber);font-weight:800}}.projected{{color:var(--green);font-weight:900}}.actual{{color:var(--purple);font-weight:800}}.small{{font-size:12px}}.detailgrid{{display:grid;grid-template-columns:repeat(4,minmax(160px,1fr));gap:8px;white-space:normal}}.detailgrid div{{background:#071a33;border-radius:8px;padding:8px}}@media(max-width:700px){{main{{padding:10px}}h1{{font-size:29px}}.banner{{font-size:12px}}th,td{{padding:8px 7px}}.detailgrid{{grid-template-columns:1fr 1fr}}}}
"""


def schedule_preview_html(built_at):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Historical Completed-Week Shadow Replay</title><style>{common_css(1500)}.result{{font-weight:900}}</style></head><body><main>
<div class="banner">HISTORICAL COMPLETED-WEEK SHADOW REPLAY — NOT LIVE DATA</div><h1>Schedule · Week 13 Replay</h1><p class="muted">Completed 2025 Week 13 results feeding the projected 2025 Week 14 closing market.</p>
<div class="meta"><span class="chip">Simulated cutoff: after Week 13 completion</span><span class="chip">Spread λ 0.50</span><span class="chip">Both-prior total λ 0.85</span><span class="chip">Built {built_at}</span><span class="chip" id="count">Loading…</span></div>
<details id="status"><summary>Schedule replay provenance</summary><div id="statusBody" class="muted">Loading…</div></details><div class="wrap"><table><thead><tr><th>Date</th><th>Matchup</th><th>Live Score</th><th>Closing Spread / ATS</th><th>Closing Total / O-U</th><th>Team Spread Impacts</th><th>Downstream Total</th><th>Next-week Readiness</th><th>Data Status</th></tr></thead><tbody id="rows"></tbody></table></div>
<script>const base='../../../data/site/dry_run/projected_close/';const n=v=>v==null?'—':Number(v).toFixed(1);const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}}[c]));
Promise.all(['postgame_shadow_updates.json','schedule_live_enrichment.json'].map(f=>fetch(base+f).then(r=>{{if(!r.ok)throw Error(f+' '+r.status);return r.json()}}))).then(([post,p])=>{{const g=p.completed_games||[];document.querySelector('#count').textContent=g.length+' completed games';document.querySelector('#status summary').textContent=`Schedule replay · ${{post.summary.teams_receiving_spread_impacts}} team spread impacts · ${{post.summary.target_games_receiving_combined_total_update}} downstream total updates`;document.querySelector('#statusBody').textContent='Week 13 closing lines, final results, and eligible PBP feed only the isolated dry-run payloads.';
document.querySelector('#rows').innerHTML=g.map(x=>`<tr><td>${{new Date(x.date).toLocaleString([],{{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}})}}</td><td><b>${{esc(x.away_team)}} at ${{esc(x.home_team)}}</b></td><td class="result">${{x.away_score}}-${{x.home_score}}</td><td>${{n(x.closing_home_spread)}} · <span class="${{x.home_ats_result==='W'?'good':x.home_ats_result==='L'?'bad':'warn'}}">Home ${{x.home_ats_result}}</span></td><td>${{n(x.closing_total)}} · <span class="${{x.total_result==='O'?'good':x.total_result==='U'?'bad':'warn'}}">${{x.total_result}}</span></td><td>${{esc(x.away_team)}} ${{n(x.away_raw_spread_impact)}} · ${{esc(x.home_team)}} ${{n(x.home_raw_spread_impact)}}</td><td>${{x.downstream_total_updates.length?x.downstream_total_updates.map(t=>esc(t.matchup)+' '+n(t.applied_total_adjustment)).join(' · '):'—'}}</td><td class="${{x.next_week_ready?'good':'warn'}}">${{x.next_week_ready?'Ready':'No Week 14 impact'}}</td><td>${{x.pbp_status}} <details><summary>Details</summary><div class="detailgrid">${{Object.entries(x.expanded).map(([k,v])=>`<div><span class="muted">${{esc(k.replaceAll('_',' '))}}</span><br><b>${{esc(v??'—')}}</b></div>`).join('')}}</div></details></td></tr>`).join('');}}).catch(e=>{{document.querySelector('#rows').innerHTML=`<tr><td colspan="9" class="bad">${{esc(e.message)}}</td></tr>`;console.error(e)}});</script></main></body></html>"""


def openers_preview_html(built_at):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Historical Projected-Close Shadow Replay</title><style>{common_css(1880)}.badge{{border:1px solid currentColor;border-radius:999px;padding:4px 7px;font-size:11px}}</style></head><body><main>
<div class="banner">HISTORICAL PROJECTED-CLOSE SHADOW REPLAY — NOT LIVE DATA</div><h1>Openers · Projected Week 14 Close</h1><p class="muted">The Week 14 opener is evaluation-only and is never an input to the projected Shadow close.</p>
<div class="meta"><span class="chip">Week 13 completed inputs</span><span class="chip">Week 14 projected market</span><span class="chip">Simulated late-Saturday cutoff</span><span class="chip">Spread λ 0.50</span><span class="chip">Total λ 0.85</span><span class="chip">Built {built_at}</span><span class="chip" id="count">Loading…</span></div>
<details id="status"><summary>Saturday Shadow status</summary><div id="statusBody" class="muted">Loading dry-run contract…</div></details><div class="wrap"><table><thead><tr><th>Kickoff</th><th>Matchup</th><th>Projected Shadow Close Spread</th><th>Week 14 Opener Spread</th><th>Week 14 Actual Close Spread</th><th>Spread Signal</th><th>Team Spread Impacts</th><th>Projected Shadow Close Total</th><th>Week 14 Opener Total</th><th>Week 14 Actual Close Total</th><th>Total Signal</th><th>Total Adjustment</th><th>Status</th></tr></thead><tbody id="rows"></tbody></table></div>
<script>const base='../../../data/site/dry_run/projected_close/';const n=v=>v==null?'—':Number(v).toFixed(1);const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}}[c]));const cls=s=>String(s).startsWith('correct')?'good':s==='wrong_direction'?'bad':'warn';const pretty=s=>String(s||'ineligible').replaceAll('_',' ');
Promise.all(['postgame_shadow_updates.json','projected_closing_lines.json','schedule_live_enrichment.json'].map(f=>fetch(base+f).then(r=>{{if(!r.ok)throw Error(f+' '+r.status);return r.json()}}))).then(([post,p,s])=>{{const g=p.games||[];const updated=g.filter(x=>x.updated_game_eligible).length;document.querySelector('#count').textContent=`${{updated}}/${{g.length}} games updated`;document.querySelector('#status summary').textContent=`Saturday Shadow · projected close ready · ${{post.summary.teams_receiving_spread_impacts}} team spread impacts · ${{post.summary.target_games_receiving_combined_total_update}} total updates`;document.querySelector('#statusBody').innerHTML='<b>Spread:</b> frozen Week 13 market-implied ratings + Week 13 team updates + HFA. <b>Total:</b> rolling offense/defense market components + combined both-prior score/PBP update. Openers, closes, and results are evaluation only.';
document.querySelector('#rows').innerHTML=g.map(x=>`<tr><td>${{new Date(x.date).toLocaleString([],{{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}})}}</td><td><b>${{esc(x.away_team)}} at ${{esc(x.home_team)}}</b></td><td class="projected">${{esc(x.projected_spread_label)}}</td><td>${{esc(x.opening_spread_label)}}</td><td class="actual">${{esc(x.closing_spread_label)}}</td><td><span class="badge ${{cls(x.spread_signal_class)}}">${{pretty(x.spread_signal_class)}}</span></td><td>${{esc(x.away_team)}} ${{n(x.away_spread_impact)}} · ${{esc(x.home_team)}} ${{n(x.home_spread_impact)}}</td><td class="projected">${{n(x.projected_total_close)}}</td><td>${{n(x.actual_opening_total)}}</td><td class="actual">${{n(x.actual_total_close)}}</td><td><span class="badge ${{cls(x.total_signal_class)}}">${{pretty(x.total_signal_class)}}</span></td><td>${{x.total_update_eligible?'combined '+n(x.applied_total_adjustment):'—'}}</td><td class="${{x.updated_game_eligible?'good':'warn'}}">${{x.updated_game_eligible?'Updated':'Baseline only'}}</td></tr>`).join('');}}).catch(e=>{{document.querySelector('#rows').innerHTML=`<tr><td colspan="13" class="bad">${{esc(e.message)}}</td></tr>`;console.error(e)}});</script></main></body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2025)
    parser.add_argument("--completed-week", type=int, default=13)
    parser.add_argument("--target-week", type=int, default=14)
    parser.add_argument("--output-dir", default="data/site/dry_run/projected_close")
    parser.add_argument("--schedule-preview", default="build/dry_run/projected_close/schedule_shadow_replay.html")
    parser.add_argument("--openers-preview", default="build/dry_run/projected_close/openers_shadow_projected_close_replay.html")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    out = (ROOT / args.output_dir).resolve()
    schedule_preview = (ROOT / args.schedule_preview).resolve()
    openers_preview = (ROOT / args.openers_preview).resolve()
    if not out.is_relative_to((ROOT / "data/site/dry_run/projected_close").resolve()):
        raise SystemExit("Output must remain under data/site/dry_run/projected_close")
    for preview in (schedule_preview, openers_preview):
        if not preview.is_relative_to((ROOT / "build/dry_run/projected_close").resolve()):
            raise SystemExit("Preview must remain under build/dry_run/projected_close")
    if args.target_week != args.completed_week + 1:
        raise SystemExit("Target week must immediately follow completed week")
    inputs = (GAMES, SPREAD_BASE, SPREAD_HISTORY, SPREAD_DELTA, TOTAL_ROWS, TOTAL_MODEL, PBP, CONFIG)
    for path in inputs:
        if not path.exists():
            raise SystemExit(f"Missing real input: {path}")
    public_before = repo_state()
    if public_before["status_short"]:
        raise SystemExit("Publication repository is not clean")
    out.mkdir(parents=True, exist_ok=True)
    schedule_preview.parent.mkdir(parents=True, exist_ok=True)
    protected = {str(path.relative_to(ROOT)): sha256(path) for path in protected_paths() if path.exists()}
    (out / "protected_files_before.json").write_text(json.dumps({"captured_at": datetime.now(timezone.utc).isoformat(), "protected_sha256": protected, "publication_repo": public_before}, indent=2) + "\n")

    cfg = json.loads(CONFIG.read_text())
    games = pd.read_csv(GAMES, low_memory=False)
    completed = games[(games.season == args.season) & (games.week == args.completed_week)].copy()
    target = games[(games.season == args.season) & (games.week == args.target_week)].copy()
    if args.strict and (len(completed) != 60 or len(target) != 67):
        raise SystemExit(f"Strict coverage failed: completed={len(completed)} target={len(target)}")
    completed_ids = {norm_id(v) for v in completed.game_id}
    completed_by_id = {norm_id(r.game_id): r for r in completed.itertuples(index=False)}
    target_by_id = {norm_id(r.game_id): r for r in target.itertuples(index=False)}

    spread_base = pd.read_csv(SPREAD_BASE, low_memory=False)
    spread_base = spread_base[(spread_base.season == args.season) & (spread_base.week == args.target_week)].copy()
    spread_base["game_id"] = spread_base.game_id.map(norm_id)
    spread_base_by_id = {r.game_id: r for r in spread_base.itertuples(index=False)}
    history = pd.read_csv(SPREAD_HISTORY, low_memory=False)
    history = history[(history.season == args.season) & (history.through_week == args.completed_week)].copy()
    rating_by_team = {str(r.team): finite(r.market_implied_rating) for r in history.itertuples(index=False)}

    spread_delta = pd.read_csv(SPREAD_DELTA, low_memory=False)
    spread_delta = spread_delta[(spread_delta.season == args.season) & (spread_delta.week == args.completed_week)].copy()
    spread_by_team = {}
    for r in spread_delta.itertuples(index=False):
        raw = finite(r.score_prediction)
        if raw is not None and norm_id(r.game_id) in completed_ids:
            spread_by_team[str(r.team)] = {"raw": raw, "pbp_reference": finite(r.score_pbp_prediction), "game_id": norm_id(r.game_id), "opponent": str(r.opponent)}

    total_predictions = pd.read_csv(TOTAL_ROWS, low_memory=False)
    total_predictions = total_predictions[(total_predictions.season == args.season) & (total_predictions.week == args.target_week)].copy()
    total_predictions["game_id"] = total_predictions.game_id.map(norm_id)
    total_by_id = {r.game_id: r for r in total_predictions.itertuples(index=False)}
    total_module = load_total_module()
    eligible_games = games[games.closing_total.notna() & games.closing_home_spread.notna()].copy()
    total_models = total_module.total_predictions(eligible_games)
    total_model = total_models[(args.season, args.target_week)]

    game_rows = []
    for g in target.sort_values(["start_date", "game_id"]).itertuples(index=False):
        gid = norm_id(g.game_id)
        spread_row = spread_base_by_id.get(gid)
        frozen_spread = finite(spread_row.predicted_home_spread) if spread_row else None
        home_rating, away_rating = rating_by_team.get(str(g.home_team)), rating_by_team.get(str(g.away_team))
        reproduced_spread = -(home_rating - away_rating + HFA) if home_rating is not None and away_rating is not None else None
        home_update, away_update = spread_by_team.get(str(g.home_team)), spread_by_team.get(str(g.away_team))
        home_impact = -cfg["spread_lambda"] * home_update["raw"] if home_update else None
        away_impact = cfg["spread_lambda"] * away_update["raw"] if away_update else None
        spread_delta_applied = ((home_impact or 0) + (away_impact or 0)) if home_update or away_update else 0.0
        projected_spread = frozen_spread + spread_delta_applied if frozen_spread is not None else None

        intercept = finite(total_model["intercept"])
        home_off = finite(total_model["off"].get(str(g.home_team), 0.0))
        away_off = finite(total_model["off"].get(str(g.away_team), 0.0))
        home_def = finite(total_model["def"].get(str(g.home_team), 0.0))
        away_def = finite(total_model["def"].get(str(g.away_team), 0.0))
        home_points_prior = intercept + home_off + away_def
        away_points_prior = intercept + away_off + home_def
        frozen_total = home_points_prior + away_points_prior
        total_row = total_by_id.get(gid)
        total_source_ids = [norm_id(total_row.home_prev_game_id), norm_id(total_row.away_prev_game_id)] if total_row else []
        total_sources_week13 = bool(total_source_ids) and all(v in completed_ids for v in total_source_ids)
        total_raw = finite(total_row.score_plus_pbp_prediction) if total_row and str(total_row.prior_data_state) == "both_prior" and total_sources_week13 else None
        total_applied = cfg["total_lambda_both_prior"] * total_raw if total_raw is not None else 0.0
        projected_total = frozen_total + total_applied
        opener_spread, close_spread = finite(g.opening_home_spread), finite(g.closing_home_spread)
        opener_total, close_total = finite(g.opening_total), finite(g.closing_total)
        actual_margin = finite(g.home_score) - finite(g.away_score)
        actual_total = finite(g.home_score) + finite(g.away_score)
        spread_move_pred = projected_spread - opener_spread if None not in (projected_spread, opener_spread) else None
        spread_move_actual = close_spread - opener_spread if None not in (close_spread, opener_spread) else None
        total_move_pred = projected_total - opener_total if None not in (projected_total, opener_total) else None
        total_move_actual = close_total - opener_total if None not in (close_total, opener_total) else None
        updated = bool(home_update or away_update or total_raw is not None)
        row = {
            "dry_run": True, "season": args.season, "completed_week": args.completed_week, "target_week": args.target_week,
            "game_id": gid, "date": str(g.start_date), "away_team": str(g.away_team), "home_team": str(g.home_team),
            "neutral_site": None, "neutral_site_status": "not_available_in_frozen_source", "hfa_used": HFA,
            "frozen_preopener_spread_baseline": frozen_spread, "frozen_spread_reproduced_from_ratings": reproduced_spread,
            "home_market_implied_rating_through_week_13": home_rating, "away_market_implied_rating_through_week_13": away_rating,
            "away_raw_spread_impact": away_update["raw"] if away_update else None, "home_raw_spread_impact": home_update["raw"] if home_update else None,
            "away_spread_impact": away_impact, "home_spread_impact": home_impact, "applied_spread_delta": spread_delta_applied,
            "projected_spread_close": projected_spread, "actual_opening_spread": opener_spread, "actual_spread_close": close_spread,
            "projected_spread_move": spread_move_pred, "actual_spread_move": spread_move_actual,
            "predicted_spread_movement_direction": direction(spread_move_pred), "actual_spread_movement_direction": direction(spread_move_actual),
            "spread_direction_agreement": direction(spread_move_pred) == direction(spread_move_actual) if None not in (spread_move_pred, spread_move_actual) else None,
            "spread_signal_class": signal_class(spread_move_pred, spread_move_actual), "spread_projected_close_error": abs(projected_spread-close_spread) if None not in (projected_spread, close_spread) else None,
            "spread_opener_clv": clv_for_signal(spread_move_pred, spread_move_actual),
            "projected_spread_label": label_spread(str(g.home_team), str(g.away_team), projected_spread),
            "opening_spread_label": label_spread(str(g.home_team), str(g.away_team), opener_spread),
            "closing_spread_label": label_spread(str(g.home_team), str(g.away_team), close_spread),
            "frozen_preopener_total_baseline": frozen_total, "total_intercept": intercept,
            "home_offensive_prior": home_off, "away_offensive_prior": away_off, "home_defensive_prior": home_def, "away_defensive_prior": away_def,
            "home_expected_points_component": home_points_prior, "away_expected_points_component": away_points_prior,
            "offense_defense_matchup_formula": "home=intercept+home offense+away defense; away=intercept+away offense+home defense",
            "pbp_fields_used": list(total_module.PBPV), "combined_total_adjustment_raw": total_raw, "applied_total_adjustment": total_applied,
            "projected_total_close": projected_total, "actual_opening_total": opener_total, "actual_total_close": close_total,
            "projected_total_move": total_move_pred, "actual_total_move": total_move_actual,
            "predicted_total_movement_direction": total_direction(total_move_pred), "actual_total_movement_direction": total_direction(total_move_actual),
            "total_direction_agreement": total_direction(total_move_pred) == total_direction(total_move_actual) if None not in (total_move_pred, total_move_actual) else None,
            "total_signal_class": signal_class(total_move_pred, total_move_actual), "total_projected_close_error": abs(projected_total-close_total) if None not in (projected_total, close_total) else None,
            "total_opener_clv": clv_for_signal(total_move_pred, total_move_actual),
            "actual_home_margin": actual_margin, "actual_total_result": actual_total,
            "spread_actual_result_error": abs((-projected_spread)-actual_margin) if None not in (projected_spread, actual_margin) else None,
            "total_actual_result_error": abs(projected_total-actual_total) if None not in (projected_total, actual_total) else None,
            "updated_game_eligible": updated, "spread_update_eligible": bool(home_update or away_update), "total_update_eligible": total_raw is not None,
            "status": "updated" if updated else "baseline_only",
            "provenance": {
                "frozen_spread_baseline": str(SPREAD_BASE.relative_to(ROOT)), "spread_rating_snapshot": str(SPREAD_HISTORY.relative_to(ROOT)),
                "spread_update": str(SPREAD_DELTA.relative_to(ROOT)), "frozen_total_baseline_formula": str(TOTAL_MODEL.relative_to(ROOT)),
                "total_update": str(TOTAL_ROWS.relative_to(ROOT)), "pbp": str(PBP.relative_to(ROOT)), "market_evaluation": str(GAMES.relative_to(ROOT)),
                "spread_source_game_ids": [v["game_id"] for v in (away_update, home_update) if v], "total_source_game_ids": total_source_ids,
                "week14_opener_used_as_input": False, "week14_close_used_as_input": False, "week14_result_used_as_input": False,
            },
            "look_ahead_checks": {"frozen_spread_through_week": args.completed_week, "frozen_total_training_week_lt": args.target_week, "postgame_sources_all_completed_week": True},
        }
        game_rows.append(row)

    team_updates = []
    for team, info in sorted(spread_by_team.items()):
        source = completed_by_id[info["game_id"]]
        team_updates.append({
            "team": team, "opponent": info["opponent"], "completed_game_id": info["game_id"],
            "final_score": f"{int(source.away_score)}-{int(source.home_score)}", "raw_spread_impact": info["raw"],
            "applied_spread_impact_team_perspective": cfg["spread_lambda"] * info["raw"], "score_pbp_reference_not_applied": info["pbp_reference"],
            "total_impact": None, "total_status": "combined_target_game_only", "provenance": str(SPREAD_DELTA.relative_to(ROOT)),
        })

    downstream_by_source = {}
    for row in game_rows:
        if row["total_update_eligible"]:
            for source_id in row["provenance"]["total_source_game_ids"]:
                downstream_by_source.setdefault(source_id, []).append({"target_game_id": row["game_id"], "matchup": f"{row['away_team']} at {row['home_team']}", "raw_total_adjustment": row["combined_total_adjustment_raw"], "applied_total_adjustment": row["applied_total_adjustment"]})

    completed_rows = []
    for g in completed.sort_values(["start_date", "game_id"]).itertuples(index=False):
        gid = norm_id(g.game_id)
        away_update, home_update = spread_by_team.get(str(g.away_team)), spread_by_team.get(str(g.home_team))
        margin, total_points = finite(g.home_score)-finite(g.away_score), finite(g.home_score)+finite(g.away_score)
        ats_margin, total_margin = margin + finite(g.closing_home_spread), total_points - finite(g.closing_total)
        expanded = {
            "opening_spread": finite(g.opening_home_spread), "closing_spread": finite(g.closing_home_spread),
            "market_baseline_spread": finite(g.closing_home_spread), "raw_spread_delta_away": away_update["raw"] if away_update else None,
            "raw_spread_delta_home": home_update["raw"] if home_update else None,
            "applied_spread_impact_away": cfg["spread_lambda"] * away_update["raw"] if away_update else None,
            "applied_spread_impact_home": cfg["spread_lambda"] * home_update["raw"] if home_update else None,
            "next_projected_close_contribution": "team contributions appear in Week 14 projected_closing_lines.json",
            "opening_total": finite(g.opening_total), "closing_total": finite(g.closing_total), "market_baseline_total": finite(g.closing_total),
            "raw_total_pbp_delta": "combined at downstream matchup", "applied_total_impact": "combined at downstream matchup",
            "next_shadow_total": "see downstream total updates", "cfbd_status": "historical final available", "pbp_status": "eligible history available",
            "spread_status": "eligible" if away_update or home_update else "missing", "total_status": "traceable downstream combined update" if gid in downstream_by_source else "no eligible Week 14 both-prior target",
            "provenance": str(GAMES.relative_to(ROOT)),
        }
        completed_rows.append({
            "dry_run": True, "season": args.season, "week": args.completed_week, "game_id": gid, "date": str(g.start_date),
            "away_team": str(g.away_team), "home_team": str(g.home_team), "away_score": int(g.away_score), "home_score": int(g.home_score),
            "opening_home_spread": finite(g.opening_home_spread), "closing_home_spread": finite(g.closing_home_spread),
            "home_ats_margin": ats_margin, "home_ats_result": "W" if ats_margin > TOLERANCE else "L" if ats_margin < -TOLERANCE else "P",
            "opening_total": finite(g.opening_total), "closing_total": finite(g.closing_total), "total_margin": total_margin,
            "total_result": "O" if total_margin > TOLERANCE else "U" if total_margin < -TOLERANCE else "P",
            "away_raw_spread_impact": away_update["raw"] if away_update else None, "home_raw_spread_impact": home_update["raw"] if home_update else None,
            "downstream_total_updates": downstream_by_source.get(gid, []), "next_week_ready": bool(away_update or home_update or gid in downstream_by_source),
            "cfbd_status": "complete", "pbp_status": "available", "spread_status": expanded["spread_status"], "total_status": expanded["total_status"], "expanded": expanded,
        })

    now = datetime.now(timezone.utc).isoformat()
    warnings = [
        "Neutral-site designation is unavailable in the frozen market source; the validated spread baseline uses its fixed 2.5-point HFA.",
        "The validated total update is a combined target-game prediction; separate team total impacts are not stored and are not fabricated.",
    ]
    postgame = {
        "dry_run": True, "schema_version": "historical-projected-close-postgame-v1", "built_at": now, "season": args.season,
        "completed_week": args.completed_week, "target_week": args.target_week, "status": "historical_projected_close_ready",
        "source_files": [str(p.relative_to(ROOT)) for p in inputs], "production_coefficients": {"spread_lambda": cfg["spread_lambda"], "total_lambda_both_prior": cfg["total_lambda_both_prior"]},
        "warnings": warnings, "updates": team_updates,
        "summary": {"completed_games_used": len(completed), "teams_evaluated": len(set(completed.home_team)|set(completed.away_team)), "teams_receiving_spread_impacts": len(team_updates), "teams_receiving_separable_total_impacts": 0, "target_games_receiving_combined_total_update": sum(r["total_update_eligible"] for r in game_rows)},
    }
    lines = {
        "dry_run": True, "schema_version": "historical-projected-closing-lines-v1", "built_at": now, "season": args.season,
        "completed_week": args.completed_week, "target_week": args.target_week, "direction_tolerance_points": TOLERANCE,
        "spread_formula": "-(home market rating through Week 13 - away market rating through Week 13 + 2.5 HFA) + 0.50*(-home raw update + away raw update)",
        "total_formula": "2*intercept + home offense + away defense + away offense + home defense + 0.85*combined both-prior score-plus-PBP update",
        "opener_role": "evaluation_only", "close_role": "evaluation_only", "result_role": "secondary_diagnostic_only", "games": game_rows,
    }
    schedule = {"dry_run": True, "schema_version": "historical-projected-close-schedule-v1", "built_at": now, "season": args.season, "completed_week": args.completed_week, "target_week": args.target_week, "completed_games": completed_rows, "target_games": game_rows}

    audit_rows = []
    for r in game_rows:
        audit_rows.append({
            "season": r["season"], "completed_week": r["completed_week"], "target_week": r["target_week"], "game_id": r["game_id"], "date": r["date"], "away_team": r["away_team"], "home_team": r["home_team"],
            "frozen_preopener_spread_baseline": r["frozen_preopener_spread_baseline"], "away_spread_impact": r["away_spread_impact"], "home_spread_impact": r["home_spread_impact"], "applied_spread_delta": r["applied_spread_delta"],
            "projected_spread_close": r["projected_spread_close"], "actual_opening_spread": r["actual_opening_spread"], "actual_spread_close": r["actual_spread_close"], "projected_spread_move": r["projected_spread_move"], "actual_spread_move": r["actual_spread_move"], "spread_signal_class": r["spread_signal_class"], "spread_projected_close_error": r["spread_projected_close_error"], "spread_opener_clv": r["spread_opener_clv"],
            "frozen_preopener_total_baseline": r["frozen_preopener_total_baseline"], "combined_total_adjustment_raw": r["combined_total_adjustment_raw"], "applied_total_adjustment": r["applied_total_adjustment"], "projected_total_close": r["projected_total_close"], "actual_opening_total": r["actual_opening_total"], "actual_total_close": r["actual_total_close"], "projected_total_move": r["projected_total_move"], "actual_total_move": r["actual_total_move"], "total_signal_class": r["total_signal_class"], "total_projected_close_error": r["total_projected_close_error"], "total_opener_clv": r["total_opener_clv"],
            "actual_home_margin": r["actual_home_margin"], "spread_actual_result_error": r["spread_actual_result_error"], "actual_total": r["actual_total_result"], "total_actual_result_error": r["total_actual_result_error"], "updated_game_eligible": r["updated_game_eligible"], "status": r["status"], "provenance": json.dumps(r["provenance"], sort_keys=True),
        })

    spread_metrics, total_metrics = market_metrics(game_rows, "spread"), market_metrics(game_rows, "total")
    def ranked(prefix, classes=None, reverse=True):
        rows = [r for r in game_rows if r.get(f"{prefix}_opener_clv") is not None and (classes is None or r.get(f"{prefix}_signal_class") in classes)]
        return [{"game_id": r["game_id"], "game": f"{r['away_team']} at {r['home_team']}", "signal_class": r[f"{prefix}_signal_class"], "clv": r[f"{prefix}_opener_clv"], "predicted_move": r[f"projected_{prefix}_move"], "actual_move": r[f"actual_{prefix}_move"]} for r in sorted(rows, key=lambda z: z[f"{prefix}_opener_clv"], reverse=reverse)[:5]]
    existing = json.loads(POST_OPENER_SUMMARY.read_text()) if POST_OPENER_SUMMARY.exists() else {"status": "not_available"}
    summary = {
        "dry_run": True, "schema_version": "historical-projected-close-summary-v1", "built_at": now, "season": args.season, "completed_week": args.completed_week, "target_week": args.target_week,
        "headline": {"spread_direction_agreement_pct": spread_metrics["direction_agreement_pct"], "total_direction_agreement_pct": total_metrics["direction_agreement_pct"], "spread_positive_clv_pct": spread_metrics["positive_clv_pct"], "spread_average_clv": spread_metrics["average_clv_points"], "total_positive_clv_pct": total_metrics["positive_clv_pct"], "total_average_clv": total_metrics["average_clv_points"], "spread_projected_close_mae": spread_metrics["projected_close_mae"], "total_projected_close_mae": total_metrics["projected_close_mae"]},
        "A_projected_close_market_evaluation": {"spread": spread_metrics, "total": total_metrics},
        "B_opener_betting_signal_evaluation": {"tolerance_points": TOLERANCE, "spread": {k:v for k,v in spread_metrics.items() if "clv" in k or "direction" in k or "signal" in k or "move" in k}, "total": {k:v for k,v in total_metrics.items() if "clv" in k or "direction" in k or "signal" in k or "move" in k}},
        "C_actual_result_diagnostic": {"spread": actual_metrics(game_rows, "spread"), "total": actual_metrics(game_rows, "total")},
        "D_existing_post_opener_adjustment_replay": existing,
        "coverage": {"completed_games_used": len(completed_rows), "teams_receiving_spread_updates": len(team_updates), "teams_receiving_separable_total_updates": 0, "target_games": len(game_rows), "games_receiving_projected_closing_spreads": sum(r["projected_spread_close"] is not None for r in game_rows), "games_receiving_projected_closing_totals": sum(r["projected_total_close"] is not None for r in game_rows), "games_counted_as_updated": sum(r["updated_game_eligible"] for r in game_rows), "games_receiving_combined_total_updates": sum(r["total_update_eligible"] for r in game_rows)},
        "largest_correct_spread_signals": ranked("spread", {"correct_direction","correct_overshot","correct_undershot"}), "largest_wrong_spread_signals": ranked("spread", {"wrong_direction"}, reverse=False),
        "largest_correct_total_signals": ranked("total", {"correct_direction","correct_overshot","correct_undershot"}), "largest_wrong_total_signals": ranked("total", {"wrong_direction"}, reverse=False),
        "largest_spread_overshoots": ranked("spread", {"correct_overshot"}), "largest_spread_undershoots": ranked("spread", {"correct_undershot"}), "largest_total_overshoots": ranked("total", {"correct_overshot"}), "largest_total_undershoots": ranked("total", {"correct_undershot"}),
        "total_model_audit": {"separate_offensive_and_defensive_priors_exist": True, "used_in_validated_baseline": True, "home_matchup": "intercept + home offense + away defense", "away_matchup": "intercept + away offense + home defense", "postgame_adjustment_storage": "combined target-game score-plus-PBP prediction", "separate_team_update_reconstruction_legitimate": False, "future_information_used": False, "pbp_fields": list(total_module.PBPV)},
        "look_ahead_assessment": "Spread and total baselines use games from weeks before Week 14. Week 14 opener, close, and results are joined only after projected closes are calculated.",
        "limitations": warnings + ["This is one historical week and is not proof of long-term predictive value."],
    }

    for name, payload in (("postgame_shadow_updates.json", postgame), ("projected_closing_lines.json", lines), ("schedule_live_enrichment.json", schedule), ("projected_close_summary.json", summary)):
        (out / name).write_text(json.dumps(clean(payload), indent=2) + "\n")
    with (out / "projected_close_game_audit.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audit_rows[0]))
        writer.writeheader(); writer.writerows(clean(audit_rows))
    schedule_preview.write_text(schedule_preview_html(now))
    openers_preview.write_text(openers_preview_html(now))
    print(json.dumps({"completed_games": len(completed_rows), "team_spread_updates": len(team_updates), "target_games": len(game_rows), "updated_games": sum(r["updated_game_eligible"] for r in game_rows), "spread": spread_metrics, "total": total_metrics, "schedule_preview": str(schedule_preview.relative_to(ROOT)), "openers_preview": str(openers_preview.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
