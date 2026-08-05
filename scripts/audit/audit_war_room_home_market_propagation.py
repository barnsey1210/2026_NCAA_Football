#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
home=ROOT/"build/public_site/index.html"
contract=ROOT/"data/site/current_market_contract.json"
matchups=ROOT/"data/site/matchups_view.json"
issues=[]
if not home.exists():
    issues.append("missing public homepage")
else:
    text=home.read_text(encoding="utf-8")
    for marker in [
        'data-war-room-home-release="locked-v2-navigation-fixed-r2-canonical-market"',
        "This Week’s Top Games",
        "Viewer’s Guide",
        "data/site/current_market_contract.json",
    ]:
        if marker not in text: issues.append(f"homepage missing marker: {marker}")
    if "Daily Briefing" in text: issues.append("legacy Daily Briefing homepage staged")
if not contract.exists(): issues.append("missing current market contract")
if not matchups.exists(): issues.append("missing matchups payload")
if contract.exists() and matchups.exists():
    c=json.loads(contract.read_text()); m=json.loads(matchups.read_text())
    cids={str(x.get("game_id")) for x in c.get("games",[])}
    mids={str(x.get("game",{}).get("game_id")) for x in m.get("games",[])}
    if not cids: issues.append("current market contract has zero games")
    if len(cids & mids)<min(100,len(cids)): issues.append("insufficient contract/matchup overlap")
result={"status":"PASS" if not issues else "FAIL","issues":issues}
print(json.dumps(result,indent=2))
if issues: raise SystemExit(1)
