#!/usr/bin/env python3
"""Validate the canonical public V2 bundle, including page-health integration."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EXPECTED_HEALTH = {
    "dashboard": "index.html", "ratings": "ratings.html", "openers": "openers.html",
    "matchups": "matchups.html", "odds": "odds.html", "schedule": "schedule.html",
    "futures": "futures.html", "conferences": "conferences.html", "playoff": "playoff.html",
    "simulations": "simulations.html", "betting": "betting.html",
}
VALID_STATUS = {"green", "yellow", "red", "gray"}
MODERN = list(EXPECTED_HEALTH.values()) + ["dashboard.html", "team.html"]
REQUIRED = MODERN + ["legacy.html", "matchup.html", "v1.html"]
HEALTH_FIELDS = {
    "page_id", "display_name", "status", "status_label", "summary", "last_success_at",
    "artifact_built_at", "metrics", "warnings", "critical_failures", "unavailable_reasons",
    "page_url", "source_artifacts",
}


def validate(root: Path, out: Path) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED:
        path = out / name
        minimum = 100 if name == "legacy.html" else 1000
        if not path.exists() or path.stat().st_size < minimum:
            errors.append(f"missing or too small: {name}")
            continue
        if name in MODERN:
            text = path.read_text(errors="ignore")

            if name == "index.html":
                required_home_markers = (
                    'data-war-room-home-release="locked-v2-navigation-fixed-r2-canonical-market"',
                    "This Week’s Top Games",
                    "Viewer’s Guide",
                    "data/site/current_market_contract.json",
                    'href="openers.html"',
                    'href="matchups.html"',
                    'href="betting.html"',
                )
                for marker in required_home_markers:
                    if marker not in text:
                        errors.append(f"War Room homepage marker missing: {marker}")

                forbidden_home_markers = (
                    "<title>NCAAF Daily Briefing</title>",
                    "Daily Briefing",
                    '<script id="db" type="application/json">',
                    "<title>2026 NCAA Football</title>",
                )
                for marker in forbidden_home_markers:
                    if marker in text:
                        errors.append(f"legacy homepage marker detected: {marker}")

                if "_v2.html" in text:
                    errors.append("prototype link leaked: index.html")

            else:
                if 'class="top"' not in text or 'href="openers.html"' not in text or 'href="matchups.html"' not in text:
                    errors.append(f"top navigation missing: {name}")
                if "_v2.html" in text:
                    errors.append(f"prototype link leaked: {name}")
                if '<link rel="stylesheet" href="page_health.css">' not in text or '<script defer src="page_health.js"></script>' not in text:
                    errors.append(f"page health loader missing: {name}")

                if name == "dashboard.html":
                    if "<title>NCAAF Daily Briefing</title>" not in text or "Daily Briefing" not in text:
                        errors.append(f"canonical V2 dashboard markers missing: {name}")
                    if '<script id="db" type="application/json">' in text or "<title>2026 NCAA Football</title>" in text:
                        errors.append(f"legacy V1 shell detected: {name}")
    for asset in ("page_health.js", "page_health.css"):
        path = out / asset
        if not path.is_file() or path.stat().st_size < 100:
            errors.append(f"required page health asset missing or too small: {asset}")
    js = out / "page_health.js"
    if js.is_file():
        text = js.read_text(errors="ignore")
        if "data/site/page_health_status.json" not in text or "page-health-summary" not in text:
            errors.append("page health JavaScript lacks the canonical payload loader or container marker")


    conferences = out / "conferences.html"
    if conferences.is_file():
        conference_text = conferences.read_text(errors="ignore")
        for marker in (
            'id="conferenceSelect"',
            'id="scheduleLayout"',
            'id="scheduleScroll"',
            'id="pageNote"',
            'class="range-key"',
            'Conf SOS:',
            'Rem SOS:',
            'id="healthToggle"',
            'matchup.html?game_id=',
        ):
            if marker not in conference_text:
                errors.append(f"Conference Logo Schedule marker missing: {marker}")
        if "Conference Workspace" in conference_text:
            errors.append("legacy Conference Workspace shell detected")
        if "matchup.html?game=" in conference_text:
            errors.append("legacy Conference matchup query parameter detected")

    betting = out / "betting.html"
    if betting.is_file():
        betting_text = betting.read_text(errors="ignore")
        for marker in ('data-view="bets">My Bets', 'data-view="model">Model Performance',
                       'id="modelPerformanceView"'):
            if marker not in betting_text:
                errors.append(f"Betting Model Performance marker missing: {marker}")
    model_performance = out / "data/site/model_performance_view.json"
    if not model_performance.is_file():
        errors.append("Model Performance public artifact missing")
    else:
        try:
            model_data = json.loads(model_performance.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"Model Performance public artifact malformed: {exc}")
        else:
            if model_data.get("schema_version") != "model-performance-view-v2":
                errors.append("Model Performance public artifact schema mismatch")

    health = root / "data/site/page_health_status.json"
    if not health.exists():
        errors.append("page health artifact missing")
    else:
        try:
            data = json.loads(health.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"page health artifact malformed: {exc}")
        else:
            pages = data.get("pages")
            if not isinstance(pages, list):
                errors.append("page health pages must be a list")
                pages = []
            ids = [page.get("page_id") for page in pages if isinstance(page, dict)]
            if set(ids) != set(EXPECTED_HEALTH) or len(ids) != len(EXPECTED_HEALTH):
                errors.append(f"page health IDs mismatch: {sorted(str(x) for x in ids)}")
            for page in pages:
                if not isinstance(page, dict):
                    errors.append("page health record is not an object")
                    continue
                page_id = page.get("page_id")
                missing = HEALTH_FIELDS - set(page)
                if missing:
                    errors.append(f"page health record {page_id!r} missing fields: {sorted(missing)}")
                if page.get("status") not in VALID_STATUS:
                    errors.append(f"page health record {page_id!r} has invalid status: {page.get('status')!r}")
                if page_id in EXPECTED_HEALTH and page.get("page_url") != EXPECTED_HEALTH[page_id]:
                    errors.append(f"page health URL mismatch for {page_id}: {page.get('page_url')!r}")

    shadow = root / "data/site/postgame_shadow_updates.json"
    if not shadow.exists():
        errors.append("postgame shadow artifact missing")
    else:
        try:
            data = json.loads(shadow.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"postgame shadow artifact malformed: {exc}")
        else:
            if data.get("applied_to_ratings") or data.get("applied_to_projections"):
                errors.append("shadow artifact marked as applied")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out.resolve() if args.out else root / "build/public_site"
    errors = validate(root, out)
    if errors:
        print("PUBLIC SITE VALIDATION FAILED")
        print("\n".join("- " + error for error in errors))
        raise SystemExit(1)
    print(f"PUBLIC SITE VALIDATION PASSED: {len(REQUIRED)} pages; shadow artifact isolated; page health complete")


if __name__ == "__main__":
    main()
