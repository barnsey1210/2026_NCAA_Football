from pathlib import Path
import re
import time
import requests
import pandas as pd
from PIL import Image, ImageDraw
from io import BytesIO

OUT_DIR = Path("logo_assets")
LOGO_DIR = Path("logos")
REVIEW_DIR = OUT_DIR / "review"

for d in [OUT_DIR, LOGO_DIR, REVIEW_DIR]:
    d.mkdir(parents=True, exist_ok=True)

ESPN_TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams?limit=1000"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}

TARGET_TEAMS = [
    "Air Force", "Akron", "Alabama", "Appalachian State", "Arizona", "Arizona State",
    "Arkansas", "Arkansas State", "Army", "Auburn", "Ball State", "Baylor",
    "Boise State", "Boston College", "Bowling Green", "Buffalo", "BYU", "California",
    "Central Florida", "Central Michigan", "Charlotte", "Cincinnati", "Clemson",
    "Coastal Carolina", "Colorado", "Colorado State", "Connecticut", "Delaware",
    "Duke", "East Carolina", "Eastern Michigan", "Florida", "Florida Atlantic",
    "Florida International", "Florida State", "Fresno State", "Georgia",
    "Georgia Southern", "Georgia State", "Georgia Tech", "Hawaii", "Houston",
    "Illinois", "Indiana", "Iowa", "Iowa State", "Jacksonville State",
    "James Madison", "Kansas", "Kansas State", "Kennesaw State", "Kent State",
    "Kentucky", "Liberty", "Louisiana", "Louisiana Tech", "Louisville", "LSU",
    "Marshall", "Maryland", "Massachusetts", "Memphis", "Miami-FL", "Miami-OH",
    "Michigan", "Michigan State", "Middle Tennessee", "Minnesota",
    "Mississippi State", "Missouri", "Missouri State", "Navy", "NC State",
    "Nebraska", "Nevada", "New Mexico", "New Mexico State", "North Carolina",
    "North Dakota State", "North Texas", "Northern Illinois", "Northwestern",
    "Notre Dame", "Ohio", "Ohio State", "Oklahoma", "Oklahoma State",
    "Old Dominion", "Ole Miss", "Oregon", "Oregon State", "Penn State",
    "Pittsburgh", "Purdue", "Rice", "Rutgers", "Sacramento State",
    "Sam Houston", "San Diego State", "San Jose State", "SMU", "South Alabama",
    "South Carolina", "South Florida", "Southern Miss", "Stanford", "Syracuse",
    "TCU", "Temple", "Tennessee", "Texas", "Texas A&M", "Texas State",
    "Texas Tech", "Toledo", "Troy", "Tulane", "Tulsa", "UAB", "UCLA",
    "UL-Monroe", "UNLV", "USC", "UTEP", "UTSA", "Utah", "Utah State",
    "Vanderbilt", "Virginia", "Virginia Tech", "Wake Forest", "Washington",
    "Washington State", "West Virginia", "Western Kentucky", "Western Michigan",
    "Wisconsin", "Wyoming",
]

