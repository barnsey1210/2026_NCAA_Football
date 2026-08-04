#!/usr/bin/env python3
"""
Cleaner total audit for the NCAAF site.

This version separates expected non-FBS/FCS missing totals from true FBS total issues.
It does not modify index.html.

Run from ~/NCAAF_AUTO:
    python3 scripts/audit/audit_game_projection_totals_v2.py

Outputs:
    data/audits/game_projection_total_audit.csv
    data/audits/game_projection_total_audit_summary.csv
"""
from __future__ import annotations

import csv, json, math, re
from pathlib import Path

ROOT = Path.cwd()
INDEX_PATH = ROOT / "index.html"
SOURCES_PATH = ROOT / "data" / "projections" / "game_projection_sources_2026.csv"
OUT_DIR = ROOT / "data" / "audits"
AUDIT_CSV = OUT_DIR / "game_projection_total_audit.csv"
SUMMARY_CSV = OUT_DIR / "game_projection_total_audit_summary.csv"

TOTAL_MIN = 34.0
TOTAL_MAX = 85.0
MARKET_WARN = 8.0
MARKET_MAJOR = 14.0
SOURCE_WARN = 6.0
SOURCE_MAJOR = 10.0


def fnum(x):
    try:
        if x is None or x == "": return None
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def load_db():
    html = INDEX_PATH.read_text(errors="ignore")
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit("ERROR: embedded DB not found in index.html")
    return json.loads(m.group(1))


def load_source_totals():
    out = {}
    if not SOURCES_PATH.exists() or SOURCES_PATH.stat().st_size == 0:
        return out
    with SOURCES_PATH.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            gid = str(r.get("game_id", ""))
            src = str(r.get("source", ""))
            total = fnum(r.get("total"))
            if gid and src and total is not None:
                out.setdefault(gid, {})[src] = total
    return out


def score_parts(total, home_margin):
    t, m = fnum(total), fnum(home_margin)
    if t is None or m is None:
        return None, None
    return (t - m) / 2, (t + m) / 2


def severity(flags):
    if any(f in flags for f in ["MISSING_TOTAL_FBS", "IMPOSSIBLE_SCORE", "MARKET_DIFF_MAJOR", "MASSEY_DIFF_MAJOR"]):
        return "MAJOR"
    if any(f in flags for f in ["OUT_OF_RANGE", "MARKET_DIFF_WARN", "MASSEY_DIFF_WARN", "MISSING_TOTAL_WITH_MARKET_NON_FBS"]):
        return "WARN"
    if any(f.startswith("INFO_") for f in flags):
        return "INFO"
    return "OK"


