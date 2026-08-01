#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import re
import pandas as pd

ROOT = Path(".")
OUT = Path("data/ratings/ratings_latest.csv")
AUDIT = Path("data/ratings/ratings_audit.csv")

SITE_INDEX = Path("index.html")

SOURCE_FILES = {
    "Sagarin Predictor": Path("data/ratings/external_sources/sagarin_latest.csv"),
    "Donchess Overall": Path("data/ratings/external_sources/donchess_latest.csv"),
    "Massey Power": Path("data/ratings/external_sources/massey_latest.csv"),
}

# Existing source folders. We will probe these and use anything that looks parseable.
EXISTING_RAW_DIRS = {
    "SP+": Path("data/ratings/raw/spplus"),
    "FPI": Path("data/ratings/raw/fpi"),
    "KFord": Path("data/ratings/raw/kford"),
    "Brad Powers": Path("data/ratings/raw/bradpowers"),
    "TeamRankings": Path("data/ratings/raw/teamrankings"),
}

def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def norm(x):
    return re.sub(r"[^a-z0-9]+", " ", str(x or "").lower()).strip()

def load_site_teams():
    """Load the canonical 2026 team universe without parsing the V2 HTML shell."""

    master_path = Path("data/ratings/ratings_master_latest.csv")
    if master_path.exists():
        master = pd.read_csv(master_path)
        if "team" in master.columns:
            teams = (
                master[["team"]]
                .dropna()
                .drop_duplicates()
                .sort_values("team")
                .reset_index(drop=True)
            )
            if len(teams) >= 138:
                teams["conference"] = ""
                return teams[["team", "conference"]]

    latest_path = Path("data/ratings/ratings_latest.csv")
    if latest_path.exists():
        latest = pd.read_csv(latest_path)
        if "team" in latest.columns:
            teams = (
                latest[["team"]]
                .dropna()
                .drop_duplicates()
                .sort_values("team")
                .reset_index(drop=True)
            )
            if len(teams) >= 138:
                teams["conference"] = ""
                return teams[["team", "conference"]]

    spplus_path = Path("data/ratings/spplus_2026_latest.csv")
    if spplus_path.exists():
        spplus = pd.read_csv(spplus_path)
        if "team" in spplus.columns:
            teams = (
                spplus[["team"]]
                .dropna()
                .drop_duplicates()
                .sort_values("team")
                .reset_index(drop=True)
            )
            if len(teams) >= 138:
                teams["conference"] = ""
                return teams[["team", "conference"]]

    raise SystemExit(
        "Could not load the canonical 138-team universe from ratings_master_latest.csv, "
        "ratings_latest.csv, or spplus_2026_latest.csv"
    )

def find_col(df, candidates):
    cols = list(df.columns)
    clean = {norm(c): c for c in cols}
    for cand in candidates:
        if norm(cand) in clean:
            return clean[norm(cand)]
    for c in cols:
        cc = norm(c)
        for cand in candidates:
            if norm(cand) in cc:
                return c
    return None

def base_rows(df, source, team_col, rating_col, rank_col=None, raw_team_col=None, **extra):
    rows = []
    for _, r in df.iterrows():
        team = r.get(team_col)
        if pd.isna(team) or str(team).strip() == "":
            continue

        raw_team = r.get(raw_team_col) if raw_team_col else team

        def val(col):
            if col and col in df.columns:
                return r.get(col)
            return None

        rows.append({
            "snapshot_date": r.get("snapshot_date", datetime.now().date().isoformat()),
            "season": r.get("season", 2026),
            "source": source,
            "team": str(team).strip(),
            "raw_team": str(raw_team).strip(),
            "rank": val(rank_col),
            "rating": val(rating_col),
            "off_rating": extra.get("off_rating"),
            "def_rating": extra.get("def_rating"),
            "hfa": extra.get("hfa"),
            "sos": extra.get("sos"),
            "source_url": r.get("source_url", ""),
            "pulled_at": r.get("pulled_at", now_utc()),
            "source_updated_at": r.get("source_updated_at", ""),
            "notes": extra.get("notes", ""),
        })
    return rows

