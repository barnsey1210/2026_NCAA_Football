#!/usr/bin/env python3
"""Validate the canonical public V2 bundle, including page-health integration."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXPECTED_HEALTH = {
    "dashboard": "index.html", "ratings": "ratings.html", "openers": "openers.html",
    "matchups": "matchups.html", "odds": "odds.html", "schedule": "schedule.html",
    "futures": "futures.html", "conferences": "conferences.html", "playoff": "playoff.html",
    "simulations": "simulations.html", "betting": "betting.html",
}
VALID_STATUS = {"green", "yellow", "red", "gray"}
MODERN = list(EXPECTED_HEALTH.values()) + ["team.html", "coaches.html", "sim_lab.html"]
REQUIRED = MODERN + ["war-room.html"]
SHARED_SHELL_PAGES = {
    "index.html", "ratings.html", "matchups.html", "conferences.html", "futures.html",
    "simulations.html", "sim_lab.html", "betting.html", "odds.html", "openers.html", "war-room.html",
    "schedule.html", "coaches.html", "playoff.html",
}
NAV_ORDER = (
    "index.html", "ratings.html", "matchups.html", "openers.html", "war-room.html",
    "odds.html", "schedule.html", "futures.html", "conferences.html", "coaches.html",
    "playoff.html", "sim_lab.html", "betting.html",
)
ACTIVE_PAGE_ALIASES = {"simulations.html": "sim_lab.html"}
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
                'id="acquireBtn"',
                "RELOAD MARKET",
                "REFRESH MARKET",
                'id="ratingsBtn"',
                'id="postgameBtn"',
                'id="connectOperatorBtn"',
                "/war-room/bootstrap",
                "/war-room/live/version",
                "/war-room/live/health",
                "/war-room/live/market-matrix",
                "requestOperation('market'",
                "CONTROL_WINDOW.postMessage",
                "pollPublishedVersion",
            ):
                if marker not in text:
                    errors.append(f"War Room terminal marker missing: {marker}")
            if "method:'POST'" in text or "method: 'POST'" in text:
                errors.append("War Room public artifact must not issue operator action POSTs")
        elif name in MODERN:
            text = path.read_text(errors="ignore")
            if name != "index.html":
                for marker in ('WAR<span>ROOM</span>', 'class="nav war-room-nav"', 'Data Healthy'):
                    if marker not in text:
                        errors.append(f"shared War Room shell missing from {name}: {marker}")
            if 'href="dashboard.html"' in text or '>Dashboard</a>' in text:
                errors.append(f"retired Dashboard navigation leaked: {name}")

            if name == "schedule.html":
                for marker in (
                    "https://control.barnseywr.com/war-room/live/schedule",
                    "refreshLiveSchedule",
                    "setInterval(refreshLiveSchedule,7500)",
                    "credentials:'omit'",
                ):
                    if marker not in text:
                        errors.append(f"Schedule live-score shell marker missing: {marker}")

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
                    and 'href="war-room.html"' in text
                    and 'href="openers.html"' in text
                    and 'href="matchups.html"' in text
                )
                if not has_shared_nav:
                    errors.append(f"top navigation missing: {name}")
                if "_v2.html" in text:
                    errors.append(f"prototype link leaked: {name}")
                if '<link rel="stylesheet" href="page_health.css">' not in text or '<script defer src="page_health.js"></script>' not in text:
                    errors.append(f"page health loader missing: {name}")

        if name in SHARED_SHELL_PAGES:
            text = path.read_text(errors="ignore")
            if text.count('class="war-room-global"') != 1:
                errors.append(f"shared shell owner count is not one: {name}")
            for marker in ('class="nav war-room-nav"', 'class="war-room-meta"', 'Data Healthy'):
                if marker not in text:
                    errors.append(f"canonical shared shell marker missing from {name}: {marker}")
            active_href = ACTIVE_PAGE_ALIASES.get(name, name)
            if f'href="{active_href}" class="active"' not in text:
                errors.append(f"shared shell active page is incorrect: {name}")
            nav_start = text.find('class="nav war-room-nav"')
            nav_end = text.find("</nav>", nav_start)
            nav_text = text[nav_start:nav_end] if nav_start >= 0 and nav_end >= 0 else ""
            positions = [nav_text.find(f'href="{href}"') for href in NAV_ORDER]
            if any(position < 0 for position in positions) or positions != sorted(positions):
                errors.append(f"shared shell navigation order is incorrect: {name}")
            if text.count("<header") != 1:
                errors.append(f"public page retains a competing semantic header: {name}")
            for legacy in ('>NCAAF</', '>NCAAF Edge</', 'class="site-nav"'):
                if legacy in text:
                    errors.append(f"legacy header marker remains in {name}: {legacy}")

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

    odds_page = out / "odds.html"
    odds_payload = out / "data" / "site" / "odds_screen_v2.json"
    expected_books = [
        "Pinnacle", "Novig", "ProphetX", "Kalshi", "DraftKings",
        "FanDuel", "BetMGM", "Caesars", "BetRivers", "Hard Rock Bet",
    ]
    if odds_page.is_file():
        odds_text = odds_page.read_text(errors="ignore")
        if "data/site/odds_screen_v2.json" not in odds_text:
            errors.append("Odds page does not reference the canonical production.2 payload")
        for marker in ("GAME_BOOKS=[...(payload.books||[])]", "--odds-book-count", "overflow-x:auto", "payload.built_at"):
            if marker not in odds_text:
                errors.append(f"Odds dynamic/responsive venue marker missing: {marker}")
        if "const BOOKS=['DraftKings','FanDuel','BetMGM','Caesars']" in odds_text:
            errors.append("Odds page retains the obsolete hardcoded four-book game path")
    if odds_payload.is_file():
        try:
            odds_data = json.loads(odds_payload.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"Odds payload malformed: {exc}")
        else:
            if odds_data.get("schema_version") != "odds_screen_v2.production.2":
                errors.append("Odds payload is not production.2")
            books = odds_data.get("sportsbooks") or odds_data.get("books") or []
            if books != expected_books:
                errors.append(f"Odds payload 10-book contract mismatch: {books!r}")

    openers = out / "openers.html"
    if openers.is_file():
        openers_text = openers.read_text(errors="ignore")
        for marker in (
            "data/site/current_market_contract.json",
            "matchup_workspace.js",
            "cache:'no-store'",
        ):
            if marker not in openers_text:
                errors.append(f"Openers canonical market/history marker missing: {marker}")
        for script_id in ('id="postgame-shadow-ui"', 'id="opener-week-js"'):
            if openers_text.count(script_id) != 1:
                errors.append(f"Openers compatibility script owner count is not one: {script_id}")
    matchup_workspace = out / "matchup_workspace.js"
    if not matchup_workspace.is_file() or "data/site/matchup_line_history.json" not in matchup_workspace.read_text(errors="ignore"):
        errors.append("Openers matchup workspace lacks the canonical line-history payload reference")
    elif openers.is_file():
        workspace_text = matchup_workspace.read_text(errors="ignore")
        for marker in (
            "Opening ATS line:", "Opening O/U:", "Date / Time", "Spread move", "Total move",
        ):
            if marker not in workspace_text:
                errors.append(f"Openers shared drawer history marker missing: {marker}")
        if not re.search(r'matchup_workspace\.js\?v=\d{8}T\d{6}Z', openers.read_text(errors="ignore")):
            errors.append("Openers shared drawer bundle is not build-version cache busted")
        history_path = out / "data" / "site" / "matchup_line_history.json"
        try:
            history_data = json.loads(history_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Openers line-history contract malformed: {exc}")
        else:
            multi_snapshot_games = sum(
                isinstance(rows, list) and len(rows) > 1 for rows in history_data.values()
            ) if isinstance(history_data, dict) else 0
            if multi_snapshot_games == 0:
                errors.append("Openers line-history contract has no multi-snapshot games")

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
        if filename == "war_room_health.json":
            if not isinstance(payload.get("fast_market_refresh"), dict):
                errors.append("War Room health fast_market_refresh must be an object")

            projection_health = payload.get("projection_health")
            if not isinstance(projection_health, dict):
                errors.append("War Room projection_health must be an object")
            else:
                if projection_health.get("scope") != "LATEST_FAST_BOARD_FBS_VS_FBS_ONLY":
                    errors.append("War Room projection_health scope must be FBS-vs-FBS latest board")

                by_week = projection_health.get("by_week")
                if not isinstance(by_week, dict) or not by_week:
                    errors.append("War Room projection_health.by_week must be a nonempty object")
                else:
                    for week, health in by_week.items():
                        if not isinstance(health, dict):
                            errors.append(f"War Room Week {week} projection health must be an object")
                            continue
                        for market in ("spread", "total", "shadow"):
                            state = health.get(market)
                            if not isinstance(state, dict):
                                errors.append(
                                    f"War Room Week {week} projection health missing {market}"
                                )
                            elif not isinstance(state.get("displayed_games"), int):
                                errors.append(
                                    f"War Room Week {week} {market} health missing displayed_games"
                                )


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
            'rank_tone',
            'rank-good',
            'rank-mid',
            'rank-low',
        ):
            if marker not in conference_text:
                errors.append(f"Conference Logo Schedule marker missing: {marker}")
        if "Conference Workspace" in conference_text:
            errors.append("legacy Conference Workspace shell detected")
        if "matchup.html?game=" in conference_text or "matchup.html?game_id=" in conference_text:
            errors.append("legacy Conference matchup route detected")
        try:
            payload_text = conference_text.split('<script id="conference-data" type="application/json">', 1)[1].split("</script>", 1)[0]
            conference_data = json.loads(payload_text)
        except (IndexError, json.JSONDecodeError) as exc:
            errors.append(f"Conference embedded payload malformed: {exc}")
        else:
            modeled = [
                game for conference in conference_data.get("conferences", [])
                for row in conference.get("rows", [])
                for game in row.get("cells", [])
                if game.get("model_margin") is not None
            ]
            if modeled and not any(game.get("win_probability") is not None for game in modeled):
                errors.append("Conference modeled games lack presentation win probabilities")

    ratings = out / "ratings.html"
    if ratings.is_file():
        ratings_text = ratings.read_text(errors="ignore")
        for marker in ("Canonical Composite", "SP+ 25%", "FPI 25%", "TeamRankings 25%", "Sagarin 25%"):
            if marker not in ratings_text:
                errors.append(f"Ratings canonical composite marker missing: {marker}")
        if "BP 25%" in ratings_text:
            errors.append("Brad Powers leaked into the production Ratings composite badge")

    matchups = out / "matchups.html"
    if matchups.is_file() and "Loading production model" in matchups.read_text(errors="ignore"):
        errors.append("Matchups retains the stale production-model loading badge")

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
