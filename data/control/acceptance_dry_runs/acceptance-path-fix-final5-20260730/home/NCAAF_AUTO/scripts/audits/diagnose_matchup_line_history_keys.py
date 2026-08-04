#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys
import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
CLEAN = ROOT / "data/history/matchup_line_history_clean.csv"
ASSET = ROOT / "data/site/matchup_line_history.json"
VIEW = ROOT / "data/site/matchups_view.json"
BUILDER = ROOT / "scripts/site/build_matchups_view.py"
INJECTOR = ROOT / "scripts/site/inject_matchup_line_history.py"
OUT = ROOT / "data/audits/matchup_line_history_key_diagnostic.txt"

def summarize_csv():
    lines = ["CLEAN CSV", "-" * 100]
    if not CLEAN.exists():
        return lines + [f"Missing: {CLEAN}"]
    df = pd.read_csv(CLEAN, low_memory=False)
    lines += [
        f"Path: {CLEAN}",
        f"Rows: {len(df)}",
        f"Columns: {' | '.join(map(str, df.columns))}",
    ]
    if "game_id" in df.columns:
        lines.append(f"Unique game_id: {df['game_id'].nunique(dropna=True)}")
    mask = df.astype(str).apply(
        lambda row: (
            row.str.contains("East Carolina", case=False, regex=False).any()
            and row.str.contains("Alabama", case=False, regex=False).any()
        ),
        axis=1,
    )
    target = df[mask]
    lines.append(f"East Carolina/Alabama rows: {len(target)}")
    if not target.empty:
        lines.append(target.head(10).to_string(index=False))
    return lines

def summarize_asset():
    lines = ["LINE-HISTORY ASSET", "-" * 100]
    keys = set()
    if not ASSET.exists():
        return lines + [f"Missing: {ASSET}"], keys
    raw = json.loads(ASSET.read_text(encoding="utf-8"))
    lines += [f"Path: {ASSET}", f"Top-level type: {type(raw).__name__}"]
    if isinstance(raw, dict):
        keys = {str(k) for k in raw}
        lines += [
            f"Top-level keys: {len(keys)}",
            f"Sample keys: {sorted(keys)[:20]}",
            f"Contains g24: {'g24' in keys}",
        ]
        target_keys = []
        for key, value in raw.items():
            text = json.dumps(value, default=str)
            if "East Carolina" in text and "Alabama" in text:
                target_keys.append(str(key))
        lines.append(f"East Carolina/Alabama asset keys: {target_keys[:20]}")
        if "g24" in raw:
            value = raw["g24"]
            lines += [f"g24 type: {type(value).__name__}", json.dumps(value, indent=2)[:5000]]
    else:
        lines.append("Asset is not a dict keyed by game_id.")
    return lines, keys

def summarize_view():
    lines = ["MATCHUPS VIEW", "-" * 100]
    ids = set()
    if not VIEW.exists():
        return lines + [f"Missing: {VIEW}"], ids
    raw = json.loads(VIEW.read_text(encoding="utf-8"))
    games = raw.get("games", []) if isinstance(raw, dict) else []
    lines.append(f"Games: {len(games)}")
    target = None
    for record in games:
        if not isinstance(record, dict):
            continue
        game = record.get("game", {})
        game_id = game.get("game_id")
        if game_id:
            ids.add(str(game_id))
        if (
            str(game.get("away_team", "")).casefold() == "east carolina"
            and str(game.get("home_team", "")).casefold() == "alabama"
        ):
            target = record
    lines += [f"Unique game_ids: {len(ids)}", f"Contains g24: {'g24' in ids}"]
    if target:
        lines.append(json.dumps(target, indent=2)[:12000])
    else:
        lines.append("East Carolina at Alabama not found.")
    return lines, ids

def source_snippets():
    lines = ["SOURCE EXPECTATIONS", "-" * 100]
    for path in [INJECTOR, BUILDER]:
        lines.append(f"\n{path}")
        if not path.exists():
            lines.append("Missing")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in [
            "matchup_line_history.json",
            "line_history.get",
            '"line_history"',
            "game_id",
            "OUT.write_text",
            "json.dumps",
        ]:
            matches = [
                (i, line.strip())
                for i, line in enumerate(text.splitlines(), start=1)
                if pattern in line
            ]
            if matches:
                lines.append(f"Pattern: {pattern}")
                for number, line in matches[:15]:
                    lines.append(f"  {number}: {line}")
    return lines

def main():
    report = ["MATCHUP LINE-HISTORY KEY DIAGNOSTIC", "=" * 100]
    report.extend(summarize_csv())
    report.append("")
    asset_lines, asset_keys = summarize_asset()
    report.extend(asset_lines)
    report.append("")
    view_lines, view_ids = summarize_view()
    report.extend(view_lines)
    report.append("")
    report += [
        "KEY OVERLAP",
        "-" * 100,
        f"Asset keys: {len(asset_keys)}",
        f"View game_ids: {len(view_ids)}",
        f"Overlap: {len(asset_keys & view_ids)}",
        f"Asset-only sample: {sorted(asset_keys - view_ids)[:30]}",
        f"View-only sample: {sorted(view_ids - asset_keys)[:30]}",
        "",
    ]
    report.extend(source_snippets())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("MATCHUP LINE-HISTORY KEY DIAGNOSTIC")
    print("=" * 100)
    print(f"Wrote: {OUT}")
    print(f"Asset keys: {len(asset_keys)}")
    print(f"View game_ids: {len(view_ids)}")
    print(f"Key overlap: {len(asset_keys & view_ids)}")
    print(f"Run: cat {OUT}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
