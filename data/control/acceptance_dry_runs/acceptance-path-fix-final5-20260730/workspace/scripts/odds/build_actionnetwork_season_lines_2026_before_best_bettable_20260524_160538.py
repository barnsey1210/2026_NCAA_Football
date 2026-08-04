#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

RAW = Path("data/odds/actionnetwork_ncaaf_game_lines_2026.csv")
OUT = Path("data/odds/actionnetwork_season_game_lines_2026.csv")

BOOK_PRIORITY = {
    "Caesars": 1,
    "DraftKings": 2,
    "FanDuel": 3,
    "BetMGM": 4,
}


def norm_team(v):
    s = "" if pd.isna(v) else str(v).strip().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(university|college|the|of|at)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def num(x):
    return pd.to_numeric(x, errors="coerce")


def fmt_point(x):
    if pd.isna(x):
        return ""
    x = float(x)
    return f"{x:.1f}".rstrip("0").rstrip(".")


def fmt_price(x):
    if pd.isna(x):
        return ""
    return f"{int(float(x)):+d}"


def spread_text(home_team, home_line):
    if pd.isna(home_line):
        return ""
    home_line = float(home_line)
    if abs(home_line) < 0.0001:
        return f"{home_team} PK"
    return f"{home_team} {fmt_point(home_line)}"


def choose_best_spread(spreads: pd.DataFrame, home_team: str, away_team: str) -> dict:
    if spreads.empty:
        return {}

    rows = []

    # We store market_spread_home from home-team perspective.
    for book, g in spreads.groupby("book"):
        home = g[g["side"].astype(str).eq("home")]
        away = g[g["side"].astype(str).eq("away")]

        if home.empty and away.empty:
            continue

        if not home.empty:
            r = home.iloc[0]
            home_line = float(r["point"])
            home_price = r["price"]
        else:
            r = away.iloc[0]
            home_line = -float(r["point"])
            home_price = None

        rows.append({
            "book": book,
            "book_priority": BOOK_PRIORITY.get(book, 99),
            "home_line": home_line,
            "price": home_price,
            "last_update": r.get("pulled_at"),
        })

    if not rows:
        return {}

    opts = pd.DataFrame(rows)

    # Current simple choice: prefer best book priority among actionable lines.
    # Later we can choose by no-vig/value side. For display, stable known book priority is cleaner.
    pick = opts.sort_values(["book_priority"]).iloc[0]

    return {
        "market_spread_home": pick["home_line"],
        "market_spread_text": spread_text(home_team, pick["home_line"]),
        "market_spread_price": pick["price"],
        "market_spread_book": pick["book"],
        "market_spread_last_update": pick["last_update"],
    }


def choose_best_total(totals: pd.DataFrame) -> dict:
    if totals.empty:
        return {}

    rows = []
    for book, g in totals.groupby("book"):
        over = g[g["side"].astype(str).str.lower().eq("over")]
        under = g[g["side"].astype(str).str.lower().eq("under")]
        if over.empty and under.empty:
            continue

        point = None
        over_price = None
        under_price = None
        last_update = None

        if not over.empty:
            r = over.iloc[0]
            point = r["point"]
            over_price = r["price"]
            last_update = r.get("pulled_at")

        if not under.empty:
            r = under.iloc[0]
            point = point if pd.notna(point) else r["point"]
            under_price = r["price"]
            last_update = last_update or r.get("pulled_at")

        rows.append({
            "book": book,
            "book_priority": BOOK_PRIORITY.get(book, 99),
            "total": point,
            "over_price": over_price,
            "under_price": under_price,
            "last_update": last_update,
        })

    if not rows:
        return {}

    opts = pd.DataFrame(rows)
    pick = opts.sort_values(["book_priority"]).iloc[0]

    return {
        "market_total": pick["total"],
        "market_total_book": pick["book"],
        "market_total_over_price": pick["over_price"],
        "market_total_under_price": pick["under_price"],
        "market_total_last_update": pick["last_update"],
    }


def main() -> None:
    if not RAW.exists():
        raise SystemExit(f"Missing {RAW}. Run pull_actionnetwork_ncaaf_game_lines_2026.py first.")

    df = pd.read_csv(RAW)
    if df.empty:
        raise SystemExit(f"{RAW} is empty.")

    df.columns = [str(c).strip() for c in df.columns]
    df["point"] = num(df["point"])
    df["price"] = num(df["price"])
    df["date"] = df["date"].astype(str).str[:10]
    df["away_norm"] = df["away_team"].map(norm_team)
    df["home_norm"] = df["home_team"].map(norm_team)

    rows = []

    group_cols = ["game_id", "date", "week", "away_team", "home_team", "away_norm", "home_norm"]

    for keys, g in df.groupby(group_cols, dropna=False):
        rec = dict(zip(group_cols, keys))

        spreads = g[g["market"].eq("spread")].copy()
        totals = g[g["market"].eq("total")].copy()

        rec.update(choose_best_spread(spreads, rec["home_team"], rec["away_team"]))
        rec.update(choose_best_total(totals))

        books = sorted(set(g["book"].dropna().astype(str)))
        rec["source"] = "Action Network"
        rec["books_available"] = ",".join(books)
        rec["books_count"] = len(books)
        rec["market_line_source"] = "Action Network"
        rec["market_price_status"] = "actual"

        if rec.get("market_spread_home") is not None or rec.get("market_total") is not None:
            rows.append(rec)

    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print(f"Wrote {OUT}: rows={len(out):,}")
    if not out.empty:
        print("\nBy week:")
        print(out.groupby("week").size().to_string())
        print("\nSpread books:")
        print(out["market_spread_book"].value_counts(dropna=False).to_string())
        print("\nTotal books:")
        print(out["market_total_book"].value_counts(dropna=False).to_string())
        print("\nSample:")
        cols = [
            "week", "date", "away_team", "home_team",
            "market_spread_text", "market_spread_price", "market_spread_book",
            "market_total", "market_total_over_price", "market_total_under_price", "market_total_book",
            "books_available"
        ]
        print(out[cols].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
