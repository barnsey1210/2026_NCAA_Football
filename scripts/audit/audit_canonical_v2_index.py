#!/usr/bin/env python3
"""Block publication when the canonical index is not the V2 dashboard shell."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
candidate = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "index.html"
if not candidate.is_absolute():
    candidate = ROOT / candidate

errors: list[str] = []
if not candidate.exists():
    errors.append("file is missing")
else:
    html = candidate.read_text(errors="ignore")
    required_markers = {
        "V2 page title": "<title>NCAAF Daily Briefing</title>",
        "V2 dashboard heading": "Daily Briefing",
        "V2 navigation container": 'class="top"',
        "dashboard summary": 'class="summary"',
    }
    for label, marker in required_markers.items():
        if marker not in html:
            errors.append(f"missing {label}: {marker}")

    required_links = (
        "index.html", "ratings.html", "openers.html", "matchups.html",
        "odds.html", "schedule.html", "futures.html", "conferences.html",
        "playoff.html", "simulations.html", "betting.html", "v1.html",
    )
    for href in required_links:
        if f'href="{href}"' not in html:
            errors.append(f"missing V2 navigation link: {href}")

    required_data = (
        "data/site/matchups_view.json",
        "data/site/betting_activity_view.json",
        "data/site/matchup_line_history.json",
        "data/agents/home_top_bets.json",
    )
    for ref in required_data:
        if ref not in html:
            errors.append(f"missing dashboard data reference: {ref}")

    forbidden = {
        "legacy embedded database": '<script id="db" type="application/json">',
        "legacy page title": "<title>2026 NCAA Football</title>",
        "prototype navigation link": "_v2.html",
    }
    for label, marker in forbidden.items():
        if marker in html:
            errors.append(f"contains {label}: {marker}")

if errors:
    print(f"CANONICAL V2 INDEX AUDIT FAILED: {candidate}")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print(f"CANONICAL V2 INDEX AUDIT PASSED: {candidate}")
