#!/usr/bin/env python3
"""Pull and normalize current 2026 NCAAF Futures markets from Kalshi.

Domains:
- Win totals
- Conference titles
- Make CFP

Kalshi remains a distinct provider internally.  Native ask prices are retained
in dollars/cents and converted to American-equivalent odds for comparison with
sportsbooks.

This puller uses public market-data endpoints only.  No account API key or
private key is required.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "scripts/site"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(SITE) not in sys.path:
    sys.path.insert(0, str(SITE))

from market_team_identity import resolve_market_team


BASE = "https://external-api.kalshi.com/trade-api/v2"

SEASON_MODEL = ROOT / "data/site/season_simulations_2026.json"
OUT = ROOT / "data/markets/kalshi/kalshi_futures_2026.json"

WIN_TOTAL_SERIES = "KXNCAAFWINS"
CFP_SERIES = "KXNCAAFPLAYOFF"

CONFERENCE_SERIES = {
    "ACC": "KXNCAAFACC",
    "Big 12": "KXNCAAFB12",
    "Big Ten": "KXNCAAFB10",
    "SEC": "KXNCAAFSEC",
    "American": "KXNCAAFAAC",
    "Conference USA": "KXNCAAFCUSA",
    "Mid-American": "KXNCAAFMAC",
    "Mountain West": "KXNCAAFMWC",
    "Pac-12": "KXNCAAFPAC12",
    "Sun Belt": "KXNCAAFSBELT",
}


def get_json(path: str, params: dict | None = None) -> dict:
    r = requests.get(
        f"{BASE}{path}",
        params=params or {},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def event_pages(series_ticker: str) -> list[dict]:
    """Return all open events for a Kalshi series."""
    events = []
    cursor = None

    while True:
        params = {
            "series_ticker": series_ticker,
            "status": "open",
            "with_nested_markets": "true",
            "limit": 200,
        }
        if cursor:
            params["cursor"] = cursor

        payload = get_json("/events", params)
        events.extend(payload.get("events", []) or [])

        cursor = payload.get("cursor")
        if not cursor:
            break

    return events


def decimal_price(value):
    if value in (None, ""):
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if x < 0 or x > 1:
        return None
    return x


def american_from_probability(p):
    """Convert an executable contract ask price to gross American-equivalent odds."""
    p = decimal_price(p)

    # 0¢ / 100¢ are not useful comparable executable return prices.
    if p is None or p <= 0 or p >= 1:
        return None

    if p < 0.5:
        return int(round(100 * (1 - p) / p))

    return int(round(-100 * p / (1 - p)))


def cents(p):
    p = decimal_price(p)
    return round(p * 100, 2) if p is not None else None


def canonical_team(raw, canonical_names):
    if not raw:
        return None
    return resolve_market_team(str(raw).strip(), canonical_names)


def base_quote(market: dict, pulled_at: str) -> dict:
    ya = decimal_price(market.get("yes_ask_dollars"))
    na = decimal_price(market.get("no_ask_dollars"))
    yb = decimal_price(market.get("yes_bid_dollars"))
    nb = decimal_price(market.get("no_bid_dollars"))

    return {
        "ticker": market.get("ticker"),
        "event_ticker": market.get("event_ticker"),
        "title": market.get("title"),
        "yes_sub_title": market.get("yes_sub_title"),
        "no_sub_title": market.get("no_sub_title"),
        "status": market.get("status"),
        "close_time": market.get("close_time"),
        "updated_time": market.get("updated_time"),
        "yes_ask": ya,
        "yes_ask_cents": cents(ya),
        "yes_bid": yb,
        "yes_bid_cents": cents(yb),
        "no_ask": na,
        "no_ask_cents": cents(na),
        "no_bid": nb,
        "no_bid_cents": cents(nb),
        "yes_american_odds": american_from_probability(ya),
        "no_american_odds": american_from_probability(na),
        "pulled_at": pulled_at,
        "source": "Kalshi public market API",
    }


def parse_win_total_team_and_threshold(market: dict):
    title = str(market.get("title") or "").strip()

    # Example:
    # Will Alabama win at least 10 games this season?
    m = re.match(
        r"^Will (.+?) win at least ([0-9]+) games? this season\?$",
        title,
        flags=re.I,
    )

    if not m:
        return None, None

    team_raw = m.group(1).strip()
    threshold = int(m.group(2))

    return team_raw, threshold


def pull_win_totals(canonical_names, pulled_at):
    rows = []
    unmatched = []
    rejected = []

    for event in event_pages(WIN_TOTAL_SERIES):
        for market in event.get("markets", []) or []:
            ticker = str(market.get("ticker") or "")

            if "-26" not in ticker:
                continue

            team_raw, threshold = parse_win_total_team_and_threshold(market)

            if not team_raw or threshold is None:
                rejected.append({
                    "ticker": ticker,
                    "reason": "unparsed_title",
                    "title": market.get("title"),
                })
                continue

            team = canonical_team(team_raw, canonical_names)

            if not team:
                unmatched.append({
                    "ticker": ticker,
                    "team_raw": team_raw,
                })
                continue

            quote = base_quote(market, pulled_at)

            # "N+ wins" is equivalent to sportsbook Over (N - 0.5).
            # Buying NO is equivalent to Under (N - 0.5).
            rows.append({
                "domain": "win_totals",
                "season": 2026,
                "team": team,
                "team_raw": team_raw,
                "threshold_wins": threshold,
                "sportsbook_line": threshold - 0.5,
                "over": {
                    "kalshi_side": "YES",
                    "ask": quote["yes_ask"],
                    "ask_cents": quote["yes_ask_cents"],
                    "american_odds": quote["yes_american_odds"],
                },
                "under": {
                    "kalshi_side": "NO",
                    "ask": quote["no_ask"],
                    "ask_cents": quote["no_ask_cents"],
                    "american_odds": quote["no_american_odds"],
                },
                "market": quote,
            })

    return rows, unmatched, rejected


def pull_binary_team_series(
    *,
    series_ticker,
    domain,
    canonical_names,
    pulled_at,
    conference=None,
):
    rows = []
    unmatched = []

    for event in event_pages(series_ticker):
        for market in event.get("markets", []) or []:
            ticker = str(market.get("ticker") or "")

            if "-26" not in ticker:
                continue

            team_raw = (
                market.get("yes_sub_title")
                or ""
            )

            team = canonical_team(team_raw, canonical_names)

            if not team:
                unmatched.append({
                    "series_ticker": series_ticker,
                    "ticker": ticker,
                    "team_raw": team_raw,
                    "title": market.get("title"),
                })
                continue

            quote = base_quote(market, pulled_at)

            rows.append({
                "domain": domain,
                "season": 2026,
                "team": team,
                "team_raw": team_raw,
                "conference": conference,
                "series_ticker": series_ticker,
                "kalshi_side": "YES",
                "ask": quote["yes_ask"],
                "ask_cents": quote["yes_ask_cents"],
                "american_odds": quote["yes_american_odds"],
                "market": quote,
            })

    return rows, unmatched


def main():
    if not SEASON_MODEL.exists():
        raise SystemExit(f"Missing canonical team universe: {SEASON_MODEL}")

    season_model = json.loads(SEASON_MODEL.read_text())
    canonical_names = [
        x.get("team")
        for x in season_model.get("teams", [])
        if x.get("team")
    ]

    pulled_at = datetime.now(timezone.utc).isoformat()

    win_rows, win_unmatched, win_rejected = pull_win_totals(
        canonical_names,
        pulled_at,
    )

    cfp_rows, cfp_unmatched = pull_binary_team_series(
        series_ticker=CFP_SERIES,
        domain="make_cfp",
        canonical_names=canonical_names,
        pulled_at=pulled_at,
    )

    conference_rows = []
    conference_unmatched = []

    for conference, series_ticker in CONFERENCE_SERIES.items():
        rows, unmatched = pull_binary_team_series(
            series_ticker=series_ticker,
            domain="conference_titles",
            canonical_names=canonical_names,
            pulled_at=pulled_at,
            conference=conference,
        )

        conference_rows.extend(rows)
        conference_unmatched.extend(unmatched)

    payload = {
        "schema_version": "kalshi-ncaaf-futures-v1",
        "season": 2026,
        "pulled_at": pulled_at,
        "provider": "Kalshi",
        "price_policy": {
            "executable_buy_price": "ask",
            "display": "native cents + American-equivalent odds",
            "bid_usage": "provenance/liquidity only",
            "american_equivalent": "gross return before fees",
        },
        "series": {
            "win_totals": WIN_TOTAL_SERIES,
            "make_cfp": CFP_SERIES,
            "conference_titles": CONFERENCE_SERIES,
        },
        "win_totals": win_rows,
        "conference_titles": conference_rows,
        "make_cfp": cfp_rows,
        "audit": {
            "canonical_teams": len(canonical_names),
            "win_total_markets": len(win_rows),
            "conference_title_markets": len(conference_rows),
            "make_cfp_markets": len(cfp_rows),
            "win_total_unmatched": win_unmatched,
            "win_total_rejected": win_rejected,
            "conference_title_unmatched": conference_unmatched,
            "make_cfp_unmatched": cfp_unmatched,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print("wrote:", OUT)
    print("pulled_at:", pulled_at)
    print("win totals:", len(win_rows))
    print("conference titles:", len(conference_rows))
    print("make CFP:", len(cfp_rows))
    print("unmatched win totals:", len(win_unmatched))
    print("rejected win totals:", len(win_rejected))
    print("unmatched conference titles:", len(conference_unmatched))
    print("unmatched CFP:", len(cfp_unmatched))


if __name__ == "__main__":
    main()
