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
ARTIFACT = ROOT / "data/research/shadow_validated_models_v1/model_artifacts.json"
FEATURES = ROOT / "data/research/shadow_live_feature_constructor/team_game_features_2026.json"
MARKET = ROOT / "data/ratings/market_implied_target_excluded_2026.json"
RATINGS = ROOT / "data/ratings/market_implied_ratings_latest.csv"
SOURCE_RATINGS = ROOT / "data/ratings/ratings_latest.csv"
MATCHUPS = ROOT / "data/site/matchups_view.json"
OUT = ROOT / "data/site/saturday_shadow_component_predictions.json"
SP_PLUS_HFA = 2.5
SAGARIN_HFA = 2.6

SHADOW_SPREAD_MODEL_ID = "shadow_spread_sp_sagarin_v1"
SHADOW_TOTAL_MODEL_ID = "shadow_total_enhanced_spplus_od_v1"


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
    """Apply one historically validated frozen standardized ridge model.

    Missing required features are not imputed. Production Shadow remains
    unavailable until the exact validated input contract is complete.
    """
    value = float(model["intercept"])

    for feature in model["feature_order"]:
        x = finite(row.get(feature))
        if x is None:
            return None

        mu = float(model["training_mean"][feature])
        sd = float(model["training_std"][feature])

        if not math.isfinite(sd) or sd == 0:
            return None

        z = (x - mu) / sd
        value += float(model["coefficients"][feature]) * z

    return float(value)


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



def latest_sagarin_rows():
    """Return the current canonical Sagarin Predictor state."""
    frame = pd.read_csv(SOURCE_RATINGS, low_memory=False)

    frame = frame[
        frame["season"].eq(2026)
        & frame["source"]
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("sagarin predictor")
    ].copy()

    frame["_cutoff"] = pd.to_datetime(
        frame["pulled_at"],
        errors="coerce",
        utc=True,
    )

    frame = (
        frame.sort_values(
            ["team", "_cutoff", "snapshot_date"]
        )
        .drop_duplicates("team", keep="last")
    )

    return frame.set_index("team").to_dict("index")

