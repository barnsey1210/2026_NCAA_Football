#!/usr/bin/env python3
import json
import math
import re
from datetime import date
from pathlib import Path

import pandas as pd

HTML = Path("index_auto_market.html")
OUT = Path("data/agents/daily_betting_angles.csv")

SIGMA_SPREAD = 14.0
SIGMA_TOTAL = 17.0
MAX_ATS = 10
MAX_TOTAL = 8
MIN_EV = 1.0
MIN_EDGE = 1.0

def normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def american_to_decimal(odds):
    try:
        o = float(odds)
    except Exception:
        o = -110
    if not math.isfinite(o) or o == 0:
        o = -110
    return 1 + o / 100 if o > 0 else 1 + 100 / abs(o)

def ev_pct(prob, odds):
    dec = american_to_decimal(odds)
    return (prob * (dec - 1) - (1 - prob)) * 100

def fmt_price(v):
    try:
        n = float(v)
    except Exception:
        return "-110 assumed"
    if not math.isfinite(n) or n == 0:
        return "-110 assumed"
    return f"+{int(n)}" if n > 0 else str(int(n))

def num(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def bet_score(edge, ev, books_count=1):
    try:
        b = float(books_count or 1)
    except Exception:
        b = 1
    score = 50 + ev * 2.0 + abs(edge) * 2.5 + min(5, max(0, b - 1) * 1.5)
    return max(0, min(100, score))

def extract_db():
    if not HTML.exists():
        raise SystemExit(f"Missing {HTML}. Build index_auto_market.html first.")
    txt = HTML.read_text(encoding="utf-8")
    m = re.search(r'<script id=["\']db["\'] type=["\']application/json["\']>(.*?)</script>', txt, re.S)
    if not m:
        raise SystemExit("Could not find embedded DB in index_auto_market.html")
    return json.loads(m.group(1))

db = extract_db()
rows = []
run_date = date.today().isoformat()

for g in db.get("games", []):
    proj_spread = num(g.get("projected_margin_home"))
    market_home = num(g.get("market_spread_home"))
    proj_total = num(g.get("projected_total"))
    market_total = num(g.get("market_total"))
    books_count = num(g.get("market_books_count")) or 1
    source = g.get("market_line_source") or "Market lines"

    if proj_spread is not None and market_home is not None:
        edge = proj_spread + market_home
        if abs(edge) >= MIN_EDGE:
            side_team = g.get("home_team") if edge >= 0 else g.get("away_team")
            side_line = market_home if edge >= 0 else -market_home
            price = g.get("market_spread_price") or -110
            prob = normal_cdf(abs(edge) / SIGMA_SPREAD)
            ev = ev_pct(prob, price)
            score = bet_score(edge, ev, books_count)
            if ev >= MIN_EV:
                rows.append({
                    "run_date": run_date,
                    "category": "Game line edge",
                    "title": f"ATS: {side_team} {side_line:+g} ({fmt_price(price)})",
                    "team": side_team,
                    "grade": "ATS",
                    "score": round(score, 2),
                    "reason": f"{g.get('away_team')} at {g.get('home_team')} · edge {side_team} +{abs(edge):.1f}; EV {ev:+.1f}%; {source}",
                    "action": "",
                    "source": "Market Lab / The Odds API",
                    "research_query": "",
                })

    if proj_total is not None and market_total is not None:
        edge = proj_total - market_total
        if abs(edge) >= MIN_EDGE:
            side = "Over" if edge >= 0 else "Under"
            price = g.get("market_total_over_price") if edge >= 0 else g.get("market_total_under_price")
            price = price or -110
            prob = normal_cdf(abs(edge) / SIGMA_TOTAL)
            ev = ev_pct(prob, price)
            score = bet_score(edge, ev, books_count)
            if ev >= MIN_EV:
                rows.append({
                    "run_date": run_date,
                    "category": "Game line edge",
                    "title": f"Total: {side} {market_total:g} ({fmt_price(price)})",
                    "team": f"{g.get('away_team')} at {g.get('home_team')}",
                    "grade": "TOTAL",
                    "score": round(score, 2),
                    "reason": f"{g.get('away_team')} at {g.get('home_team')} · edge {side} +{abs(edge):.1f}; EV {ev:+.1f}%; {source}",
                    "action": "",
                    "source": "Market Lab / The Odds API",
                    "research_query": "",
                })

df_new = pd.DataFrame(rows)
if not df_new.empty:
    ats = df_new[df_new["grade"].eq("ATS")].sort_values("score", ascending=False).head(MAX_ATS)
    totals = df_new[df_new["grade"].eq("TOTAL")].sort_values("score", ascending=False).head(MAX_TOTAL)
    df_new = pd.concat([ats, totals], ignore_index=True)

if OUT.exists():
    df = pd.read_csv(OUT)
else:
    df = pd.DataFrame(columns=["run_date","category","title","team","grade","score","reason","action","source","research_query"])

if not df.empty and "category" in df.columns:
    df = df[~((df["run_date"].astype(str) == run_date) & (df["category"] == "Game line edge"))]

df = pd.concat([df, df_new], ignore_index=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False)

print(f"Appended game line edges: {len(df_new)}")
if not df_new.empty:
    print(df_new[["title","grade","score","reason"]].head(20).to_string(index=False))
