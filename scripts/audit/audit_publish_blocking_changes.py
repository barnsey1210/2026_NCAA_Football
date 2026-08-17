#!/usr/bin/env python3
from pathlib import Path
import subprocess
import hashlib

MAIN = Path("/Users/jameslindesmith/NCAAF_MAIN_REPO")
AUTO = Path("/Users/jameslindesmith/NCAAF_AUTO")

FILES = [
    "conferences.html",
    "data/qa/page_health_status.json",
    "data/qa/page_health_status_details.csv",
    "data/site/model_performance_view.json",
    "data/site/page_health_status.json",
    "odds.html",
]

def sh(*args):
    return subprocess.run(args, cwd=MAIN, text=True, capture_output=True)

def sha(path):
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]

print("=== PUBLISH-BLOCKING TRACKED CHANGES ===")
for rel in FILES:
    path = MAIN / rel
    r = sh("git", "status", "--short", "--", rel)
    status = r.stdout.strip() or "clean"
    print(f"\n{rel}")
    print(f"  git status: {status}")
    d = sh("git", "diff", "--numstat", "--", rel)
    print(f"  diff numstat: {d.stdout.strip() or 'none'}")
    print(f"  main sha: {sha(path) or 'missing'}")
    auto = AUTO / rel
    print(f"  auto sha: {sha(auto) or 'missing'}")
    pub = AUTO / "build/public_site" / rel
    print(f"  public sha: {sha(pub) or 'missing'}")

print("\n=== SUMMARY DIFF STAT ===")
r = sh("git", "diff", "--stat", "--", *FILES)
print(r.stdout or "(no diff stat)")

print("\n=== HEAD COMPARISON ===")
for rel in FILES:
    r = sh("git", "diff", "--quiet", "HEAD", "--", rel)
    print(f"{'DIRTY' if r.returncode else 'CLEAN'}  {rel}")

print("\nNo files were changed.")
