#!/usr/bin/env python3
"""Audit the current Openers RP implementation and available historical 1H data.

This script is intentionally read-only. It does not modify HTML, shell scripts,
CSVs, or databases.

It answers two questions:
1. What returning-production code currently exists in openers_v2.html?
2. Which local files can support a 2024-2025 first-half ATS backtest of the
   validated full-game returning-production signals?
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sqlite3
import sys
from typing import Iterable

import pandas as pd


ROOT = Path.home() / "NCAAF_AUTO"

OPENERS_CANDIDATES = [
    ROOT / "openers_v2.html",
    ROOT / "openers.html",
    ROOT / "build/public_site/openers.html",
    Path.home() / "Sites/NCAAF_SITE/openers.html",
]

SEARCH_ROOTS = [
    ROOT / "SGO",
    ROOT / "data",
    ROOT / "scripts",
    ROOT,
]

REPORT = ROOT / "data/audits/openers_rp_and_1h_data_audit.txt"
CSV_REPORT = ROOT / "data/audits/one_half_candidate_files_audit.csv"


KEYWORDS = (
    "1h",
    "first_half",
    "first half",
    "halves",
    "half_odds",
    "1st_half",
)


def text_context(text: str, pattern: str, radius: int = 500) -> list[str]:
    results: list[str] = []
    for match in re.finditer(pattern, text, flags=re.I):
        start = max(0, match.start() - radius)
        end = min(len(text), match.end() + radius)
        snippet = text[start:end]
        snippet = re.sub(r"\s+", " ", snippet)
        results.append(snippet)
    return results


def audit_openers(lines: list[str]) -> None:
    lines.append("OPENERS RETURNING-PRODUCTION AUDIT")
    lines.append("=" * 88)

    found = False

    for path in OPENERS_CANDIDATES:
        if not path.exists():
            continue

        found = True
        text = path.read_text(encoding="utf-8", errors="ignore")

        lines.append("")
        lines.append(f"FILE: {path}")
        lines.append(f"SIZE: {path.stat().st_size:,} bytes")
        lines.append(
            "VALIDATED MARKER PRESENT: "
            + str("VALIDATED_RP_OPENERS_CONTEXT_START" in text)
        )
        lines.append(
            "VALIDATED JSON REFERENCE PRESENT: "
            + str(
                "returning_production_validated_signals_2026.json"
                in text
            )
        )
        lines.append(
            "advantageRows PRESENT: "
            + str("function advantageRows" in text)
        )

        snippets = []
        for pattern in [
            r"Returning prod",
            r"returning_production",
            r"overall_rank",
            r"advantageRows",
        ]:
            snippets.extend(text_context(text, pattern, radius=350))

        unique = []
        seen = set()
        for snippet in snippets:
            if snippet not in seen:
                unique.append(snippet)
                seen.add(snippet)

        lines.append(f"RP-RELATED SNIPPETS FOUND: {len(unique)}")

        for i, snippet in enumerate(unique[:12], start=1):
            lines.append(f"  SNIPPET {i}: {snippet}")

    if not found:
        lines.append("No Openers HTML file found.")


def candidate_files() -> list[Path]:
    found: set[Path] = set()

    for root in SEARCH_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            lower = path.name.lower()

            if any(keyword in lower for keyword in KEYWORDS):
                found.add(path)

    return sorted(found)


def detect_column(columns: Iterable[str], candidates: Iterable[str]) -> str:
    normalized = {
        re.sub(r"[^a-z0-9]+", "_", str(col).lower()).strip("_"): str(col)
        for col in columns
    }

    for candidate in candidates:
        key = re.sub(
            r"[^a-z0-9]+",
            "_",
            candidate.lower(),
        ).strip("_")
        if key in normalized:
            return normalized[key]

    return ""


def inspect_csv(path: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "path": str(path),
        "file_type": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
        "read_ok": False,
        "rows": None,
        "columns": "",
        "season_column": "",
        "game_id_column": "",
        "home_team_column": "",
        "away_team_column": "",
        "team_column": "",
        "opponent_column": "",
        "first_half_spread_column": "",
        "first_half_home_score_column": "",
        "first_half_away_score_column": "",
        "ats_result_column": "",
        "seasons": "",
        "error": "",
    }

    try:
        frame = pd.read_csv(path, low_memory=False)
        result["read_ok"] = True
        result["rows"] = len(frame)
        result["columns"] = " | ".join(map(str, frame.columns))

        result["season_column"] = detect_column(
            frame.columns,
            ["season", "year"],
        )
        result["game_id_column"] = detect_column(
            frame.columns,
            [
                "game_id",
                "event_id",
                "id",
                "espn_game_id",
                "sgo_game_id",
            ],
        )
        result["home_team_column"] = detect_column(
            frame.columns,
            ["home_team", "home", "home_name"],
        )
        result["away_team_column"] = detect_column(
            frame.columns,
            ["away_team", "away", "away_name"],
        )
        result["team_column"] = detect_column(
            frame.columns,
            ["team", "team_name"],
        )
        result["opponent_column"] = detect_column(
            frame.columns,
            ["opponent", "opp", "opponent_team"],
        )
        result["first_half_spread_column"] = detect_column(
            frame.columns,
            [
                "closing_1h_spread",
                "close_1h_spread",
                "first_half_spread",
                "1h_spread",
                "closing_first_half_spread",
                "home_1h_spread",
                "closing_home_1h_spread",
                "spread_1h",
            ],
        )
        result["first_half_home_score_column"] = detect_column(
            frame.columns,
            [
                "home_1h_score",
                "first_half_home_score",
                "home_first_half_score",
                "halftime_home_score",
            ],
        )
        result["first_half_away_score_column"] = detect_column(
            frame.columns,
            [
                "away_1h_score",
                "first_half_away_score",
                "away_first_half_score",
                "halftime_away_score",
            ],
        )
        result["ats_result_column"] = detect_column(
            frame.columns,
            [
                "1h_ats_result",
                "first_half_ats_result",
                "ats_result",
                "result",
            ],
        )

        season_col = result["season_column"]
        if season_col:
            seasons = (
                pd.to_numeric(frame[season_col], errors="coerce")
                .dropna()
                .astype(int)
                .unique()
            )
            result["seasons"] = ",".join(map(str, sorted(seasons)))

    except Exception as exc:
        result["error"] = str(exc)

    return result


def inspect_sqlite(path: Path) -> dict[str, object]:
    result: dict[str, object] = {
        "path": str(path),
        "file_type": path.suffix.lower(),
        "size_bytes": path.stat().st_size,
        "read_ok": False,
        "rows": None,
        "columns": "",
        "season_column": "",
        "game_id_column": "",
        "home_team_column": "",
        "away_team_column": "",
        "team_column": "",
        "opponent_column": "",
        "first_half_spread_column": "",
        "first_half_home_score_column": "",
        "first_half_away_score_column": "",
        "ats_result_column": "",
        "seasons": "",
        "error": "",
    }

    try:
        con = sqlite3.connect(path)
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
            con,
        )["name"].tolist()

        table_descriptions = []

        for table in tables:
            info = pd.read_sql_query(f"PRAGMA table_info('{table}')", con)
            cols = info["name"].astype(str).tolist()
            matched = [
                col
                for col in cols
                if any(keyword.replace(" ", "_") in col.lower()
                       for keyword in KEYWORDS)
            ]

            if matched:
                count = pd.read_sql_query(
                    f"SELECT COUNT(*) AS n FROM '{table}'",
                    con,
                ).iloc[0]["n"]
                table_descriptions.append(
                    f"{table} ({count} rows): " + " | ".join(cols)
                )

        con.close()

        result["read_ok"] = True
        result["columns"] = " || ".join(table_descriptions)
        result["rows"] = len(table_descriptions)

    except Exception as exc:
        result["error"] = str(exc)

    return result


def audit_one_half(lines: list[str]) -> pd.DataFrame:
    lines.append("")
    lines.append("")
    lines.append("FIRST-HALF DATA AUDIT")
    lines.append("=" * 88)

    files = candidate_files()

    # Also inspect known project files even if their names do not contain 1H.
    known = [
        ROOT / "SGO/sgo_ncaaf_2024_2025_halves_odds.csv",
        ROOT / "data/research/opening_receiver_1h_ats_2024.csv",
        ROOT / "data/research/opening_receiver_1h_ats_2025.csv",
        ROOT / "data/research/opening_receiver_1h_ats_2024_2025_combined.csv",
        ROOT / "ncaaf_backtest.db",
    ]

    files = sorted(set(files + [p for p in known if p.exists()]))

    lines.append(f"CANDIDATE FILES FOUND: {len(files)}")

    rows = []

    for path in files:
        if path.suffix.lower() in {".csv", ".txt"}:
            row = inspect_csv(path)
        elif path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
            row = inspect_sqlite(path)
        else:
            row = {
                "path": str(path),
                "file_type": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "read_ok": False,
                "rows": None,
                "columns": "",
                "season_column": "",
                "game_id_column": "",
                "home_team_column": "",
                "away_team_column": "",
                "team_column": "",
                "opponent_column": "",
                "first_half_spread_column": "",
                "first_half_home_score_column": "",
                "first_half_away_score_column": "",
                "ats_result_column": "",
                "seasons": "",
                "error": "Unsupported audit type",
            }

        rows.append(row)

        lines.append("")
        lines.append(f"FILE: {row['path']}")
        lines.append(f"TYPE: {row['file_type']}")
        lines.append(f"SIZE: {row['size_bytes']:,} bytes")
        lines.append(f"READ OK: {row['read_ok']}")
        lines.append(f"ROWS/TABLES: {row['rows']}")
        lines.append(f"SEASONS: {row['seasons']}")
        lines.append(f"GAME ID COL: {row['game_id_column']}")
        lines.append(
            f"HOME/AWAY COLS: {row['home_team_column']} / "
            f"{row['away_team_column']}"
        )
        lines.append(
            f"TEAM/OPP COLS: {row['team_column']} / "
            f"{row['opponent_column']}"
        )
        lines.append(
            f"1H SPREAD COL: {row['first_half_spread_column']}"
        )
        lines.append(
            "1H SCORE COLS: "
            f"{row['first_half_home_score_column']} / "
            f"{row['first_half_away_score_column']}"
        )
        lines.append(f"ATS RESULT COL: {row['ats_result_column']}")

        if row["error"]:
            lines.append(f"ERROR: {row['error']}")

        lines.append(f"COLUMNS: {row['columns']}")

    return pd.DataFrame(rows)


def main() -> None:
    lines: list[str] = []

    audit_openers(lines)
    frame = audit_one_half(lines)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    frame.to_csv(CSV_REPORT, index=False)

    print("\n".join(lines))
    print()
    print("Created:")
    print(REPORT)
    print(CSV_REPORT)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
