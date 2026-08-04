#!/usr/bin/env python3
"""Audit the matchup line-history pipeline.

Read-only. This script does not modify project files.

It checks:
- freshness of game_line_history.csv
- freshness and contents of data/site/matchups_view.json
- whether East Carolina at Alabama has July 28 history in the source payload
- whether matchup_workspace.js renders history newest-to-oldest
- which project scripts reference game_line_history.csv or matchups_view.json
- whether daily_market_update.sh calls those scripts before publishing
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import re
import sys

import pandas as pd


ROOT = Path.home() / "NCAAF_AUTO"
HISTORY = ROOT / "data/odds/game_line_history.csv"
PAYLOAD = ROOT / "data/site/matchups_view.json"
WORKSPACE = ROOT / "matchup_workspace.js"
DAILY = ROOT / "daily_market_update.sh"
OUT = ROOT / "data/audits/matchup_line_history_pipeline_audit.txt"


def modified(path: Path) -> str:
    if not path.exists():
        return "missing"
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat()


def latest_history_date() -> str:
    if not HISTORY.exists():
        return "missing"
    df = pd.read_csv(HISTORY, low_memory=False)
    if "snapshot_date" not in df.columns:
        return "snapshot_date column missing"
    values = pd.to_datetime(df["snapshot_date"], errors="coerce")
    return values.max().isoformat() if values.notna().any() else "unparseable"


def extract_history_rows(game: dict) -> list[dict]:
    candidates = []

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {
                    "line_history",
                    "history",
                    "market_history",
                    "game_line_history",
                } and isinstance(child, list):
                    candidates.extend(x for x in child if isinstance(x, dict))
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(game)
    return candidates


def date_values(rows: list[dict]) -> list[str]:
    values = []
    keys = [
        "snapshot_date",
        "snapshot_ts",
        "date",
        "captured_at",
        "updated_at",
        "timestamp",
    ]
    for row in rows:
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                values.append(str(value))
                break
    return values


def find_game(games: list[dict], away: str, home: str) -> dict | None:
    for game in games:
        game_meta = game.get("game", {})
        if (
            str(game_meta.get("away_team", "")).casefold() == away.casefold()
            and str(game_meta.get("home_team", "")).casefold() == home.casefold()
        ):
            return game
    return None


def script_references() -> list[str]:
    results = []
    search_roots = [
        ROOT / "scripts",
        ROOT,
    ]

    seen = set()
    for base in search_roots:
        if not base.exists():
            continue
        paths = list(base.rglob("*.py")) + list(base.rglob("*.sh"))
        for path in paths:
            if path in seen:
                continue
            seen.add(path)
            if "backups" in path.parts or ".git" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if (
                "game_line_history.csv" in text
                or "matchups_view.json" in text
                or "line_history" in text
            ):
                hits = []
                for line_number, line in enumerate(text.splitlines(), start=1):
                    if (
                        "game_line_history.csv" in line
                        or "matchups_view.json" in line
                        or "line_history" in line
                    ):
                        hits.append(f"{line_number}: {line.strip()}")
                results.append(
                    f"{path}\n  " + "\n  ".join(hits[:20])
                )
    return results


def main() -> None:
    lines = [
        "MATCHUP LINE-HISTORY PIPELINE AUDIT",
        "=" * 100,
        f"Generated: {datetime.now().isoformat()}",
        "",
        "SOURCE FRESHNESS",
        "-" * 100,
        f"History CSV: {HISTORY}",
        f"History modified: {modified(HISTORY)}",
        f"History latest snapshot: {latest_history_date()}",
        f"Payload JSON: {PAYLOAD}",
        f"Payload modified: {modified(PAYLOAD)}",
        f"Workspace JS: {WORKSPACE}",
        f"Workspace modified: {modified(WORKSPACE)}",
        "",
    ]

    payload_games = []
    if PAYLOAD.exists():
        data = json.loads(PAYLOAD.read_text(encoding="utf-8"))
        payload_games = data.get("games", [])
        lines.extend(
            [
                "PAYLOAD SUMMARY",
                "-" * 100,
                f"Games in payload: {len(payload_games)}",
            ]
        )

        target = find_game(
            payload_games,
            "East Carolina",
            "Alabama",
        )
        if target is None:
            lines.append("East Carolina at Alabama: not found")
        else:
            rows = extract_history_rows(target)
            dates = date_values(rows)
            parsed = pd.to_datetime(pd.Series(dates), errors="coerce")
            lines.append(f"East Carolina at Alabama history rows: {len(rows)}")
            lines.append(
                "East Carolina at Alabama latest history date: "
                + (
                    parsed.max().isoformat()
                    if parsed.notna().any()
                    else "no parseable date"
                )
            )
            lines.append(
                "East Carolina at Alabama unique history dates: "
                + str(parsed.dt.date.nunique() if parsed.notna().any() else 0)
            )
            lines.append(
                "Contains 2026-07-28: "
                + str(any("2026-07-28" in value for value in dates))
            )

        all_dates = []
        games_with_history = 0
        for game in payload_games:
            rows = extract_history_rows(game)
            if rows:
                games_with_history += 1
                all_dates.extend(date_values(rows))

        parsed_all = pd.to_datetime(
            pd.Series(all_dates),
            errors="coerce",
        )
        lines.append(f"Games with history rows: {games_with_history}")
        lines.append(
            "Latest history date anywhere in payload: "
            + (
                parsed_all.max().isoformat()
                if parsed_all.notna().any()
                else "no parseable date"
            )
        )
    else:
        lines.extend(
            [
                "PAYLOAD SUMMARY",
                "-" * 100,
                "matchups_view.json is missing",
            ]
        )

    lines.extend(["", "WORKSPACE RENDER LOGIC", "-" * 100])
    if WORKSPACE.exists():
        js = WORKSPACE.read_text(encoding="utf-8", errors="ignore")
        lines.append(
            "Newest-to-oldest renderer present: "
            + str("latest=[...dedup].reverse()" in re.sub(r"\s+", "", js))
        )
        lines.append(
            "Opening spread label present: "
            + str("Open spread:" in js)
        )
        lines.append(
            "Opening total label present: "
            + str("Open total:" in js)
        )
    else:
        lines.append("matchup_workspace.js is missing")

    lines.extend(["", "DAILY PIPELINE ORDER", "-" * 100])
    if DAILY.exists():
        text = DAILY.read_text(encoding="utf-8", errors="ignore")
        references = [
            "append_game_line_history.py",
            "build_game_line_movement_report.py",
            "build_matchups_view.py",
            "matchups_view.json",
            "build_site_from_workbook_safe_with_movement.py",
            "git push",
        ]
        for name in references:
            lines.append(f"{name}: position {text.find(name)}")
    else:
        lines.append("daily_market_update.sh is missing")

    lines.extend(["", "PROJECT SCRIPT REFERENCES", "-" * 100])
    refs = script_references()
    if refs:
        lines.extend(refs)
    else:
        lines.append("No relevant script references found")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("MATCHUP LINE-HISTORY PIPELINE AUDIT")
    print("=" * 100)
    print(f"Wrote: {OUT}")
    print()
    print("Paste the full audit output with:")
    print(f"cat {OUT}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
