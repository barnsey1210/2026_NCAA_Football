#!/usr/bin/env python3
"""Validate that index.html is the locked War Room homepage."""

from __future__ import annotations

from pathlib import Path
import sys


def validate(path: Path) -> list[str]:
    if not path.is_file():
        return [f"missing index file: {path}"]

    html = path.read_text(errors="ignore")
    errors: list[str] = []

    required = {
        "locked War Room release marker": "data-war-room-home-release=",
        "War Room brand": "WAR<span>ROOM</span>",
        "native War Room header": '<header class="war-room-global">',
        "native War Room navigation": '<nav class="nav war-room-nav">',
        "data-health indicator": "Data Healthy",
        "Top Games lane": "This Week’s Top Games",
        "Viewer’s Guide lane": "Viewer’s Guide",
        "canonical current-market contract": "data/site/current_market_contract.json",
        "canonical matchup payload": "data/site/matchups_view.json",
        "canonical Openers drawer route": "openers.html?game_id=",
    }
    for label, marker in required.items():
        if marker not in html:
            errors.append(f"missing {label}: {marker}")

    forbidden = {
        "retired Daily Briefing title": "<title>NCAAF Daily Briefing</title>",
        "retired Daily Briefing heading": ">Daily Briefing<",
        "retired Dashboard route": 'href="dashboard.html"',
        "retired V1 route": 'href="v1.html"',
        "retired V1 label": "V1 Reference",
        "legacy embedded database": '<script id="db" type="application/json">',
        "legacy NCAA page title": "<title>2026 NCAA Football</title>",
    }
    for label, marker in forbidden.items():
        if marker in html:
            errors.append(f"contains {label}: {marker}")

    return errors


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html").resolve()
    errors = validate(path)
    if errors:
        print(f"WAR ROOM INDEX AUDIT FAILED: {path}")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"WAR ROOM INDEX AUDIT PASSED: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