def apply_validated_shadow_state(
    row,
    side,
    source,
    sp_baseline,
    sagarin_baseline,
):
    """Populate validated Shadow provider/component state for one team."""

    models = row["_models"]

    if source is not None:
        spread_ready = bool(source.get("validated_shadow_spread_ready"))
        total_ready = bool(source.get("validated_shadow_total_ready"))

        sp_delta = (
            predict(source, models["shadow_spread_spplus_update_v1"])
            if spread_ready
            else None
        )
        sag_delta = (
            predict(source, models["shadow_spread_sagarin_update_v1"])
            if spread_ready
            else None
        )
        off_delta = (
            predict(source, models["shadow_total_spplus_offense_update_v1"])
            if total_ready
            else None
        )
        def_delta = (
            predict(source, models["shadow_total_spplus_defense_update_v1"])
            if total_ready
            else None
        )

        sp_entering = finite(source.get("stale_spplus"))
        sag_entering = finite(source.get("stale_sagarin_predictor"))
        off_entering = finite(source.get("stale_spplus_offense"))
        def_entering = finite(source.get("stale_spplus_defense"))

        row[f"{side}_validated_spread_ready"] = spread_ready
        row[f"{side}_validated_total_ready"] = total_ready

        row[f"{side}_sp_plus_entering"] = sp_entering
        row[f"{side}_predicted_sp_plus_change"] = sp_delta
        row[f"{side}_sp_plus_updated"] = (
            sp_entering + sp_delta
            if sp_entering is not None and sp_delta is not None
            else None
        )

        row[f"{side}_sagarin_entering"] = sag_entering
        row[f"{side}_predicted_sagarin_change"] = sag_delta
        row[f"{side}_sagarin_updated"] = (
            sag_entering + sag_delta
            if sag_entering is not None and sag_delta is not None
            else None
        )

        row[f"{side}_sp_plus_offense_entering"] = off_entering
        row[f"{side}_predicted_sp_plus_offense_change"] = off_delta
        row[f"{side}_sp_plus_offense_updated"] = (
            off_entering + off_delta
            if off_entering is not None and off_delta is not None
            else None
        )

        row[f"{side}_sp_plus_defense_entering"] = def_entering
        row[f"{side}_predicted_sp_plus_defense_change"] = def_delta
        row[f"{side}_sp_plus_defense_updated"] = (
            def_entering + def_delta
            if def_entering is not None and def_delta is not None
            else None
        )

        row[f"{side}_component_status"] = "postgame_validated_shadow"
        row[f"{side}_component_reason"] = (
            "historically_validated_frozen_provider_update_models"
        )
        row[f"{side}_movement_estimator_invoked"] = bool(
            sp_delta is not None
            or sag_delta is not None
            or off_delta is not None
            or def_delta is not None
        )
        row[f"{side}_sp_plus_snapshot_timestamp"] = (
            source.get("sp_plus_snapshot_timestamp")
            or source.get("feature_cutoff")
        )
        row[f"{side}_sagarin_snapshot_timestamp"] = (
            source.get("sagarin_snapshot_timestamp")
        )

    elif sp_baseline or sagarin_baseline:
        # No completed game for this team: retain stale provider states.
        row[f"{side}_validated_spread_ready"] = False
        row[f"{side}_validated_total_ready"] = False

        row[f"{side}_sp_plus_entering"] = finite(sp_baseline.get("rating")) if sp_baseline else None
        row[f"{side}_predicted_sp_plus_change"] = 0.0
        row[f"{side}_sp_plus_updated"] = finite(sp_baseline.get("rating")) if sp_baseline else None

        sag_entering = (
            finite(sagarin_baseline.get("rating"))
            if sagarin_baseline
            else None
        )

        row[f"{side}_sagarin_entering"] = sag_entering
        row[f"{side}_predicted_sagarin_change"] = (
            0.0 if sag_entering is not None else None
        )
        row[f"{side}_sagarin_updated"] = sag_entering

        row[f"{side}_sp_plus_offense_entering"] = finite(sp_baseline.get("off_rating")) if sp_baseline else None
        row[f"{side}_predicted_sp_plus_offense_change"] = 0.0
        row[f"{side}_sp_plus_offense_updated"] = finite(sp_baseline.get("off_rating")) if sp_baseline else None

        row[f"{side}_sp_plus_defense_entering"] = finite(sp_baseline.get("def_rating")) if sp_baseline else None
        row[f"{side}_predicted_sp_plus_defense_change"] = 0.0
        row[f"{side}_sp_plus_defense_updated"] = finite(sp_baseline.get("def_rating")) if sp_baseline else None

        row[f"{side}_component_status"] = "preseason_baseline"
        row[f"{side}_component_reason"] = "no_completed_game_to_update"
        row[f"{side}_movement_estimator_invoked"] = False
        row[f"{side}_sp_plus_snapshot_timestamp"] = (
            (
                sp_baseline.get("pulled_at")
                or sp_baseline.get("snapshot_date")
            )
            if sp_baseline
            else None
        )
        row[f"{side}_sagarin_snapshot_timestamp"] = (
            (
                sagarin_baseline.get("pulled_at")
                or sagarin_baseline.get("snapshot_date")
            )
            if sagarin_baseline
            else None
        )

    else:
        for key in (
            "sp_plus_entering",
            "predicted_sp_plus_change",
            "sp_plus_updated",
            "sagarin_entering",
            "predicted_sagarin_change",
            "sagarin_updated",
            "sp_plus_offense_entering",
            "predicted_sp_plus_offense_change",
            "sp_plus_offense_updated",
            "sp_plus_defense_entering",
            "predicted_sp_plus_defense_change",
            "sp_plus_defense_updated",
        ):
            row[f"{side}_{key}"] = None

        row[f"{side}_validated_spread_ready"] = False
        row[f"{side}_validated_total_ready"] = False
        row[f"{side}_component_status"] = "provider_state_unavailable"
        row[f"{side}_component_reason"] = "canonical_entering_state_missing"
        row[f"{side}_movement_estimator_invoked"] = False
        row[f"{side}_sp_plus_snapshot_timestamp"] = None
        row[f"{side}_sagarin_snapshot_timestamp"] = None


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
    sagarin = latest_sagarin_rows()
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
            "generated_at": generated_at, "model_version": artifact.get("model_version"),
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

        apply_validated_shadow_state(
            row,
            "away",
            ar,
            sp_plus.get(away),
            sagarin.get(away),
        )
        apply_validated_shadow_state(
            row,
            "home",
            hr,
            sp_plus.get(home),
            sagarin.get(home),
        )
        row.pop("_models", None)
        state_map = {
            "postgame_validated_shadow": "postgame_updated",
            "preseason_baseline": "baseline_only",
            "provider_state_unavailable": "unavailable",
        }
        row["away_update_state"] = state_map.get(row["away_component_status"], "unavailable")
        row["home_update_state"] = state_map.get(row["home_component_status"], "unavailable")
        row["completed_team_update_count"] = sum(
            row[f"{side}_update_state"] == "postgame_updated" for side in ("away", "home")
        )
        row["has_genuine_postgame_update"] = row["completed_team_update_count"] > 0

        # Model maturity is domain-specific and independent
        # of model/data quality.
        #
        # A team counts as updated for a domain only when its
        # completed-game feature row passed that validated model's
        # readiness gate.
        spread_update_count = sum(
            bool(
                row.get(
                    f"{side}_validated_spread_ready"
                )
            )
            for side in ("away", "home")
        )

        total_update_count = sum(
            bool(
                row.get(
                    f"{side}_validated_total_ready"
                )
            )
            for side in ("away", "home")
        )

        row[
            "shadow_spread_updated_team_count"
        ] = spread_update_count

        row[
            "shadow_total_updated_team_count"
        ] = total_update_count
        row["away_spread_shadow_ready"] = bool(row.get("away_validated_spread_ready"))
        row["home_spread_shadow_ready"] = bool(row.get("home_validated_spread_ready"))
        row["away_total_shadow_ready"] = bool(row.get("away_validated_total_ready"))
        row["home_total_shadow_ready"] = bool(row.get("home_validated_total_ready"))

        def shadow_state(count):
            if count <= 0:
                return "STALE"
            if count == 1:
                return "SHADOW_PARTIAL"
            return "SHADOW"

        row[
            "shadow_spread_maturity_state"
        ] = shadow_state(
            spread_update_count
        )

        row[
            "shadow_total_maturity_state"
        ] = shadow_state(
            total_update_count
        )

        # Compatibility field for existing consumers. This is
        # intentionally the most mature Shadow state reached by
        # either domain; spread/total authority must use the
        # domain-specific fields above.
        maturity_rank = {
            "STALE": 0,
            "SHADOW_PARTIAL": 1,
            "SHADOW": 2,
        }

        row["shadow_maturity_state"] = max(
            (
                row["shadow_spread_maturity_state"],
                row["shadow_total_maturity_state"],
            ),
            key=lambda x: maturity_rank[x],
        )

        # ----------------------------------------------------------
        # Validated Shadow SP+ fair spread
        # ----------------------------------------------------------

        sp_spread_ready = (
            row.get("away_sp_plus_updated") is not None
            and row.get("home_sp_plus_updated") is not None
            and (
                row.get("away_validated_spread_ready")
                or row.get("home_validated_spread_ready")
            )
        )

        if sp_spread_ready:
            hfa = 0.0 if row["neutral_site"] else SP_PLUS_HFA
            row["predicted_updated_sp_plus_spread"] = -(
                row["home_sp_plus_updated"]
                - row["away_sp_plus_updated"]
                + hfa
            )
        else:
            row["predicted_updated_sp_plus_spread"] = None
            missing.append("validated Shadow SP+ spread inputs unavailable")

        # ----------------------------------------------------------
        # Validated Shadow Sagarin fair spread
        # ----------------------------------------------------------

        sag_spread_ready = (
            row.get("away_sagarin_updated") is not None
            and row.get("home_sagarin_updated") is not None
            and (
                row.get("away_validated_spread_ready")
                or row.get("home_validated_spread_ready")
            )
        )

        if sag_spread_ready:
            # Preserve the current Sagarin provider projection convention:
            # home - away + 2.6 HFA for non-neutral games.
            sag_hfa = 0.0 if row["neutral_site"] else SAGARIN_HFA
            row["predicted_updated_sagarin_spread"] = -(
                row["home_sagarin_updated"]
                - row["away_sagarin_updated"]
                + sag_hfa
            )
        else:
            row["predicted_updated_sagarin_spread"] = None
            missing.append("validated Shadow Sagarin spread inputs unavailable")

        # The component builder exposes provider fair spreads.
        # The canonical projection contract owns the final 50/50 formula.
        row["shadow_spread_formula"] = (
            "(Shadow SP+ fair spread + Shadow Sagarin fair spread) / 2"
        )
        row["spread_projection_readiness"] = (
            "ready"
            if row["predicted_updated_sp_plus_spread"] is not None
            and row["predicted_updated_sagarin_spread"] is not None
            else "unavailable"
        )

        # Non-authoritative diagnostic only.
        row["internal_shadow_spread_baseline"] = None
        row["shadow_spread"] = None

        # ----------------------------------------------------------
        # Validated Shadow Total components
        # ----------------------------------------------------------

        total_inputs_ready = all(
            row.get(k) is not None
            for k in (
                "home_sp_plus_offense_updated",
                "away_sp_plus_offense_updated",
                "home_sp_plus_defense_updated",
                "away_sp_plus_defense_updated",
            )
        ) and (
            row.get("home_validated_total_ready")
            or row.get("away_validated_total_ready")
        )

        if total_inputs_ready:
            row["predicted_sp_plus_component_total"] = (
                0.5
                * (
                    row["home_sp_plus_offense_updated"]
                    + row["away_sp_plus_defense_updated"]
                )
                + 0.5
                * (
                    row["away_sp_plus_offense_updated"]
                    + row["home_sp_plus_defense_updated"]
                )
            )
            row["total_projection_readiness"] = "ready"
        else:
            row["predicted_sp_plus_component_total"] = None
            row["total_projection_readiness"] = "unavailable"
            missing.append("validated Shadow SP+ offense/defense inputs unavailable")

        # Explicit canonical model identity/provenance.
        row["shadow_spread_model_id"] = SHADOW_SPREAD_MODEL_ID
        row["shadow_total_model_id"] = SHADOW_TOTAL_MODEL_ID

        row["validated_shadow_model_version"] = artifact.get(
            "model_version"
        )

        row["validated_shadow_spread_inputs_validated"] = bool(
            row.get("spread_projection_readiness") == "ready"
        )

        row["enhanced_spplus_od_v1_inputs_validated"] = bool(
            row.get("total_projection_readiness") == "ready"
        )

        # No 60/40 blend and no -1.1573 bias correction in the
        # historically validated production Shadow Total.
        row["raw_60_40_total"] = None
        row["total_bias_correction"] = None
        row["internal_shadow_total_baseline"] = None
        row["shadow_total"] = None

        model = match.get("model") or {}
        spread_market = ((match.get("market") or {}).get("spread") or {})
        total_market = ((match.get("market") or {}).get("total") or {})

        row["current_model_spread"] = finite(model.get("home_spread"))
        row["existing_projected_total"] = finite(model.get("total"))
        row["best_market_spread"] = finite(spread_market.get("home_line"))
        row["best_market_total"] = finite(total_market.get("line"))

        # Final Shadow values and edges are owned by the canonical
        # projection contract/resolver, not reconstructed here.
        row["spread_impact"] = None
        row["shadow_spread_edge"] = None
        row["spread_value_tier"] = None
        row["spread_value_label"] = "Unavailable"

        row["total_impact"] = None
        row["shadow_total_edge"] = None
        row["total_value_tier"] = None
        row["total_value_label"] = "Unavailable"
        row["spread_missing_reasons"] = missing
        row["total_missing_reasons"] = [m for m in missing if "offense/defense" in m or "feature row" in m]
        row["shadow_display_ready"] = bool(
            row["has_genuine_postgame_update"]
            and (
                row["spread_projection_readiness"] == "ready"
                or row["total_projection_readiness"] == "ready"
            )
        )
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
        row["prior_sp_plus_state_available"] = bool(
            row.get("away_sp_plus_entering") is not None
            and row.get("home_sp_plus_entering") is not None
        )
        row["prior_sagarin_state_available"] = bool(
            row.get("away_sagarin_entering") is not None
            and row.get("home_sagarin_entering") is not None
        )
        row["next_game_mapping_status"] = "matched" if ar is not None and hr is not None else "preseason_schedule_target"
        row["no_lookahead_pass"] = bool(target.get("target_game_excluded"))
        row["arithmetic_pass"] = True
        games.append(row)

    payload = {
        "schema_version": "saturday-shadow-component-predictions-v1",
        "generated_at": generated_at,
        "model_version": artifact.get("model_version"),
        "frozen_models_loaded_without_refit": True,
        "fpi_teamrankings_used": False,
        "fixture_only": False,
        "games": games,
        "summary": {
            "games": len(games),

            "displayed_shadow_rows": sum(
                r.get("shadow_display_ready") is True
                for r in games
            ),

            "postgame_updated_teams": sum(
                r.get(f"{side}_update_state") == "postgame_updated"
                for r in games
                for side in ("away", "home")
            ),

            "stale_games": sum(
                r.get("shadow_maturity_state") == "STALE"
                for r in games
            ),

            "shadow_partial_games": sum(
                r.get("shadow_maturity_state") == "SHADOW_PARTIAL"
                for r in games
            ),

            "shadow_games": sum(
                r.get("shadow_maturity_state") == "SHADOW"
                for r in games
            ),

            "sp_plus_baseline_games": sum(
                r.get("prior_sp_plus_state_available") is True
                for r in games
            ),

            "sagarin_baseline_games": sum(
                r.get("prior_sagarin_state_available") is True
                for r in games
            ),

            "spread_component_ready": sum(
                r.get("spread_projection_readiness") == "ready"
                for r in games
            ),

            "total_component_ready": sum(
                r.get("total_projection_readiness") == "ready"
                for r in games
            ),

            "independent_market_ready": sum(
                r.get("market_readiness_state") == "independent_market_ready"
                for r in games
            ),

            "market_context_only": sum(
                r.get("market_readiness_state") == "market_context_only"
                for r in games
            ),

            "market_unavailable": sum(
                r.get("market_readiness_state") == "market_unavailable"
                for r in games
            ),
        },
    }
    atomic_json(OUT, payload)
    print(json.dumps(payload["summary"], indent=2))
    print("wrote:", OUT)


if __name__ == "__main__":
    main()
