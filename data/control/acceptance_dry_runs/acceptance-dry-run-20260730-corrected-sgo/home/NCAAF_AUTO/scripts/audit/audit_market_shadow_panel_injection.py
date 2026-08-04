#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
pages = [
    ROOT / "ratings_v2.html",
    ROOT / "openers_v2.html",
    ROOT / "schedule_v2.html",
]

start = "<!-- MARKET_SHADOW_LAYER_START -->"
end = "<!-- MARKET_SHADOW_LAYER_END -->"

for page in pages:
    assert page.exists(), f"Missing {page}"
    text = page.read_text(encoding="utf-8", errors="ignore")
    assert text.count(start) == 1, f"{page.name}: expected one start marker"
    assert text.count(end) == 1, f"{page.name}: expected one end marker"
    assert 'id="market-shadow-layer-data"' in text, f"{page.name}: missing data payload"

print("PASS: market shadow panels injected")
for page in pages:
    print(page.name)
