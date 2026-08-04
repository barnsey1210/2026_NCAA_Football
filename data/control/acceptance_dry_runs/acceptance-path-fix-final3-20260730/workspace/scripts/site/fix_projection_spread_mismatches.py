#!/usr/bin/env python3
import json
import math
import re
from pathlib import Path

FILES = ["index.html", "index_auto_market.html", "index_publish.html"]
THRESHOLD = 7.0

def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None

def load_db(html):
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit("Could not find DB JSON")
    return m, json.loads(m.group(1))

def display(home, away, margin_home):
    if margin_home is None:
        return ""
    if abs(margin_home) < 0.05:
        return "Pick"
    return f"{home} -{abs(margin_home):.1f}" if margin_home > 0 else f"{away} -{abs(margin_home):.1f}"

def fix_file(path):
    p = Path(path)
    if not p.exists():
        return

    html = p.read_text(errors="ignore")
    m, db = load_db(html)

    teams = {}
    for t in db.get("teams", []):
        name = str(t.get("team") or "").strip()
        if name:
            teams[name.lower()] = t

    fixes = []

    for g in db.get("games", []):
        away = g.get("away_team")
        home = g.get("home_team")
        at = teams.get(str(away).lower(), {})
        ht = teams.get(str(home).lower(), {})

        away_rating = num(at.get("combo"))
        home_rating = num(ht.get("combo"))
        current = num(g.get("projected_margin_home"))

        if away_rating is None or home_rating is None or current is None:
            continue

        hfa = num(ht.get("hfa"))
        if hfa is None:
            hfa = 0 if g.get("neutral_site") else 2.5

        rating_margin_home = home_rating - away_rating + (0 if g.get("neutral_site") else hfa)

        sign_mismatch = (current > 0 and rating_margin_home < 0) or (current < 0 and rating_margin_home > 0)
        diff = abs(current - rating_margin_home)

        if sign_mismatch and diff >= THRESHOLD:
            before = current
            g["projected_margin_home_before_projection_fix"] = before
            g["projected_margin_home"] = round(rating_margin_home, 3)
            g["projection_fix_note"] = (
                f"Corrected projected_margin_home from {before:.3f} to {rating_margin_home:.3f}; "
                f"rating sanity check: {display(home, away, rating_margin_home)}"
            )
            fixes.append({
                "week": g.get("week"),
                "away": away,
                "home": home,
                "before": before,
                "after": rating_margin_home,
                "before_display": display(home, away, before),
                "after_display": display(home, away, rating_margin_home),
            })

    if not fixes:
        print(f"{path}: no projection spread mismatches fixed")
        return

    new_json = json.dumps(db, separators=(",", ":"), ensure_ascii=False)
    html = html[:m.start(1)] + new_json + html[m.end(1):]
    p.write_text(html)

    print(f"{path}: fixed {len(fixes)} projection spread mismatch(es)")
    for f in fixes:
        print(f"  Week {f['week']}: {f['away']} at {f['home']} | {f['before_display']} -> {f['after_display']}")

def main():
    for f in FILES:
        fix_file(f)

if __name__ == "__main__":
    main()
