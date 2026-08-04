#!/usr/bin/env python3
from pathlib import Path
import json
import re
import html
import pandas as pd
import numpy as np

HTML = Path("index.html")
OUT = Path("data/audit/site_market_data_audit.csv")
SUMMARY = Path("data/audit/site_market_data_audit_summary.csv")

def extract_db(html_text):
    m = re.search(
        r'<script[^>]+id=["\']db["\'][^>]*>([\s\S]*?)</script>',
        html_text,
        flags=re.I
    )
    if not m:
        raise SystemExit("Could not find <script id=\"db\"> JSON block")

    raw = html.unescape(m.group(1).strip())
    return json.loads(raw)

def has_num(v):
    return v is not None and str(v).strip() != "" and pd.notna(v)

db = extract_db(HTML.read_text(errors="ignore"))
games = db.get("games", [])

rows = []
for g in games:
    spread_status = str(g.get("market_price_status") or "").lower()
    total_status = str(g.get("market_total_price_status") or g.get("market_price_status") or "").lower()

    has_spread = has_num(g.get("market_spread_home")) and spread_status == "actual"
    has_total = has_num(g.get("market_total")) and total_status == "actual"

    rows.append({
        "game_id": g.get("game_id"),
        "week": g.get("week"),
        "date": g.get("date"),
        "away_team": g.get("away_team"),
        "home_team": g.get("home_team"),

        "projected_margin_home": g.get("projected_margin_home"),
        "projected_total": g.get("projected_total"),

        "market_spread_home": g.get("market_spread_home"),
        "market_spread_text": g.get("market_spread_text"),
        "market_spread_book": g.get("market_spread_book"),
        "market_spread_price": g.get("market_spread_price"),
        "market_line_source": g.get("market_line_source"),
        "market_price_status": g.get("market_price_status"),
        "market_line_note": g.get("market_line_note"),
        "market_books_count": g.get("market_books_count"),
        "market_books_available": g.get("market_books_available"),

        "market_total": g.get("market_total"),
        "market_total_book": g.get("market_total_book"),
        "market_total_over_price": g.get("market_total_over_price"),
        "market_total_under_price": g.get("market_total_under_price"),
        "market_total_last_update": g.get("market_total_last_update"),

        "has_actual_market_spread": has_spread,
        "has_actual_market_total": has_total,

        "spread_edge_home_if_actual": (
            float(g.get("projected_margin_home")) + float(g.get("market_spread_home"))
            if has_spread and has_num(g.get("projected_margin_home"))
            else np.nan
        ),
        "total_edge_if_actual": (
            float(g.get("projected_total")) - float(g.get("market_total"))
            if has_total and has_num(g.get("projected_total"))
            else np.nan
        ),
    })

df = pd.DataFrame(rows)
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)

summary = pd.DataFrame([
    {"metric": "games", "value": len(df)},
    {"metric": "projected_spread_games", "value": int(df["projected_margin_home"].notna().sum())},
    {"metric": "actual_market_spread_games", "value": int(df["has_actual_market_spread"].sum())},
    {"metric": "missing_or_hidden_market_spread_games", "value": int((~df["has_actual_market_spread"]).sum())},
    {"metric": "projected_total_games", "value": int(df["projected_total"].notna().sum())},
    {"metric": "actual_market_total_games", "value": int(df["has_actual_market_total"].sum())},
    {"metric": "missing_or_hidden_market_total_games", "value": int((~df["has_actual_market_total"]).sum())},
])
summary.to_csv(SUMMARY, index=False)

print("wrote:", OUT)
print("wrote:", SUMMARY)
print()
print(summary.to_string(index=False))

print("\nHawaii / Stanford:")
print(df[(df.away_team=="Hawaii") & (df.home_team=="Stanford")].to_string(index=False))

print("\nWeek 0 market audit:")
cols = [
    "week","date","away_team","home_team",
    "projected_margin_home","market_spread_home","market_spread_text",
    "market_price_status","market_line_source","has_actual_market_spread",
    "projected_total","market_total","has_actual_market_total"
]
print(df[df["week"].eq(0)][cols].to_string(index=False))

print("\nActual market spread games sample:")
print(df[df["has_actual_market_spread"]][cols].head(50).to_string(index=False))

print("\nHidden/missing market spread sample:")
print(df[~df["has_actual_market_spread"]][cols].head(75).to_string(index=False))
