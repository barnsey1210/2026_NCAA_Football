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



def price_num(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def better_price(a, b):
    """
    Higher American price is better for the bettor.
    Examples: +105 beats -110; -105 beats -115.
    """
    an = price_num(a)
    bn = price_num(b)
    if an is None:
        return False
    if bn is None:
        return True
    return an > bn


def spread_display_rank(home_line):
    """
    For the generic Market Spread display, rank by the favorite's best bettable number.
    Home perspective:
      home_line < 0 => home favored, better is closer to 0: -6.5 beats -7.5
      home_line > 0 => away favored, better is closer to 0: +6.5 beats +7.5
      0 => pick'em
    """
    try:
        return abs(float(home_line))
    except Exception:
        return 9999


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
    # Also keep side-specific best prices so Market Lab can later choose the side the model likes.
    for book, g in spreads.groupby("book"):
        home = g[g["side"].astype(str).eq("home")]
        away = g[g["side"].astype(str).eq("away")]

        if home.empty and away.empty:
            continue

        home_line = None
        away_line = None
        home_price = None
        away_price = None
        last_update = None

        if not home.empty:
            r_home = home.sort_values("price", ascending=False).iloc[0]
            home_line = float(r_home["point"])
            home_price = r_home["price"]
            last_update = r_home.get("pulled_at")

        if not away.empty:
            r_away = away.sort_values("price", ascending=False).iloc[0]
            away_line = float(r_away["point"])
            away_price = r_away["price"]
            last_update = last_update or r_away.get("pulled_at")

        # If one side is missing, infer the home-perspective spread from the other side.
        if home_line is None and away_line is not None:
            home_line = -away_line
        if away_line is None and home_line is not None:
            away_line = -home_line

        if home_line is None:
            continue

        # Display price should correspond to the favorite side.
        # home_line < 0 means home is favored; home_line > 0 means away is favored.
        if abs(home_line) < 0.0001:
            display_price = home_price if better_price(home_price, away_price) else away_price
            display_side = "pick"
            display_team = "Pick"
        elif home_line < 0:
            display_price = home_price
            display_side = "home"
            display_team = home_team
        else:
            display_price = away_price
            display_side = "away"
            display_team = away_team

        rows.append({
            "book": book,
            "book_priority": BOOK_PRIORITY.get(book, 99),
            "home_line": home_line,
            "away_line": away_line,
            "home_price": home_price,
            "away_price": away_price,
            "display_price": display_price,
            "display_side": display_side,
            "display_team": display_team,
            "last_update": last_update,
            "display_rank": spread_display_rank(home_line),
        })

    if not rows:
        return {}

    opts = pd.DataFrame(rows)

    # Best generic display line = best favorite-side number, then best favorite price, then book priority.
    opts["display_price_sort"] = pd.to_numeric(opts["display_price"], errors="coerce").fillna(-99999)
    pick = opts.sort_values(
        ["display_rank", "display_price_sort", "book_priority"],
        ascending=[True, False, True]
    ).iloc[0]

    # Best home-side and away-side bettable options for side-aware Market Lab use later.
    home_opts = opts[opts["home_price"].notna()].copy()
    away_opts = opts[opts["away_price"].notna()].copy()

    best_home = None
    if not home_opts.empty:
        # For a home-side bet, more points are better if home is underdog; fewer points to lay are better if home is favorite.
        # In home-perspective terms, larger home_line is generally better for betting home.
        home_opts["home_side_rank"] = pd.to_numeric(home_opts["home_line"], errors="coerce")
        home_opts["home_price_sort"] = pd.to_numeric(home_opts["home_price"], errors="coerce").fillna(-99999)
        best_home = home_opts.sort_values(
            ["home_side_rank", "home_price_sort", "book_priority"],
            ascending=[False, False, True]
        ).iloc[0]

    best_away = None
    if not away_opts.empty:
        # For an away-side bet, lower home_line is generally better because it means away gets more points or lays fewer.
        away_opts["away_side_rank"] = pd.to_numeric(away_opts["home_line"], errors="coerce")
        away_opts["away_price_sort"] = pd.to_numeric(away_opts["away_price"], errors="coerce").fillna(-99999)
        best_away = away_opts.sort_values(
            ["away_side_rank", "away_price_sort", "book_priority"],
            ascending=[True, False, True]
        ).iloc[0]

    out = {
        "market_spread_home": pick["home_line"],
        "market_spread_text": spread_text(home_team, pick["home_line"]),
        "market_spread_price": pick["display_price"],
        "market_spread_book": pick["book"],
        "market_spread_last_update": pick["last_update"],
        "market_spread_display_side": pick["display_side"],
        "market_spread_display_team": pick["display_team"],
    }

    if best_home is not None:
        out.update({
            "market_best_home_spread_home": best_home["home_line"],
            "market_best_home_spread_text": spread_text(home_team, best_home["home_line"]),
            "market_best_home_spread_price": best_home["home_price"],
            "market_best_home_spread_book": best_home["book"],
        })

    if best_away is not None:
        out.update({
            "market_best_away_spread_home": best_away["home_line"],
            "market_best_away_spread_text": spread_text(home_team, best_away["home_line"]),
            "market_best_away_spread_price": best_away["away_price"],
            "market_best_away_spread_book": best_away["book"],
        })

    return out




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
            r = over.sort_values("price", ascending=False).iloc[0]
            point = r["point"]
            over_price = r["price"]
            last_update = r.get("pulled_at")

        if not under.empty:
            r = under.sort_values("price", ascending=False).iloc[0]
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

    # Generic total display remains stable by preferred book, but store side-specific best prices.
    pick = opts.sort_values(["book_priority"]).iloc[0]

    over_opts = opts[opts["over_price"].notna()].copy()
    under_opts = opts[opts["under_price"].notna()].copy()

    best_over = None
    if not over_opts.empty:
        # Over bettor wants lowest total, then best price.
        over_opts["total_sort"] = pd.to_numeric(over_opts["total"], errors="coerce")
        over_opts["price_sort"] = pd.to_numeric(over_opts["over_price"], errors="coerce").fillna(-99999)
        best_over = over_opts.sort_values(
            ["total_sort", "price_sort", "book_priority"],
            ascending=[True, False, True]
        ).iloc[0]

    best_under = None
    if not under_opts.empty:
        # Under bettor wants highest total, then best price.
        under_opts["total_sort"] = pd.to_numeric(under_opts["total"], errors="coerce")
        under_opts["price_sort"] = pd.to_numeric(under_opts["under_price"], errors="coerce").fillna(-99999)
        best_under = under_opts.sort_values(
            ["total_sort", "price_sort", "book_priority"],
            ascending=[False, False, True]
        ).iloc[0]

    out = {
        "market_total": pick["total"],
        "market_total_book": pick["book"],
        "market_total_over_price": pick["over_price"],
        "market_total_under_price": pick["under_price"],
        "market_total_last_update": pick["last_update"],
    }

    if best_over is not None:
        out.update({
            "market_best_over_total": best_over["total"],
            "market_best_over_price": best_over["over_price"],
            "market_best_over_book": best_over["book"],
        })

    if best_under is not None:
        out.update({
            "market_best_under_total": best_under["total"],
            "market_best_under_price": best_under["under_price"],
            "market_best_under_book": best_under["book"],
        })

    return out




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
            "market_best_home_spread_text", "market_best_home_spread_price", "market_best_home_spread_book",
            "market_best_away_spread_text", "market_best_away_spread_price", "market_best_away_spread_book",
            "market_total", "market_total_over_price", "market_total_under_price", "market_total_book",
            "market_best_over_total", "market_best_over_price", "market_best_over_book",
            "market_best_under_total", "market_best_under_price", "market_best_under_book",
            "books_available"
        ]
        print(out[cols].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
