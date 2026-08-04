#!/usr/bin/env python3
"""Audit why no 2026 games matched the estimated 1H RP candidate scan.

Read-only. Does not modify project files.

Checks:
- 2026 Weeks 1-4 games found in embedded DB
- Returning-production coverage for both teams
- Which model-spread fields are actually present
- Counts of games meeting RP-only candidate conditions before market role
- Counts after applying estimated 1H role
"""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import unicodedata
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd


BASE = Path("/Users/jameslindesmith/NCAAF_AUTO")
INDEX_HTML = BASE / "index.html"

OUT_ROWS = BASE / "data/audits/rp_1h_2026_no_match_diagnostic_rows.csv"
OUT_SUMMARY = BASE / "data/audits/rp_1h_2026_no_match_diagnostic_summary.csv"


ALIASES = {
    "texas a m": "texas a&m",
    "app st": "appalachian state",
    "app state": "appalachian state",
    "wku": "western kentucky",
    "va tech": "virginia tech",
    "fau": "florida atlantic",
    "fiu": "florida international",
    "so miss": "southern miss",
    "miss st": "mississippi state",
    "nc st": "nc state",
    "ohio st": "ohio state",
    "wash st": "washington state",
}


def normalize_team(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return ALIASES.get(text, text)


def numeric(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        n = float(value)
        return n if np.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def js_object(text: str, const_name: str) -> Any:
    m = re.search(rf"const\s+{re.escape(const_name)}\s*=\s*", text)
    if not m:
        raise KeyError(f"Missing JS constant: {const_name}")

    start = m.end()
    while start < len(text) and text[start].isspace():
        start += 1

    opener = text[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_string = False
    quote = ""
    escaped = False

    for i in range(start, len(text)):
        ch = text[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                in_string = False
            continue

        if ch in {"'", '"', "`"}:
            in_string = True
            quote = ch
            continue

        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])

    raise ValueError(f"Could not parse {const_name}")


def embedded_db(text: str) -> dict[str, Any]:
    m = re.search(
        r'<script[^>]+id=["\']db["\'][^>]*>(.*?)</script>',
        text,
        re.S | re.I,
    )
    if not m:
        raise KeyError("Missing embedded DB")
    return json.loads(m.group(1))


def rp_values(row: dict[str, Any]) -> tuple[float | None, float | None, float | None]:
    def first(keys):
        for key in keys:
            if key in row:
                n = numeric(row.get(key))
                if n is not None:
                    return n
        return None

    return (
        first(["overall", "overall_pct", "overall_rp"]),
        first(["offense", "offense_pct", "off_rp"]),
        first(["defense", "defense_pct", "def_rp"]),
    )


def collect_numeric_fields(obj: Any, prefix: str = "") -> dict[str, float]:
    out: dict[str, float] = {}

    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            n = numeric(value)
            if n is not None:
                out[path] = n
            elif isinstance(value, dict):
                out.update(collect_numeric_fields(value, path))

    return out


def likely_spread_fields(fields: dict[str, float]) -> dict[str, float]:
    return {
        key: value
        for key, value in fields.items()
        if "spread" in key.lower()
        or "margin" in key.lower()
        or "projection" in key.lower()
    }


def main() -> None:
    text = INDEX_HTML.read_text(encoding="utf-8", errors="ignore")
    db = embedded_db(text)
    rp_raw = js_object(text, "RETURNING_PRODUCTION_2026")

    rp_lookup = {}
    for team, row in rp_raw.items():
        if isinstance(row, dict):
            rp_lookup[normalize_team(team)] = row

    games = db.get("games", [])
    rows = []
    spread_field_counter = Counter()

    for game in games:
        week = numeric(game.get("week"))
        if week is None or not (1 <= week <= 4):
            continue

        away = str(game.get("away_team", "")).strip()
        home = str(game.get("home_team", "")).strip()

        away_rp = rp_lookup.get(normalize_team(away))
        home_rp = rp_lookup.get(normalize_team(home))

        all_fields = collect_numeric_fields(game)
        spread_fields = likely_spread_fields(all_fields)
        spread_field_counter.update(spread_fields.keys())

        row = {
            "game_id": game.get("game_id"),
            "week": week,
            "date": game.get("date"),
            "away_team": away,
            "home_team": home,
            "away_rp_found": away_rp is not None,
            "home_rp_found": home_rp is not None,
            "spread_like_field_count": len(spread_fields),
            "spread_like_fields": json.dumps(spread_fields, sort_keys=True),
        }

        if away_rp and home_rp:
            ao, aoff, adef = rp_values(away_rp)
            ho, hoff, hdef = rp_values(home_rp)

            row.update(
                {
                    "away_overall": ao,
                    "away_offense": aoff,
                    "away_defense": adef,
                    "home_overall": ho,
                    "home_offense": hoff,
                    "home_defense": hdef,
                    "away_off_vs_def": None if aoff is None or hdef is None else aoff - hdef,
                    "away_def_vs_off": None if adef is None or hoff is None else adef - hoff,
                    "home_off_vs_def": None if hoff is None or adef is None else hoff - adef,
                    "home_def_vs_off": None if hdef is None or aoff is None else hdef - aoff,
                }
            )

            row["away_candidate_a_rp_only"] = (
                row["away_def_vs_off"] is not None
                and row["away_def_vs_off"] >= 25
            )
            row["home_candidate_a_rp_only"] = (
                row["home_def_vs_off"] is not None
                and row["home_def_vs_off"] >= 25
            )
            row["away_candidate_b_rp_only"] = (
                row["away_off_vs_def"] is not None
                and row["away_off_vs_def"] > 0
                and row["away_def_vs_off"] is not None
                and row["away_def_vs_off"] < 0
            )
            row["home_candidate_b_rp_only"] = (
                row["home_off_vs_def"] is not None
                and row["home_off_vs_def"] > 0
                and row["home_def_vs_off"] is not None
                and row["home_def_vs_off"] < 0
            )

        rows.append(row)

    frame = pd.DataFrame(rows)
    OUT_ROWS.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_ROWS, index=False)

    summary_rows = [
        {"metric": "weeks_1_4_games", "value": len(frame)},
        {
            "metric": "games_with_both_rp",
            "value": int((frame["away_rp_found"] & frame["home_rp_found"]).sum()),
        },
        {
            "metric": "games_with_any_spread_like_field",
            "value": int((frame["spread_like_field_count"] > 0).sum()),
        },
        {
            "metric": "candidate_a_rp_only_team_sides",
            "value": int(
                frame.get("away_candidate_a_rp_only", pd.Series(dtype=bool)).fillna(False).sum()
                + frame.get("home_candidate_a_rp_only", pd.Series(dtype=bool)).fillna(False).sum()
            ),
        },
        {
            "metric": "candidate_b_rp_only_team_sides",
            "value": int(
                frame.get("away_candidate_b_rp_only", pd.Series(dtype=bool)).fillna(False).sum()
                + frame.get("home_candidate_b_rp_only", pd.Series(dtype=bool)).fillna(False).sum()
            ),
        },
    ]

    for field, count in spread_field_counter.most_common(30):
        summary_rows.append(
            {"metric": f"spread_field::{field}", "value": count}
        )

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_SUMMARY, index=False)

    print("2026 RP / MODEL SPREAD DIAGNOSTIC")
    print("=" * 100)
    print(summary.to_string(index=False))

    print()
    print("RP-ONLY CANDIDATE GAMES")
    print("=" * 100)

    candidate_mask = pd.Series(False, index=frame.index)
    for col in [
        "away_candidate_a_rp_only",
        "home_candidate_a_rp_only",
        "away_candidate_b_rp_only",
        "home_candidate_b_rp_only",
    ]:
        if col in frame.columns:
            candidate_mask |= frame[col].fillna(False)

    cols = [
        "week",
        "date",
        "away_team",
        "home_team",
        "away_candidate_a_rp_only",
        "home_candidate_a_rp_only",
        "away_candidate_b_rp_only",
        "home_candidate_b_rp_only",
        "spread_like_fields",
    ]
    cols = [c for c in cols if c in frame.columns]

    print(frame.loc[candidate_mask, cols].to_string(index=False))

    print()
    print("Created:")
    print(OUT_ROWS)
    print(OUT_SUMMARY)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
