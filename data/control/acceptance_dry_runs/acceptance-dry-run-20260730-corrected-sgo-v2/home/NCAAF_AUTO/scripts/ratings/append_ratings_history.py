#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

LATEST = Path("data/ratings/ratings_latest.csv")
HISTORY = Path("data/ratings/ratings_history.csv")

KEYS = ["snapshot_date", "season", "source", "team"]

def main():
    latest = pd.read_csv(LATEST)

    if HISTORY.exists():
        hist = pd.read_csv(HISTORY)
        out = pd.concat([hist, latest], ignore_index=True)
    else:
        out = latest.copy()

    out = out.drop_duplicates(subset=KEYS, keep="last")
    out = out.sort_values(["source", "team", "snapshot_date"])
    out.to_csv(HISTORY, index=False)

    print(f"Wrote {HISTORY}: {len(out)} rows")
    print(out.groupby("source").size().to_string())

if __name__ == "__main__":
    main()
