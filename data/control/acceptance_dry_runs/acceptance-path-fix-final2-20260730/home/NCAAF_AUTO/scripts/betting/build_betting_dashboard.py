#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import json
import re
import pandas as pd

ROOT = Path.cwd()
BETS = ROOT / "data" / "bets"
BETS.mkdir(parents=True, exist_ok=True)

INFILE = BETS / "bets_raw.csv"
ENRICHED = BETS / "bets_enriched.csv"
DASH = BETS / "betting_dashboard.json"

def money_to_float(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    if not s or s.lower() == "nan":
        return None
    s = s.replace("$", "").replace(",", "").replace("(", "-").replace(")", "")
    try:
        return float(s)
    except Exception:
        return None

def num(x):
    if pd.isna(x):
        return None
    s = str(x).strip().replace("%", "")
    if not s or s.lower() == "nan":
        return None
    try:
        return float(s)
    except Exception:
        return None

def american_to_implied(odds):
    if odds is None or pd.isna(odds):
        return None
    odds = float(odds)
    if odds < 0:
        return abs(odds) / (abs(odds) + 100.0)
    return 100.0 / (odds + 100.0)

def clean_status(result):
    if pd.isna(result) or str(result).strip() == "":
        return "Open"
    s = str(result).strip().lower()
    if s in ["w", "win", "won"]:
        return "Won"
    if s in ["l", "loss", "lost"]:
        return "Lost"
    if s in ["p", "push"]:
        return "Push"
    if "cash" in s:
        return "Cashout"
    return str(result).strip()

def parse_side_from_bet(bet):
    s = f" {str(bet).lower()} "
    if " under " in s:
        return "Under"
    if " over " in s:
        return "Over"
    if " win " in s:
        return "Yes"
    return ""

def parse_team_from_bet(bet):
    s = str(bet).strip()
    s = re.sub(r"\s+(under|over)\s+[-+]?\d+(\.\d+)?$", "", s, flags=re.I)
    s = re.sub(r"\s+win\s+.*$", "", s, flags=re.I)
    aliases = {
        "iowa state": "Iowa State",
        "georgia tech": "Georgia Tech",
        "ohio state": "Ohio State",
        "ole miss": "Ole Miss",
        "miami oh": "Miami-OH",
        "miami ohio": "Miami-OH",
        "missouri st": "Missouri State",
        "cal": "California",
        "unlv": "UNLV",
    }
    return aliases.get(s.lower(), s.title())

if not INFILE.exists():
    raise SystemExit(f"Missing {INFILE}. Run pull_google_sheet_bets.py first.")

df = pd.read_csv(INFILE)

df["stake"] = df.get("Bet Amount", "").apply(money_to_float)
df["bet_price"] = df.get("Bet Price", "").apply(num)
df["bet_line"] = df.get("Bet Line", "").apply(num)
df["closing_line"] = df.get("Closing Line", "").apply(num)
df["closing_price"] = df.get("Closing Price", "").apply(num)
df["profit_num"] = df.get("Profit", "").apply(money_to_float)
df["status"] = df.get("Result", "").apply(clean_status)
df["is_open"] = df["status"].eq("Open")

# Sheet Profit may show pending risk as negative on open bets.
# Dashboard realized profit should only count settled bets.
df["realized_profit"] = df["profit_num"]
df.loc[df["is_open"], "realized_profit"] = 0.0
df["side"] = df.get("Bet", "").apply(parse_side_from_bet)
df["team_guess"] = df.get("Bet", "").apply(parse_team_from_bet)

df["line_clv"] = None
for idx, row in df.iterrows():
    side = row.get("side")
    bl = row.get("bet_line")
    cl = row.get("closing_line")
    if bl is None or cl is None or pd.isna(bl) or pd.isna(cl):
        continue
    if side == "Over":
        df.at[idx, "line_clv"] = cl - bl
    elif side == "Under":
        df.at[idx, "line_clv"] = bl - cl

df["bet_implied_prob"] = df["bet_price"].apply(american_to_implied)
df["closing_implied_prob"] = df["closing_price"].apply(american_to_implied)

df["price_clv_pp"] = None
for idx, row in df.iterrows():
    b = row.get("bet_implied_prob")
    c = row.get("closing_implied_prob")
    if b is not None and c is not None and not pd.isna(b) and not pd.isna(c):
        df.at[idx, "price_clv_pp"] = round((c - b) * 100, 2)

settled = df[~df["is_open"]]
open_bets = df[df["is_open"]]

total_bets = int(len(df))
open_count = int(len(open_bets))
settled_count = int(len(settled))
exposure = float(open_bets["stake"].fillna(0).sum())
avg_bet = float(df["stake"].fillna(0).mean()) if total_bets else 0.0
profit = float(settled["realized_profit"].fillna(0).sum()) if settled_count else 0.0
settled_risk = float(settled["stake"].fillna(0).sum()) if settled_count else 0.0
roi = profit / settled_risk if settled_risk else None

wins = int(settled["status"].eq("Won").sum()) if settled_count else 0
losses = int(settled["status"].eq("Lost").sum()) if settled_count else 0
pushes = int(settled["status"].eq("Push").sum()) if settled_count else 0

def group_summary(col):
    if col not in df.columns:
        return []
    g = df.groupby(col, dropna=False).agg(
        bets=("Bet", "count"),
        open=("is_open", "sum"),
        stake=("stake", "sum"),
        profit=("realized_profit", "sum"),
    ).reset_index()
    g["settled"] = g["bets"] - g["open"]
    return g.sort_values(["bets", "stake"], ascending=False).head(25).to_dict(orient="records")

open_cols = [
    "Date", "Account", "Bet Description", "Source", "Sportsbook",
    "Sport", "Bet", "Bet Type", "stake", "bet_line", "bet_price",
    "closing_line", "closing_price", "line_clv", "price_clv_pp",
    "status", "Notes", "team_guess", "side"
]
open_table = open_bets[[c for c in open_cols if c in open_bets.columns]].copy()

dashboard = {
    "updated_at": datetime.now().isoformat(timespec="seconds"),
    "summary": {
        "bets": total_bets,
        "open": open_count,
        "settled": settled_count,
        "exposure": round(exposure, 2),
        "avg_bet": round(avg_bet, 2),
        "profit": round(profit, 2),
        "roi": round(roi, 4) if roi is not None else None,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "missing_dates": int(df.get("missing_date", pd.Series(dtype=bool)).fillna(False).sum()) if "missing_date" in df.columns else None,
        "missing_sport": int(df.get("missing_sport", pd.Series(dtype=bool)).fillna(False).sum()) if "missing_sport" in df.columns else None,
        "missing_bet_type": int(df.get("missing_bet_type", pd.Series(dtype=bool)).fillna(False).sum()) if "missing_bet_type" in df.columns else None,
    },
    "by_bet_description": group_summary("Bet Description"),
    "by_sportsbook": group_summary("Sportsbook"),
    "by_source": group_summary("Source"),
    "by_sport": group_summary("Sport"),
    "open_bets": open_table.to_dict(orient="records"),
}

df.to_csv(ENRICHED, index=False)
DASH.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")

print("wrote:", ENRICHED)
print("wrote:", DASH)
print(json.dumps(dashboard["summary"], indent=2))
