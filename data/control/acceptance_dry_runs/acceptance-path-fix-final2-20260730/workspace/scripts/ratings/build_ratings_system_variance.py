from pathlib import Path
import pandas as pd
import numpy as np

MASTER = Path("data/ratings/ratings_master_latest.csv")
OUT = Path("data/ratings/ratings_system_variance.csv")

ACTIVE_COLS = ["spplus", "fpi", "teamrankings"]

def tier_from_range(x):
    if pd.isna(x):
        return "missing"
    if x >= 6:
        return "high"
    if x >= 3:
        return "medium"
    return "low"

def main():
    df = pd.read_csv(MASTER)

    vals = df[ACTIVE_COLS].apply(pd.to_numeric, errors="coerce")

    out = df[["team", "power_rank", "power_rating"] + ACTIVE_COLS].copy()
    out["rating_source_count"] = vals.notna().sum(axis=1)
    out["rating_min"] = vals.min(axis=1)
    out["rating_max"] = vals.max(axis=1)
    out["rating_range"] = out["rating_max"] - out["rating_min"]
    out["rating_stddev"] = vals.std(axis=1)
    out["rating_variance_tier"] = out["rating_range"].apply(tier_from_range)

    def high_low_sources(row):
        available = {c: row[c] for c in ACTIVE_COLS if pd.notna(row[c])}
        if not available:
            return "", ""
        hi = max(available, key=available.get)
        lo = min(available, key=available.get)
        return hi, lo

    pairs = out.apply(high_low_sources, axis=1)
    out["highest_source"] = [p[0] for p in pairs]
    out["lowest_source"] = [p[1] for p in pairs]

    out = out.sort_values(["rating_range", "power_rank"], ascending=[False, True])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print(f"wrote {OUT}: {len(out)} rows")
    print()
    print("Top rating disagreement teams:")
    print(out[[
        "team","power_rank","power_rating","spplus","fpi","teamrankings",
        "rating_range","rating_stddev","rating_variance_tier","highest_source","lowest_source"
    ]].head(25).to_string(index=False))

if __name__ == "__main__":
    main()
