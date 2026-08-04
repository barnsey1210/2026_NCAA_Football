#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path.home()/"NCAAF_AUTO"
path=ROOT/"data/research/phase_opponent_shadow_calibration/summary.json"
assert path.exists(), f"Missing {path}"
s=json.loads(path.read_text())

spread=s["spread"]["selected_on_2024"]
assert spread["holdout"]["n"] > 0
assert spread["holdout_baseline"]["n"] > 0
assert s["total"]["uses_pbp"] is True
assert s["total"]["holdout_shadow"]["n"] > 0

print("PASS: phase/opponent shadow calibration")
print("selected spread structure:", spread["kind"])
print("spread coefficients:", spread["coef"])
print("spread 2025 baseline MAE:", spread["holdout_baseline"]["mae"])
print("spread 2025 shadow MAE:", spread["holdout"]["mae"])
print("total 2024 lambda:", s["total"]["lambda"])
print("total 2025 baseline MAE:", s["total"]["holdout_baseline"]["mae"])
print("total 2025 shadow MAE:", s["total"]["holdout_shadow"]["mae"])
print("total uses PBP:", s["total"]["uses_pbp"])
