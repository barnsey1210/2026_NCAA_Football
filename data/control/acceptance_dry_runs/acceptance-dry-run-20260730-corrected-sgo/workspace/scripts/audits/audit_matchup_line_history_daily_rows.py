#!/usr/bin/env python3
"""Audit why matchup line history omits unchanged daily snapshots.

Read-only. No files are modified.

The audit compares:
- every stored snapshot date for selected games
- dates surviving the line-history asset
- dates likely surviving renderer-side deduplication
- dedupe/filter logic in inject_matchup_line_history.py and matchup_workspace.js
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys

import pandas as pd


ROOT = Path.home() / "NCAAF_AUTO"
HISTORY = ROOT / "data/odds/game_line_history.csv"
CLEAN = ROOT / "data/history/matchup_line_history_clean.csv"
ASSET = ROOT / "data/site/matchup_line_history.json"
INJECTOR = ROOT / "scripts/site/inject_matchup_line_history.py"
WORKSPACE = ROOT / "matchup_workspace.js"
OUT = ROOT / "data/audits/matchup_line_history_daily_rows_audit.txt"

TARGETS = {
    "g24": "East Carolina at Alabama",
    "g88": "Sam Houston at Troy",
    "g25": "Maine at Appalachian State",
}


def dates_from_csv(path: Path, game_id: str) -> list[str]:
    if not path.exists():
        return []
    df = pd.read_csv(path, low_memory=False)
    if "game_id" not in df.columns:
        return []
    date_col = "snapshot_date" if "snapshot_date" in df.columns else None
    if not date_col:
        return []
    subset = df[df["game_id"].astype(str).eq(game_id)].copy()
    values = pd.to_datetime(subset[date_col], errors="coerce")
    return sorted({value.date().isoformat() for value in values.dropna()})


def asset_rows(game_id: str) -> list[dict]:
    if not ASSET.exists():
        return []
    data = json.loads(ASSET.read_text(encoding="utf-8"))
    rows = data.get(game_id, []) if isinstance(data, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def asset_dates(game_id: str) -> list[str]:
    dates = []
    for row in asset_rows(game_id):
        value = row.get("snapshot_date")
        if value:
            dates.append(str(value)[:10])
    return sorted(set(dates))


def compressed_by_values(game_id: str) -> list[str]:
    """Simulate common renderer compression: retain rows only when values change."""
    rows = asset_rows(game_id)
    rows = sorted(rows, key=lambda row: str(row.get("snapshot_date") or ""))
    retained = []
    previous = None
    for row in rows:
        signature = (
            row.get("market_spread_home"),
            row.get("market_spread_price"),
            row.get("market_spread_book"),
            row.get("market_total"),
            row.get("market_total_over_price"),
            row.get("market_total_under_price"),
            row.get("market_total_book"),
            row.get("source"),
        )
        if signature != previous:
            retained.append(str(row.get("snapshot_date") or "")[:10])
            previous = signature
    return retained


def source_hits(path: Path) -> list[str]:
    lines = []
    if not path.exists():
        return [f"Missing: {path}"]

    text = path.read_text(encoding="utf-8", errors="ignore")
    patterns = [
        r"dedup",
        r"reverse\(",
        r"filter\(",
        r"snapshot_date",
        r"market_spread_home",
        r"market_total",
        r"signature",
        r"seen",
        r"previous",
        r"unchanged",
    ]

    source_lines = text.splitlines()
    matched_numbers = set()

    for number, line in enumerate(source_lines, start=1):
        if any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in patterns):
            for nearby in range(max(1, number - 3), min(len(source_lines), number + 3) + 1):
                matched_numbers.add(nearby)

    for number in sorted(matched_numbers):
        lines.append(f"{number}: {source_lines[number - 1]}")
    return lines[:500]


def main() -> None:
    report = [
        "MATCHUP LINE-HISTORY DAILY ROW AUDIT",
        "=" * 100,
        "",
        "SUMMARY BY GAME",
        "-" * 100,
    ]

    for game_id, label in TARGETS.items():
        raw_dates = dates_from_csv(HISTORY, game_id)
        clean_dates = dates_from_csv(CLEAN, game_id)
        json_dates = asset_dates(game_id)
        simulated = compressed_by_values(game_id)

        report.extend(
            [
                f"{game_id} — {label}",
                f"  Raw history unique dates: {len(raw_dates)}",
                f"  Clean history unique dates: {len(clean_dates)}",
                f"  Asset unique dates: {len(json_dates)}",
                f"  Simulated change-only dates: {len(simulated)}",
                f"  Latest raw date: {raw_dates[-1] if raw_dates else 'none'}",
                f"  Latest asset date: {json_dates[-1] if json_dates else 'none'}",
                f"  Raw dates missing from asset: {sorted(set(raw_dates) - set(json_dates))}",
                f"  Dates omitted by value compression: {sorted(set(json_dates) - set(simulated))}",
                f"  Simulated displayed dates newest first: {list(reversed(simulated[-20:]))}",
                "",
            ]
        )

    report.extend(
        [
            "INJECTOR DEDUPE/FILTER LOGIC",
            "-" * 100,
            f"File: {INJECTOR}",
            *source_hits(INJECTOR),
            "",
            "WORKSPACE DEDUPE/FILTER LOGIC",
            "-" * 100,
            f"File: {WORKSPACE}",
            *source_hits(WORKSPACE),
        ]
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("MATCHUP LINE-HISTORY DAILY ROW AUDIT")
    print("=" * 100)
    print(f"Wrote: {OUT}")
    print()
    for game_id, label in TARGETS.items():
        raw_dates = dates_from_csv(HISTORY, game_id)
        json_dates = asset_dates(game_id)
        simulated = compressed_by_values(game_id)
        print(
            f"{game_id} {label}: raw={len(raw_dates)}, "
            f"asset={len(json_dates)}, change-only={len(simulated)}"
        )
    print()
    print(f"Run: cat {OUT}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
