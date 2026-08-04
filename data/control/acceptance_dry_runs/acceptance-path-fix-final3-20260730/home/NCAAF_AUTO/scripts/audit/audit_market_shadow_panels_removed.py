#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
pages = [
    ROOT / "ratings_v2.html",
    ROOT / "openers_v2.html",
    ROOT / "schedule_v2.html",
]

START = "<!-- MARKET_SHADOW_LAYER_START -->"
END = "<!-- MARKET_SHADOW_LAYER_END -->"

for page in pages:
    assert page.exists(), f"Missing: {page}"
    text = page.read_text(encoding="utf-8", errors="ignore")
    assert START not in text, f"{page.name}: start marker still present"
    assert END not in text, f"{page.name}: end marker still present"
    assert 'id="market-shadow-layer-data"' not in text, f"{page.name}: payload still present"

print("PASS: temporary market-shadow panels removed")
for page in pages:
    print(page.name)
