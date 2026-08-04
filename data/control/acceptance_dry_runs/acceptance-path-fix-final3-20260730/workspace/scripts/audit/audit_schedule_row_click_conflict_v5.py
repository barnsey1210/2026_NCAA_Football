#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
page = ROOT / "schedule_v2.html"
text = page.read_text(encoding="utf-8", errors="ignore")

native_start = text.find("rows.querySelectorAll('.scheduleNativeRow').forEach(row=>{")
assert native_start >= 0, "Native row handler block missing"
native_end = text.find("})", native_start)
snippet = text[native_start:native_start + 900]

assert "row.addEventListener('click'" in snippet
assert "e.stopPropagation()" in snippet
assert "e.stopImmediatePropagation()" in snippet
assert "},true)" in snippet
assert "row.onclick" not in snippet

print("PASS: Schedule row click conflict v5")
print("Native rows expand inline and suppress the global matchup listener.")
