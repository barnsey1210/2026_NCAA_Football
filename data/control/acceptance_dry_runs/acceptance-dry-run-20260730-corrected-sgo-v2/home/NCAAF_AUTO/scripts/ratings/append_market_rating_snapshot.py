#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
LATEST = ROOT / "data/ratings/market_implied_ratings_latest.csv"
HISTORY = ROOT / "data/ratings/market_implied_rating_snapshots.csv"

def main():
    if not LATEST.exists():
        raise SystemExit(f"Missing {LATEST}")
    new = pd.read_csv(LATEST, low_memory=False)
    new["snapshot_timestamp"] = datetime.now(timezone.utc).isoformat()

    if HISTORY.exists():
        old = pd.read_csv(HISTORY, low_memory=False)
        out = pd.concat([old, new], ignore_index=True)
        keys = [
            "snapshot_timestamp", "season", "through_week", "team"
        ]
        out = out.drop_duplicates(keys, keep="last")
    else:
        out = new

    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(HISTORY, index=False)
    print("wrote:", HISTORY)
    print("rows:", len(out))

if __name__ == "__main__":
    main()
