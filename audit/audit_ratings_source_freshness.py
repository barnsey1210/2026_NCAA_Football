#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, date
import json
import re
import pandas as pd

ROOT = Path.cwd()
OUT_DIR = ROOT / "data" / "audits"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date.today()

SOURCE_CANDIDATES = {
    "SP+": [
        ROOT / "data/ratings/spplus_2026_from_espn_latest.csv",
        ROOT / "data/ratings/spplus_2026_latest.csv",
    ],
    "FPI": [
        ROOT / "data/ratings/fpi_2026_latest.csv",
        ROOT / "data/ratings/fpi_2025_test_latest.csv",
    ],
    "TeamRankings": [
        ROOT / "data/ratings/teamrankings_2026_latest.csv",
        ROOT / "data/ratings/teamrankings_2025_test_latest.csv",
    ],
    "KFord": [
        ROOT / "data/ratings/kford_2026_latest.csv",
        ROOT / "data/ratings/kford_2025_test_latest.csv",
        ROOT / "data/ratings/kford_latest.csv",
    ],
    "Brad Powers": [
        ROOT / "data/ratings/bradpowers_2026_latest.csv",
        ROOT / "data/ratings/bradpowers_2026_latest.csv",
        ROOT / "data/ratings/bradpowers_latest.csv",
    ],
    "Sagarin Predictor": [
        ROOT / "data/ratings/external_sources/sagarin_latest.csv",
        ROOT / "data/ratings/sagarin_ratings_latest.csv",
        ROOT / "data/ratings/sagarin_latest.csv",
    ],
    "Massey Power": [
        ROOT / "data/ratings/external_sources/massey_latest.csv",
        ROOT / "data/ratings/massey_ratings_latest.csv",
        ROOT / "data/ratings/massey_visible_ratings_latest.csv",
        ROOT / "data/ratings/massey_latest.csv",
    ],
    "Donchess Overall": [
        ROOT / "data/ratings/external_sources/donchess_latest.csv",
        ROOT / "data/ratings/donchess_ratings_latest.csv",
        ROOT / "data/ratings/donchess_latest.csv",
    ],
}

RAW_DIRS = {
    "SP+": ROOT / "data/ratings/raw/spplus",
    "FPI": ROOT / "data/ratings/raw/fpi",
    "TeamRankings": ROOT / "data/ratings/raw/teamrankings",
    "KFord": ROOT / "data/ratings/raw/kford",
    "Brad Powers": ROOT / "data/ratings/raw/bradpowers",
}

def file_age_days(path: Path):
    if not path.exists():
        return None
    mtime = datetime.fromtimestamp(path.stat().st_mtime).date()
    return (TODAY - mtime).days

def latest_file(paths):
    existing = [p for p in paths if p.exists()]
    if not existing:
        return None
    return max(existing, key=lambda p: p.stat().st_mtime)

def latest_raw_file(raw_dir):
    if not raw_dir.exists():
        return None
    files = [p for p in raw_dir.glob("*") if p.is_file()]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)

def snapshot_date_from_df(df):
    for col in ["snapshot_date", "date", "as_of", "updated_at", "run_date"]:
        if col in df.columns:
            vals = df[col].dropna().astype(str)
            if len(vals):
                return vals.max()
    return ""

def infer_rating_col(df, source):
    candidates = [
        "rating", "power_rating", "power", "value",
        "spplus", "sp", "fpi", "teamrankings", "kford", "bradpowers",
        "sagarin", "massey", "donchess",
    ]
    lower_map = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c in lower_map:
            return lower_map[c]
    for c in df.columns:
        if re.search(r"rating|power|fpi|sp|predictor|overall", c, re.I):
            return c
    return ""

