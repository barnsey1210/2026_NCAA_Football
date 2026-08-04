#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
script = ROOT / "daily_market_update.sh"
text = script.read_text(encoding="utf-8", errors="ignore")

required = [
    "python3 scripts/site/build_public_site.py",
    "python3 scripts/publish/check_public_site.py",
    "scripts/publish/publish_site.sh --push",
    "pull_cfbd_lines_2026.py",
    "pull_actionnetwork_ncaaf_game_lines_2026.py",
    "pull_theodds_ncaaf_lines_2026.py",
]
for token in required:
    assert token in text, f"Missing: {token}"

assert text.count("# AUTO_GITHUB_PUBLISH_START") == 1
assert text.count("# AUTO_GITHUB_PUBLISH_END") == 1
assert "git add index.html" not in text

print("PASS: daily Schedule kickoff refresh/publish v1")
print("Daily flow now refreshes line sources, rebuilds Schedule enrichment, validates, and publishes the full site.")
