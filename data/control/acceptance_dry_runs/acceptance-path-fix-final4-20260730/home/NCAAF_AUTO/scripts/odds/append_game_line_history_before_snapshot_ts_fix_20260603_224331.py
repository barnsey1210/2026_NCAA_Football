import pandas as pd
from pathlib import Path
from datetime import date

OUT = Path("data/odds/game_line_history.csv")
RUN_DATE = date.today().isoformat()

SOURCES = [
    ("Action Network", Path("data/odds/actionnetwork_season_game_lines_2026.csv")),
    ("The Odds API", Path("data/odds/theodds_season_game_lines_2026.csv")),
]

def clean(v):
    if pd.isna(v):
        return ""
    return str(v).strip()

def num(v):
    try:
        if pd.isna(v) or str(v).strip() == "":
            return ""
        return float(v)
    except Exception:
        return ""

rows = []

for source_name, path in SOURCES:
    if not path.exists():
        print(f"Missing source file: {path}")
        continue

    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]

    for _, r in df.iterrows():
        rows.append({
            "snapshot_date": RUN_DATE,
            "source": clean(r.get("market_line_source")) or source_name,
            "week": clean(r.get("week")),
            "game_date": clean(r.get("date"))[:10],
            "away_team": clean(r.get("away_team")),
            "home_team": clean(r.get("home_team")),
            "market_spread_text": clean(r.get("market_spread_text")),
            "market_spread_home": num(r.get("market_spread_home")),
            "market_spread_price": num(r.get("market_spread_price")),
            "market_spread_book": clean(r.get("market_spread_book")),
            "market_total": num(r.get("market_total")),
            "market_total_over_price": num(r.get("market_total_over_price")),
            "market_total_under_price": num(r.get("market_total_under_price")),
            "market_total_book": clean(r.get("market_total_book")),
            "books_available": clean(r.get("books_available")),
        })

new = pd.DataFrame(rows)

if OUT.exists():
    old = pd.read_csv(OUT)
    all_df = pd.concat([old, new], ignore_index=True)
else:
    all_df = new

dedupe_cols = [
    "snapshot_date", "source", "game_date", "away_team", "home_team",
    "market_spread_book", "market_total_book"
]
dedupe_cols = [c for c in dedupe_cols if c in all_df.columns]
all_df = all_df.drop_duplicates(subset=dedupe_cols, keep="last")

OUT.parent.mkdir(parents=True, exist_ok=True)
all_df.to_csv(OUT, index=False)

print(f"Wrote {OUT}: {len(all_df)} total rows; appended {len(new)} rows for {RUN_DATE}")
