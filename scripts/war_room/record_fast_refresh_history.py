#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

QUOTA = ROOT / "data/war_room/audits/theodds_api_quota_status_fast.json"
HEALTH = ROOT / "data/site/war_room_health.json"
LATENCY = ROOT / "data/war_room/audits/fast_market_latency_study.json"
ARCHIVE = ROOT / "data/war_room/odds/raw_archive"

OUT = ROOT / "data/war_room/audits/fast_market_refresh_history.csv"

BOOKS = [
    "DraftKings",
    "FanDuel",
    "BetMGM",
    "Caesars",
    "Pinnacle",
    "Novig",
    "ProphetX",
    "Kalshi",
]


def slug(value: str) -> str:
    return (
        value.lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def main():
    quota = json.loads(QUOTA.read_text())
    health = json.loads(HEALTH.read_text())
    latency = json.loads(LATENCY.read_text())

    refresh = health["fast_market_refresh"]
    refresh_id = refresh["refresh_id"]

    raw_files = sorted(
        ARCHIVE.glob("theodds_ncaaf_*.json"),
        key=lambda p: p.stat().st_mtime,
    )

    raw_snapshot = (
        str(raw_files[-1].relative_to(ROOT))
        if raw_files
        else ""
    )

    overall_latency = latency.get("provider_quote_age", {}).get("overall", {})

    row = {
        "refresh_id": refresh_id,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "last_fast_pull_at": refresh["last_fast_pull_at"],
        "raw_snapshot": raw_snapshot,
        "games_returned": refresh["upcoming_games_in_pull"],
        "markets": ",".join(quota.get("requested_markets") or []),
        "http_latency_ms": quota.get("http_latency_ms"),
        "credits_last": quota.get("x_requests_last"),
        "credits_used": quota.get("x_requests_used"),
        "credits_remaining": quota.get("x_requests_remaining"),
        "quote_age_median_seconds": overall_latency.get("median_seconds"),
        "quote_age_p90_seconds": overall_latency.get("p90_seconds"),
        "quote_age_max_seconds": overall_latency.get("max_seconds"),
    }

    latency_books = latency.get("provider_quote_age", {}).get("books", {})

    for book in BOOKS:
        h = health["books"].get(book, {})
        prefix = slug(book)

        row[f"{prefix}_status"] = h.get("status")
        row[f"{prefix}_color"] = h.get("color")
        row[f"{prefix}_participated"] = h.get(
            "participated_in_last_fast_pull"
        )
        row[f"{prefix}_games"] = h.get("games_with_any_quote")
        row[f"{prefix}_board_breadth_pct"] = h.get("board_breadth_pct")
        row[f"{prefix}_spread_games"] = h.get("spread_games")
        row[f"{prefix}_total_games"] = h.get("total_games")
        row[f"{prefix}_spread_completeness_pct"] = h.get(
            "spread_completeness_pct"
        )
        row[f"{prefix}_total_completeness_pct"] = h.get(
            "total_completeness_pct"
        )

        book_latency = latency_books.get(book, {}).get("all", {})
        row[f"{prefix}_quote_age_median_seconds"] = book_latency.get(
            "median_seconds"
        )
        row[f"{prefix}_quote_age_p90_seconds"] = book_latency.get(
            "p90_seconds"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)

    existing_rows = []
    if OUT.exists():
        with OUT.open(newline="", encoding="utf-8") as f:
            existing_rows = list(csv.DictReader(f))

        if any(r.get("refresh_id") == refresh_id for r in existing_rows):
            print("refresh already recorded:", refresh_id)
            return

    # Schema can evolve during War Room development. If an older CSV exists
    # with a different header, rewrite it into the current schema while
    # preserving common fields.
    fieldnames = list(row.keys())

    if existing_rows:
        normalized = []
        for old in existing_rows:
            normalized.append({
                key: old.get(key, "")
                for key in fieldnames
            })

        normalized.append(row)

        with OUT.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(normalized)
    else:
        with OUT.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(row)

    print("recorded:", refresh_id)
    print("history:", OUT)
    print("raw snapshot:", raw_snapshot)


if __name__ == "__main__":
    main()
