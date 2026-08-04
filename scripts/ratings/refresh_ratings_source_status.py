#!/usr/bin/env python3
from __future__ import annotations
import csv, os, tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LATEST = ROOT / "data/ratings/ratings_latest.csv"
STATUS = ROOT / "data/ratings/ratings_source_status.csv"


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def atomic_write(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp, path)
    except Exception:
        try: os.unlink(temp)
        except FileNotFoundError: pass
        raise


def main() -> None:
    latest = read_rows(LATEST)
    previous = {row.get("source", ""): row for row in read_rows(STATUS)}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in latest:
        grouped[row.get("source", "")].append(row)
    fields = list(next(iter(previous.values())).keys()) if previous else []
    for required in ("source", "teams", "rows", "snapshot_date", "pulled_at", "source_updated_at", "status_built_at"):
        if required not in fields:
            fields.append(required)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    output = []
    for source in sorted(set(previous) | set(grouped)):
        rows = grouped.get(source, [])
        row = dict(previous.get(source, {}))
        row["source"] = source
        if rows:
            row["teams"] = len({x.get("team") for x in rows if x.get("team")})
            row["rows"] = len(rows)
            snapshots = [x.get("snapshot_date") for x in rows if x.get("snapshot_date")]
            pulls = [x.get("pulled_at") for x in rows if x.get("pulled_at")]
            updates = [x.get("source_updated_at") for x in rows if x.get("source_updated_at")]
            if snapshots: row["snapshot_date"] = max(snapshots)
            if pulls: row["pulled_at"] = max(pulls)
            if updates: row["source_updated_at"] = max(updates)
            if "latest_pull_at" in fields and pulls: row["latest_pull_at"] = max(pulls)
        row["status_built_at"] = now
        output.append({field: row.get(field, "") for field in fields})
    atomic_write(STATUS, output, fields)
    print(f"wrote: {STATUS}")
    print(f"sources: {len(output)}")


if __name__ == "__main__":
    main()
