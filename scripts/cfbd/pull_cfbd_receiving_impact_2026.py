#!/usr/bin/env python3
"""Pull and normalize CFBD WR/TE receiving PPA and usage for matchup cards."""
from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/canonical/cfbd_receiving_impact_2026.json"
BASE = "https://api.collegefootballdata.com"


def get(path: str, params: dict, key: str):
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    key = os.environ.get("CFBD_API_KEY", "").strip()
    if not key:
        raise SystemExit("Missing CFBD_API_KEY")

    ppa = []
    usage = []
    for position in ("WR", "TE"):
        ppa.extend(get("/ppa/players/season", {"year": args.year, "position": position, "threshold": 5}, key))
        usage.extend(get("/player/usage", {"year": args.year, "position": position}, key))
    usage_by_id = {str(row["id"]): row.get("usage", {}) for row in usage}
    rows = []
    for row in ppa:
        average = row.get("averagePPA", {}).get("pass")
        total = row.get("totalPPA", {}).get("pass")
        pass_usage = usage_by_id.get(str(row["id"]), {}).get("pass")
        if not all(isinstance(value, (int, float)) for value in (average, total, pass_usage)):
            continue
        # Matchup-card ranks use established rotation receivers, not every player
        # credited with a single target or pass involvement.
        if pass_usage < 0.05:
            continue
        rows.append({
            "year": args.year,
            "athleteId": str(row["id"]),
            "athleteName": row["name"],
            "position": row["position"],
            "team": row["team"],
            "conference": row.get("conference"),
            "usage": pass_usage,
            "averagePPA": average,
            "totalPPA": total,
        })
    rows.sort(key=lambda row: (row["team"], -row["usage"], -row["totalPPA"], row["athleteName"]))
    payload = {
        "schema_version": "cfbd-receiving-impact-v1",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "season": args.year,
        "source": "CFBD /ppa/players/season joined to /player/usage",
        "players": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "players": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
