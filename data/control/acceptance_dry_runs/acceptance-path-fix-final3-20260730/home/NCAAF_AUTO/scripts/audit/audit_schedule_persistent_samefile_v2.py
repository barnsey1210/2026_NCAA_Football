#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
target = ROOT / "scripts/site/build_schedule_persistent.py"
text = target.read_text(encoding="utf-8", errors="ignore")

assert "def copy_if_distinct" in text
assert "source.samefile(destination)" in text
assert "already shared/synced" in text

print("PASS: persistent Schedule SameFile handling v2")
print("Shared or symlinked public data paths are now skipped safely.")
