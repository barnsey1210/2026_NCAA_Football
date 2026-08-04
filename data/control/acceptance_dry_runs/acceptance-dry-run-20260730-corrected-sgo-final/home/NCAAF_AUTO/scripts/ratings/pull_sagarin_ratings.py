#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import re
import json
import pandas as pd
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUTDIR = Path("data/ratings/external_sources")
OUTDIR.mkdir(parents=True, exist_ok=True)

URL = "https://sagarin.com/sports/cfsend.htm"
HEADERS = {"User-Agent": "Mozilla/5.0"}

TEAM_ALIASES = {
    "LOUISIANA-LAFAYETTE": "Louisiana",
    "LOUISIANAMONROE": "UL-Monroe",
    "LOUISIANA MONROE": "UL-Monroe",
    "MIAMI-OHIO": "Miami-OH",
    "SAM HOUSTON STATE": "Sam Houston",
    "SAM HOUSTON": "Sam Houston",
    "UCLA": "UCLA",
    "SOUTHERN CALIFORNIA": "USC",
    "ARMY WEST POINT": "Army",
    "FLA. INTERNATIONAL": "Florida International",
    "FLA INTERNATIONAL": "Florida International",
    "MIAMI FLORIDA": "Miami-FL",
    "MIAMI-FLORIDA": "Miami-FL",
    "MIAMI (FL)": "Miami-FL",
    "MISSISSIPPI": "Ole Miss",
    "MISSISSIPPI ST": "Mississippi State",
    "MISSISSIPPI STATE": "Mississippi State",
    "FLORIDA INTL": "Florida International",
    "FIU": "Florida International",
    "MIDDLE TENN ST": "Middle Tennessee",
    "MIDDLE TENNESSEE ST": "Middle Tennessee",
    "MIDDLE TENNESSEE": "Middle Tennessee",
    "BOWLING GREEN ST": "Bowling Green",
    "KENT ST": "Kent State",
    "BALL ST": "Ball State",
    "APPALACHIAN ST": "Appalachian State",
    "ARKANSAS ST": "Arkansas State",
    "BOISE ST": "Boise State",
    "COLORADO ST": "Colorado State",
    "FRESNO ST": "Fresno State",
    "GEORGIA ST": "Georgia State",
    "GEORGIA SOUTHERN": "Georgia Southern",
    "JAMES MADISON": "James Madison",
    "JMU": "James Madison",
    "KANSAS ST": "Kansas State",
    "KENNESAW ST": "Kennesaw State",
    "LOUISIANA LAFAYETTE": "Louisiana",
    "LA LAFAYETTE": "Louisiana",
    "LOUISIANA": "Louisiana",
    "LA MONROE": "UL-Monroe",
    "UL MONROE": "UL-Monroe",
    "LOUISIANA MONROE": "UL-Monroe",
    "NEW MEXICO ST": "New Mexico State",
    "NORTH TEXAS ST": "North Texas",
    "NORTH TEXAS": "North Texas",
    "OREGON ST": "Oregon State",
    "SAN DIEGO ST": "San Diego State",
    "SAN JOSE ST": "San Jose State",
    "TEXAS ST": "Texas State",
    "UTAH ST": "Utah State",
    "WASHINGTON ST": "Washington State",
    "WESTERN KY": "Western Kentucky",
    "W KENTUCKY": "Western Kentucky",
    "WESTERN KENTUCKY": "Western Kentucky",
    "EAST CAROLINA": "East Carolina",
    "UCF": "Central Florida",
    "CENTRAL FLORIDA": "Central Florida",
    "CONNECTICUT": "Connecticut",
    "UMASS": "Massachusetts",
    "MASSACHUSETTS": "Massachusetts",
    "HAWAI'I": "Hawaii",
    "HAWAII": "Hawaii",
    "ARMY": "Army",
    "NAVY": "Navy",
    "BYU": "BYU",
    "SMU": "SMU",
    "TCU": "TCU",
    "UAB": "UAB",
    "UTEP": "UTEP",
    "UTSA": "UTSA",
    "UNLV": "UNLV",
    "USC": "USC",
    "LSU": "LSU",
    "NC STATE": "NC State",
    "OHIO ST": "Ohio State",
    "PENN ST": "Penn State",
    "MICHIGAN ST": "Michigan State",
    "IOWA ST": "Iowa State",
    "OKLAHOMA ST": "Oklahoma State",
    "TEXAS A&M": "Texas A&M",
    "TEXAS TECH": "Texas Tech",
    "VIRGINIA TECH": "Virginia Tech",
    "GEORGIA TECH": "Georgia Tech",
}

def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def canon_team(raw):
    s = str(raw or "").strip()
    s = re.sub(r"\s+", " ", s)

    # Sagarin appends class markers such as A / AA after team names.
    s = re.sub(r"\s+(A|AA|Aa|AAA)\s*$", "", s).strip()

    upper = s.upper()
    if upper in TEAM_ALIASES:
        return TEAM_ALIASES[upper]

    out = s.title()
    replacements = {
        " Nc ": " NC ",
        " Byu": "BYU",
        " Smu": "SMU",
        " Tcu": "TCU",
        " Uab": "UAB",
        " Utep": "UTEP",
        " Utsa": "UTSA",
        " Unlv": "UNLV",
        " Usc": "USC",
        " Lsu": "LSU",
    }
    for a, b in replacements.items():
        out = out.replace(a, b)
    if out == "Byu": out = "BYU"
    if out == "Smu": out = "SMU"
    if out == "Tcu": out = "TCU"
    if out == "Usc": out = "USC"
    if out == "Lsu": out = "LSU"
    return out

