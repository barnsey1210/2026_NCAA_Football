#!/usr/bin/env python3
"""Replace Odds Screen current quotes with the canonical market contract.

The existing Odds builder remains responsible for opener and history display.
This adapter replaces only current quote selection and best flags.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/site/current_market_contract.json"
ODDS = ROOT / "data/site/odds_screen_v2.json"


def atomic_json(path: Path, value: dict) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def blank_quotes(books):
    return {book: {"spread": {}, "total": {}, "moneyline": {}} for book in books}


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    payload = json.loads(ODDS.read_text())
    by_id = {str(g["game_id"]): g for g in contract.get("games", [])}
    books = payload.get("books", contract.get("target_sportsbooks", []))

    for game in payload.get("games", []):
        current = by_id.get(str(game.get("game_id")))
        game["quotes"] = blank_quotes(books)
        game["best_flags"] = {}
        if not current or current.get("availability_status") == "MISSING":
            game["source_updated_at"] = None
            game["current_market_status"] = "MISSING"
            game.setdefault("data_quality_notes", []).append("No fresh canonical current market")
            continue

        for book, markets in current.get("quotes", {}).items():
            if book not in game["quotes"]:
                game["quotes"][book] = {"spread": {}, "total": {}, "moneyline": {}}
            for market, sides in markets.items():
                game["quotes"][book][market] = {
                    side: {
                        "point": q.get("line"),
                        "price": q.get("price"),
                        "updated_at": q.get("source_updated_at"),
                        "source": q.get("source"),
                        "freshness_status": q.get("freshness_status"),
                        "valid": True,
                    }
                    for side, q in sides.items()
                }

        best_lookup = {
            ("spread", "away"): current.get("best", {}).get("away_spread"),
            ("spread", "home"): current.get("best", {}).get("home_spread"),
            ("total", "over"): current.get("best", {}).get("over"),
            ("total", "under"): current.get("best", {}).get("under"),
            ("moneyline", "away"): current.get("best", {}).get("away_moneyline"),
            ("moneyline", "home"): current.get("best", {}).get("home_moneyline"),
        }
        for (market, side), q in best_lookup.items():
            if q:
                game["best_flags"].setdefault(q["sportsbook"], {}).setdefault(market, {})[side] = True

        game["source_updated_at"] = current.get("current_market_updated_at")
        game["current_market_status"] = current.get("availability_status")

    payload["current_market_contract"] = {
        "source": "data/site/current_market_contract.json",
        "schema_version": contract.get("schema_version"),
        "built_at": contract.get("built_at"),
    }
    atomic_json(ODDS, payload)
    print(f"Applied canonical current market to {len(payload.get('games', []))} Odds Screen games")


if __name__ == "__main__":
    main()
