#!/usr/bin/env python3
"""
Audit game projected spreads against the current team power ratings embedded in index.html.

Purpose
-------
Catch games where the stored game projection no longer matches the current team ratings
+ home-field logic shown on the site.

Expected home margin formula:
    expected_home_margin = home_combo - away_combo + home_hfa_used

Where:
    home_hfa_used = 0 for neutral-site games, otherwise the home team's hfa.

The site displays a projected spread from projected_margin_home:
    if projected_margin_home > 0 => home favored by projected_margin_home
    if projected_margin_home < 0 => away favored by abs(projected_margin_home)

Run from ~/NCAAF_AUTO:
    python3 scripts/audit/audit_game_projection_spreads.py

Outputs:
    data/audits/game_projection_spread_audit.csv
    data/audits/game_projection_spread_audit_summary.csv
"""
from __future__ import annotations

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
AUDIT_CSV = OUT_DIR / "game_projection_spread_audit.csv"
SUMMARY_CSV = OUT_DIR / "game_projection_spread_audit_summary.csv"

WARN_THRESHOLD = 0.75
BAD_THRESHOLD = 1.50
MAJOR_THRESHOLD = 3.00


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


def fmt_spread(team: str, spread_for_team: float | None) -> str:
    if spread_for_team is None:
        return ""
    if abs(spread_for_team) < 0.05:
        return f"{team} PK"
    return f"{team} {spread_for_team:+.1f}".replace(".0", "")


def spread_from_home_margin(home_team: str, away_team: str, home_margin: float | None) -> str:
    if home_margin is None:
        return ""
    if abs(home_margin) < 0.05:
        return f"{home_team} PK"
    if home_margin > 0:
        return fmt_spread(home_team, -abs(home_margin))
    return fmt_spread(away_team, -abs(home_margin))


def load_db(index_path: Path) -> dict:
    html = index_path.read_text(errors="ignore")
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit(f"ERROR: could not find embedded DB in {index_path}")
    return json.loads(m.group(1))


def main() -> None:
    if not INDEX_PATH.exists():
        raise SystemExit(f"ERROR: {INDEX_PATH} not found. Run from ~/NCAAF_AUTO or adjust INDEX_PATH.")

    db = load_db(INDEX_PATH)
    teams = {str(t.get("team", "")): t for t in db.get("teams", []) if t.get("team")}
    games = db.get("games", []) or []

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    counts = {
        "games": 0,
        "ok": 0,
        "warn": 0,
        "bad": 0,
        "major": 0,
        "missing_team": 0,
        "missing_rating": 0,
    }

    for g in games:
        counts["games"] += 1
        away = str(g.get("away_team") or "")
        home = str(g.get("home_team") or "")
        away_row = teams.get(away)
        home_row = teams.get(home)

        projected_margin_home = fnum(g.get("projected_margin_home"))
        neutral = is_neutral_site(g)

        away_power = fnum(away_row.get("combo")) if away_row else None
        home_power = fnum(home_row.get("combo")) if home_row else None
        home_hfa = fnum(home_row.get("hfa")) if home_row else None
        hfa_used = 0.0 if neutral else (home_hfa if home_hfa is not None else 0.0)

        expected_margin_home = None
        diff = None
        flag = "OK"
        reason = ""

        if not away_row or not home_row:
            flag = "MISSING_TEAM"
            reason = "team missing from DB.teams"
            counts["missing_team"] += 1
        elif away_power is None or home_power is None:
            flag = "MISSING_RATING"
            reason = "team combo rating missing"
            counts["missing_rating"] += 1
        elif projected_margin_home is None:
            flag = "MISSING_PROJECTION"
            reason = "game projected_margin_home missing"
            counts["bad"] += 1
        else:
            expected_margin_home = home_power - away_power + hfa_used
            diff = projected_margin_home - expected_margin_home
            adiff = abs(diff)
            if adiff >= MAJOR_THRESHOLD:
                flag = "MAJOR"
                counts["major"] += 1
            elif adiff >= BAD_THRESHOLD:
                flag = "BAD"
                counts["bad"] += 1
            elif adiff >= WARN_THRESHOLD:
                flag = "WARN"
                counts["warn"] += 1
            else:
                counts["ok"] += 1

            if flag != "OK":
                reason = f"stored projection differs from current rating formula by {diff:+.2f} pts"

        rows.append({
            "flag": flag,
            "reason": reason,
            "game_id": g.get("game_id", ""),
            "cfbd_game_id": g.get("cfbd_game_id", ""),
            "week": g.get("week", g.get("cfbd_week", "")),
            "date": g.get("date", g.get("cfbd_date", "")),
            "away_team": away,
            "home_team": home,
            "neutral_site": neutral,
            "away_power": away_power,
            "home_power": home_power,
            "home_hfa": home_hfa,
            "hfa_used": hfa_used,
            "stored_projected_margin_home": projected_margin_home,
            "expected_margin_home": expected_margin_home,
            "projection_diff_pts": diff,
            "stored_projected_spread": spread_from_home_margin(home, away, projected_margin_home),
            "expected_projected_spread": spread_from_home_margin(home, away, expected_margin_home),
            "market_spread": g.get("market_spread_text", g.get("market_formatted_spread", "")),
            "projected_total": g.get("projected_total", ""),
            "market_total": g.get("market_total", ""),
        })

    # Sort highest-risk first, then date/week.
    def sort_key(r):
        diff = r.get("projection_diff_pts")
        adiff = abs(float(diff)) if diff not in (None, "") else -1
        return (-adiff, str(r.get("date", "")), str(r.get("game_id", "")))

    rows.sort(key=sort_key)

    fields = [
        "flag", "reason", "game_id", "cfbd_game_id", "week", "date",
        "away_team", "home_team", "neutral_site", "away_power", "home_power",
        "home_hfa", "hfa_used", "stored_projected_margin_home", "expected_margin_home",
        "projection_diff_pts", "stored_projected_spread", "expected_projected_spread",
        "market_spread", "projected_total", "market_total",
    ]

    with AUDIT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "value"])
        w.writeheader()
        for k, v in counts.items():
            w.writerow({"metric": k, "value": v})

    print(f"wrote: {AUDIT_CSV}")
    print(f"wrote: {SUMMARY_CSV}")
    print("summary:", counts)
    print("\nTop projection mismatches:")
    for r in rows[:25]:
        if r["flag"] == "OK":
            continue
        diff = r["projection_diff_pts"]
        diff_s = f"{diff:+.2f}" if isinstance(diff, (int, float)) else ""
        print(
            f"{r['flag']:>6} {r['date']} W{r['week']} "
            f"{r['away_team']} at {r['home_team']} | "
            f"stored {r['stored_projected_spread']} vs expected {r['expected_projected_spread']} | diff {diff_s}"
        )


if __name__ == "__main__":
    main()
