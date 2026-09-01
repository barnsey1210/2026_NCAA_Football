#!/usr/bin/env python3
"""Small append-only primitives for prospective model tracking v2."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

def stable_id(dataset: str, *parts: object) -> str:
    raw="|".join([dataset, *["" if p is None else str(p) for p in parts]])
    return hashlib.sha256(raw.encode()).hexdigest()

def read_ids(path: Path, id_field: str) -> set[str]:
    if not path.exists(): return set()
    return {json.loads(line)[id_field] for line in path.read_text().splitlines() if line.strip()}

def append_unique(path: Path, rows: list[dict], id_field: str, accept: bool=False) -> dict:
    existing=read_ids(path,id_field); new=[r for r in rows if r[id_field] not in existing]
    if accept and new:
        with path.open("a",encoding="utf-8") as fh:
            for row in new: fh.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
    return {"path":str(path),"candidates":len(rows),"already_present":len(rows)-len(new),"would_append":len(new),"accepted":len(new) if accept else 0}
