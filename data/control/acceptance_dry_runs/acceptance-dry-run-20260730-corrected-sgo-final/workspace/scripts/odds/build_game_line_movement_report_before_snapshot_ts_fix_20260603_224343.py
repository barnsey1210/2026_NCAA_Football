import pandas as pd
from pathlib import Path

IN = Path("data/odds/game_line_history.csv")
OUT = Path("data/odds/game_line_movement_report.csv")

REPORT_COLS = [
    "snapshot_latest",
    "open_date",
    "previous_date",
    "game_date",
    "week",
    "away_team",
    "home_team",
    "source",
    "market",
    "field",
    "book",
    "open",
    "previous",
    "latest",
    "move_from_open",
    "move_from_previous",
    "summary",
]

if not IN.exists():
    pd.DataFrame(columns=REPORT_COLS).to_csv(OUT, index=False)
    raise SystemExit(f"Missing {IN}; wrote empty {OUT}")

df = pd.read_csv(IN)
df.columns = [str(c).strip() for c in df.columns]

if df.empty:
    pd.DataFrame(columns=REPORT_COLS).to_csv(OUT, index=False)
    print(f"Wrote empty {OUT}")
    raise SystemExit()

# Support either schema: older uses date, newer may use game_date.
if "game_date" not in df.columns or df["game_date"].isna().all():
    if "date" in df.columns:
        df["game_date"] = df["date"].astype(str).str[:10]
    else:
        df["game_date"] = ""

for c in [
    "snapshot_date", "game_date", "away_team", "home_team", "source",
    "market_spread_book", "market_total_book", "week"
]:
    if c not in df.columns:
        df[c] = ""
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
    return int(n) if float(n).is_integer() else round(float(n), 3)

def add_report(out, base, market, field, book, open_val, prev_val, latest_val, open_date, prev_date, latest_date):
    open_n = as_num(open_val)
    prev_n = as_num(prev_val)
    latest_n = as_num(latest_val)

    if open_n is None or latest_n is None:
        return

    move_open = latest_n - open_n
    move_prev = None if prev_n is None else latest_n - prev_n

    if abs(move_open) < 1e-9 and (move_prev is None or abs(move_prev) < 1e-9):
        return

    away = str(base.get("away_team", "") or "")
    home = str(base.get("home_team", "") or "")
    bk = str(book or "")

    out.append({
        "snapshot_latest": latest_date,
        "open_date": open_date,
        "previous_date": prev_date or "",
        "game_date": str(base.get("game_date", "") or ""),
        "week": str(base.get("week", "") or ""),
        "away_team": away,
        "home_team": home,
        "source": str(base.get("source", "") or ""),
        "market": market,
        "field": field,
        "book": bk,
        "open": fmt(open_n),
        "previous": "" if prev_n is None else fmt(prev_n),
        "latest": fmt(latest_n),
        "move_from_open": fmt(move_open),
        "move_from_previous": "" if move_prev is None else fmt(move_prev),
        "summary": f"{away} at {home} {bk} {field} moved {fmt(open_n)} → {fmt(latest_n)}"
    })

reports = []

# Group by source too, because Action and The Odds can have different selected lines/books.
game_key_cols = ["game_date", "away_team", "home_team", "source"]

for _, g in df.groupby(game_key_cols, dropna=False):
    g = g.sort_values("snapshot_date").copy()

    dates = sorted([d for d in g["snapshot_date"].dropna().astype(str).unique() if d])
    if len(dates) < 2:
        continue

    open_date = dates[0]
    latest_date = dates[-1]
    prev_date = dates[-2]

    open_rows = g[g["snapshot_date"] == open_date]
    latest_rows = g[g["snapshot_date"] == latest_date]
    prev_rows = g[g["snapshot_date"] == prev_date]

    for _, lr in latest_rows.iterrows():
        spread_book = str(lr.get("market_spread_book", "") or "")
        total_book = str(lr.get("market_total_book", "") or "")

        # Spread line/price comparisons by same selected book when possible.
        if spread_book:
            o = open_rows[open_rows["market_spread_book"].astype(str) == spread_book]
            p = prev_rows[prev_rows["market_spread_book"].astype(str) == spread_book]
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

        # Total comparisons by same selected total book when possible.
        if total_book:
            o = open_rows[open_rows["market_total_book"].astype(str) == total_book]
            p = prev_rows[prev_rows["market_total_book"].astype(str) == total_book]
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

out = pd.DataFrame(reports, columns=REPORT_COLS)

if not out.empty:
    out = out.sort_values(
        ["snapshot_latest", "game_date", "market", "away_team", "home_team"],
        ascending=[False, True, True, True, True]
    )

OUT.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT, index=False)

print(f"Wrote {OUT}: {len(out)} movement rows")
