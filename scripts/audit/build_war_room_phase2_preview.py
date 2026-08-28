#!/usr/bin/env python3
"""Build an isolated visual fixture for War Room matrix Phase 2.

This utility never acquires data and never writes canonical artifacts. It
copies the current local shell/contracts to /tmp and overlays synthetic timing
metadata solely for browser presentation checks.
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = Path("/tmp/ncaaf-war-room-phase2-preview")


def iso(minutes_ago: int) -> str:
    return (
        datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    ).isoformat().replace("+00:00", "Z")


def displayed_quote(game: dict, market: str) -> dict | None:
    side = (game.get("edges") or {}).get(market, {}).get("best_side")
    return (
        (game.get("market") or {}).get("best_sportsbook", {})
        .get(market, {}).get(side)
    )


def set_opener_age(game: dict, market: str, minutes: int) -> None:
    opener = game["market"]["openers"].get(market)
    if opener:
        opener["observed_at"] = iso(minutes)


def set_shadow_demo(game: dict, market: str, away_ready: bool,
                    home_ready: bool, value: float | None = None) -> None:
    """Exercise READY/PARTIAL/WAIT visual states in the isolated preview only."""
    readiness = game.setdefault("shadow_readiness", {})
    readiness[f"away_{market}_shadow_ready"] = away_ready
    readiness[f"home_{market}_shadow_ready"] = home_ready
    model = game.setdefault("models", {}).setdefault(f"shadow_{market}", {})
    model["selection_status"] = "AVAILABLE" if value is not None else "UNAVAILABLE"
    model["value_home_line" if market == "spread" else "value_total"] = value


def add_move(game: dict, market: str, minutes: int, direction: str, refresh_id: str) -> None:
    quote = displayed_quote(game, market)
    if not quote:
        return
    current = float(quote["line"])
    if market == "spread":
        old = current - 0.5 if abs(current) >= abs(current - 0.5) else current + 0.5
        if direction == "DOWN":
            old = current - 0.5 if abs(current - 0.5) > abs(current) else current + 0.5
    else:
        old = current - 0.5 if direction == "UP" else current + 0.5
    quote["last_material_move"] = {
        "event_id": f"preview-{game['game_id']}-{market}",
        "detected_refresh_id": refresh_id,
        "detected_at": iso(minutes),
        "quote_timestamp": iso(minutes + 1),
        "old_line": old,
        "new_line": current,
        "book": quote["book"],
        "market": market,
        "side": quote["side"],
        "direction": direction,
        "magnitude_old": abs(old),
        "magnitude_new": abs(current),
        "previous_qualifying_moves": 1,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    output = args.output.resolve()
    data_out = output / "data/site"
    data_out.mkdir(parents=True, exist_ok=True)

    shutil.copy2(ROOT / "war-room.html", output / "war-room.html")
    for name in ("war_room_health.json", "war_room_activity.json"):
        shutil.copy2(ROOT / "data/site" / name, data_out / name)
    logo_target = output / "logos"
    if logo_target.exists() or logo_target.is_symlink():
        logo_target.unlink() if logo_target.is_symlink() else shutil.rmtree(logo_target)
    logo_target.symlink_to(ROOT / "logos", target_is_directory=True)

    matrix = json.loads((ROOT / "data/site/war_room_market_matrix.json").read_text())
    matrix["fast_market_refresh"]["recent_completed_refresh_ids"] = [
        "preview-latest", "preview-prior-1", "preview-prior-2"
    ]
    games = matrix.get("games", [])
    if len(games) < 6:
        raise SystemExit("Preview requires at least six current local matrix games")

    set_opener_age(games[0], "spread", 10)  # NEW
    set_opener_age(games[0], "total", 10)   # NEW + move
    set_opener_age(games[1], "spread", 45)  # RECENT
    set_opener_age(games[2], "total", 75)   # RECENT
    games[3]["market"]["openers"]["spread"] = None
    games[3]["market"]["openers"]["total"] = None

    set_shadow_demo(games[0], "spread", True, True, -4.5)  # READY
    set_shadow_demo(games[0], "total", True, True, 55.5)   # READY
    set_shadow_demo(games[1], "spread", True, False)       # PARTIAL
    set_shadow_demo(games[1], "total", False, True)        # PARTIAL

    # Presentation-only TOTAL EDGE fixtures: retain production calculations
    # while exercising inline over/under, small-edge, and zero-edge layouts.
    games[6]["edges"]["total"]["best_side"] = "over"
    games[6]["edges"]["total"]["best_edge"] = 0
    games[7]["edges"]["total"]["best_side"] = "under"
    games[7]["edges"]["total"]["best_edge"] = 0.3

    add_move(games[0], "spread", 5, "UP", "preview-latest")       # red
    add_move(games[0], "total", 5, "UP", "preview-latest")        # NEW + move
    add_move(games[1], "spread", 25, "DOWN", "older-generation") # yellow by age
    add_move(games[1], "total", 20, "DOWN", "older-generation")   # total down
    add_move(games[2], "spread", 60, "UP", "older-generation")    # gray
    add_move(games[2], "total", 80, "UP", "preview-prior-2")      # yellow by generation
    add_move(games[4], "spread", 100, "UP", "preview-latest")     # expired
    # Game 5 intentionally has no marker: price-only/sub-threshold/non-BEST
    # moves are absent from the bounded matrix contract.

    (data_out / "war_room_market_matrix.json").write_text(
        json.dumps(matrix, indent=2) + "\n"
    )
    print(output / "war-room.html")


if __name__ == "__main__":
    main()
