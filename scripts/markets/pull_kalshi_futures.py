#!/usr/bin/env python3
"""Pull and normalize current 2026 NCAAF Futures markets from Kalshi.

Domains:
- Win totals
- Conference titles
- Make CFP
- National championship

Kalshi remains a distinct provider internally.  Native ask prices are retained
in dollars/cents and converted to American-equivalent odds for comparison with
sportsbooks.

This puller uses public market-data endpoints only.  No account API key or
private key is required.
"""

from __future__ import annotations

import json
import math
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
NATIONAL_TITLE_SERIES = "KXNCAAF"
FEE_SCHEDULE_URL = "https://kalshi.com/docs/kalshi-fee-schedule.pdf"

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


def series_metadata(series_ticker: str) -> dict:
    return (get_json(f"/series/{series_ticker}").get("series") or {})


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


def kalshi_taker_fee(price, fee_type="quadratic", fee_multiplier=1):
    """Return the entry fee for one immediately matched contract.

    The official schedule defines the general taker fee as the next whole cent
    above 0.07 * C * P * (1-P).  We compare one contract because the UI quote
    is a per-contract executable ask.  Flat-fee markets are deliberately
    rejected rather than assigned an invented schedule.
    """
    p = decimal_price(price)
    multiplier = decimal_price(fee_multiplier)
    if p is None or multiplier is None:
        return None
    if fee_type not in {"quadratic", "quadratic_with_maker_fees"}:
        return None
    raw = 0.07 * multiplier * p * (1 - p)
    return math.ceil((raw - 1e-12) * 100) / 100


def american_from_cost(cost):
    """Convert total entry cost to held-to-settlement American odds."""
    p = decimal_price(cost)

    # 0¢ / 100¢ are not useful comparable executable return prices.
    if p is None or p <= 0 or p >= 1:
        return None

    if p < 0.5:
        return int(round(100 * (1 - p) / p))

    return int(round(-100 * p / (1 - p)))


def fee_terms(series: dict, event: dict) -> dict:
    fee_type = event.get("fee_type_override") or series.get("fee_type")
    multiplier = event.get("fee_multiplier_override")
    if multiplier is None:
        multiplier = series.get("fee_multiplier")
    return {"fee_type": fee_type, "fee_multiplier": multiplier}


def cents(p):
    p = decimal_price(p)
    return round(p * 100, 2) if p is not None else None


def canonical_team(raw, canonical_names):
    if not raw:
        return None
    return resolve_market_team(str(raw).strip(), canonical_names)


def side_quote(ask, fee_type, fee_multiplier):
    ask = decimal_price(ask)
    fee = kalshi_taker_fee(ask, fee_type, fee_multiplier)
    cost = round(ask + fee, 10) if ask is not None and fee is not None else None
    return {
        "ask": ask,
        "ask_cents": cents(ask),
        "entry_fee": fee,
        "entry_fee_cents": cents(fee),
        "effective_cost": cost,
        "american_odds": american_from_cost(cost),
    }


def base_quote(market: dict, pulled_at: str, terms: dict) -> dict:
    ya = decimal_price(market.get("yes_ask_dollars"))
    na = decimal_price(market.get("no_ask_dollars"))
    yb = decimal_price(market.get("yes_bid_dollars"))
    nb = decimal_price(market.get("no_bid_dollars"))

    yes = side_quote(ya, terms["fee_type"], terms["fee_multiplier"])
    no = side_quote(na, terms["fee_type"], terms["fee_multiplier"])
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
        "fee_type": terms["fee_type"],
        "fee_multiplier": terms["fee_multiplier"],
        "fee_schedule_url": FEE_SCHEDULE_URL,
        "yes_entry_fee": yes["entry_fee"],
        "yes_effective_cost": yes["effective_cost"],
        "yes_american_odds": yes["american_odds"],
        "no_entry_fee": no["entry_fee"],
        "no_effective_cost": no["effective_cost"],
        "no_american_odds": no["american_odds"],
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

    series = series_metadata(WIN_TOTAL_SERIES)
    for event in event_pages(WIN_TOTAL_SERIES):
        terms = fee_terms(series, event)
        for market in event.get("markets", []) or []:
            ticker = str(market.get("ticker") or "")

            if market.get("status") != "active":
                continue

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

            quote = base_quote(market, pulled_at, terms)

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
                    "entry_fee": quote["yes_entry_fee"],
                    "effective_cost": quote["yes_effective_cost"],
                    "american_odds": quote["yes_american_odds"],
                },
                "under": {
                    "kalshi_side": "NO",
                    "ask": quote["no_ask"],
                    "ask_cents": quote["no_ask_cents"],
                    "entry_fee": quote["no_entry_fee"],
                    "effective_cost": quote["no_effective_cost"],
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

    series = series_metadata(series_ticker)
    for event in event_pages(series_ticker):
        terms = fee_terms(series, event)
        for market in event.get("markets", []) or []:
            ticker = str(market.get("ticker") or "")

            if market.get("status") != "active":
                continue

            if domain != "national_title" and "-26" not in ticker:
                continue
            if domain == "national_title" and not str(event.get("event_ticker") or "").endswith("-27"):
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

            quote = base_quote(market, pulled_at, terms)

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
                "entry_fee": quote["yes_entry_fee"],
                "effective_cost": quote["yes_effective_cost"],
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

    national_rows, national_unmatched = pull_binary_team_series(
        series_ticker=NATIONAL_TITLE_SERIES,
        domain="national_title",
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
        "schema_version": "kalshi-ncaaf-futures-v2",
        "season": 2026,
        "pulled_at": pulled_at,
        "provider": "Kalshi",
        "price_policy": {
            "executable_buy_price": "ask",
            "display": "native cents + American-equivalent odds",
            "bid_usage": "provenance/liquidity only",
            "american_equivalent": "one-contract ask plus official taker entry fee; held to settlement",
            "fee_schedule_url": FEE_SCHEDULE_URL,
            "exit_fee": "not included",
        },
        "series": {
            "win_totals": WIN_TOTAL_SERIES,
            "make_cfp": CFP_SERIES,
            "national_title": NATIONAL_TITLE_SERIES,
            "conference_titles": CONFERENCE_SERIES,
        },
        "win_totals": win_rows,
        "conference_titles": conference_rows,
        "make_cfp": cfp_rows,
        "national_title": national_rows,
        "audit": {
            "canonical_teams": len(canonical_names),
            "win_total_markets": len(win_rows),
            "conference_title_markets": len(conference_rows),
            "make_cfp_markets": len(cfp_rows),
            "national_title_markets": len(national_rows),
            "win_total_unmatched": win_unmatched,
            "win_total_rejected": win_rejected,
            "conference_title_unmatched": conference_unmatched,
            "make_cfp_unmatched": cfp_unmatched,
            "national_title_unmatched": national_unmatched,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print("wrote:", OUT)
    print("pulled_at:", pulled_at)
    print("win totals:", len(win_rows))
    print("conference titles:", len(conference_rows))
    print("make CFP:", len(cfp_rows))
    print("national title:", len(national_rows))
    print("unmatched win totals:", len(win_unmatched))
    print("rejected win totals:", len(win_rejected))
    print("unmatched conference titles:", len(conference_unmatched))
    print("unmatched CFP:", len(cfp_unmatched))
    print("unmatched national title:", len(national_unmatched))


if __name__ == "__main__":
    main()
