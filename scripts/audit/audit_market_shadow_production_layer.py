#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
cfg = json.loads((ROOT / "config/market_shadow_production.json").read_text())
data = json.loads((ROOT / "data/site/saturday_shadow_lines.json").read_text())
ratings = pd.read_csv(ROOT / "data/ratings/fundamental_market_rating_comparison.csv", low_memory=False)

assert cfg["projected_market_value"]["terminology"] == "PROJECTED MARKET VALUE"
assert cfg["projected_market_value"]["spread"]["mode"] == "neutral_only"
assert cfg["projected_market_value"]["total"]["mode"] == "three_tier"
assert cfg["blend_market_into_fundamental"] is False
assert len(ratings) >= 100
assert "games" in data

for r in data["games"]:
    spread_components = r.get("spread_components") or {}
    spread_selection = r.get("shadow_spread_selection") or {}

    if r.get("saturday_shadow_spread") is not None:
        assert spread_selection.get("model_id") == "shadow_spread_sp_sagarin_v1"
        assert spread_selection.get("selection_status") == "AVAILABLE"
        assert spread_selection.get("availability_status") == "AVAILABLE"
        assert spread_selection.get("source_type") == "CANONICAL_GAME_PROJECTION"
        assert spread_selection.get("fallback_used") is False
        assert spread_selection.get("value_home_line") is not None
        assert abs(spread_selection["value_home_line"] - r["saturday_shadow_spread"]) < 1e-8
        assert spread_components.get("Shadow SP+") == "PRESENT"
        assert spread_components.get("Shadow Sagarin") == "PRESENT"
        assert spread_components.get("forbidden_fallbacks_rejected") == "MARKET_SPPLUS_AND_SPPLUS_ONLY"
    total_components = r.get("total_components") or {}
    total_selection = r.get("shadow_total_selection") or {}

    if r.get("saturday_shadow_total") is not None:
        assert total_selection.get("model_id") == "shadow_total_enhanced_spplus_od_v1"
        assert total_selection.get("selection_status") == "AVAILABLE"
        assert total_selection.get("availability_status") == "AVAILABLE"
        assert total_selection.get("source_type") == "CANONICAL_GAME_PROJECTION"
        assert total_selection.get("fallback_used") is False
        assert total_selection.get("value_total") is not None
        assert abs(total_selection["value_total"] - r["saturday_shadow_total"]) < 1e-8
        assert total_components.get("updated home SP+ offense") == "PRESENT"
        assert total_components.get("updated away SP+ offense") == "PRESENT"
        assert total_components.get("updated home SP+ defense") == "PRESENT"
        assert total_components.get("updated away SP+ defense") == "PRESENT"
        assert total_components.get("frozen_model_specification") == "PRESENT"
        assert total_components.get("exact_live_input_identity") == "PRESENT"
        assert total_components.get("current_60_40_bridge_rejected") == "YES"
    if not r.get("has_genuine_postgame_update"):
        assert r.get("saturday_shadow_spread") is None
        assert r.get("saturday_shadow_total") is None
        assert r.get("applied_spread_delta") is None
        assert r.get("applied_total_delta") is None
        assert r.get("spread_value_label") == "Unavailable"
        assert r.get("total_value_label") == "Unavailable"

print("PASS: market shadow production layer")
print("ratings rows:", len(ratings))
print("shadow games:", len(data["games"]))
