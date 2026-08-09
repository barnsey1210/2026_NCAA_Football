#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
import json
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/snapshots/preseason/preseason_db.json"
OUT = ROOT / "data/ratings/external_sources/dratings_ncaaf_predictions_latest.csv"
AUDIT = ROOT / "data/ratings/external_sources/dratings_ncaaf_predictions_audit.json"

BASE = "https://www.dratings.com"
START_URL = BASE + "/predictor/ncaa-football-predictions/upcoming/3#scroll-upcoming"
MAX_NAV_PAGES = 250

ALIASES = {
    "miami hurricanes": "Miami-FL",
    "miami florida hurricanes": "Miami-FL",
    "miami redhawks": "Miami-OH",
    "miami ohio redhawks": "Miami-OH",
    "miami oh redhawks": "Miami-OH",
    "ucf knights": "Central Florida",
    "uconn huskies": "Connecticut",
    "ole miss rebels": "Mississippi",
    "app state mountaineers": "Appalachian State",
    "appalachian state mountaineers": "Appalachian State",
    "hawaii rainbow warriors": "Hawaii",
    "louisiana ragin cajuns": "Louisiana",
    "southern miss golden eagles": "Southern Mississippi",
    "utsa roadrunners": "UTSA",
    "utep miners": "UTEP",
    "smu mustangs": "SMU",
    "tcu horned frogs": "TCU",
    "unlv rebels": "UNLV",
    "usc trojans": "USC",
    "lsu tigers": "LSU",
    "byu cougars": "BYU",
    "fiu panthers": "Florida International",
    "albany great danes": "UAlbany",
    "bethune cookman wildcats": "Bethune-Cookman",
}

def norm(x):
    return re.sub(r"[^a-z0-9]+", " ", str(x or "").lower()).strip()

def load_site_context():
    db = json.loads(DB.read_text())
    teams = set()
    dates = set()
    games = set()
    for g in db.get("games", []):
        away = str(g.get("away_team") or "")
        home = str(g.get("home_team") or "")
        date = str(g.get("date") or "")[:10]
        if away:
            teams.add(away)
        if home:
            teams.add(home)
        if date:
            dates.add(date)
        if date and away and home:
            games.add((date, norm(away), norm(home)))
    return sorted(teams), dates, games

def canonical_team(raw, site_teams):
    n = norm(raw)

    if n in ALIASES and ALIASES[n] in site_teams:
        return ALIASES[n]

    exact = {norm(t): t for t in site_teams}
    if n in exact:
        return exact[n]

    prefix = [(len(norm(t)), t) for t in site_teams if n.startswith(norm(t) + " ")]
    if prefix:
        return max(prefix)[1]

    return None

def parse_points(text):
    vals = re.findall(r"-?\d+(?:\.\d+)?", text or "")
    if len(vals) < 2:
        return None, None
    return float(vals[0]), float(vals[1])

