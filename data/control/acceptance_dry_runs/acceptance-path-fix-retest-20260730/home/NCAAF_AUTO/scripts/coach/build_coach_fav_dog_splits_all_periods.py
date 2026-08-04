#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import re

SRC = Path("data/import/coach_halves_team_games_2024_2025.csv")
OUT_DIR = Path("data/coach")
AUDIT_DIR = Path("data/audit")
OUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

def side_from_spread(x):
    try:
        v = float(x)
    except Exception:
        return ""
    if v < 0:
        return "Favorite"
    if v > 0:
        return "Underdog"
    return "Pick"

def norm_result(x):
    s = str(x or "").strip().upper()
    if s.startswith("W"):
        return "W"
    if s.startswith("L"):
        return "L"
    if s.startswith("P"):
        return "P"
    if s.startswith("O"):
        return "O"
    if s.startswith("U"):
        return "U"
    return ""

def agg(g):
    ats_w = (g["ats_result"] == "W").sum()
    ats_l = (g["ats_result"] == "L").sum()
    ats_p = (g["ats_result"] == "P").sum()
    ats_decisions = ats_w + ats_l

    overs = (g["total_result"] == "O").sum()
    unders = (g["total_result"] == "U").sum()
    total_p = (g["total_result"] == "P").sum()
    total_decisions = overs + unders

    return pd.Series({
        "games": len(g),
        "ats_w": ats_w,
        "ats_l": ats_l,
        "ats_push": ats_p,
        "ats_win_pct": round(ats_w / ats_decisions, 4) if ats_decisions else "",
        "overs": overs,
        "unders": unders,
        "total_push": total_p,
        "over_pct": round(overs / total_decisions, 4) if total_decisions else "",
        "avg_ats_margin": round(pd.to_numeric(g["ats_margin"], errors="coerce").mean(), 2),
        "avg_total_margin": round(pd.to_numeric(g["total_margin"], errors="coerce").mean(), 2),
        "avg_spread": round(pd.to_numeric(g["spread"], errors="coerce").mean(), 2),
        "seasons": ", ".join(map(str, sorted(set(g["season"].dropna().astype(int))))),
        "historical_teams": ", ".join(sorted(set(str(x).strip() for x in g["historical_team"] if str(x).strip()))),
    })

df = pd.read_csv(SRC, low_memory=False)

periods = [
    {
        "period": "Full Game",
        "spread": "Game Spread",
        "ats": "Game ATS Result",
        "ats_margin": "Game ATS +/-",
        "total": "Game Total Result",
        "total_margin": "Game Total +/-",
    },
    {
        "period": "1H",
        "spread": "1H Spread",
        "ats": "1H ATS Result",
        "ats_margin": "1H ATS +/-",
        "total": "1H Total Result",
        "total_margin": "1H Total +/-",
    },
    {
        "period": "2H",
        "spread": "2H Spread",
        "ats": "2H ATS Result",
        "ats_margin": "2H ATS +/-",
        "total": "2H Total Result",
        "total_margin": "2H Total +/-",
    },
]

long_rows = []

for p in periods:
    needed = [p["spread"], p["ats"], p["total"]]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        print(f"SKIP {p['period']}: missing {missing}")
        continue

    temp = pd.DataFrame({
        "season": pd.to_numeric(df["Season"], errors="coerce"),
        "date": df.get("Date", ""),
        "coach": df["Current Coach"].astype(str).str.strip(),
        "current_team": df["Current Team"].astype(str).str.strip(),
        "historical_team": df["Historical Team"].astype(str).str.strip(),
        "opponent": df.get("Opponent", ""),
        "period": p["period"],
        "spread": pd.to_numeric(df[p["spread"]], errors="coerce"),
        "fav_dog": df[p["spread"]].map(side_from_spread),
        "ats_result": df[p["ats"]].map(norm_result),
        "ats_margin": pd.to_numeric(df[p["ats_margin"]], errors="coerce"),
        "total_result": df[p["total"]].map(norm_result),
        "total_margin": pd.to_numeric(df[p["total_margin"]], errors="coerce"),
    })

    temp = temp[
        temp["coach"].ne("")
        & temp["current_team"].ne("")
        & temp["fav_dog"].isin(["Favorite", "Underdog", "Pick"])
    ].copy()

    long_rows.append(temp)

long = pd.concat(long_rows, ignore_index=True)

summary = (
    long
    .groupby(["coach", "current_team", "period", "fav_dog"], dropna=False)
    .apply(agg)
    .reset_index()
    .sort_values(["current_team", "coach", "period", "fav_dog"])
)

long.to_csv(OUT_DIR / "coach_fav_dog_game_rows_all_periods.csv", index=False)
summary.to_csv(OUT_DIR / "coach_fav_dog_splits_all_periods.csv", index=False)

audit = pd.DataFrame([{
    "source_file": str(SRC),
    "source_rows": len(df),
    "output_game_rows": len(long),
    "output_summary_rows": len(summary),
    "periods": ", ".join(sorted(long["period"].unique())),
    "coaches": long["coach"].nunique(),
    "current_teams": long["current_team"].nunique(),
    "seasons": ", ".join(map(str, sorted(set(long["season"].dropna().astype(int))))),
}])
audit.to_csv(AUDIT_DIR / "coach_fav_dog_all_periods_audit.csv", index=False)

print("wrote:", OUT_DIR / "coach_fav_dog_game_rows_all_periods.csv", "rows:", len(long))
print("wrote:", OUT_DIR / "coach_fav_dog_splits_all_periods.csv", "rows:", len(summary))
print("wrote:", AUDIT_DIR / "coach_fav_dog_all_periods_audit.csv")

print("\nAudit:")
print(audit.to_string(index=False))

print("\nSample:")
print(summary.head(60).to_string(index=False))