def load_sagarin(path):
    if not path.exists():
        return [], {"source": "Sagarin Predictor", "status": "missing", "path": str(path), "rows": 0}

    df = pd.read_csv(path)

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "snapshot_date": r.get("snapshot_date", datetime.now().date().isoformat()),
            "season": r.get("season", 2026),
            "source": "Sagarin Predictor",
            "team": r.get("team"),
            "raw_team": r.get("raw_team", r.get("team")),
            "rank": r.get("predictor_rank"),
            "rating": r.get("predictor_rating"),
            "off_rating": "",
            "def_rating": "",
            "hfa": "",
            "sos": r.get("sos"),
            "source_url": r.get("source_url", "https://sagarin.com/sports/cfsend.htm"),
            "pulled_at": r.get("pulled_at", now_utc()),
            "source_updated_at": "",
            "notes": "Default Sagarin source uses predictor_rating and predictor_rank.",
        })

    return rows, {"source": "Sagarin Predictor", "status": "ok", "path": str(path), "rows": len(rows)}

def load_donchess(path):
    if not path.exists():
        return [], {"source": "Donchess Overall", "status": "missing", "path": str(path), "rows": 0}

    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "snapshot_date": r.get("snapshot_date", datetime.now().date().isoformat()),
            "season": r.get("season", 2026),
            "source": "Donchess Overall",
            "team": r.get("team"),
            "raw_team": r.get("raw_team", r.get("team")),
            "rank": r.get("rank"),
            "rating": r.get("rating"),
            "off_rating": "",
            "def_rating": "",
            "hfa": "",
            "sos": r.get("sos"),
            "source_url": r.get("source_url", "https://www.dratings.com/sports/ncaa-fbs-football-ratings/"),
            "pulled_at": r.get("pulled_at", now_utc()),
            "source_updated_at": "",
            "notes": "Donchess Overall from DRatings table. Inference/Standard/Vegas retained in source file for future testing.",
        })
    return rows, {"source": "Donchess Overall", "status": "ok", "path": str(path), "rows": len(rows)}

def load_massey(path):
    if not path.exists():
        return [], {"source": "Massey Power", "status": "missing", "path": str(path), "rows": 0}

    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "snapshot_date": r.get("snapshot_date", datetime.now().date().isoformat()),
            "season": r.get("season", 2026),
            "source": "Massey Power",
            "team": r.get("team"),
            "raw_team": r.get("raw_team", r.get("team")),
            "rank": r.get("power_rank"),
            "rating": r.get("power"),
            "off_rating": r.get("off_rating"),
            "def_rating": r.get("def_rating"),
            "hfa": r.get("hfa"),
            "sos": r.get("sos"),
            "source_url": r.get("source_url", "https://masseyratings.com/cf/fbs/ratings"),
            "pulled_at": r.get("pulled_at", now_utc()),
            "source_updated_at": "",
            "notes": "Massey default rating uses Power column. Manual rendered-table source.",
        })
    return rows, {"source": "Massey Power", "status": "ok", "path": str(path), "rows": len(rows)}

