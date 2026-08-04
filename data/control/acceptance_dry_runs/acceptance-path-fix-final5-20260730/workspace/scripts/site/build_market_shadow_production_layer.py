#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path.home() / "NCAAF_AUTO"
steps = [
    ROOT / "scripts/ratings/build_fundamental_market_rating_comparison.py",
    ROOT / "scripts/site/build_saturday_shadow_lines.py",

]
for step in steps:
    if not step.exists():
        raise SystemExit(f"Missing: {step}")
    print("RUN:", step)
    subprocess.run([sys.executable, str(step)], check=True)
print("market shadow production layer complete")
