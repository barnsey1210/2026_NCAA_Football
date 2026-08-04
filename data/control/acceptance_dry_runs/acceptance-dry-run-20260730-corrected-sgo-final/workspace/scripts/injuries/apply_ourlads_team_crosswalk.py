#!/usr/bin/env python3
from pathlib import Path

import pandas as pd

IMPORTANCE = Path("data/rosters/player_importance_2026.csv")
CROSSWALK = Path("data/rosters/team_name_crosswalk_ourlads_to_site.csv")
OUT = Path("data/rosters/player_importance_2026_normalized.csv")
AUDIT = Path("data/audit/player_importance_team_crosswalk_audit.csv")

def main():
    imp = pd.read_csv(IMPORTANCE)
    xwalk = pd.read_csv(CROSSWALK)

    mapping = dict(zip(xwalk["ourlads_team"], xwalk["site_team"]))

    out = imp.copy()
    out["team_ourlads"] = out["team"]
    out["team"] = out["team_ourlads"].map(mapping).fillna(out["team_ourlads"])
    out["team_crosswalked"] = out["team"].ne(out["team_ourlads"])

    unmatched = out[out["team"].eq(out["team_ourlads"]) & ~out["team_ourlads"].isin(xwalk["site_team"])]
    audit = pd.DataFrame({
        "ourlads_team": sorted(out["team_ourlads"].unique()),
    })
    audit["site_team"] = audit["ourlads_team"].map(mapping)
    audit["missing_site_team"] = audit["site_team"].isna()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)

    out.to_csv(OUT, index=False)
    audit.to_csv(AUDIT, index=False)

    print("input rows:", len(imp))
    print("output rows:", len(out))
    print("ourlads teams:", out["team_ourlads"].nunique())
    print("site teams:", out["team"].nunique())
    print("missing mappings:", int(audit["missing_site_team"].sum()))
    print("wrote:", OUT)
    print("wrote:", AUDIT)

    if audit["missing_site_team"].any():
        print(audit[audit["missing_site_team"]].to_string(index=False))

if __name__ == "__main__":
    main()