def latest_csv_in_dir(path):
    if not path.exists():
        return None
    candidates = sorted(
        list(path.glob("*.csv")) + list(path.glob("*.xlsx")),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return candidates[0] if candidates else None

def load_generic_existing(source, path):
    latest = latest_csv_in_dir(path)
    if not latest:
        return [], {"source": source, "status": "missing/no files", "path": str(path), "rows": 0}

    try:
        if latest.suffix.lower() == ".xlsx":
            df = pd.read_excel(latest)
        else:
            df = pd.read_csv(latest)
    except Exception as e:
        return [], {"source": source, "status": f"read_error: {e}", "path": str(latest), "rows": 0}

    team_col = find_col(df, ["team", "Team", "school", "School", "name"])
    rating_col = find_col(df, ["rating", "power", "overall", "combo", "rank_rating", "Rating"])
    rank_col = find_col(df, ["rank", "Rank", "rk"])

    if not team_col or not rating_col:
        return [], {
            "source": source,
            "status": f"could_not_infer_columns team={team_col} rating={rating_col}",
            "path": str(latest),
            "rows": len(df),
            "columns": "|".join(map(str, df.columns)),
        }

    rows = base_rows(
        df,
        source=source,
        team_col=team_col,
        rating_col=rating_col,
        rank_col=rank_col,
        raw_team_col=team_col,
        notes=f"Generic parsed from {latest.name}; confirm rating column={rating_col}.",
    )

    return rows, {
        "source": source,
        "status": "ok_generic",
        "path": str(latest),
        "rows": len(rows),
        "team_col": team_col,
        "rating_col": rating_col,
        "rank_col": rank_col,
    }

def strip_record_team(x):
    s = str(x or "").strip()
    s = re.sub(r"\([^)]*\)", "", s).strip()
    s = re.sub(r"^\d+\.\s*", "", s).strip()
    return s

TEAM_ALIASES = {
    "Miami (OH) RedHawks": "Miami-OH",
    "Miami-OH RedHawks": "Miami-OH",
    "Miami RedHawks": "Miami-OH",
    "Kent St.": "Kent State",
    "Missouri St.": "Missouri State",
    # SP+ abbreviations
    "Penn St.": "Penn State",
    "S. Carolina": "South Carolina",
    "Kansas St.": "Kansas State",
    "Va. Tech": "Virginia Tech",
    "Florida St.": "Florida State",
    "Oklahoma St.": "Oklahoma State",
    "Arizona St.": "Arizona State",
    "Ga. Tech": "Georgia Tech",
    "Miss. St.": "Mississippi State",
    "N. Carolina": "North Carolina",
    "W. Virginia": "West Virginia",
    "Michigan St.": "Michigan State",
    "SDSU": "San Diego State",
    "NDSU": "North Dakota State",
    "Boston Coll.": "Boston College",
    "ECU": "East Carolina",
    "Fresno St.": "Fresno State",
    "USF": "South Florida",
    "Wash. St.": "Washington State",
    "ODU": "Old Dominion",
    "Texas St.": "Texas State",
    "Oregon St.": "Oregon State",
    "FAU": "Florida Atlantic",
    "WMU": "Western Michigan",
    "Utah St.": "Utah State",
    "J'ville State": "Jacksonville State",
    "Colorado St.": "Colorado State",
    "La. Tech": "Louisiana Tech",
    "Arkansas St.": "Arkansas State",
    "Ga. Southern": "Georgia Southern",
    "App. St.": "Appalachian State",
    "CMU": "Central Michigan",
    "BGSU": "Bowling Green",
    "S. Alabama": "South Alabama",
    "Coastal Caro.": "Coastal Carolina",
    "EMU": "Eastern Michigan",
    "SJSU": "San Jose State",
    "NMSU": "New Mexico State",
    "NIU": "Northern Illinois",
    "Sac State": "Sacramento State",
    "So. Miss": "Southern Miss",
    "Georgia St.": "Georgia State",

    # FPI mascot/short names
    "App State": "Appalachian State",
    "App State Mountaineers": "Appalachian State",
    "Arkansas State Red Wolves": "Arkansas State",
    "California Golden": "California",
    "California Golden Bears": "California",
    "Charlotte 49ers": "Charlotte",
    "Coastal Carolina Chanticleers": "Coastal Carolina",
    "Colorado Buffaloes": "Colorado",
    "East Carolina Pirates": "East Carolina",
    "Florida State Seminoles": "Florida State",
    "Hawai'i Rainbow Warriors": "Hawaii",
    "Kansas Jayhawks": "Kansas",
    "Marshall Thundering Herd": "Marshall",
    "Nebraska Cornhuskers": "Nebraska",
    "Old Dominion Monarchs": "Old Dominion",
    "Purdue Boilermakers": "Purdue",
    "Sam Houston Bearkats": "Sam Houston",
    "San Diego State Aztecs": "San Diego State",
    "San José State": "San Jose State",
    "San José State Spartans": "San Jose State",
    "South Alabama Jaguars": "South Alabama",
    "Southern Miss Golden": "Southern Miss",
    "Southern Miss Golden Eagles": "Southern Miss",
    "Stanford Cardinal": "Stanford",
    "Tulsa Golden Hurricane": "Tulsa",
    "UL Monroe Warhawks": "UL-Monroe",
    "Virginia Tech Hokies": "Virginia Tech",

    # TeamRankings abbreviations
    "Arizona St": "Arizona State",
    "C Michigan": "Central Michigan",
    "Coastal Car": "Coastal Carolina",
    "E Carolina": "East Carolina",
    "E Michigan": "Eastern Michigan",
    "Florida St": "Florida State",
    "Georgia So": "Georgia Southern",
    "J Madison": "James Madison",
    "Jacksonville St": "Jacksonville State",
    "Missouri St": "Missouri State",
    "N Illinois": "Northern Illinois",
    "N Texas": "North Texas",
    "S Alabama": "South Alabama",
    "S Florida": "South Florida",
    "Ohio St": "Ohio State",
    "Ohio State Buckeyes": "Ohio State",
    "Penn St": "Penn State",
    "Penn State Nittany Lions": "Penn State",
    "Notre Dame Fighting Irish": "Notre Dame",
    "Oregon Ducks": "Oregon",
    "Indiana Hoosiers": "Indiana",
    "Texas Tech Red Raiders": "Texas Tech",
    "Georgia Bulldogs": "Georgia",
    "Alabama Crimson Tide": "Alabama",
    "Miami": "Miami-FL",
    "Miami Hurricanes": "Miami-FL",
    "Miami Florida": "Miami-FL",
    "Miami (FL)": "Miami-FL",
    "Miami OH": "Miami-OH",
    "Miami (OH)": "Miami-OH",
    "Ole Miss Rebels": "Ole Miss",
    "Mississippi": "Ole Miss",
    "Mississippi St": "Mississippi State",
    "Florida Intl": "Florida International",
    "Florida Intl.": "Florida International",
    "Florida International Panthers": "Florida International",
    "FIU": "Florida International",
    "Kennesaw St": "Kennesaw State",
    "Kennesaw St.": "Kennesaw State",
    "Kennesaw State Owls": "Kennesaw State",
    "UConn": "Connecticut",
    "Connecticut Huskies": "Connecticut",
    "W Michigan": "Western Michigan",
    "Western Michigan Broncos": "Western Michigan",
    "NC State Wolfpack": "NC State",
    "NC State": "NC State",
    "UCF": "Central Florida",
    "UCF Knights": "Central Florida",
    "Central Florida": "Central Florida",
    "USC Trojans": "USC",
    "Southern California": "USC",
    "SMU Mustangs": "SMU",
    "TCU Horned Frogs": "TCU",
    "BYU Cougars": "BYU",
    "UTSA Roadrunners": "UTSA",
    "UAB Blazers": "UAB",
    "UNLV Rebels": "UNLV",
    "UTEP Miners": "UTEP",
    "Georgia Tech Yellow Jackets": "Georgia Tech",
    "Louisiana Ragin' Cajuns": "Louisiana",
    "La Lafayette": "Louisiana",
    "Louisiana-Lafayette": "Louisiana",
    "UL Monroe": "UL-Monroe",
    "ULM": "UL-Monroe",
    "Louisiana Monroe": "UL-Monroe",
    "JMU": "James Madison",
    "James Madison Dukes": "James Madison",
    "App St": "Appalachian State",
    "Appalachian St": "Appalachian State",
    "Arkansas St": "Arkansas State",
    "Boise St": "Boise State",
    "Colorado St": "Colorado State",
    "Fresno St": "Fresno State",
    "Georgia St": "Georgia State",
    "Iowa St": "Iowa State",
    "Kansas St": "Kansas State",
    "Kent St": "Kent State",
    "Ball St": "Ball State",
    "Bowling Green St": "Bowling Green",
    "Michigan St": "Michigan State",
    "New Mexico St": "New Mexico State",
    "North Texas Mean Green": "North Texas",
    "North Texas St": "North Texas",
    "Oklahoma St": "Oklahoma State",
    "Oregon St": "Oregon State",
    "San Diego St": "San Diego State",
    "San Jose St": "San Jose State",
    "Sam Houston St": "Sam Houston",
    "Sam Houston State": "Sam Houston",
    "Texas St": "Texas State",
    "Utah St": "Utah State",
    "Washington St": "Washington State",
    "WKU": "Western Kentucky",
    "W Kentucky": "Western Kentucky",
    "Middle Tenn": "Middle Tennessee",
    "MTSU": "Middle Tennessee",
    "Massachusetts Minutemen": "Massachusetts",
    "UMass": "Massachusetts",
    "Hawai'i": "Hawaii",
    "Hawaii Rainbow Warriors": "Hawaii",
    "Army Black Knights": "Army",
    "Navy Midshipmen": "Navy",
}

MASCOT_SUFFIXES = [
    "Buckeyes","Hoosiers","Ducks","Fighting Irish","Bulldogs","Red Raiders",
    "Hurricanes","Rebels","Crimson Tide","Utes","Longhorns","Aggies",
    "Cougars","Hawkeyes","Trojans","Sooners","Commodores","Wolverines",
    "Huskies","Mustangs","Nittany Lions","Horned Frogs","Fighting Illini",
    "Mean Green","Bulls","Cyclones","Volunteers","Midshipmen","Wildcats",
    "Cardinals","Cavaliers","Panthers","Green Wave","Tigers","Yellow Jackets",
    "Blue Devils","Wolfpack","Gators","Gamecocks","Sun Devils","Knights",
    "Bears","Bearcats","Cowboys","Mountaineers","Spartans","Badgers",
    "Terrapins","Scarlet Knights","Golden Gophers","Bruins","Orange",
    "Demon Deacons","Tar Heels","Razorbacks","Flames","Blue Hens",
    "Owls","Blue Raiders","Hilltoppers","Miners","Falcons","Lobos",
    "Wolf Pack","Zips","Cardinals","Chippewas","Eagles","Golden Flashes",
    "RedHawks","Bobcats","Rockets","Broncos","Rams","Beavers",
]

def canon_team(x):
    s = strip_record_team(x)
    s = re.sub(r"\s+", " ", s).strip()

    if s in TEAM_ALIASES:
        return TEAM_ALIASES[s]

    # Remove mascot suffixes, then check aliases again.
    for suffix in sorted(MASCOT_SUFFIXES, key=len, reverse=True):
        if s.endswith(" " + suffix):
            base = s[:-(len(suffix)+1)].strip()
            return TEAM_ALIASES.get(base, base)

    return TEAM_ALIASES.get(s, s)

def extract_ranked_team(x):
    s = str(x or "").strip()
    m = re.match(r"^\s*(\d+)\.\s*(.*?)\s*$", s)
    if m:
        return int(m.group(1)), canon_team(m.group(2))
    return None, canon_team(s)

def parse_num_first(x):
    if x is None:
        return None
    m = re.search(r"[-+]?\d+(?:\.\d+)?", str(x))
    return float(m.group(0)) if m else None

def _rank_series(values):
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric.rank(method="min", ascending=False).astype("Int64")


def load_spplus():
    source = "SP+"
    accepted = Path("data/ratings/spplus_2026_from_espn_latest.csv")
    raw_fallback = Path("data/ratings/raw/spplus/spplus_table_0.csv")

    if accepted.exists():
        df = pd.read_csv(accepted)
        required = {"team", "spplus", "spplus_off", "spplus_def"}
        missing = sorted(required - set(df.columns))
        if missing:
            return [], {
                "source": source,
                "status": f"accepted_missing_columns: {missing}",
                "path": str(accepted),
                "rows": len(df),
            }

        ranks = _rank_series(df["spplus"])
        rows = []
        for i, r in df.iterrows():
            rows.append({
                "snapshot_date": datetime.now().date().isoformat(),
                "season": 2026,
                "source": source,
                "team": str(r.get("team")).strip(),
                "raw_team": r.get("team_raw", r.get("team")),
                "rank": ranks.iloc[i],
                "rating": pd.to_numeric(r.get("spplus"), errors="coerce"),
                "off_rating": pd.to_numeric(r.get("spplus_off"), errors="coerce"),
                "def_rating": pd.to_numeric(r.get("spplus_def"), errors="coerce"),
                "hfa": "",
                "sos": "",
                "source_url": "",
                "pulled_at": now_utc(),
                "source_updated_at": "",
                "notes": "Validated accepted SP+ 2026 source; rating=spplus.",
            })
        return rows, {
            "source": source,
            "status": "ok_accepted",
            "path": str(accepted),
            "rows": len(rows),
        }

    if not raw_fallback.exists():
        return [], {
            "source": source,
            "status": "missing",
            "path": f"{accepted}|{raw_fallback}",
            "rows": 0,
        }

    df = pd.read_csv(raw_fallback)
    rows = []
    for _, r in df.iterrows():
        rank, team = extract_ranked_team(r.get("team"))
        rows.append({
            "snapshot_date": datetime.now().date().isoformat(),
            "season": 2026,
            "source": source,
            "team": team,
            "raw_team": r.get("team"),
            "rank": rank,
            "rating": parse_num_first(r.get("sp")),
            "off_rating": parse_num_first(r.get("off_sp")),
            "def_rating": parse_num_first(r.get("def_sp")),
            "hfa": "",
            "sos": "",
            "source_url": "",
            "pulled_at": now_utc(),
            "source_updated_at": "",
            "notes": "Fallback raw SP+ table_0; rating=sp.",
        })
    return rows, {
        "source": source,
        "status": "ok_raw_fallback",
        "path": str(raw_fallback),
        "rows": len(rows),
    }


def load_fpi():
    source = "FPI"
    accepted = Path("data/ratings/fpi_2026_latest.csv")
    raw_team = Path("data/ratings/raw/fpi/fpi_table_0.csv")
    raw_vals = Path("data/ratings/raw/fpi/fpi_table_1.csv")

    if accepted.exists():
        df = pd.read_csv(accepted)
        required = {"team", "fpi"}
        missing = sorted(required - set(df.columns))
        if missing:
            return [], {
                "source": source,
                "status": f"accepted_missing_columns: {missing}",
                "path": str(accepted),
                "rows": len(df),
            }

        ranks = _rank_series(df["fpi"])
        rows = []
        for i, r in df.iterrows():
            rows.append({
                "snapshot_date": datetime.now().date().isoformat(),
                "season": 2026,
                "source": source,
                "team": str(r.get("team")).strip(),
                "raw_team": r.get("team_raw", r.get("team")),
                "rank": ranks.iloc[i],
                "rating": pd.to_numeric(r.get("fpi"), errors="coerce"),
                "off_rating": "",
                "def_rating": "",
                "hfa": "",
                "sos": "",
                "source_url": "",
                "pulled_at": now_utc(),
                "source_updated_at": "",
                "notes": "Validated accepted FPI 2026 source; rating=fpi.",
            })
        return rows, {
            "source": source,
            "status": "ok_accepted",
            "path": str(accepted),
            "rows": len(rows),
        }

    if not raw_team.exists() or not raw_vals.exists():
        return [], {
            "source": source,
            "status": "missing",
            "path": f"{accepted}|{raw_team}|{raw_vals}",
            "rows": 0,
        }

    teams = pd.read_csv(raw_team)
    vals = pd.read_csv(raw_vals)
    n = min(len(teams), len(vals))
    rows = []
    for i in range(n):
        team = canon_team(teams.iloc[i].get("team"))
        rows.append({
            "snapshot_date": datetime.now().date().isoformat(),
            "season": 2026,
            "source": source,
            "team": team,
            "raw_team": teams.iloc[i].get("team"),
            "rank": vals.iloc[i].get("power_index_rk"),
            "rating": vals.iloc[i].get("power_index_fpi"),
            "off_rating": "",
            "def_rating": "",
            "hfa": "",
            "sos": "",
            "source_url": "",
            "pulled_at": now_utc(),
            "source_updated_at": "",
            "notes": "Fallback raw FPI tables merged by row order.",
        })
    return rows, {
        "source": source,
        "status": "ok_raw_fallback",
        "path": f"{raw_team}|{raw_vals}",
        "rows": len(rows),
    }


def load_teamrankings():
    source = "TeamRankings"
    accepted = Path("data/ratings/teamrankings_2026_latest.csv")
    raw_fallback = Path("data/ratings/raw/teamrankings/teamrankings_table_0.csv")

    if accepted.exists():
        df = pd.read_csv(accepted)
        required = {"team", "teamrankings"}
        missing = sorted(required - set(df.columns))
        if missing:
            return [], {
                "source": source,
                "status": f"accepted_missing_columns: {missing}",
                "path": str(accepted),
                "rows": len(df),
            }

        ranks = _rank_series(df["teamrankings"])
        rows = []
        for i, r in df.iterrows():
            rows.append({
                "snapshot_date": datetime.now().date().isoformat(),
                "season": 2026,
                "source": source,
                "team": str(r.get("team")).strip(),
                "raw_team": r.get("team_raw", r.get("team")),
                "rank": ranks.iloc[i],
                "rating": pd.to_numeric(r.get("teamrankings"), errors="coerce"),
                "off_rating": "",
                "def_rating": "",
                "hfa": "",
                "sos": "",
                "source_url": "",
                "pulled_at": now_utc(),
                "source_updated_at": "",
                "notes": "Validated accepted TeamRankings 2026 source; rating=teamrankings.",
            })
        return rows, {
            "source": source,
            "status": "ok_accepted",
            "path": str(accepted),
            "rows": len(rows),
        }

    if not raw_fallback.exists():
        return [], {
            "source": source,
            "status": "missing",
            "path": f"{accepted}|{raw_fallback}",
            "rows": 0,
        }

    df = pd.read_csv(raw_fallback)
    rows = []
    for _, r in df.iterrows():
        team = canon_team(r.get("team"))
        rows.append({
            "snapshot_date": datetime.now().date().isoformat(),
            "season": 2026,
            "source": source,
            "team": team,
            "raw_team": r.get("team"),
            "rank": r.get("rank"),
            "rating": r.get("rating"),
            "off_rating": "",
            "def_rating": "",
            "hfa": "",
            "sos": "",
            "source_url": "",
            "pulled_at": now_utc(),
            "source_updated_at": "",
            "notes": "Fallback raw TeamRankings table_0.",
        })
    return rows, {
        "source": source,
        "status": "ok_raw_fallback",
        "path": str(raw_fallback),
        "rows": len(rows),
    }


def load_kford():
    path = Path("data/ratings/kford_2025_test_latest.csv")
    source = "KFord"
    if not path.exists():
        return [], {"source": source, "status": "missing", "path": str(path), "rows": 0}

    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "snapshot_date": r.get("snapshot_date", datetime.now().date().isoformat()),
            "season": r.get("season", 2026),
            "source": source,
            "team": r.get("team"),
            "raw_team": r.get("team_raw", r.get("team")),
            "rank": r.get("rank"),
            "rating": r.get("kford"),
            "off_rating": "",
            "def_rating": "",
            "hfa": "",
            "sos": "",
            "source_url": "",
            "pulled_at": now_utc(),
            "source_updated_at": "",
            "notes": "KFord parsed manual/latest file; rating=kford.",
        })
    return rows, {"source": source, "status": "ok", "path": str(path), "rows": len(rows)}

