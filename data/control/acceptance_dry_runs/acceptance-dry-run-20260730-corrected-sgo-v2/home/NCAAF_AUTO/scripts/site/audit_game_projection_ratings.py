#!/usr/bin/env python3
import json
import math
import re
from pathlib import Path

import pandas as pd

HTML_PATH = Path("index.html")
OUT_ALL = Path("data/audit/game_projection_rating_audit.csv")
OUT_BAD = Path("data/audit/game_projection_rating_suspicious.csv")

def extract_db(html):
    import html as html_lib

    m = re.search(r'<script[^>]+id=["\']db["\'][^>]*>(.*?)</script>', html, re.S)
    if m:
        raw = html_lib.unescape(m.group(1).strip())
        return json.loads(raw)

    markers = [
        "window.__NCAAF_DB__",
        "window.NCAAF_DB",
        "__NCAAF_DB__",
        "const DB",
    ]

    idx = -1
    for marker in markers:
        idx = html.find(marker)
        if idx >= 0:
            break

    if idx < 0:
        raise ValueError("Could not find DB marker or script id=db in index.html")

    start_json = html.find("{", idx)
    if start_json < 0:
        raise ValueError("Could not find JSON start")

    in_str = False
    esc = False
    depth = 0

    for i in range(start_json, len(html)):
        ch = html[i]

        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[start_json:i+1])

    raise ValueError("Could not find JSON end")

def fnum(x):
    try:
        if x is None or x == "":
            return None
        v = float(x)
        if math.isnan(v):
            return None
        return v
    except Exception:
        return None

def team_name(x):
    return str(x or "").strip()

def get_team_key(t):
    for k in ["team", "name", "school", "display_name"]:
        if k in t and str(t[k]).strip():
            return str(t[k]).strip()
    return ""

def get_rating(t):
    keys = [
        "combo",
        "rating_combo",
        "power_combo",
        "avg_rating",
        "power_rating",
        "rating",
        "team_rating",
    ]
    for k in keys:
        v = fnum(t.get(k))
        if v is not None:
            return v, k
    return None, ""

def get_rank(t):
    for k in ["rank", "combo_rank", "rating_rank", "power_rank"]:
        v = fnum(t.get(k))
        if v is not None:
            return int(v), k
    return None, ""

def get_hfa(g, home_team):
    for k in ["hfa", "home_field_advantage", "home_advantage"]:
        v = fnum(g.get(k))
        if v is not None:
            return v, f"game.{k}"

    for k in ["hfa", "home_field_advantage", "home_advantage"]:
        v = fnum(home_team.get(k, None)) if home_team else None
        if v is not None:
            return v, f"home_team.{k}"

    neutral = str(g.get("neutral_site", g.get("neutral", ""))).lower() in ["1", "true", "yes"]
    if neutral:
        return 0.0, "neutral_default"

    return 2.5, "default_2.5"

def get_game_team(g, side):
    candidates = [
        side,
        f"{side}_team",
        f"{side}_name",
        f"{side}Team",
    ]
    for k in candidates:
        if k in g and str(g[k]).strip():
            return str(g[k]).strip()
    return ""

def get_proj_margin_home(g):
    keys = [
        "projected_margin_home",
        "proj_margin_home",
        "rating_margin_home",
        "projected_spread_home",
    ]
    for k in keys:
        v = fnum(g.get(k))
        if v is not None:
            return v, k
    return None, ""

def fmt_line(home, away, margin_home):
    if margin_home is None:
        return ""
    if abs(margin_home) < 0.05:
        return "Pick"
    if margin_home > 0:
        return f"{home} -{abs(margin_home):.1f}"
    return f"{away} -{abs(margin_home):.1f}"

html = HTML_PATH.read_text(errors="ignore")
db = extract_db(html)

teams = db.get("teams", [])
games = db.get("games", db.get("schedule", []))