def clean_num(x):
    if x is None:
        return None
    m = re.search(r"[-+]?\d+(?:\.\d+)?", str(x))
    return float(m.group(0)) if m else None

def fetch():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=45)
    except requests.exceptions.SSLError:
        r = requests.get(URL, headers=HEADERS, timeout=45, verify=False)

    if r.status_code != 200:
        # Some local Python SSL stacks need verify=False even after successful connection attempts.
        r = requests.get(URL, headers=HEADERS, timeout=45, verify=False)

    print("GET", r.status_code, URL)
    r.raise_for_status()
    raw_path = OUTDIR / "sagarin_raw.html"
    raw_path.write_text(r.text, encoding="utf-8")
    return r.text

def parse_sagarin_text(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")

    lines = [line.rstrip() for line in text.splitlines()]
    rows = []

    for line in lines:
        raw = line.strip()
        if not raw:
            continue

        # Common Sagarin line shape begins with rank then team then rating fields.
        # We keep this flexible and audit heavily.
        m = re.match(r"^\s*(\d{1,4})\s+([A-Za-z0-9 .'\-&()/]+?)\s+(?:=|\s)\s*(-?\d+(?:\.\d+)?)\b(.*)$", line)
        if not m:
            # Alternative: rank team rating without equals.
            m = re.match(r"^\s*(\d{1,4})\s+([A-Za-z0-9 .'\-&()/]+?)\s+(-?\d+(?:\.\d+)?)\s+(.*)$", line)
        if not m:
            continue

        rank = int(m.group(1))
        raw_team = re.sub(r"\([^)]*\)", "", m.group(2)).strip()
        raw_team = re.sub(r"\s+(A|AA|Aa|AAA)\s*$", "", raw_team).strip()
        rating = clean_num(m.group(3))
        rest = m.group(4) or ""

        # Filter obvious non-team/conference/header rows.
        if len(raw_team) < 2:
            continue
        if raw_team.upper() in {
            "HOME", "ROAD", "COLLEGE FOOTBALL", "RATING",
            "ACC", "BIG 12", "BIG TEN", "AMERICAN ATHLETIC", "CONF-USA",
            "CONFERENCE USA", "INDEPENDENTS", "MAC", "MOUNTAIN WEST",
            "PAC-12", "SEC", "SUN BELT", "C", "C INDIANA"
        }:
            continue
        if rank > 1000:
            continue

        # Numeric structure after the main rating generally looks like:
        # W, L, SCHEDL, SCHEDL_RANK, top10_w/l, top30_w/l,
        # predictor, predictor_rank, golden, golden_rank, recent, recent_rank,
        # strong_recent, strong_recent_rank, ...
        nums = [float(x) for x in re.findall(r"[-+]?\d+(?:\.\d+)?", rest)]

        wins = nums[0] if len(nums) >= 1 else None
        losses = nums[1] if len(nums) >= 2 else None
        sos = nums[2] if len(nums) >= 3 else None
        sos_rank = nums[3] if len(nums) >= 4 else None
        predictor = nums[8] if len(nums) >= 9 else None
        predictor_rank = nums[9] if len(nums) >= 10 else None
        golden = nums[10] if len(nums) >= 11 else None
        golden_rank = nums[11] if len(nums) >= 12 else None
        recent = nums[12] if len(nums) >= 13 else None
        recent_rank = nums[13] if len(nums) >= 14 else None
        strong_recent = nums[14] if len(nums) >= 15 else None
        strong_recent_rank = nums[15] if len(nums) >= 16 else None

        team = canon_team(raw_team)

        rows.append({
            "snapshot_date": datetime.now().date().isoformat(),
            "season": 2026,
            "source": "Sagarin",
            "team": team,
            "raw_team": raw_team,
            "rank": rank,
            "rating": rating,
            "wins": wins,
            "losses": losses,
            "sos": sos,
            "sos_rank": sos_rank,
            "predictor_rating": predictor,
            "predictor_rank": predictor_rank,
            "golden_mean_rating": golden,
            "golden_mean_rank": golden_rank,
            "recent_rating": recent,
            "recent_rank": recent_rank,
            "strong_recent_rating": strong_recent,
            "strong_recent_rank": strong_recent_rank,
            "raw_extra_numbers": json.dumps(nums[:20]),
            "source_url": URL,
            "pulled_at": now_utc(),
            "notes": "preformatted text parse; rating components parsed from Sagarin fields",
        })

    return pd.DataFrame(rows)

def main():
    html = fetch()
    out = parse_sagarin_text(html)

    # Drop exact duplicate team/rank rows if any.
    if not out.empty:
        out = out.drop_duplicates(subset=["source", "team", "rank"], keep="first")

    out_path = OUTDIR / "sagarin_latest.csv"
    out.to_csv(out_path, index=False)

    print("Rows:", len(out))
    print("Wrote:", out_path)
    if len(out):
        print(out.head(40).to_string(index=False))

if __name__ == "__main__":
    main()
