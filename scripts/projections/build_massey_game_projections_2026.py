#!/usr/bin/env python3
"""
Parse live Massey FBS Games pages captured by:
collect_massey_games_2026_safari.py

Input:
data/ratings/external_sources/massey/browser_raw_2026/*.txt

Output:
data/ratings/external_sources/massey_game_projections_2026.csv
"""

from pathlib import Path
import re
import pandas as pd
from datetime import datetime


RAW_DIR = Path("data/ratings/external_sources/massey/browser_raw_2026")
OUT = Path("data/ratings/external_sources/massey_game_projections_2026.csv")
AUDIT = Path("data/ratings/external_sources/massey_game_projection_parse_audit_2026.csv")
PROGRESS = Path(
    "data/research/historical_totals/massey/"
    "massey_2026_safari_collection_progress.csv"
)


def collection_times():
    if not PROGRESS.is_file() or PROGRESS.stat().st_size == 0:
        return {}

    frame = pd.read_csv(PROGRESS, low_memory=False)
    if frame.empty or "date" not in frame.columns or "collected_at" not in frame.columns:
        return {}

    if "status" in frame.columns:
        frame = frame[frame["status"].astype(str).eq("OK")].copy()

    frame = frame.dropna(subset=["date", "collected_at"])
    if frame.empty:
        return {}

    frame["date"] = frame["date"].astype(str)
    frame["collected_at"] = frame["collected_at"].astype(str)
    frame = frame.sort_values("collected_at").drop_duplicates("date", keep="last")
    return dict(zip(frame["date"], frame["collected_at"]))


DATE_RE = re.compile(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\d{2}\.\d{2}$")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}\.PM\.ET$|^\d{1,2}:\d{2}\.AM\.ET$")
PCT_RE = re.compile(r"^\d+\s*%$")
NUM_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def parse_date(year, raw):
    month, day = raw.split()[1].split(".")
    return f"{year}-{int(month):02d}-{int(day):02d}"


def parse_file(path, pulled_at=None):
    rows = []
    audit = []

    lines = [
        x.strip()
        for x in path.read_text(errors="ignore").splitlines()
        if x.strip()
    ]

    year = 2026
    i = 0

    while i < len(lines):
        if not DATE_RE.match(lines[i]):
            i += 1
            continue

        raw_date = lines[i]
        game_date = parse_date(year, raw_date)
        i += 1

        if i < len(lines) and TIME_RE.match(lines[i]):
            i += 1

        if i + 1 >= len(lines):
            break

        away = lines[i]
        home_line = lines[i + 1]

        if home_line.startswith("@ "):
            home = home_line[2:].strip()
        else:
            home = home_line.strip()

        i += 2

        # skip rankings/standings
        while i < len(lines) and (
            lines[i].startswith("#")
            or lines[i].startswith("(")
        ):
            i += 1

        nums = []
        pcts = []

        while i < len(lines) and not DATE_RE.match(lines[i]):
            s = lines[i]

            if PCT_RE.match(s):
                pcts.append(float(s.replace("%", "")) / 100)
            elif NUM_RE.match(s):
                nums.append(float(s))

            i += 1

        # Expected:
        # scores (2), projected points (2), pwin (2), mov, total
        if len(nums) < 6 or len(pcts) < 2:
            audit.append({
                "file": path.name,
                "away": away,
                "home": home,
                "status": "INSUFFICIENT_FIELDS",
                "nums": len(nums),
                "pcts": len(pcts),
            })
            continue

        away_score = nums[0]
        home_score = nums[1]
        away_pred = nums[2]
        home_pred = nums[3]
        mov = nums[-2]
        total = nums[-1]

        rows.append({
            "snapshot_date": (
                str(pulled_at)[:10]
                if pulled_at
                else datetime.utcnow().date().isoformat()
            ),
            "pulled_at": pulled_at or "",
            "season": 2026,
            "game_date": game_date,
            "away_team": away,
            "home_team": home,
            "away_current_score": away_score,
            "home_current_score": home_score,
            "away_projected_points": away_pred,
            "home_projected_points": home_pred,
            "away_win_prob": pcts[0],
            "home_win_prob": pcts[1],
            "projected_spread_home": mov,
            "projected_total": total,
            "source_file": path.name,
            "source_url": "https://masseyratings.com/cf/fbs/games",
        })

        audit.append({
            "file": path.name,
            "away": away,
            "home": home,
            "status": "OK",
        })

    return rows, audit


def main():
    all_rows = []
    all_audit = []
    collected = collection_times()

    for path in sorted(RAW_DIR.glob("massey_games_*.txt")):
        raw_date = path.stem.replace("massey_games_", "")
        board_date = (
            f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
            if len(raw_date) == 8
            else ""
        )
        rows, audit = parse_file(path, pulled_at=collected.get(board_date))
        all_rows.extend(rows)
        all_audit.extend(audit)

    pd.DataFrame(all_rows).to_csv(OUT, index=False)
    pd.DataFrame(all_audit).to_csv(AUDIT, index=False)

    print(f"Wrote {OUT}: {len(all_rows)} rows")
    print(f"Wrote {AUDIT}: {len(all_audit)} rows")

    if all_audit:
        print(pd.DataFrame(all_audit)["status"].value_counts())


if __name__ == "__main__":
    main()
