#!/usr/bin/env python3
"""Build prospective Shadow components from frozen artifacts only.

This is an inference adapter, not a training script. It consumes the canonical
team-game feature constructor and target-excluded market state, rejects fixture
rows, and preserves the prior valid output if any input or arithmetic fails.
"""
from __future__ import annotations

import json
import math
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "data/research/shadow_component_bridge_v1/model_artifacts.json"
FEATURES = ROOT / "data/research/shadow_live_feature_constructor/team_game_features_2026.json"
MARKET = ROOT / "data/ratings/market_implied_target_excluded_2026.json"
RATINGS = ROOT / "data/ratings/market_implied_ratings_latest.csv"
SOURCE_RATINGS = ROOT / "data/ratings/ratings_latest.csv"
MATCHUPS = ROOT / "data/site/matchups_view.json"
OUT = ROOT / "data/site/saturday_shadow_component_predictions.json"
HFA = 2.5


def norm_id(value):
    value = str(value or "").strip()
    return value[:-2] if value.endswith(".0") else value


def finite(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except Exception:
        return None


def atomic_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as f:
        json.dump(payload, f, indent=2, allow_nan=False)
        f.write("\n")
        tmp = Path(f.name)
    tmp.replace(path)


def predict(row, model):
    values = np.array([finite(row.get(k)) for k in model["feature_order"]], dtype=object)
    x = np.array([float(v) if v is not None else np.nan for v in values], dtype=float)
    med = np.asarray(model["imputation"]["values"], dtype=float)
    mu = np.asarray(model["scaling"]["mean"], dtype=float)
    sd = np.asarray(model["scaling"]["std"], dtype=float)
    z = (np.where(np.isfinite(x), x, med) - mu) / sd
    return float(model["intercept"] + z @ np.asarray(model["coefficients"], dtype=float))


def latest_sp_plus_rows():
    """Return the current canonical SP+ state used for a no-event baseline."""
    frame = pd.read_csv(SOURCE_RATINGS, low_memory=False)
    frame = frame[
        frame["season"].eq(2026)
        & frame["source"].astype(str).str.strip().str.casefold().eq("sp+")
    ].copy()
    frame["_cutoff"] = pd.to_datetime(frame["pulled_at"], errors="coerce", utc=True)
    frame = frame.sort_values(["team", "_cutoff", "snapshot_date"]).drop_duplicates("team", keep="last")
    return frame.set_index("team").to_dict("index")


def apply_sp_plus_state(row, side, source, baseline):
    """Populate one team's SP+ state independently of its opponent."""
    if source is not None:
        changes = {
            "market": predict(source, row["_models"]["market_rating_movement"]),
            "overall": predict(source, row["_models"]["sp_plus_overall_movement"]),
            "offense": predict(source, row["_models"]["sp_plus_offense_movement"]),
            # Artifact target is defensive improvement; site convention stores
            # defensive points allowed, so improvement reduces that value.
            "defense": -predict(source, row["_models"]["sp_plus_defense_improvement"]),
        }
        entering = {
            "overall": finite(source.get("current_sp_plus_overall") or source.get("sp_plus_entering")),
            "offense": finite(source.get("current_sp_plus_offense") or source.get("sp_plus_offense_entering")),
            "defense": finite(source.get("current_sp_plus_defense") or source.get("sp_plus_defense_entering")),
        }
        status = "postgame_model_update"
        reason = "completed_game_frozen_movement_model"
        estimator_invoked = True
        snapshot = source.get("sp_plus_snapshot_timestamp") or source.get("feature_cutoff")
    elif baseline:
        changes = {"market": 0.0, "overall": 0.0, "offense": 0.0, "defense": 0.0}
        entering = {
            "overall": finite(baseline.get("rating")),
            "offense": finite(baseline.get("off_rating")),
            "defense": finite(baseline.get("def_rating")),
        }
        status = "preseason_baseline"
        reason = "no_completed_game_to_update"
        estimator_invoked = False
        snapshot = baseline.get("pulled_at") or baseline.get("snapshot_date")
    else:
        changes = {"market": None, "overall": None, "offense": None, "defense": None}
        entering = {"overall": None, "offense": None, "defense": None}
        status = "sp_plus_unavailable"
        reason = "canonical_2026_sp_plus_snapshot_missing"
        estimator_invoked = False
        snapshot = None

    row[f"{side}_component_status"] = status
    row[f"{side}_component_reason"] = reason
    row[f"{side}_movement_estimator_invoked"] = estimator_invoked
    row[f"{side}_sp_plus_snapshot_timestamp"] = snapshot
    row[f"{side}_predicted_market_rating_change"] = changes["market"]
    row[f"{side}_sp_plus_entering"] = entering["overall"]
    row[f"{side}_predicted_sp_plus_change"] = changes["overall"]
    row[f"{side}_sp_plus_updated"] = (
        entering["overall"] + changes["overall"] if entering["overall"] is not None and changes["overall"] is not None else None
    )
    for component in ("offense", "defense"):
        row[f"{side}_sp_plus_{component}_entering"] = entering[component]
        row[f"{side}_predicted_sp_plus_{component}_change"] = changes[component]
        row[f"{side}_sp_plus_{component}_updated"] = (
            entering[component] + changes[component]
            if entering[component] is not None and changes[component] is not None else None
        )


def main():
    for path in (ARTIFACT, FEATURES, MARKET, RATINGS, SOURCE_RATINGS, MATCHUPS):
        if not path.exists():
            raise SystemExit(f"Missing required input: {path}")

    artifact = json.loads(ARTIFACT.read_text())
    feature_payload = json.loads(FEATURES.read_text())
    market_payload = json.loads(MARKET.read_text())
    matchup_payload = json.loads(MATCHUPS.read_text())
    if feature_payload.get("fixture_only"):
        raise SystemExit("Fixture feature rows are not accepted by production inference.")
    if market_payload.get("fixture_only"):
        raise SystemExit("Fixture market rows are not accepted by production inference.")

    all_board = pd.read_csv(RATINGS, low_memory=False).set_index("team").to_dict("index")
    sp_plus = latest_sp_plus_rows()
    market_by_game = {norm_id(r.get("game_id")): r for r in market_payload.get("games", [])}
    matchups = {norm_id((r.get("game") or {}).get("game_id")): r for r in matchup_payload.get("games", [])}
    team_rows = {}
    for row in feature_payload.get("rows", []):
        if row.get("fixture_only"):
            raise SystemExit("Fixture row found in canonical feature payload.")
        gid = norm_id(row.get("next_game_id"))
        team = row.get("team")
        if gid and team:
            prior = team_rows.get((gid, team))
            if not prior or int(row.get("completed_week") or -1) > int(prior.get("completed_week") or -1):
                team_rows[(gid, team)] = row

    models = artifact["models"]
    total_model = artifact["sp_plus_component_total"]
    generated_at = datetime.now(timezone.utc).isoformat()
    games = []
    for gid, target in market_by_game.items():
        match = matchups.get(gid) or {}
        game = match.get("game") or {}
        away, home = target.get("away_team"), target.get("home_team")
        ar, hr = team_rows.get((gid, away)), team_rows.get((gid, home))
        missing = []

        row = {
            "game_id": gid, "season": 2026, "week": target.get("week"),
            "game_date": game.get("date"), "kickoff": game.get("kickoff") or game.get("start_date"),
            "away_team": away, "home_team": home, "neutral_site": bool(target.get("neutral_site")),
            "generated_at": generated_at, "model_version": artifact.get("artifact_version"),
            "feature_cutoff": max([x.get("feature_cutoff") for x in (ar, hr) if x and x.get("feature_cutoff")], default=None),
            "completed_game_ids_used": [x.get("completed_game_id") for x in (ar, hr) if x and x.get("completed_game_id")],
            "feature_sources": [str(FEATURES.relative_to(ROOT)), str(MARKET.relative_to(ROOT))],
            "market_readiness_state": target.get("market_readiness_state"),
            "market_readiness_reason": target.get("market_readiness_reason"),
            "leave_one_out_component_size": target.get("leave_one_out_component_size"),
            "target_game_excluded": bool(target.get("target_game_excluded")),
            "predicted_market_rating_spread": target.get("predicted_market_rating_spread"),
            "away_market_rating_entering": target.get("away_market_rating_entering"),
            "home_market_rating_entering": target.get("home_market_rating_entering"),
            "fixture_only": False,
            "_models": models,
        }
        for prefix, team in (("away", away), ("home", home)):
            board = all_board.get(team, {})
            row[f"{prefix}_all_board_market_rating"] = finite(board.get("market_implied_rating"))
            row[f"{prefix}_all_board_market_rank"] = finite(board.get("market_implied_rank"))
            row[f"{prefix}_market_games_in_rating"] = finite(board.get("games_used"))
            row[f"{prefix}_market_sample_status"] = board.get("sample_status")

        apply_sp_plus_state(row, "away", ar, sp_plus.get(away))
        apply_sp_plus_state(row, "home", hr, sp_plus.get(home))
        row.pop("_models", None)
        state_map = {
            "postgame_model_update": "postgame_updated",
            "preseason_baseline": "baseline_only",
            "sp_plus_unavailable": "unavailable",
        }
        row["away_update_state"] = state_map.get(row["away_component_status"], "unavailable")
        row["home_update_state"] = state_map.get(row["home_component_status"], "unavailable")
        row["completed_team_update_count"] = sum(
            row[f"{side}_update_state"] == "postgame_updated" for side in ("away", "home")
        )
        row["has_genuine_postgame_update"] = row["completed_team_update_count"] > 0
        if row["away_sp_plus_updated"] is None or row["home_sp_plus_updated"] is None:
            missing.append("prospective entering SP+ overall snapshot unavailable")
        else:
            hfa = 0.0 if row["neutral_site"] else HFA
            row["predicted_updated_sp_plus_spread"] = -(
                row["home_sp_plus_updated"] - row["away_sp_plus_updated"] + hfa
            )

        total_fields = {
            "predicted_updated_home_offense": row.get("home_sp_plus_offense_updated"),
            "predicted_updated_away_offense": row.get("away_sp_plus_offense_updated"),
            "predicted_updated_home_defense": row.get("home_sp_plus_defense_updated"),
            "predicted_updated_away_defense": row.get("away_sp_plus_defense_updated"),
        }
        if all(v is not None for v in total_fields.values()):
            row["predicted_sp_plus_component_total"] = predict(total_fields, total_model)
        else:
            missing.append("prospective entering SP+ offense/defense snapshot unavailable")

        sp = finite(row.get("predicted_updated_sp_plus_spread"))
        market_sp = finite(row.get("predicted_market_rating_spread"))
        internal_spread = None
        if sp is None:
            row["shadow_spread_formula"] = "Unavailable"
            row["spread_projection_readiness"] = "sp_plus_unavailable"
        elif target.get("market_readiness_state") == "independent_market_ready" and market_sp is not None:
            internal_spread = 0.5 * market_sp + 0.5 * sp
            row["shadow_spread_formula"] = "50/50 Market + SP+"
            row["spread_projection_readiness"] = "independent_market_ready"
        else:
            internal_spread = sp
            row["shadow_spread_formula"] = "SP+ Fallback"
            row["spread_projection_readiness"] = target.get("market_readiness_state") or "market_unavailable"
        row["internal_shadow_spread_baseline"] = internal_spread

        model = match.get("model") or {}
        spread_market = ((match.get("market") or {}).get("spread") or {})
        total_market = ((match.get("market") or {}).get("total") or {})
        row["current_model_spread"] = finite(model.get("home_spread"))
        row["existing_projected_total"] = finite(model.get("total"))
        row["best_market_spread"] = finite(spread_market.get("home_line"))
        row["best_market_total"] = finite(total_market.get("line"))
        spread_inputs_ready = internal_spread is not None
        row["shadow_spread"] = internal_spread if row["has_genuine_postgame_update"] and spread_inputs_ready else None
        row["spread_impact"] = row["shadow_spread"] - row["current_model_spread"] if row["shadow_spread"] is not None and row["current_model_spread"] is not None else None
        row["shadow_spread_edge"] = row["best_market_spread"] - row["shadow_spread"] if row["shadow_spread"] is not None and row["best_market_spread"] is not None else None
        row["spread_value_tier"] = "neutral" if row["shadow_spread"] is not None else None
        row["spread_value_label"] = "neutral projected market value" if row["shadow_spread"] is not None else "Unavailable"

        component_total = finite(row.get("predicted_sp_plus_component_total"))
        existing_total = row["existing_projected_total"]
        if component_total is not None and existing_total is not None:
            row["raw_60_40_total"] = 0.6 * component_total + 0.4 * existing_total
            row["total_bias_correction"] = -1.1573
            row["internal_shadow_total_baseline"] = row["raw_60_40_total"] - 1.1573
            row["total_projection_readiness"] = "ready"
        else:
            row["internal_shadow_total_baseline"] = None
            row["total_projection_readiness"] = "unavailable"
        total_has_update = row["has_genuine_postgame_update"] and any(
            row.get(f"{side}_movement_estimator_invoked") is True for side in ("away", "home")
        )
        row["shadow_total"] = row["internal_shadow_total_baseline"] if total_has_update and row["internal_shadow_total_baseline"] is not None else None
        row["total_impact"] = row["shadow_total"] - existing_total if row["shadow_total"] is not None and existing_total is not None else None
        row["shadow_total_edge"] = row["shadow_total"] - row["best_market_total"] if row["shadow_total"] is not None and row["best_market_total"] is not None else None
        row["total_value_tier"] = None
        row["total_value_label"] = "Unavailable"
        row["spread_missing_reasons"] = missing
        row["total_missing_reasons"] = [m for m in missing if "offense/defense" in m or "feature row" in m]
        row["shadow_display_ready"] = bool(row["has_genuine_postgame_update"] and (row["shadow_spread"] is not None or row["shadow_total"] is not None))
        if not row["has_genuine_postgame_update"]:
            row["shadow_activation_reason"] = "awaiting_completed_game"
            row["shadow_status"] = "Awaiting completed game"
            row["shadow_missing_reasons"] = []
        elif row["shadow_display_ready"]:
            row["shadow_activation_reason"] = "genuine_postgame_update"
            row["shadow_status"] = "Active"
            row["shadow_missing_reasons"] = missing
        else:
            row["shadow_activation_reason"] = "required_inputs_unavailable"
            row["shadow_status"] = "Unavailable"
            row["shadow_missing_reasons"] = missing or ["Postgame data incomplete"]
        row["pbp_available"] = bool(ar and hr and ar.get("pbp_available") and hr.get("pbp_available"))
        row["market_close_available"] = bool(ar and hr and ar.get("close_available") and hr.get("close_available"))
        row["prior_market_state_available"] = bool(target.get("away_market_rating_entering") is not None and target.get("home_market_rating_entering") is not None)
        row["prior_sp_plus_state_available"] = sp is not None
        row["next_game_mapping_status"] = "matched" if ar is not None and hr is not None else "preseason_schedule_target"
        row["no_lookahead_pass"] = bool(target.get("target_game_excluded"))
        row["arithmetic_pass"] = True
        games.append(row)

    payload = {
        "schema_version": "saturday-shadow-component-predictions-v1",
        "generated_at": generated_at,
        "model_version": artifact.get("artifact_version"),
        "frozen_models_loaded_without_refit": True,
        "fpi_teamrankings_used": False,
        "fixture_only": False,
        "games": games,
        "summary": {
            "games": len(games),
            "internal_baseline_rows": sum(r.get("internal_shadow_spread_baseline") is not None or r.get("internal_shadow_total_baseline") is not None for r in games),
            "displayed_shadow_rows": sum(r.get("shadow_display_ready") is True for r in games),
            "postgame_updated_teams": sum(r.get(f"{side}_update_state") == "postgame_updated" for r in games for side in ("away", "home")),
            "independent_market_ready": sum(r.get("market_readiness_state") == "independent_market_ready" for r in games),
            "market_context_only": sum(r.get("market_readiness_state") == "market_context_only" for r in games),
            "market_unavailable": sum(r.get("market_readiness_state") == "market_unavailable" for r in games),
            "sp_plus_unavailable": sum(r.get("internal_shadow_spread_baseline") is None for r in games),
        },
    }
    atomic_json(OUT, payload)
    print(json.dumps(payload["summary"], indent=2))
    print("wrote:", OUT)


if __name__ == "__main__":
    main()
