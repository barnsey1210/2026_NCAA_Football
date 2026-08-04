#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import pandas as pd

ROOT = Path.cwd()
OUT = ROOT / "data" / "bets"
OUT.mkdir(parents=True, exist_ok=True)

SHEET_ID = "1ElvXHLnvt7u2UDp6oZ796OHzVppm7KOEuGp6_1jEekI"
GID = "0"

URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={GID}"

df = pd.read_csv(URL)
df = df.dropna(how="all")

keep_cols = [
    "Date", "Account", "Bet Description", "Source", "Sportsbook",
    "Bet Amount", "Sport", "Bet", "Bet Type", "Bet Line", "Bet Price",
    "Result", "Profit", "Running Profit", "Closing Line", "Closing Price",
    "CLV", "EV", "Notes", "CLV %"
]
df = df[[c for c in keep_cols if c in df.columns]]

for c in ["Date", "Bet Description", "Sportsbook", "Bet Amount", "Bet", "Sport", "Bet Type"]:
    if c not in df.columns:
        df[c] = ""

def clean_text(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

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

df["_bet_clean"] = df["Bet"].apply(clean_text)
df["_book_clean"] = df["Sportsbook"].apply(clean_text)
df["_desc_clean"] = df["Bet Description"].apply(clean_text)
df["_amount_num"] = df["Bet Amount"].apply(money_to_float)

df = df[
    (df["_bet_clean"] != "")
    & (df["_book_clean"] != "")
    & (df["_desc_clean"] != "")
    & df["_amount_num"].notna()
    & (df["_amount_num"] > 0)
].copy()

df["missing_date"] = df["Date"].isna() | (df["Date"].astype(str).str.strip() == "")
df["missing_sport"] = df["Sport"].isna() | (df["Sport"].astype(str).str.strip() == "")
df["missing_bet_type"] = df["Bet Type"].isna() | (df["Bet Type"].astype(str).str.strip() == "")

df = df.drop(columns=["_bet_clean", "_book_clean", "_desc_clean", "_amount_num"], errors="ignore")
df["pulled_at"] = datetime.now().isoformat(timespec="seconds")

raw_path = OUT / "bets_raw.csv"
df.to_csv(raw_path, index=False)

print("real bet rows:", len(df))
print("missing dates:", int(df["missing_date"].sum()))
print("missing sport:", int(df["missing_sport"].sum()))
print("missing bet type:", int(df["missing_bet_type"].sum()))
print("wrote:", raw_path)
print(df.head(30).to_string(index=False))
