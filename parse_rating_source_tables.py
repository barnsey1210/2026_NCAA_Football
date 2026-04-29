#!/usr/bin/env python3

from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "ratings" / "raw"
OUT = ROOT / "data" / "ratings"

def norm_team(s):
    s = str(s or "").strip()
    s = re.sub(r"\([^)]*\)", "", s)          # remove records like (12-2)
    s = re.sub(r"^\s*\d+\.\s*", "", s)       # remove rank prefix like 1. Ohio State
    s = s.replace("&", "and")
    s = s.replace("Hawaiʻi", "Hawaii").replace("Hawai'i", "Hawaii")
    s = s.replace("San José", "San Jose")
    s = re.sub(r"[^A-Za-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s

ALIASES = {
    # Common short names / acronyms
    "air force": "Air Force",
    "akron": "Akron",
    "alabama": "Alabama",
    "app": "Appalachian State",
    "app st": "Appalachian State",
    "app state": "Appalachian State",
    "appalachian state": "Appalachian State",
    "arizona": "Arizona",
    "arizona st": "Arizona State",
    "arizona state": "Arizona State",
    "arkansas": "Arkansas",
    "arkansas st": "Arkansas State",
    "arkansas state": "Arkansas State",
    "army": "Army",
    "auburn": "Auburn",
    "ball st": "Ball State",
    "ball state": "Ball State",
    "baylor": "Baylor",
    "bgsu": "Bowling Green",
    "boise st": "Boise State",
    "boise state": "Boise State",
    "boston coll": "Boston College",
    "boston college": "Boston College",
    "bowling green": "Bowling Green",
    "buffalo": "Buffalo",
    "byu": "BYU",
    "california": "California",
    "central florida": "Central Florida",
    "ucf": "Central Florida",
    "charlotte": "Charlotte",
    "cincinnati": "Cincinnati",
    "clemson": "Clemson",
    "cmu": "Central Michigan",
    "central michigan": "Central Michigan",
    "c michigan": "Central Michigan",
    "coastal car": "Coastal Carolina",
    "coastal caro": "Coastal Carolina",
    "coastal carolina": "Coastal Carolina",
    "colorado": "Colorado",
    "colorado st": "Colorado State",
    "colorado state": "Colorado State",
    "connecticut": "Connecticut",
    "uconn": "Connecticut",
    "delaware": "Delaware",
    "duke": "Duke",
    "e carolina": "East Carolina",
    "ecu": "East Carolina",
    "east carolina": "East Carolina",
    "emu": "Eastern Michigan",
    "e michigan": "Eastern Michigan",
    "eastern michigan": "Eastern Michigan",
    "fau": "Florida Atlantic",
    "florida atlantic": "Florida Atlantic",
    "fiu": "Florida International",
    "florida intl": "Florida International",
    "florida international": "Florida International",
    "florida": "Florida",
    "florida st": "Florida State",
    "florida state": "Florida State",
    "fresno st": "Fresno State",
    "fresno state": "Fresno State",
    "ga southern": "Georgia Southern",
    "georgia so": "Georgia Southern",
    "georgia southern": "Georgia Southern",
    "ga state": "Georgia State",
    "georgia st": "Georgia State",
    "georgia state": "Georgia State",
    "ga tech": "Georgia Tech",
    "georgia tech": "Georgia Tech",
    "georgia": "Georgia",
    "hawaii": "Hawaii",
    "houston": "Houston",
    "illinois": "Illinois",
    "indiana": "Indiana",
    "iowa": "Iowa",
    "iowa st": "Iowa State",
    "iowa state": "Iowa State",
    "j ville state": "Jacksonville State",
    "jacksonville st": "Jacksonville State",
    "jacksonville state": "Jacksonville State",
    "j madison": "James Madison",
    "jmu": "James Madison",
    "james madison": "James Madison",
    "kansas": "Kansas",
    "kansas st": "Kansas State",
    "kansas state": "Kansas State",
    "kennesaw st": "Kennesaw State",
    "kennesaw state": "Kennesaw State",
    "kent st": "Kent State",
    "kent state": "Kent State",
    "kentucky": "Kentucky",
    "la tech": "Louisiana Tech",
    "louisiana tech": "Louisiana Tech",
    "liberty": "Liberty",
    "louisiana": "Louisiana",
    "la lafayette": "Louisiana",
    "louisiana lafayette": "Louisiana",
    "ul lafayette": "Louisiana",
    "louisiana monroe": "UL-Monroe",
    "ul monroe": "UL-Monroe",
    "ulm": "UL-Monroe",
    "louisville": "Louisville",
    "lsu": "LSU",
    "marshall": "Marshall",
    "maryland": "Maryland",
    "massachusetts": "Massachusetts",
    "umass": "Massachusetts",
    "memphis": "Memphis",
    "miami": "Miami-FL",
    "miami fl": "Miami-FL",
    "miami florida": "Miami-FL",
    "miami oh": "Miami-OH",
    "miami ohio": "Miami-OH",
    "michigan": "Michigan",
    "michigan st": "Michigan State",
    "michigan state": "Michigan State",
    "middle tenn": "Middle Tennessee",
    "mtsu": "Middle Tennessee",
    "middle tennessee": "Middle Tennessee",
    "minnesota": "Minnesota",
    "miss st": "Mississippi State",
    "mississippi st": "Mississippi State",
    "mississippi state": "Mississippi State",
    "missouri": "Missouri",
    "missouri st": "Missouri State",
    "missouri state": "Missouri State",
    "navy": "Navy",
    "nc state": "NC State",
    "n c state": "NC State",
    "north carolina state": "NC State",
    "nebraska": "Nebraska",
    "nevada": "Nevada",
    "new mexico": "New Mexico",
    "new mexico st": "New Mexico State",
    "nmsu": "New Mexico State",
    "new mexico state": "New Mexico State",
    "n carolina": "North Carolina",
    "north carolina": "North Carolina",
    "n dakota st": "North Dakota State",
    "ndsu": "North Dakota State",
    "north dakota state": "North Dakota State",
    "n texas": "North Texas",
    "north texas": "North Texas",
    "niu": "Northern Illinois",
    "n illinois": "Northern Illinois",
    "northern illinois": "Northern Illinois",
    "northwestern": "Northwestern",
    "notre dame": "Notre Dame",
    "odu": "Old Dominion",
    "old dominion": "Old Dominion",
    "ohio": "Ohio",
    "ohio st": "Ohio State",
    "ohio state": "Ohio State",
    "oklahoma": "Oklahoma",
    "oklahoma st": "Oklahoma State",
    "oklahoma state": "Oklahoma State",
    "ole miss": "Ole Miss",
    "mississippi": "Ole Miss",
    "oregon": "Oregon",
    "oregon st": "Oregon State",
    "oregon state": "Oregon State",
    "penn st": "Penn State",
    "penn state": "Penn State",
    "pittsburgh": "Pittsburgh",
    "pitt": "Pittsburgh",
    "purdue": "Purdue",
    "rice": "Rice",
    "rutgers": "Rutgers",
    "sac state": "Sacramento State",
    "sacramento state": "Sacramento State",
    "s alabama": "South Alabama",
    "south alabama": "South Alabama",
    "s carolina": "South Carolina",
    "south carolina": "South Carolina",
    "s florida": "South Florida",
    "south florida": "South Florida",
    "usf": "South Florida",
    "sam houston": "Sam Houston",
    "san diego st": "San Diego State",
    "sdsu": "San Diego State",
    "san diego state": "San Diego State",
    "san jose st": "San Jose State",
    "san jose state": "San Jose State",
    "sjsu": "San Jose State",
    "smu": "SMU",
    "so miss": "Southern Miss",
    "southern miss": "Southern Miss",
    "southern mississippi": "Southern Miss",
    "stanford": "Stanford",
    "syracuse": "Syracuse",
    "tcu": "TCU",
    "temple": "Temple",
    "tennessee": "Tennessee",
    "texas": "Texas",
    "texas a m": "Texas A&M",
    "texas am": "Texas A&M",
    "texas aandm": "Texas A&M",
    "texas st": "Texas State",
    "texas state": "Texas State",
    "texas tech": "Texas Tech",
    "toledo": "Toledo",
    "troy": "Troy",
    "tulane": "Tulane",
    "tulsa": "Tulsa",
    "uab": "UAB",
    "ucla": "UCLA",
    "unlv": "UNLV",
    "usc": "USC",
    "southern california": "USC",
    "utah": "Utah",
    "utah st": "Utah State",
    "utah state": "Utah State",
    "utep": "UTEP",
    "utsa": "UTSA",
    "texas san antonio": "UTSA",
    "ut san antonio": "UTSA",
    "vanderbilt": "Vanderbilt",
    "virginia": "Virginia",
    "va tech": "Virginia Tech",
    "virginia tech": "Virginia Tech",
    "wake forest": "Wake Forest",
    "washington": "Washington",
    "wash st": "Washington State",
    "washington st": "Washington State",
    "washington state": "Washington State",
    "w virginia": "West Virginia",
    "west virginia": "West Virginia",
    "wku": "Western Kentucky",
    "w kentucky": "Western Kentucky",
    "western kentucky": "Western Kentucky",
    "w michigan": "Western Michigan",
    "wmu": "Western Michigan",
    "western michigan": "Western Michigan",
    "wisconsin": "Wisconsin",
    "wyoming": "Wyoming",

    # FPI mascot-name rows
    "air force falcons": "Air Force",
    "akron zips": "Akron",
    "alabama crimson tide": "Alabama",
    "app state mountaineers": "Appalachian State",
    "arizona state sun devils": "Arizona State",
    "arizona wildcats": "Arizona",
    "arkansas razorbacks": "Arkansas",
    "arkansas state red wolves": "Arkansas State",
    "army black knights": "Army",
    "auburn tigers": "Auburn",
    "ball state cardinals": "Ball State",
    "baylor bears": "Baylor",
    "boise state broncos": "Boise State",
    "boston college eagles": "Boston College",
    "bowling green falcons": "Bowling Green",
    "buffalo bulls": "Buffalo",
    "byu cougars": "BYU",
    "california golden bears": "California",
    "central michigan chippewas": "Central Michigan",
    "charlotte 49ers": "Charlotte",
    "cincinnati bearcats": "Cincinnati",
    "clemson tigers": "Clemson",
    "coastal carolina chanticleers": "Coastal Carolina",
    "colorado buffaloes": "Colorado",
    "colorado state rams": "Colorado State",
    "delaware blue hens": "Delaware",
    "duke blue devils": "Duke",
    "east carolina pirates": "East Carolina",
    "eastern michigan eagles": "Eastern Michigan",
    "florida atlantic owls": "Florida Atlantic",
    "florida gators": "Florida",
    "florida international panthers": "Florida International",
    "florida state seminoles": "Florida State",
    "fresno state bulldogs": "Fresno State",
    "georgia bulldogs": "Georgia",
    "georgia southern eagles": "Georgia Southern",
    "georgia state panthers": "Georgia State",
    "georgia tech yellow jackets": "Georgia Tech",
    "hawaii rainbow warriors": "Hawaii",
    "houston cougars": "Houston",
    "illinois fighting illini": "Illinois",
    "indiana hoosiers": "Indiana",
    "iowa hawkeyes": "Iowa",
    "iowa state cyclones": "Iowa State",
    "jacksonville state gamecocks": "Jacksonville State",
    "james madison dukes": "James Madison",
    "kansas jayhawks": "Kansas",
    "kansas state wildcats": "Kansas State",
    "kennesaw state owls": "Kennesaw State",
    "kent state golden flashes": "Kent State",
    "kentucky wildcats": "Kentucky",
    "liberty flames": "Liberty",
    "louisiana ragin cajuns": "Louisiana",
    "louisiana tech bulldogs": "Louisiana Tech",
    "louisville cardinals": "Louisville",
    "lsu tigers": "LSU",
    "marshall thundering herd": "Marshall",
    "maryland terrapins": "Maryland",
    "massachusetts minutemen": "Massachusetts",
    "memphis tigers": "Memphis",
    "miami hurricanes": "Miami-FL",
    "miami redhawks": "Miami-OH",
    "michigan state spartans": "Michigan State",
    "michigan wolverines": "Michigan",
    "middle tennessee blue raiders": "Middle Tennessee",
    "minnesota golden gophers": "Minnesota",
    "mississippi state bulldogs": "Mississippi State",
    "missouri state bears": "Missouri State",
    "missouri tigers": "Missouri",
    "navy midshipmen": "Navy",
    "nc state wolfpack": "NC State",
    "nebraska cornhuskers": "Nebraska",
    "nevada wolf pack": "Nevada",
    "new mexico lobos": "New Mexico",
    "new mexico state aggies": "New Mexico State",
    "north carolina tar heels": "North Carolina",
    "north texas mean green": "North Texas",
    "northern illinois huskies": "Northern Illinois",
    "northwestern wildcats": "Northwestern",
    "notre dame fighting irish": "Notre Dame",
    "ohio bobcats": "Ohio",
    "ohio state buckeyes": "Ohio State",
    "oklahoma sooners": "Oklahoma",
    "oklahoma state cowboys": "Oklahoma State",
    "old dominion monarchs": "Old Dominion",
    "ole miss rebels": "Ole Miss",
    "oregon ducks": "Oregon",
    "oregon state beavers": "Oregon State",
    "penn state nittany lions": "Penn State",
    "pittsburgh panthers": "Pittsburgh",
    "purdue boilermakers": "Purdue",
    "rice owls": "Rice",
    "rutgers scarlet knights": "Rutgers",
    "sam houston bearkats": "Sam Houston",
    "san diego state aztecs": "San Diego State",
    "san jose state spartans": "San Jose State",
    "smu mustangs": "SMU",
    "south alabama Jaguars".lower(): "South Alabama",
    "south carolina gamecocks": "South Carolina",
    "south florida bulls": "South Florida",
    "southern miss golden eagles": "Southern Miss",
    "stanford cardinal": "Stanford",
    "syracuse orange": "Syracuse",
    "tcu horned frogs": "TCU",
    "temple owls": "Temple",
    "tennessee volunteers": "Tennessee",
    "texas a m aggies": "Texas A&M",
    "texas aandm aggies": "Texas A&M",
    "texas longhorns": "Texas",
    "texas state bobcats": "Texas State",
    "texas tech red raiders": "Texas Tech",
    "toledo rockets": "Toledo",
    "troy trojans": "Troy",
    "tulane green wave": "Tulane",
    "tulsa golden hurricane": "Tulsa",
    "uab blazers": "UAB",
    "ucf knights": "Central Florida",
    "ucla bruins": "UCLA",
    "uconn huskies": "Connecticut",
    "ul monroe warhawks": "UL-Monroe",
    "unlv rebels": "UNLV",
    "usc trojans": "USC",
    "utah state aggies": "Utah State",
    "utah utes": "Utah",
    "utep miners": "UTEP",
    "utsa roadrunners": "UTSA",
    "vanderbilt commodores": "Vanderbilt",
    "virginia cavaliers": "Virginia",
    "virginia tech hokies": "Virginia Tech",
    "wake forest demon deacons": "Wake Forest",
    "washington huskies": "Washington",
    "washington state cougars": "Washington State",
    "west virginia mountaineers": "West Virginia",
    "western kentucky hilltoppers": "Western Kentucky",
    "western michigan broncos": "Western Michigan",
    "wisconsin badgers": "Wisconsin",
    "wyoming cowboys": "Wyoming",
}

def canonical(s):
    k = norm_team(s)
    if k in ALIASES:
        return ALIASES[k]
    out = " ".join(w.capitalize() for w in k.split())
    fixes = {
        "Lsu": "LSU", "Byu": "BYU", "Usc": "USC", "Ucla": "UCLA",
        "Smu": "SMU", "Tcu": "TCU", "Unlv": "UNLV", "Utep": "UTEP",
        "Uab": "UAB", "Utsa": "UTSA", "Ucf": "Central Florida", "Usf": "South Florida",
        "Fau": "Florida Atlantic", "Fiu": "Florida International", "Nc State": "NC State",
    }
    return fixes.get(out, out)

def latest_table(source, table_num):
    files = sorted((RAW / source).glob(f"{source}_table_{table_num}.csv"))
    if not files:
        raise SystemExit(f"Missing {source}_table_{table_num}.csv. Run test_rating_sources.py first.")
    return files[-1]

def parse_teamrankings():
    p = latest_table("teamrankings", 0)
    df = pd.read_csv(p)
    out = pd.DataFrame()
    out["team_raw"] = df["team"]
    out["team"] = out["team_raw"].map(canonical)
    out["teamrankings"] = pd.to_numeric(df["rating"], errors="coerce")
    out = out[["team", "teamrankings", "team_raw"]].sort_values("team")
    out.to_csv(OUT / "teamrankings_2025_test_latest.csv", index=False)
    return out

def parse_fpi():
    team_p = latest_table("fpi", 0)
    rating_p = latest_table("fpi", 1)
    teams = pd.read_csv(team_p)
    ratings = pd.read_csv(rating_p)

    if len(teams) != len(ratings):
        raise SystemExit(f"FPI team/rating row mismatch: teams={len(teams)} ratings={len(ratings)}")

    out = pd.DataFrame()
    out["team_raw"] = teams["team"]
    out["team"] = out["team_raw"].map(canonical)
    out["fpi"] = pd.to_numeric(ratings["power_index_fpi"], errors="coerce")
    out = out[["team", "fpi", "team_raw"]].sort_values("team")
    out.to_csv(OUT / "fpi_2025_test_latest.csv", index=False)
    return out

def parse_spplus():
    p = latest_table("spplus", 0)
    df = pd.read_csv(p)
    out = pd.DataFrame()
    out["team_raw"] = df["team"]
    out["team"] = out["team_raw"].map(canonical)
    out["spplus"] = pd.to_numeric(df["sp"], errors="coerce")
    out["spplus_off"] = df["off_sp"].astype(str).str.extract(r"([-+]?\d+(?:\.\d+)?)")[0].astype(float)
    out["spplus_def"] = df["def_sp"].astype(str).str.extract(r"([-+]?\d+(?:\.\d+)?)")[0].astype(float)
    out = out[["team", "spplus", "spplus_off", "spplus_def", "team_raw"]].sort_values("team")
    out.to_csv(OUT / "spplus_2026_from_espn_latest.csv", index=False)
    return out

def audit(name, df, expected=None):
    print(f"\n{name}")
    print("rows:", len(df))
    print("unique teams:", df["team"].nunique())
    print("duplicates:", df[df["team"].duplicated(keep=False)]["team"].tolist())
    rating_cols = [c for c in df.columns if c not in ("team", "team_raw")]
    for c in rating_cols:
        print(f"missing {c}:", df[c].isna().sum())
    print(df.head(15).to_string(index=False))

def main():
    tr = parse_teamrankings()
    fpi = parse_fpi()
    sp = parse_spplus()

    audit("TeamRankings parsed", tr)
    audit("FPI parsed", fpi)
    audit("SP+ parsed", sp)

    # Compare coverage to current 2026 SP+ team universe.
    current = pd.read_csv(OUT / "spplus_2026_latest.csv")
    current_teams = set(current["team"])
    for name, df in [("teamrankings", tr), ("fpi", fpi), ("spplus_espn", sp)]:
        teams = set(df["team"])
        missing = sorted(current_teams - teams)
        extra = sorted(teams - current_teams)
        print(f"\nCoverage vs 2026 site universe — {name}")
        print("missing from source:", len(missing), missing)
        print("extra in source:", len(extra), extra)

if __name__ == "__main__":
    main()
