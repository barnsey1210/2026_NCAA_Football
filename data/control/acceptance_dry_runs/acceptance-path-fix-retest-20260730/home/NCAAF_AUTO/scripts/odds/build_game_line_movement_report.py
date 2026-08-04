#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import math

HIST = Path("data/odds/game_line_history.csv")
OUT = Path("data/odds/game_line_movement_report.csv")

def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None

def fmt_line(x):
    v = num(x)
    if v is None:
        return ""
    if abs(v) == int(abs(v)):
        return f"{v:+.0f}"
    return f"{v:+.1f}"

def fmt_total(x):
    v = num(x)
    if v is None:
        return ""
    if abs(v) == int(abs(v)):
        return f"{v:.0f}"
    return f"{v:.1f}"

def fmt_odds(x):
    v = num(x)
    if v is None:
        return ""
    v = int(v)
    return f"+{v}" if v > 0 else str(v)

def changed(a, b):
    av = num(a)
    bv = num(b)
    if av is None or bv is None:
        return False
    return av != bv

def add_row(rows, prev, cur, market, book, previous, latest, change, previous_price="", latest_price=""):
    away = cur.get("away_team", "")
    home = cur.get("home_team", "")
    game = f"{away} at {home}".strip(" at ")

    if market == "Spread":
        summary = f"{game} spread {fmt_line(previous)} → {fmt_line(latest)} at {book}"
    elif market == "Total":
        summary = f"{game} total {fmt_total(previous)} → {fmt_total(latest)} at {book}"
    elif market == "Total Over Price":
        summary = f"{game} total over price {fmt_odds(previous)} → {fmt_odds(latest)} at {book}"
    elif market == "Total Under Price":
        summary = f"{game} total under price {fmt_odds(previous)} → {fmt_odds(latest)} at {book}"
    else:
        summary = f"{game} {market} {previous} → {latest} at {book}"

    rows.append({
        "snapshot_prev": prev.get("_snapshot_label", prev.get("_snapshot_key", prev.get("snapshot_date", ""))),
        "snapshot_latest": cur.get("_snapshot_label", cur.get("_snapshot_key", cur.get("snapshot_date", ""))),
        "source_prev": prev.get("source", ""),
        "source_latest": cur.get("source", ""),
        "game_id": cur.get("game_id", ""),
        "date": cur.get("date", ""),
        "week": cur.get("week", ""),
        "away_team": away,
        "home_team": home,
        "market": market,
        "book": book,
        "previous": previous,
        "latest": latest,
        "change": change,
        "previous_price": previous_price,
        "latest_price": latest_price,
        "summary": summary,
    })

def main():
    if not HIST.exists():
        raise SystemExit(f"Missing {HIST}")

    h = pd.read_csv(HIST)
    if h.empty:
        pd.DataFrame().to_csv(OUT, index=False)
        print(f"Wrote empty {OUT}")
        return

    # Use snapshot_date for grouping because older rows may not have a unique snapshot_ts.
    # Keep snapshot_ts as display label when available.
    h["_snapshot_key"] = h["snapshot_date"].astype(str)
    h["_snapshot_label"] = h.get("snapshot_ts")
    h["_snapshot_label"] = h["_snapshot_label"].where(
        h["_snapshot_label"].notna() & h["_snapshot_label"].astype(str).ne(""),
        h["_snapshot_key"]
    )

    h["_snapshot_dt"] = pd.to_datetime(h["_snapshot_key"], utc=True, errors="coerce")
    h = h[h["_snapshot_dt"].notna()].copy()

    snaps = h[["_snapshot_key", "_snapshot_dt"]].drop_duplicates().sort_values("_snapshot_dt")
    if len(snaps) < 2:
        raise SystemExit("Need at least two game-line snapshots to build movement report")

    prev_key = snaps.iloc[-2]["_snapshot_key"]
    latest_key = snaps.iloc[-1]["_snapshot_key"]

    prev_df = h[h["_snapshot_key"].eq(prev_key)].drop_duplicates(subset=["game_id"], keep="last").set_index("game_id")
    cur_df = h[h["_snapshot_key"].eq(latest_key)].drop_duplicates(subset=["game_id"], keep="last").set_index("game_id")

    rows = []
    for gid in sorted(set(prev_df.index).intersection(set(cur_df.index))):
        prev = prev_df.loc[gid]
        cur = cur_df.loc[gid]

        if changed(prev.get("market_spread_home"), cur.get("market_spread_home")):
            pv = num(prev.get("market_spread_home"))
            cv = num(cur.get("market_spread_home"))
            add_row(
                rows, prev, cur,
                market="Spread",
                book=cur.get("market_spread_book", ""),
                previous=pv,
                latest=cv,
                change=cv - pv,
                previous_price=prev.get("market_spread_price", ""),
                latest_price=cur.get("market_spread_price", ""),
            )

        if changed(prev.get("market_total"), cur.get("market_total")):
            pv = num(prev.get("market_total"))
            cv = num(cur.get("market_total"))
            add_row(
                rows, prev, cur,
                market="Total",
                book=cur.get("market_total_book", ""),
                previous=pv,
                latest=cv,
                change=cv - pv,
            )

        if changed(prev.get("market_total_over_price"), cur.get("market_total_over_price")):
            pv = num(prev.get("market_total_over_price"))
            cv = num(cur.get("market_total_over_price"))
            add_row(
                rows, prev, cur,
                market="Total Over Price",
                book=cur.get("market_total_book", ""),
                previous=pv,
                latest=cv,
                change=cv - pv,
            )

        if changed(prev.get("market_total_under_price"), cur.get("market_total_under_price")):
            pv = num(prev.get("market_total_under_price"))
            cv = num(cur.get("market_total_under_price"))
            add_row(
                rows, prev, cur,
                market="Total Under Price",
                book=cur.get("market_total_book", ""),
                previous=pv,
                latest=cv,
                change=cv - pv,
            )

    out = pd.DataFrame(rows)
    if not out.empty:
        out["abs_change"] = pd.to_numeric(out["change"], errors="coerce").abs()
        out = out.sort_values(["market", "abs_change"], ascending=[True, False]).drop(columns=["abs_change"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print(f"Wrote {OUT}: {len(out)} rows")
    if not out.empty:
        print(out["market"].value_counts().to_string())
        print(out[["away_team","home_team","market","book","previous","latest","change","summary"]].head(40).to_string(index=False))

if __name__ == "__main__":
    main()
