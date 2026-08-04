#!/usr/bin/env python3
from pathlib import Path
import re

root=Path.home()/"NCAAF_AUTO"
files=[
    root/"scripts/research/analyze_postgame_pbp_market_rating_update.py",
    root/"scripts/research/analyze_postgame_total_market_update.py",
    root/"scripts/site/build_postgame_shadow_updates.py",
]

terms=(
    "target","closing","close","next_game","next game","line_move",
    "spread_move","total_move","opener","baseline","mae"
)

for path in files:
    print("\nFILE:",path)
    if not path.exists():
        print("MISSING")
        continue
    lines=path.read_text(errors="ignore").splitlines()
    for i,line in enumerate(lines,1):
        low=line.lower()
        if any(term in low for term in terms):
            print(f"{i}: {line[:300]}")

print("\nInterpretation rule:")
print("Confirm the exact target column and baseline expression from the research scripts.")
print("Do not label the UI as next-game closing-line prediction until those lines explicitly support it.")
