#!/usr/bin/env python3
from pathlib import Path
import json, csv
from collections import Counter, defaultdict

RAW = Path("data/markets/sgo/sgo_ncaaf_events_curl_raw.json")
OUT_ODDS = Path("data/audit/sgo_odds_inventory.csv")
OUT_BOOKS = Path("data/audit/sgo_book_inventory.csv")

def strip_headers(raw):
    if "\r\n\r\n" in raw:
        return raw.split("\r\n\r\n", 1)[1]
    if "\n\n" in raw:
        return raw.split("\n\n", 1)[1]
    return raw

raw = RAW.read_text(errors="ignore")
data = json.loads(strip_headers(raw))
events = data.get("data", [])

odd_rows = []
book_counts = Counter()
odd_counts = Counter()
period_counts = Counter()
market_counts = Counter()

for e in events:
    home = e.get("teams", {}).get("home", {}).get("names", {}).get("long")
    away = e.get("teams", {}).get("away", {}).get("names", {}).get("long")
    event_id = e.get("eventID")
    starts_at = e.get("status", {}).get("startsAt")
    odds = e.get("odds", {}) or {}

    for odd_id, o in odds.items():
        books = o.get("byBookmaker", {}) or {}
        odd_counts[odd_id] += 1
        period_counts[o.get("periodID")] += 1
        market_counts[o.get("marketName")] += 1

        for b, bd in books.items():
            book_counts[b] += 1

        odd_rows.append({
            "event_id": event_id,
            "start_time_utc": starts_at,
            "away_team": away,
            "home_team": home,
            "odd_id": odd_id,
            "market_name": o.get("marketName"),
            "stat_id": o.get("statID"),
            "stat_entity_id": o.get("statEntityID"),
            "period_id": o.get("periodID"),
            "bet_type_id": o.get("betTypeID"),
            "side_id": o.get("sideID"),
            "book_odds": o.get("bookOdds"),
            "book_spread": o.get("bookSpread"),
            "book_over_under": o.get("bookOverUnder"),
            "books_count": len(books),
            "books": ",".join(sorted(books.keys())),
        })

OUT_ODDS.parent.mkdir(parents=True, exist_ok=True)

with OUT_ODDS.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(odd_rows[0].keys()))
    w.writeheader()
    w.writerows(odd_rows)

with OUT_BOOKS.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["book", "odds_entries"])
    w.writeheader()
    for book, n in sorted(book_counts.items()):
        w.writerow({"book": book, "odds_entries": n})

print("events:", len(events))
print("odd rows:", len(odd_rows))
print("wrote:", OUT_ODDS)
print("wrote:", OUT_BOOKS)

print("\nMarkets:")
for k, v in market_counts.most_common():
    print(k, v)

print("\nPeriods:")
for k, v in period_counts.most_common():
    print(k, v)

print("\nBooks:")
for k, v in book_counts.most_common(40):
    print(k, v)

print("\nSample 1H / half odds:")
for r in odd_rows:
    txt = " ".join(str(r.get(k) or "") for k in ["odd_id","market_name","period_id"])
    if "half" in txt.lower() or r.get("period_id") in ["1h", "first-half", "half-1"]:
        print(r)