def main():
    if not INDEX_PATH.exists():
        raise SystemExit("ERROR: index.html not found. Run from ~/NCAAF_AUTO.")

    db = load_db()
    team_set = {str(t.get("team", "")) for t in db.get("teams", []) if t.get("team")}
    src_totals = load_source_totals()
    games = db.get("games", []) or []
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    counts = {"games": 0, "ok": 0, "info": 0, "warn": 0, "major": 0, "fbs_games": 0, "non_fbs_or_unmapped_games": 0, "has_market_total": 0, "has_massey_total": 0}

    for g in games:
        counts["games"] += 1
        gid = str(g.get("game_id", ""))
        away = str(g.get("away_team") or "")
        home = str(g.get("home_team") or "")
        is_fbs_mapped = away in team_set and home in team_set
        if is_fbs_mapped: counts["fbs_games"] += 1
        else: counts["non_fbs_or_unmapped_games"] += 1

        proj_total = fnum(g.get("projected_total"))
        market_total = fnum(g.get("market_total"))
        home_margin = fnum(g.get("projected_margin_home"))
        srcs = src_totals.get(gid, {})
        massey_total = srcs.get("Massey Games")
        if market_total is not None: counts["has_market_total"] += 1
        if massey_total is not None: counts["has_massey_total"] += 1

        flags, notes = [], []
        if proj_total is None:
            if is_fbs_mapped:
                flags.append("MISSING_TOTAL_FBS")
                notes.append("projected_total missing for mapped FBS-vs-FBS game")
            elif market_total is not None:
                flags.append("MISSING_TOTAL_WITH_MARKET_NON_FBS")
                notes.append("non-FBS/unmapped game has market total but no model total")
            else:
                flags.append("INFO_MISSING_TOTAL_NON_FBS")
                notes.append("non-FBS/unmapped opponent; model total not expected yet")
        else:
            if proj_total < TOTAL_MIN or proj_total > TOTAL_MAX:
                flags.append("OUT_OF_RANGE")
                notes.append(f"projected_total {proj_total:.1f} outside {TOTAL_MIN:.0f}-{TOTAL_MAX:.0f} sanity range")
            away_pts, home_pts = score_parts(proj_total, home_margin)
            if away_pts is not None and home_pts is not None and (away_pts < -0.1 or home_pts < -0.1):
                flags.append("IMPOSSIBLE_SCORE")
                notes.append(f"implied score has negative points: {away} {away_pts:.1f}, {home} {home_pts:.1f}")
            if market_total is not None:
                mdiff = proj_total - market_total
                if abs(mdiff) >= MARKET_MAJOR:
                    flags.append("MARKET_DIFF_MAJOR")
                    notes.append(f"projection vs market total differs by {mdiff:+.1f}")
                elif abs(mdiff) >= MARKET_WARN:
                    flags.append("MARKET_DIFF_WARN")
                    notes.append(f"projection vs market total differs by {mdiff:+.1f}")
            if massey_total is not None:
                sdiff = proj_total - massey_total
                if abs(sdiff) >= SOURCE_MAJOR:
                    flags.append("MASSEY_DIFF_MAJOR")
                    notes.append(f"projection vs Massey total differs by {sdiff:+.1f}")
                elif abs(sdiff) >= SOURCE_WARN:
                    flags.append("MASSEY_DIFF_WARN")
                    notes.append(f"projection vs Massey total differs by {sdiff:+.1f}")

        sev = severity(flags)
        counts[sev.lower()] += 1
        away_pts, home_pts = score_parts(proj_total, home_margin)
        rows.append({
            "severity": sev,
            "flags": ";".join(flags) if flags else "OK",
            "notes": " | ".join(notes),
            "is_fbs_mapped": is_fbs_mapped,
            "game_id": gid,
            "cfbd_game_id": g.get("cfbd_game_id", ""),
            "week": g.get("week", g.get("cfbd_week", "")),
            "date": g.get("date", g.get("cfbd_date", "")),
            "away_team": away,
            "home_team": home,
            "projected_total": proj_total,
            "market_total": market_total,
            "market_total_diff": None if proj_total is None or market_total is None else round(proj_total - market_total, 3),
            "massey_total": massey_total,
            "massey_total_diff": None if proj_total is None or massey_total is None else round(proj_total - massey_total, 3),
            "projected_margin_home": home_margin,
            "implied_away_points": None if away_pts is None else round(away_pts, 3),
            "implied_home_points": None if home_pts is None else round(home_pts, 3),
            "market_total_book": g.get("market_total_book", ""),
            "market_total_last_update": g.get("market_total_last_update", ""),
            "projection_total_sources": g.get("projection_total_sources", ""),
        })

    def sort_key(r):
        sev_rank = {"MAJOR": 0, "WARN": 1, "INFO": 2, "OK": 3}.get(r["severity"], 4)
        diffs = [abs(float(x)) for x in [r.get("market_total_diff"), r.get("massey_total_diff")] if x not in (None, "")]
        return (sev_rank, -max(diffs or [0]), str(r.get("date", "")))
    rows.sort(key=sort_key)

    fields = ["severity", "flags", "notes", "is_fbs_mapped", "game_id", "cfbd_game_id", "week", "date", "away_team", "home_team", "projected_total", "market_total", "market_total_diff", "massey_total", "massey_total_diff", "projected_margin_home", "implied_away_points", "implied_home_points", "market_total_book", "market_total_last_update", "projection_total_sources"]
    with AUDIT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "value"]); w.writeheader()
        for k,v in counts.items(): w.writerow({"metric": k, "value": v})

    print(f"wrote: {AUDIT_CSV}")
    print(f"wrote: {SUMMARY_CSV}")
    print("summary:", counts)
    print("\nTop actionable total flags:")
    for r in rows[:50]:
        if r["severity"] not in {"MAJOR", "WARN"}: continue
        print(f"{r['severity']:>5} {r['date']} W{r['week']} {r['away_team']} at {r['home_team']} | proj {r['projected_total']} market {r['market_total']} diff {r['market_total_diff']} | {r['flags']}")

if __name__ == "__main__":
    main()
