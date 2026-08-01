#!/usr/bin/env python3
"""
append_market_history.py

SAFE market history tracker.

Reads latest/current files:
- market_win_totals_import.csv
- market_conference_futures_import.csv

Appends/dedupes history files:
- market_win_totals_history.csv
- market_conference_futures_history.csv

Creates movement exports:
- market_win_totals_movement.csv
- market_conference_futures_movement.csv
- market_movement_export.xlsx

Does NOT touch 2026_NCAA _Season.xlsm.

Usage:
  python3 append_market_history.py

After running, your daily flow should be:
  python3 pull_actionnetwork_win_totals_api.py
  python3 pull_actionnetwork_conference_futures_api.py
  python3 append_market_history.py
  python3 build_market_futures_safe.py ...
  python3 build_site_from_workbook_safe.py ...
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any, Optional

import pandas as pd


WIN_LATEST = "market_win_totals_import.csv"
FUT_LATEST = "market_conference_futures_import.csv"
WIN_HISTORY = "market_win_totals_history.csv"
FUT_HISTORY = "market_conference_futures_history.csv"
WIN_MOVEMENT = "market_win_totals_movement.csv"
FUT_MOVEMENT = "market_conference_futures_movement.csv"
MOVEMENT_XLSX = "market_movement_export.xlsx"


def clean(v: Any) -> Any:
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    return v


def to_float(v: Any) -> Optional[float]:
    v = clean(v)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None


def to_int(v: Any) -> Optional[int]:
    f = to_float(v)
    return int(round(f)) if f is not None else None


def read_csv_or_empty(path: str, columns: list[str]) -> pd.DataFrame:
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(p)
    for c in columns:
        if c not in df.columns:
            df[c] = None
    return df[columns + [c for c in df.columns if c not in columns]]


def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if "snapshot_date" in df.columns:
        df["snapshot_date"] = pd.to_datetime(df["snapshot_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    return df


def append_history(latest_path: str, history_path: str, key_cols: list[str], columns: list[str]) -> pd.DataFrame:
    latest = normalize_dates(read_csv_or_empty(latest_path, columns))
    hist = normalize_dates(read_csv_or_empty(history_path, columns))

    combined = pd.concat([hist, latest], ignore_index=True)
    if combined.empty:
        combined.to_csv(history_path, index=False)
        return combined

    for c in columns:
        if c not in combined.columns:
            combined[c] = None

    combined = combined.drop_duplicates(subset=key_cols, keep="last")
    combined = combined.sort_values(key_cols).reset_index(drop=True)
    combined.to_csv(history_path, index=False)
    return combined


def american_to_prob(odds: Any) -> Optional[float]:
    o = to_float(odds)
    if o is None or o == 0:
        return None
    if o > 0:
        return 100.0 / (o + 100.0)
    return abs(o) / (abs(o) + 100.0)


def fmt_american(o: Any) -> str:
    oi = to_int(o)
    if oi is None:
        return ""
    return f"+{oi}" if oi > 0 else str(oi)


def build_win_movement(hist: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "season", "team", "conference", "book", "first_snapshot_date", "latest_snapshot_date",
        "opening_win_total", "current_win_total", "win_total_move",
        "opening_over_odds", "current_over_odds", "over_odds_move",
        "opening_under_odds", "current_under_odds", "under_odds_move",
        "snapshots"
    ]
    if hist.empty:
        return pd.DataFrame(columns=cols)

    df = hist.copy()
    df["snapshot_date_dt"] = pd.to_datetime(df["snapshot_date"], errors="coerce")
    rows = []

    for keys, g in df.groupby(["season", "team", "book"], dropna=False):
        g = g.sort_values("snapshot_date_dt")
        first = g.iloc[0]
        last = g.iloc[-1]
        conf = last.get("conference") if clean(last.get("conference")) is not None else first.get("conference")

        opening_line = to_float(first.get("win_total"))
        current_line = to_float(last.get("win_total"))
        opening_over = to_int(first.get("over_odds"))
        current_over = to_int(last.get("over_odds"))
        opening_under = to_int(first.get("under_odds"))
        current_under = to_int(last.get("under_odds"))

        rows.append({
            "season": keys[0],
            "team": keys[1],
            "conference": conf,
            "book": keys[2],
            "first_snapshot_date": first.get("snapshot_date"),
            "latest_snapshot_date": last.get("snapshot_date"),
            "opening_win_total": opening_line,
            "current_win_total": current_line,
            "win_total_move": None if opening_line is None or current_line is None else current_line - opening_line,
            "opening_over_odds": opening_over,
            "current_over_odds": current_over,
            "over_odds_move": None if opening_over is None or current_over is None else current_over - opening_over,
            "opening_under_odds": opening_under,
            "current_under_odds": current_under,
            "under_odds_move": None if opening_under is None or current_under is None else current_under - opening_under,
            "snapshots": len(g),
        })

    return pd.DataFrame(rows, columns=cols)


def build_futures_movement(hist: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "season", "conference", "team", "book", "first_snapshot_date", "latest_snapshot_date",
        "opening_american_odds", "current_american_odds", "american_odds_move",
        "opening_implied_prob", "current_implied_prob", "implied_prob_move",
        "snapshots"
    ]
    if hist.empty:
        return pd.DataFrame(columns=cols)

    df = hist.copy()
    df["snapshot_date_dt"] = pd.to_datetime(df["snapshot_date"], errors="coerce")
    rows = []

    for keys, g in df.groupby(["season", "conference", "team", "book"], dropna=False):
        g = g.sort_values("snapshot_date_dt")
        first = g.iloc[0]
        last = g.iloc[-1]

        opening_odds = to_int(first.get("american_odds"))
        current_odds = to_int(last.get("american_odds"))
        opening_prob = american_to_prob(opening_odds)
        current_prob = american_to_prob(current_odds)

        rows.append({
            "season": keys[0],
            "conference": keys[1],
            "team": keys[2],
            "book": keys[3],
            "first_snapshot_date": first.get("snapshot_date"),
            "latest_snapshot_date": last.get("snapshot_date"),
            "opening_american_odds": opening_odds,
            "current_american_odds": current_odds,
            "american_odds_move": None if opening_odds is None or current_odds is None else current_odds - opening_odds,
            "opening_implied_prob": opening_prob,
            "current_implied_prob": current_prob,
            "implied_prob_move": None if opening_prob is None or current_prob is None else current_prob - opening_prob,
            "snapshots": len(g),
        })

    return pd.DataFrame(rows, columns=cols)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--win-latest", default=WIN_LATEST)
    p.add_argument("--futures-latest", default=FUT_LATEST)
    p.add_argument("--win-history", default=WIN_HISTORY)
    p.add_argument("--futures-history", default=FUT_HISTORY)
    p.add_argument("--win-movement", default=WIN_MOVEMENT)
    p.add_argument("--futures-movement", default=FUT_MOVEMENT)
    p.add_argument("--movement-xlsx", default=MOVEMENT_XLSX)
    args = p.parse_args()

    win_cols = ["snapshot_date", "season", "team", "conference", "book", "win_total", "over_odds", "under_odds", "source_url", "notes"]
    fut_cols = ["snapshot_date", "season", "conference", "team", "book", "american_odds", "source_url", "notes"]

    win_hist = append_history(
        args.win_latest,
        args.win_history,
        ["snapshot_date", "season", "team", "book", "win_total"],
        win_cols,
    )
    fut_hist = append_history(
        args.futures_latest,
        args.futures_history,
        ["snapshot_date", "season", "conference", "team", "book"],
        fut_cols,
    )

    win_move = build_win_movement(win_hist)
    fut_move = build_futures_movement(fut_hist)

    win_move.to_csv(args.win_movement, index=False)
    fut_move.to_csv(args.futures_movement, index=False)

    with pd.ExcelWriter(args.movement_xlsx, engine="openpyxl") as writer:
        win_hist.to_excel(writer, index=False, sheet_name="Win Totals History")
        fut_hist.to_excel(writer, index=False, sheet_name="Conference Futures History")
        win_move.to_excel(writer, index=False, sheet_name="Win Totals Movement")
        fut_move.to_excel(writer, index=False, sheet_name="Conference Futures Movement")

    print("Done.")
    print("Win history rows:", len(win_hist), "->", args.win_history)
    print("Futures history rows:", len(fut_hist), "->", args.futures_history)
    print("Win movement rows:", len(win_move), "->", args.win_movement)
    print("Futures movement rows:", len(fut_move), "->", args.futures_movement)
    print("Movement workbook:", args.movement_xlsx)


if __name__ == "__main__":
    main()
