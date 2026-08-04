#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT = Path.home() / "NCAAF_AUTO"
path = ROOT / "data/site/schedule_live_enrichment.json"
raw = path.read_text(encoding="utf-8")

assert "NaN" not in raw
assert "Infinity" not in raw
json.loads(raw)

node = subprocess.run(
    ["node", "-e", "JSON.parse(require('fs').readFileSync(process.argv[1],'utf8'));", str(path)],
    capture_output=True,
    text=True,
)
assert node.returncode == 0, node.stderr

print("PASS: Schedule enrichment is valid browser JSON v5")
