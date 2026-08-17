#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path.cwd()
print("THE ODDS API GOVERNANCE AUDIT")
print("="*96)
print("repo:",ROOT)

targets=[
"daily_market_update.sh",
"pull_theodds_ncaaf_lines_2026.py",
"build_theodds_season_lines_2026.py",
"scripts/markets/build_current_market_contract.py",
"scripts/odds/append_game_line_history.py",
]

for rel in targets:
    f=ROOT/rel
    print("\n"+"="*96)
    print(rel, "=>", "FOUND" if f.exists() else "MISSING")
    if not f.exists(): continue
    lines=f.read_text(errors="replace").splitlines()
    pats=[
        r"api\.the-odds-api\.com", r"THE_ODDS_API_KEY", r"ODDS_API_KEY",
        r"x-requests-last", r"x-requests-used", r"x-requests-remaining",
        r"bookmakers", r"regions", r"markets", r"americanfootball_ncaaf",
        r"current_market_contract", r"The Odds API", r"SportsGameOdds",
        r"Action Network", r"game_line_history"
    ]
    hits=[]
    for i,line in enumerate(lines,1):
        if any(re.search(p,line,re.I) for p in pats):
            hits.append((i,line))
    for i,line in hits[:220]:
        print(f"{i:5d}: {line}")
    if len(hits)>220:
        print(f"... {len(hits)-220} more matching lines omitted")

print("\n"+"="*96)
print("ALL LIVE-CALL-CAPABLE THE ODDS API PYTHON FILES")
call_sites=[]
for f in ROOT.rglob("*.py"):
    if any(part in {".git",".venv","venv","__pycache__","build"} for part in f.parts):
        continue
    try: text=f.read_text(errors="replace")
    except Exception: continue
    if "api.the-odds-api.com" in text or "THE_ODDS_API_KEY" in text:
        liveish=bool(re.search(r"urlopen|requests\.(get|post)|httpx\.|urllib\.request|api\.the-odds-api\.com",text))
        call_sites.append((str(f.relative_to(ROOT)),liveish))
for rel,liveish in sorted(call_sites):
    print(f"{'LIVE?' if liveish else 'REF '}  {rel}")

print("\n"+"="*96)
print("CURRENT OUTPUT ARTIFACTS")
for rel in [
    "data/site/current_market_contract.json",
    "data/odds/game_line_history.csv",
    "data/audits/theodds_ncaaf_10book_test.json",
]:
    f=ROOT/rel
    print(rel, "FOUND" if f.exists() else "missing", f.stat().st_size if f.exists() and f.is_file() else "")

issues=[]
daily=ROOT/"daily_market_update.sh"
if daily.exists() and "pull_theodds_ncaaf_lines_2026.py" not in daily.read_text(errors="replace"):
    issues.append("daily workflow does not call The Odds API acquisition script")

puller=ROOT/"pull_theodds_ncaaf_lines_2026.py"
if puller.exists():
    t=puller.read_text(errors="replace").lower()
    if not all(x in t for x in ("x-requests-last","x-requests-used","x-requests-remaining")):
        issues.append("primary puller does not record all quota headers")
    if "bookmakers" not in t:
        issues.append("primary puller may not use explicit <=10-book bookmaker selection")

live_owners=[rel for rel,liveish in call_sites if liveish]
if len(live_owners)>1:
    issues.append("multiple live-call-capable files exist; tests should default to fixture/replay")

print("\n"+"="*96)
print("ISSUES / NEXT PATCH TARGETS")
if issues:
    for i,x in enumerate(issues,1): print(f"{i}. {x}")
else:
    print("No obvious governance defects detected by static audit.")
print("\nNO PROVIDER CALLS WERE MADE BY THIS AUDIT.\n")