def load_brad_powers():
    path = Path("data/ratings/bradpowers_2026_latest.csv")
    source = "Brad Powers"
    if not path.exists():
        return [], {"source": source, "status": "missing", "path": str(path), "rows": 0}

    df = pd.read_csv(path)
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "snapshot_date": r.get("snapshot_date", datetime.now().date().isoformat()),
            "season": r.get("season", 2026),
            "source": source,
            "team": r.get("team"),
            "raw_team": r.get("team_raw", r.get("team")),
            "rank": r.get("rank"),
            "rating": r.get("bradpowers"),
            "off_rating": "",
            "def_rating": "",
            "hfa": "",
            "sos": "",
            "source_url": "",
            "pulled_at": now_utc(),
            "source_updated_at": "",
            "notes": "Brad Powers normalized value; rating=bradpowers. Raw value retained in source CSV.",
        })
    return rows, {"source": source, "status": "ok", "path": str(path), "rows": len(rows)}


def main():
    site = load_site_teams()
    site_names = set(site["team"])

    all_rows = []
    audit = []

    # Existing/internal systems with explicit loaders
    for loader in [load_spplus, load_fpi, load_teamrankings]:
        rows, a = loader()
        all_rows.extend(rows)
        audit.append(a)

    # Manual/parser-output systems
    for loader in [load_kford, load_brad_powers]:
        rows, a = loader()
        all_rows.extend(rows)
        audit.append(a)

    # External systems with explicit mappings
    for loader, source, path in [
        (load_sagarin, "Sagarin Predictor", SOURCE_FILES["Sagarin Predictor"]),
        (load_donchess, "Donchess Overall", SOURCE_FILES["Donchess Overall"]),
        (load_massey, "Massey Power", SOURCE_FILES["Massey Power"]),
    ]:
        rows, a = loader(path)
        all_rows.extend(rows)
        audit.append(a)

    out = pd.DataFrame(all_rows)

    if not out.empty:
        out = out[out["team"].notna()]
        out["team"] = out["team"].astype(str).str.strip()
        out = out[out["team"].isin(site_names)].copy()

        # Ensure numeric where appropriate.
        for col in ["rank", "rating", "off_rating", "def_rating", "hfa", "sos"]:
            out[col] = pd.to_numeric(out[col], errors="coerce")

        out = out.sort_values(["source", "rank", "team"], na_position="last")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    # Coverage audit after site filtering
    coverage = []
    for source in sorted(out["source"].unique()) if not out.empty else []:
        src = out[out["source"] == source]
        names = set(src["team"])
        coverage.append({
            "source": source,
            "status": "coverage",
            "rows_after_site_filter": len(src),
            "matched_site_teams": len(names),
            "missing_site_teams": "; ".join(sorted(site_names - names)),
            "extra_teams_after_filter": "",
        })

    audit_df = pd.DataFrame(audit + coverage)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    audit_df.to_csv(AUDIT, index=False)

    print(f"Wrote {OUT}: {len(out)} rows")
    print(f"Wrote {AUDIT}")

    if not out.empty:
        print("\nRows by source:")
        print(out.groupby("source").size().to_string())

        print("\nCoverage:")
        for source in sorted(out["source"].unique()):
            src = out[out["source"] == source]
            print(source, len(set(src["team"])), "site teams")

if __name__ == "__main__":
    main()
