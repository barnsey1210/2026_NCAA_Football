#!/usr/bin/env python3
"""Audit the isolated historical projected-close Saturday Shadow replay."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/market_shadow_production.json"
PUBLIC_REPO = Path("/Users/jameslindesmith/Sites/NCAAF_SITE")
TOL = 1e-7


def close(a, b, tol=TOL):
    return a is not None and b is not None and math.isclose(float(a), float(b), abs_tol=tol, rel_tol=tol)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_state():
    status = subprocess.run(["git", "-C", str(PUBLIC_REPO), "status", "--short"], check=True, capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", str(PUBLIC_REPO), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    return {"head": head, "status_short": status}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/site/dry_run/projected_close")
    parser.add_argument("--schedule-preview", default="build/dry_run/projected_close/schedule_shadow_replay.html")
    parser.add_argument("--openers-preview", default="build/dry_run/projected_close/openers_shadow_projected_close_replay.html")
    args = parser.parse_args()
    out = (ROOT / args.output_dir).resolve()
    required = {
        "post": out / "postgame_shadow_updates.json",
        "lines": out / "projected_closing_lines.json",
        "schedule": out / "schedule_live_enrichment.json",
        "summary": out / "projected_close_summary.json",
        "csv": out / "projected_close_game_audit.csv",
        "safety": out / "protected_files_before.json",
        "schedule_html": (ROOT / args.schedule_preview).resolve(),
        "openers_html": (ROOT / args.openers_preview).resolve(),
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    assert not missing, f"Missing outputs: {missing}"
    post = json.loads(required["post"].read_text())
    lines = json.loads(required["lines"].read_text())
    schedule = json.loads(required["schedule"].read_text())
    summary = json.loads(required["summary"].read_text())
    safety = json.loads(required["safety"].read_text())
    cfg = json.loads(CONFIG.read_text())

    assert post["dry_run"] and lines["dry_run"] and schedule["dry_run"] and summary["dry_run"]
    assert post["completed_week"] == lines["completed_week"] == schedule["completed_week"] == 13
    assert post["target_week"] == lines["target_week"] == schedule["target_week"] == 14
    assert post["production_coefficients"]["spread_lambda"] == cfg["spread_lambda"] == 0.5
    assert post["production_coefficients"]["total_lambda_both_prior"] == cfg["total_lambda_both_prior"] == 0.85
    games = lines["games"]
    assert len(games) == 67 and len(schedule["completed_games"]) == 60
    assert len({g["game_id"] for g in games}) == len(games)
    assert len({g["game_id"] for g in schedule["completed_games"]}) == len(schedule["completed_games"])
    schedule_target = {g["game_id"]: g for g in schedule["target_games"]}
    assert set(schedule_target) == {g["game_id"] for g in games}

    updated = 0
    total_updates = 0
    for game in games:
        assert game["away_team"] and game["home_team"]
        assert game["provenance"]["week14_opener_used_as_input"] is False
        assert game["provenance"]["week14_close_used_as_input"] is False
        assert game["provenance"]["week14_result_used_as_input"] is False
        assert game["look_ahead_checks"]["frozen_spread_through_week"] == 13
        assert game["look_ahead_checks"]["frozen_total_training_week_lt"] == 14
        assert close(game["frozen_preopener_spread_baseline"], game["frozen_spread_reproduced_from_ratings"])
        expected_delta = (game["home_spread_impact"] or 0.0) + (game["away_spread_impact"] or 0.0)
        assert close(game["applied_spread_delta"], expected_delta)
        assert close(game["projected_spread_close"], game["frozen_preopener_spread_baseline"] + expected_delta)
        expected_total_base = game["home_expected_points_component"] + game["away_expected_points_component"]
        assert close(game["frozen_preopener_total_baseline"], expected_total_base)
        expected_total_delta = cfg["total_lambda_both_prior"] * game["combined_total_adjustment_raw"] if game["combined_total_adjustment_raw"] is not None else 0.0
        assert close(game["applied_total_adjustment"], expected_total_delta)
        assert close(game["projected_total_close"], game["frozen_preopener_total_baseline"] + expected_total_delta)
        assert close(game["projected_spread_move"], game["projected_spread_close"] - game["actual_opening_spread"])
        assert close(game["actual_spread_move"], game["actual_spread_close"] - game["actual_opening_spread"])
        assert close(game["projected_total_move"], game["projected_total_close"] - game["actual_opening_total"])
        assert close(game["actual_total_move"], game["actual_total_close"] - game["actual_opening_total"])
        assert schedule_target[game["game_id"]]["projected_spread_close"] == game["projected_spread_close"]
        assert schedule_target[game["game_id"]]["projected_total_close"] == game["projected_total_close"]
        should_update = bool(game["spread_update_eligible"] or game["total_update_eligible"])
        assert game["updated_game_eligible"] == should_update
        updated += should_update
        total_updates += bool(game["total_update_eligible"])

    assert updated == 62
    assert total_updates == 56
    assert summary["coverage"]["games_counted_as_updated"] == updated
    assert summary["coverage"]["games_receiving_combined_total_updates"] == total_updates
    assert summary["coverage"]["games_receiving_projected_closing_spreads"] == 67
    assert summary["coverage"]["games_receiving_projected_closing_totals"] == 67
    assert summary["total_model_audit"]["separate_team_update_reconstruction_legitimate"] is False
    assert summary["total_model_audit"]["future_information_used"] is False

    completed_ids = {g["game_id"] for g in schedule["completed_games"]}
    for update in post["updates"]:
        assert update["completed_game_id"] in completed_ids
    for game in games:
        assert all(source_id in completed_ids for source_id in game["provenance"]["spread_source_game_ids"])
        if game["total_update_eligible"]:
            assert all(source_id in completed_ids for source_id in game["provenance"]["total_source_game_ids"])
    for completed in schedule["completed_games"]:
        assert completed["away_score"] is not None and completed["home_score"] is not None
        assert completed["expanded"] and completed["expanded"]["provenance"]

    schedule_html = required["schedule_html"].read_text()
    openers_html = required["openers_html"].read_text()
    assert "HISTORICAL COMPLETED-WEEK SHADOW REPLAY — NOT LIVE DATA" in schedule_html
    assert "HISTORICAL PROJECTED-CLOSE SHADOW REPLAY — NOT LIVE DATA" in openers_html
    assert "../../../data/site/dry_run/projected_close/" in schedule_html
    assert "../../../data/site/dry_run/projected_close/" in openers_html
    forbidden = ["data/site/postgame_shadow_updates.json", "data/site/saturday_shadow_lines.json", "data/site/schedule_live_enrichment.json"]
    assert not any(item in schedule_html or item in openers_html for item in forbidden)
    assert "projected_spread_label" in openers_html and "projected_total_close" in openers_html
    assert "<details" in schedule_html and "<details" in openers_html

    for relative, before_hash in safety["protected_sha256"].items():
        path = ROOT / relative
        assert path.exists(), f"Protected file disappeared: {relative}"
        assert sha256(path) == before_hash, f"Protected file changed: {relative}"
    current_repo = repo_state()
    assert safety["publication_repo"]["status_short"] == ""
    assert current_repo["status_short"] == ""
    assert current_repo["head"] == safety["publication_repo"]["head"]

    print("PASS: historical projected-close Shadow replay")
    print(f"completed_games={len(schedule['completed_games'])} target_games={len(games)} updated={updated}")
    print(f"spread MAE={summary['headline']['spread_projected_close_mae']:.4f} direction={summary['headline']['spread_direction_agreement_pct']:.2f}% positive_CLV={summary['headline']['spread_positive_clv_pct']:.2f}%")
    print(f"total MAE={summary['headline']['total_projected_close_mae']:.4f} direction={summary['headline']['total_direction_agreement_pct']:.2f}% positive_CLV={summary['headline']['total_positive_clv_pct']:.2f}%")
    print("Schedule-to-Openers traceability passed")
    print("protected production files unchanged")
    print("publication repository unchanged and clean")


if __name__ == "__main__":
    main()
