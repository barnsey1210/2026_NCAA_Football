#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
SOURCE_PAGE = ROOT / "schedule_v2.html"
ENRICHMENT_BUILDER = ROOT / "scripts/site/build_schedule_live_enrichment.py"
ENRICHMENT = ROOT / "data/site/schedule_live_enrichment.json"
PUBLIC_ROOT = ROOT / "build/public_site"
PUBLIC_PAGE = PUBLIC_ROOT / "schedule.html"
PUBLIC_DATA = PUBLIC_ROOT / "data/site/schedule_live_enrichment.json"

REQUIRED_PAGE_TOKENS = [
    "Schedule & Results",
    "Saturday Rules & Validation",
    "Date / Time",
    "Spread Impact",
    "Total Impact",
    "Next Week",
    "Data Status",
    "scheduleImpactPairV11",
    "scheduleNextWeekV11",
    "scheduleHeaderTipV12",
    "scheduleNativeDetail",
]

FORBIDDEN_PAGE_TOKENS = [
    "Historical Saturday Shadow Replay",
    "Spread CLV",
    "Total CLV",
    "matchup_workspace.js",
    "MARKET_SHADOW_LAYER_START",
    "SCHEDULE_LIVE_SCOREBOARD_START",
]

def audit_source() -> None:
    if not SOURCE_PAGE.exists():
        raise RuntimeError(f"Missing canonical Schedule source: {SOURCE_PAGE}")
    text = SOURCE_PAGE.read_text(encoding="utf-8", errors="ignore")
    for token in REQUIRED_PAGE_TOKENS:
        if token not in text:
            raise RuntimeError(f"Canonical Schedule page missing required token: {token}")
    for token in FORBIDDEN_PAGE_TOKENS:
        if token in text:
            raise RuntimeError(f"Canonical Schedule page contains forbidden legacy token: {token}")

def build_enrichment() -> None:
    subprocess.run([sys.executable, str(ENRICHMENT_BUILDER)], check=True)
    kickoff_builder = ROOT / "scripts/site/enrich_schedule_kickoff_times.py"
    subprocess.run([sys.executable, str(kickoff_builder)], check=True)
    fbs_guard = ROOT / "scripts/site/enforce_fbs_shadow_exclusions.py"
    subprocess.run([sys.executable, str(fbs_guard)], check=True)
    if not ENRICHMENT.exists():
        raise RuntimeError(f"Schedule enrichment was not written: {ENRICHMENT}")
    data = json.loads(ENRICHMENT.read_text())
    if not isinstance(data.get("games"), list) or not data["games"]:
        raise RuntimeError("Schedule enrichment contains no games")

def copy_if_distinct(source: Path, destination: Path) -> bool:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        if destination.exists() and source.samefile(destination):
            print(f"already shared/synced: {source} == {destination}")
            return False
    except OSError:
        pass
    shutil.copy2(source, destination)
    return True

def publicize_schedule_html(source_text: str) -> str:
    replacements = {
        "ratings_v2.html": "ratings.html",
        "openers_v2.html": "openers.html",
        "matchups_v2.html": "matchups.html",
        "schedule_v2.html": "schedule.html",
        "futures_v2.html": "futures.html",
        "conferences_v2.html": "conferences.html",
        "simulations_v2.html": "simulations.html",
        "betting_v2.html": "betting.html",
    }
    out = source_text
    for old, new in replacements.items():
        out = out.replace(old, new)

    # Catch every remaining local prototype destination, not only the
    # currently known navigation pages. The public validator rejects any
    # occurrence of "_v2.html" anywhere in the document.
    out = re.sub(
        r'([A-Za-z0-9_-]+)_v2\.html',
        r'\1.html',
        out,
    )

    # Validation expects every top-nav item, including the active page,
    # to be represented by a canonical public href.
    out = out.replace(
        '<a class="active">Schedule</a>',
        '<a class="active" href="schedule.html">Schedule</a>',
    )
    return out

def sync_public() -> None:
    PUBLIC_PAGE.parent.mkdir(parents=True, exist_ok=True)
    public_html = publicize_schedule_html(
        SOURCE_PAGE.read_text(encoding="utf-8", errors="ignore")
    )
    PUBLIC_PAGE.write_text(public_html, encoding="utf-8")
    copied_data = copy_if_distinct(ENRICHMENT, PUBLIC_DATA)
    print(f"synced/publicized artifact: {SOURCE_PAGE.name} -> {PUBLIC_PAGE}")
    if copied_data:
        print(f"synced public artifact: {ENRICHMENT.relative_to(ROOT)} -> {PUBLIC_DATA}")

def audit_public() -> None:
    public_text = PUBLIC_PAGE.read_text(encoding="utf-8", errors="ignore")
    if "_v2.html" in public_text:
        matches = sorted(set(re.findall(r'[A-Za-z0-9_-]+_v2\.html', public_text)))
        raise RuntimeError(
            "Prototype link leaked into public Schedule page: "
            + ", ".join(matches or ["unknown _v2.html token"])
        )

    required_nav = (
        'href="ratings.html"',
        'href="openers.html"',
        'href="matchups.html"',
        'href="schedule.html"',
        'href="futures.html"',
        'href="conferences.html"',
        'href="simulations.html"',
        'href="betting.html"',
    )
    for token in required_nav:
        if token not in public_text:
            raise RuntimeError(f"Public Schedule navigation missing: {token}")

    if ENRICHMENT.read_bytes() != PUBLIC_DATA.read_bytes():
        raise RuntimeError("Public Schedule enrichment does not match canonical data")

def main() -> None:
    audit_source()
    build_enrichment()
    sync_public()
    audit_public()
    print("PASS: persistent Schedule build")

if __name__ == "__main__":
    main()
