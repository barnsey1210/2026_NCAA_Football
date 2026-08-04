#!/usr/bin/env python3
import html as html_lib
import json
import math
import re
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

FILES = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

AUDIT = Path("data/audit/projection_rating_mismatch_fixes.csv")

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

def extract_db_and_span(text):
    m = re.search(r'(<script[^>]+id=["\']db["\'][^>]*>)(.*?)(</script>)', text, re.S)
    if not m:
        raise ValueError("Could not find script id=db")
    raw = html_lib.unescape(m.group(2).strip())
    db = json.loads(raw)
    return db, m.start(2), m.end(2)

def replace_db(text, start, end, db):
    payload = json.dumps(db, separators=(",", ":"), ensure_ascii=False)
    return text[:start] + payload + text[end:]

def get_team_name(t):
    return str(t.get("team") or t.get("name") or "").strip()

def get_rating(t):
    for k in ["combo", "rating_combo", "power_combo", "avg_rating", "power_rating", "rating", "team_rating"]:
        v = fnum(t.get(k))
        if v is not None:
            return v
    return None

def get_rank(t):
    for k in ["rank", "combo_rank", "rating_rank", "power_rank"]:
        v = fnum(t.get(k))
        if v is not None:
            return int(v)
    return None

def get_game_team(g, side):
    for k in [f"{side}_team", side, f"{side}_name", f"{side}Team"]:
        if k in g and str(g[k]).strip():
            return str(g[k]).strip()
    return ""

def get_hfa(g, home_team):
    for k in ["hfa", "home_field_advantage", "home_advantage"]:
        v = fnum(g.get(k))
        if v is not None:
            return v

    for k in ["hfa", "home_field_advantage", "home_advantage"]:
        v = fnum(home_team.get(k)) if home_team else None
        if v is not None:
            return v

    neutral = str(g.get("neutral_site", g.get("neutral", ""))).lower() in ["1", "true", "yes"]
    return 0.0 if neutral else 2.5

def get_proj(g):
    for k in ["projected_margin_home", "proj_margin_home", "rating_margin_home", "projected_spread_home"]:
        v = fnum(g.get(k))
        if v is not None:
            return v, k
    return None, ""

def line(home, away, margin_home):
    if margin_home is None:
        return ""
    if abs(margin_home) < 0.05:
        return "Pick"
    if margin_home > 0:
        return f"{home} -{abs(margin_home):.1f}"
    return f"{away} -{abs(margin_home):.1f}"

all_fixes = []

for path in FILES:
    if not path.exists():
        continue

    text = path.read_text(errors="ignore")
    db, start, end = extract_db_and_span(text)

    teams = db.get("teams", [])
    games = db.get("games", [])

    team_map = {get_team_name(t): t for t in teams if get_team_name(t)}

    changed = 0

    for g in games:
        home = get_game_team(g, "home")
        away = get_game_team(g, "away")

        ht = team_map.get(home, {})
        at = team_map.get(away, {})

        hr = get_rating(ht)
        ar = get_rating(at)
        home_rank = get_rank(ht)
        away_rank = get_rank(at)

        stored, key = get_proj(g)

        if not key or stored is None or hr is None or ar is None:
            continue

        hfa = get_hfa(g, ht)
        rating_margin = round(hr - ar + hfa, 1)
        diff = round(stored - rating_margin, 1)

        reasons = []

        if stored * rating_margin < 0 and abs(diff) >= 3.0:
            reasons.append("sign_mismatch")

        if abs(stored) <= 1.5 and abs(rating_margin) >= 4.0 and abs(diff) >= 3.0:
            reasons.append("default_or_too_small")

        if abs(diff) >= 5.0:
            reasons.append("diff_5plus")

        if not reasons:
            continue

        g["projected_margin_home_before_rating_audit_fix"] = stored
        g[key] = rating_margin
        g["projection_rating_audit_fix_note"] = (
            f"Corrected {key} from {stored:.1f} to {rating_margin:.1f}; "
            f"stored={line(home, away, stored)}; rating={line(home, away, rating_margin)}; "
            f"reasons={','.join(reasons)}; fixed_at={datetime.now(timezone.utc).isoformat()}"
        )

        all_fixes.append({
            "file": str(path),
            "week": g.get("week", ""),
            "date": g.get("date", g.get("game_date", "")),
            "away": away,
            "home": home,
            "away_rank": away_rank,
            "home_rank": home_rank,
            "stored_before": stored,
            "rating_margin_home": rating_margin,
            "diff_before": diff,
            "stored_line_before": line(home, away, stored),
            "rating_line_after": line(home, away, rating_margin),
            "reasons": ",".join(reasons),
        })

        changed += 1

    if changed:
        backup = path.with_suffix(path.suffix + ".before_projection_rating_fix")
        backup.write_text(text)
        new_text = replace_db(text, start, end, db)
        path.write_text(new_text)
        print(path, "fixed", changed, "backup", backup)
    else:
        print(path, "fixed", 0)

AUDIT.parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame(all_fixes).to_csv(AUDIT, index=False)
print("wrote:", AUDIT)
if all_fixes:
    print(pd.DataFrame(all_fixes).to_string(index=False))
