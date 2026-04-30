#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import json
import re
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RATINGS_DIR = ROOT / "data" / "ratings"
CONFIG_PATH = RATINGS_DIR / "ratings_config.json"

SPPLUS_LATEST = RATINGS_DIR / "spplus_2026_from_espn_latest.csv"
MASTER_LATEST = RATINGS_DIR / "ratings_master_latest.csv"
HISTORY_PATH = RATINGS_DIR / "ratings_history.csv"
REPORT_PATH = RATINGS_DIR / "ratings_validation_report.txt"
TEAM_AUDIT_PATH = RATINGS_DIR / "team_name_audit.csv"

SYSTEMS = ["spplus", "fpi", "teamrankings", "kford", "bradpowers"]


def norm_team(name: str) -> str:
    s = str(name or "").strip().lower()
    s = s.replace("&", "and")
    s = s.replace("hawaiʻi", "hawaii")
    s = s.replace("hawai'i", "hawaii")
    s = s.replace("louisiana–monroe", "louisiana monroe")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


TEAM_ALIASES = {
    "app state": "Appalachian State",
    "appalachian state": "Appalachian State",
    "army black knights": "Army",
    "army": "Army",
    "byu": "BYU",
    "central florida": "Central Florida",
    "ucf": "Central Florida",
    "connecticut": "Connecticut",
    "uconn": "Connecticut",
    "florida atlantic": "Florida Atlantic",
    "fau": "Florida Atlantic",
    "florida international": "Florida International",
    "fiu": "Florida International",
    "georgia tech": "Georgia Tech",
    "hawaii": "Hawaii",
    "james madison": "James Madison",
    "lsu": "LSU",
    "louisiana": "Louisiana",
    "louisiana lafayette": "Louisiana",
    "ul lafayette": "Louisiana",
    "louisiana monroe": "UL-Monroe",
    "ul monroe": "UL-Monroe",
    "ulm": "UL-Monroe",
    "massachusetts": "Massachusetts",
    "umass": "Massachusetts",
    "miami": "Miami-FL",
    "miami fl": "Miami-FL",
    "miami florida": "Miami-FL",
    "miami oh": "Miami-OH",
    "miami ohio": "Miami-OH",
    "mississippi": "Ole Miss",
    "ole miss": "Ole Miss",
    "n c state": "NC State",
    "nc state": "NC State",
    "north carolina state": "NC State",
    "notre dame": "Notre Dame",
    "penn state": "Penn State",
    "san jose state": "San Jose State",
    "south florida": "South Florida",
    "usf": "South Florida",
    "southern california": "USC",
    "usc": "USC",
    "texas a m": "Texas A&M",
    "texas aandm": "Texas A&M",
    "texas am": "Texas A&M",
    "texas san antonio": "UTSA",
    "ut san antonio": "UTSA",
    "utsa": "UTSA",
    "ucla": "UCLA",
    "unlv": "UNLV",
    "utep": "UTEP",
    "uab": "UAB",
    "western kentucky": "Western Kentucky",
    "wku": "Western Kentucky",
}


def canonical_team(name: str) -> str:
    raw = str(name or "").strip()
    key = norm_team(raw)
    if key in TEAM_ALIASES:
        return TEAM_ALIASES[key]

    # Title-case fallback, then common acronym fixes.
    out = " ".join(w.capitalize() for w in key.split())
    fixes = {
        "Byu": "BYU",
        "Fau": "Florida Atlantic",
        "Fiu": "Florida International",
        "Lsu": "LSU",
        "Smu": "SMU",
        "Tcu": "TCU",
        "Uab": "UAB",
        "Ucf": "Central Florida",
        "Ucla": "UCLA",
        "Unlv": "UNLV",
        "Utep": "UTEP",
        "Usf": "South Florida",
        "Usc": "USC",
        "Utsa": "UTSA",
        "Nc State": "NC State",
    }
    return fixes.get(out, out)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise SystemExit(f"Missing config: {CONFIG_PATH}")

    cfg = json.loads(CONFIG_PATH.read_text())
    weights = cfg.get("weights", {})
    total = sum(float(weights.get(s, 0) or 0) for s in SYSTEMS)

    if abs(total - 1.0) > 0.000001:
        raise SystemExit(f"Ratings weights must sum to 1.0. Current sum: {total}")

    return cfg


def normalize_rating_file(path: Path, system: str) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Missing active ratings file for {system}: {path}")

    df = pd.read_csv(path)

    lower_cols = {str(c).strip().lower(): c for c in df.columns}

    team_col = None
    for c in ["team", "school", "name"]:
        if c in lower_cols:
            team_col = lower_cols[c]
            break

    rating_col = None
    for c in [system, "rating", "power_rating", "power", "sp+", "spplus", "value"]:
        if c in lower_cols:
            rating_col = lower_cols[c]
            break

    if team_col is None or rating_col is None:
        raise SystemExit(
            f"{system} file must have team and rating columns. "
            f"Found columns: {list(df.columns)}"
        )

    out = pd.DataFrame()
    out["team_raw"] = df[team_col].astype(str).str.strip()
    out["team"] = out["team_raw"].map(canonical_team)
    out[system] = pd.to_numeric(df[rating_col], errors="coerce")

    return out


