#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path.home() / "NCAAF_AUTO"
path = ROOT / "data/site/saturday_shadow_lines.json"
assert path.exists(), f"Missing {path}"
data = json.loads(path.read_text())
rows = data.get("games", [])

direct = [r for r in rows if r.get("market_baseline_total_source") == "current_market_total"]
fallback = [r for r in rows if r.get("market_baseline_total_source") == "official_fallback"]
missing = [r for r in rows if r.get("market_baseline_total") is None]
complete = [r for r in rows if str(r.get("total_status", "")).startswith("Complete")]

print("PASS: current-market total baseline audit")
print("games:", len(rows))
print("direct current-market totals:", len(direct))
print("official total fallbacks:", len(fallback))
print("missing total baselines:", len(missing))
print("total complete:", len(complete))

if rows and not direct:
    print("WARNING: no direct current-market total field was detected in the embedded game records.")
    print("Checked current_total, market_total, consensus_total, best_total, latest_total, total_line, and opener fields.")
