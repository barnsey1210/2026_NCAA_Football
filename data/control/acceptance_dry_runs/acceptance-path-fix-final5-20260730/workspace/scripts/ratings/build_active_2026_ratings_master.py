from pathlib import Path
import pandas as pd

LATEST = Path("data/ratings/ratings_latest.csv")
OUT = Path("data/ratings/ratings_master_latest.csv")
STATUS = Path("data/ratings/ratings_source_status.csv")

ACTIVE_SOURCES = {
    "SP+": "spplus",
    "FPI": "fpi",
    "TeamRankings": "teamrankings",
    "Brad Powers": "bradpowers",
}

REFERENCE_SOURCES = [
    "Brad Powers",
    "KFord",
    "Massey Power",
    "Sagarin Predictor",
    "Donchess Overall",
]

def main():
    if not LATEST.exists():
        raise SystemExit(f"missing {LATEST}")

    latest = pd.read_csv(LATEST)

    active = latest[latest["source"].isin(ACTIVE_SOURCES.keys())].copy()

    pivot = active.pivot_table(
        index="team",
        columns="source",
        values="rating",
        aggfunc="first"
    ).reset_index()

    for src in ACTIVE_SOURCES:
        if src not in pivot.columns:
            pivot[src] = pd.NA

    active_cols = list(ACTIVE_SOURCES.keys())
    pivot["source_count"] = pivot[active_cols].notna().sum(axis=1)
    pivot["power_rating"] = pivot[active_cols].mean(axis=1)
    pivot.loc[pivot["source_count"] < 2, "power_rating"] = pd.NA
    pivot["composite_status"] = pivot["source_count"].map({
        4: "official_full_coverage",
        3: "official_reweighted_three_sources",
        2: "official_limited_coverage_two_sources",
        1: "unofficial_one_source",
        0: "unavailable",
    })

    for src, out_col in ACTIVE_SOURCES.items():
        pivot[out_col] = pivot[src]
        pivot[out_col + "_weight"] = (
            pivot[src].notna().astype(float) /
            pivot["source_count"].replace(0, pd.NA)
        )

    pivot["rating_date"] = latest["snapshot_date"].dropna().astype(str).max()
    pivot["season"] = 2026
    pivot["power_rank"] = pivot["power_rating"].rank(ascending=False, method="min").astype("Int64")

    out = pivot[[
        "rating_date",
        "season",
        "team",
        "spplus",
        "fpi",
        "teamrankings",
        "bradpowers",
        "power_rating",
        "spplus_weight",
        "fpi_weight",
        "teamrankings_weight",
        "bradpowers_weight",
        "source_count",
        "composite_status",
        "power_rank",
    ]].copy()

    # Compatibility columns used by existing site/projection code.
    for c in ["kford", "kford_weight"]:
        out[c] = 0.0

    out = out[[
        "rating_date",
        "season",
        "team",
        "spplus",
        "fpi",
        "teamrankings",
        "kford",
        "bradpowers",
        "power_rating",
        "spplus_weight",
        "fpi_weight",
        "teamrankings_weight",
        "kford_weight",
        "bradpowers_weight",
        "source_count",
        "composite_status",
        "power_rank",
    ]].sort_values("power_rank")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    rows = []
    for src, g in latest.groupby("source"):
        active_2026 = src in ACTIVE_SOURCES
        rows.append({
            "source": src,
            "teams": g["team"].nunique(),
            "rows": len(g),
            "snapshot_date": g["snapshot_date"].dropna().astype(str).max() if "snapshot_date" in g else "",
            "pulled_at": g["pulled_at"].dropna().astype(str).max() if "pulled_at" in g else "",
            "source_updated_at": "",
            "active_2026": active_2026,
            "production_weight_pct": round(100.0 / len(ACTIVE_SOURCES), 4) if active_2026 else 0.0,
            "display_status": "Active 2026" if active_2026 else "Stale / reference only",
        })

    status = pd.DataFrame(rows).sort_values(["active_2026", "source"], ascending=[False, True])
    status.to_csv(STATUS, index=False)

    print(f"wrote {OUT}: {len(out)} rows")
    print(out[["power_rank","team","power_rating","spplus","fpi","teamrankings","source_count"]].head(20).to_string(index=False))
    print()
    print("source count coverage:")
    print(out["source_count"].value_counts().sort_index().to_string())
    print()
    print(f"wrote {STATUS}")

if __name__ == "__main__":
    main()