def main():
    cfg = load_config()
    season = int(cfg.get("season", 2026))
    expected = int(cfg.get("expected_team_count", 138))
    weights = {s: float(cfg["weights"].get(s, 0) or 0) for s in SYSTEMS}
    active = cfg.get("active_systems", {})

    run_date = datetime.now().strftime("%Y-%m-%d")
    pulled_at = datetime.now().isoformat(timespec="seconds")

    # Parsed/latest source files.
    # These filenames can point to 2025 test data now and later be changed to 2026 live files.
    # Only nonzero-weight / active systems are required by validation.
    system_files = {
        "spplus": SPPLUS_LATEST,
        "fpi": RATINGS_DIR / "fpi_2025_test_latest.csv",
        "teamrankings": RATINGS_DIR / "teamrankings_2025_test_latest.csv",
        "kford": RATINGS_DIR / "kford_2025_test_latest.csv",
        "bradpowers": RATINGS_DIR / "bradpowers_2025_test_latest.csv",
    }

    report = []
    report.append("Ratings Build Validation")
    report.append(f"Run date: {run_date}")
    report.append(f"Pulled at: {pulled_at}")
    report.append(f"Season: {season}")
    report.append("")

    frames = []
    audit_rows = []

    for system in SYSTEMS:
        weight = weights[system]
        is_active = bool(active.get(system, False)) or weight > 0

        if not is_active and weight == 0:
            report.append(f"{system}: inactive / zero weight")
            continue

        df = normalize_rating_file(system_files[system], system)

        dupes = df[df["team"].duplicated(keep=False)].sort_values("team")
        missing_rating = df[df[system].isna()]

        report.append(f"{system}: {len(df)} rows")

        if len(df) != expected:
            report.append(f"  ERROR: expected {expected} teams, found {len(df)}")

        if len(dupes):
            report.append(f"  ERROR: duplicate mapped teams: {dupes['team'].tolist()}")

        if len(missing_rating):
            report.append(f"  ERROR: missing/non-numeric ratings: {missing_rating['team_raw'].tolist()}")

        for _, r in df.iterrows():
            audit_rows.append({
                "system": system,
                "team_raw": r["team_raw"],
                "team_mapped": r["team"],
                "rating": r[system],
            })

        frames.append(df[["team", system]])

    if not frames:
        raise SystemExit("No active ratings systems found.")

    master = frames[0]
    for df in frames[1:]:
        master = master.merge(df, on="team", how="outer")

    master = master.sort_values("team").reset_index(drop=True)

    if len(master) != expected:
        report.append("")
        report.append(f"ERROR: master expected {expected} teams, found {len(master)}")

    if master["team"].duplicated().any():
        report.append("ERROR: duplicate teams in master")

    # Check missing active/nonzero ratings.
    for system in SYSTEMS:
        weight = weights[system]
        if weight <= 0:
            master[system] = master[system] if system in master.columns else pd.NA
            continue

        if system not in master.columns:
            report.append(f"ERROR: missing nonzero-weight system column: {system}")
            continue

        missing = master[master[system].isna()]["team"].tolist()
        if missing:
            report.append(f"ERROR: {system} missing teams with nonzero weight: {missing}")

    # Calculate weighted Power Rating.
    master["power_rating"] = 0.0
    for system in SYSTEMS:
        if system not in master.columns:
            master[system] = pd.NA
        weight = weights[system]
        if weight > 0:
            master["power_rating"] = master["power_rating"] + master[system].astype(float) * weight

    master.insert(0, "rating_date", run_date)
    master.insert(1, "season", season)

    for system in SYSTEMS:
        master[f"{system}_weight"] = weights[system]

    # Rank: higher power rating is better.
    master["power_rank"] = master["power_rating"].rank(ascending=False, method="min").astype(int)

    errors = [line for line in report if line.strip().startswith("ERROR:") or " ERROR:" in line]

    report.append("")
    report.append(f"Expected teams: {expected}")
    report.append(f"Master teams: {len(master)}")
    report.append(f"Weight sum: {sum(weights.values()):.6f}")
    report.append(f"Validation status: {'FAIL' if errors else 'PASS'}")

    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    pd.DataFrame(audit_rows).to_csv(TEAM_AUDIT_PATH, index=False)

    if errors:
        print(REPORT_PATH.read_text())
        raise SystemExit("Ratings validation failed. Site files were not updated.")

    master.to_csv(MASTER_LATEST, index=False)

    hist_cols = ["rating_date", "season", "team"] + SYSTEMS + ["power_rating", "power_rank"]
    hist = master[hist_cols].copy()

    if HISTORY_PATH.exists():
        old = pd.read_csv(HISTORY_PATH)
        combined = pd.concat([old, hist], ignore_index=True)
        combined = combined.drop_duplicates(["rating_date", "season", "team"], keep="last")
    else:
        combined = hist

    combined.to_csv(HISTORY_PATH, index=False)

    print(REPORT_PATH.read_text())
    print(f"Wrote {MASTER_LATEST}")
    print(f"Wrote {HISTORY_PATH}")
    print(f"Wrote {TEAM_AUDIT_PATH}")


if __name__ == "__main__":
    main()
