#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path.home()/"NCAAF_AUTO"
for step in [ROOT/"scripts/site/build_schedule_live_enrichment.py",ROOT/"scripts/site/inject_schedule_live_scoreboard.py"]:
    print("RUN:",step); subprocess.run([sys.executable,str(step)],check=True)
print("schedule live scoreboard build complete")
