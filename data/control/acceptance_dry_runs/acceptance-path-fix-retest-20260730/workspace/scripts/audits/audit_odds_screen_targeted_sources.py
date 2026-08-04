#!/usr/bin/env python3
"""Create a concise, targeted odds-screen source audit.

Read-only. No source files are modified.

This script inspects only the most relevant current NCAAF odds sources and
prints a compact report with:
- row counts
- exact columns
- unique books from true book columns only
- market coverage
- sample rows
- recommendation for Stage 1 and Stage 2 odds-page inputs

Outputs:
data/audits/odds_screen_targeted_audit.txt
data/audits/odds_screen_targeted_columns.csv
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

import pandas as pd


ROOT = Path.home() / "NCAAF_AUTO"

CANDIDATES = [
    ROOT / "data/markets/sgo/sgo_ncaaf_game_odds.csv",
    ROOT / "data/odds/actionnetwork_ncaaf_game_lines_2026.csv",
    ROOT / "data/odds/action_ncaaf_game_lines_2026.csv",
    ROOT / "data/odds/actionnetwork_season_game_lines_2026.csv",
    ROOT / "data/odds/season_game_lines_2026.csv",
    ROOT / "data/odds/cfbd_lines_2026.csv",
    ROOT / "data/history/matchup_line_history_clean.csv",
    ROOT / "data/site/matchups_view.json",
]

TRUE_BOOK_COLUMNS = {
    "book",
    "sportsbook",
    "book_name",
    "book_key",
    "market_spread_book",
    "market_total_book",
    "market_best_home_spread_book",
    "market_best_away_spread_book",
    "market_best_over_book",
    "market_best_under_book",
    "market_home_moneyline_book",
    "market_away_moneyline_book",
    "books_available",
    "market_books_available",
}

IDENTITY_COLUMNS = [
    "game_id",
    "event_id",
    "date",
    "game_date",
    "week",
    "away_team",
    "home_team",
]

MARKET_COLUMNS = [
    "market_spread_home",
    "market_spread_open_home",
    "market_spread_text",
    "market_spread_price",
    "market_spread_book",
    "market_best_home_spread_home",
    "market_best_home_spread_text",
    "market_best_home_spread_price",
    "market_best_home_spread_book",
    "market_best_away_spread_home",
    "market_best_away_spread_text",
    "market_best_away_spread_price",
    "market_best_away_spread_book",
    "market_total",
    "market_total_open",
    "market_total_book",
    "market_total_over_price",
    "market_total_under_price",
    "market_best_over_total",
    "market_best_over_price",
    "market_best_over_book",
    "market_best_under_total",
    "market_best_under_price",
    "market_best_under_book",
    "market_home_moneyline",
    "market_home_moneyline_book",
    "market_away_moneyline",
    "market_away_moneyline_book",
    "market_books_available",
    "market_books_count",
    "books_available",
    "books_count",
    "market_spread_last_update",
    "market_total_last_update",
    "last_update",
    "updated_at",
]

OUT = ROOT / "data/audits/odds_screen_targeted_audit.txt"
OUT_COLUMNS = ROOT / "data/audits/odds_screen_targeted_columns.csv"


def read_source(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)

    if path.suffix.lower() == ".json":
        raw = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        if isinstance(raw, dict) and isinstance(raw.get("games"), list):
            rows = []
            for record in raw["games"]:
                game = record.get("game", {})
                market = record.get("market", {})
                spread = market.get("spread", {})
                total = market.get("total", {})
                rows.append(
                    {
                        "game_id": game.get("game_id"),
                        "date": game.get("date"),
                        "week": game.get("week"),
                        "away_team": game.get("away_team"),
                        "home_team": game.get("home_team"),
                        "market_spread_home": spread.get("home_line"),
                        "market_spread_open_home": spread.get("open_home_line"),
                        "market_spread_price": spread.get("price"),
                        "market_spread_book": spread.get("book"),
                        "market_total": total.get("line"),
                        "market_total_open": total.get("open"),
                        "market_total_over_price": total.get("over_price"),
                        "market_total_under_price": total.get("under_price"),
                        "market_total_book": total.get("book"),
                        "market_books_available": market.get("books_available"),
                        "market_books_count": market.get("books_count"),
                    }
                )
            return pd.DataFrame(rows)

    return pd.DataFrame()


def clean_book_values(df: pd.DataFrame) -> list[str]:
    values = set()

    for column in df.columns:
        if column not in TRUE_BOOK_COLUMNS:
            continue

        for value in df[column].dropna().astype(str):
            for token in value.replace("|", ",").split(","):
                token = token.strip()
                if not token:
                    continue
                if token.lower() in {"nan", "none", "false", "true"}:
                    continue
                if token.replace(".", "", 1).replace("-", "", 1).isdigit():
                    continue
                values.add(token)

    return sorted(values)


def field_coverage(df: pd.DataFrame, columns: list[str]) -> list[tuple[str, int]]:
    result = []
    for column in columns:
        if column in df.columns:
            result.append((column, int(df[column].notna().sum())))
    return result


def sample_rows(df: pd.DataFrame) -> str:
    columns = [
        column
        for column in IDENTITY_COLUMNS + MARKET_COLUMNS
        if column in df.columns
    ]
    if not columns:
        return "No relevant columns."

    subset = df[columns].head(5).copy()
    return subset.to_string(index=False)


def classify(df: pd.DataFrame) -> tuple[bool, bool]:
    columns = set(df.columns)

    has_game = (
        "game_id" in columns
        or {"away_team", "home_team"}.issubset(columns)
    )

    has_stage1 = has_game and bool(
        columns.intersection(
            {
                "market_spread_home",
                "market_total",
                "market_best_home_spread_home",
                "market_best_over_total",
            }
        )
    )

    has_true_book_column = bool(columns.intersection(TRUE_BOOK_COLUMNS))
    has_stage2 = has_game and has_true_book_column and (
        "book" in columns
        or "sportsbook" in columns
        or "book_name" in columns
        or "book_key" in columns
    )

    return has_stage1, has_stage2


def main() -> None:
    lines = [
        "NCAAF ODDS SCREEN TARGETED SOURCE AUDIT",
        "=" * 100,
    ]

    column_rows = []
    stage1_candidates = []
    stage2_candidates = []

    for path in CANDIDATES:
        lines.extend(["", str(path), "-" * 100])

        if not path.exists():
            lines.append("MISSING")
            continue

        try:
            df = read_source(path)
        except Exception as exc:
            lines.append(f"READ ERROR: {exc}")
            continue

        books = clean_book_values(df)
        stage1, stage2 = classify(df)

        if stage1:
            stage1_candidates.append(str(path))
        if stage2:
            stage2_candidates.append(str(path))

        game_count = None
        if "game_id" in df.columns:
            game_count = int(df["game_id"].nunique(dropna=True))
        elif {"away_team", "home_team"}.issubset(df.columns):
            game_count = int(
                df[["away_team", "home_team"]]
                .astype(str)
                .agg("|".join, axis=1)
                .nunique()
            )

        lines.append(f"Rows: {len(df)}")
        lines.append(f"Games: {game_count}")
        lines.append(f"Stage 1 candidate: {stage1}")
        lines.append(f"Stage 2 long-form matrix candidate: {stage2}")
        lines.append(f"True books detected: {', '.join(books) if books else 'none'}")
        lines.append("")

        coverage = field_coverage(df, MARKET_COLUMNS)
        lines.append("Market-field coverage:")
        if coverage:
            for column, populated in coverage:
                lines.append(f"  {column}: {populated}")
        else:
            lines.append("  none")

        lines.append("")
        lines.append("Sample rows:")
        lines.append(sample_rows(df))

        for column in df.columns:
            column_rows.append(
                {
                    "path": str(path),
                    "column": str(column),
                    "populated_rows": int(df[column].notna().sum()),
                    "dtype": str(df[column].dtype),
                }
            )

    lines.extend(
        [
            "",
            "RECOMMENDATION",
            "=" * 100,
            "Stage 1 should use the normalized current-game source with the best",
            "coverage for opener, current spread/total, best-side prices, moneylines,",
            "books available, and last-updated fields.",
            "",
            "Stage 2 requires a true long-form source with one row per",
            "game + sportsbook + market + outcome. A file is not considered",
            "Stage 2-ready merely because it contains a best-book column.",
            "",
            "Stage 1 candidates:",
            *[f"  {path}" for path in stage1_candidates],
            "",
            "Stage 2 long-form candidates:",
            *([f"  {path}" for path in stage2_candidates] or ["  none"]),
        ]
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    pd.DataFrame(column_rows).to_csv(OUT_COLUMNS, index=False)

    print("NCAAF ODDS SCREEN TARGETED SOURCE AUDIT")
    print("=" * 100)
    print(f"Wrote: {OUT}")
    print(f"Wrote: {OUT_COLUMNS}")
    print()
    print("Stage 1 candidates:", len(stage1_candidates))
    print("Stage 2 long-form candidates:", len(stage2_candidates))
    print()
    print("Run:")
    print(f"sed -n '/RECOMMENDATION/,$p' {OUT}")
    print()
    print("For full review, upload:")
    print(OUT)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
