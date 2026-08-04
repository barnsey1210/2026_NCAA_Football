#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import re
import json
import pandas as pd

INFILE = Path("data/ratings/external_sources/massey_visible_ratings_table.txt")
OUTFILE = Path("data/ratings/external_sources/massey_latest.csv")
AUDIT = Path("data/ratings/external_sources/massey_parse_audit.csv")

TEAM_ALIASES = {
    "Arizona St": "Arizona State",
    "Ball St": "Ball State",
    "C Michigan": "Central Michigan",
    "Coastal Car": "Coastal Carolina",
    "E Michigan": "Eastern Michigan",
    "FL Atlantic": "Florida Atlantic",
    "Florida St": "Florida State",
    "Ga Southern": "Georgia Southern",
    "Jacksonville St": "Jacksonville State",
    "Kennesaw": "Kennesaw State",
    "MTSU": "Middle Tennessee",
    "Missouri St": "Missouri State",
    "N Dakota St": "North Dakota State",
    "N Illinois": "Northern Illinois",
    "CS Sacramento": "Sacramento State",
    "ULM": "UL-Monroe",
    "UT San Antonio": "UTSA",
    "WKU": "Western Kentucky",
    "W Michigan": "Western Michigan",
    "Ohio St": "Ohio State",
    "Penn St": "Penn State",
    "Notre Dame": "Notre Dame",
    "Miami FL": "Miami-FL",
    "Southern California": "USC",
    "Mississippi": "Ole Miss",
    "North Carolina St": "NC State",
    "NC St": "NC State",
    "Central Florida": "Central Florida",
    "UCF": "Central Florida",
    "Florida Intl": "Florida International",
    "FIU": "Florida International",
    "Middle Tenn": "Middle Tennessee",
    "Middle Tennessee St": "Middle Tennessee",
    "Western Kentucky": "Western Kentucky",
    "W Kentucky": "Western Kentucky",
    "Louisiana": "Louisiana",
    "Louisiana Lafayette": "Louisiana",
    "UL Lafayette": "Louisiana",
    "Louisiana Monroe": "UL-Monroe",
    "UL Monroe": "UL-Monroe",
    "La Monroe": "UL-Monroe",
    "Appalachian St": "Appalachian State",
    "Arkansas St": "Arkansas State",
    "Boise St": "Boise State",
    "Colorado St": "Colorado State",
    "Fresno St": "Fresno State",
    "Georgia St": "Georgia State",
    "Iowa St": "Iowa State",
    "Kansas St": "Kansas State",
    "Kennesaw St": "Kennesaw State",
    "Kent": "Kent State",
    "Kent St": "Kent State",
    "Michigan St": "Michigan State",
    "Mississippi St": "Mississippi State",
    "New Mexico St": "New Mexico State",
    "North Texas St": "North Texas",
    "Oklahoma St": "Oklahoma State",
    "Oregon St": "Oregon State",
    "San Diego St": "San Diego State",
    "San Jose St": "San Jose State",
    "Texas St": "Texas State",
    "Utah St": "Utah State",
    "Washington St": "Washington State",
    "Bowling Green St": "Bowling Green",
    "Miami OH": "Miami-OH",
    "Miami (OH)": "Miami-OH",
    "Hawaii": "Hawaii",
    "Hawai'i": "Hawaii",
    "Sam Houston St": "Sam Houston",
    "Sam Houston State": "Sam Houston",
}

def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def canon_team(x):
    s = re.sub(r"\s+", " ", str(x or "").strip())
    return TEAM_ALIASES.get(s, s)

def fnum(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None

def inum(x):
    n = fnum(x)
    return int(n) if n is not None else None

def parse_hfa_sos_line(line):
    # Example: "2.26    1"
    vals = re.findall(r"[-+]?\d+(?:\.\d+)?", str(line))
    if len(vals) >= 2:
        return float(vals[0]), int(float(vals[1]))
    if len(vals) == 1:
        return float(vals[0]), None
    return None, None

def parse_ew_el_line(line):
    # Example: "10.20   1.80"
    vals = re.findall(r"[-+]?\d+(?:\.\d+)?", str(line))
    if len(vals) >= 2:
        return float(vals[0]), float(vals[1])
    return None, None

def main():
    lines = [x.strip() for x in INFILE.read_text(errors="ignore").splitlines()]
    lines = [x for x in lines if x]

    # remove header/correlation
    cleaned = []
    skip_prefixes = {"Team", "Correlation"}
    for line in lines:
        first = line.split()[0] if line.split() else ""
        if first in skip_prefixes:
            continue
        cleaned.append(line)

    rows = []
    audit = []
    i = 0

    while i + 16 < len(cleaned):
        try:
            team_raw = cleaned[i]
            conf = cleaned[i+1]
            record = cleaned[i+2]
            record_decimal = fnum(cleaned[i+3])

            rating_rank = inum(cleaned[i+4])
            rating = fnum(cleaned[i+5])

            power_rank = inum(cleaned[i+6])
            power = fnum(cleaned[i+7])

            off_rank = inum(cleaned[i+8])
            off_rating = fnum(cleaned[i+9])

            def_rank = inum(cleaned[i+10])
            def_rating = fnum(cleaned[i+11])

            hfa, sos_rank = parse_hfa_sos_line(cleaned[i+12])
            sos = fnum(cleaned[i+13])

            ssf_rank = inum(cleaned[i+14])
            ssf = fnum(cleaned[i+15])

            expected_wins, expected_losses = parse_ew_el_line(cleaned[i+16])

            # A valid row should have ranks/ratings and a record like 0-0.
            if not re.search(r"\d+-\d+", record) or rating_rank is None or rating is None:
                audit.append({"status": "skipped_bad_block", "line_index": i, "line": team_raw})
                i += 1
                continue

            team = canon_team(team_raw)

            rows.append({
                "snapshot_date": datetime.now().date().isoformat(),
                "season": 2026,
                "source": "Massey Ratings",
                "team": team,
                "raw_team": team_raw,
                "conference": conf,
                "record": record,
                "record_decimal": record_decimal,
                "rank": rating_rank,
                "rating": rating,
                "power_rank": power_rank,
                "power": power,
                "off_rank": off_rank,
                "off_rating": off_rating,
                "def_rank": def_rank,
                "def_rating": def_rating,
                "hfa": hfa,
                "sos_rank": sos_rank,
                "sos": sos,
                "ssf_rank": ssf_rank,
                "ssf": ssf,
                "expected_wins": expected_wins,
                "expected_losses": expected_losses,
                "source_url": "https://masseyratings.com/cf/fbs/ratings",
                "pulled_at": now_utc(),
                "notes": "Parsed from manually copied/rendered Massey ratings table.",
            })
            audit.append({"status": "parsed", "line_index": i, "team": team, "raw_team": team_raw})
            i += 17

        except Exception as e:
            audit.append({"status": f"error: {e}", "line_index": i, "line": cleaned[i] if i < len(cleaned) else ""})
            i += 1

    out = pd.DataFrame(rows)
    out.to_csv(OUTFILE, index=False)
    pd.DataFrame(audit).to_csv(AUDIT, index=False)

    print(f"Wrote {OUTFILE}: {len(out)} rows")
    print(f"Wrote {AUDIT}")
    if len(out):
        print(out.head(25).to_string(index=False))
        print("\nLast 10:")
        print(out.tail(10).to_string(index=False))

if __name__ == "__main__":
    main()
