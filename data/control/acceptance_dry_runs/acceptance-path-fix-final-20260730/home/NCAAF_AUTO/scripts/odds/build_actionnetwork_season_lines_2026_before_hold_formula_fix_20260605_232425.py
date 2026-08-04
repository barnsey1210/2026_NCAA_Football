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



def side_spread_text(team, line):
    if pd.isna(line):
        return ""
    line = float(line)
    if abs(line) < 0.0001:
        return f"{team} PK"
    sign = "+" if line > 0 else ""
    return f"{team} {sign}{fmt_point(line)}"


def american_implied_prob(price):
    try:
        p = float(price)
    except Exception:
        return None
    if pd.isna(p):
        return None
    if p > 0:
        return 100.0 / (p + 100.0)
    return abs(p) / (abs(p) + 100.0)


def adjust_prob_for_half_points(prob, half_points, direction):
    if prob is None or pd.isna(prob):
        return None

    # Conservative half-point adjustment used only to standardize different numbers.
    # This avoids overstating arbs/middles from unmatched spreads.
    bump = 0.015 * abs(float(half_points or 0))
    prob = float(prob)

    if direction == "worse":
        prob += bump
    elif direction == "better":
        prob -= bump

    return min(max(prob, 0.01), 0.99)


def standardized_spread_hold_pct(home_line, home_price, away_line, away_price):
    """
    Standardize best home and best away spread prices to the same spread number,
    then calculate hold.

    home_line is from home-team perspective.
    away_line is from away-team perspective.

    Negative hold = arb/+EV shopping signal.
    Positive hold = normal market hold.
    """
    try:
        h_line = float(home_line)
        a_line = float(away_line)
    except Exception:
        return None, None, None

    h_prob = american_implied_prob(home_price)
    a_prob = american_implied_prob(away_price)
    if h_prob is None or a_prob is None:
        return None, None, None

    # Away +10 equals home -10. Standardize to midpoint between home-line views.
    away_as_home_line = -a_line
    target_home_line = (h_line + away_as_home_line) / 2.0
    target_away_line = -target_home_line

    # Home bettor prefers larger home line.
    h_delta = target_home_line - h_line
    h_direction = "better" if h_delta > 0 else "worse" if h_delta < 0 else "same"
    h_half_points = abs(h_delta) / 0.5

    # Away bettor prefers larger away line.
    a_delta = target_away_line - a_line
    a_direction = "better" if a_delta > 0 else "worse" if a_delta < 0 else "same"
    a_half_points = abs(a_delta) / 0.5

    h_adj = adjust_prob_for_half_points(h_prob, h_half_points, h_direction)
    a_adj = adjust_prob_for_half_points(a_prob, a_half_points, a_direction)

    hold = round((h_adj + a_adj - 1.0) * 100.0, 2)
    return hold, round(target_home_line, 2), round(target_away_line, 2)


def hold_label(hold):
    if hold is None or pd.isna(hold):
        return ""
    return f"Hold {float(hold):+.1f}%"


def invalid_same_book_pair(home_line, away_line):
    """
    Only invalidates a same-book pair where both sides have the same nonzero sign.
    This does NOT invalidate cross-book both-underdog opportunities.
    """
    try:
        h = None if home_line is None or pd.isna(home_line) else float(home_line)
    except Exception:
        h = None
    try:
        a = None if away_line is None or pd.isna(away_line) else float(away_line)
    except Exception:
        a = None

    if h is None or a is None:
        return False
    if abs(h) < 0.0001 and abs(a) < 0.0001:
        return False
    return (h > 0 and a > 0) or (h < 0 and a < 0)


