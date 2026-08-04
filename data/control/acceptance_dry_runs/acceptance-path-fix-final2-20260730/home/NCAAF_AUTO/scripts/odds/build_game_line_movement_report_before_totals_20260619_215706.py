#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd
import re

IN = Path("data/odds/game_line_history.csv")
OUT = Path("data/odds/game_line_movement_report.csv")

OUT_COLS = [
    "snapshot_prev", "snapshot_latest",
    "source_prev", "source_latest",
    "game_id", "date", "week", "away_team", "home_team",
    "market", "book",
    "previous", "latest", "change",
    "previous_price", "latest_price",
    "summary",
]

SOURCE_PRIORITY = {
    "action network": 1,
    "the odds api": 2,
    "cfbd lines": 3,
}

def norm_text(v):
    return re.sub(r"[^a-z0-9]+", " ", str(v or "").lower()).strip()

def num(v):
    try:
        if v is None or pd.isna(v):
            return None
        s = str(v).strip()
        if s == "" or s.lower() in {"nan", "none", "nat"}:
            return None
        return float(s)
    except Exception:
        return None

def fmt_line(v):
    x = num(v)
    if x is None:
        return ""
    if abs(x) < 0.0001:
        return "PK"
    s = f"{x:+.1f}"
    return s.rstrip("0").rstrip(".")

def fmt_total(v):
    x = num(v)
    if x is None:
        return ""
    return f"{x:.1f}".rstrip("0").rstrip(".")

def fmt_price(v):
    x = num(v)
    if x is None:
        return ""
    x = int(round(x))
    return f"+{x}" if x > 0 else str(x)

def first_nonblank(*vals):
    for v in vals:
        if v is not None and not pd.isna(v) and str(v).strip() != "" and str(v).strip().lower() not in {"nan","none","nat"}:
            return v
    return ""

def source_rank(v):
    return SOURCE_PRIORITY.get(norm_text(v), 99)

def effective_snapshot_series(df):
    if "snapshot_ts" not in df.columns:
        df["snapshot_ts"] = ""
    if "snapshot_date" not in df.columns:
        df["snapshot_date"] = ""
    ts = df["snapshot_ts"].astype(str).str.strip()
    dt = df["snapshot_date"].astype(str).str.strip()
    ts = ts.where(~ts.str.lower().isin(["", "nan", "none", "nat"]), dt)
    return pd.to_datetime(ts, errors="coerce", utc=True, format="mixed")

def game_key_row(r):
    # Use team/date key so Action can be the primary published source.
    # Keep source out of the key.
    return "|".join([
        str(r.get("date") or "").strip()[:10],
        norm_text(r.get("away_norm") or r.get("away_team")),
        norm_text(r.get("home_norm") or r.get("home_team")),
    ])

def collapse_to_published_snapshot(df):
    d = df.copy()
    d["_game_key"] = d.apply(game_key_row, axis=1)
    d["_source_rank"] = d["source"].apply(source_rank)
    d["_has_spread"] = d["market_spread_home"].apply(lambda x: 0 if num(x) is not None else 1)
    d["_has_total"] = d["market_total"].apply(lambda x: 0 if num(x) is not None else 1)

    # Sort by source priority first, then prefer rows with any usable spread/total.
    d = d.sort_values(["_game_key", "_source_rank", "_has_spread", "_has_total"])
    return d.drop_duplicates("_game_key", keep="first").copy()

