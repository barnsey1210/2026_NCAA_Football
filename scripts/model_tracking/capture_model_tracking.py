#!/usr/bin/env python3
"""Create a prospective capture batch; append only with explicit --accept."""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from model_tracking import (CORE_SPREAD_MODELS, append_jsonl, available_average,
                            is_trackable_game, read_jsonl, spread_core, stable_id,
                            total_consensus)

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "data/model_tracking"
SOURCE_COLUMNS = {
    "SP+": "spplus",
    "FPI": "fpi",
    "TeamRankings": "teamrankings",
    "Brad Powers": "bradpowers",
    "KFord": "kford",
}
NON_NEUTRAL_HFA = 2.6


def norm(x):
    return re.sub(r"[^a-z0-9]+", "", str(x or "").lower())


def prob_ev(edge, price, scale):
    p = .5 * (1 + math.erf(abs(edge) / scale / math.sqrt(2)))
    profit = price / 100 if price > 0 else 100 / abs(price)
    return (p * profit - (1 - p)) * 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accept", action="store_true", help="Append records to accepted JSONL ledgers")
    ap.add_argument("--batch-output", default="data/model_tracking/last_capture_preview.json")
    args = ap.parse_args()

    cfg = json.loads((STORE / "config.json").read_text())
    matchups = json.loads((ROOT / "data/site/matchups_view.json").read_text())["games"]
    ratings_df = pd.read_csv(ROOT / "data/ratings/ratings_master_latest.csv").replace({float("nan"): None})
    ratings = {norm(r["team"]): r for r in ratings_df.to_dict("records")}
    built_at = datetime.now(timezone.utc).isoformat()
    today_et = datetime.now(ZoneInfo("America/New_York")).date()

    # Only one official prospective snapshot is allowed for each game/market.
    accepted_pairs = {
        (row.get("canonical_game_id"), row.get("market_type"))
        for row in read_jsonl(STORE / "model_opportunities.jsonl")
    }

    opportunities, predictions, observations = [], [], []

    for row in matchups:
        game, market, production = row["game"], row.get("market", {}), row.get("model", {})
        game_status = str(game.get("status") or "").strip().lower()

        if (
            not is_trackable_game(game_status)
            or bool(game.get("completed"))
            or game_status in {"completed", "final", "closed"}
        ):
            continue

        # Canonical matchup data currently contains a date but not an exact
        # kickoff timestamp. Capture normally on the prior calendar day.
        # Use same-day only as a fallback when the prior daily run was missed.
        raw_game_date = str(game.get("date") or "").strip()
        try:
            game_date = date.fromisoformat(raw_game_date[:10])
        except (TypeError, ValueError):
            continue

        days_until_game = (game_date - today_et).days

        if days_until_game == 1:
            snapshot_timing = "day_before"
        elif days_until_game == 0:
            snapshot_timing = "same_day_fallback"
        else:
            continue

        home = ratings.get(norm(game["home_team"]))
        away = ratings.get(norm(game["away_team"]))
        individual = {}
        source_times = {}

        # Individual team-rating projections use the same validated production
        # home-field rule as the site: 2.6 for non-neutral games and 0.0 for
        # neutral-site games. Never infer HFA from a stored production margin.
        if home and away:
            neutral = bool(game.get("neutral_site"))
            hfa = 0.0 if neutral else 2.6
            for display, col in SOURCE_COLUMNS.items():
                if home.get(col) is not None and away.get(col) is not None and display != "KFord":
                    individual[display] = float(home[col]) - float(away[col]) + hfa
                    source_times[display] = str(home.get("rating_date") or "")

        core = spread_core(individual)
        avg = available_average(individual, cfg["approved_spread_models"])

        specs = [
            ("spread", market.get("spread", {}), individual),
            ("total", market.get("total", {}), {"Production Total": production.get("total")}),
        ]

        for market_type, quote, values in specs:
            # Never replace or duplicate a game's official pregame snapshot.
            if (game["game_id"], market_type) in accepted_pairs:
                continue

            line = quote.get("home_line") if market_type == "spread" else quote.get("line")
            if line is None or not values:
                continue

            observed_at = quote.get("updated_at") or built_at
            book = quote.get("book") or "UNKNOWN"
            obs_id = stable_id(game["game_id"], market_type, book, observed_at, line)
            prices = (
                {"selected": quote.get("price")}
                if market_type == "spread"
                else {"over": quote.get("over_price"), "under": quote.get("under_price")}
            )

            observations.append({
                "market_observation_id": obs_id,
                "canonical_game_id": game["game_id"],
                "market_type": market_type,
                "sportsbook": book,
                "source": "matchups_view",
                "observed_at": observed_at,
                "line": line,
                "side_prices": prices,
                "available": True,
                "suspended": False,
                "is_executable": True,
                "provenance_grade": "EARLIEST_CAPTURED",
                "revision": 1,
            })

            opp_id = stable_id(game["game_id"], market_type, obs_id, "estimated_ev_v1")
            expected = cfg["approved_spread_models"] if market_type == "spread" else cfg["approved_total_models"]
            included = [x for x in expected if values.get(x) is not None]
            total_rule = (
                total_consensus(values, expected, cfg["total_consensus_minimum"])
                if market_type == "total"
                else None
            )

            opp = {
                "opportunity_id": opp_id,
                "canonical_game_id": game["game_id"],
                "season": 2026,
                "site_week": game.get("week"),
                "kickoff_utc": game.get("date"),
                "kickoff_precision": "date_only",
                "scheduled_game_date": game_date.isoformat(),
                "capture_date_et": today_et.isoformat(),
                "days_until_game": days_until_game,
                "snapshot_timing": snapshot_timing,
                "away_team": game["away_team"],
                "home_team": game["home_team"],
                "neutral_site": bool(game.get("neutral_site")),
                "hfa_used": 0.0 if bool(game.get("neutral_site")) else 2.6,
                "hfa_method": "validated_fixed_hfa",
                "fcs_opponent_flag": not (home and away),
                "market_type": market_type,
                "opener_market_observation_id": obs_id,
                "opener_provenance_grade": "EARLIEST_CAPTURED",
                "models_expected": expected,
                "models_available": included,
                "models_missing": [x for x in expected if x not in included],
                "model_count": len(included),
                "model_source_timestamps": source_times,
                "consensus_versions": (
                    ["spread_core_v1" if core["eligible"] else None, "spread_available_average_v1"]
                    if market_type == "spread"
                    else (["totals_consensus_v1"] if total_rule["eligible"] else [])
                ),
                "qualification_status": "TRACKED_NOT_QUALIFIED",
                "estimated_ev_pct": None,
                "qualification_rule_version": "estimated_ev_v1",
                "created_at": built_at,
                "revision": 1,
                "supersedes_id": None,
                "correction_reason": None,
            }
            opp["consensus_versions"] = [x for x in opp["consensus_versions"] if x]
            opportunities.append(opp)

            model_rows = list(values.items())
            if market_type == "spread":
                if core["eligible"]:
                    model_rows.append(("spread_core_v1", core["value"]))
                if avg["eligible"]:
                    model_rows.append(("spread_available_average_v1", avg["value"]))
            elif total_rule["eligible"]:
                model_rows.append(("totals_consensus_v1", total_rule["value"]))

            evs = []
            for model, value in model_rows:
                if value is None:
                    continue
                edge = float(value) + float(line) if market_type == "spread" else float(value) - float(line)
                price = quote.get("price") or (
                    quote.get("over_price") if edge >= 0 else quote.get("under_price")
                ) or -110
                ev = prob_ev(edge, float(price), 17 if market_type == "spread" else 14)
                evs.append(ev)
                predictions.append({
                    "prediction_id": stable_id(opp_id, model, observed_at),
                    "opportunity_id": opp_id,
                    "canonical_game_id": game["game_id"],
                    "model_id": model,
                    "model_type": "consensus" if model.endswith("_v1") else "individual",
                    "model_set_version": model if model.endswith("_v1") else "individual_v1",
                    "snapshot_at": built_at,
                    "source_updated_at": source_times.get(model, built_at),
                    "available_at_opener": True,
                    "predicted_home_margin": value if market_type == "spread" else None,
                    "predicted_total": value if market_type == "total" else None,
                    "models_included": (
                        core["models"] if model == "spread_core_v1"
                        else avg["models"] if model == "spread_available_average_v1"
                        else total_rule["models"] if model == "totals_consensus_v1"
                        else [model]
                    ),
                    "opening_edge": edge,
                    "estimated_ev_pct": ev,
                    "qualification_status": (
                        "QUALIFIED" if ev >= cfg["qualification"]["minimum_ev_pct"] else "NOT_QUALIFIED"
                    ),
                    "hfa_used": 0.0 if bool(game.get("neutral_site")) else 2.6,
                    "hfa_method": "validated_fixed_hfa",
                    "revision": 1,
                })

            if evs:
                opp["estimated_ev_pct"] = max(evs)
                opp["qualification_status"] = (
                    "QUALIFIED"
                    if max(evs) >= cfg["qualification"]["minimum_ev_pct"]
                    else "NOT_QUALIFIED"
                )

    batch = {
        "schema_version": "model-capture-preview-v1",
        "built_at": built_at,
        "accepted": args.accept,
        "methodology": {
            "spread_hfa": {"non_neutral": NON_NEUTRAL_HFA, "neutral": 0.0},
            "spread_core": cfg["spread_core_v1"],
        },
        "observations": observations,
        "opportunities": opportunities,
        "predictions": predictions,
    }
    out = ROOT / args.batch_output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(batch, indent=2) + "\n")

    if args.accept:
        for r in observations:
            append_jsonl(STORE / "market_observations.jsonl", r, ["market_observation_id"])
        for r in opportunities:
            append_jsonl(STORE / "model_opportunities.jsonl", r, ["opportunity_id"])
        for r in predictions:
            append_jsonl(STORE / "model_predictions.jsonl", r, ["prediction_id"])

    print(
        f"{'Accepted' if args.accept else 'Previewed'} "
        f"{len(opportunities)} opportunities, {len(predictions)} predictions -> {out}"
    )


if __name__ == "__main__":
    main()
