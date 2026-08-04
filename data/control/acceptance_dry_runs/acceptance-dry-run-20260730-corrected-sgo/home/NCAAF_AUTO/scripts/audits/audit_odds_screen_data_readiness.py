#!/usr/bin/env python3
"""Audit available sportsbook-level NCAAF odds data for a new odds screen.

Read-only. This script does not modify source data or site files.

It inventories likely odds files, inspects schemas, identifies sportsbook-level
rows/columns, and determines whether the current project can support:

Stage 1
- opener
- consensus/current spread and total
- best side prices
- best over/under
- moneyline
- source book and book count

Stage 2
- one column per sportsbook, similar to a market-screen matrix

Outputs
-------
data/audits/odds_screen_data_inventory.csv
data/audits/odds_screen_book_coverage.csv
data/audits/odds_screen_market_coverage.csv
data/audits/odds_screen_readiness.txt
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
import json
import re
import sys
from typing import Iterable

import pandas as pd


ROOT = Path.home() / "NCAAF_AUTO"

OUT_INVENTORY = ROOT / "data/audits/odds_screen_data_inventory.csv"
OUT_BOOKS = ROOT / "data/audits/odds_screen_book_coverage.csv"
OUT_MARKETS = ROOT / "data/audits/odds_screen_market_coverage.csv"
OUT_REPORT = ROOT / "data/audits/odds_screen_readiness.txt"

SEARCH_DIRS = [
    ROOT / "data/odds",
    ROOT / "data/markets",
    ROOT / "data/raw",
    ROOT / "SGO",
    ROOT / "data",
]

BOOK_ALIASES = {
    "circa": "Circa",
    "pinnacle": "Pinnacle",
    "bookmaker": "BookMaker",
    "kalshi": "Kalshi",
    "novig": "Novig",
    "draftkings": "DraftKings",
    "draft kings": "DraftKings",
    "fanduel": "FanDuel",
    "fan duel": "FanDuel",
    "betmgm": "BetMGM",
    "bet mgm": "BetMGM",
    "caesars": "Caesars",
    "william hill": "Caesars",
    "hard rock": "Hard Rock",
    "hardrock": "Hard Rock",
    "betrivers": "BetRivers",
    "bet rivers": "BetRivers",
    "fanatics": "Fanatics",
    "espn bet": "ESPN BET",
    "espnbet": "ESPN BET",
    "bet365": "Bet365",
    "bet 365": "Bet365",
    "bally bet": "Bally Bet",
    "ballybet": "Bally Bet",
    "sports interaction": "Sports Interaction",
    "sportsbook": "Sportsbook",
}

MARKET_TERMS = {
    "spread": ["spread", "point_spread", "handicap"],
    "total": ["total", "over_under", "overunder"],
    "moneyline": ["moneyline", "money_line", "ml"],
    "first_half": ["1h", "first_half", "first half"],
    "second_half": ["2h", "second_half", "second half"],
}

BOOK_COLUMN_HINTS = [
    "book",
    "sportsbook",
    "bookmaker",
    "provider",
    "operator",
    "shop",
]

GAME_COLUMN_HINTS = [
    "game_id",
    "event_id",
    "matchup_id",
    "fixture_id",
]

TEAM_COLUMN_HINTS = [
    "away_team",
    "home_team",
    "away",
    "home",
]

LINE_COLUMN_HINTS = [
    "line",
    "spread",
    "total",
    "moneyline",
    "price",
    "odds",
    "over",
    "under",
]


def iter_candidate_files() -> Iterable[Path]:
    seen = set()

    for directory in SEARCH_DIRS:
        if not directory.exists():
            continue

        for pattern in ("*.csv", "*.json", "*.jsonl", "*.parquet"):
            for path in directory.rglob(pattern):
                if path in seen:
                    continue
                seen.add(path)

                lower_path = str(path).lower()
                if any(part in lower_path for part in [
                    "/backups/",
                    "/archive/",
                    "/archived/",
                    "/__pycache__/",
                    "/node_modules/",
                ]):
                    continue

                filename = path.name.lower()
                if any(term in filename for term in [
                    "odds",
                    "line",
                    "market",
                    "sportsbook",
                    "book",
                    "sgo",
                    "actionnetwork",
                    "theodds",
                ]):
                    yield path


def safe_read(path: Path) -> pd.DataFrame:
    try:
        suffix = path.suffix.lower()

        if suffix == ".csv":
            return pd.read_csv(path, low_memory=False)

        if suffix == ".parquet":
            return pd.read_parquet(path)

        if suffix == ".jsonl":
            return pd.read_json(path, lines=True)

        if suffix == ".json":
            raw = json.loads(path.read_text(encoding="utf-8", errors="ignore"))

            if isinstance(raw, list):
                return pd.json_normalize(raw)

            if isinstance(raw, dict):
                for key in [
                    "data",
                    "events",
                    "games",
                    "rows",
                    "results",
                    "odds",
                    "markets",
                ]:
                    value = raw.get(key)
                    if isinstance(value, list):
                        return pd.json_normalize(value)

                # Dict keyed by id.
                if raw and all(isinstance(value, dict) for value in raw.values()):
                    return pd.json_normalize(list(raw.values()))

        return pd.DataFrame()

    except Exception:
        return pd.DataFrame()


def detect_columns(columns: list[str], hints: list[str]) -> list[str]:
    result = []
    for column in columns:
        lower = column.lower()
        if any(hint in lower for hint in hints):
            result.append(column)
    return result


def canonical_book(value: object) -> str:
    text = str(value or "").strip()
    lower = re.sub(r"[_\-]+", " ", text.lower())
    lower = re.sub(r"\s+", " ", lower)

    for alias, canonical in BOOK_ALIASES.items():
        if alias in lower:
            return canonical

    return text if text and text.lower() not in {"nan", "none"} else ""


def extract_books_from_columns(columns: list[str]) -> set[str]:
    books = set()

    for column in columns:
        canonical = canonical_book(column)
        if canonical and canonical != column:
            books.add(canonical)
            continue

        lower = column.lower()
        for alias, canonical_name in BOOK_ALIASES.items():
            if alias in lower:
                books.add(canonical_name)

    return books


def detect_market_types(columns: list[str]) -> list[str]:
    markets = []

    for market, terms in MARKET_TERMS.items():
        if any(any(term in column.lower() for term in terms) for column in columns):
            markets.append(market)

    return markets


def inventory_file(path: Path) -> tuple[dict, list[dict], list[dict]]:
    df = safe_read(path)
    columns = [str(column) for column in df.columns]

    book_columns = detect_columns(columns, BOOK_COLUMN_HINTS)
    game_columns = detect_columns(columns, GAME_COLUMN_HINTS)
    team_columns = detect_columns(columns, TEAM_COLUMN_HINTS)
    line_columns = detect_columns(columns, LINE_COLUMN_HINTS)
    market_types = detect_market_types(columns)

    books = extract_books_from_columns(columns)
    long_form_book_values = set()

    for column in book_columns:
        if column not in df.columns:
            continue
        values = df[column].dropna().astype(str).head(50000)
        for value in values:
            canonical = canonical_book(value)
            if canonical:
                long_form_book_values.add(canonical)

    books.update(long_form_book_values)

    game_count = None
    for column in game_columns:
        if column in df.columns:
            game_count = int(df[column].nunique(dropna=True))
            break

    if game_count is None and len(team_columns) >= 2:
        try:
            game_count = int(
                df[team_columns[:2]]
                .astype(str)
                .agg("|".join, axis=1)
                .nunique(dropna=True)
            )
        except Exception:
            game_count = None

    has_long_form_books = bool(book_columns and long_form_book_values)
    has_wide_form_books = bool(extract_books_from_columns(columns))
    has_game_identity = bool(game_columns or len(team_columns) >= 2)
    has_market_values = bool(line_columns)
    stage2_candidate = (
        has_game_identity
        and has_market_values
        and (has_long_form_books or has_wide_form_books)
    )

    inventory = {
        "path": str(path),
        "rows": len(df),
        "columns_count": len(columns),
        "games": game_count,
        "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        "book_columns": " | ".join(book_columns),
        "books_detected": " | ".join(sorted(books)),
        "market_types": " | ".join(market_types),
        "game_columns": " | ".join(game_columns),
        "team_columns": " | ".join(team_columns),
        "line_columns": " | ".join(line_columns),
        "has_long_form_books": has_long_form_books,
        "has_wide_form_books": has_wide_form_books,
        "stage2_matrix_candidate": stage2_candidate,
        "all_columns": " | ".join(columns),
    }

    book_rows = []
    for book in sorted(books):
        count = None

        for column in book_columns:
            if column not in df.columns:
                continue
            canonical_series = df[column].map(canonical_book)
            matches = canonical_series.eq(book)
            if matches.any():
                count = int(matches.sum())
                break

        book_rows.append(
            {
                "path": str(path),
                "book": book,
                "rows_for_book": count,
                "market_types": " | ".join(market_types),
                "stage2_matrix_candidate": stage2_candidate,
            }
        )

    market_rows = []
    for market in market_types:
        relevant_columns = [
            column
            for column in columns
            if any(
                term in column.lower()
                for term in MARKET_TERMS[market]
            )
        ]

        populated = 0
        for column in relevant_columns:
            if column in df.columns:
                populated = max(populated, int(df[column].notna().sum()))

        market_rows.append(
            {
                "path": str(path),
                "market": market,
                "relevant_columns": " | ".join(relevant_columns),
                "max_populated_rows": populated,
                "rows": len(df),
                "games": game_count,
            }
        )

    return inventory, book_rows, market_rows


def main() -> None:
    inventory_rows = []
    book_rows = []
    market_rows = []

    candidates = sorted(
        iter_candidate_files(),
        key=lambda path: str(path).lower(),
    )

    for path in candidates:
        inventory, books, markets = inventory_file(path)

        # Skip unreadable/empty files with no schema.
        if inventory["rows"] == 0 and inventory["columns_count"] == 0:
            continue

        inventory_rows.append(inventory)
        book_rows.extend(books)
        market_rows.extend(markets)

    inventory_df = pd.DataFrame(inventory_rows)
    books_df = pd.DataFrame(book_rows)
    markets_df = pd.DataFrame(market_rows)

    for output in [
        OUT_INVENTORY,
        OUT_BOOKS,
        OUT_MARKETS,
        OUT_REPORT,
    ]:
        output.parent.mkdir(parents=True, exist_ok=True)

    inventory_df.to_csv(OUT_INVENTORY, index=False)
    books_df.to_csv(OUT_BOOKS, index=False)
    markets_df.to_csv(OUT_MARKETS, index=False)

    stage2 = (
        inventory_df[
            inventory_df["stage2_matrix_candidate"].eq(True)
        ]
        if not inventory_df.empty
        else pd.DataFrame()
    )

    all_books = (
        sorted(set(books_df["book"].dropna().astype(str)))
        if not books_df.empty
        else []
    )

    all_markets = (
        sorted(set(markets_df["market"].dropna().astype(str)))
        if not markets_df.empty
        else []
    )

    report = [
        "NCAAF ODDS SCREEN DATA READINESS",
        "=" * 100,
        f"Generated: {datetime.now().isoformat()}",
        "",
        "SUMMARY",
        "-" * 100,
        f"Candidate odds/market files inspected: {len(inventory_df)}",
        f"Stage 2 sportsbook-matrix candidates: {len(stage2)}",
        f"Sportsbooks detected: {len(all_books)}",
        f"Books: {', '.join(all_books) if all_books else 'none'}",
        f"Markets detected: {', '.join(all_markets) if all_markets else 'none'}",
        "",
        "STAGE 1 READINESS",
        "-" * 100,
        "Stage 1 can use the normalized season-game-line files for opener,",
        "current consensus spread/total, best side prices, moneyline, source book,",
        "book count, and matchup links.",
        "",
        "STAGE 2 MATRIX CANDIDATES",
        "-" * 100,
    ]

    if stage2.empty:
        report.append(
            "No clear sportsbook-level matrix source was identified."
        )
    else:
        display_columns = [
            "path",
            "rows",
            "games",
            "books_detected",
            "market_types",
            "book_columns",
            "line_columns",
        ]
        report.append(
            stage2[display_columns].to_string(index=False)
        )

    report.extend(
        [
            "",
            "TOP FILES BY ROW COUNT",
            "-" * 100,
        ]
    )

    if inventory_df.empty:
        report.append("No readable odds files found.")
    else:
        top = inventory_df.sort_values(
            "rows",
            ascending=False,
        ).head(25)
        report.append(
            top[
                [
                    "path",
                    "rows",
                    "games",
                    "books_detected",
                    "market_types",
                    "stage2_matrix_candidate",
                ]
            ].to_string(index=False)
        )

    report.extend(
        [
            "",
            "OUTPUTS",
            "-" * 100,
            str(OUT_INVENTORY),
            str(OUT_BOOKS),
            str(OUT_MARKETS),
        ]
    )

    OUT_REPORT.write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    print("NCAAF ODDS SCREEN DATA READINESS")
    print("=" * 100)
    print(f"Files inspected: {len(inventory_df)}")
    print(f"Stage 2 candidates: {len(stage2)}")
    print(f"Sportsbooks detected: {len(all_books)}")
    print(f"Markets detected: {', '.join(all_markets) if all_markets else 'none'}")
    print()
    print(f"Wrote: {OUT_REPORT}")
    print(f"Wrote: {OUT_INVENTORY}")
    print(f"Wrote: {OUT_BOOKS}")
    print(f"Wrote: {OUT_MARKETS}")
    print()
    print(f"Run: cat {OUT_REPORT}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
