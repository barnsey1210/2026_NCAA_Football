#!/usr/bin/env python3
"""Recover dated 2025 weekly SP+ tables from ESPN Wayback snapshots."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import io
import gzip
import json
import re
import urllib.parse
import urllib.request

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/import/sp_plus/wayback_2025/cdx_snapshots.json"
RAW = ROOT / "data/import/sp_plus/wayback_2025/raw"
OUT = ROOT / "data/import/sp_plus/espn_sp_plus_weekly_2025.csv"

# Tuesday noon UTC is safely after the usual Sunday/Monday rating update.
TARGETS = {
    1: "20250902120000", 2: "20250909120000", 3: "20250916120000",
    4: "20250923120000", 5: "20250930120000", 6: "20251007120000",
    7: "20251014120000", 8: "20251021120000", 9: "20251028120000",
    10: "20251104120000", 11: "20251111120000", 12: "20251118120000",
    13: "20251125120000", 14: "20251202120000", 15: "20251209120000",
}


def dt(value):
    return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)


def select_snapshots(rows):
    stamps = sorted({r[0] for r in rows[1:] if r and r[0].startswith("2025")})
    selected = {}
    for week, target_value in TARGETS.items():
        target = dt(target_value)
        near = [s for s in stamps if target-timedelta(days=1) <= dt(s) <= target+timedelta(days=4)]
        selected[week] = sorted(near or stamps, key=lambda s: (dt(s) < target, abs((dt(s)-target).total_seconds())))
    return selected


def fetch(timestamp, original):
    encoded = original.replace("+", "%2B")
    url = f"https://web.archive.org/web/{timestamp}id_/{encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as response:
        body = response.read()
        if body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        return body, url


def split_metric(value):
    match = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*(?:\((\d+)\))?", str(value))
    return (float(match.group(1)), int(match.group(2)) if match.group(2) else None) if match else (None, None)


def main():
    cdx = json.loads(SRC.read_text())
    selected = select_snapshots(cdx)
    original = cdx[1][1]
    RAW.mkdir(parents=True, exist_ok=True)
    records = []
    manifest = []
    for week, candidates in selected.items():
        last_error = None
        for timestamp in candidates[:40]:
            try:
                body, replay_url = fetch(timestamp, original)
                tables = pd.read_html(io.BytesIO(body))
                rating = next(t for t in tables if {"Team", "Rating", "Offense", "Defense"}.issubset(t.columns))
                if len(rating) != 136:
                    raise ValueError(f"expected 136 rows, got {len(rating)}")
                break
            except Exception as exc:
                last_error = exc
        else:
            raise RuntimeError(f"no valid snapshot for week {week}: {last_error}")
        path = RAW / f"week_{week:02d}_{timestamp}.html"
        path.write_bytes(body)
        for _, row in rating.iterrows():
            team_match = re.match(r"^(\d+)\.\s*(.*?)\s*\(([^)]*)\)$", str(row["Team"]))
            offense, offense_rank = split_metric(row["Offense"])
            defense, defense_rank = split_metric(row["Defense"])
            special, special_rank = split_metric(row.get("Spec Tms"))
            records.append({
                "season": 2025, "snapshot_week": week,
                "team_rank": int(team_match.group(1)) if team_match else None,
                "team": team_match.group(2) if team_match else row["Team"],
                "record": team_match.group(3) if team_match else None,
                "sp_plus": float(row["Rating"]), "offense": offense, "offense_rank": offense_rank,
                "defense": defense, "defense_rank": defense_rank,
                "special_teams": special, "special_teams_rank": special_rank,
                "source_timestamp": timestamp, "source_url": replay_url,
            })
        manifest.append({"snapshot_week": week, "timestamp": timestamp, "rows": len(rating), "file": str(path)})
        print(f"week {week}: {timestamp} rows={len(rating)}")
    pd.DataFrame(records).to_csv(OUT, index=False)
    (OUT.parent / "espn_sp_plus_weekly_2025_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(f"wrote {OUT}: {len(records)} rows")


if __name__ == "__main__":
    main()
