#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

FILES = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

CSV_1H = Path("data/import/coach_1h_betting_current_2026.csv")
CSV_2H = Path("data/import/coach_2h_betting_current_2026.csv")

def clean_key(c: str) -> str:
    s = str(c).strip().lower()
    s = s.replace("%", "")
    s = s.replace("+/-", "")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s

def load_rows(path: Path):
    df = pd.read_csv(path)
    df.columns = [clean_key(c) for c in df.columns]

    # Match existing frontend key expectations.
    rename = {
        "current_coach": "current_coach",
        "current_team": "current_team",
        "historical_team_s": "historical_team_s",
        "ats_rank": "ats_rank",
        "games": "games",
        "ats_games": "ats_games",
        "ats_w": "ats_w",
        "ats_l": "ats_l",
        "ats_push": "ats_push",
        "ats_win": "ats_win",
        "avg_ats": "avg_ats",
        "over_games": "over_games",
        "overs": "overs",
        "unders": "unders",
        "total_push": "total_push",
        "over": "over",
        "avg_total": "avg_total",
        "seasons_covered": "seasons_covered",
    }
    df = df.rename(columns=rename)

    # Convert NaN to None and keep JSON clean.
    rows = []
    for rec in df.to_dict(orient="records"):
        out = {}
        for k, v in rec.items():
            if pd.isna(v):
                out[k] = None
            else:
                out[k] = v

        # Frontend compatibility aliases.
        # Older site components expect generic coach betting keys.
        out["team"] = out.get("current_team")
        out["coach"] = out.get("current_coach")
        out["head_coach"] = out.get("current_coach")
        out["tracked_teams"] = out.get("historical_team_s")
        out["ats_pct"] = out.get("ats_win")
        out["ats_win_pct"] = out.get("ats_win")
        out["ats_margin"] = out.get("avg_ats")
        out["ats_plus_minus"] = out.get("avg_ats")
        out["ats_pm"] = out.get("avg_ats")
        out["ats_margin_avg"] = out.get("avg_ats")
        out["avg_ats_margin"] = out.get("avg_ats")
        out["avg_ats_plus_minus"] = out.get("avg_ats")
        out["avg_cover_margin"] = out.get("avg_ats")
        out["cover_margin"] = out.get("avg_ats")
        out["over_pct"] = out.get("over")
        out["total_margin"] = out.get("avg_total")
        out["avg_total_margin"] = out.get("avg_total")

        # Display-friendly records.
        try:
            w = int(out.get("ats_w") or 0)
            l = int(out.get("ats_l") or 0)
            push = int(out.get("ats_push") or 0)
            out["ats_record"] = f"{w}-{l}-{push}"
        except Exception:
            out["ats_record"] = None

        try:
            o = int(out.get("overs") or 0)
            u = int(out.get("unders") or 0)
            tp = int(out.get("total_push") or 0)
            out["ou_record"] = f"{o}-{u}-{tp}"
            out["over_under_record"] = out["ou_record"]
        except Exception:
            out["ou_record"] = None
            out["over_under_record"] = None

        rows.append(out)
    return rows

def inject(path: Path, rows_1h, rows_2h):
    txt = path.read_text(errors="ignore")
    m = re.search(r'(<script id="db" type="application/json">)(.*?)(</script>)', txt, re.S)
    if not m:
        raise SystemExit(f"{path}: DB script tag not found")

    db = json.loads(m.group(2))
    db["coach_1h_betting"] = rows_1h
    db["coach_2h_betting"] = rows_2h
    db["coach_1h_summary"] = rows_1h
    db["coach_2h_summary"] = rows_2h

    # Add/update metadata so the page can later display this cleanly.
    db.setdefault("meta", {})
    db["meta"]["coach_halves_source"] = "SGO 2024/2025 complete refresh"
    db["meta"]["coach_halves_stats_through"] = "2026-01-20"

    new_json = json.dumps(db, separators=(",", ":"), ensure_ascii=False)
    new_txt = txt[:m.start(2)] + new_json + txt[m.end(2):]
    path.write_text(new_txt)
    print(f"{path}: injected {len(rows_1h)} 1H rows and {len(rows_2h)} 2H rows")

def main():
    if not CSV_1H.exists():
        raise SystemExit(f"Missing {CSV_1H}")
    if not CSV_2H.exists():
        raise SystemExit(f"Missing {CSV_2H}")

    rows_1h = load_rows(CSV_1H)
    rows_2h = load_rows(CSV_2H)

    for p in FILES:
        if p.exists():
            inject(p, rows_1h, rows_2h)

if __name__ == "__main__":
    main()