# Strict aliases only. No fuzzy/contains matching.
ALIASES = {
    "Air Force": ["Air Force Falcons"],
    "Akron": ["Akron Zips"],
    "Alabama": ["Alabama Crimson Tide"],
    "Appalachian State": ["Appalachian State Mountaineers", "App State Mountaineers"],
    "Arizona": ["Arizona Wildcats"],
    "Arizona State": ["Arizona State Sun Devils"],
    "Arkansas": ["Arkansas Razorbacks"],
    "Arkansas State": ["Arkansas State Red Wolves"],
    "Army": ["Army Black Knights", "Army West Point Black Knights"],
    "Auburn": ["Auburn Tigers"],
    "Ball State": ["Ball State Cardinals"],
    "Baylor": ["Baylor Bears"],
    "Boise State": ["Boise State Broncos"],
    "Boston College": ["Boston College Eagles"],
    "Bowling Green": ["Bowling Green Falcons"],
    "Buffalo": ["Buffalo Bulls"],
    "BYU": ["BYU Cougars", "Brigham Young Cougars"],
    "California": ["California Golden Bears", "Cal Golden Bears"],
    "Central Florida": ["UCF Knights", "Central Florida Knights"],
    "Central Michigan": ["Central Michigan Chippewas"],
    "Charlotte": ["Charlotte 49ers"],
    "Cincinnati": ["Cincinnati Bearcats"],
    "Clemson": ["Clemson Tigers"],
    "Coastal Carolina": ["Coastal Carolina Chanticleers"],
    "Colorado": ["Colorado Buffaloes"],
    "Colorado State": ["Colorado State Rams"],
    "Connecticut": ["UConn Huskies", "Connecticut Huskies"],
    "Delaware": ["Delaware Blue Hens"],
    "Duke": ["Duke Blue Devils"],
    "East Carolina": ["East Carolina Pirates"],
    "Eastern Michigan": ["Eastern Michigan Eagles"],
    "Florida": ["Florida Gators"],
    "Florida Atlantic": ["Florida Atlantic Owls", "FAU Owls"],
    "Florida International": ["FIU Panthers", "Florida International Panthers"],
    "Florida State": ["Florida State Seminoles"],
    "Fresno State": ["Fresno State Bulldogs"],
    "Georgia": ["Georgia Bulldogs"],
    "Georgia Southern": ["Georgia Southern Eagles"],
    "Georgia State": ["Georgia State Panthers"],
    "Georgia Tech": ["Georgia Tech Yellow Jackets"],
    "Hawaii": ["Hawai'i Rainbow Warriors", "Hawaii Rainbow Warriors", "Hawaiʻi Rainbow Warriors"],
    "Houston": ["Houston Cougars"],
    "Illinois": ["Illinois Fighting Illini"],
    "Indiana": ["Indiana Hoosiers"],
    "Iowa": ["Iowa Hawkeyes"],
    "Iowa State": ["Iowa State Cyclones"],
    "Jacksonville State": ["Jacksonville State Gamecocks"],
    "James Madison": ["James Madison Dukes"],
    "Kansas": ["Kansas Jayhawks"],
    "Kansas State": ["Kansas State Wildcats"],
    "Kennesaw State": ["Kennesaw State Owls"],
    "Kent State": ["Kent State Golden Flashes"],
    "Kentucky": ["Kentucky Wildcats"],
    "Liberty": ["Liberty Flames"],
    "Louisiana": ["Louisiana Ragin' Cajuns", "Louisiana Ragin Cajuns", "Louisiana-Lafayette Ragin' Cajuns"],
    "Louisiana Tech": ["Louisiana Tech Bulldogs"],
    "Louisville": ["Louisville Cardinals"],
    "LSU": ["LSU Tigers", "Louisiana State Tigers"],
    "Marshall": ["Marshall Thundering Herd"],
    "Maryland": ["Maryland Terrapins"],
    "Massachusetts": ["UMass Minutemen", "Massachusetts Minutemen"],
    "Memphis": ["Memphis Tigers"],
    "Miami-FL": ["Miami Hurricanes", "Miami (FL) Hurricanes", "Miami FL Hurricanes"],
    "Miami-OH": ["Miami (OH) RedHawks", "Miami OH RedHawks", "Miami RedHawks"],
    "Michigan": ["Michigan Wolverines"],
    "Michigan State": ["Michigan State Spartans"],
    "Middle Tennessee": ["Middle Tennessee Blue Raiders", "Middle Tennessee State Blue Raiders"],
    "Minnesota": ["Minnesota Golden Gophers"],
    "Mississippi State": ["Mississippi State Bulldogs"],
    "Missouri": ["Missouri Tigers"],
    "Missouri State": ["Missouri State Bears"],
    "Navy": ["Navy Midshipmen"],
    "NC State": ["NC State Wolfpack", "North Carolina State Wolfpack"],
    "Nebraska": ["Nebraska Cornhuskers"],
    "Nevada": ["Nevada Wolf Pack"],
    "New Mexico": ["New Mexico Lobos"],
    "New Mexico State": ["New Mexico State Aggies"],
    "North Carolina": ["North Carolina Tar Heels"],
    "North Dakota State": ["North Dakota State Bison"],
    "North Texas": ["North Texas Mean Green"],
    "Northern Illinois": ["Northern Illinois Huskies"],
    "Northwestern": ["Northwestern Wildcats"],
    "Notre Dame": ["Notre Dame Fighting Irish"],
    "Ohio": ["Ohio Bobcats"],
    "Ohio State": ["Ohio State Buckeyes"],
    "Oklahoma": ["Oklahoma Sooners"],
    "Oklahoma State": ["Oklahoma State Cowboys"],
    "Old Dominion": ["Old Dominion Monarchs"],
    "Ole Miss": ["Ole Miss Rebels", "Mississippi Rebels"],
    "Oregon": ["Oregon Ducks"],
    "Oregon State": ["Oregon State Beavers"],
    "Penn State": ["Penn State Nittany Lions"],
    "Pittsburgh": ["Pittsburgh Panthers", "Pitt Panthers"],
    "Purdue": ["Purdue Boilermakers"],
    "Rice": ["Rice Owls"],
    "Rutgers": ["Rutgers Scarlet Knights"],
    "Sacramento State": ["Sacramento State Hornets"],
    "Sam Houston": ["Sam Houston Bearkats", "Sam Houston State Bearkats"],
    "San Diego State": ["San Diego State Aztecs"],
    "San Jose State": ["San José State Spartans", "San Jose State Spartans"],
    "SMU": ["SMU Mustangs", "Southern Methodist Mustangs"],
    "South Alabama": ["South Alabama Jaguars"],
    "South Carolina": ["South Carolina Gamecocks"],
    "South Florida": ["South Florida Bulls", "USF Bulls"],
    "Southern Miss": ["Southern Miss Golden Eagles", "Southern Mississippi Golden Eagles"],
    "Stanford": ["Stanford Cardinal"],
    "Syracuse": ["Syracuse Orange"],
    "TCU": ["TCU Horned Frogs"],
    "Temple": ["Temple Owls"],
    "Tennessee": ["Tennessee Volunteers"],
    "Texas": ["Texas Longhorns"],
    "Texas A&M": ["Texas A&M Aggies", "Texas A and M Aggies"],
    "Texas State": ["Texas State Bobcats"],
    "Texas Tech": ["Texas Tech Red Raiders"],
    "Toledo": ["Toledo Rockets"],
    "Troy": ["Troy Trojans"],
    "Tulane": ["Tulane Green Wave"],
    "Tulsa": ["Tulsa Golden Hurricane"],
    "UAB": ["UAB Blazers"],
    "UCLA": ["UCLA Bruins"],
    "UL-Monroe": ["UL Monroe Warhawks", "Louisiana Monroe Warhawks", "Louisiana-Monroe Warhawks", "ULM Warhawks"],
    "UNLV": ["UNLV Rebels"],
    "USC": ["USC Trojans", "Southern California Trojans"],
    "UTEP": ["UTEP Miners", "Texas-El Paso Miners"],
    "UTSA": ["UTSA Roadrunners", "Texas-San Antonio Roadrunners"],
    "Utah": ["Utah Utes"],
    "Utah State": ["Utah State Aggies"],
    "Vanderbilt": ["Vanderbilt Commodores"],
    "Virginia": ["Virginia Cavaliers"],
    "Virginia Tech": ["Virginia Tech Hokies"],
    "Wake Forest": ["Wake Forest Demon Deacons"],
    "Washington": ["Washington Huskies"],
    "Washington State": ["Washington State Cougars"],
    "West Virginia": ["West Virginia Mountaineers"],
    "Western Kentucky": ["Western Kentucky Hilltoppers", "WKU Hilltoppers"],
    "Western Michigan": ["Western Michigan Broncos"],
    "Wisconsin": ["Wisconsin Badgers"],
    "Wyoming": ["Wyoming Cowboys"],
}

