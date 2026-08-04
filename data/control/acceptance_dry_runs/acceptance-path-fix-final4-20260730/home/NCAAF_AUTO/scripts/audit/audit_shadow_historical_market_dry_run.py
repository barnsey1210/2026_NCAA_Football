#!/usr/bin/env python3
"""Audit the isolated historical market Shadow replay and its safety boundary."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DRY = ROOT / "data/site/dry_run"
PREVIEW = ROOT / "build/dry_run/openers_shadow_dry_run.html"
CONFIG = ROOT / "config/market_shadow_production.json"
PUBLIC_REPO = Path("/Users/jameslindesmith/Sites/NCAAF_SITE")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def close(a, b):
    return a is not None and b is not None and math.isclose(float(a), float(b), abs_tol=1e-8)


def main():
    names = ["postgame_shadow_updates.json", "saturday_shadow_lines.json", "schedule_live_enrichment.json", "shadow_market_replay_summary.json"]
    payload = {}
    for name in names:
        path = DRY / name
        assert path.exists(), f"missing {path}"
        payload[name] = json.loads(path.read_text())
        assert payload[name].get("dry_run") is True, f"missing dry-run marker: {name}"
    post = payload["postgame_shadow_updates.json"]
    lines = payload["saturday_shadow_lines.json"]
    schedule = payload["schedule_live_enrichment.json"]
    summary = payload["shadow_market_replay_summary.json"]
    cfg = json.loads(CONFIG.read_text())
    assert (post["season"], post["completed_week"], post["target_week"]) == (2025, 13, 14)
    assert lines["season"] == 2025 and lines["target_week"] == 14
    assert schedule["season"] == 2025 and schedule["week"] == 14
    assert lines["production_coefficients"]["spread_lambda"] == cfg["spread_lambda"]
    assert lines["production_coefficients"]["total_lambda_both_prior"] == cfg["total_lambda_both_prior"]
    games = lines["games"]
    assert len(games) == 67 and len({g["game_id"] for g in games}) == len(games)
    schedule_by_id = {g["game_id"]: g for g in schedule["games"]}
    assert set(schedule_by_id) == {g["game_id"] for g in games}
    for game in games:
        assert game["week"] == 14 and game["season"] == 2025
        assert game["away_team"] == schedule_by_id[game["game_id"]]["away_team"]
        assert game["home_team"] == schedule_by_id[game["game_id"]]["home_team"]
        assert game["market_baseline_spread_field"] == "opening_home_spread"
        assert game["market_baseline_total_field"] == "opening_total"
        assert game["provenance"]["later_market_used_as_input"] is False
        assert game["provenance"]["actual_result_used_as_input"] is False
        if game["shadow_spread"] is not None:
            assert close(game["shadow_spread"], game["historical_market_baseline_spread"] + game["applied_spread_delta"])
            contributions = sum(v or 0 for v in (game["away_spread_impact"], game["home_spread_impact"]))
            assert close(game["applied_spread_delta"], contributions)
        if game["shadow_total"] is not None:
            assert close(game["shadow_total"], game["historical_market_baseline_total"] + game["applied_total_delta"])
            assert close(game["applied_total_delta"], cfg["total_lambda_both_prior"] * game["raw_total_impact"])
            assert game["provenance"]["total_sources_match_completed_week"] is True
        eligible = game["applied_spread_delta"] is not None or game["applied_total_delta"] is not None
        assert game["updated_game_eligible"] is eligible
        assert game["away_total_impact"] is None and game["home_total_impact"] is None
        assert close(game["actual_home_margin"], float(game["actual_home_margin"]))
    assert summary["target_games_counted_as_updated"] == sum(g["updated_game_eligible"] for g in games)
    assert summary["target_games_counted_as_updated"] > 0
    assert PREVIEW.exists()
    html = PREVIEW.read_text()
    assert "HISTORICAL MARKET SHADOW DRY RUN — NOT LIVE DATA" in html
    assert "../../data/site/dry_run/" in html
    for name in ("postgame_shadow_updates.json", "saturday_shadow_lines.json", "schedule_live_enrichment.json"):
        assert name in html
    assert "data/site/postgame_shadow_updates.json" not in html.replace("../../data/site/dry_run/postgame_shadow_updates.json", "")
    safety = json.loads((DRY / "protected_files_before.json").read_text())
    for relative, digest in safety["protected_sha256"].items():
        path = ROOT / relative
        assert path.exists() and sha256(path) == digest, f"protected file changed: {relative}"
    status = subprocess.run(["git", "-C", str(PUBLIC_REPO), "status", "--short"], check=True, capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", str(PUBLIC_REPO), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    assert not status, "publication repository is dirty"
    assert head == safety["publication_repo"]["head"], "publication repository HEAD changed"
    assert not safety["publication_repo"]["status_short"], "publication repository was dirty before replay"
    print("PASS: historical market Shadow dry run")
    print(f"games={len(games)} updated={summary['target_games_counted_as_updated']}")
    print(f"spread baseline/shadow MAE={summary['spread_market_evaluation']['baseline_mae_to_later_market']:.4f}/{summary['spread_market_evaluation']['shadow_mae_to_later_market']:.4f}")
    print(f"total baseline/shadow MAE={summary['total_market_evaluation']['baseline_mae_to_later_market']:.4f}/{summary['total_market_evaluation']['shadow_mae_to_later_market']:.4f}")
    print("protected production files unchanged")
    print("publication repository unchanged and clean")


if __name__ == "__main__":
    main()
