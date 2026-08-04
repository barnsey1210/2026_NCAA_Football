#!/usr/bin/env python3
from pathlib import Path

import pandas as pd

INP = Path("data/rosters/player_importance_2026_normalized.csv")
OUT = Path("data/rosters/player_importance_2026_alert_ready.csv")
GAPS = Path("data/audit/player_importance_qb_gaps.csv")

def main():
    df = pd.read_csv(INP)

    before = len(df)

    dedupe_cols = [
        "team",
        "player",
        "position",
        "depth_rank",
        "source",
    ]

    df = df.drop_duplicates(subset=dedupe_cols, keep="last").copy()

    if "depth_rank_source" not in df.columns:
        df["depth_rank_source"] = df["depth_rank"]

    additions = []
    gaps = []

    for team, g in df.groupby("team"):
        qbs = g[g["position"].eq("QB")].copy()
        has_qb1 = not qbs[qbs["depth_rank"].eq(1)].empty

        if has_qb1:
            continue

        if qbs.empty:
            gaps.append({
                "team": team,
                "gap_type": "no_qb_rows",
                "note": "No QB rows parsed from Ourlads for this team",
            })
            continue

        qbs = qbs.sort_values(["depth_rank", "importance_score"], ascending=[True, False])
        top = qbs.iloc[0].copy()

        gaps.append({
            "team": team,
            "gap_type": "has_qb_rows_no_qb1",
            "note": f"Promoted top available QB row from depth_rank={top['depth_rank']} as estimated QB1 for injury-alert purposes",
        })

        top["depth_rank_source"] = top["depth_rank"]
        top["depth_rank"] = 1
        top["starter_flag"] = True
        top["role"] = "QB1_EST"
        top["importance_score"] = max(float(top["importance_score"]), 7.5)
        top["notes"] = str(top.get("notes", "")) + " | estimated QB1 fallback because Ourlads QB1 blank"
        additions.append(top)

    if additions:
        add_df = pd.DataFrame(additions)
        df = pd.concat([df, add_df], ignore_index=True)

    df = df.drop_duplicates(subset=["team", "player", "position", "depth_rank", "role"], keep="last").copy()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    GAPS.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUT, index=False)
    pd.DataFrame(gaps).to_csv(GAPS, index=False)

    qb1 = df[(df["position"].eq("QB")) & (df["depth_rank"].eq(1))]

    print("input rows:", before)
    print("deduped/output rows:", len(df))
    print("site teams:", df["team"].nunique())
    print("QB1 rows:", len(qb1))
    print("QB1 teams:", qb1["team"].nunique())
    print("fallback QB1 additions:", len(additions))
    print("gaps:", len(gaps))
    print("wrote:", OUT)
    print("wrote:", GAPS)

    if gaps:
        print("\nQB GAPS")
        print(pd.DataFrame(gaps).to_string(index=False))

if __name__ == "__main__":
    main()
