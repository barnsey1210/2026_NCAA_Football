#!/usr/bin/env python3
from pathlib import Path
import re
import json
import csv

ROOT = Path.home() / "NCAAF_AUTO"

TOKENS = [
    "postgame_shadow_updates",
    "completed_team_updates",
    "Saturday shadow",
    "awaiting_live_results",
    "score/ATS model",
    "current-season PBP",
    "shadow only",
    "postgame_spread_repricing",
    "postgame_total_repricing",
]

SKIP = {".git", "build", "backups", "__pycache__", "node_modules"}

def skipped(path):
    return any(part in SKIP for part in path.parts)

def summarize_csv(path):
    try:
        with path.open(newline="", errors="ignore") as f:
            r = csv.reader(f)
            header = next(r, [])
            rows = [row for _, row in zip(range(3), r)]
        return header, rows
    except Exception:
        return [], []

def summarize_json(path):
    try:
        data = json.loads(path.read_text(errors="ignore"))
        if isinstance(data, dict):
            return f"dict[{len(data)}]", list(data)[:30]
        if isinstance(data, list):
            keys = sorted({k for row in data[:10] if isinstance(row, dict) for k in row})
            return f"list[{len(data)}]", keys
    except Exception:
        pass
    return "unreadable", []

print("SATURDAY SHADOW PIPELINE AUDIT")
print("root:", ROOT)

hits = []
for path in ROOT.rglob("*"):
    if not path.is_file() or skipped(path):
        continue
    if path.suffix.lower() not in {".py", ".sh", ".json", ".csv", ".html", ".md", ".txt"}:
        continue
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        continue
    matched = [token for token in TOKENS if token.lower() in text.lower()]
    if matched:
        hits.append((path, matched))

for path, matched in sorted(hits):
    print("\nFILE:", path.relative_to(ROOT))
    print("matches:", ", ".join(matched))
    print("bytes:", path.stat().st_size)
    if path.suffix.lower() == ".csv":
        header, rows = summarize_csv(path)
        print("columns:", header)
        for row in rows:
            print("sample:", row[:16])
    elif path.suffix.lower() == ".json":
        kind, keys = summarize_json(path)
        print("json:", kind)
        print("keys:", keys)
    else:
        lines = path.read_text(errors="ignore").splitlines()
        for i, line in enumerate(lines, 1):
            if any(token.lower() in line.lower() for token in TOKENS):
                print(f"{i}: {line[:260]}")

artifact = ROOT / "data/site/postgame_shadow_updates.json"
print("\nCURRENT SHADOW ARTIFACT")
print("exists:", artifact.exists())
if artifact.exists():
    try:
        data = json.loads(artifact.read_text())
        print(json.dumps(data, indent=2)[:12000])
    except Exception as exc:
        print("read error:", exc)

print("\nLIKELY INPUT INVENTORY")
for pattern in (
    "data/**/*pbp*.csv",
    "data/**/*play*by*play*.csv",
    "data/**/*game*metric*.csv",
    "data/**/*postgame*.csv",
    "data/**/*shadow*.json",
    "scripts/**/*postgame*.py",
    "scripts/**/*pbp*.py",
    "scripts/**/*shadow*.py",
):
    for path in sorted(ROOT.glob(pattern)):
        if path.is_file() and not skipped(path):
            print(path.relative_to(ROOT), path.stat().st_size)

print("\nNEXT CHECKS")
print("1. Identify the builder that writes data/site/postgame_shadow_updates.json.")
print("2. Identify spread-model and total-model input schemas.")
print("3. Confirm whether team estimates and game-level Week+1 projections are already emitted.")
print("4. Confirm that shadow outputs never overwrite official ratings/projections.")