# Manual ESPN ID overrides for teams the endpoint/name index missed.
MANUAL_ESPN_IDS = {
    "Missouri State": "2623",
    "Purdue": "2509",
    "Sam Houston": "2534",
    "SMU": "2567",
    "South Carolina": "2579",
    "Southern Miss": "2572",
    "TCU": "2628",
    "Tennessee": "2633",
    "Texas Tech": "2641",
    "Toledo": "2649",
    "Troy": "2653",
    "Tulane": "2655",
    "UTEP": "2638",
    "UTSA": "2636",
    "Western Michigan": "2711",
    "Wyoming": "2751",
}


def slugify(team: str) -> str:
    text = team.lower()
    text = text.replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def norm(s: str) -> str:
    s = str(s).lower()
    s = s.replace("&", "and")
    s = s.replace("'", "")
    s = s.replace("’", "")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(university|college|the|of|at)\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def fetch_espn_teams():
    print(f"Fetching ESPN teams: {ESPN_TEAMS_URL}")
    r = requests.get(ESPN_TEAMS_URL, headers=HEADERS, timeout=60)
    r.raise_for_status()
    data = r.json()

    teams = []
    for item in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
        team = item.get("team", {})
        logos = team.get("logos", []) or []

        logo_url = ""
        if logos:
            logo_url = logos[0].get("href", "")

        teams.append({
            "espn_id": str(team.get("id", "")),
            "display_name": team.get("displayName", ""),
            "short_display_name": team.get("shortDisplayName", ""),
            "name": team.get("name", ""),
            "nickname": team.get("nickname", ""),
            "abbreviation": team.get("abbreviation", ""),
            "logo_url": logo_url,
        })

    print(f"ESPN teams found: {len(teams)}")
    return teams