def infer_data_vintage(path, df, source):
    """
    file freshness = when we pulled/parsed it.
    data vintage = whether the source itself appears to be true 2026 current data,
    prior-year/test data, manual current, or unknown.
    """
    path_s = str(path).lower() if path else ""
    cols = set(df.columns)

    seasons = []
    if "season" in df.columns:
        seasons = sorted(pd.to_numeric(df["season"], errors="coerce").dropna().astype(int).unique().tolist())

    snapshot_dates = []
    if "snapshot_date" in df.columns:
        snapshot_dates = sorted(df["snapshot_date"].dropna().astype(str).unique().tolist())

    notes = []

    # Strong filename clues from our own historical naming.
    if "2025_test" in path_s:
        notes.append("filename contains 2025_test")
        # Some 2025_test files are currently refreshed from pages that still contain completed-season records.
        return "prior_or_test_data", "; ".join(notes)

    if "2025" in path_s and "2026" not in path_s:
        notes.append("filename contains 2025 but not 2026")
        return "prior_or_test_data", "; ".join(notes)

    if "2026" in path_s:
        notes.append("filename contains 2026")

    if seasons:
        notes.append("season=" + ",".join(map(str, seasons)))
        if max(seasons) >= 2026:
            return "2026_current", "; ".join(notes)
        if max(seasons) <= 2025:
            return "prior_or_test_data", "; ".join(notes)

    # Source-specific judgment.
    if source in ["Sagarin Predictor", "Massey Power", "Donchess Overall"]:
        # These parsers write season/snapshot_date and currently return 2026 data.
        if seasons and max(seasons) >= 2026:
            return "2026_current", "; ".join(notes)
        return "unknown", "; ".join(notes)

    if source == "SP+":
        # Our SP+ file is explicitly 2026 from ESPN.
        if "2026" in path_s:
            return "2026_current", "; ".join(notes)
        return "unknown", "; ".join(notes)

    if source in ["FPI", "TeamRankings", "KFord", "Brad Powers"]:
        # These can be fresh files but still based on old/test/prior-year pages unless source has
        # clearly moved to 2026 preseason/season.
        if "2026" in path_s:
            return "2026_current", "; ".join(notes)
        return "prior_or_test_data", "; ".join(notes or ["no explicit 2026 marker"])

    return "unknown", "; ".join(notes)

def inspect_csv(path, source):
    info = {
        "rows": "",
        "teams": "",
        "rating_col": "",
        "missing_rating": "",
        "snapshot_date": "",
        "data_vintage": "",
        "vintage_notes": "",
    }
    if not path or not path.exists():
        return info
    try:
        df = pd.read_csv(path)
    except Exception as e:
        info["rows"] = f"ERROR: {e}"
        return info

    info["rows"] = len(df)
    team_col = ""
    for c in df.columns:
        if c.lower() in ["team", "team_name", "school"]:
            team_col = c
            break
    if team_col:
        info["teams"] = df[team_col].nunique(dropna=True)

    rating_col = infer_rating_col(df, source)
    info["rating_col"] = rating_col
    if rating_col:
        info["missing_rating"] = int(pd.to_numeric(df[rating_col], errors="coerce").isna().sum())

    info["snapshot_date"] = snapshot_date_from_df(df)
    vintage, vintage_notes = infer_data_vintage(path, df, source)
    info["data_vintage"] = vintage
    info["vintage_notes"] = vintage_notes
    return info

rows = []

for source, paths in SOURCE_CANDIDATES.items():
    latest = latest_file(paths)
    raw = latest_raw_file(RAW_DIRS[source]) if source in RAW_DIRS else None
    csv_info = inspect_csv(latest, source)

    source_age = file_age_days(latest) if latest else None
    raw_age = file_age_days(raw) if raw else None

    if latest is None:
        status = "missing"
    elif source_age is not None and source_age <= 1:
        status = "fresh"
    elif source_age is not None and source_age <= 7:
        status = "recent"
    else:
        status = "stale"

    rows.append({
        "source": source,
        "file_status": status,
        "latest_csv": str(latest.relative_to(ROOT)) if latest else "",
        "csv_age_days": source_age if source_age is not None else "",
        "latest_raw": str(raw.relative_to(ROOT)) if raw else "",
        "raw_age_days": raw_age if raw_age is not None else "",
        "rows": csv_info["rows"],
        "teams": csv_info["teams"],
        "rating_col": csv_info["rating_col"],
        "missing_rating": csv_info["missing_rating"],
        "snapshot_date": csv_info["snapshot_date"],
        "data_vintage": csv_info["data_vintage"],
        "vintage_notes": csv_info["vintage_notes"],
    })

out = pd.DataFrame(rows)
out.to_csv(OUT_DIR / "ratings_source_freshness.csv", index=False)

summary = pd.DataFrame([{
    "audit_date": TODAY.isoformat(),
    "sources": len(out),
    "fresh_files": int((out["file_status"] == "fresh").sum()),
    "recent_files": int((out["file_status"] == "recent").sum()),
    "stale_files": int((out["file_status"] == "stale").sum()),
    "missing_files": int((out["file_status"] == "missing").sum()),
    "current_2026_sources": int((out["data_vintage"] == "2026_current").sum()),
    "prior_or_test_sources": int((out["data_vintage"] == "prior_or_test_data").sum()),
    "unknown_vintage_sources": int((out["data_vintage"] == "unknown").sum()),
}])
summary.to_csv(OUT_DIR / "ratings_source_freshness_summary.csv", index=False)

print("wrote:", OUT_DIR / "ratings_source_freshness.csv")
print("wrote:", OUT_DIR / "ratings_source_freshness_summary.csv")
print()
print(out.to_string(index=False))
