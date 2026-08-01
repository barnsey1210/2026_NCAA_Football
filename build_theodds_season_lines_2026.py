#!/usr/bin/env python3
import re
import unicodedata
from pathlib import Path

import pandas as pd

IN = Path("data/odds/theodds_ncaaf_lines_2026.csv")
OUT = Path("data/odds/theodds_season_game_lines_2026.csv")
AUDIT = Path("data/odds/theodds_season_game_lines_2026_audit.csv")

OUT.parent.mkdir(parents=True, exist_ok=True)

def strip_accents(s):
    return "".join(ch for ch in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(ch))

def norm_team(s):
    s = strip_accents(str(s or "").lower())
    s = re.sub(r"\b(eagles|hornets|wolfpack|cavaliers|tigers|bulldogs|wildcats|cardinals|aggies|rebels|buckeyes|longhorns|wolverines|spartans|huskies|cougars|bears|baylor bears|auburn tigers)\b", " ", s)
    s = re.sub(r"\b(university|college|the|of|at)\b", " ", s)
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def clean_team_display(s):
    # Remove common nickname suffixes The Odds API includes.
    s = str(s or "").strip()
    suffixes = [
        " Eagles", " Hornets", " Wolfpack", " Cavaliers", " Tigers", " Bulldogs", " Wildcats",
        " Cardinals", " Aggies", " Rebels", " Buckeyes", " Longhorns", " Wolverines",
        " Spartans", " Huskies", " Cougars", " Bears", " Ducks", " Trojans", " Gators",
        " Seminoles", " Hawkeyes", " Fighting Irish", " Badgers", " Nittany Lions"
    ]
    for suf in suffixes:
        if s.endswith(suf):
            return s[:-len(suf)].strip()
    return s

def fmt_spread(team, point):
    if pd.isna(point):
        return ""
    point = float(point)
    if point == 0:
        return f"{team} PK"
    return f"{team} {point:+g}".replace("+", "+")

def pick_primary_book(rows):
    # Preferred display order for the current site. We still keep books_available.
    pref = ["DraftKings", "FanDuel", "BetMGM", "BetRivers", "Bovada", "BetOnline.ag", "LowVig.ag", "MyBookie.ag"]
    for b in pref:
        sub = rows[rows["book"].eq(b)]
        if not sub.empty:
            return sub.iloc[0]
    return rows.iloc[0]

if not IN.exists():
    raise SystemExit(f"Missing {IN}. Run pull_theodds_ncaaf_lines_2026.py first.")

df = pd.read_csv(IN)
if df.empty:
    pd.DataFrame().to_csv(OUT, index=False)
    raise SystemExit(f"{IN} is empty.")

df["date"] = pd.to_datetime(df["commence_time"], errors="coerce").dt.strftime("%Y-%m-%d")
df["away_clean"] = df["away_team"].map(clean_team_display)
df["home_clean"] = df["home_team"].map(clean_team_display)

out = []
audit = []

for (game_id, away, home, date), g in df.groupby(["game_id", "away_clean", "home_clean", "date"], dropna=False):
    books = ",".join(sorted(g["book"].dropna().unique()))

    spread_rows = g[g["market"].eq("spreads")].copy()
    total_rows = g[g["market"].eq("totals")].copy()

    rec = {
        "source": "The Odds API",
        "game_id": game_id,
        "date": date,
        "away_team": away,
        "home_team": home,
        "away_norm": norm_team(away),
        "home_norm": norm_team(home),
        "books_available": books,
        "books_count": len([b for b in books.split(",") if b]),
        "market_line_source": "The Odds API",
        "market_price_status": "actual",
    }

    # Display spread: use preferred book's home side, converted to home spread.
    if not spread_rows.empty:
        spread_rows["side_clean"] = spread_rows["side"].map(clean_team_display)
        home_side = spread_rows[spread_rows["side_clean"].map(norm_team).eq(norm_team(home))]
        if not home_side.empty:
            r = pick_primary_book(home_side)
            home_point = float(r["point"])
            rec.update({
                "market_spread_home": home_point,
                "market_spread_text": fmt_spread(home, home_point),
                "market_spread_price": r["price"],
                "market_spread_book": r["book"],
                "market_spread_last_update": r.get("last_update"),
            })

    # Display total: use preferred book total pair.
    if not total_rows.empty:
        # Prefer books where both Over and Under exist at same point.
        chosen = None
        for book, bdf in total_rows.groupby("book"):
            if {"Over", "Under"}.issubset(set(bdf["side"])):
                chosen = bdf
                break
        if chosen is None:
            chosen = total_rows

        # Apply preferred book order.
        chosen_book_row = pick_primary_book(chosen)
        book = chosen_book_row["book"]
        bdf = total_rows[total_rows["book"].eq(book)]
        over = bdf[bdf["side"].eq("Over")]
        under = bdf[bdf["side"].eq("Under")]
        point = chosen_book_row["point"]

        rec.update({
            "market_total": point,
            "market_total_book": book,
            "market_total_over_price": over.iloc[0]["price"] if not over.empty else None,
            "market_total_under_price": under.iloc[0]["price"] if not under.empty else None,
            "market_total_last_update": chosen_book_row.get("last_update"),
        })

    out.append(rec)
    audit.append({
        "game_id": game_id,
        "date": date,
        "away_team": away,
        "home_team": home,
        "books_count": rec["books_count"],
        "has_spread": "market_spread_home" in rec,
        "has_total": "market_total" in rec,
    })

out_df = pd.DataFrame(out).sort_values(["date", "away_team", "home_team"])
audit_df = pd.DataFrame(audit).sort_values(["date", "away_team", "home_team"])

out_df.to_csv(OUT, index=False)
audit_df.to_csv(AUDIT, index=False)

print(f"Wrote {OUT}: {len(out_df):,} games")
print(f"Wrote {AUDIT}: {len(audit_df):,} games")

print("\nCoverage:")
print("games with spread:", int(out_df.get("market_spread_home", pd.Series()).notna().sum()) if "market_spread_home" in out_df else 0)
print("games with total:", int(out_df.get("market_total", pd.Series()).notna().sum()) if "market_total" in out_df else 0)

print("\nSample:")
cols = [c for c in [
    "date", "away_team", "home_team", "market_spread_text", "market_spread_price",
    "market_spread_book", "market_total", "market_total_over_price",
    "market_total_under_price", "market_total_book", "books_available"
] if c in out_df.columns]
print(out_df[cols].head(30).to_string(index=False))
