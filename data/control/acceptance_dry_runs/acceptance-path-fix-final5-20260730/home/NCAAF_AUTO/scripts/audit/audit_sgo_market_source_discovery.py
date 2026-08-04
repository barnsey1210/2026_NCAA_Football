#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path.home() / "NCAAF_AUTO"
path = ROOT / "data/audit/sgo_market_source_discovery.json"
assert path.exists(), f"Missing {path}"
data = json.loads(path.read_text())
sources = data.get("sources", [])
assert sources, "No market-bearing arrays found in embedded DB."

best = sources[0]
total_hits = sum(
    v for k, v in best["market_counts"].items()
    if k.startswith("total:")
)
spread_hits = sum(
    v for k, v in best["market_counts"].items()
    if k.startswith("spread:")
)

print("PASS: SGO market source discovery")
print("best source:", best["path"])
print("rows:", best["rows"])
print("total field hits:", total_hits)
print("spread field hits:", spread_hits)
print("fields:", best["market_counts"])
