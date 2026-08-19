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
MODERN = list(EXPECTED_HEALTH.values()) + ["team.html"]
REQUIRED = MODERN + ["war-room.html"]
HEALTH_FIELDS = {
    "page_id", "display_name", "status", "status_label", "summary", "last_success_at",
    "artifact_built_at", "metrics", "warnings", "critical_failures", "unavailable_reasons",
    "page_url", "source_artifacts",
}


def validate(root: Path, out: Path) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED:
        path = out / name
        minimum = 1000
        if not path.exists() or path.stat().st_size < minimum:
            errors.append(f"missing or too small: {name}")
            continue
        if name == "war-room.html":
            text = path.read_text(errors="ignore")
            for marker in (
                "data/site/war_room_market_matrix.json",
                "data/site/war_room_health.json",
                'id="refreshBtn"',
            ):
                if marker not in text:
                    errors.append(f"War Room terminal marker missing: {marker}")
        elif name in MODERN:
            text = path.read_text(errors="ignore")
            if name != "index.html":
                for marker in ('WAR<span>ROOM</span>', 'class="nav war-room-nav"', 'Data Healthy'):
                    if marker not in text:
                        errors.append(f"shared War Room shell missing from {name}: {marker}")
            if 'href="dashboard.html"' in text or '>Dashboard</a>' in text:
                errors.append(f"retired Dashboard navigation leaked: {name}")

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
                has_shared_nav = (
                    'class="nav war-room-nav"' in text
                    and 'href="index.html"' in text
                    and 'href="openers.html"' in text
                    and 'href="matchups.html"' in text
                )
                if not has_shared_nav:
                    errors.append(f"top navigation missing: {name}")
                if "_v2.html" in text:
                    errors.append(f"prototype link leaked: {name}")
                if '<link rel="stylesheet" href="page_health.css">' not in text or '<script defer src="page_health.js"></script>' not in text:
                    errors.append(f"page health loader missing: {name}")

    for retired in ("dashboard.html", "legacy.html", "v1.html"):
        if (out / retired).exists():
            errors.append(f"retired public artifact returned: {retired}")

    matchup_payload = out / "data/site/matchups_view.json"
    if matchup_payload.is_file() and matchup_payload.stat().st_size > 16 * 1024 * 1024:
        errors.append(f"public matchup payload exceeds 16 MiB: {matchup_payload.stat().st_size}")

    for asset in ("page_health.js", "page_health.css"):
        path = out / asset
        if not path.is_file() or path.stat().st_size < 100:
            errors.append(f"required page health asset missing or too small: {asset}")
    js = out / "page_health.js"
    if js.is_file():
        text = js.read_text(errors="ignore")
        if "data/site/page_health_status.json" not in text or "page-health-summary" not in text:
            errors.append("page health JavaScript lacks the canonical payload loader or container marker")

    war_room_artifacts = {
        "war_room_market_matrix.json": "war-room-market-matrix-v1",
        "war_room_health.json": "war-room-health-v1",
    }
    for filename, expected_schema in war_room_artifacts.items():
        path = out / "data" / "site" / filename
        if not path.is_file():
            errors.append(f"War Room public artifact missing: data/site/{filename}")
            continue
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"War Room public artifact malformed ({filename}): {exc}")
            continue
        if payload.get("schema_version") != expected_schema:
            errors.append(
                f"War Room public artifact schema mismatch ({filename}): "
                f"{payload.get('schema_version')!r}"
            )
        if filename == "war_room_market_matrix.json" and not isinstance(payload.get("games"), list):
            errors.append("War Room market matrix games must be a list")
        if filename == "war_room_health.json" and not isinstance(payload.get("fast_market_refresh"), dict):
            errors.append("War Room health fast_market_refresh must be an object")


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
            'openers.html?game_id=',
        ):
            if marker not in conference_text:
                errors.append(f"Conference Logo Schedule marker missing: {marker}")
        if "Conference Workspace" in conference_text:
            errors.append("legacy Conference Workspace shell detected")
        if "matchup.html?game=" in conference_text or "matchup.html?game_id=" in conference_text:
            errors.append("legacy Conference matchup route detected")

    betting = out / "betting.html"
    if betting.is_file():
        betting_text = betting.read_text(errors="ignore")
        for marker in ('data-view="bets">My Bets', 'data-view="model">Model Performance',
                       'id="modelPerformanceView"', 'data-performance-mode="standard"',
                       'data-performance-mode="shadow"', 'id="standardModelsPanel"',
                       'id="shadowModelsPanel"', 'data/site/shadow_model_performance.json'):
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

    shadow_performance = out / "data/site/shadow_model_performance.json"
    if not shadow_performance.is_file():
        errors.append("Shadow Model Performance public artifact missing")
    else:
        try:
            shadow_data = json.loads(shadow_performance.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"Shadow Model Performance public artifact malformed: {exc}")
        else:
            if shadow_data.get("schema_version") != "shadow-model-performance-v1":
                errors.append("Shadow Model Performance public artifact schema mismatch")
            expected = {
                "spread": {"ALL": 470, "2+": 246, "2.5+": 204, "3+": 172, "3.5+": 142, "4+": 110, "5+": 59},
                "totals": {"ALL": 462, "1+": 341, "1.5+": 286, "2+": 242, "2.5+": 203, "3+": 173, "3.5+": 133, "4+": 109, "5+": 66},
            }
            for market, rows in expected.items():
                actual = {row.get("threshold"): row.get("sample_size") for row in shadow_data.get(market, {}).get("pooled", {}).get("thresholds", [])}
                if actual != rows:
                    errors.append(f"Shadow {market} pooled threshold contract mismatch: {actual}")
            spread_quality = shadow_data.get("spread", {}).get("stale_vs_shadow", {}).get("pooled", {})
            totals_quality = shadow_data.get("totals", {}).get("stale_vs_shadow", {}).get("pooled", {})
            if (spread_quality.get("stale", {}).get("sample_size"), spread_quality.get("shadow", {}).get("sample_size")) != (470, 470):
                errors.append("Shadow spread quality sample mismatch")
            if (totals_quality.get("stale", {}).get("sample_size"), totals_quality.get("shadow", {}).get("sample_size")) != (462, 462):
                errors.append("Shadow totals quality sample mismatch")

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
    print(f"PUBLIC SITE VALIDATION PASSED: {len(REQUIRED)} pages; War Room artifacts present; shadow artifact isolated; page health complete")


if __name__ == "__main__":
    main()