def parse_nav_date(text):
    m = re.search(r"Games for ([A-Za-z]+) (\d{1,2}), (\d{4})", text or "")
    if not m:
        return None
    raw = f"{m.group(1)} {m.group(2)} {m.group(3)}"
    for fmt in ("%b %d %Y", "%B %d %Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    return None

def parse_page(html, url, site_teams, site_dates, canonical_games):
    soup = BeautifulSoup(html, "html.parser")
    upcoming = soup.find(id="scroll-upcoming")
    if not upcoming:
        return [], None, None

    page_date = None
    h2 = upcoming.find("h2")
    if h2:
        m = re.search(r"([A-Za-z]+ \d{1,2}, \d{4})", h2.get_text(" ", strip=True))
        if m:
            page_date = datetime.strptime(m.group(1), "%B %d, %Y").date()

    rows = []
    table = upcoming.find("table")
    pulled_at = datetime.now(timezone.utc).isoformat()

    if table:
        for tr in table.select("tbody tr"):
            td = tr.find_all("td")
            if len(td) < 7:
                continue

            team_links = td[1].find_all("a")
            if len(team_links) < 2:
                continue

            away_raw = team_links[0].get_text(" ", strip=True)
            home_raw = team_links[1].get_text(" ", strip=True)
            away = canonical_team(away_raw, site_teams)
            home = canonical_team(home_raw, site_teams)

            game_date = page_date.isoformat() if page_date else None
            mdate = re.search(r"(\d{2}/\d{2}/\d{4})", td[0].get_text(" ", strip=True))
            if mdate:
                game_date = datetime.strptime(mdate.group(1), "%m/%d/%Y").date().isoformat()

            away_pts, home_pts = parse_points(td[5].get_text(" ", strip=True))
            if away_pts is None or home_pts is None:
                continue

            total_vals = re.findall(r"-?\d+(?:\.\d+)?", td[6].get_text(" ", strip=True))
            projected_total = float(total_vals[0]) if total_vals else round(away_pts + home_pts, 3)

            win_vals = re.findall(r"(\d+(?:\.\d+)?)%", td[2].get_text(" ", strip=True))
            home_win_prob = float(win_vals[1]) / 100.0 if len(win_vals) >= 2 else None

            key = (
                game_date,
                norm(away) if away else "",
                norm(home) if home else "",
            )

            rows.append({
                "game_date": game_date,
                "away_team_raw": away_raw,
                "home_team_raw": home_raw,
                "away_team": away or away_raw,
                "home_team": home or home_raw,
                "away_projected_points": away_pts,
                "home_projected_points": home_pts,
                "projected_spread_home": round(home_pts - away_pts, 3),
                "projected_total": projected_total,
                "home_win_prob": home_win_prob,
                "source_url": url,
                "pulled_at": pulled_at,
                "away_team_matched": bool(away),
                "home_team_matched": bool(home),
                "site_schedule_date": bool(game_date in site_dates) if game_date else False,
                "on_canonical_site_schedule": bool(away and home and key in canonical_games),
            })

    # Follow the site's forward "Games for ..." link.
    candidates = []
    for a in soup.find_all("a", href=True):
        d = parse_nav_date(a.get_text(" ", strip=True))
        href = a.get("href") or ""
        if d and "/predictor/ncaa-football-predictions/" in href:
            if page_date is None or d > page_date:
                candidates.append((d, urljoin(BASE, href)))

    next_url = min(candidates, key=lambda x: x[0])[1] if candidates else None
    return rows, page_date, next_url

def main():
    if not DB.exists():
        raise SystemExit(f"Missing canonical schedule DB: {DB}")

    site_teams, site_dates, canonical_games = load_site_context()
    max_site_date = max(site_dates) if site_dates else None

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 NCAAFResearch/1.0"})

    url = START_URL
    seen = set()
    all_rows = []
    pages = []

    for _ in range(MAX_NAV_PAGES):
        clean = url.split("#", 1)[0]
        if clean in seen:
            break
        seen.add(clean)

        response = session.get(url, timeout=30)
        response.raise_for_status()

        rows, page_date, next_url = parse_page(
            response.text,
            url,
            site_teams,
            site_dates,
            canonical_games,
        )

        pages.append({
            "url": url,
            "page_date": page_date.isoformat() if page_date else None,
            "rows": len(rows),
            "canonical_site_games": sum(bool(r["on_canonical_site_schedule"]) for r in rows),
            "next_url": next_url,
        })
        all_rows.extend(rows)

        if not next_url:
            break

        if page_date and max_site_date and page_date.isoformat() > max_site_date:
            break

        url = next_url
        time.sleep(0.15)
    else:
        raise SystemExit("STOP: navigation page limit reached")

    if not all_rows:
        raise SystemExit("DRatings returned zero prediction rows")

    df = pd.DataFrame(all_rows)
    df = df.drop_duplicates(
        subset=["game_date", "away_team_raw", "home_team_raw"],
        keep="last",
    ).sort_values(["game_date", "away_team", "home_team"])

    if max_site_date:
        df = df[df["game_date"].astype(str) <= max_site_date].copy()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    both = df["away_team_matched"] & df["home_team_matched"]
    canonical = df["on_canonical_site_schedule"]

    audit = {
        "schema_version": "dratings-ncaaf-pull-audit-v2",
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "navigation_method": "follow_dratings_next_game_date_link",
        "rows": int(len(df)),
        "both_teams_matched": int(both.sum()),
        "canonical_site_games": int(canonical.sum()),
        "pages_visited": len(pages),
        "first_prediction_date": str(df["game_date"].min()) if len(df) else None,
        "last_prediction_date": str(df["game_date"].max()) if len(df) else None,
        "unmatched_rows": df.loc[
            ~both,
            ["game_date", "away_team_raw", "home_team_raw", "away_team", "home_team"],
        ].to_dict("records"),
        "pages": pages,
    }

    AUDIT.write_text(json.dumps(audit, indent=2) + "\n")

    print(f"Wrote {OUT}: {len(df)} rows")
    print(f"Wrote {AUDIT}")
    print(f"pages_visited: {audit['pages_visited']}")
    print(f"first_prediction_date: {audit['first_prediction_date']}")
    print(f"last_prediction_date: {audit['last_prediction_date']}")
    print(f"canonical_site_games: {audit['canonical_site_games']}")
    print(f"both_teams_matched: {audit['both_teams_matched']}")

if __name__ == "__main__":
    main()
