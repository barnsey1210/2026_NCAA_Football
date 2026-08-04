#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path.home() / "NCAAF_AUTO"
INDEX = ROOT / "index.html"
OUT = ROOT / "data/audit/sgo_market_source_discovery.json"

MARKET_KEYS = {
    "spread": [
        "market_spread", "sgo_game_spread", "sgo_spread", "spread",
        "current_spread", "consensus_spread", "best_spread",
    ],
    "total": [
        "market_total", "sgo_game_total", "sgo_total", "total",
        "current_total", "consensus_total", "best_total",
    ],
    "game_id": ["game_id", "id", "event_id", "sgo_game_id"],
    "home": ["home_team", "home", "home_name"],
    "away": ["away_team", "away", "away_name"],
}

def nonempty(v):
    return v is not None and v != ""

def inspect_list(name, rows):
    if not rows or not isinstance(rows[0], dict):
        return None

    keys = Counter()
    counts = Counter()
    examples = {}

    for row in rows:
        for key in row:
            keys[key] += 1
        for group, candidates in MARKET_KEYS.items():
            for key in candidates:
                if key in row and nonempty(row.get(key)):
                    counts[f"{group}:{key}"] += 1
                    examples.setdefault(f"{group}:{key}", row.get(key))

    total_hits = sum(
        counts[f"total:{key}"] for key in MARKET_KEYS["total"]
    )
    spread_hits = sum(
        counts[f"spread:{key}"] for key in MARKET_KEYS["spread"]
    )

    if total_hits == 0 and spread_hits == 0:
        return None

    return {
        "path": name,
        "rows": len(rows),
        "market_counts": dict(counts),
        "common_keys": keys.most_common(40),
        "examples": examples,
    }

def walk(value, path="DB"):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(child, list):
                result = inspect_list(child_path, child)
                if result:
                    found.append(result)
            found.extend(walk(child, child_path))
    elif isinstance(value, list):
        for i, child in enumerate(value[:5]):
            if isinstance(child, (dict, list)):
                found.extend(walk(child, f"{path}[{i}]"))
    return found

def main():
    html = INDEX.read_text(encoding="utf-8", errors="ignore")
    match = re.search(
        r'<script id="db" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    if not match:
        raise SystemExit("Could not locate embedded DB.")

    db = json.loads(match.group(1))
    found = walk(db)
    found.sort(
        key=lambda r: (
            -sum(
                v for k, v in r["market_counts"].items()
                if k.startswith("total:")
            ),
            -sum(
                v for k, v in r["market_counts"].items()
                if k.startswith("spread:")
            ),
        )
    )

    payload = {
        "schema_version": "sgo-market-source-discovery-v1",
        "sources": found,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print("SGO/market source discovery")
    print("candidate arrays:", len(found))
    for src in found[:15]:
        total = sum(
            v for k, v in src["market_counts"].items()
            if k.startswith("total:")
        )
        spread = sum(
            v for k, v in src["market_counts"].items()
            if k.startswith("spread:")
        )
        print()
        print(src["path"])
        print("rows:", src["rows"])
        print("total field hits:", total)
        print("spread field hits:", spread)
        print("fields:", src["market_counts"])
    print()
    print("wrote:", OUT)

if __name__ == "__main__":
    main()
