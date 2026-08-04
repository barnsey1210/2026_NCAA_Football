#!/usr/bin/env python3
"""Build shadow-only Saturday rating estimates without changing projections."""
from __future__ import annotations

import argparse, csv, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ROWS = ROOT / "data/research/postgame_pbp_market_rating_update_2021_2024/modeling_rows_2021_2025.csv"
SPREAD_SUMMARY = ROOT / "data/research/postgame_pbp_market_rating_update_2021_2024/summary.json"
TOTAL_SUMMARY = ROOT / "data/research/postgame_total_market_update_2021_2025/summary.json"
MATCHUPS = ROOT / "data/site/matchups_view.json"
FEATURES = ["team_margin", "team_closing_spread", "team_ats_margin", "abs_team_closing_spread"]

def clean(v): return str(v or "").strip()
def number(v):
    try: return float(v)
    except (TypeError, ValueError): return None
def final(v): return clean(v).lower() in {"1", "true", "yes", "final", "completed"}
def key(away, home, date): return (clean(away).casefold(), clean(home).casefold(), clean(date)[:10])

def score_predictor():
    d = pd.read_csv(ROWS, low_memory=False)
    d = d[(d.season <= 2024)].dropna(subset=FEATURES + ["target_next_market_innovation"])
    x, y = d[FEATURES].to_numpy(float), d.target_next_market_innovation.to_numpy(float)
    mean, std = x.mean(0), np.where(x.std(0) > 1e-9, x.std(0), 1)
    z = np.c_[np.ones(len(x)), (x - mean) / std]
    penalty = 20 * np.eye(z.shape[1]); penalty[0, 0] = 0
    beta = np.linalg.solve(z.T @ z + penalty, z.T @ y)
    return lambda values: float(np.r_[1, (np.asarray(values) - mean) / std] @ beta)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="data/results/game_results_2026.csv")
    ap.add_argument("--output", default="data/site/postgame_shadow_updates.json")
    ap.add_argument("--allow-synthetic", action="store_true")
    args = ap.parse_args()
    result_path, out = ROOT / args.results, ROOT / args.output
    games = json.loads(MATCHUPS.read_text()).get("games", []) if MATCHUPS.exists() else []
    by_key = {key(g["game"].get("away_team"), g["game"].get("home_team"), g["game"].get("date")): g for g in games}
    schedules = {}
    for g in games:
        for team in (g["game"].get("away_team"), g["game"].get("home_team")):
            schedules.setdefault(clean(team).casefold(), []).append(g)
    for schedule in schedules.values(): schedule.sort(key=lambda g: clean(g["game"].get("date")))
    spread = json.loads(SPREAD_SUMMARY.read_text()); total = json.loads(TOTAL_SUMMARY.read_text())
    payload = {
        "schema_version": "postgame-shadow-v1", "built_at": datetime.now(timezone.utc).isoformat(),
        "mode": "shadow_only", "applied_to_ratings": False, "applied_to_projections": False,
        "results_source": args.results,
        "spread_model": {"status": "ready", "method": "score-only: margin, close, ATS margin, spread magnitude",
            "holdout_2025": spread.get("holdout_2025_score_only", {}),
            "pbp_excluded_reason": "PBP failed incremental 2025 spread holdout"},
        "total_model": {"status": "awaiting_current_season_pbp",
            "method": "score surprises plus garbage-time-filtered PBP from both teams' prior games",
            "holdout_2025": total.get("holdout_score_plus_pbp", {})},
        "updates": [], "warnings": []}
    if not result_path.exists():
        payload["status"] = "awaiting_live_results"
        payload["warnings"].append("No live 2026 results artifact exists yet.")
    else:
        source_head = result_path.read_text(errors="ignore")[:4096].lower()
        synthetic = "dryrun" in result_path.name.lower() or "dryrun_fake" in source_head
        if synthetic and not args.allow_synthetic:
            payload["status"] = "synthetic_results_rejected"
            payload["warnings"].append("Synthetic inputs require --allow-synthetic.")
        else:
            predict = score_predictor()
            with result_path.open(newline="", encoding="utf-8-sig") as f: results = list(csv.DictReader(f))
            for r in results:
                if not final(r.get("completed")) and not final(r.get("status")): continue
                site = by_key.get(key(r.get("away_team"), r.get("home_team"), r.get("date")))
                if not site:
                    payload["warnings"].append(f"Unmatched result: {clean(r.get('away_team'))} at {clean(r.get('home_team'))}"); continue
                close = number(site.get("market", {}).get("spread", {}).get("home_line"))
                away_score, home_score = number(r.get("away_score")), number(r.get("home_score"))
                if close is None or away_score is None or home_score is None:
                    payload["warnings"].append(f"Missing close/score: {clean(r.get('away_team'))} at {clean(r.get('home_team'))}"); continue
                for team, opponent, margin, team_close in ((r.get("home_team"), r.get("away_team"), home_score-away_score, close), (r.get("away_team"), r.get("home_team"), away_score-home_score, -close)):
                    estimate = predict([margin, team_close, margin + team_close, abs(team_close)])
                    upcoming = [g for g in schedules.get(clean(team).casefold(), []) if clean(g["game"].get("date")) > clean(r.get("date"))]
                    ng = upcoming[0]["game"] if upcoming else None
                    payload["updates"].append({"team": clean(team), "opponent": clean(opponent),
                        "completed_game_id": site["game"].get("game_id"), "completed_date": clean(r.get("date"))[:10],
                        "team_margin": margin, "team_closing_spread": team_close, "team_ats_margin": margin + team_close,
                        "estimated_spread_rating_innovation": round(estimate, 2),
                        "next_game_id": ng.get("game_id") if ng else None,
                        "next_opponent": ((ng.get("away_team") if clean(ng.get("home_team")).casefold() == clean(team).casefold() else ng.get("home_team")) if ng else None),
                        "total_estimate_status": "pending_current_season_pbp", "synthetic_input": synthetic})
            payload["status"] = "dry_run_ready" if synthetic else "live_shadow_ready"
    payload["summary"] = {"completed_team_updates": len(payload["updates"]), "warnings": len(payload["warnings"])}
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"status": payload["status"], **payload["summary"]}, indent=2))

if __name__ == "__main__": main()
