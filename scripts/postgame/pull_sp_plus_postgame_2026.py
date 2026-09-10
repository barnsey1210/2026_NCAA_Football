#!/usr/bin/env python3
"""Acquire and normalize the public SP+ 2026 postgame performance table."""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE_WORKBOOK = "https://docs.google.com/spreadsheets/d/1vwoVl-Dxy0es87Z9I1RTvFzr72Lb1fAkREfbLxbK-eg/edit"
SOURCE_EXPORT = "https://docs.google.com/spreadsheets/d/1vwoVl-Dxy0es87Z9I1RTvFzr72Lb1fAkREfbLxbK-eg/gviz/tq?tqx=out:csv&sheet=POSTGAME%20WIN%20EXPECTANCY"
DEFAULT_OUTPUT = Path("data/canonical/sp_plus_postgame_2026.json")


def number(value):
    try:
        parsed = float(str(value).strip().rstrip("%"))
        return parsed if math.isfinite(parsed) else None
    except (TypeError, ValueError):
        return None


def normalize_csv(text, collected_at):
    rows = []
    for raw in csv.DictReader(io.StringIO(text)):
        if not raw.get("date") or not raw.get("team") or not raw.get("opponent"):
            continue
        pgwe = number(raw.get("PGWE"))
        if pgwe is not None and str(raw.get("PGWE", "")).strip().endswith("%"):
            pgwe /= 100.0
        row = {
            "date": datetime.strptime(raw["date"].strip(), "%m/%d/%y").date().isoformat(),
            "team": raw["team"].strip(), "opponent": raw["opponent"].strip(),
            "win": int(number(raw.get("win"))), "pts": int(number(raw.get("pts"))),
            "opp_pts": int(number(raw.get("opp pts"))), "actual_margin": number(raw.get("margin")),
            "sp_plus_pgwe": pgwe, "sp_plus_adjusted_margin": number(raw.get("adj mgn")),
            "source": "SP+ POSTGAME WIN EXPECTANCY public sheet",
            "source_url": SOURCE_WORKBOOK, "collected_at": collected_at,
        }
        required = (row["actual_margin"], row["sp_plus_pgwe"], row["sp_plus_adjusted_margin"])
        if any(value is None for value in required) or not 0 <= row["sp_plus_pgwe"] <= 1:
            raise ValueError(f"invalid SP+ postgame row: {raw}")
        rows.append(row)
    if not rows:
        raise ValueError("SP+ postgame export contained no usable rows")
    return rows


def atomic_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, allow_nan=False); handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-url", default=SOURCE_EXPORT)
    parser.add_argument("--input-csv", help="read a previously acquired export instead of making a request")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    collected_at = datetime.now(timezone.utc).isoformat()
    if args.input_csv:
        text = Path(args.input_csv).read_text(encoding="utf-8-sig")
    else:
        request = urllib.request.Request(args.source_url, headers={"User-Agent": "NCAAF-War-Room/1.0"})
        with urllib.request.urlopen(request, timeout=45) as response:
            text = response.read().decode("utf-8-sig")
    rows = normalize_csv(text, collected_at)
    payload = {"schema_version": "sp-plus-postgame-2026-v1", "season": 2026,
               "source": "SP+ POSTGAME WIN EXPECTANCY public sheet", "source_url": SOURCE_WORKBOOK,
               "source_export_url": args.source_url, "collected_at": collected_at,
               "rows": rows, "summary": {"team_rows": len(rows)}}
    atomic_json(Path(args.output), payload)
    print(json.dumps({"output": args.output, "team_rows": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
