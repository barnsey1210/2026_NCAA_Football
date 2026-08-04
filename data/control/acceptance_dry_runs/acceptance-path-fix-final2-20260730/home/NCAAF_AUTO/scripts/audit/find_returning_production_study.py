#!/usr/bin/env python3
from pathlib import Path
import csv
import json
import re

ROOT = Path.home() / "NCAAF_AUTO"
EXPECTED_SIGNALS = ROOT / "data/signals/returning_production_early_season_signals.csv"
EXPECTED_BADGES = ROOT / "data/site/rp_support_badges.json"
ANGLE_OUT = ROOT / "data/signals/game_betting_angles_2026.csv"

SKIP_PARTS = {
    ".git", "build", "backups", "__pycache__", "node_modules",
    "NCAAF_SITE",
}
NAME_RE = re.compile(
    r"(returning.?production|early.?season|rp.?signal|rp.?study|continuity)",
    re.I,
)

def skipped(path):
    return any(part in SKIP_PARTS for part in path.parts)

def csv_info(path):
    try:
        with path.open(newline="", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            rows = []
            for _, row in zip(range(3), reader):
                rows.append(row)
        return header, rows
    except Exception:
        return [], []

def json_info(path):
    try:
        data = json.loads(path.read_text(errors="ignore"))
        if isinstance(data, list):
            sample = data[:2]
            keys = sorted({k for row in sample if isinstance(row, dict) for k in row})
            return f"list[{len(data)}]", keys, sample
        if isinstance(data, dict):
            return f"dict[{len(data)}]", list(data)[:20], []
    except Exception:
        pass
    return "unreadable", [], []

print("RETURNING PRODUCTION STUDY LOCATOR")
print("root:", ROOT)

candidates = []
for path in ROOT.rglob("*"):
    if not path.is_file() or skipped(path):
        continue
    relative = path.relative_to(ROOT)
    if NAME_RE.search(str(relative)):
        candidates.append(path)
        continue
    if path.suffix.lower() in {".csv", ".json", ".md", ".txt", ".py"}:
        try:
            head = path.read_text(errors="ignore")[:12000]
        except Exception:
            continue
        if re.search(
            r"returning production|rp_support|early.?season.*ats|"
            r"high.*rp.*low.*rp|off_vs_def_gap",
            head,
            re.I,
        ):
            candidates.append(path)

seen = set()
unique = []
for path in candidates:
    key = str(path.resolve())
    if key not in seen:
        seen.add(key)
        unique.append(path)

for path in sorted(unique):
    rel = path.relative_to(ROOT)
    print(f"\nCANDIDATE: {rel}")
    print("bytes:", path.stat().st_size)
    if path.suffix.lower() == ".csv":
        header, rows = csv_info(path)
        print("columns:", header)
        for row in rows:
            print("sample:", row[:12])
    elif path.suffix.lower() == ".json":
        kind, keys, sample = json_info(path)
        print("json:", kind)
        print("keys:", keys)
        if sample:
            print("sample:", sample)
    else:
        try:
            hits = [
                line.strip()
                for line in path.read_text(errors="ignore").splitlines()
                if re.search(r"returning production|rp_support|early.?season", line, re.I)
            ][:8]
            for hit in hits:
                print("hit:", hit[:240])
        except Exception:
            pass

print("\nEXPECTED INTEGRATION FILES")
for path in (EXPECTED_SIGNALS, EXPECTED_BADGES):
    print(path.relative_to(ROOT), "exists=" + str(path.exists()),
          "bytes=" + str(path.stat().st_size if path.exists() else 0))

if EXPECTED_SIGNALS.exists():
    header, rows = csv_info(EXPECTED_SIGNALS)
    print("signal columns:", header)
    print("signal sample rows:", len(rows))

if EXPECTED_BADGES.exists():
    kind, keys, sample = json_info(EXPECTED_BADGES)
    print("badge json:", kind, "keys:", keys)

print("\nCURRENT ANGLE OUTPUT")
print(ANGLE_OUT.relative_to(ROOT), "exists=" + str(ANGLE_OUT.exists()))
if ANGLE_OUT.exists():
    header, _ = csv_info(ANGLE_OUT)
    print("angle columns:", header)
    try:
        with ANGLE_OUT.open(newline="", errors="ignore") as f:
            rows = list(csv.DictReader(f))
        rp = [
            row for row in rows
            if row.get("angle_key") == "rp_support"
            or "returning production" in str(row.get("angle_label", "")).lower()
        ]
        print("rp_support rows:", len(rp))
        for row in rp[:10]:
            print(
                row.get("game_id"),
                row.get("week"),
                row.get("side_team"),
                row.get("reason"),
            )
    except Exception as exc:
        print("angle read error:", exc)

print("\nCONSUMER CHECK")
builder_candidates = [
    ROOT / "scripts/signals/build_game_betting_angles_2026.py",
    ROOT / "build_game_betting_angles_2026.py",
]
for path in builder_candidates:
    if path.exists():
        txt = path.read_text(errors="ignore")
        print(path.relative_to(ROOT))
        print("  expects returning_production_early_season_signals.csv:",
              "returning_production_early_season_signals.csv" in txt)
        print("  expects rp_support_badges.json:", "rp_support_badges.json" in txt)
        print("  emits rp_support:", '"rp_support"' in txt or "'rp_support'" in txt)
