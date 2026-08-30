#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

CFBD = ROOT / "data/canonical/cfbd_schedule_2026.json"
DB = ROOT / "data/snapshots/preseason/preseason_db.json"

OUT_JSON = ROOT / "data/canonical/game_results_2026.json"
OUT_CSV = ROOT / "data/canonical/game_results_2026.csv"
AUDIT = ROOT / "data/audits/game_results_2026_audit.json"

ALIASES = {
    "ucf": "central florida",
    "uconn": "connecticut",
    "ole miss": "mississippi",
    "app state": "appalachian state",
    "ul monroe": "ul monroe",
    "ul-monroe": "ul monroe",
    "houston christian": "hcu",
    "houston baptist": "hcu",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm(value: Any) -> str:
    s = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()
    return ALIASES.get(s, s)


def finite(value: Any):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def clean_int(value: Any):
    x = finite(value)
    return int(x) if x is not None and float(x).is_integer() else x


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        dir=path.parent,
        delete=False,
        encoding="utf-8",
    ) as handle:
        handle.write(text)
        tmp = Path(handle.name)
    tmp.replace(path)


def first_value(row: dict, keys: list[str]):
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def market_fields(game: dict) -> dict:
    return {
        "opening_home_spread": finite(first_value(game, [
            "opening_home_spread",
            "market_open_spread_home",
            "opener_spread_home",
            "opening_spread_home",
        ])),
        "opening_total": finite(first_value(game, [
            "opening_total",
            "market_open_total",
            "opener_total",
        ])),
        "closing_home_spread": finite(first_value(game, [
            "closing_home_spread",
            "market_close_spread_home",
            "market_spread_home",
        ])),
        "closing_total": finite(first_value(game, [
            "closing_total",
            "market_close_total",
            "market_total",
        ])),
    }


def main() -> None:
    if not CFBD.exists():
        raise SystemExit(f"Missing required input: {CFBD}")
    if not DB.exists():
        raise SystemExit(f"Missing required input: {DB}")

    cfbd_payload = json.loads(CFBD.read_text())
    db = json.loads(DB.read_text())

    cfbd_games = cfbd_payload.get("games", [])
    site_games = db.get("games", [])

    by_cfbd_id = {
        str(g.get("cfbd_game_id")): g
        for g in site_games
        if g.get("cfbd_game_id") is not None
    }

    by_pair = {}
    for g in site_games:
        key = (norm(g.get("away_team")), norm(g.get("home_team")))
        by_pair.setdefault(key, []).append(g)

    rows = []
    unmatched = []
    ambiguous = []

    for cg in cfbd_games:
        if not cg.get("completed"):
            continue

        away = cg.get("away_team")
        home = cg.get("home_team")
        away_score = finite(cg.get("away_points"))
        home_score = finite(cg.get("home_points"))

        if away_score is None or home_score is None:
            continue

        sg = None
        method = None

        cid = cg.get("cfbd_game_id")
        if cid is not None:
            sg = by_cfbd_id.get(str(cid))
            if sg is not None:
                method = "cfbd_game_id"

        if sg is None:
            candidates = by_pair.get((norm(away), norm(home)), [])
            if len(candidates) == 1:
                sg = candidates[0]
                method = "unique_team_pair"
            elif len(candidates) > 1:
                same_week = [
                    x for x in candidates
                    if str(x.get("week")) == str(cg.get("week"))
                ]
                if len(same_week) == 1:
                    sg = same_week[0]
                    method = "team_pair_plus_week"
                elif len(same_week) > 1:
                    ambiguous.append({
                        "cfbd_game_id": cid,
                        "away_team": away,
                        "home_team": home,
                        "week": cg.get("week"),
                        "candidate_game_ids": [x.get("game_id") for x in same_week],
                    })

        if sg is None:
            unmatched.append({
                "cfbd_game_id": cid,
                "week": cg.get("week"),
                "date": cg.get("date"),
                "away_team": away,
                "home_team": home,
            })
            continue

        market = market_fields(sg)
        home_margin = home_score - away_score
        total_points = home_score + away_score

        close_spread = market["closing_home_spread"]
        close_total = market["closing_total"]

        row = {
            "schema_version": "game-results-2026-v1",
            "season": 2026,
            "game_id": str(sg.get("game_id") or ""),
            "cfbd_game_id": cid,
            "week": clean_int(cg.get("week")),
            "provider_week": clean_int(cg.get("provider_week")),
            "date": cg.get("date"),
            "start_date": cg.get("start_date"),
            "away_team": sg.get("away_team") or away,
            "home_team": sg.get("home_team") or home,
            "neutral_site": bool(cg.get("neutral_site")),
            "completed": True,
            "status": cg.get("status") or "completed",
            "away_score": clean_int(away_score),
            "home_score": clean_int(home_score),
            "home_margin_actual": clean_int(home_margin),
            "total_points_actual": clean_int(total_points),
            **market,
            "close_available": close_spread is not None and close_total is not None,
            "ats_margin_home": (
                home_margin + close_spread
                if close_spread is not None
                else None
            ),
            "total_margin": (
                total_points - close_total
                if close_total is not None
                else None
            ),
            "match_method": method,
            "source": "CollegeFootballData /games",
            "source_updated_at": cg.get("cfbd_last_updated"),
            "pulled_at": cg.get("pulled_at") or cfbd_payload.get("pulled_at"),
        }
        rows.append(row)

    rows.sort(key=lambda x: (
        int(x.get("week") or 0),
        str(x.get("date") or ""),
        str(x.get("game_id") or ""),
    ))

    payload = {
        "schema_version": "game-results-2026-v1",
        "generated_at": now_iso(),
        "season": 2026,
        "source": "CollegeFootballData /games + canonical site game mapping",
        "games": rows,
        "summary": {
            "completed_cfbd_games": sum(
                bool(g.get("completed"))
                and finite(g.get("home_points")) is not None
                and finite(g.get("away_points")) is not None
                for g in cfbd_games
            ),
            "matched_results": len(rows),
            "unmatched_completed_games": len(unmatched),
            "ambiguous_completed_games": len(ambiguous),
            "with_closing_spread": sum(r["closing_home_spread"] is not None for r in rows),
            "with_closing_total": sum(r["closing_total"] is not None for r in rows),
            "with_complete_close": sum(r["close_available"] for r in rows),
        },
    }

    frame = pd.DataFrame(rows)

    atomic_text(
        OUT_JSON,
        json.dumps(payload, indent=2, allow_nan=False) + "\n",
    )
    atomic_text(
        OUT_CSV,
        frame.to_csv(index=False),
    )

    audit = {
        "schema_version": "game-results-2026-audit-v1",
        "generated_at": now_iso(),
        **payload["summary"],
        "unmatched": unmatched,
        "ambiguous": ambiguous,
    }
    atomic_text(
        AUDIT,
        json.dumps(audit, indent=2, allow_nan=False) + "\n",
    )

    print(json.dumps(payload["summary"], indent=2))
    print("wrote:", OUT_JSON)
    print("wrote:", OUT_CSV)
    print("wrote:", AUDIT)

    if ambiguous:
        raise SystemExit("Ambiguous completed-game mappings remain")


if __name__ == "__main__":
    main()
