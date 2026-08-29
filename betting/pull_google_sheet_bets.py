#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import argparse
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

PUBLISHED_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vTmGvvkdhjSorHoTPbW5f33N6--AXLmWBLitZomgKejjOpo2aG6bL4UFtVfD3RFteCUNPEbDilnq2X1/"
    "pub?gid=938568824&single=true&output=csv"
)

keep_cols = [
    "Date", "Account", "Bet Description", "Source", "Sportsbook",
    "Bet Amount", "Sport", "Bet", "Bet Type", "Bet Line", "Bet Price",
    "Result", "Profit", "Running Profit", "Closing Line", "Closing Price",
    "CLV", "EV", "Notes", "CLV %"
]
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

def normalize_wager_frame(frame):
    df = frame.dropna(how="all").copy()
    df = df[[c for c in keep_cols if c in df.columns]]

    required = ["Date", "Bet Description", "Sportsbook", "Bet Amount", "Bet", "Sport", "Bet Type"]
    for column in required:
        if column not in df.columns:
            df[column] = ""

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
    df["pulled_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return df


def main():
    parser = argparse.ArgumentParser(description="Pull the authoritative published wager ledger.")
    parser.add_argument("--input-csv", help="Use a local captured CSV instead of the published Sheet.")
    parser.add_argument("--output", default=str(ROOT / "data/bets/bets_raw.csv"))
    args = parser.parse_args()

    source = Path(args.input_csv) if args.input_csv else PUBLISHED_SHEET_CSV_URL
    df = normalize_wager_frame(pd.read_csv(source))
    raw_path = Path(args.output)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(raw_path, index=False)
    print("real bet rows:", len(df))
    print("missing dates:", int(df["missing_date"].sum()))
    print("missing sport:", int(df["missing_sport"].sum()))
    print("missing bet type:", int(df["missing_bet_type"].sum()))
    print("wrote:", raw_path)


if __name__ == "__main__":
    main()
