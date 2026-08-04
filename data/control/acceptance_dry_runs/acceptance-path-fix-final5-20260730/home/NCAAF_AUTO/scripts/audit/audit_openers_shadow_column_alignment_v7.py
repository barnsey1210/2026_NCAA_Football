#!/usr/bin/env python3
from pathlib import Path

ROOT=Path.home()/"NCAAF_AUTO"
p=(ROOT/"openers_v2.html").read_text(errors="ignore")

assert "function enhanceTableMarks(){if(projectionMode==='shadow')return;" in p
assert 'id="openers-shadow-column-alignment-css-v7"' in p
assert "tbody td:nth-child(7)" in p
assert "tbody td:nth-child(6){border-left:0}" in p

print("PASS: Openers shadow column alignment v7")
