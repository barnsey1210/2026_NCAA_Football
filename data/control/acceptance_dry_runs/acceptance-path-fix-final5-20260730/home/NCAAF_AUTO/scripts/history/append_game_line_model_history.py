#!/usr/bin/env python3
"""Append/update weekly game market/model history for matchup page charts.

Place at: scripts/history/append_game_line_model_history.py
Run after the site index.html has current projections/markets, before build_matchup_page.py.
"""
import csv
import json
import re
from datetime import datetime, timezone, date
from pathlib import Path

INDEX = Path("index.html")
OUT = Path("data/history/game_line_model_history.csv")
SEASON = 2026

FIELDS = [
    "snapshot_date", "snapshot_label", "season", "game_id", "cfbd_game_id", "game_date", "game_week",
    "away_team", "home_team", "market_spread_home", "market_total", "market_spread_open_home", "market_total_open",
    "projected_margin_home", "model_spread_home", "projected_total", "market_spread_book", "market_total_book",
    "market_books_available", "market_spread_last_update", "market_total_last_update", "market_line_source",
]


def parse_db():
    txt = INDEX.read_text(errors="ignore")
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', txt, flags=re.S)
    if not m:
        raise SystemExit("Could not find DB script in index.html")
    return json.loads(m.group(1))


def parse_date(x):
    if not x:
        return None
    try:
        return datetime.fromisoformat(str(x).replace("Z", "+00:00")).date()
    except Exception:
        try:
            return datetime.strptime(str(x)[:10], "%Y-%m-%d").date()
        except Exception:
            return None


def snapshot_label(games, today):
    dates = [parse_date(g.get("date") or g.get("cfbd_date")) for g in games]
    dates = [d for d in dates if d]
    if dates and today < min(dates):
        return "Preseason"

    eligible = []
    for g in games:
        d = parse_date(g.get("date") or g.get("cfbd_date"))
        wk = g.get("cfbd_week") or g.get("week")
        if d and d <= today and wk not in (None, ""):
            try:
                eligible.append(int(wk))
            except Exception:
                pass
    if eligible:
        return f"Wk {max(eligible)}"
    return "Preseason"


def num_or_blank(x):
    if x in (None, ""):
        return ""
    try:
        return str(round(float(x), 3))
    except Exception:
        return ""


def main():
    db = parse_db()
    games = db.get("games", []) or []
    now = datetime.now(timezone.utc)
    today = now.date()
    label = snapshot_label(games, today)
    snap = today.isoformat()

    existing = []
    if OUT.exists() and OUT.stat().st_size > 0:
        with OUT.open(newline="", encoding="utf-8") as f:
            existing = list(csv.DictReader(f))

    # Keep one latest row per game per snapshot_label.
    keyed = {(r.get("game_id"), r.get("snapshot_label")): r for r in existing}

    added = 0
    for g in games:
        gid = str(g.get("game_id") or "").strip()
        if not gid:
            continue
        projected_margin_home = g.get("projected_margin_home")
        model_spread_home = ""
        try:
            model_spread_home = str(round(-float(projected_margin_home), 3))
        except Exception:
            pass
        row = {
            "snapshot_date": snap,
            "snapshot_label": label,
            "season": str(SEASON),
            "game_id": gid,
            "cfbd_game_id": str(g.get("cfbd_game_id") or ""),
            "game_date": str(g.get("date") or g.get("cfbd_date") or ""),
            "game_week": str(g.get("cfbd_week") or g.get("week") or ""),
            "away_team": str(g.get("away_team") or ""),
            "home_team": str(g.get("home_team") or ""),
            "market_spread_home": num_or_blank(g.get("market_spread_home")),
            "market_total": num_or_blank(g.get("market_total")),
            "market_spread_open_home": num_or_blank(g.get("market_spread_open_home")),
            "market_total_open": num_or_blank(g.get("market_total_open")),
            "projected_margin_home": num_or_blank(projected_margin_home),
            "model_spread_home": model_spread_home,
            "projected_total": num_or_blank(g.get("projected_total")),
            "market_spread_book": str(g.get("market_spread_book") or ""),
            "market_total_book": str(g.get("market_total_book") or ""),
            "market_books_available": str(g.get("market_books_available") or ""),
            "market_spread_last_update": str(g.get("market_spread_last_update") or ""),
            "market_total_last_update": str(g.get("market_total_last_update") or ""),
            "market_line_source": str(g.get("market_line_source") or ""),
        }
        if keyed.get((gid, label)) != row:
            keyed[(gid, label)] = row
            added += 1

    rows = list(keyed.values())
    rows.sort(key=lambda r: (r.get("game_date", ""), r.get("game_id", ""), r.get("snapshot_label", "")))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print("snapshot_label:", label)
    print("history rows:", len(rows))
    print("rows inserted/updated:", added)
    print("wrote:", OUT)


if __name__ == "__main__":
    main()
