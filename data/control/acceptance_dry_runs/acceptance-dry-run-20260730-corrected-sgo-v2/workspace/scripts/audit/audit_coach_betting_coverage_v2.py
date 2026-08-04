#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import re

OUT = Path("data/audit")
OUT.mkdir(parents=True, exist_ok=True)

FILES = [
    "Coach_betting_data/team_betting_trends_2006_2025.csv",
    "Coach_betting_data/coach_tenures_2006_2025.csv",
    "data/import/coach_1h_betting_current_2026.csv",
    "data/import/coach_2h_betting_current_2026.csv",
    "data/import/coach_halves_team_games_2024_2025.csv",
    "data/import/coach_halves_missing_teams.csv",
]

def norm(x):
    s = str(x or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace(".", "")
    return s.lower()

def pick_col(df, names):
    for n in names:
        for c in df.columns:
            if str(c).strip().lower() == n:
                return c
    for n in names:
        for c in df.columns:
            if n in str(c).strip().lower():
                return c
    return None

rows = []

for f in FILES:
    p = Path(f)
    if not p.exists():
        rows.append({
            "source_file": f,
            "status": "MISSING",
        })
        continue

    df = pd.read_csv(p, low_memory=False)
    cols = list(df.columns)
    low = " | ".join(str(c).lower() for c in cols)

    coach_col = pick_col(df, ["current coach", "head coach", "coach"])
    team_col = pick_col(df, ["current team", "team", "school"])

    # Determine actual coverage by columns.
    has_spread = any(k in low for k in ["ats w", "ats l", "ats win", "ats result", "ats +/-", "cover"])
    has_total = any(k in low for k in ["over", "under", "total result", "total +/-", "ou push"])

    if "1h" in f.lower() or "1h " in low or "1h ats" in low or "1h total" in low:
        half = "1H"
    elif "2h" in f.lower() or "2h " in low or "2h ats" in low or "2h total" in low:
        half = "2H"
    elif "halves_team_games" in f.lower():
        half = "GameRowsWith1H"
    else:
        half = "FullGame"

    source_note = ""
    if "2006_2025" in f:
        source_note = "historical 2006-2025 full-game/team-season source"
    elif "current_2026" in f:
        source_note = "current 2026 coach half-game aggregate source"
    elif "halves_team_games_2024_2025" in f:
        source_note = "2024-2025 team-game half source"
    elif "missing_teams" in f:
        source_note = "teams/coaches missing from half-game aggregate source"

    teams = []
    coaches = []
    pat_rows = 0

    if coach_col:
        coaches = sorted(set(str(x).strip() for x in df[coach_col].dropna() if str(x).strip()))
        pat_rows += df[coach_col].astype(str).str.contains("Pat Fitzgerald", case=False, na=False).sum()

    if team_col:
        teams = sorted(set(str(x).strip() for x in df[team_col].dropna() if str(x).strip()))
        pat_rows += df[team_col].astype(str).str.contains("Northwestern|Michigan State", case=False, na=False).sum()

    rows.append({
        "source_file": f,
        "status": "OK",
        "rows": len(df),
        "half_scope": half,
        "has_spread_ats_columns": has_spread,
        "has_total_columns": has_total,
        "coach_col": coach_col or "",
        "team_col": team_col or "",
        "unique_coaches": len(coaches),
        "unique_teams": len(teams),
        "pat_or_related_rows": int(pat_rows),
        "source_note": source_note,
        "columns": ", ".join(map(str, cols)),
    })

audit = pd.DataFrame(rows)
audit.to_csv(OUT / "coach_betting_coverage_audit_v2.csv", index=False)

print("\nCoverage inventory:")
print(audit[[
    "source_file",
    "rows",
    "half_scope",
    "has_spread_ats_columns",
    "has_total_columns",
    "unique_coaches",
    "unique_teams",
    "pat_or_related_rows",
    "source_note",
]].to_string(index=False))

print("\nBottom line:")
print("- Full-game coach betting is historical 2006-2025.")
print("- 1H/2H coach betting is not equivalent historical coverage; it is current/recent half-game coverage.")
print("- Pat Fitzgerald has historical full-game Northwestern data but no historical 1H/2H Northwestern backfill.")
print("- For Michigan State 2026, Pat Fitzgerald is listed as missing from half-game aggregate coverage.")
