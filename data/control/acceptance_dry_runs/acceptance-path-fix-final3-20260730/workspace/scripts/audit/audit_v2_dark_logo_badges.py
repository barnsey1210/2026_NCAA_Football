#!/usr/bin/env python3
from pathlib import Path

root=Path.home()/"NCAAF_AUTO"
pages=sorted(root.glob("*_v2.html"))
assert pages, "No V2 pages found"
missing=[]
for path in pages:
    text=path.read_text(errors="ignore")
    if "V2_DARK_LOGO_BADGES_CSS_V2" not in text or 'img[src*="/iowa.png"]' not in text:
        missing.append(path.name)
if missing:
    raise AssertionError("Missing CSS dark-logo treatment: "+", ".join(missing))
print(f"PASS: CSS dark-logo treatment present on {len(pages)} V2 pages")
