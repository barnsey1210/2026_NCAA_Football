#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path.home() / "NCAAF_AUTO"
summary_path = ROOT / "data/research/full_saturday_shadow_backtest/summary.json"
assert summary_path.exists(), f"Missing {summary_path}"
s = json.loads(summary_path.read_text())

assert s["spread"]["baseline"]["n"] > 0
assert s["spread"]["best_shadow"]["n"] > 0
assert s["total"]["baseline"]["n"] > 0
assert s["total"]["best_shadow"]["n"] > 0

print("PASS: full Saturday shadow backtest")
print("spread baseline MAE:", s["spread"]["baseline"]["mae"])
print("spread shadow MAE:", s["spread"]["best_shadow"]["mae"])
print("spread lambda:", s["spread"]["best_lambda"])
print("total baseline MAE:", s["total"]["baseline"]["mae"])
print("total shadow MAE:", s["total"]["best_shadow"]["mae"])
print("total lambda:", s["total"]["best_lambda"])