def main():
    if not IN.exists() or IN.stat().st_size == 0:
        pd.DataFrame(columns=OUT_COLS).to_csv(OUT, index=False)
        print(f"No history found. Wrote empty {OUT}")
        return

    h = pd.read_csv(IN, dtype=str)
    if h.empty:
        pd.DataFrame(columns=OUT_COLS).to_csv(OUT, index=False)
        print(f"Empty history. Wrote empty {OUT}")
        return

    for c in [
        "source","date","week","away_team","home_team","away_norm","home_norm",
        "market_spread_home","market_spread_price","market_spread_book",
        "market_total","market_total_over_price","market_total_under_price","market_total_book",
        "game_id"
    ]:
        if c not in h.columns:
            h[c] = ""

    h["_snapshot"] = effective_snapshot_series(h)
    h = h[h["_snapshot"].notna()].copy()

    snapshots = sorted(h["_snapshot"].dropna().unique())
    if len(snapshots) < 2:
        pd.DataFrame(columns=OUT_COLS).to_csv(OUT, index=False)
        print(f"Only {len(snapshots)} snapshot found. Wrote empty {OUT}")
        return

    prev_ts, latest_ts = snapshots[-2], snapshots[-1]
    prev = collapse_to_published_snapshot(h[h["_snapshot"] == prev_ts])
    latest = collapse_to_published_snapshot(h[h["_snapshot"] == latest_ts])

    merged = latest.merge(
        prev,
        on="_game_key",
        how="left",
        suffixes=("_latest", "_prev")
    )

    rows = []
    for _, r in merged.iterrows():
        base = {
            "snapshot_prev": pd.Timestamp(prev_ts).isoformat(),
            "snapshot_latest": pd.Timestamp(latest_ts).isoformat(),
            "source_prev": r.get("source_prev", ""),
            "source_latest": r.get("source_latest", ""),
            "game_id": first_nonblank(r.get("game_id_latest"), r.get("game_id_prev")),
            "date": first_nonblank(r.get("date_latest"), r.get("date_prev")),
            "week": first_nonblank(r.get("week_latest"), r.get("week_prev")),
            "away_team": first_nonblank(r.get("away_team_latest"), r.get("away_team_prev")),
            "home_team": first_nonblank(r.get("home_team_latest"), r.get("home_team_prev")),
        }

        # If no previous published row, we can later report "New Line".
        if pd.isna(r.get("source_prev")):
            continue

        sp_prev = num(r.get("market_spread_home_prev"))
        sp_latest = num(r.get("market_spread_home_latest"))
        sp_price_prev = fmt_price(r.get("market_spread_price_prev"))
        sp_price_latest = fmt_price(r.get("market_spread_price_latest"))
        sp_book = first_nonblank(r.get("market_spread_book_latest"), r.get("market_spread_book_prev"))

        if sp_prev is not None and sp_latest is not None:
            line_changed = abs(sp_latest - sp_prev) > 0.0001
            sp_price_delta = abs((num(sp_price_latest) or 0) - (num(sp_price_prev) or 0)) if sp_price_prev and sp_price_latest else 0
            price_changed = sp_price_prev != sp_price_latest and sp_price_delta >= 10
            source_changed = norm_text(r.get("source_prev")) != norm_text(r.get("source_latest"))

            if line_changed or price_changed:
                row = {
                    **base,
                    "market": "Spread",
                    "book": sp_book,
                    "previous": fmt_line(sp_prev),
                    "latest": fmt_line(sp_latest),
                    "change": round(sp_latest - sp_prev, 2),
                    "previous_price": sp_price_prev,
                    "latest_price": sp_price_latest,
                }
                row["summary"] = (
                    f'{row["away_team"]} at {row["home_team"]} spread '
                    f'{row["previous"]} → {row["latest"]}'
                    f' ({row["source_prev"]} → {row["source_latest"]})'
                )
                rows.append(row)

        tot_prev = num(r.get("market_total_prev"))
        tot_latest = num(r.get("market_total_latest"))
        tot_price_prev = fmt_price(first_nonblank(r.get("market_total_over_price_prev"), r.get("market_total_under_price_prev")))
        tot_price_latest = fmt_price(first_nonblank(r.get("market_total_over_price_latest"), r.get("market_total_under_price_latest")))
        tot_book = first_nonblank(r.get("market_total_book_latest"), r.get("market_total_book_prev"))

        if tot_prev is not None and tot_latest is not None:
            line_changed = abs(tot_latest - tot_prev) > 0.0001
            tot_price_delta = abs((num(tot_price_latest) or 0) - (num(tot_price_prev) or 0)) if tot_price_prev and tot_price_latest else 0
            price_changed = tot_price_prev != tot_price_latest and tot_price_delta >= 10
            source_changed = norm_text(r.get("source_prev")) != norm_text(r.get("source_latest"))

            if line_changed or price_changed:
                row = {
                    **base,
                    "market": "Total",
                    "book": tot_book,
                    "previous": fmt_total(tot_prev),
                    "latest": fmt_total(tot_latest),
                    "change": round(tot_latest - tot_prev, 2),
                    "previous_price": tot_price_prev,
                    "latest_price": tot_price_latest,
                }
                row["summary"] = (
                    f'{row["away_team"]} at {row["home_team"]} total '
                    f'{row["previous"]} → {row["latest"]}'
                    f' ({row["source_prev"]} → {row["source_latest"]})'
                )
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
        print(out.head(60).to_string(index=False))

if __name__ == "__main__":
    main()
