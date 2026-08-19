#!/usr/bin/env python3

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]

QUOTES = (
    ROOT
    / "data/war_room/odds/theodds_ncaaf_lines_2026_fast.csv"
)

QUOTA = (
    ROOT
    / "data/war_room/audits/theodds_api_quota_status_fast.json"
)

OUT = (
    ROOT
    / "data/war_room/audits/fast_market_latency_study.json"
)


def ts(value):
    raw = str(value or "").strip()

    if not raw:
        return None

    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    try:
        d = datetime.fromisoformat(raw)
    except ValueError:
        return None

    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)

    return d.astimezone(timezone.utc)


def pct(values, q):
    if not values:
        return None

    vals = sorted(values)

    idx = round((len(vals) - 1) * q)

    return vals[idx]


def main():
    if not QUOTES.exists():
        raise SystemExit(f"Missing fast quotes: {QUOTES}")

    if not QUOTA.exists():
        raise SystemExit(f"Missing fast quota audit: {QUOTA}")

    quota = json.loads(QUOTA.read_text())

    response_at = ts(
        quota.get("response_received_at")
        or quota.get("pulled_at")
    )

    if response_at is None:
        raise SystemExit("No response timestamp available")

    with QUOTES.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    by_book = defaultdict(list)
    by_book_market = defaultdict(list)

    all_ages = []

    for r in rows:
        market = str(r.get("market") or "").strip()

        if market not in {"spreads", "totals"}:
            continue

        book = str(r.get("book") or "").strip()

        # Provider timestamps can be represented under different normalized
        # names. Use the first valid one available.
        last = None

        for field in (
            "last_update",
            "market_last_update",
            "book_last_update",
            "provider_last_update",
        ):
            last = ts(r.get(field))
            if last is not None:
                break

        if last is None:
            continue

        age = (response_at - last).total_seconds()

        # Defensive guard against minor clock skew.
        if age < -5:
            continue

        age = max(0.0, age)

        all_ages.append(age)
        by_book[book].append(age)
        by_book_market[(book, market)].append(age)

    def summarize(values):
        if not values:
            return {
                "samples": 0,
                "min_seconds": None,
                "median_seconds": None,
                "p90_seconds": None,
                "max_seconds": None,
            }

        return {
            "samples": len(values),
            "min_seconds": round(min(values), 1),
            "median_seconds": round(median(values), 1),
            "p90_seconds": round(pct(values, .90), 1),
            "max_seconds": round(max(values), 1),
        }

    books = {}

    for book in sorted(by_book):
        books[book] = {
            "all": summarize(by_book[book]),
            "spreads": summarize(
                by_book_market.get((book, "spreads"), [])
            ),
            "totals": summarize(
                by_book_market.get((book, "totals"), [])
            ),
        }

    payload = {
        "schema_version": "war-room-fast-latency-v1",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "request": {
            "profile": quota.get("profile"),
            "markets": quota.get("requested_markets"),
            "request_started_at": quota.get("request_started_at"),
            "response_received_at": quota.get(
                "response_received_at"
            ),
            "http_latency_ms": quota.get("http_latency_ms"),
            "credits_used_this_call": quota.get(
                "x_requests_last"
            ),
            "credits_remaining": quota.get(
                "x_requests_remaining"
            ),
        },
        "provider_quote_age": {
            "overall": summarize(all_ages),
            "books": books,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print()
    print("FAST MARKET LATENCY STUDY")
    print("=" * 74)

    print(
        "HTTP API latency:",
        f'{quota.get("http_latency_ms")} ms',
    )

    print(
        "API credits:",
        quota.get("x_requests_last"),
    )

    overall = payload["provider_quote_age"]["overall"]

    print(
        "Provider quote age:",
        f'median={overall["median_seconds"]}s',
        f'p90={overall["p90_seconds"]}s',
        f'max={overall["max_seconds"]}s',
    )

    print()
    print(
        f'{"BOOK":12} {"MED":>7} {"P90":>7} '
        f'{"MAX":>7} {"SAMPLES":>8}'
    )

    for book, data in books.items():
        s = data["all"]

        print(
            f'{book:12} '
            f'{str(s["median_seconds"]):>7} '
            f'{str(s["p90_seconds"]):>7} '
            f'{str(s["max_seconds"]):>7} '
            f'{s["samples"]:>8}'
        )

    print()
    print("wrote:", OUT)


if __name__ == "__main__":
    main()
