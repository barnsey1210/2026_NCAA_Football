#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import sys
import pandas as pd

if str(ROOT := Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(ROOT))
from betting.track_close_resolver import game_label_matches, resolve_game

PUBLISHED_SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vTmGvvkdhjSorHoTPbW5f33N6--AXLmWBLitZomgKejjOpo2aG6bL4UFtVfD3RFteCUNPEbDilnq2X1/"
    "pub?gid=938568824&single=true&output=csv"
)

keep_cols = [
    "Date", "Week", "Account", "Bet Description", "Source", "Sportsbook",
    "Bet Amount", "Sport", "Bet", "Bet Type", "Bet Line", "Bet Price",
    "Result", "Profit", "Running Profit", "Track Close", "Game", "Game ID",
    "Closing Line", "Closing Price",
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

def load_canonical_games(root=ROOT):
    path = Path(root) / "data/site/current_market_contract.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing canonical game universe: {path}")
    return json.loads(path.read_text()).get("games") or []


def attach_game_identity(df, games):
    by_id = {str(game.get("game_id") or "").strip(): game for game in games}
    rows = []
    for _, source_row in df.iterrows():
        row = source_row.copy()
        raw_label = "" if pd.isna(row.get("Game")) else str(row.get("Game"))
        raw_id = "" if pd.isna(row.get("Game ID")) else str(row.get("Game ID"))
        sheet_id = raw_id.strip()
        row["raw_sheet_game"] = raw_label
        row["raw_sheet_game_id"] = raw_id

        game = None
        identity_source = None
        identity_status = None
        identity_reason = None
        if sheet_id:
            game = by_id.get(sheet_id)
            if game:
                identity_source = "SHEET_GAME_ID"
                identity_status = "MATCHED"
                identity_reason = "valid_sheet_game_id"
            else:
                identity_status = "INVALID_SHEET_GAME_ID"
                identity_reason = "invalid_sheet_game_id"
        else:
            game, fallback_reason = resolve_game(row, games)
            if game:
                identity_source = "FALLBACK_RESOLVER"
                identity_status = "MATCHED"
                identity_reason = fallback_reason
            else:
                identity_status = "UNMATCHED"
                identity_reason = fallback_reason

        row["game_identity_source"] = identity_source
        row["game_identity_status"] = identity_status
        row["game_identity_reason"] = identity_reason
        row["game_label_mismatch"] = bool(game and raw_label and not game_label_matches(raw_label, game))
        row["game_id"] = game.get("game_id") if game else None
        row["canonical_game_id"] = game.get("game_id") if game else None
        row["canonical_game_week"] = game.get("week") if game else None
        row["canonical_game_date"] = game.get("date") if game else None
        row["canonical_away_team"] = game.get("away_team") if game else None
        row["canonical_home_team"] = game.get("home_team") if game else None
        rows.append(row)
    return pd.DataFrame(rows)


def normalize_wager_frame(frame, games=None):
    df = frame.dropna(how="all").copy()
    df = df[[c for c in keep_cols if c in df.columns]]

    required = ["Date", "Week", "Account", "Bet Description", "Sportsbook", "Bet Amount", "Bet", "Sport", "Bet Type", "Game", "Game ID"]
    for column in required:
        if column not in df.columns:
            df[column] = ""

    # The current Sheet renamed the old semantic bucket to Week. Retain the
    # legacy field for downstream compatibility without changing Sheet values.
    empty_description = df["Bet Description"].apply(clean_text).eq("")
    df.loc[empty_description, "Bet Description"] = df.loc[empty_description, "Week"]

    df["_bet_clean"] = df["Bet"].apply(clean_text)
    df["_book_clean"] = df["Sportsbook"].apply(clean_text)
    df["_amount_num"] = df["Bet Amount"].apply(money_to_float)
    df = df[
        (df["_bet_clean"] != "")
        & (df["_book_clean"] != "")
        & df["_amount_num"].notna()
        & (df["_amount_num"] > 0)
    ].copy()
    df["missing_date"] = df["Date"].isna() | (df["Date"].astype(str).str.strip() == "")
    df["missing_sport"] = df["Sport"].isna() | (df["Sport"].astype(str).str.strip() == "")
    df["missing_bet_type"] = df["Bet Type"].isna() | (df["Bet Type"].astype(str).str.strip() == "")
    df = df.drop(columns=["_bet_clean", "_book_clean", "_amount_num"], errors="ignore")
    if games is not None:
        df = attach_game_identity(df, games)
    df["pulled_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return df


def main():
    parser = argparse.ArgumentParser(description="Pull the authoritative published wager ledger.")
    parser.add_argument("--input-csv", help="Use a local captured CSV instead of the published Sheet.")
    parser.add_argument("--output", default=str(ROOT / "data/bets/bets_raw.csv"))
    args = parser.parse_args()

    source = Path(args.input_csv) if args.input_csv else PUBLISHED_SHEET_CSV_URL
    df = normalize_wager_frame(pd.read_csv(source), load_canonical_games())
    raw_path = Path(args.output)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(raw_path, index=False)
    print("real bet rows:", len(df))
    print("missing dates:", int(df["missing_date"].sum()))
    print("missing sport:", int(df["missing_sport"].sum()))
    print("missing bet type:", int(df["missing_bet_type"].sum()))
    print("sheet game ids:", int(df["raw_sheet_game_id"].astype(str).str.strip().ne("").sum()))
    print("fallback resolver:", int(df["game_identity_source"].eq("FALLBACK_RESOLVER").sum()))
    print("invalid sheet game ids:", int(df["game_identity_status"].eq("INVALID_SHEET_GAME_ID").sum()))
    print("game label mismatches:", int(df["game_label_mismatch"].fillna(False).sum()))
    print("unmatched:", int(df["game_identity_status"].eq("UNMATCHED").sum()))
    print("wrote:", raw_path)


if __name__ == "__main__":
    main()
