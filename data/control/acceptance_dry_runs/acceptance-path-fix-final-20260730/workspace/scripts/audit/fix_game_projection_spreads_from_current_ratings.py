#!/usr/bin/env python3
"""
Fix stored game projected spreads in index.html so they match current embedded team ratings.

Formula:
    projected_margin_home = home_combo - away_combo + (0 if neutral_site else home_hfa)

This script is intentionally narrow:
    - updates projected_margin_home only
    - does not change market lines
    - does not change projected_total
    - does not change schedule table code or matchup button behavior
    - skips games where either team cannot be mapped to DB.teams

Usage from ~/NCAAF_AUTO:
    python3 scripts/audit/fix_game_projection_spreads_from_current_ratings.py --dry-run
    python3 scripts/audit/fix_game_projection_spreads_from_current_ratings.py --apply

Outputs:
    data/audits/game_projection_spread_fix_preview.csv
    data/audits/game_projection_spread_fix_summary.csv
    index.html.bak_projection_fix when --apply is used
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.ncaaf_config import is_neutral_site

ROOT = Path.cwd()
INDEX_PATH = ROOT / "index.html"
OUT_DIR = ROOT / "data" / "audits"
PREVIEW_CSV = OUT_DIR / "game_projection_spread_fix_preview.csv"
SUMMARY_CSV = OUT_DIR / "game_projection_spread_fix_summary.csv"
BACKUP_PATH = ROOT / "index.html.bak_projection_fix"

THRESHOLD = 0.05


def fnum(x):
    try:
        if x is None or x == "":
            return None
        v = float(x)
        if math.isfinite(v):
            return v
    except Exception:
        return None
    return None


def boolish(x) -> bool:
    if isinstance(x, bool):
        return x
    if x is None:
        return False
    return str(x).strip().lower() in {"1", "true", "yes", "y"}


def spread_from_home_margin(home_team: str, away_team: str, home_margin: float | None) -> str:
    if home_margin is None:
        return ""
    if abs(home_margin) < 0.05:
        return f"{home_team} PK"
    if home_margin > 0:
        return f"{home_team} {-abs(home_margin):+.1f}".replace(".0", "")
    return f"{away_team} {-abs(home_margin):+.1f}".replace(".0", "")


def safe_json(obj) -> str:
    return json.dumps(obj, separators=(",", ":")).replace("</", "<\\/")


def load_index_db() -> tuple[str, dict, re.Match]:
    html = INDEX_PATH.read_text(errors="ignore")
    m = re.search(r'(<script id="db" type="application/json">)(.*?)(</script>)', html, re.S)
    if not m:
        raise SystemExit(f"ERROR: could not find embedded DB in {INDEX_PATH}")
    db = json.loads(m.group(2))
    return html, db, m


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write corrected projected_margin_home values back to index.html")
    ap.add_argument("--dry-run", action="store_true", help="preview only; this is the default")
    args = ap.parse_args()
    apply = bool(args.apply)

    if not INDEX_PATH.exists():
        raise SystemExit("ERROR: index.html not found. Run this from ~/NCAAF_AUTO.")

    html, db, m = load_index_db()
    teams = {str(t.get("team", "")): t for t in db.get("teams", []) if t.get("team")}
    games = db.get("games", []) or []
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    preview = []
    fixed = 0
    skipped_missing_team = 0
    skipped_missing_rating = 0
    unchanged = 0

    for g in games:
        away = str(g.get("away_team") or "")
        home = str(g.get("home_team") or "")
        away_row = teams.get(away)
        home_row = teams.get(home)
        if not away_row or not home_row:
            skipped_missing_team += 1
            continue

        away_power = fnum(away_row.get("combo"))
        home_power = fnum(home_row.get("combo"))
        home_hfa = fnum(home_row.get("hfa"))
        if away_power is None or home_power is None:
            skipped_missing_rating += 1
            continue

        neutral = is_neutral_site(g)
        hfa_used = 0.0 if neutral else (home_hfa if home_hfa is not None else 0.0)
        old = fnum(g.get("projected_margin_home"))
        new = round(home_power - away_power + hfa_used, 3)
        diff = None if old is None else old - new

        if old is None or abs(diff) > THRESHOLD:
            fixed += 1
            preview.append({
                "game_id": g.get("game_id", ""),
                "cfbd_game_id": g.get("cfbd_game_id", ""),
                "week": g.get("week", g.get("cfbd_week", "")),
                "date": g.get("date", g.get("cfbd_date", "")),
                "away_team": away,
                "home_team": home,
                "neutral_site": neutral,
                "away_power": away_power,
                "home_power": home_power,
                "hfa_used": hfa_used,
                "old_projected_margin_home": old,
                "new_projected_margin_home": new,
                "diff_removed": diff,
                "old_projected_spread": spread_from_home_margin(home, away, old),
                "new_projected_spread": spread_from_home_margin(home, away, new),
            })
            if apply:
                g["projected_margin_home"] = new
                g["projection_status"] = "rating_formula_corrected"
                g["projection_note"] = "Projected spread corrected from current team combo ratings plus HFA/neutral-site logic."
        else:
            unchanged += 1

    fields = [
        "game_id", "cfbd_game_id", "week", "date", "away_team", "home_team", "neutral_site",
        "away_power", "home_power", "hfa_used", "old_projected_margin_home",
        "new_projected_margin_home", "diff_removed", "old_projected_spread", "new_projected_spread",
    ]
    with PREVIEW_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(preview)

    summary = {
        "apply": apply,
        "games": len(games),
        "would_fix_or_fixed": fixed,
        "unchanged": unchanged,
        "skipped_missing_team": skipped_missing_team,
        "skipped_missing_rating": skipped_missing_rating,
        "preview_csv": str(PREVIEW_CSV),
    }
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "value"])
        w.writeheader()
        for k, v in summary.items():
            w.writerow({"metric": k, "value": v})

    if apply:
        BACKUP_PATH.write_text(html)
        new_db_json = safe_json(db)
        new_html = html[:m.start(2)] + new_db_json + html[m.end(2):]
        INDEX_PATH.write_text(new_html)
        print(f"updated: {INDEX_PATH}")
        print(f"backup:  {BACKUP_PATH}")
    else:
        print("dry run only; index.html not changed")

    print(f"wrote: {PREVIEW_CSV}")
    print(f"wrote: {SUMMARY_CSV}")
    print("summary:", summary)
    print("\nPreview of largest fixes:")
    for r in preview[:25]:
        diff = r["diff_removed"]
        diff_s = f"{diff:+.2f}" if isinstance(diff, (int, float)) else ""
        print(
            f"{r['date']} W{r['week']} {r['away_team']} at {r['home_team']} | "
            f"{r['old_projected_spread']} -> {r['new_projected_spread']} | removed {diff_s} pts"
        )


if __name__ == "__main__":
    main()
