#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd

IN = Path("data/odds/game_line_history.csv")
OUT = Path("data/odds/game_line_movement_report.csv")

OUT_COLS = [
    "snapshot_prev", "snapshot_latest",
    "source", "game_id", "date", "week", "away_team", "home_team",
    "market", "book",
    "previous", "latest", "change",
    "previous_price", "latest_price",
    "summary",
]

def num(v):
    try:
        if v is None or v == "" or pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None

def fmt_line(v):
    x = num(v)
    if x is None:
        return ""
    if abs(x) < 0.0001:
        return "PK"
    s = f"{x:+.1f}".replace("+", "")
    return s.rstrip("0").rstrip(".")

def fmt_price(v):
    x = num(v)
    if x is None:
        return ""
    x = int(round(x))
    return f"+{x}" if x > 0 else str(x)

def norm(v):
    return str(v or "").strip().lower()

def first_nonblank(*vals):
    for v in vals:
        if v is not None and not pd.isna(v) and str(v).strip() != "":
            return v
    return ""

def build_summary(row, market):
    away = row.get("away_team", "")
    home = row.get("home_team", "")
    book = row.get("book", "")
    prev = row.get("previous", "")
    latest = row.get("latest", "")
    price_prev = row.get("previous_price", "")
    price_latest = row.get("latest_price", "")
    if market == "Spread":
        return f"{away} at {home} {book} spread {prev} → {latest}" + (f" ({price_prev} → {price_latest})" if price_prev or price_latest else "")
    return f"{away} at {home} {book} total {prev} → {latest}" + (f" ({price_prev} → {price_latest})" if price_prev or price_latest else "")

def main():
    if not IN.exists() or IN.stat().st_size == 0:
        pd.DataFrame(columns=OUT_COLS).to_csv(OUT, index=False)
        print(f"No history found. Wrote empty {OUT}")
        return

    df = pd.read_csv(IN)
    if df.empty:
        pd.DataFrame(columns=OUT_COLS).to_csv(OUT, index=False)
        print(f"Empty history. Wrote empty {OUT}")
        return

    if "snapshot_ts" not in df.columns:
        df["snapshot_ts"] = ""

    # Older history rows only had snapshot_date. Use that as a fallback so
    # old rows can still be compared against newer timestamped snapshots.
    ts_raw = df["snapshot_ts"].copy()
    ts_raw = ts_raw.where(ts_raw.notna() & (ts_raw.astype(str).str.strip() != ""), df.get("snapshot_date", ""))
    df["_snapshot"] = pd.to_datetime(ts_raw, errors="coerce")
    df = df[df["_snapshot"].notna()].copy()

    snapshots = sorted(df["_snapshot"].dropna().unique())
    if len(snapshots) < 2:
        pd.DataFrame(columns=OUT_COLS).to_csv(OUT, index=False)
        print(f"Only {len(snapshots)} snapshot found. Wrote empty {OUT}")
        return

    prev_ts, latest_ts = snapshots[-2], snapshots[-1]
    prev = df[df["_snapshot"] == prev_ts].copy()
    latest = df[df["_snapshot"] == latest_ts].copy()

    key_cols = ["source", "date", "away_norm", "home_norm"]
    for c in key_cols:
        if c not in prev.columns:
            prev[c] = ""
        if c not in latest.columns:
            latest[c] = ""

    prev["_key"] = prev.apply(lambda r: "|".join(norm(r.get(c)) for c in key_cols), axis=1)
    latest["_key"] = latest.apply(lambda r: "|".join(norm(r.get(c)) for c in key_cols), axis=1)

    pcols = [
        "_key",
        "market_spread_home", "market_spread_price", "market_spread_book",
        "market_total", "market_total_over_price", "market_total_under_price", "market_total_book",
    ]
    for c in pcols:
        if c not in prev.columns:
            prev[c] = ""

    merged = latest.merge(prev[pcols], on="_key", how="left", suffixes=("_latest", "_prev"))

    rows = []
    for _, r in merged.iterrows():
        base = {
            "snapshot_prev": pd.Timestamp(prev_ts).isoformat(),
            "snapshot_latest": pd.Timestamp(latest_ts).isoformat(),
            "source": r.get("source", ""),
            "game_id": r.get("game_id", ""),
            "date": r.get("date", ""),
            "week": r.get("week", ""),
            "away_team": r.get("away_team", ""),
            "home_team": r.get("home_team", ""),
        }

        sp_prev = num(r.get("market_spread_home_prev"))
        sp_latest = num(r.get("market_spread_home_latest"))
        sp_price_prev = r.get("market_spread_price_prev")
        sp_price_latest = r.get("market_spread_price_latest")
        sp_book = first_nonblank(r.get("market_spread_book_latest"), r.get("market_spread_book_prev"))

        if sp_prev is not None and sp_latest is not None:
            price_changed = fmt_price(sp_price_prev) != fmt_price(sp_price_latest)
            line_changed = abs(sp_latest - sp_prev) > 0.0001
            if line_changed or price_changed:
                row = {
                    **base,
                    "market": "Spread",
                    "book": sp_book,
                    "previous": fmt_line(sp_prev),
                    "latest": fmt_line(sp_latest),
                    "change": round(sp_latest - sp_prev, 2),
                    "previous_price": fmt_price(sp_price_prev),
                    "latest_price": fmt_price(sp_price_latest),
                }
                row["summary"] = build_summary(row, "Spread")
                rows.append(row)

        tot_prev = num(r.get("market_total_prev"))
        tot_latest = num(r.get("market_total_latest"))
        tot_price_prev = first_nonblank(r.get("market_total_over_price_prev"), r.get("market_total_under_price_prev"))
        tot_price_latest = first_nonblank(r.get("market_total_over_price_latest"), r.get("market_total_under_price_latest"))
        tot_book = first_nonblank(r.get("market_total_book_latest"), r.get("market_total_book_prev"))

        if tot_prev is not None and tot_latest is not None:
            price_changed = fmt_price(tot_price_prev) != fmt_price(tot_price_latest)
            line_changed = abs(tot_latest - tot_prev) > 0.0001
            if line_changed or price_changed:
                row = {
                    **base,
                    "market": "Total",
                    "book": tot_book,
                    "previous": fmt_line(tot_prev),
                    "latest": fmt_line(tot_latest),
                    "change": round(tot_latest - tot_prev, 2),
                    "previous_price": fmt_price(tot_price_prev),
                    "latest_price": fmt_price(tot_price_latest),
                }
                row["summary"] = build_summary(row, "Total")
                rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        out = pd.DataFrame(columns=OUT_COLS)
    else:
        out = out[OUT_COLS].sort_values(["market", "date", "away_team", "home_team"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"Wrote {OUT}: {len(out)} movement rows")
    if len(out):
        print(out.head(40).to_string(index=False))

if __name__ == "__main__":
    main()
