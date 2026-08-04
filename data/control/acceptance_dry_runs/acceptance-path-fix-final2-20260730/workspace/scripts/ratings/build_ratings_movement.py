#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

HISTORY = Path("data/ratings/ratings_history.csv")
OUT = Path("data/ratings/ratings_movement.csv")

def main():
    hist = pd.read_csv(HISTORY)

    hist["snapshot_date"] = pd.to_datetime(hist["snapshot_date"]).dt.date.astype(str)
    hist["rating"] = pd.to_numeric(hist["rating"], errors="coerce")
    hist["rank"] = pd.to_numeric(hist["rank"], errors="coerce")

    rows = []

    for (season, source, team), g in hist.groupby(["season", "source", "team"], dropna=False):
        g = g.dropna(subset=["snapshot_date"]).sort_values("snapshot_date")
        g = g.drop_duplicates("snapshot_date", keep="last")

        if len(g) < 2:
            continue

        prev = g.iloc[-2]
        cur = g.iloc[-1]

        rows.append({
            "season": season,
            "source": source,
            "team": team,
            "snapshot_prev": prev["snapshot_date"],
            "snapshot_latest": cur["snapshot_date"],
            "prev_rating": prev.get("rating"),
            "latest_rating": cur.get("rating"),
            "rating_change": (cur.get("rating") - prev.get("rating")) if pd.notna(cur.get("rating")) and pd.notna(prev.get("rating")) else "",
            "prev_rank": prev.get("rank"),
            "latest_rank": cur.get("rank"),
            "rank_change": (prev.get("rank") - cur.get("rank")) if pd.notna(cur.get("rank")) and pd.notna(prev.get("rank")) else "",
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)

    print(f"Wrote {OUT}: {len(out)} rows")
    if len(out):
        print(out.sort_values("rating_change", key=lambda s: s.abs(), ascending=False).head(30).to_string(index=False))

if __name__ == "__main__":
    main()
