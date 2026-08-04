#!/usr/bin/env python3

from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INFILE = ROOT / "data" / "ratings" / "manual" / "kford_latest.txt"
OUT = ROOT / "data" / "ratings" / "kford_2025_test_latest.csv"

CONFERENCES = [
    "Conference USA", "Mountain West", "Independent",
    "Big Ten", "Big 12", "Sun Belt",
    "American", "C-USA", "CUSA", "Pac-12",
    "ACC", "SEC", "MAC"
]

ALIASES = {
    "Miami (FL)": "Miami-FL",
    "Miami (OH)": "Miami-OH",
    "Miami (Ohio)": "Miami-OH",
    "Pitt": "Pittsburgh",
    "UConn": "Connecticut",
    "WKU": "Western Kentucky",
    "NIU": "Northern Illinois",
    "UCF": "Central Florida",
    "FAU": "Florida Atlantic",
    "FIU": "Florida International",
    "UMass": "Massachusetts",
    "USF": "South Florida",
    "App State": "Appalachian State",
    "ULM": "UL-Monroe",
    "San José State": "San Jose State",
    "Texas AandM": "Texas A&M",
}

def canon_team(s):
    s = re.sub(r"\s+", " ", str(s or "").strip())
    return ALIASES.get(s, s)

def parse_line(line):
    line = re.sub(r"\s+", " ", line).strip()
    if not line or line.lower().startswith(("rank ", "kford", "copyright")):
        return None

    conf_alt = "|".join(re.escape(c) for c in sorted(CONFERENCES, key=len, reverse=True))
    pat = re.compile(rf"^(\d+)\s+(.+?)\s+({conf_alt})\s+([-+]?\d+(?:\.\d+)?)\s+(\d+)\s+(\d+)$")
    m = pat.match(line)
    if not m:
        return None

    rank, team, conf, rating, wins, losses = m.groups()
    return {
        "rank": int(rank),
        "team": canon_team(team),
        "conference": conf,
        "kford": float(rating),
        "wins": int(wins),
        "losses": int(losses),
        "team_raw": team,
    }

def main():
    if not INFILE.exists():
        raise SystemExit(f"Missing {INFILE}. Create it by pasting the KFord table text there.")

    text = INFILE.read_text(encoding="utf-8", errors="ignore")
    lines = [x.strip() for x in text.splitlines() if x.strip()]

    rows = []
    for line in lines:
        r = parse_line(line)
        if r:
            rows.append(r)

    df = pd.DataFrame(rows)

    if df.empty or len(df) < 100:
        print("rows parsed:", 0 if df.empty else len(df))
        print("First 40 input lines:")
        print("\n".join(lines[:40]))
        raise SystemExit("KFord manual parse failed / parsed too few rows.")

    df = df.drop_duplicates("rank").sort_values("rank")
    df.to_csv(OUT, index=False)

    print("rows parsed:", len(df))
    print(df.head(25).to_string(index=False))
    print()
    print("unique teams:", df["team"].nunique())
    print("duplicates:", df[df["team"].duplicated(keep=False)]["team"].tolist())
    print("missing kford:", df["kford"].isna().sum())
    print("Wrote", OUT)

if __name__ == "__main__":
    main()