def build_espn_index(espn_teams):
    index = {}

    for row in espn_teams:
        values = [
            row["display_name"],
            row["short_display_name"],
            row["name"],
            row["nickname"],
            row["abbreviation"],
        ]

        for v in values:
            if v:
                key = norm(v)
                if key and key not in index:
                    index[key] = row

    return index


def build_espn_id_index(espn_teams):
    return {str(row["espn_id"]): row for row in espn_teams if row.get("espn_id")}


def match_team(target, espn_index, espn_by_id):
    """
    Strict matching only, with manual ESPN ID overrides for known missing teams.
    No broad contains matching.
    """
    if target in MANUAL_ESPN_IDS:
        espn_id = MANUAL_ESPN_IDS[target]
        if espn_id in espn_by_id:
            return espn_by_id[espn_id], f"manual ESPN ID {espn_id}", "manual_id"

    candidates = [target] + ALIASES.get(target, [])

    for c in candidates:
        key = norm(c)
        if key in espn_index:
            return espn_index[key], c, "exact"

    return None, "", "missing"


def download_logo(url, out_path):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()

    img = Image.open(BytesIO(r.content)).convert("RGBA")

    canvas = Image.new("RGBA", (128, 128), (255, 255, 255, 0))
    img.thumbnail((116, 116), Image.LANCZOS)
    canvas.alpha_composite(img, ((128 - img.width) // 2, (128 - img.height) // 2))
    canvas.save(out_path)


def make_contact_sheet(rows):
    card_w = 270
    card_h = 82
    cols = 3
    row_count = (len(rows) + cols - 1) // cols

    sheet = Image.new("RGB", (cols * card_w, row_count * card_h), "white")
    draw = ImageDraw.Draw(sheet)

    for idx, row in enumerate(rows):
        col = idx % cols
        rr = idx // cols
        x0 = col * card_w
        y0 = rr * card_h

        status = row["Status"]
        team = row["Team"]

        if status == "downloaded":
            logo_path = LOGO_DIR / f"{slugify(team)}.png"
            if logo_path.exists():
                img = Image.open(logo_path).convert("RGBA")
                img.thumbnail((48, 48), Image.LANCZOS)
                sheet.paste(img, (x0 + 14, y0 + 16), img)
            label2 = row["ESPN Display Name"][:34]
            color = (80, 80, 80)
        else:
            label2 = status
            color = (180, 0, 0)

        draw.text((x0 + 75, y0 + 18), team, fill="black")
        draw.text((x0 + 75, y0 + 41), label2, fill=color)
        draw.rectangle([x0, y0, x0 + card_w - 1, y0 + card_h - 1], outline=(220, 220, 220))

    out = REVIEW_DIR / "logo_contact_sheet.png"
    sheet.save(out)
    print(f"Saved review contact sheet: {out}")


def main():
    espn_teams = fetch_espn_teams()
    espn_index = build_espn_index(espn_teams)
    espn_by_id = build_espn_id_index(espn_teams)

    rows = []

    for target in TARGET_TEAMS:
        match, matched_on, match_type = match_team(target, espn_index, espn_by_id)
        filename = f"{slugify(target)}.png"
        out_path = LOGO_DIR / filename

        if not match:
            print(f"MISSING: {target}")
            rows.append({
                "Team": target,
                "Slug": slugify(target),
                "Logo File": "",
                "Status": "missing",
                "ESPN Display Name": "",
                "ESPN ID": "",
                "ESPN Logo URL": "",
                "Matched On": "",
                "Match Type": "",
            })
            continue

        logo_url = match.get("logo_url", "")
        if not logo_url:
            print(f"NO LOGO URL: {target} -> {match.get('display_name')}")
            rows.append({
                "Team": target,
                "Slug": slugify(target),
                "Logo File": "",
                "Status": "no logo url",
                "ESPN Display Name": match.get("display_name", ""),
                "ESPN ID": match.get("espn_id", ""),
                "ESPN Logo URL": "",
                "Matched On": matched_on,
                "Match Type": match_type,
            })
            continue

        try:
            download_logo(logo_url, out_path)
            print(f"Downloaded {target}: {out_path}")
            status = "downloaded"
            logo_file = f"logos/{filename}"
        except Exception as e:
            print(f"ERROR downloading {target}: {e}")
            status = f"download error: {e}"
            logo_file = ""

        rows.append({
            "Team": target,
            "Slug": slugify(target),
            "Logo File": logo_file,
            "Status": status,
            "ESPN Display Name": match.get("display_name", ""),
            "ESPN ID": match.get("espn_id", ""),
            "ESPN Logo URL": logo_url,
            "Matched On": matched_on,
            "Match Type": match_type,
        })

        time.sleep(0.05)

    df = pd.DataFrame(rows)
    manifest = OUT_DIR / "logo_manifest.csv"
    missing = OUT_DIR / "logo_missing.csv"
    xlsx = OUT_DIR / "logo_manifest.xlsx"

    df.to_csv(manifest, index=False)
    df[df["Status"] != "downloaded"].to_csv(missing, index=False)

    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Logo Manifest")

    make_contact_sheet(rows)

    print()
    print("Done.")
    print(f"Logo folder: {LOGO_DIR.resolve()}")
    print(f"Manifest: {manifest.resolve()}")
    print(f"Missing: {missing.resolve()}")
    print(f"Review sheet: {(REVIEW_DIR / 'logo_contact_sheet.png').resolve()}")
    print(f"Downloaded: {(df['Status'] == 'downloaded').sum()}")
    print(f"Missing/errors: {(df['Status'] != 'downloaded').sum()}")


if __name__ == "__main__":
    main()