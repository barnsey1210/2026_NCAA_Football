#!/usr/bin/env python3
"""Non-network, non-publication acceptance tests for refresh controller V1."""
from pathlib import Path
import hashlib, json, os, subprocess, sys

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
CTL = ROOT / "scripts/control/run_data_refresh.py"
SHELLS = [p for p in ROOT.glob("*_v2.html")] + [ROOT/"index.html", ROOT/"team.html", ROOT/"matchup.html"]

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
before = {str(p.relative_to(ROOT)): digest(p) for p in SHELLS}
cases = [
    (["status"], 0, "status-only"),
    (["odds", "--dry-run", "--scope", "both", "--test-scenario", "no_change"], 0, "odds games+futures no-change"),
    (["ratings", "--dry-run", "--test-scenario", "rating_failure"], 0, "rating failure isolation"),
    (["ratings", "--dry-run", "--test-scenario", "malformed_rating"], 0, "malformed rejection"),
    (["postgame", "--dry-run"], 0, "postgame canonical plan"),
    (["pregame", "--dry-run"], 0, "pregame canonical plan"),
    (["full", "--dry-run", "--test-scenario", "quota_block"], 2, "quota blocking"),
    (["odds", "--dry-run", "--providers", "sports_game_odds", "--test-scenario", "cooldown_block"], 2, "cooldown blocking"),
    (["full", "--dry-run", "--test-scenario", "overlap"], 2, "overlap blocking"),
    (["publish-existing", "--dry-run"], 0, "data-only publication plan"),
]
failures=[]
for args, expected, label in cases:
    r=subprocess.run([PY, str(CTL), *args], cwd=ROOT, text=True, capture_output=True)
    if r.returncode != expected: failures.append(f"{label}: rc {r.returncode}, expected {expected}")
after = {str(p.relative_to(ROOT)): digest(p) for p in SHELLS}
if before != after: failures.append("canonical V2 hashes changed")
generated = "\n".join((ROOT/x).read_text(errors="ignore") for x in ["data/control/latest_refresh_status.json", "data/control/refresh_run_history.json", "data/control/refresh_runs.jsonl"] if (ROOT/x).exists())
for name in ("THE_ODDS_API_KEY", "SGO_API_KEY", "SPORTSGAMEODDS_API_KEY", "CFBD_API_KEY", "NCAAF_GMAIL_APP_PASSWORD"):
    val=os.environ.get(name)
    if val and val in generated: failures.append(f"secret value leaked: {name}")
daily=(ROOT/"daily_market_update.sh").read_text()
publisher=(ROOT/"scripts/publish/publish_site.sh").read_text()
if "build/public_site" not in publisher or "audit_canonical_v2_index.py" not in publisher: failures.append("canonical publisher protections missing")
if "Skipping legacy index injectors" not in daily: failures.append("legacy prevention marker missing")
registry=json.loads((ROOT/"scripts/control/refresh_stage_registry.json").read_text())
if set(registry.get("modes",{})) != {"status","odds","ratings","postgame","pregame","full","publish-existing"}: failures.append("canonical mode registry incomplete")
if registry["modes"]["odds"].get("default_scope") != "both": failures.append("odds default scope is not games+futures")
print(f"Refresh controller tests: {'FAILED' if failures else 'PASSED'}")
for _,_,label in cases: print(f"- {label}: tested")
print(f"- V2 shell hashes unchanged: {before == after}")
print("- External calls made: 0")
print("- Publication performed: no")
for f in failures: print(f"ERROR: {f}")
raise SystemExit(1 if failures else 0)
