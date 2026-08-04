#!/usr/bin/env python3
import json
import re
from pathlib import Path
from collections import Counter

p = Path("index.html")
if not p.exists():
    raise SystemExit("FAIL: index.html missing")

html = p.read_text(errors="ignore")
m = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
if not m:
    raise SystemExit("FAIL: missing embedded DB")

db = json.loads(m.group(1))

teams = db.get("teams", [])
games = db.get("games", [])
confs = db.get("conferences", [])

market_rows = [
    g for g in games
    if g.get("market_spread_home") is not None or g.get("market_total") is not None
]

teams_with_rating = [
    t for t in teams
    if t.get("combo") is not None or t.get("rank") is not None or t.get("conference") is not None
]

futures_best = db.get("market_futures_best_prices", [])
win_totals = db.get("market_win_totals_raw", [])
conf_futures = db.get("market_conference_futures_raw", [])

checks = [
    ("teams", len(teams), 130),
    ("games", len(games), 800),
    ("conferences", len(confs), 10),
    ("teams_with_rating", len(teams_with_rating), 130),
    ("market_lab_rows", len(market_rows), 20),
    ("market_futures_best_prices", len(futures_best), 50),
    ("market_win_totals_raw", len(win_totals), 50),
    ("market_conference_futures_raw", len(conf_futures), 50),
]

failed = False
for name, actual, minimum in checks:
    print(f"{name}: {actual} / minimum {minimum}")
    if actual < minimum:
        failed = True

print("market sources:", Counter(str(g.get("market_line_source") or g.get("line_source") or "blank") for g in market_rows))

if failed:
    raise SystemExit("FAIL: publish sanity check failed")

print("PASS: index.html is safe to publish")
