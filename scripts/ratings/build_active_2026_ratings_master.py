from pathlib import Path
import pandas as pd

LATEST = Path("data/ratings/ratings_latest.csv")
OUT = Path("data/ratings/ratings_master_latest.csv")
STATUS = Path("data/ratings/ratings_source_status.csv")

# Canonical Team Rating Engine — fixed 25% each.
ACTIVE_SOURCES = {
    "SP+": "spplus",
    "FPI": "fpi",
    "TeamRankings": "teamrankings",
    "Sagarin Rating": "sagarin",
}

REFERENCE_SOURCES = ["Brad Powers", "Donchess Overall", "KFord", "Massey Power"]

def main():
    if not LATEST.exists():
        raise SystemExit(f"missing {LATEST}")

    latest = pd.read_csv(LATEST)
    active = latest[latest["source"].isin(ACTIVE_SOURCES.keys())].copy()

    pivot = active.pivot_table(index="team", columns="source", values="rating", aggfunc="first").reset_index()

    for src in ACTIVE_SOURCES:
        if src not in pivot.columns:
            pivot[src] = pd.NA
        pivot[src] = pd.to_numeric(pivot[src], errors="coerce")

    # Use Sagarin main Rating field, preserve raw, zero-center so 0 = average team.
    sagarin_source = "Sagarin Rating"
    pivot["sagarin_raw"] = pivot[sagarin_source]
    sagarin_mean = pivot[sagarin_source].mean(skipna=True)
    if pd.notna(sagarin_mean):
        pivot[sagarin_source] = pivot[sagarin_source] - sagarin_mean

    active_cols = list(ACTIVE_SOURCES.keys())
    pivot["source_count"] = pivot[active_cols].notna().sum(axis=1)

    # Canonical Team Rating Engine:
    #   FULL = SP+ 25% / FPI 25% / TeamRankings 25% / Sagarin 25%.
    #   DEGRADED = equal renormalization across the available canonical sources.
    # This preserves continuity for simulations/futures while clearly recording
    # the effective weights used for each team.
    pivot["power_rating"] = pivot[active_cols].mean(axis=1, skipna=True)
    pivot.loc[pivot["source_count"].eq(0), "power_rating"] = pd.NA
    pivot["power_rating"] = pd.to_numeric(pivot["power_rating"], errors="coerce")
    pivot["rating_resolution_mode"] = pivot["source_count"].apply(
        lambda n: "FULL" if int(n) == 4 else ("DEGRADED_RENORMALIZED" if int(n) > 0 else "UNAVAILABLE")
    )

    denom = pivot["source_count"].replace(0, pd.NA)
    for src, out_col in ACTIVE_SOURCES.items():
        pivot[out_col] = pivot[src]
        pivot[out_col + "_weight"] = pivot[src].notna().astype(float) / denom

    pivot["rating_date"] = latest["snapshot_date"].dropna().astype(str).max()
    pivot["season"] = 2026
    pivot["power_rank"] = pivot["power_rating"].rank(ascending=False, method="min", na_option="bottom").astype("Int64")

    out = pivot[["rating_date","season","team","spplus","fpi","teamrankings","sagarin","sagarin_raw","power_rating","spplus_weight","fpi_weight","teamrankings_weight","sagarin_weight","source_count","rating_resolution_mode","power_rank"]].copy()

    # Compatibility-only columns; not part of the composite.
    out["dratings"] = 0.0
    out["dratings_weight"] = 0.0
    out["kford"] = 0.0
    out["bradpowers"] = 0.0
    out["kford_weight"] = 0.0
    out["bradpowers_weight"] = 0.0

    out = out[["rating_date","season","team","spplus","fpi","teamrankings","dratings","sagarin","sagarin_raw","kford","bradpowers","power_rating","spplus_weight","fpi_weight","teamrankings_weight","dratings_weight","sagarin_weight","kford_weight","bradpowers_weight","source_count","rating_resolution_mode","power_rank"]].sort_values(["power_rank","team"], na_position="last")

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
            "production_weight_pct": 25.0 if active_2026 else 0.0,
            "display_status": "Active 2026" if active_2026 else "Stale / reference only",
        })

    status = pd.DataFrame(rows).sort_values(["active_2026","source"], ascending=[False,True])
    status.to_csv(STATUS, index=False)

    print(f"wrote {OUT}: {len(out)} rows")
    print(out[["power_rank","team","power_rating","spplus","fpi","teamrankings","sagarin","sagarin_raw","source_count"]].head(20).to_string(index=False))
    print()
    print("Sagarin raw mean:", round(pd.to_numeric(out["sagarin_raw"], errors="coerce").mean(), 6))
    print("Sagarin normalized mean:", round(pd.to_numeric(out["sagarin"], errors="coerce").mean(), 6))
    print("Composite available:", int(out["power_rating"].notna().sum()), "/", len(out))
    print("Resolution modes:")
    print(out["rating_resolution_mode"].value_counts(dropna=False).to_string())
    print()
    print(f"wrote {STATUS}")

if __name__ == "__main__":
    main()
