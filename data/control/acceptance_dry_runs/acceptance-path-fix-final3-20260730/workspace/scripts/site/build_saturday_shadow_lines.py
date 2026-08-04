#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
CONFIG = ROOT / "config/market_shadow_production.json"
INDEX = ROOT / "v1.html"
MARKET = ROOT / "data/ratings/market_implied_ratings_latest.csv"
COMPARISON = ROOT / "data/ratings/fundamental_market_rating_comparison.csv"
POSTGAME = ROOT / "data/site/postgame_shadow_updates.json"
REPLAY = ROOT / "data/site/postgame_shadow_replay.json"
COMPONENTS = ROOT / "data/site/saturday_shadow_component_predictions.json"
OUT_JSON = ROOT / "data/site/saturday_shadow_lines.json"
OUT_CSV = ROOT / "data/site/saturday_shadow_lines.csv"
SNAPSHOT = ROOT / "data/history/saturday_shadow_line_snapshots.csv"

def norm_id(v):
    s = str(v or "").strip()
    return s[:-2] if s.endswith(".0") else s

def num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def read_db():
    html = INDEX.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit("Could not locate embedded DB in v1.html")
    return json.loads(m.group(1))

def pick_games(db):
    rows = db.get("games") or db.get("schedule") or []
    out = []
    for r in rows:
        season = int(num(r.get("season") or 2026) or 2026)
        if season != 2026:
            continue
        status = str(r.get("status") or "").lower()
        hp = num(r.get("home_points") or r.get("home_score"))
        ap = num(r.get("away_points") or r.get("away_score"))
        completed = status in {"final", "completed", "complete"} or (hp is not None and ap is not None)
        if completed:
            continue
        home = r.get("home_team") or r.get("home")
        away = r.get("away_team") or r.get("away")
        if not home or not away:
            continue
        out.append({
            "game_id": norm_id(r.get("game_id") or r.get("id")),
            "season": season,
            "week": int(num(r.get("week")) or 0),
            "date": r.get("date") or r.get("start_date"),
            "home_team": home,
            "away_team": away,
            "neutral": bool(r.get("neutral") or r.get("neutral_site")),
            "official_model_spread": num(r.get("model_spread") or r.get("projected_spread") or r.get("site_spread")),
            "official_model_total": num(r.get("model_total") or r.get("projected_total") or r.get("site_total")),
            "opening_spread": num(r.get("opening_spread") or r.get("open_spread") or r.get("market_open_spread")),
            "opening_total": num(r.get("opening_total") or r.get("open_total") or r.get("market_open_total")),
            "current_market_total": num(
                r.get("current_total")
                or r.get("market_total")
                or r.get("consensus_total")
                or r.get("best_total")
                or r.get("latest_total")
                or r.get("total_line")
                or r.get("opening_total")
                or r.get("open_total")
                or r.get("market_open_total")
            ),
            "closing_spread": num(r.get("closing_spread") or r.get("close_spread")),
            "closing_total": num(r.get("closing_total") or r.get("close_total")),
        })
    return out

def load_team_deltas():
    spread = {}
    total_by_game = {}
    source = None
    for path in (POSTGAME, REPLAY):
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        source = str(path.relative_to(ROOT))
        for r in data.get("spread_updates", []):
            team = r.get("team")
            val = num(r.get("predicted_next_market_innovation") or r.get("spread_delta"))
            if team and val is not None:
                spread[team] = {
                    "raw_delta": val,
                    "source_game_id": norm_id(data.get("game", {}).get("game_id") or r.get("source_game_id")),
                    "source": source,
                }
        tu = data.get("total_update") or {}
        for r in tu.get("next_game_predictions", []):
            gid = norm_id(r.get("next_game_id"))
            val = num(r.get("predicted_next_total_innovation"))
            if gid and val is not None:
                total_by_game[gid] = {
                    "raw_delta": val,
                    "prior_data_state": r.get("prior_data_state") or "one_prior",
                    "source": source,
                }
        if spread or total_by_game:
            break
    return spread, total_by_game, source

def load_component_predictions():
    """Load only explicitly produced, no-look-ahead component predictions.

    Missing components are intentionally not imputed from the official model or
    from the former 0.50/0.85 formulas.
    """
    if not COMPONENTS.exists():
        return {}, None
    data = json.loads(COMPONENTS.read_text())
    rows = data if isinstance(data, list) else data.get("games", [])
    return {
        norm_id(r.get("game_id")): r for r in rows if norm_id(r.get("game_id"))
    }, str(COMPONENTS.relative_to(ROOT))

def weighted_value(row, weights):
    values = {key: num(row.get(key)) for key in weights}
    missing = [key for key, value in values.items() if value is None]
    if missing:
        return None, missing
    return sum(float(weights[key]) * values[key] for key in weights), []

