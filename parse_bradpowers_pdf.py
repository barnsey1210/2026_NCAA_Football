#!/usr/bin/env python3

from pathlib import Path
import re
import pandas as pd
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "ratings" / "raw" / "bradpowers"
OUT = ROOT / "data" / "ratings" / "bradpowers_2025_test_latest.csv"
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
    files = sorted(RAW_DIR.glob("bradpowers_*.pdf"))
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
    pat = re.compile(
        r"^\s*(\d+)\.\s+(.+?)\s+(\d{2,3}\.\d{2})\s+(\d{2,3}\.\d{2})\s+([-+]?\d+(?:\.\d+)?)\s*$"
    )

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        m = pat.match(line)
        if not m:
            continue

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

    # Keep only the college football table. It should have ranks 1..136-ish.
    df = df.drop_duplicates("team").sort_values(["rank", "team"])

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

    if len(df) < 100:
        raise SystemExit("Parsed fewer than 100 rows. Need inspect PDF text.")

    df.to_csv(OUT, index=False)
    print("Wrote", OUT)

if __name__ == "__main__":
    main()
