#!/usr/bin/env python3
"""Deterministic game identity and authoritative frozen-close resolution."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import math
import re


ROOT = Path(__file__).resolve().parents[1]


def clean_key(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = re.sub(r"[^a-z0-9]+", " ", str(value).lower())
    return re.sub(r"\s+", " ", text).strip()


def _alias_map(root=ROOT):
    path = Path(root) / "config/team_aliases.json"
    raw = json.loads(path.read_text()).get("aliases", {}) if path.exists() else {}
    aliases = {clean_key(key): value for key, value in raw.items()}
    # Sheet/provider variants not otherwise present in the shared identity file.
    aliases.update({
        "ark st": "Arkansas State",
        "ball st": "Ball State",
        "fiu": "Florida International",
        "georgia st": "Georgia State",
        "middle tennessee state": "Middle Tennessee",
        "minnestoa": "Minnesota",
        "northern ill": "Northern Illinois",
        "okst": "Oklahoma State",
        "oregon st": "Oregon State",
        "sam houston state": "Sam Houston",
        "san jose st": "San Jose State",
        "ucf": "Central Florida",
        "usc": "USC",
    })
    return aliases


def canonical_team(value, root=ROOT):
    key = clean_key(value)
    return _alias_map(root).get(key, str(value or "").strip())


def parse_week(row):
    text = " ".join(str(row.get(key) or "") for key in ("Bet Description", "Week", "week_bucket", "week"))
    match = re.search(r"\bweek\s*(\d+)\b", text, re.I)
    if match:
        return int(match.group(1))
    try:
        return int(float(row.get("week")))
    except (TypeError, ValueError):
        return None


def wager_team_tokens(row):
    bet = str(row.get("Bet") or row.get("selection") or "")
    head = re.split(r"\bover\b|\bunder\b", bet, flags=re.I)[0]
    return [
        canonical_team(part)
        for part in re.split(r"[/@]|(?:\s+vs\.?\s+)|(?:\s+at\s+)", head, flags=re.I)
        if clean_key(part)
    ]


def market_kind(row):
    kind = clean_key(row.get("Bet Type") or row.get("market"))
    bet = clean_key(row.get("Bet") or row.get("selection"))
    side = clean_key(row.get("side"))
    if kind in {"total", "game total"} or side in {"over", "under"} or re.search(r"\b(over|under)\b", bet):
        return "total"
    if kind in {"side", "spread"}:
        return "spread"
    if kind == "moneyline":
        return "moneyline"
    return None


def raw_sheet_game_id(row):
    """Return the Sheet-owned game ID without treating derived IDs as Sheet input."""
    for key in ("raw_sheet_game_id", "Game ID"):
        value = row.get(key)
        if value is not None and not (isinstance(value, float) and math.isnan(value)):
            text = str(value).strip()
            if text and text.lower() != "nan":
                return text
    return ""


def canonical_game_id(row):
    """Return an already-validated canonical ID carried by the wager row."""
    for key in ("game_id", "canonical_game_id", "current_market_game_id"):
        value = row.get(key)
        if value is not None and not (isinstance(value, float) and math.isnan(value)):
            text = str(value).strip()
            if text and text.lower() != "nan":
                return text
    return ""


def game_label_matches(label, game):
    """Validate the human-readable Sheet label without making it authoritative."""
    if not str(label or "").strip():
        return None
    label_key = clean_key(label)
    away_key = clean_key(canonical_team(game.get("away_team")))
    home_key = clean_key(canonical_team(game.get("home_team")))
    return bool(away_key and home_key and away_key in label_key and home_key in label_key)


def resolve_game(row, games):
    """Return (unique game, reason); ambiguity always fails closed."""
    by_id = {str(game.get("game_id") or "").strip(): game for game in games}
    sheet_id = raw_sheet_game_id(row)
    identity_status = str(row.get("game_identity_status") or "").strip().upper()

    # A populated Sheet ID is authoritative. Invalid populated IDs never fall
    # through to fuzzy matching, because doing so would silently overwrite the
    # user's explicit identity selection.
    if sheet_id:
        game = by_id.get(sheet_id)
        return (game, "sheet_game_id") if game else (None, "invalid_sheet_game_id")
    if identity_status == "INVALID_SHEET_GAME_ID":
        return None, "invalid_sheet_game_id"

    derived_id = canonical_game_id(row)
    if derived_id and derived_id in by_id:
        return by_id[derived_id], "canonical_game_id"

    week = parse_week(row)
    pool = [game for game in games if week is None or int(float(game.get("week", -1))) == week]
    kind = market_kind(row)

    if kind == "total":
        tokens = {clean_key(canonical_team(token)) for token in wager_team_tokens(row) if clean_key(token)}
        matches = []
        for game in pool:
            participants = {clean_key(canonical_team(game.get("away_team"))), clean_key(canonical_team(game.get("home_team")))}
            if tokens and tokens.issubset(participants):
                matches.append(game)
        if len(matches) == 1:
            return matches[0], "exact_matchup_week"
        return None, "ambiguous_matchup" if matches else "no_match"

    team = canonical_team(row.get("team_guess") or row.get("team") or row.get("Bet") or row.get("selection"))
    team_key = clean_key(team)
    matches = [
        game for game in pool
        if team_key in {clean_key(canonical_team(game.get("away_team"))), clean_key(canonical_team(game.get("home_team")))}
    ]
    if len(matches) == 1:
        return matches[0], "exact_team_week"
    return None, "ambiguous_team" if matches else "no_match"


def selected_side(row, game, kind):
    if kind == "total":
        side = clean_key(row.get("side"))
        if side in {"over", "under"}:
            return side
        match = re.search(r"\b(over|under)\b", clean_key(row.get("Bet") or row.get("selection")))
        return match.group(1) if match else None
    team = clean_key(canonical_team(row.get("team_guess") or row.get("team") or row.get("Bet") or row.get("selection")))
    if team == clean_key(canonical_team(game.get("away_team"))):
        return "away"
    if team == clean_key(canonical_team(game.get("home_team"))):
        return "home"
    return None


def authoritative_frozen_quote(row, game):
    """Select a paired FROZEN_CLOSE quote, preferring Pinnacle."""
    kind = market_kind(row)
    if kind not in {"spread", "total"}:
        return None, "not_applicable_point_clv" if kind == "moneyline" else "unsupported_market"
    side = selected_side(row, game, kind)
    if not side:
        return None, "missing_selected_side"
    other = ({"over": "under", "under": "over"} if kind == "total" else {"away": "home", "home": "away"})[side]
    quotes = game.get("quotes") or {}
    books = ["Pinnacle", *sorted(book for book in quotes if book != "Pinnacle")]
    for book in books:
        market = (quotes.get(book) or {}).get(kind) or {}
        selected, opposite = market.get(side), market.get(other)
        if not selected or not opposite:
            continue
        if selected.get("freshness_status") != "FROZEN_CLOSE" or opposite.get("freshness_status") != "FROZEN_CLOSE":
            continue
        if selected.get("line") is None:
            continue
        return {
            "game_id": game.get("game_id"), "kind": kind, "side": side,
            "book": book, "selected": selected, "opposite": opposite,
            "authority": "FROZEN_CLOSE",
        }, "pinnacle_frozen_close" if book == "Pinnacle" else "deterministic_frozen_fallback"
    return None, "authoritative_frozen_close_missing"


def point_clv(row, quote):
    bet_line = float(row.get("bet_line"))
    close_line = float(quote["selected"]["line"])
    if quote["kind"] == "spread":
        return bet_line - close_line
    return close_line - bet_line if quote["side"] == "over" else bet_line - close_line
