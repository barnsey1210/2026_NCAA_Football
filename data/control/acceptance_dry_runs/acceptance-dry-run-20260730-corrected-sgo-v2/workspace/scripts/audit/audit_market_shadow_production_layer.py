#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
cfg = json.loads((ROOT / "config/market_shadow_production.json").read_text())
data = json.loads((ROOT / "data/site/saturday_shadow_lines.json").read_text())
ratings = pd.read_csv(ROOT / "data/ratings/fundamental_market_rating_comparison.csv", low_memory=False)

assert cfg["spread_component_weights"] == {
    "predicted_market_rating_spread": 0.5,
    "predicted_updated_sp_plus_spread": 0.5,
}
assert cfg["total_component_weights"] == {
    "predicted_sp_plus_component_total": 0.6,
    "existing_projected_total": 0.4,
}
assert cfg["total_bias_correction"] == -1.1573
assert cfg["projected_market_value"]["terminology"] == "PROJECTED MARKET VALUE"
assert cfg["projected_market_value"]["spread"]["mode"] == "neutral_only"
assert cfg["projected_market_value"]["total"]["mode"] == "three_tier"
assert cfg["blend_market_into_fundamental"] is False
assert len(ratings) >= 100
assert "games" in data

for r in data["games"]:
    spread_components = r.get("spread_components") or {}
    readiness = r.get("market_readiness_state")
    if r.get("shadow_display_ready") and readiness == "independent_market_ready" and all(spread_components.get(key) is not None for key in cfg["spread_component_weights"]):
        expected = sum(cfg["spread_component_weights"][key] * spread_components[key] for key in cfg["spread_component_weights"])
        assert abs(expected - r["saturday_shadow_spread"]) < 1e-8
    elif r.get("saturday_shadow_spread") is not None:
        expected = spread_components.get("predicted_updated_sp_plus_spread")
        assert expected is not None and abs(expected - r["saturday_shadow_spread"]) < 1e-8
        assert r.get("shadow_spread_formula") == "SP+ Fallback"
    total_components = r.get("total_components") or {}
    if r.get("shadow_display_ready") and all(total_components.get(key) is not None for key in cfg["total_component_weights"]):
        expected = sum(cfg["total_component_weights"][key] * total_components[key] for key in cfg["total_component_weights"]) + cfg["total_bias_correction"]
        assert abs(expected - r["saturday_shadow_total"]) < 1e-8
    elif r.get("saturday_shadow_total") is not None:
        raise AssertionError("total rendered without every approved component")
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
print("spread weights:", cfg["spread_component_weights"])
print("total weights:", cfg["total_component_weights"], "bias", cfg["total_bias_correction"])
