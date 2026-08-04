#!/usr/bin/env python3

from pathlib import Path
import re
import pandas as pd
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "ratings" / "raw" / "bradpowers"
OUT = ROOT / "data" / "ratings" / "bradpowers_2026_latest.csv"
TEXT_OUT = ROOT / "data" / "ratings" / "raw" / "bradpowers" / "bradpowers_latest_extracted.txt"

ALIASES = {
    "Miami (FL)": "Miami-FL",
    "Miami (Ohio)": "Miami-OH",
    "Miami (OH)": "Miami-OH",
    "Pitt": "Pittsburgh",
    "USF": "South Florida",
    "UCF": "Central Florida",
    "UConn": "Connecticut",
    "FAU": "Florida Atlantic",
    "FIU": "Florida International",
    "UMass": "Massachusetts",
    "WKU": "Western Kentucky",
    "NIU": "Northern Illinois",
    "ULM": "UL-Monroe",
    "San José State": "San Jose State",
    "App State": "Appalachian State",

    "UL-Lafayette": "Louisiana",
    "UL Lafayette": "Louisiana",
    "Sam Houston State": "Sam Houston",
    "Texas AandM": "Texas A&M",
}

def canon_team(s):
    s = re.sub(r"\s+", " ", str(s or "").strip())
    return ALIASES.get(s, s)

def latest_pdf():
    supplied = sorted((ROOT / "data" / "ratings").glob("Powers_*.pdf"), key=lambda p: p.stat().st_mtime)
    files = supplied or sorted(RAW_DIR.glob("bradpowers_*.pdf"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise SystemExit("No Brad Powers PDF found. Run test_rating_sources.py first.")
    return files[-1]

def extract_text(pdf_path):
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n".join(pages)
    TEXT_OUT.write_text(text, encoding="utf-8")
    return text

def parse_rows(text):
    rows = []

    # Brad Powers row shape:
    # 1. Indiana 79.40 96.40 +17.0
    # 10. Ole Miss 80.86 83.86 +3.0
    # Team names can contain spaces and parentheses.
    # The 2026 PDF lays out three rankings columns on each extracted text line,
    # so scan for every row-shaped match rather than anchoring one row per line.
    pat = re.compile(
        r"(\d{1,3})\.\s+([A-Za-z&().'\- ]+?)\s+"
        r"(\d{2,3}\.\d{2})\s+(\d{2,3}\.\d{2})\s+([+-]\d+(?:\.\d+)?)"
    )

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        for m in pat.finditer(line):
            rank, team, start, now, diff = m.groups()
            rows.append({
                "rank": int(rank),
                "team": canon_team(team),
                "bradpowers_start": float(start),
                "bradpowers": float(now),
                "bradpowers_diff": float(diff),
                "team_raw": team,
            })

    df = pd.DataFrame(rows)

    if df.empty:
        raise SystemExit("No Brad Powers rating rows parsed.")

    df = df.drop_duplicates("rank").sort_values(["rank", "team"])

    expected = set(range(1, 139))
    parsed = set(df["rank"])
    if parsed != expected:
        raise SystemExit(f"Brad Powers coverage mismatch: missing={sorted(expected-parsed)} extra={sorted(parsed-expected)}")
    if df["team"].duplicated().any():
        raise SystemExit(f"Duplicate Brad Powers teams: {df[df['team'].duplicated(False)]['team'].tolist()}")

    return df

def main():
    pdf = latest_pdf()
    print("PDF:", pdf)

    text = extract_text(pdf)
    print("Extracted text:", TEXT_OUT)

    df = parse_rows(text)

    # Normalize Brad Powers to a zero-centered power-rating scale.
    # Raw Brad Powers numbers are on a high baseline scale, while SP+/FPI/KFord/etc.
    # are already centered around an average team near 0.
    bp_avg = df["bradpowers"].mean()
    df["bradpowers_raw"] = df["bradpowers"]
    df["bradpowers_avg"] = bp_avg
    df["bradpowers"] = df["bradpowers_raw"] - bp_avg

    print("rows parsed:", len(df))
    print("Brad Powers raw average:", round(bp_avg, 4))
    print(df.head(30).to_string(index=False))
    print()
    print("unique teams:", df["team"].nunique())
    print("duplicates:", df[df["team"].duplicated(keep=False)]["team"].tolist())
    print("missing bradpowers:", df["bradpowers"].isna().sum())

    if len(df) != 138:
        raise SystemExit(f"Expected 138 Brad Powers teams; parsed {len(df)}.")

    df.to_csv(OUT, index=False)
    print("Wrote", OUT)
    m = re.search(r"Powers_(\d{1,2})-(\d{1,2})-(\d{2,4})", pdf.stem, re.I)
    if m:
        month, day, year = map(int, m.groups())
        year = year + 2000 if year < 100 else year
        dated_out = OUT.with_name(f"bradpowers_{year:04d}-{month:02d}-{day:02d}.csv")
        df.to_csv(dated_out, index=False)
        print("Wrote", dated_out)

if __name__ == "__main__":
    main()
