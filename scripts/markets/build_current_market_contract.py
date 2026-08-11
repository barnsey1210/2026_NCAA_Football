#!/usr/bin/env python3
"""Build the canonical current-market contract.

This contract is the only allowed source-selection layer for current game odds.
Historical snapshots remain separate and must never silently replace missing
current quotes.

Priority is applied independently for each:
  canonical_game_id × sportsbook × market_type × side

Source priority:
  1. Fresh The Odds API quote
  2. Fresh SportsGameOdds accepted quote
  3. Fresh Action Network quote
  4. Missing

Stale quotes are retained only in the audit counts, never as current values.
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATCHUPS = ROOT / "data/site/matchups_view.json"
THEODDS = ROOT / "data/odds/theodds_ncaaf_lines_2026.csv"
SGO = ROOT / "data/markets/sgo/sgo_accepted_quotes.csv"
ACTION = ROOT / "data/odds/actionnetwork_ncaaf_game_lines_2026.csv"
OUT = ROOT / "data/site/current_market_contract.json"
AUDIT = ROOT / "data/audits/current_market_contract_build_audit.json"

TARGET_BOOKS = (
    "Pinnacle",
    "Novig",
    "ProphetX",
    "Kalshi",
    "DraftKings",
    "FanDuel",
    "BetMGM",
    "Caesars",
    "Fanatics",
    "Hard Rock Bet",
)
REFERENCE_BOOK_PRIORITY = TARGET_BOOKS
MAX_AGE_HOURS = float(os.environ.get("NCAAF_CURRENT_MARKET_MAX_AGE_HOURS", "18"))


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=False)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def csv_rows(path: Path) -> list[dict]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig", errors="ignore") as handle:
        return list(csv.DictReader(handle))


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def parse_time(value: str | None) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def normalize_team(value: str | None) -> str:
    text = (value or "").lower().replace("&", "and")
    text = text.replace("hawai'i", "hawaii").replace("miami (fl)", "miami-fl")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    aliases = {
        "miami fl": "miami florida",
        "miami": "miami florida",
        "ole miss": "mississippi",
        "ucf": "central florida",
        "utsa": "texas san antonio",
        "uconn": "connecticut",
        "umass": "massachusetts",
        "southern miss": "southern mississippi",

        # The Odds API provider-name aliases / mascot suffixes.
        "umass minutemen": "massachusetts",
        "rutgers scarlet knights": "rutgers",
        "albany": "ualbany",
        "buffalo bulls": "buffalo",
        "bethune cookman wildcats": "bethune cookman",
        "ucf knights": "central florida",
        "arkansas pine bluff golden lions": "uapb",
        "uab blazers": "uab",
        "illinois fighting illini": "illinois",
        "indiana state sycamores": "indiana state",
        "purdue boilermakers": "purdue",
        "miami hurricanes": "miami florida",
        "stanford cardinal": "stanford",
        "lafayette leopards": "lafayette",
        "uconn huskies": "connecticut",
        "youngstown st penguins": "youngstown state",
        "citadel bulldogs": "the citadel",
        "ut rio grande valley vaqueros": "utrgv",
        "utsa roadrunners": "texas san antonio",
        "charleston southern buccaneers": "charleston so",
        "georgia southern eagles": "georgia southern",
        "houston baptist huskies": "hcu",
        "rice owls": "rice",
        "southeastern louisiana lions": "southeastern la",
        "south alabama jaguars": "south alabama",
        "mississippi valley state delta devils": "mvsu",
        "sacramento state hornets": "sacramento state",
        "washington state cougars": "washington state",
        "washington huskies": "washington",
        "louisville cardinals": "louisville",
        "ole miss rebels": "mississippi",
        "lsu tigers": "lsu",
        "houston cougars": "houston",
        "texas tech red raiders": "texas tech",
        "clemson tigers": "clemson",
        "oklahoma sooners": "oklahoma",
        "texas longhorns": "texas",
        "notre dame fighting irish": "notre dame",

        # The Odds API provider-name aliases / mascot suffixes.
        "umass minutemen": "massachusetts",
        "rutgers scarlet knights": "rutgers",
        "albany": "ualbany",
        "buffalo bulls": "buffalo",
        "bethune cookman wildcats": "bethune cookman",
        "ucf knights": "central florida",
        "arkansas pine bluff golden lions": "uapb",
        "uab blazers": "uab",
        "illinois fighting illini": "illinois",
        "indiana state sycamores": "indiana state",
        "purdue boilermakers": "purdue",
        "miami hurricanes": "miami florida",
        "stanford cardinal": "stanford",
        "lafayette leopards": "lafayette",
        "uconn huskies": "connecticut",
        "youngstown st penguins": "youngstown state",
        "citadel bulldogs": "the citadel",
        "ut rio grande valley vaqueros": "utrgv",
        "utsa roadrunners": "texas san antonio",
        "charleston southern buccaneers": "charleston so",
        "georgia southern eagles": "georgia southern",
        "houston baptist huskies": "hcu",
        "rice owls": "rice",
        "southeastern louisiana lions": "southeastern la",
        "south alabama jaguars": "south alabama",
        "mississippi valley state delta devils": "mvsu",
        "sacramento state hornets": "sacramento state",
        "washington state cougars": "washington state",
        "washington huskies": "washington",
        "louisville cardinals": "louisville",
        "ole miss rebels": "mississippi",
        "lsu tigers": "lsu",
        "houston cougars": "houston",
        "texas tech red raiders": "texas tech",
        "clemson tigers": "clemson",
        "oklahoma sooners": "oklahoma",
        "texas longhorns": "texas",
        "notre dame fighting irish": "notre dame",
    }
    cleaned = " ".join(text.split())
    return aliases.get(cleaned, cleaned)


def normalize_book(value: str | None) -> str | None:
    text = re.sub(r"[^a-z0-9]+", "", str(value or "").lower())
    aliases = {
        "draftkings": "DraftKings",
        "fanduel": "FanDuel",
        "betmgm": "BetMGM",
        "mgm": "BetMGM",
        "caesars": "Caesars",
        "caesar": "Caesars",
        "hardrockbet": "Hard Rock Bet",
        "hardrockbetoh": "Hard Rock Bet",
        "hardrock": "Hard Rock Bet",
        "pinnacle": "Pinnacle",
        "novig": "Novig",
        "prophetx": "ProphetX",
        "kalshi": "Kalshi",
        "fanatics": "Fanatics",
        "bovada": "Bovada",
    }
    return aliases.get(text)


def game_key(date, away, home):
    return str(date or "")[:10], normalize_team(away), normalize_team(home)


def team_name_compatible(left, right):
    # Fallback for provider mascot/nickname suffixes.
    a = normalize_team(left)
    b = normalize_team(right)
    if not a or not b:
        return False
    if a == b:
        return True
    return a.startswith(b + " ") or b.startswith(a + " ")


def resolve_game_id(date_candidates, away, home, identity, key_to_game_id):
    # 1) Exact date + canonical orientation.
    for date in date_candidates:
        gid = key_to_game_id.get(game_key(date, away, home))
        if gid:
            return gid, "exact", False

    candidate_dates = {str(d or "")[:10] for d in date_candidates if d}

    # 2) Same date + compatible provider names.
    matches = []
    for gid, meta in identity.items():
        if str(meta.get("date") or "")[:10] not in candidate_dates:
            continue
        if team_name_compatible(away, meta.get("away_team")) and team_name_compatible(home, meta.get("home_team")):
            matches.append(gid)
    if len(matches) == 1:
        return matches[0], "nickname_prefix", False

    # 3) Same date + reversed orientation.
    reversed_matches = []
    for gid, meta in identity.items():
        if str(meta.get("date") or "")[:10] not in candidate_dates:
            continue
        if team_name_compatible(away, meta.get("home_team")) and team_name_compatible(home, meta.get("away_team")):
            reversed_matches.append(gid)
    if len(reversed_matches) == 1:
        return reversed_matches[0], "reversed_same_date", True

    # 4) Unique same two teams within +/- 2 days.
    from datetime import date as _date
    parsed_dates = []
    for d in date_candidates:
        try:
            parsed_dates.append(_date.fromisoformat(str(d)[:10]))
        except Exception:
            pass

    nearby = []
    for gid, meta in identity.items():
        try:
            canonical_date = _date.fromisoformat(str(meta.get("date") or "")[:10])
        except Exception:
            continue
        if not any(abs((canonical_date - d).days) <= 2 for d in parsed_dates):
            continue

        same_orientation = (
            team_name_compatible(away, meta.get("away_team"))
            and team_name_compatible(home, meta.get("home_team"))
        )
        reversed_orientation = (
            team_name_compatible(away, meta.get("home_team"))
            and team_name_compatible(home, meta.get("away_team"))
        )
        if same_orientation:
            nearby.append((gid, False))
        elif reversed_orientation:
            nearby.append((gid, True))

    unique_ids = {gid for gid, _ in nearby}
    if len(unique_ids) == 1:
        gid = next(iter(unique_ids))
        reversed_orientation = next(flag for g, flag in nearby if g == gid)
        return gid, "unique_teams_within_2_days", reversed_orientation

    return None, "ambiguous_or_missing", False


SITE_TZ = ZoneInfo("America/New_York")


def site_date_from_timestamp(value: str | None) -> str:
    parsed = parse_time(value)
    return parsed.astimezone(SITE_TZ).date().isoformat() if parsed else ""


def quote_age_hours(timestamp: str | None, now: datetime) -> float | None:
    parsed = parse_time(timestamp)
    return (now - parsed).total_seconds() / 3600 if parsed else None


def fresh(timestamp: str | None, now: datetime) -> bool:
    age = quote_age_hours(timestamp, now)
    return age is not None and -0.25 <= age <= MAX_AGE_HOURS


def quote_record(*, source, game_id, book, market, side, line, price, updated_at, now):
    age = quote_age_hours(updated_at, now)
    return {
        "source": source,
        "game_id": game_id,
        "sportsbook": book,
        "market_type": market,
        "side": side,
        "line": line,
        "price": price,
        "source_updated_at": updated_at,
        "quote_age_hours": round(age, 3) if age is not None else None,
        "freshness_status": "LIVE" if fresh(updated_at, now) else "STALE",
    }


def pair_is_valid(market: str, sides: dict) -> bool:
    expected = {"away", "home"} if market in {"spread", "moneyline"} else {"over", "under"}
    if set(sides) != expected:
        return False
    if market == "spread":
        a, h = number(sides["away"].get("line")), number(sides["home"].get("line"))
        return a is not None and h is not None and abs(a + h) <= 0.01
    if market == "total":
        o, u = number(sides["over"].get("line")), number(sides["under"].get("line"))
        return o is not None and u is not None and abs(o - u) <= 0.01
    return all(number(sides[s].get("price")) is not None for s in expected)


def best_quote(quotes: dict, market: str, side: str):
    candidates = []
    for book, book_data in quotes.items():
        q = book_data.get(market, {}).get(side)
        if not q or q.get("freshness_status") not in {"LIVE", "BACKUP_SOURCE"}:
            continue
        line, price = number(q.get("line")), number(q.get("price"))
        if market == "moneyline":
            if price is not None:
                candidates.append(((price,), q))
        elif line is not None:
            if market == "spread":
                score = (line, price if price is not None else -100000)
            elif side == "over":
                score = (-line, price if price is not None else -100000)
            else:
                score = (line, price if price is not None else -100000)
            candidates.append((score, q))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def reference_pair(quotes: dict, market: str):
    for book in REFERENCE_BOOK_PRIORITY:
        sides = quotes.get(book, {}).get(market, {})
        if pair_is_valid(market, sides):
            return {"sportsbook": book, **sides}
    return None


def main() -> None:
    if not MATCHUPS.exists():
        raise SystemExit(f"Missing canonical game identity payload: {MATCHUPS}")

    now = datetime.now(timezone.utc)
    matchup_payload = json.loads(MATCHUPS.read_text())
    games = matchup_payload.get("games", [])
    identity = {}
    key_to_game_id = {}
    for row in games:
        game = row.get("game", {})
        gid = str(game.get("game_id") or "")
        if not gid:
            continue
        identity[gid] = {
            "game_id": gid,
            "date": str(game.get("date") or "")[:10],
            "week": game.get("week"),
            "away_team": game.get("away_team"),
            "home_team": game.get("home_team"),
        }
        key_to_game_id[game_key(game.get("date"), game.get("away_team"), game.get("home_team"))] = gid

    candidates = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    excluded = []
    source_counts = Counter()

    # Primary: fresh The Odds API quote inventory.
    for row in csv_rows(THEODDS):
        local_date = site_date_from_timestamp(row.get("commence_time"))
        date_candidates = [
            local_date,
            str(row.get("commence_time") or "")[:10],
        ]
        gid, match_method, reversed_orientation = resolve_game_id(
            date_candidates,
            row.get("away_team"),
            row.get("home_team"),
            identity,
            key_to_game_id,
        )
        if not gid:
            excluded.append({
                "source": "The Odds API",
                "reason": "unmatched_game_identity",
                "date_candidates": date_candidates,
                "away_team": row.get("away_team"),
                "home_team": row.get("home_team"),
            })
            continue

        book = normalize_book(row.get("book_key") or row.get("book"))
        raw_market = str(row.get("market") or "").lower()
        market = {
            "h2h": "moneyline",
            "spreads": "spread",
            "totals": "total",
            "moneyline": "moneyline",
            "spread": "spread",
            "total": "total",
        }.get(raw_market)
        raw_side = str(row.get("side") or "").strip()

        if market in {"spread", "moneyline"}:
            if normalize_team(raw_side) == normalize_team(row.get("away_team")):
                provider_side = "away"
            elif normalize_team(raw_side) == normalize_team(row.get("home_team")):
                provider_side = "home"
            else:
                continue

            if reversed_orientation:
                side = "home" if provider_side == "away" else "away"
            else:
                side = provider_side
        elif market == "total":
            side = raw_side.lower()
        else:
            continue

        if not book or side not in {"away", "home", "over", "under"}:
            continue

        q = quote_record(
            source="The Odds API", game_id=gid, book=book, market=market, side=side,
            line=number(row.get("point")), price=number(row.get("price")),
            updated_at=row.get("last_update") or row.get("pulled_at"), now=now,
        )
        if q["freshness_status"] != "LIVE":
            excluded.append({"source": "The Odds API", "reason": "stale_current_quote", **q})
            continue

        candidates[gid][book][market][side] = q
        source_counts["The Odds API"] += 1

    # SportsGameOdds is retained as an emergency backup provider only.
    # It is intentionally excluded from the live current market contract.
    # Historical SGO artifacts remain available separately.
    #
    # Normal production market sourcing:
    #   1. The Odds API
    #   2. Action Network fallback
    #
    # Do not re-enable SGO here unless primary providers fail.
    pass

    # Backup: fresh Action Network only where The Odds API did not provide that exact
    # game/book/market/side.
    for row in csv_rows(ACTION):
        # Action Network's `date` is UTC-derived for late-night games. Resolve
        # the canonical site date from commence_time in America/New_York first,
        # then fall back to the raw date for older rows without commence_time.
        local_date = site_date_from_timestamp(row.get("commence_time"))
        keys = [
            game_key(local_date, row.get("away_team"), row.get("home_team")),
            game_key(row.get("date"), row.get("away_team"), row.get("home_team")),
        ]
        gid = next((key_to_game_id.get(key) for key in keys if key_to_game_id.get(key)), None)
        if not gid:
            excluded.append({
                "source": "Action Network",
                "reason": "unmatched_game_identity",
                "raw_date": row.get("date"),
                "site_date": local_date,
                "away_team": row.get("away_team"),
                "home_team": row.get("home_team"),
            })
            continue
        book = normalize_book(row.get("book"))
        market = str(row.get("market") or "").lower()
        side = str(row.get("side") or "").lower()
        timestamp = row.get("pulled_at") or row.get("source_updated_at")
        if not book or market not in {"spread", "total", "moneyline"}:
            continue
        if side not in {"away", "home", "over", "under"}:
            continue
        if side in candidates[gid][book][market]:
            continue
        q = quote_record(
            source="Action Network", game_id=gid, book=book, market=market, side=side,
            line=number(row.get("point")), price=number(row.get("price")),
            updated_at=timestamp, now=now,
        )
        if q["freshness_status"] != "LIVE":
            excluded.append({"source": "Action Network", "reason": "stale_current_quote", **q})
            continue
        q["freshness_status"] = "BACKUP_SOURCE"
        candidates[gid][book][market][side] = q
        source_counts["Action Network"] += 1

    contract_games = []
    stale_current_quotes_displayed = 0
    invalid_pairs = 0
    games_with_any_current = 0

    for gid, meta in identity.items():
        quotes = {}
        for book in TARGET_BOOKS:
            book_output = {}
            for market in ("spread", "total", "moneyline"):
                sides = dict(candidates[gid][book][market])
                if not sides:
                    continue
                if not pair_is_valid(market, sides):
                    invalid_pairs += 1
                    excluded.append({
                        "source": "contract_validation",
                        "reason": "invalid_or_incomplete_pair",
                        "game_id": gid,
                        "sportsbook": book,
                        "market_type": market,
                    })
                    continue
                book_output[market] = sides
            if book_output:
                quotes[book] = book_output

        best = {
            "away_spread": best_quote(quotes, "spread", "away"),
            "home_spread": best_quote(quotes, "spread", "home"),
            "over": best_quote(quotes, "total", "over"),
            "under": best_quote(quotes, "total", "under"),
            "away_moneyline": best_quote(quotes, "moneyline", "away"),
            "home_moneyline": best_quote(quotes, "moneyline", "home"),
        }
        reference = {
            "spread": reference_pair(quotes, "spread"),
            "total": reference_pair(quotes, "total"),
            "moneyline": reference_pair(quotes, "moneyline"),
        }
        timestamps = [
            q.get("source_updated_at")
            for book_data in quotes.values()
            for market_data in book_data.values()
            for q in market_data.values()
            if q.get("source_updated_at")
        ]
        availability = "LIVE" if any(
            q.get("source") == "The Odds API"
            for book_data in quotes.values()
            for market_data in book_data.values()
            for q in market_data.values()
        ) else ("BACKUP_SOURCE" if quotes else "MISSING")
        if quotes:
            games_with_any_current += 1
        contract_games.append({
            **meta,
            "availability_status": availability,
            "availability_reason": None if quotes else "No fresh accepted current quote from an approved provider",
            "current_market_updated_at": max(timestamps) if timestamps else None,
            "quotes": quotes,
            "reference": reference,
            "best": best,
        })

    payload = {
        "schema_version": "current-market-contract-v1",
        "built_at": now.isoformat(),
        "max_quote_age_hours": MAX_AGE_HOURS,
        "source_priority": ["The Odds API", "Action Network", "MISSING"],
        "stale_data_policy": "Stale quotes are never exposed as current. Historical snapshots remain separate.",
        "target_sportsbooks": list(TARGET_BOOKS),
        "games": contract_games,
    }
    audit = {
        "built_at": now.isoformat(),
        "games_total": len(contract_games),
        "games_with_any_current": games_with_any_current,
        "games_missing_current": len(contract_games) - games_with_any_current,
        "accepted_quote_counts_by_source": dict(source_counts),
        "invalid_pairs_excluded": invalid_pairs,
        "stale_current_quotes_displayed": stale_current_quotes_displayed,
        "excluded_count": len(excluded),
        "excluded_sample": excluded[:100],
        "inputs": [
            str(MATCHUPS.relative_to(ROOT)),
            str(THEODDS.relative_to(ROOT)),
            str(SGO.relative_to(ROOT)),
            str(ACTION.relative_to(ROOT)),
        ],
        "output": str(OUT.relative_to(ROOT)),
    }
    atomic_json(OUT, payload)
    atomic_json(AUDIT, audit)
    print(json.dumps(audit, indent=2))
    if stale_current_quotes_displayed:
        raise SystemExit("stale_current_quotes_displayed must be zero")


if __name__ == "__main__":
    main()
