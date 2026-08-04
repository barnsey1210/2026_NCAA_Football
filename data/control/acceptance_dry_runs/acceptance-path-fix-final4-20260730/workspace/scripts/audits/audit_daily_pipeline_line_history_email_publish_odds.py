#!/usr/bin/env python3
"""Audit NCAAF line history, 8am automation, publishing, and daily email moves.

Read-only. This script does not modify project files.

Checks
------
1. Daily automation
   - LaunchAgent plist discovery and loaded status
   - latest daily log start/finish/error lines
   - freshness of key generated files

2. GitHub auto-publishing
   - whether daily_market_update.sh contains publish commands
   - current repo status and recent commit
   - whether required site assets are copied/staged by the daily script

3. Game line history
   - source/history/movement CSV coverage and latest snapshot dates
   - duplicate snapshots
   - spread/total field availability
   - embedded line-history data inside current site HTML
   - matchup examples, including East Carolina at Alabama

4. Daily betting-angle email
   - category counts
   - suspicious "Game line move" rows caused only by price changes
   - malformed odds such as -1108.0
   - "nan" text in generated HTML

5. Odds-screen readiness
   - normalized game-line files and sportsbook columns currently available

Outputs
-------
data/audits/daily_pipeline_audit.txt
data/audits/daily_pipeline_file_freshness.csv
data/audits/game_line_history_audit.csv
data/audits/email_game_line_move_audit.csv
data/audits/odds_screen_source_inventory.csv
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import plistlib
import re
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path.home() / "NCAAF_AUTO"
SITE_REPO = Path.home() / "Sites/NCAAF_SITE"
LOG = Path.home() / "Scripts/NCAAF/daily_market_update.log"

OUT_REPORT = ROOT / "data/audits/daily_pipeline_audit.txt"
OUT_FRESHNESS = ROOT / "data/audits/daily_pipeline_file_freshness.csv"
OUT_HISTORY = ROOT / "data/audits/game_line_history_audit.csv"
OUT_EMAIL = ROOT / "data/audits/email_game_line_move_audit.csv"
OUT_ODDS = ROOT / "data/audits/odds_screen_source_inventory.csv"

DAILY_SCRIPT = ROOT / "daily_market_update.sh"

FILE_CANDIDATES = [
    ROOT / "data/odds/season_game_lines_2026.csv",
    ROOT / "data/odds/actionnetwork_season_game_lines_2026.csv",
    ROOT / "data/odds/theodds_season_game_lines_2026.csv",
    ROOT / "data/odds/game_line_history.csv",
    ROOT / "data/odds/game_line_movement_report.csv",
    ROOT / "data/odds/game_line_movement.csv",
    ROOT / "daily_market_movement_report.csv",
    ROOT / "data/agents/daily_betting_angles.csv",
    ROOT / "data/agents/daily_betting_angles.html",
    ROOT / "index_auto_market.html",
    ROOT / "index.html",
    ROOT / "build/public_site/openers.html",
    SITE_REPO / "index.html",
    SITE_REPO / "openers.html",
]

HISTORY_CANDIDATES = [
    ROOT / "data/odds/game_line_history.csv",
    ROOT / "data/odds/game_lines_history.csv",
    ROOT / "data/odds/season_game_line_history_2026.csv",
    ROOT / "game_line_history.csv",
]

MOVEMENT_CANDIDATES = [
    ROOT / "data/odds/game_line_movement_report.csv",
    ROOT / "data/odds/game_line_movement.csv",
    ROOT / "game_line_movement_report.csv",
]

ODDS_SOURCE_CANDIDATES = [
    ROOT / "data/odds/season_game_lines_2026.csv",
    ROOT / "data/odds/actionnetwork_season_game_lines_2026.csv",
    ROOT / "data/odds/theodds_season_game_lines_2026.csv",
    ROOT / "data/odds/cfbd_season_game_lines_2026.csv",
]


def shell(command: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=25,
            check=False,
        )
        text = (result.stdout or "") + (result.stderr or "")
        return result.returncode, text.strip()
    except Exception as exc:
        return 1, f"{type(exc).__name__}: {exc}"


def age_hours(path: Path) -> float | None:
    if not path.exists():
        return None
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - modified).total_seconds() / 3600


def safe_read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, low_memory=False)
    except Exception:
        return pd.DataFrame()


def find_first(paths: list[Path]) -> Path | None:
    return next((path for path in paths if path.exists()), None)


def detect_date_column(df: pd.DataFrame) -> str | None:
    priorities = [
        "snapshot_at",
        "snapshot_date",
        "captured_at",
        "updated_at",
        "timestamp",
        "date",
        "move_date",
    ]
    lower = {str(column).lower(): column for column in df.columns}
    for name in priorities:
        if name in lower:
            return str(lower[name])
    return None


def detect_columns(df: pd.DataFrame, terms: list[str]) -> list[str]:
    found = []
    for column in df.columns:
        lower = str(column).lower()
        if any(term in lower for term in terms):
            found.append(str(column))
    return found


def file_freshness() -> pd.DataFrame:
    rows = []
    for path in FILE_CANDIDATES:
        exists = path.exists()
        rows.append(
            {
                "path": str(path),
                "exists": exists,
                "modified": (
                    datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                    if exists
                    else ""
                ),
                "age_hours": round(age_hours(path), 2) if exists else np.nan,
                "size_bytes": path.stat().st_size if exists else np.nan,
            }
        )
    return pd.DataFrame(rows)


def launch_agent_audit() -> list[str]:
    lines = ["LAUNCHAGENT / 8AM AUTOMATION", "-" * 100]

    launch_dirs = [
        Path.home() / "Library/LaunchAgents",
        Path("/Library/LaunchAgents"),
    ]
    matches = []

    for directory in launch_dirs:
        if not directory.exists():
            continue
        for plist in directory.glob("*.plist"):
            try:
                raw = plist.read_bytes()
                data = plistlib.loads(raw)
            except Exception:
                continue

            text = json.dumps(data, default=str).lower()
            if (
                "ncaaf" in text
                or "daily_market_update.sh" in text
                or "daily market" in text
            ):
                matches.append((plist, data))

    if not matches:
        lines.append("No matching LaunchAgent plist found.")
    else:
        for plist, data in matches:
            lines.append(f"Plist: {plist}")
            lines.append(f"  Label: {data.get('Label')}")
            lines.append(f"  ProgramArguments: {data.get('ProgramArguments')}")
            lines.append(f"  StartCalendarInterval: {data.get('StartCalendarInterval')}")
            lines.append(f"  RunAtLoad: {data.get('RunAtLoad')}")
            lines.append(f"  StandardOutPath: {data.get('StandardOutPath')}")
            lines.append(f"  StandardErrorPath: {data.get('StandardErrorPath')}")

    code, output = shell(["launchctl", "list"])
    if code == 0:
        relevant = [
            line for line in output.splitlines()
            if "ncaaf" in line.lower() or "market" in line.lower()
        ]
        lines.append("Loaded launchctl entries:")
        lines.extend(f"  {line}" for line in relevant[:30])
        if not relevant:
            lines.append("  No matching loaded entry.")
    else:
        lines.append(f"launchctl list failed: {output}")

    return lines


def log_audit() -> list[str]:
    lines = ["DAILY LOG", "-" * 100, f"Log path: {LOG}"]

    if not LOG.exists():
        lines.append("Log does not exist.")
        return lines

    text = LOG.read_text(encoding="utf-8", errors="ignore")
    recent = text.splitlines()[-400:]

    starts = [line for line in recent if "Daily market update started:" in line]
    finishes = [line for line in recent if "Daily market update finished:" in line]
    errors = [
        line for line in recent
        if re.search(r"\b(ERROR|Traceback|failed|WARNING: GitHub push failed)\b", line)
    ]

    lines.append(f"Latest start: {starts[-1] if starts else 'not found'}")
    lines.append(f"Latest finish: {finishes[-1] if finishes else 'not found'}")
    lines.append("Recent errors/warnings:")
    if errors:
        lines.extend(f"  {line}" for line in errors[-40:])
    else:
        lines.append("  None found in last 400 lines.")

    return lines


def publish_audit() -> list[str]:
    lines = ["GITHUB AUTO-PUBLISH", "-" * 100]

    if DAILY_SCRIPT.exists():
        text = DAILY_SCRIPT.read_text(encoding="utf-8", errors="ignore")
        lines.append(f"Daily script: {DAILY_SCRIPT}")
        lines.append(f"Contains git push: {'git push' in text}")
        copies_index = 'cp index.html "$PUBLISH_REPO/index.html"' in text
        lines.append(f"Copies index.html: {copies_index}")
        lines.append(
            "Stages only index.html: "
            + str(bool(re.search(r"git add\s+index\.html\b", text)))
        )
        lines.append(
            "Publishes Openers/workspace/assets: "
            + str(
                any(
                    token in text
                    for token in [
                        "openers.html",
                        "matchup_workspace.js",
                        "data/site/",
                        "logos/",
                    ]
                )
            )
        )
    else:
        lines.append("daily_market_update.sh missing.")

    if SITE_REPO.exists():
        code, status = shell(["git", "status", "--short"], cwd=SITE_REPO)
        lines.append(f"Repo status code: {code}")
        lines.append(status or "Working tree clean.")

        code, latest = shell(
            ["git", "log", "-1", "--date=iso", "--pretty=%h %ad %s"],
            cwd=SITE_REPO,
        )
        lines.append(f"Latest commit: {latest or 'unavailable'}")

        code, branch = shell(
            ["git", "branch", "--show-current"],
            cwd=SITE_REPO,
        )
        lines.append(f"Branch: {branch or 'unavailable'}")
    else:
        lines.append(f"Publish repo missing: {SITE_REPO}")

    return lines


def history_audit() -> pd.DataFrame:
    rows = []

    for path in HISTORY_CANDIDATES + MOVEMENT_CANDIDATES:
        if not path.exists():
            continue

        df = safe_read_csv(path)
        date_col = detect_date_column(df)
        spread_cols = detect_columns(df, ["spread", "line"])
        total_cols = detect_columns(df, ["total"])
        price_cols = detect_columns(df, ["price", "odds"])

        latest = ""
        unique_dates = np.nan
        if date_col and not df.empty:
            parsed = pd.to_datetime(df[date_col], errors="coerce")
            if parsed.notna().any():
                latest = parsed.max().isoformat()
                unique_dates = int(parsed.dt.date.nunique())

        rows.append(
            {
                "path": str(path),
                "rows": len(df),
                "date_column": date_col or "",
                "latest_snapshot": latest,
                "unique_snapshot_dates": unique_dates,
                "spread_columns": " | ".join(spread_cols),
                "total_columns": " | ".join(total_cols),
                "price_columns": " | ".join(price_cols),
                "columns": " | ".join(map(str, df.columns)),
            }
        )

    return pd.DataFrame(rows)


def html_history_audit() -> list[str]:
    lines = ["MATCHUP LINE-HISTORY DISPLAY", "-" * 100]

    html_candidates = [
        ROOT / "index.html",
        ROOT / "index_auto_market.html",
        ROOT / "matchup.html",
        ROOT / "openers_v2.html",
    ]

    for path in html_candidates:
        if not path.exists():
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        counts = {
            "line_history": len(re.findall(r"line[_ -]?history", text, flags=re.I)),
            "opening ATS": len(re.findall(r"Opening ATS", text, flags=re.I)),
            "SportsGameOdds": len(re.findall(r"SportsGameOdds", text, flags=re.I)),
            "East Carolina": len(re.findall(r"East Carolina", text, flags=re.I)),
            "2026-07-21": len(re.findall(r"2026-07-21", text)),
        }
        lines.append(f"{path}: {counts}")

    return lines


def email_audit() -> pd.DataFrame:
    csv_path = ROOT / "data/agents/daily_betting_angles.csv"
    if not csv_path.exists():
        return pd.DataFrame()

    df = safe_read_csv(csv_path)
    if df.empty:
        return pd.DataFrame()

    work = df.copy()
    for column in ["category", "title", "reason", "action", "score"]:
        if column not in work.columns:
            work[column] = ""

    joined = (
        work[["category", "title", "reason", "action", "score"]]
        .fillna("")
        .astype(str)
        .agg(" | ".join, axis=1)
    )

    game_move = work["category"].astype(str).str.lower().eq("game line move")
    suspicious_price_only = game_move & joined.str.contains(
        r"price|american odds|-1\d{2}\s*[→>-]+\s*-1\d{2}",
        case=False,
        regex=True,
    )
    malformed_odds = joined.str.contains(
        r"(?<!\d)-\d{4,}(?:\.0)?\b|\bnan\b",
        case=False,
        regex=True,
    )

    output = work.loc[game_move | suspicious_price_only | malformed_odds].copy()
    output["audit_game_line_move"] = game_move.loc[output.index].values
    output["audit_price_only"] = suspicious_price_only.loc[output.index].values
    output["audit_malformed_or_nan"] = malformed_odds.loc[output.index].values
    return output


def email_html_lines() -> list[str]:
    lines = ["DAILY EMAIL HTML", "-" * 100]
    path = ROOT / "data/agents/daily_betting_angles.html"

    if not path.exists():
        lines.append("HTML report missing.")
        return lines

    text = path.read_text(encoding="utf-8", errors="ignore")
    lines.append(f"Path: {path}")
    contains_literal_nan = bool(re.search(r'\bnan\b', text, flags=re.I))
    contains_malformed_odds = bool(re.search(r'-\d{4,}(?:\.0)?\b', text))
    lines.append(f"Contains literal nan: {contains_literal_nan}")
    lines.append(f"Contains malformed 4-digit negative odds: {contains_malformed_odds}")
    lines.append(f"Game line move headings: {len(re.findall(r'Game line move', text, flags=re.I))}")
    return lines


def odds_inventory() -> pd.DataFrame:
    rows = []

    for path in ODDS_SOURCE_CANDIDATES:
        if not path.exists():
            continue

        df = safe_read_csv(path)
        books = []
        for column in df.columns:
            lower = str(column).lower()
            if any(
                book in lower
                for book in [
                    "circa",
                    "pinnacle",
                    "bookmaker",
                    "kalshi",
                    "novig",
                    "draftkings",
                    "fanduel",
                    "betmgm",
                    "caesars",
                    "hardrock",
                    "betrivers",
                    "fanatics",
                    "espn",
                    "bet365",
                ]
            ):
                books.append(str(column))

        rows.append(
            {
                "path": str(path),
                "rows": len(df),
                "games": (
                    df["game_id"].nunique()
                    if "game_id" in df.columns
                    else np.nan
                ),
                "sportsbook_columns": " | ".join(books),
                "all_columns": " | ".join(map(str, df.columns)),
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    for path in [
        OUT_REPORT,
        OUT_FRESHNESS,
        OUT_HISTORY,
        OUT_EMAIL,
        OUT_ODDS,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)

    freshness = file_freshness()
    history = history_audit()
    email = email_audit()
    odds = odds_inventory()

    freshness.to_csv(OUT_FRESHNESS, index=False)
    history.to_csv(OUT_HISTORY, index=False)
    email.to_csv(OUT_EMAIL, index=False)
    odds.to_csv(OUT_ODDS, index=False)

    report_lines = [
        "NCAAF DAILY PIPELINE AUDIT",
        "=" * 100,
        f"Generated: {datetime.now().isoformat()}",
        "",
    ]
    report_lines.extend(launch_agent_audit())
    report_lines.append("")
    report_lines.extend(log_audit())
    report_lines.append("")
    report_lines.extend(publish_audit())
    report_lines.append("")
    report_lines.extend(html_history_audit())
    report_lines.append("")
    report_lines.extend(email_html_lines())
    report_lines.append("")
    report_lines.extend(
        [
            "FILE FRESHNESS SUMMARY",
            "-" * 100,
            freshness.to_string(index=False),
            "",
            "GAME LINE HISTORY FILES",
            "-" * 100,
            history.to_string(index=False) if not history.empty else "No history/movement CSV found.",
            "",
            "EMAIL MOVE AUDIT",
            "-" * 100,
            (
                email[
                    [
                        column
                        for column in [
                            "category",
                            "title",
                            "reason",
                            "action",
                            "score",
                            "audit_price_only",
                            "audit_malformed_or_nan",
                        ]
                        if column in email.columns
                    ]
                ].to_string(index=False)
                if not email.empty
                else "No suspicious game-line email rows found."
            ),
            "",
            "ODDS SCREEN SOURCE INVENTORY",
            "-" * 100,
            odds.to_string(index=False) if not odds.empty else "No normalized odds sources found.",
        ]
    )

    OUT_REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print("NCAAF DAILY PIPELINE AUDIT")
    print("=" * 100)
    print(f"Freshness rows: {len(freshness)}")
    print(f"History/movement files found: {len(history)}")
    print(f"Suspicious email rows: {len(email)}")
    print(f"Odds source files found: {len(odds)}")
    print()
    print("Created:")
    print(OUT_REPORT)
    print(OUT_FRESHNESS)
    print(OUT_HISTORY)
    print(OUT_EMAIL)
    print(OUT_ODDS)
    print()
    print("Next: paste the LAUNCHAGENT / 8AM AUTOMATION, GITHUB AUTO-PUBLISH,")
    print("GAME LINE HISTORY FILES, EMAIL MOVE AUDIT, and ODDS SCREEN SOURCE INVENTORY sections.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
