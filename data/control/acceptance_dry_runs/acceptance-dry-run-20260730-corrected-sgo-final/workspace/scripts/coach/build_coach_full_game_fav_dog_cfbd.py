#!/usr/bin/env python3
from pathlib import Path
import os
import re
import time
import json
import requests
import pandas as pd

START_SEASON = 2006
END_SEASON = 2025

ROOT = Path(".")
CACHE = ROOT / "cfbd_cache" / "coach_full_game_fav_dog"
OUT = ROOT / "data/coach"
AUDIT = ROOT / "data/audit"
CACHE.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
AUDIT.mkdir(parents=True, exist_ok=True)

TENURES_FILE = ROOT / "Coach_betting_data/coach_tenures_2006_2025.csv"

BASE_URL = "https://api.collegefootballdata.com"

def norm(x):
    s = str(x or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace(".", "")
    s = s.replace("&", "and")
    return s.lower()

TEAM_ALIASES = {
    "hawaii": "hawaii",
    "hawai'i": "hawaii",
    "miami": "miami-fl",
    "miami fl": "miami-fl",
    "miami (fl)": "miami-fl",
    "miami oh": "miami-oh",
    "miami (oh)": "miami-oh",
    "ole miss": "ole miss",
    "mississippi": "ole miss",
    "ul monroe": "ul-monroe",
    "ulm": "ul-monroe",
    "louisiana monroe": "ul-monroe",
    "louisiana lafayette": "louisiana",
    "ul lafayette": "louisiana",
    "app state": "appalachian state",
    "appalachian st": "appalachian state",
    "san jose st": "san jose state",
    "san jose st.": "san jose state",
    "boise st": "boise state",
    "fresno st": "fresno state",
    "oregon st": "oregon state",
    "washington st": "washington state",
    "penn st": "penn state",
    "ohio st": "ohio state",
    "michigan st": "michigan state",
    "oklahoma st": "oklahoma state",
    "kansas st": "kansas state",
    "iowa st": "iowa state",
    "arizona st": "arizona state",
    "texas st": "texas state",
    "arkansas st": "arkansas state",
    "new mexico st": "new mexico state",
    "colorado st": "colorado state",
    "utah st": "utah state",
    "kent st": "kent state",
}

def team_key(x):
    n = norm(x)
    return TEAM_ALIASES.get(n, n)

def headers():
    key = os.environ.get("CFBD_API_KEY") or os.environ.get("COLLEGEFOOTBALLDATA_API_KEY")
    h = {"User-Agent": "NCAAF coach fav/dog builder"}
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h

def get_json(endpoint, params, cache_name):
    path = CACHE / cache_name
    if path.exists():
        return json.loads(path.read_text())

    url = BASE_URL + endpoint
    print("pulling", url, params)
    r = requests.get(url, headers=headers(), params=params, timeout=60)
    if r.status_code == 401 or r.status_code == 403:
        raise SystemExit("CFBD auth failed. Set CFBD_API_KEY in your shell.")
    r.raise_for_status()
    data = r.json()
    path.write_text(json.dumps(data))
    time.sleep(0.75)
    return data

def parse_score(x):
    try:
        return float(x)
    except Exception:
        return None

def first_line_for_game(line_obj):
    lines = line_obj.get("lines") or []
    if not lines:
        return None

    # Prefer common sharper books if available, otherwise first usable.
    preferred = ["DraftKings", "Circa", "FanDuel", "BetMGM", "Caesars", "consensus"]
    usable = []
    for ln in lines:
        spread = ln.get("spread")
        total = ln.get("overUnder")
        if spread is None and total is None:
            continue
        usable.append(ln)

    if not usable:
        return None

    for book in preferred:
        for ln in usable:
            if str(ln.get("provider") or "").lower() == book.lower():
                return ln

    return usable[0]

def spread_side(team_spread):
    try:
        s = float(team_spread)
    except Exception:
        return ""
    if s < 0:
        return "Favorite"
    if s > 0:
        return "Underdog"
    return "Pick"

def ats_result(actual_margin, spread):
    if actual_margin is None or spread is None:
        return ""
    v = actual_margin + spread
    if v > 0:
        return "W"
    if v < 0:
        return "L"
    return "P"

def total_result(total_points, total_line):
    if total_points is None or total_line is None:
        return ""
    v = total_points - total_line
    if v > 0:
        return "O"
    if v < 0:
        return "U"
    return "P"

def load_tenures():
    ten = pd.read_csv(TENURES_FILE, low_memory=False)
    ten.columns = [str(c).strip() for c in ten.columns]

    needed = ["Season", "Team", "Head Coach"]
    missing = [c for c in needed if c not in ten.columns]
    if missing:
        raise SystemExit(f"Missing tenure columns: {missing}")

    current_team_col = "Coach Current Team" if "Coach Current Team" in ten.columns else "Team"

    out = ten[["Season", "Team", "Head Coach", current_team_col]].copy()
    out.columns = ["season", "historical_team", "coach", "current_team"]
    out["season"] = pd.to_numeric(out["season"], errors="coerce")
    out["historical_team_key"] = out["historical_team"].map(team_key)
    return out.dropna(subset=["season", "historical_team_key", "coach"])

def build():
    ten = load_tenures()

    all_rows = []
    audit_rows = []

    for season in range(START_SEASON, END_SEASON + 1):
        games = get_json(
            "/games",
            {"year": season, "seasonType": "regular"},
            f"games_{season}_regular.json"
        )

        lines = get_json(
            "/lines",
            {"year": season, "seasonType": "regular"},
            f"lines_{season}_regular.json"
        )

        games_by_id = {str(g.get("id")): g for g in games if g.get("id") is not None}
        line_count = 0
        used_count = 0

        for lg in lines:
            gid = str(lg.get("id") or lg.get("gameId") or "")
            if not gid or gid not in games_by_id:
                continue

            g = games_by_id[gid]
            line = first_line_for_game(lg)
            if not line:
                continue

            spread = line.get("spread")
            total = line.get("overUnder")

            try:
                home_spread = float(spread) if spread is not None else None
            except Exception:
                home_spread = None

            try:
                total_line = float(total) if total is not None else None
            except Exception:
                total_line = None

            if home_spread is None:
                continue

            away_team = g.get("away_team") or g.get("awayTeam") or lg.get("awayTeam")
            home_team = g.get("home_team") or g.get("homeTeam") or lg.get("homeTeam")

            away_points = parse_score(g.get("away_points") if "away_points" in g else g.get("awayPoints"))
            home_points = parse_score(g.get("home_points") if "home_points" in g else g.get("homePoints"))

            if away_team is None or home_team is None or away_points is None or home_points is None:
                continue

            total_points = away_points + home_points
            home_margin = home_points - away_points
            away_margin = away_points - home_points

            # CFBD line spread is home-team spread. Negative = home favored.
            team_rows = [
                {
                    "season": season,
                    "game_id": gid,
                    "date": g.get("start_date") or g.get("startDate"),
                    "team": home_team,
                    "opponent": away_team,
                    "home_away": "Home",
                    "team_spread": home_spread,
                    "team_points": home_points,
                    "opp_points": away_points,
                    "team_margin": home_margin,
                    "total_line": total_line,
                    "total_points": total_points,
                    "book": line.get("provider"),
                },
                {
                    "season": season,
                    "game_id": gid,
                    "date": g.get("start_date") or g.get("startDate"),
                    "team": away_team,
                    "opponent": home_team,
                    "home_away": "Away",
                    "team_spread": -home_spread,
                    "team_points": away_points,
                    "opp_points": home_points,
                    "team_margin": away_margin,
                    "total_line": total_line,
                    "total_points": total_points,
                    "book": line.get("provider"),
                },
            ]

            for r in team_rows:
                r["team_key"] = team_key(r["team"])
                r["fav_dog"] = spread_side(r["team_spread"])
                r["ats_margin"] = r["team_margin"] + r["team_spread"]
                r["ats_result"] = ats_result(r["team_margin"], r["team_spread"])
                r["total_margin"] = (
                    r["total_points"] - r["total_line"]
                    if r["total_line"] is not None
                    else None
                )
                r["total_result"] = total_result(r["total_points"], r["total_line"])

            all_rows.extend(team_rows)
            used_count += 1

        audit_rows.append({
            "season": season,
            "games_returned": len(games),
            "lines_returned": len(lines),
            "games_with_usable_lines": used_count,
        })

    rows = pd.DataFrame(all_rows)
    if rows.empty:
        raise SystemExit("No CFBD game-line rows built.")

    rows = rows.merge(
        ten,
        left_on=["season", "team_key"],
        right_on=["season", "historical_team_key"],
        how="left"
    )

    rows = rows[rows["coach"].notna() & rows["current_team"].notna()].copy()

    rows.to_csv(OUT / "coach_full_game_fav_dog_cfbd_game_rows.csv", index=False)

    def agg(g):
        ats_w = (g["ats_result"] == "W").sum()
        ats_l = (g["ats_result"] == "L").sum()
        ats_p = (g["ats_result"] == "P").sum()
        ats_dec = ats_w + ats_l

        overs = (g["total_result"] == "O").sum()
        unders = (g["total_result"] == "U").sum()
        total_p = (g["total_result"] == "P").sum()
        total_dec = overs + unders

        return pd.Series({
            "period": "Full Game",
            "games": len(g),
            "ats_w": ats_w,
            "ats_l": ats_l,
            "ats_push": ats_p,
            "ats_win_pct": round(ats_w / ats_dec, 4) if ats_dec else "",
            "overs": overs,
            "unders": unders,
            "total_push": total_p,
            "over_pct": round(overs / total_dec, 4) if total_dec else "",
            "avg_ats_margin": round(pd.to_numeric(g["ats_margin"], errors="coerce").mean(), 2),
            "avg_total_margin": round(pd.to_numeric(g["total_margin"], errors="coerce").mean(), 2),
            "avg_spread": round(pd.to_numeric(g["team_spread"], errors="coerce").mean(), 2),
            "seasons": f"{int(g['season'].min())}-{int(g['season'].max())}",
            "historical_teams": ", ".join(sorted(set(str(x) for x in g["historical_team"].dropna()))),
            "source": "CFBD full-game lines/results",
        })

    splits = (
        rows[rows["fav_dog"].isin(["Favorite", "Underdog", "Pick"])]
        .groupby(["coach", "current_team", "fav_dog"], dropna=False)
        .apply(agg)
        .reset_index()
        .sort_values(["current_team", "coach", "fav_dog"])
    )

    splits.to_csv(OUT / "coach_full_game_fav_dog_cfbd_splits.csv", index=False)
    pd.DataFrame(audit_rows).to_csv(AUDIT / "coach_full_game_fav_dog_cfbd_audit.csv", index=False)

    print("wrote:", OUT / "coach_full_game_fav_dog_cfbd_game_rows.csv", "rows:", len(rows))
    print("wrote:", OUT / "coach_full_game_fav_dog_cfbd_splits.csv", "rows:", len(splits))
    print("wrote:", AUDIT / "coach_full_game_fav_dog_cfbd_audit.csv")

    print("\nAudit:")
    print(pd.DataFrame(audit_rows).to_string(index=False))

    print("\nSample:")
    print(splits.head(40).to_string(index=False))

if __name__ == "__main__":
    build()