def choose_best_spread(spreads: pd.DataFrame, home_team: str, away_team: str) -> dict:
    if spreads.empty:
        return {}

    rows = []

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

        # Conservative validation: same book cannot have both sides with same nonzero sign.
        # Example invalid: Caesars home +10 and away +10.
        # Do not flip or invent; skip that sportsbook's spread pair.
        if invalid_same_book_pair(home_line, away_line):
            continue

        if home_line is None and away_line is not None:
            home_line = -away_line
        if away_line is None and home_line is not None:
            away_line = -home_line

        if home_line is None:
            continue

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
    opts["display_price_sort"] = pd.to_numeric(opts["display_price"], errors="coerce").fillna(-99999)

    # Generic display line = best favorite-side number/price.
    pick = opts.sort_values(
        ["display_rank", "display_price_sort", "book_priority"],
        ascending=[True, False, True]
    ).iloc[0]

    home_opts = opts[opts["home_price"].notna()].copy()
    away_opts = opts[opts["away_price"].notna()].copy()

    best_home = None
    if not home_opts.empty:
        # Home bettor prefers larger home line.
        home_opts["home_side_rank"] = pd.to_numeric(home_opts["home_line"], errors="coerce")
        home_opts["home_price_sort"] = pd.to_numeric(home_opts["home_price"], errors="coerce").fillna(-99999)
        best_home = home_opts.sort_values(
            ["home_side_rank", "home_price_sort", "book_priority"],
            ascending=[False, False, True]
        ).iloc[0]

    best_away = None
    if not away_opts.empty:
        # Away bettor prefers larger away line, not lower home_line after invalid pairs are removed.
        away_opts["away_side_rank"] = pd.to_numeric(away_opts["away_line"], errors="coerce")
        away_opts["away_price_sort"] = pd.to_numeric(away_opts["away_price"], errors="coerce").fillna(-99999)
        best_away = away_opts.sort_values(
            ["away_side_rank", "away_price_sort", "book_priority"],
            ascending=[False, False, True]
        ).iloc[0]

    out = {
        "market_spread_home": pick["home_line"],
        "market_spread_text": side_spread_text(home_team, pick["home_line"]),
        "market_spread_price": pick["display_price"],
        "market_spread_book": pick["book"],
        "market_spread_last_update": pick["last_update"],
        "market_spread_display_side": pick["display_side"],
        "market_spread_display_team": pick["display_team"],
    }

    if best_home is not None:
        out.update({
            "market_best_home_spread_home": best_home["home_line"],
            "market_best_home_spread_text": side_spread_text(home_team, best_home["home_line"]),
            "market_best_home_spread_price": best_home["home_price"],
            "market_best_home_spread_book": best_home["book"],
        })

    if best_away is not None:
        out.update({
            "market_best_away_spread_home": best_away["home_line"],
            "market_best_away_spread_text": side_spread_text(away_team, best_away["away_line"]),
            "market_best_away_spread_price": best_away["away_price"],
            "market_best_away_spread_book": best_away["book"],
        })

    if best_home is not None and best_away is not None:
        hold, target_home, target_away = standardized_spread_hold_pct(
            best_home["home_line"],
            best_home["home_price"],
            best_away["away_line"],
            best_away["away_price"],
        )
        if hold is not None:
            out["market_spread_hold_pct"] = hold
            out["market_spread_hold_label"] = hold_label(hold)
            out["market_spread_hold_home_line"] = target_home
            out["market_spread_hold_away_line"] = target_away

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





def is_known_bad_total_market(rec: dict) -> bool:
    """
    Known false/stale totals from source feeds that should not be exported
    as posted market totals.

    Keep this list intentionally small. These are not model opinions;
    these are source-data validation exclusions.
    """
    away = str(rec.get("away_team", "")).strip().lower()
    home = str(rec.get("home_team", "")).strip().lower()

    # Action Network/FanDuel false total: this 58.5 is not actually posted yet.
    if away == "north alabama" and home == "arkansas":
        return True

    return False


def clear_total_fields(rec: dict) -> None:
    """
    Remove all full-game total fields from a record while preserving spread data.
    """
    total_fields = [
        "market_total",
        "market_total_open",
        "market_total_book",
        "market_total_over_price",
        "market_total_under_price",
        "market_total_last_update",
        "market_best_over_total",
        "market_best_over_price",
        "market_best_over_book",
        "market_best_under_total",
        "market_best_under_price",
        "market_best_under_book",
    ]
    for k in total_fields:
        rec[k] = None

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

        if is_known_bad_total_market(rec):
            clear_total_fields(rec)

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
