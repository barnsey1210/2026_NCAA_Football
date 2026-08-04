#!/usr/bin/env python3

from pathlib import Path
import re
import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "ratings" / "raw" / "kford"
OUT = ROOT / "data" / "ratings"

CONFERENCES = [
    "American", "ACC", "Big Ten", "Big 12", "C-USA", "Conference USA",
    "Independent", "MAC", "Mountain West", "Pac-12", "SEC", "Sun Belt"
]

ALIASES = {
    "Miami (FL)": "Miami-FL",
    "Miami (OH)": "Miami-OH",
    "Texas AandM": "Texas A&M",
    "Texas A&M": "Texas A&M",
    "UCF": "Central Florida",
    "FAU": "Florida Atlantic",
    "FIU": "Florida International",
    "UMass": "Massachusetts",
    "USF": "South Florida",
    "App State": "Appalachian State",
    "ULM": "UL-Monroe",
    "Louisiana Monroe": "UL-Monroe",
    "Louisiana-Monroe": "UL-Monroe",
    "San José State": "San Jose State",
    "Bowling Green": "Bowling Green",
}

def canon_team(s):
    s = re.sub(r"\s+", " ", str(s or "").strip())
    return ALIASES.get(s, s)

def latest_html():
    files = sorted(RAW.glob("kford_*.html"))
    if not files:
        raise SystemExit("No KFord HTML files found. Run test_rating_sources.py first.")
    return files[-1]

def extract_text_from_html(path):
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style noise.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n")
    lines = [re.sub(r"\s+", " ", x).strip() for x in text.splitlines()]
    lines = [x for x in lines if x]
    return lines, text

def parse_lines(lines):
    rows = []

    conf_alt = "|".join(re.escape(c) for c in sorted(CONFERENCES, key=len, reverse=True))

    # Expected row shape:
    # 1 Indiana Big Ten 30.7 13 0
    # 7 Miami (FL) ACC 22.0 10 2
    pattern = re.compile(
        rf"^\s*(\d+)\s+(.+?)\s+({conf_alt})\s+([-+]?\d+(?:\.\d+)?)\s+(\d+)\s+(\d+)\s*$"
    )

    for line in lines:
        m = pattern.match(line)
        if not m:
            continue

        rank, team, conf, rating, wins, losses = m.groups()
        rows.append({
            "rank": int(rank),
            "team": canon_team(team),
            "conference": conf,
            "kford": float(rating),
            "wins": int(wins),
            "losses": int(losses),
            "team_raw": team,
        })

    return pd.DataFrame(rows)

def main():
    path = latest_html()
    print("Parsing:", path)

    lines, full_text = extract_text_from_html(path)
    df = parse_lines(lines)

    print("rows parsed:", len(df))

    if len(df) < 100:
        print("\nOnly parsed a small number of rows. Showing possible rating text snippets:")
        for i, line in enumerate(lines):
            if "Indiana" in line or "Ohio State" in line or "KFOR" in line or "Rating" in line:
                print(i, line)
        raise SystemExit("KFord parse did not find enough rows.")

    df = df.sort_values("rank")
    out = OUT / "kford_2025_test_latest.csv"
    df.to_csv(out, index=False)

    print(df.head(25).to_string(index=False))
    print()
    print("unique teams:", df["team"].nunique())
    print("duplicates:", df[df["team"].duplicated(keep=False)]["team"].tolist())
    print("missing kford:", df["kford"].isna().sum())
    print("Wrote", out)

if __name__ == "__main__":
    main()
