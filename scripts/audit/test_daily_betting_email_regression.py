#!/usr/bin/env python3
"""Regression checks for the generated daily betting email.

This test does not send email. It validates the final CSV and HTML artifacts
after the daily betting-angle pipeline has run.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data/agents/daily_betting_angles.csv"
HTML_PATH = ROOT / "data/agents/daily_betting_angles.html"

REQUIRED_CATEGORIES = {
    "Game line edge",
}

GIANT_PRICE_RE = re.compile(r"(?<!\d)[+-]\d{5,}(?:\.\d+)?")
NAN_RE = re.compile(r"(?i)(?:^|[\s,;:>])nan(?:$|[\s,;:<])")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    if not CSV_PATH.exists():
        fail(f"missing CSV: {CSV_PATH}")

    if not HTML_PATH.exists():
        fail(f"missing HTML: {HTML_PATH}")

    df = pd.read_csv(CSV_PATH)

    if df.empty:
        fail("daily betting-angle CSV is empty")

    if "category" not in df.columns:
        fail("CSV has no category column")

    category_counts = df["category"].fillna("").value_counts().to_dict()

    for category in REQUIRED_CATEGORIES:
        if int(category_counts.get(category, 0)) <= 0:
            fail(f"required category has zero rows: {category}")

    duplicate_count = int(df.duplicated().sum())
    if duplicate_count:
        fail(f"CSV contains {duplicate_count} exact duplicate rows")

    csv_text = df.fillna("").astype(str).to_csv(index=False)

    if GIANT_PRICE_RE.search(csv_text):
        fail("CSV contains a malformed five-or-more-digit signed price")

    if NAN_RE.search(csv_text):
        fail("CSV contains a visible nan value")

    email_html = HTML_PATH.read_text(errors="ignore")
    visible_text = html.unescape(re.sub(r"<[^>]+>", " ", email_html))

    if not email_html.strip():
        fail("email HTML is empty")

    if GIANT_PRICE_RE.search(visible_text):
        fail("HTML contains a malformed five-or-more-digit signed price")

    if NAN_RE.search(visible_text):
        fail("HTML contains a visible nan value")

    if "Game Line Moves" not in email_html:
        fail("HTML is missing the Game Line Moves section")

    if "Game Line Edges" not in email_html and "Game line edge" not in email_html:
        fail("HTML is missing the Game Line Edges section")

    game_moves = int(category_counts.get("Game line move", 0))
    game_edges = int(category_counts.get("Game line edge", 0))

    print("PASS: daily betting email regression")
    print(f"CSV rows: {len(df)}")
    print(f"Game line moves: {game_moves}")
    print(f"Game line edges: {game_edges}")
    print(f"Exact duplicate rows: {duplicate_count}")
    print(f"HTML bytes: {len(email_html.encode())}")
    print("Visible nan values: 0")
    print("Malformed giant prices: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