def market_total_baseline(game):
    current = num(game.get("current_market_total"))
    if current is not None:
        return current, "current_market_total"
    for key in ("market_baseline_total", "predicted_closing_total_baseline", "market_implied_total"):
        v = num(game.get(key))
        if v is not None:
            return v, "market_offense_defense_model"
    if game.get("official_model_total") is not None:
        return game.get("official_model_total"), "official_fallback"
    return None, "missing"

def main():
    for p in (CONFIG, INDEX, MARKET):
        if not p.exists():
            raise SystemExit(f"Missing required input: {p}")

    cfg = json.loads(CONFIG.read_text())
    db = read_db()
    games = pick_games(db)

    market = pd.read_csv(MARKET, low_memory=False)
    mr = {
        r.team: {
            "rating": num(r.market_implied_rating),
            "rank": int(num(r.market_implied_rank) or 0),
            "move_1w": num(r.get("market_move_1w")),
            "move_4w": num(r.get("market_move_4w")),
        }
        for _, r in market.iterrows()
    }

    fundamental = {}
    if COMPARISON.exists():
        comp = pd.read_csv(COMPARISON, low_memory=False)
        for _, r in comp.iterrows():
            fundamental[r.team] = {
                "fundamental_rating": num(r.get("fundamental_rating")),
                "fundamental_rank": int(num(r.get("fundamental_rank")) or 0),
                "fundamental_minus_market": num(r.get("fundamental_minus_market")),
            }

    spread_delta, total_delta, delta_source = load_team_deltas()
    components, component_source = load_component_predictions()
    rows = []

    for g in games:
        home, away = g["home_team"], g["away_team"]
        h, a = mr.get(home, {}), mr.get(away, {})
        hr, ar = h.get("rating"), a.get("rating")
        hfa = 0.0 if g["neutral"] else 2.5
        market_baseline_spread = -(hr - ar + hfa) if hr is not None and ar is not None else None

        hd = spread_delta.get(home, {}).get("raw_delta")
        ad = spread_delta.get(away, {}).get("raw_delta")
        raw_matchup_spread_delta = -hd + ad if hd is not None and ad is not None else None
        component = components.get(g["game_id"], {})
        shadow_spread = num(component.get("shadow_spread"))
        display_ready = component.get("shadow_display_ready") is True
        has_update = component.get("has_genuine_postgame_update") is True
        missing_spread_components = list(component.get("shadow_missing_reasons") or component.get("spread_missing_reasons") or [])
        applied_spread_delta = (
            shadow_spread - g["official_model_spread"]
            if shadow_spread is not None and g["official_model_spread"] is not None
            else None
        )

        total_base, total_base_source = market_total_baseline(g)
        td = total_delta.get(g["game_id"], {})
        total_state = td.get("prior_data_state")
        raw_total_delta = td.get("raw_delta")
        total_inputs = {
            "predicted_sp_plus_component_total": component.get("predicted_sp_plus_component_total"),
            "existing_projected_total": g.get("official_model_total"),
        }
        shadow_total = num(component.get("shadow_total"))
        missing_total_components = list(component.get("shadow_missing_reasons") or component.get("total_missing_reasons") or [])
        applied_total_delta = (
            shadow_total - g["official_model_total"]
            if shadow_total is not None and g["official_model_total"] is not None
            else None
        )

        if not has_update:
            spread_status = total_status = "Awaiting completed game"
        else:
            spread_status = "Complete" if shadow_spread is not None else "Unavailable — " + ", ".join(missing_spread_components or ["Postgame data incomplete"])
            total_status = "Complete" if shadow_total is not None else "Unavailable — " + ", ".join(missing_total_components or ["Postgame data incomplete"])

        opener_spread = g.get("opening_spread")
        opener_total = g.get("opening_total")
        expected_spread_clv = opener_spread - shadow_spread if opener_spread is not None and shadow_spread is not None else None
        expected_total_clv = shadow_total - opener_total if opener_total is not None and shadow_total is not None else None

        rows.append({
            **g,
            "home_market_rating": hr,
            "home_market_rank": h.get("rank"),
            "away_market_rating": ar,
            "away_market_rank": a.get("rank"),
            "home_fundamental_rating": fundamental.get(home, {}).get("fundamental_rating"),
            "away_fundamental_rating": fundamental.get(away, {}).get("fundamental_rating"),
            "home_fundamental_minus_market": fundamental.get(home, {}).get("fundamental_minus_market"),
            "away_fundamental_minus_market": fundamental.get(away, {}).get("fundamental_minus_market"),
            "market_baseline_spread": market_baseline_spread,
            "home_raw_postgame_delta": hd,
            "away_raw_postgame_delta": ad,
            "raw_matchup_spread_delta": raw_matchup_spread_delta,
            "spread_components": {key: num(component.get(key)) for key in cfg["spread_component_weights"]},
            "missing_spread_components": missing_spread_components,
            "away_spread_impact": num(component.get("away_spread_impact")),
            "home_spread_impact": num(component.get("home_spread_impact")),
            "applied_spread_delta": applied_spread_delta,
            "saturday_shadow_spread": shadow_spread,
            "expected_spread_clv": expected_spread_clv,
            "spread_status": spread_status,
            "market_baseline_total": total_base,
            "market_baseline_total_source": total_base_source,
            "raw_total_delta": raw_total_delta,
            "total_components": total_inputs,
            "missing_total_components": missing_total_components,
            "away_total_impact": num(component.get("away_total_impact")),
            "home_total_impact": num(component.get("home_total_impact")),
            "applied_total_delta": applied_total_delta,
            "saturday_shadow_total": shadow_total,
            "expected_total_clv": expected_total_clv,
            "total_data_state": total_state,
            "total_status": total_status,
            "delta_source": delta_source,
            "component_source": component_source,
            "spread_projected_market_value_score": num(component.get("spread_projected_market_value_score")),
            "total_projected_market_value_score": num(component.get("total_projected_market_value_score")),
            "shadow_spread_formula": component.get("shadow_spread_formula"),
            "spread_projection_readiness": component.get("spread_projection_readiness"),
            "market_readiness_state": component.get("market_readiness_state"),
            "market_readiness_reason": component.get("market_readiness_reason"),
            "away_component_status": component.get("away_component_status"),
            "home_component_status": component.get("home_component_status"),
            "away_predicted_sp_plus_change": num(component.get("away_predicted_sp_plus_change")),
            "home_predicted_sp_plus_change": num(component.get("home_predicted_sp_plus_change")),
            "away_update_state": component.get("away_update_state", "baseline_only"),
            "home_update_state": component.get("home_update_state", "baseline_only"),
            "completed_team_update_count": int(component.get("completed_team_update_count") or 0),
            "has_genuine_postgame_update": has_update,
            "shadow_display_ready": display_ready,
            "shadow_activation_reason": component.get("shadow_activation_reason", "awaiting_completed_game"),
            "shadow_status": component.get("shadow_status", "Awaiting completed game"),
            "shadow_missing_reasons": component.get("shadow_missing_reasons") or [],
            "spread_impact": applied_spread_delta,
            "total_impact": applied_total_delta,
            "spread_value_tier": component.get("spread_value_tier"),
            "spread_value_label": component.get("spread_value_label", "Unavailable"),
            "total_value_tier": component.get("total_value_tier"),
            "total_value_label": component.get("total_value_label", "Unavailable"),
            "current_model_spread": g.get("official_model_spread"),
            "current_model_total": g.get("official_model_total"),
            "current_market_spread": g.get("opening_spread"),
            "current_market_total": g.get("opening_total"),
            "predicted_market_rating_spread": num(component.get("predicted_market_rating_spread")),
            "predicted_updated_sp_plus_spread": num(component.get("predicted_updated_sp_plus_spread")),
            "predicted_sp_plus_component_total": num(component.get("predicted_sp_plus_component_total")),
            "raw_60_40_total": num(component.get("raw_60_40_total")),
            "total_bias_correction": num(component.get("total_bias_correction")),
            "feature_cutoff": component.get("feature_cutoff"),
            "leave_one_out_component_size": component.get("leave_one_out_component_size"),
            **{
                f"{side}_{field}": component.get(f"{side}_{field}")
                for side in ("away", "home")
                for field in (
                    "all_board_market_rating", "all_board_market_rank",
                    "market_games_in_rating", "market_sample_status",
                    "sp_plus_entering", "sp_plus_offense_entering", "sp_plus_defense_entering",
                    "predicted_sp_plus_offense_change", "predicted_sp_plus_defense_change",
                )
            },
        })

    built_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": "saturday-shadow-lines-v2",
        "built_at": built_at,
        "formulas": {
            "spread": cfg["spread_formula"],
            "total": cfg["total_formula"],
        },
        "projected_market_value": cfg["projected_market_value"],
        "primary_goal": cfg["primary_goal"],
        "blend_market_into_fundamental": False,
        "games": rows,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)

    snap = pd.DataFrame(rows)
    snap["snapshot_timestamp"] = built_at
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    if SNAPSHOT.exists():
        old = pd.read_csv(SNAPSHOT, low_memory=False)
        snap = pd.concat([old, snap], ignore_index=True)
    snap.to_csv(SNAPSHOT, index=False)

    print(json.dumps({
        "games": len(rows),
        "spread_complete": sum(r["spread_status"] == "Complete" for r in rows),
        "total_complete": sum(str(r["total_status"]).startswith("Complete") for r in rows),
        "current_market_total_baselines": sum(
            r.get("market_baseline_total_source") == "current_market_total"
            for r in rows
        ),
        "official_total_fallbacks": sum(
            r.get("market_baseline_total_source") == "official_fallback"
            for r in rows
        ),
        "missing_total_baselines": sum(
            r.get("market_baseline_total") is None
            for r in rows
        ),
        "output": str(OUT_JSON.relative_to(ROOT)),
    }, indent=2))
    print("wrote:", OUT_JSON)
    print("wrote:", OUT_CSV)
    print("wrote:", SNAPSHOT)

if __name__ == "__main__":
    main()
