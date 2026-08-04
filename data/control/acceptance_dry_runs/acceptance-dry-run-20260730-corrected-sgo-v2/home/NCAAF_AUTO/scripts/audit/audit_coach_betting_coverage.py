#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import re

ROOT = Path(".")
OUT_DIR = ROOT / "data/audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def norm_name(x):
    s = str(x or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace(".", "")
    return s.lower()

def safe_read_csv(p):
    try:
        if p.stat().st_size == 0:
            return None
        return pd.read_csv(p)
    except Exception:
        return None

def classify_source(path, df):
    name = path.as_posix().lower()
    cols = " ".join(str(c).lower() for c in df.columns)

    if "coach" not in name and "coach" not in cols:
        return None

    # Market / category classification
    if "1h" in name or "first half" in name or "1h" in cols or "first half" in cols:
        half = "1H"
    elif "2h" in name or "second half" in name or "2h" in cols or "second half" in cols:
        half = "2H"
    else:
        half = "Full"

    if "total" in name or "over" in cols or "under" in cols or "total" in cols:
        market = "Total"
    elif "ats" in name or "spread" in name or "cover" in cols or "ats" in cols or "spread" in cols:
        market = "Spread"
    else:
        market = "Unknown"

    return f"{half}_{market}"

def find_col(df, candidates):
    cols = list(df.columns)
    low = {str(c).lower().strip(): c for c in cols}
    for cand in candidates:
        if cand in low:
            return low[cand]
    for c in cols:
        cl = str(c).lower()
        if any(cand in cl for cand in candidates):
            return c
    return None

def summarize_row(row, cols):
    pieces = []
    for c in cols:
        if c in row.index:
            v = row[c]
            if pd.notna(v) and str(v).strip() != "":
                pieces.append(f"{c}={v}")
    return "; ".join(pieces[:10])

# Load all likely coach CSVs.
records = []
source_summaries = []

for p in sorted(ROOT.rglob("*.csv")):
    if any(part in {".git", "backups", "__pycache__"} for part in p.parts):
        continue

    df = safe_read_csv(p)
    if df is None or df.empty:
        continue

    source_type = classify_source(p, df)
    if not source_type:
        continue

    coach_col = find_col(df, ["coach", "head_coach", "coach_name", "head coach"])
    team_col = find_col(df, ["team", "school"])

    if not coach_col and not team_col:
        continue

    source_summaries.append({
        "source_file": p.as_posix(),
        "source_type": source_type,
        "rows": len(df),
        "columns": ", ".join(map(str, df.columns)),
        "coach_col": coach_col or "",
        "team_col": team_col or "",
    })

    useful_cols = [
        c for c in df.columns
        if any(k in str(c).lower() for k in [
            "wins", "loss", "push", "ats", "cover", "margin", "over", "under",
            "total", "pct", "record", "roi", "units", "games"
        ])
    ]

    for _, r in df.iterrows():
        coach = r.get(coach_col, "") if coach_col else ""
        team = r.get(team_col, "") if team_col else ""

        if not str(coach).strip() and not str(team).strip():
            continue

        records.append({
            "source_file": p.as_posix(),
            "source_type": source_type,
            "coach": str(coach).strip(),
            "coach_norm": norm_name(coach),
            "team": str(team).strip(),
            "team_norm": norm_name(team),
            "detail": summarize_row(r, useful_cols),
        })

sources = pd.DataFrame(source_summaries)
rows = pd.DataFrame(records)

sources.to_csv(OUT_DIR / "coach_betting_source_inventory.csv", index=False)

if rows.empty:
    print("No coach betting rows found.")
    print(f"wrote: {OUT_DIR / 'coach_betting_source_inventory.csv'}")
    raise SystemExit

rows.to_csv(OUT_DIR / "coach_betting_rows_long.csv", index=False)

# Coverage by coach.
coverage = rows.pivot_table(
    index=["coach_norm"],
    columns="source_type",
    values="source_file",
    aggfunc="count",
    fill_value=0
).reset_index()

# Attach best display coach/team.
display = (
    rows.sort_values(["coach_norm", "coach"])
    .groupby("coach_norm")
    .agg(
        coach=("coach", lambda x: next((v for v in x if str(v).strip()), "")),
        teams=("team", lambda x: ", ".join(sorted(set(str(v).strip() for v in x if str(v).strip())))),
        source_files=("source_file", lambda x: " | ".join(sorted(set(map(str, x)))))
    )
    .reset_index()
)

coverage = display.merge(coverage, on="coach_norm", how="left")

for col in ["Full_Spread", "1H_Spread", "2H_Spread", "Full_Total", "1H_Total", "2H_Total", "Full_Unknown", "1H_Unknown", "2H_Unknown"]:
    if col not in coverage.columns:
        coverage[col] = 0

coverage["has_full_spread"] = coverage["Full_Spread"] > 0
coverage["missing_1h_spread"] = coverage["has_full_spread"] & (coverage["1H_Spread"] == 0)
coverage["missing_2h_spread"] = coverage["has_full_spread"] & (coverage["2H_Spread"] == 0)
coverage["missing_any_half_spread"] = coverage["missing_1h_spread"] | coverage["missing_2h_spread"]

coverage["has_full_total"] = coverage["Full_Total"] > 0
coverage["missing_1h_total"] = coverage["has_full_total"] & (coverage["1H_Total"] == 0)
coverage["missing_2h_total"] = coverage["has_full_total"] & (coverage["2H_Total"] == 0)
coverage["missing_any_half_total"] = coverage["missing_1h_total"] | coverage["missing_2h_total"]

coverage = coverage.sort_values([
    "missing_any_half_spread",
    "missing_any_half_total",
    "coach"
], ascending=[False, False, True])

coverage.to_csv(OUT_DIR / "coach_betting_coverage_audit.csv", index=False)

# Pat Fitzgerald focused audit.
pat = rows[
    rows["coach_norm"].str.contains("pat fitzgerald", na=False)
    | rows["coach"].astype(str).str.contains("Pat Fitzgerald", case=False, na=False)
    | rows["team"].astype(str).str.contains("Northwestern", case=False, na=False)
].copy()

pat.to_csv(OUT_DIR / "coach_betting_pat_fitzgerald_audit.csv", index=False)

print("wrote:", OUT_DIR / "coach_betting_source_inventory.csv")
print("wrote:", OUT_DIR / "coach_betting_rows_long.csv")
print("wrote:", OUT_DIR / "coach_betting_coverage_audit.csv")
print("wrote:", OUT_DIR / "coach_betting_pat_fitzgerald_audit.csv")

print("\nSource inventory:")
print(sources[["source_type", "rows", "source_file", "coach_col", "team_col"]].to_string(index=False))

print("\nPotential issue: full-game spread exists but 1H/2H spread missing")
issue = coverage[coverage["missing_any_half_spread"]].copy()
print(issue[[
    "coach",
    "teams",
    "Full_Spread",
    "1H_Spread",
    "2H_Spread",
    "Full_Total",
    "1H_Total",
    "2H_Total",
]].head(80).to_string(index=False))

print("\nPat Fitzgerald / Northwestern rows:")
if pat.empty:
    print("No Pat Fitzgerald / Northwestern rows found in coach betting sources.")
else:
    print(pat[["source_type", "coach", "team", "source_file", "detail"]].to_string(index=False))