team_map = {}
for t in teams:
    nm = get_team_key(t)
    if nm:
        team_map[nm] = t

rows = []

for g in games:
    home = get_game_team(g, "home")
    away = get_game_team(g, "away")

    ht = team_map.get(home, {})
    at = team_map.get(away, {})

    home_rating, home_rating_key = get_rating(ht)
    away_rating, away_rating_key = get_rating(at)

    home_rank, home_rank_key = get_rank(ht)
    away_rank, away_rank_key = get_rank(at)

    proj, proj_key = get_proj_margin_home(g)
    hfa, hfa_source = get_hfa(g, ht)

    rating_margin_home = None
    diff = None
    if home_rating is not None and away_rating is not None:
        rating_margin_home = home_rating - away_rating + hfa

    if proj is not None and rating_margin_home is not None:
        diff = proj - rating_margin_home

    issues = []

    if home_rating is None:
        issues.append("missing_home_rating")
    if away_rating is None:
        issues.append("missing_away_rating")
    if proj is None:
        issues.append("missing_projected_margin")

    if proj is not None and rating_margin_home is not None:
        if abs(proj) == 1.0 and abs(rating_margin_home - proj) >= 3.0:
            issues.append("possible_default_1")
        if abs(proj) <= 1.5 and abs(rating_margin_home) >= 4.0:
            issues.append("suspicious_small_projection")
        if proj * rating_margin_home < 0 and abs(diff) >= 3.0:
            issues.append("sign_mismatch")
        if abs(diff) >= 7.0:
            issues.append("big_diff_7plus")
        if abs(diff) >= 5.0:
            issues.append("diff_5plus")

    rows.append({
        "week": g.get("week", ""),
        "date": g.get("date", g.get("game_date", "")),
        "away": away,
        "home": home,
        "away_rank": away_rank,
        "home_rank": home_rank,
        "away_rating": away_rating,
        "home_rating": home_rating,
        "hfa": hfa,
        "hfa_source": hfa_source,
        "stored_margin_home": proj,
        "stored_margin_key": proj_key,
        "rating_margin_home": rating_margin_home,
        "diff_stored_minus_rating": diff,
        "stored_line": fmt_line(home, away, proj),
        "rating_line": fmt_line(home, away, rating_margin_home),
        "issues": ",".join(issues),
    })

df = pd.DataFrame(rows)

OUT_ALL.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_ALL, index=False)

bad = df[df["issues"].astype(str).ne("")].copy()
bad["abs_diff"] = pd.to_numeric(bad["diff_stored_minus_rating"], errors="coerce").abs()
bad = bad.sort_values(["abs_diff", "week", "date"], ascending=[False, True, True])
bad.to_csv(OUT_BAD, index=False)

print("games:", len(df))
print("teams:", len(team_map))
print("wrote:", OUT_ALL)
print("wrote:", OUT_BAD)

print("\nIssue counts:")
if bad.empty:
    print("none")
else:
    exploded = bad.assign(issue=bad["issues"].str.split(",")).explode("issue")
    print(exploded["issue"].value_counts().to_string())

print("\nTop suspicious:")
cols = [
    "week","date","away","home","away_rank","home_rank",
    "stored_line","rating_line","stored_margin_home","rating_margin_home",
    "diff_stored_minus_rating","issues"
]
print(bad[cols].head(40).to_string(index=False))

print("\nNC State / Virginia:")
mask = (
    df["away"].astype(str).str.contains("NC State", case=False, na=False) |
    df["home"].astype(str).str.contains("NC State", case=False, na=False) |
    df["away"].astype(str).str.contains("Virginia", case=False, na=False) |
    df["home"].astype(str).str.contains("Virginia", case=False, na=False)
)
print(df[mask & df["away"].astype(str).str.contains("NC State", case=False, na=False) & df["home"].astype(str).str.contains("Virginia", case=False, na=False)][cols].to_string(index=False))
