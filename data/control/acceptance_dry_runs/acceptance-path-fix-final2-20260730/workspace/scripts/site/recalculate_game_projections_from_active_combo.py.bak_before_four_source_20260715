from pathlib import Path
import re
import json
import math
import pandas as pd

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

def fnum(x, default=None):
    try:
        if x is None or pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default

def win_prob_from_margin(margin):
    return 1.0 / (1.0 + math.exp(-margin / 6.5))

def load_db(path):
    s = path.read_text(errors="ignore")
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', s, flags=re.S)
    if not m:
        raise SystemExit(f"DB JSON not found in {path}")
    return s, json.loads(m.group(1)), m

def write_db(path, html, db, m):
    new = json.dumps(db, separators=(",", ":"))
    path.write_text(html[:m.start(1)] + new + html[m.end(1):], encoding="utf-8")

def recalc(path):
    html, db, m = load_db(path)

    teams = {t.get("team"): t for t in db.get("teams", [])}
    changed = 0
    skipped = 0

    for g in db.get("games", []):
        away = g.get("away_team")
        home = g.get("home_team")
        at = teams.get(away)
        ht = teams.get(home)

        if not at or not ht:
            skipped += 1
            continue

        away_rating = fnum(at.get("combo"))
        home_rating = fnum(ht.get("combo"))

        if away_rating is None or home_rating is None:
            skipped += 1
            continue

        neutral = bool(
            g.get("neutral_site")
            or g.get("neutral")
            or g.get("is_neutral")
            or g.get("Neutral Site?")
        )

        hfa = 0.0 if neutral else fnum(ht.get("hfa"), 0.0)
        margin_home = home_rating - away_rating + hfa
        wp_home = win_prob_from_margin(margin_home)

        old_margin = fnum(g.get("projected_margin_home"))

        g["projected_margin_home"] = round(margin_home, 4)
        g["projection_spread_home"] = round(margin_home, 4)
        g["site_spread_home"] = round(margin_home, 4)
        g["blend_spread_home"] = round(margin_home, 4)

        g["win_prob_home"] = round(wp_home, 12)
        g["home_win_prob"] = round(wp_home, 6)
        g["away_win_prob"] = round(1.0 - wp_home, 6)

        fav = home if margin_home >= 0 else away
        g["projection_spread_text"] = f"{fav} -{abs(margin_home):.1f}"
        g["projection_spread_sources"] = "Active Combo"
        g["projection_status"] = "active_combo_projection"
        g["projection_note"] = "Projected spread recalculated from active SP+/FPI/TeamRankings combo plus HFA."

        if old_margin is None or abs(old_margin - margin_home) > 0.0001:
            changed += 1

    write_db(path, html, db, m)
    print(f"{path}: recalculated={changed}, skipped={skipped}, games={len(db.get('games', []))}")

for p in TARGETS:
    if p.exists():
        backup = p.with_suffix(p.suffix + ".bak_before_active_combo_projection")
        if not backup.exists():
            backup.write_text(p.read_text(errors="ignore"), encoding="utf-8")
        recalc(p)
