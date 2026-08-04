import pandas as pd
from pathlib import Path

IN = Path("data/odds/game_line_history.csv")
OUT = Path("data/odds/game_line_movement_report.csv")

if not IN.exists():
    raise SystemExit(f"Missing {IN}")

df = pd.read_csv(IN)
df.columns = [str(c).strip() for c in df.columns]

if df.empty:
    pd.DataFrame().to_csv(OUT, index=False)
    print(f"Wrote empty {OUT}")
    raise SystemExit()

for c in ["snapshot_date", "game_date", "away_team", "home_team", "source", "market_spread_book", "market_total_book"]:
    if c in df.columns:
        df[c] = df[c].fillna("").astype(str)

def as_num(v):
    try:
        if pd.isna(v) or str(v).strip() == "":
            return None
        return float(v)
    except Exception:
        return None

def fmt(v):
    n = as_num(v)
    if n is None:
        return ""
    return int(n) if float(n).is_integer() else n

def add_report(out, base, market, field, book, open_val, prev_val, latest_val, open_date, prev_date, latest_date):
    open_n = as_num(open_val)
    prev_n = as_num(prev_val)
    latest_n = as_num(latest_val)

    if open_n is None or latest_n is None:
        return

    move_open = latest_n - open_n
    move_prev = None if prev_n is None else latest_n - prev_n

    if move_open == 0 and (move_prev is None or move_prev == 0):
        return

    out.append({
        "snapshot_latest": latest_date,
        "open_date": open_date,
        "previous_date": prev_date or "",
        "game_date": base.get("game_date", ""),
        "week": base.get("week", ""),
        "away_team": base.get("away_team", ""),
        "home_team": base.get("home_team", ""),
        "source": base.get("source", ""),
        "market": market,
        "field": field,
        "book": book or "",
        "open": fmt(open_n),
        "previous": "" if prev_n is None else fmt(prev_n),
        "latest": fmt(latest_n),
        "move_from_open": fmt(move_open),
        "move_from_previous": "" if move_prev is None else fmt(move_prev),
        "summary": f"{base.get('away_team','')} at {base.get('home_team','')} {book or ''} {field} moved {fmt(open_n)} → {fmt(latest_n)}"
    })

reports = []
game_key_cols = ["game_date", "away_team", "home_team", "source"]

for _, g in df.groupby(game_key_cols, dropna=False):
    g = g.sort_values("snapshot_date").copy()

    dates = sorted(g["snapshot_date"].dropna().astype(str).unique())
    if not dates:
        continue

    open_date = dates[0]
    latest_date = dates[-1]
    prev_date = dates[-2] if len(dates) >= 2 else ""

    open_rows = g[g["snapshot_date"] == open_date]
    latest_rows = g[g["snapshot_date"] == latest_date]
    prev_rows = g[g["snapshot_date"] == prev_date] if prev_date else pd.DataFrame()

    # Compare selected spread row by book when possible.
    for _, lr in latest_rows.iterrows():
        spread_book = str(lr.get("market_spread_book", "") or "")
        total_book = str(lr.get("market_total_book", "") or "")

        if spread_book:
            o = open_rows[open_rows["market_spread_book"].astype(str) == spread_book]
            p = prev_rows[prev_rows["market_spread_book"].astype(str) == spread_book] if not prev_rows.empty else pd.DataFrame()
        else:
            o = open_rows
            p = prev_rows

        orow = o.iloc[-1] if not o.empty else open_rows.iloc[0]
        prow = p.iloc[-1] if not p.empty else None

        add_report(
            reports, lr, "Spread", "home spread", spread_book,
            orow.get("market_spread_home"),
            None if prow is None else prow.get("market_spread_home"),
            lr.get("market_spread_home"),
            open_date, prev_date, latest_date
        )

        add_report(
            reports, lr, "Spread Price", "spread price", spread_book,
            orow.get("market_spread_price"),
            None if prow is None else prow.get("market_spread_price"),
            lr.get("market_spread_price"),
            open_date, prev_date, latest_date
        )

        if total_book:
            o = open_rows[open_rows["market_total_book"].astype(str) == total_book]
            p = prev_rows[prev_rows["market_total_book"].astype(str) == total_book] if not prev_rows.empty else pd.DataFrame()
        else:
            o = open_rows
            p = prev_rows

        if not o.empty:
            orow = o.iloc[-1]
        if not p.empty:
            prow = p.iloc[-1]
        else:
            prow = None

        add_report(
            reports, lr, "Total", "game total", total_book,
            orow.get("market_total"),
            None if prow is None else prow.get("market_total"),
            lr.get("market_total"),
            open_date, prev_date, latest_date
        )

out = pd.DataFrame(reports)

if not out.empty:
    out = out.sort_values(
        ["snapshot_latest", "game_date", "market", "away_team", "home_team"],
        ascending=[False, True, True, True, True]
    )

OUT.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT, index=False)

print(f"Wrote {OUT}: {len(out)} movement rows")
