#!/usr/bin/env python3
"""
Audit game projected totals for the standalone site DB.

Unlike spread, total does not have a simple one-line combo-rating identity like:
    home_combo - away_combo + HFA

So this audit checks totals by sanity and cross-source tests:
    - missing / non-numeric projected_total
    - unrealistic total range
    - implied projected team scores below zero
    - large disagreement vs market total
    - large disagreement vs optional source file totals, especially Massey Games

Run from ~/NCAAF_AUTO:
    python3 scripts/audit/audit_game_projection_totals.py

Outputs:
    data/audits/game_projection_total_audit.csv
    data/audits/game_projection_total_audit_summary.csv
"""
from __future__ import annotations

import csv
import json
import math
import re
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
        if x is None or x == "":
            return None
        v = float(x)
        if math.isfinite(v):
            return v
    except Exception:
        return None
    return None


def load_db(index_path: Path) -> dict:
    html = index_path.read_text(errors="ignore")
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit(f"ERROR: could not find embedded DB in {index_path}")
    return json.loads(m.group(1))


def load_source_totals(path: Path) -> dict:
    # Map game_id -> {source: total}
    out: dict[str, dict[str, float]] = {}
    if not path.exists() or path.stat().st_size == 0:
        return out
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            gid = str(r.get("game_id", ""))
            src = str(r.get("source", ""))
            total = fnum(r.get("total"))
            if gid and src and total is not None:
                out.setdefault(gid, {})[src] = total
    return out


def score_parts(total, home_margin):
    t = fnum(total)
    m = fnum(home_margin)
    if t is None or m is None:
        return None, None
    return (t - m) / 2, (t + m) / 2  # away points, home points


def severity(flags: list[str]) -> str:
    if any("MAJOR" in f or "IMPOSSIBLE" in f or "MISSING" in f for f in flags):
        return "MAJOR"
    if any("WARN" in f or "OUT_OF_RANGE" in f for f in flags):
        return "WARN"
    return "OK"


def main() -> None:
    if not INDEX_PATH.exists():
        raise SystemExit("ERROR: index.html not found. Run from ~/NCAAF_AUTO.")

    db = load_db(INDEX_PATH)
    source_totals = load_source_totals(SOURCES_PATH)
    games = db.get("games", []) or []
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    counts = {"games": 0, "ok": 0, "warn": 0, "major": 0, "has_market_total": 0, "has_massey_total": 0}

    for g in games:
        counts["games"] += 1
        gid = str(g.get("game_id", ""))
        away = str(g.get("away_team") or "")
        home = str(g.get("home_team") or "")
        proj_total = fnum(g.get("projected_total"))
        market_total = fnum(g.get("market_total"))
        home_margin = fnum(g.get("projected_margin_home"))
        srcs = source_totals.get(gid, {})
        massey_total = srcs.get("Massey Games")

        if market_total is not None:
            counts["has_market_total"] += 1
        if massey_total is not None:
            counts["has_massey_total"] += 1

        flags = []
        notes = []

        if proj_total is None:
            flags.append("MISSING_TOTAL")
            notes.append("projected_total is missing or non-numeric")
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
        sev_rank = {"MAJOR": 0, "WARN": 1, "OK": 2}.get(r["severity"], 3)
        diffs = [abs(float(x)) for x in [r.get("market_total_diff"), r.get("massey_total_diff")] if x not in (None, "")]
        return (sev_rank, -max(diffs or [0]), str(r.get("date", "")))

    rows.sort(key=sort_key)

    fields = [
        "severity", "flags", "notes", "game_id", "cfbd_game_id", "week", "date", "away_team", "home_team",
        "projected_total", "market_total", "market_total_diff", "massey_total", "massey_total_diff",
        "projected_margin_home", "implied_away_points", "implied_home_points",
        "market_total_book", "market_total_last_update", "projection_total_sources",
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
    print("\nTop total audit flags:")
    for r in rows[:30]:
        if r["severity"] == "OK":
            continue
        print(
            f"{r['severity']:>5} {r['date']} W{r['week']} {r['away_team']} at {r['home_team']} | "
            f"proj {r['projected_total']} market {r['market_total']} diff {r['market_total_diff']} | {r['flags']}"
        )


if __name__ == "__main__":
    main()
