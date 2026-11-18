#!/usr/bin/env python3
"""Refresh the accepted CFP committee ranking snapshot from CFBD.

The public JSON is replaced only after a complete 25-team committee poll is
validated.  A transient provider failure preserves the last accepted file.
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "data/site/cfp_committee_rankings_2026.json"
HISTORY = ROOT / "data/models/cfp_rankings_official_2026.csv"
URL = "https://api.collegefootballdata.com/rankings"
POLL = "Playoff Committee Rankings"
ALIASES = {"Miami": "Miami-FL"}
G6 = {"American Athletic", "Conference USA", "Mid-American", "Mountain West", "Pac-12", "Sun Belt"}


def canonical(team: str) -> str:
    return ALIASES.get(team, team)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        tmp = Path(handle.name)
    tmp.replace(path)


def fetch() -> list[dict]:
    key = os.environ.get("CFBD_API_KEY", "").strip()
    if not key:
        raise RuntimeError("CFBD_API_KEY is unavailable")
    query = urllib.parse.urlencode({"year": 2026, "seasonType": "regular"})
    req = urllib.request.Request(f"{URL}?{query}", headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def select_latest(payload: list[dict]) -> tuple[int, list[dict]]:
    candidates = []
    for week in payload:
        poll = next((p for p in week.get("polls", []) if p.get("poll") == POLL), None)
        if poll:
            candidates.append((int(week.get("week", 0)), poll.get("ranks", [])))
    if not candidates:
        raise ValueError("CFBD returned no CFP committee poll")
    week, ranks = max(candidates, key=lambda item: item[0])
    clean = sorted(ranks, key=lambda row: int(row.get("rank", 999)))
    if len(clean) < 25 or [int(row.get("rank", 0)) for row in clean[:25]] != list(range(1, 26)):
        raise ValueError("CFP committee poll failed complete Top 25 validation")
    return week, clean[:25]


def build(week: int, ranks: list[dict]) -> dict:
    rows = [
        {
            "rank": int(row["rank"]),
            "team": canonical(str(row["school"])),
            "conference": str(row.get("conference") or ""),
        }
        for row in ranks
    ]
    non_g6 = [row for row in rows if row["conference"] not in G6][:11]
    g6 = next((row for row in rows if row["conference"] in G6), None)
    if len(non_g6) != 11 or not g6:
        raise ValueError("Unable to derive 11 at-large/power teams plus the highest-ranked G6 team")
    field_rows = non_g6 + [g6]
    field = [{"seed": seed, **row} for seed, row in enumerate(field_rows, 1)]
    field_names = {row["team"] for row in field}
    next_out = [row for row in rows if row["team"] not in field_names][:8]
    now = datetime.now(timezone.utc)
    return {
        "schema_version": "cfp-committee-rankings-v1",
        "season": 2026,
        "week": week,
        "poll": POLL,
        "source": "CollegeFootballData",
        "accepted_at": now.isoformat().replace("+00:00", "Z"),
        "ranking_date": now.astimezone().date().isoformat(),
        "rankings": rows,
        "field": field,
        "next_out": next_out,
        "field_rule": "Top 11 non-G6 teams plus highest-ranked G6 team; G6 seeded 12th",
    }


def update_history(snapshot: dict) -> None:
    existing = []
    if HISTORY.exists():
        existing = list(csv.DictReader(HISTORY.open(encoding="utf-8")))
    week = str(snapshot["week"])
    existing = [row for row in existing if not (row.get("season") == "2026" and row.get("week") == week)]
    for row in snapshot["rankings"]:
        existing.append({
            "season": 2026,
            "week": snapshot["week"],
            "ranking_date": snapshot["ranking_date"],
            "poll": snapshot["poll"],
            "rank": row["rank"],
            "team": row["team"],
            "conference": row["conference"],
        })
    columns = ["season", "week", "ranking_date", "poll", "rank", "team", "conference"]
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=HISTORY.parent, delete=False) as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(existing, key=lambda x: (int(x["season"]), int(x["week"]), int(x["rank"]))))
        tmp = Path(handle.name)
    tmp.replace(HISTORY)


def main() -> int:
    try:
        week, ranks = select_latest(fetch())
        snapshot = build(week, ranks)
        atomic_text(PUBLIC, json.dumps(snapshot, indent=2) + "\n")
        update_history(snapshot)
        print(f"Accepted CFP committee rankings: 2026 week {week}, {len(snapshot['rankings'])} teams")
        return 0
    except Exception as exc:
        if PUBLIC.exists():
            print(f"WARNING: preserving accepted CFP committee snapshot: {exc}")
            return 0
        raise


if __name__ == "__main__":
    raise SystemExit(main())
