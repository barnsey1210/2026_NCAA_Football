#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
MARKET = ROOT / "data/ratings/market_implied_ratings_latest.csv"
INDEX = ROOT / "index.html"
OUT = ROOT / "data/ratings/fundamental_market_rating_comparison.csv"
AUDIT = ROOT / "data/ratings/fundamental_market_rating_comparison_audit.json"

CANDIDATES = [
    "combo",
    "overall_rating",
    "power_rating",
    "composite_rating",
    "rating",
    "site_rating",
    "predictive_rating",
]

def numeric_series(s):
    return pd.to_numeric(s, errors="coerce")

def main():
    if not MARKET.exists():
        raise SystemExit(f"Missing {MARKET}; run market rating research first.")
    if not INDEX.exists():
        raise SystemExit(f"Missing {INDEX}")

    html = INDEX.read_text(encoding="utf-8", errors="ignore")
    m = re.search(
        r'<script id="db" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    if not m:
        raise SystemExit("Could not locate embedded DB in index.html.")

    db = json.loads(m.group(1))
    teams = pd.DataFrame(db.get("teams", []))
    if "team" not in teams:
        raise SystemExit("Embedded teams table has no team column.")

    fundamental_col = None
    for col in CANDIDATES:
        if col in teams and numeric_series(teams[col]).notna().sum() >= 50:
            fundamental_col = col
            break

    market = pd.read_csv(MARKET, low_memory=False)
    audit = {
        "market_rows": int(len(market)),
        "fundamental_column": fundamental_col,
        "status": None,
    }

    if fundamental_col is None:
        audit["status"] = "fundamental rating column not identified"
        AUDIT.write_text(json.dumps(audit, indent=2) + "\n")
        print(json.dumps(audit, indent=2))
        return

    fundamental = teams[["team", fundamental_col]].copy()
    fundamental["fundamental_rating"] = numeric_series(
        fundamental[fundamental_col]
    )
    fundamental = fundamental.drop(columns=[fundamental_col])

    out = fundamental.merge(market, on="team", how="outer")
    out["fundamental_minus_market"] = (
        out.fundamental_rating - out.market_implied_rating
    )
    out["abs_fundamental_market_gap"] = out.fundamental_minus_market.abs()
    out["fundamental_rank"] = (
        out.fundamental_rating.rank(method="min", ascending=False)
    )
    out = out.sort_values(
        ["abs_fundamental_market_gap", "team"],
        ascending=[False, True],
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    audit.update({
        "status": "ok",
        "rows": int(len(out)),
        "matched": int(
            (
                out.fundamental_rating.notna()
                & out.market_implied_rating.notna()
            ).sum()
        ),
        "output": str(OUT.relative_to(ROOT)),
        "note": (
            "Market ratings remain separate from the fundamental blend. "
            "Differences are diagnostic and are not blended into the official rating."
        ),
    })
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))
    print("wrote:", OUT)

if __name__ == "__main__":
    main()
