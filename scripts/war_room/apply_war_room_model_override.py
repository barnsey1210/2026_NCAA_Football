#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

OUT=ROOT / "data/control/war_room_model_override.json"

SPREAD_ALLOWED={
    "SP+",
    "FPI",
    "TeamRankings",
    "DRatings",
}

TOTAL_ALLOWED={
    "SP+",
    "Massey Dual",
    "DRatings Total",
}


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(
        json.dumps(value, indent=2, sort_keys=True)+"\n"
    )
    tmp.replace(path)


def parse_sources(value):
    if not value:
        return []
    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


parser=argparse.ArgumentParser()
parser.add_argument(
    "--mode",
    required=True,
    choices=["AUTO","MANUAL"],
)
parser.add_argument("--spread-sources", default="")
parser.add_argument("--total-sources", default="")
parser.add_argument("--requester", default="operator")
parser.add_argument("--task-id", default="")
args=parser.parse_args()

spread=parse_sources(args.spread_sources)
total=parse_sources(args.total_sources)

unknown_spread=[
    source for source in spread
    if source not in SPREAD_ALLOWED
]

unknown_total=[
    source for source in total
    if source not in TOTAL_ALLOWED
]

if unknown_spread or unknown_total:
    raise SystemExit(
        "invalid manual source selection: "
        f"spread={unknown_spread} total={unknown_total}"
    )

if args.mode=="MANUAL" and not spread and not total:
    raise SystemExit(
        "MANUAL requires at least one selected source"
    )

payload={
    "schema_version":
        "war-room-model-override-v1",
    "mode": args.mode,
    "spread_sources": spread,
    "total_sources": total,
    "updated_at":
        datetime.now(timezone.utc).isoformat(),
    "updated_by": args.requester[:120],
}

atomic_json(OUT,payload)

task_path = (
    ROOT
    / "data/control/war_room_services/tasks"
    / f"{args.task_id}.json"
    if args.task_id
    else None
)

latest_path = (
    ROOT
    / "data/control/war_room_services/latest.json"
)

try:
    for command in [
        [
            sys.executable,
            "scripts/war_room/build_war_room_market_matrix.py",
        ],
    ]:
        subprocess.run(
            command,
            cwd=ROOT,
            check=True,
        )
except Exception as exc:
    if task_path and task_path.exists():
        try:
            task = json.loads(task_path.read_text())
        except Exception:
            task = {}

        task["status"] = "FAILED"
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        task["error"] = str(exc)
        atomic_json(task_path, task)
        atomic_json(latest_path, task)

    raise

if task_path and task_path.exists():
    try:
        task = json.loads(task_path.read_text())
    except Exception:
        task = {}

    task["status"] = "COMPLETED"
    task["completed_at"] = datetime.now(timezone.utc).isoformat()
    atomic_json(task_path, task)
    atomic_json(latest_path, task)

print(json.dumps(payload, indent=2))
