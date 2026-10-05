#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "scripts/site"
if str(SITE) not in sys.path:
    sys.path.insert(0, str(SITE))

from market_team_identity import resolve_market_team

# Code/config live in MAIN. Operational market/model artifacts live in AUTO.
# Default to the local repo so this also works normally after deployment into
# AUTO, while allowing canonical MAIN code to be validated against AUTO data.
DATA_ROOT = Path(
    os.environ.get("NCAAF_RUNTIME_ROOT", str(ROOT))
).expanduser().resolve()

SEASON_SIM = DATA_ROOT / "data/site/season_simulations_2026.json"
WIN_CURRENT = DATA_ROOT / "market_win_totals_import.csv"
CONF_CURRENT = DATA_ROOT / "market_conference_futures_import.csv"
PLAYOFF_CURRENT = DATA_ROOT / "data/markets/action/action_playoff_futures_2026.json"
KALSHI_CURRENT = DATA_ROOT / "data/markets/kalshi/kalshi_futures_2026.json"
POLICY_PATH = ROOT / "config/futures_market_policy.json"
ELIGIBILITY_PATH = ROOT / "config/futures_book_eligibility.json"

OUT = Path(
    os.environ.get(
        "NCAAF_FUTURES_CONTRACT_OUT",
        str(DATA_ROOT / "data/markets/current_futures_market_2026.json"),
    )
).expanduser().resolve()


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def clean_price(value):
    value = number(value)
    if value is None or value == 0 or abs(value) > 1_000_000:
        return None
    return int(value)


def implied(price):
    price = clean_price(price)
    if price is None:
        return None
    if price > 0:
        return 100 / (price + 100)
    return abs(price) / (abs(price) + 100)


def best_price(quotes, approved_books=None, *, eligible_only=True):
    candidates = []

    for book, quote in quotes.items():
        if approved_books is not None and book not in approved_books:
            continue
        if eligible_only and quote.get("eligible_for_best") is False:
            continue

        price = clean_price(quote.get("price"))
        if price is not None:
            candidates.append((price, book))

    if not candidates:
        return None, None

    return max(candidates)


def conference_segment(conference, eligibility):
    groups = eligibility.get("conference_classification", {})
    for segment in ("power", "g6", "non_power_other"):
        if conference in groups.get(segment, []):
            return segment
    raise ValueError(f"Unclassified canonical conference: {conference!r}")


def annotate_quotes(quotes, *, market_domain, segment, eligibility):
    exchanges = set(eligibility.get("exchanges", []))
    domain = eligibility.get("domains", {}).get(market_domain, {})
    rule = domain.get(segment, domain.get("all", {}))
    eligible = set(rule.get("eligible_sportsbooks", []))
    excluded = rule.get("excluded_sportsbooks", {})
    exchange_policy = eligibility.get("exchange_policy", {})

    for book, quote in quotes.items():
        quote["market_domain"] = market_domain
        quote["segment"] = segment
        if book in exchanges or quote.get("provider_type") == "exchange":
            quote["provider_type"] = "exchange"
            quote["eligible_for_best"] = False
            quote["eligible_for_edge"] = False
            quote["quote_status"] = exchange_policy.get("quote_status", "REFERENCE_ONLY")
            quote["exclusion_reason"] = exchange_policy.get("exclusion_reason", "EXCHANGE_REFERENCE_ONLY")
        elif book in eligible:
            quote["provider_type"] = "sportsbook"
            quote["eligible_for_best"] = True
            quote["eligible_for_edge"] = True
            quote["quote_status"] = "ELIGIBLE"
            quote["exclusion_reason"] = None
        else:
            quote["provider_type"] = "sportsbook"
            quote["eligible_for_best"] = False
            quote["eligible_for_edge"] = False
            quote["quote_status"] = "POLICY_EXCLUDED"
            quote["exclusion_reason"] = excluded.get(book, "SPORTSBOOK_NOT_ELIGIBLE_FOR_SEGMENT")
    return quotes


def iso_from_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)).replace(
            tzinfo=timezone.utc
        ).isoformat()
    except ValueError:
        return None


def newest(values):
    good = [x for x in values if x]
    return max(good) if good else None


def prior_executable_teams(path: Path, market_key: str) -> set[str]:
    """Read the prior on-disk contract before replacing it."""
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return set()
    return {
        row.get("team")
        for row in payload.get(market_key, {}).get("rows", [])
        if row.get("team")
        and row.get("outcome") in (None, "Yes")
        and row.get("executable_book_count")
    }


def apply_make_cfp_availability(
    canonical_names,
    rows,
    *,
    acquisition_succeeded,
    raw_executable_teams,
    unmatched_labels,
    prior_active_teams,
):
    """Make every canonical team inspectable without fabricating a quote."""
    yes_rows = {
        row.get("team"): row
        for row in rows
        if row.get("team") and row.get("outcome") in (None, "Yes")
    }
    has_unmatched = bool(unmatched_labels)
    for team in canonical_names:
        row = yes_rows.get(team)
        if row is not None and row.get("executable_book_count"):
            row["market_availability"] = "AVAILABLE"
            row["market_availability_reason"] = (
                "At least one approved executable provider currently lists Make CFP"
            )
            continue

        evidence = []
        if not acquisition_succeeded:
            evidence.append("approved provider acquisition did not succeed")
        if team in raw_executable_teams:
            evidence.append("approved raw provider row was lost before executable normalization")
        if has_unmatched:
            evidence.append("unmatched approved provider labels remain")

        state = "MISSING_FAILED" if evidence else "NOT_LISTED_BY_MARKET"
        reason = (
            "; ".join(evidence)
            if evidence
            else (
                "No approved executable provider currently offers a Make CFP price; "
                "prior listing is no longer present across successful current providers"
                if team in prior_active_teams
                else "No approved executable provider currently offers a Make CFP price"
            )
        )
        if row is None:
            row = {
                "team": team,
                "outcome": "Yes",
                "quotes": {},
                "books": [],
                "book_count": 0,
                "executable_books": [],
                "executable_book_count": 0,
                "best_observed_price": None,
                "best_observed_book": None,
                "best_executable_price": None,
                "best_executable_book": None,
                "pulled_at": None,
            }
            rows.append(row)
        row["market_availability"] = state
        row["market_availability_reason"] = reason

    rows.sort(key=lambda row: (row.get("team") or "", row.get("outcome") or ""))
    return rows


def current_kalshi_payload(path: Path, now=None, max_hours=26):
    """Return a fresh successful Kalshi payload, otherwise None (no carry-forward)."""
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
        stamp = datetime.fromisoformat(str(payload.get("pulled_at") or "").replace("Z", "+00:00"))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    now = now or datetime.now(timezone.utc)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    age = (now - stamp.astimezone(timezone.utc)).total_seconds() / 3600
    return payload if -0.25 <= age <= max_hours else None


def kalshi_quote(row, side=None):
    item = row.get(side) if side else row
    if not isinstance(item, dict) or clean_price(item.get("american_odds")) is None:
        return None
    market = row.get("market") or {}
    return {
        "price": clean_price(item.get("american_odds")),
        "implied_probability": implied(item.get("american_odds")),
        "native_ask_cents": item.get("ask_cents"),
        "entry_fee_cents": number(item.get("entry_fee")) * 100 if number(item.get("entry_fee")) is not None else None,
        "effective_cost": item.get("effective_cost"),
        "display": f"Kalshi {number(item.get('ask_cents')):g}¢ ({clean_price(item.get('american_odds')):+d})",
        "provider_type": "exchange",
        "ticker": market.get("ticker"),
        "pulled_at": market.get("pulled_at"),
        "source": market.get("source") or "Kalshi public market API",
        "fee_type": market.get("fee_type"),
        "fee_multiplier": market.get("fee_multiplier"),
        "fee_schedule_url": market.get("fee_schedule_url"),
    }


def main():
    sim = json.loads(SEASON_SIM.read_text())
    canonical_names = [x["team"] for x in sim["teams"]]
    team_conferences = {x["team"]: x.get("conference") for x in sim["teams"]}

    policy = json.loads(POLICY_PATH.read_text())
    eligibility = json.loads(ELIGIBILITY_PATH.read_text())
    approved_books = set(policy.get("approved_executable_books", []))
    provider_types = policy.get("provider_types", {})
    kalshi = current_kalshi_payload(KALSHI_CURRENT)

    unmatched = {
        "win_totals": [],
        "conference_titles": [],
        "playoff_futures": [],
        "make_cfp": [],
        "national_title": [],
    }

    # ---------------- WIN TOTALS ----------------
    wins = defaultdict(dict)

    # market_win_totals_import.csv also retains historical observations for
    # movement/history. Only rows observed today for the active season may
    # enter the current executable contract.
    active_season = 2026
    current_date = (
        datetime.now(timezone.utc)
        .astimezone(ZoneInfo("America/New_York"))
        .date()
        .isoformat()
    )

    win_source_rows = read_csv(WIN_CURRENT)

    for row in win_source_rows:
        try:
            row_season = int(float(str(row.get("season") or "").strip()))
        except (TypeError, ValueError):
            continue

        observed_date = str(row.get("snapshot_date") or "").strip()
        source_url = str(row.get("source_url") or "")

        if row_season != active_season:
            continue

        if observed_date != current_date:
            continue

        # Defense in depth: do not permit a provider URL that explicitly
        # identifies another season to masquerade as a 2026 quote.
        source_season_match = re.search(
            r"_([0-9]{4})_ncaaf_regular_season_total_wins",
            source_url,
            flags=re.I,
        )
        provider_market_season = re.match(
            r"^([0-9]{4})\b",
            str(row.get("market_identity") or "").strip(),
        )
        if (
            source_season_match
            and int(source_season_match.group(1)) != active_season
            and (
                provider_market_season is None
                or int(provider_market_season.group(1)) != active_season
            )
        ):
            continue

        team = resolve_market_team(row.get("team"), canonical_names)
        if not team:
            unmatched["win_totals"].append(row.get("team"))
            continue

        book = str(row.get("book") or "").strip()
        if not book:
            continue

        line = number(row.get("win_total"))
        over = clean_price(row.get("over_odds"))
        under = clean_price(row.get("under_odds"))

        if line is None or (over is None and under is None):
            continue

        wins[team][book] = {
            "number": line,
            "over_price": over,
            "under_price": under,
            "observed_date": row.get("snapshot_date"),
            "pulled_at": row.get("pulled_at") or None,
            "source_url": row.get("source_url") or None,
            "source": row.get("acquisition_source") or "normalized win totals import",
            "market_identity": row.get("market_identity") or None,
            "action_book_id": row.get("action_book_id") or None,
            "action_book_display_name": row.get("action_book_display_name") or None,
            "action_book_state": row.get("action_book_state") or None,
            "action_book_source_name": row.get("action_book_source_name") or None,
        }

    if kalshi:
        kalshi_win_rows = defaultdict(list)
        for row in kalshi.get("win_totals", []):
            team = resolve_market_team(row.get("team"), canonical_names)
            if not team:
                unmatched["win_totals"].append(row.get("team"))
                continue
            kalshi_win_rows[team].append(row)
        for team, candidate_rows in kalshi_win_rows.items():
            sportsbook_numbers = Counter(
                quote.get("number") for book, quote in wins.get(team, {}).items()
                if book != "Kalshi" and quote.get("number") is not None
            )
            if not sportsbook_numbers:
                continue
            reference_number = sportsbook_numbers.most_common(1)[0][0]
            matches = [
                row for row in candidate_rows
                if number(row.get("sportsbook_line")) == reference_number
            ]
            # Never guess among thresholds or compare unlike win-total lines.
            if len(matches) != 1:
                unmatched["win_totals"].append(
                    f"{team}: ambiguous Kalshi threshold for {reference_number}"
                )
                continue
            row = matches[0]
            over = kalshi_quote(row, "over")
            under = kalshi_quote(row, "under")
            if not over and not under:
                continue
            wins[team]["Kalshi"] = {
                "number": number(row.get("sportsbook_line")),
                "over_price": over.get("price") if over else None,
                "under_price": under.get("price") if under else None,
                "over_native_ask_cents": over.get("native_ask_cents") if over else None,
                "under_native_ask_cents": under.get("native_ask_cents") if under else None,
                "over_display": over.get("display") if over else None,
                "under_display": under.get("display") if under else None,
                "provider_type": "exchange",
                "pulled_at": (row.get("market") or {}).get("pulled_at"),
                "source": "Kalshi public market API",
                "market": row.get("market"),
            }

    win_rows = []
    for team in sorted(wins):
        quotes = wins[team]
        segment = conference_segment(team_conferences.get(team), eligibility)
        annotate_quotes(
            quotes,
            market_domain="win_totals",
            segment=segment,
            eligibility=eligibility,
        )

        executable_quotes = {
            book: quote
            for book, quote in quotes.items()
            if book in approved_books and quote.get("eligible_for_best") is True
        }

        over_candidates = [
            (
                (-quote["number"], quote.get("over_price") or -1_000_000),
                book,
                quote,
            )
            for book, quote in executable_quotes.items()
            if quote.get("over_price") is not None
        ]

        under_candidates = [
            (
                (quote["number"], quote.get("under_price") or -1_000_000),
                book,
                quote,
            )
            for book, quote in executable_quotes.items()
            if quote.get("under_price") is not None
        ]

        best_over = max(
            over_candidates,
            default=(None, None, None),
        )
        best_under = max(
            under_candidates,
            default=(None, None, None),
        )

        numbers = {}
        for quote in executable_quotes.values():
            n = quote["number"]
            numbers[n] = numbers.get(n, 0) + 1

        reference_number = (
            max(numbers, key=lambda n: numbers[n])
            if numbers
            else None
        )

        win_rows.append({
            "team": team,
            "market_domain": "win_totals",
            "segment": segment,
            "quotes": quotes,
            "books": sorted(quotes),
            "book_count": len(quotes),
            "executable_books": sorted(executable_quotes),
            "executable_book_count": len(executable_quotes),
            "best_over": (
                {"book": best_over[1], **best_over[2]}
                if best_over[2]
                else None
            ),
            "best_under": (
                {"book": best_under[1], **best_under[2]}
                if best_under[2]
                else None
            ),
            "reference_number": reference_number,
            "last_observed_date": newest(
                q.get("observed_date") for q in quotes.values()
            ),
            "pulled_at": newest(
                q.get("pulled_at") for q in quotes.values()
            ),
        })

    # ------------- CONFERENCE TITLES -------------
    conference = defaultdict(dict)

    for row in read_csv(CONF_CURRENT):
        try:
            row_season = int(float(str(row.get("season") or "").strip()))
        except (TypeError, ValueError):
            continue

        observed_date = str(row.get("snapshot_date") or "").strip()

        if row_season != active_season:
            continue

        if observed_date != current_date:
            continue

        team = resolve_market_team(row.get("team"), canonical_names)
        if not team:
            unmatched["conference_titles"].append(row.get("team"))
            continue

        book = str(row.get("book") or "").strip()
        price = clean_price(row.get("american_odds"))
        if not book or price is None:
            continue

        conference[team][book] = {
            "price": price,
            "implied_probability": implied(price),
            "observed_date": row.get("snapshot_date"),
            "pulled_at": row.get("pulled_at") or None,
            "source_url": row.get("source_url") or None,
            "source": row.get("acquisition_source") or "normalized conference futures import",
            "market_identity": row.get("market_identity") or None,
            "action_book_id": row.get("action_book_id") or None,
            "action_book_display_name": row.get("action_book_display_name") or None,
            "action_book_state": row.get("action_book_state") or None,
            "action_book_source_name": row.get("action_book_source_name") or None,
        }

    if kalshi:
        for row in kalshi.get("conference_titles", []):
            team = resolve_market_team(row.get("team"), canonical_names)
            quote = kalshi_quote(row)
            if team and quote:
                conference[team]["Kalshi"] = quote
            elif row.get("team"):
                unmatched["conference_titles"].append(row.get("team"))

    conference_rows = []
    for team in sorted(conference):
        quotes = conference[team]
        segment = conference_segment(team_conferences.get(team), eligibility)
        annotate_quotes(
            quotes,
            market_domain="conference_titles",
            segment=segment,
            eligibility=eligibility,
        )
        best_all_price, best_all_book = best_price(quotes, eligible_only=False)
        best_exec_price, best_exec_book = best_price(
            quotes, approved_books
        )

        conference_rows.append({
            "team": team,
            "market_domain": "conference_titles",
            "segment": segment,
            "quotes": quotes,
            "books": sorted(quotes),
            "book_count": len(quotes),
            "executable_books": sorted(
                b for b in quotes if b in approved_books
            ),
            "executable_book_count": sum(
                1 for b in quotes if b in approved_books
            ),
            "best_observed_price": best_all_price,
            "best_observed_book": best_all_book,
            "best_executable_price": best_exec_price,
            "best_executable_book": best_exec_book,
            "last_observed_date": newest(
                q.get("observed_date") for q in quotes.values()
            ),
            "pulled_at": newest(
                q.get("pulled_at") for q in quotes.values()
            ),
        })

    # ---------------- PLAYOFF FUTURES ----------------
    action = json.loads(PLAYOFF_CURRENT.read_text())
    action_books = {
        str(k): v for k, v in action.get("books", {}).items()
    }
    action_book_metadata = action.get("book_metadata", {})

    playoff_domains = {}
    prior_active_by_domain = {
        key: prior_executable_teams(OUT, key)
        for key in ("make_cfp", "national_title")
    }

    for market_key in ("make_cfp", "national_title"):
        market = action.get("markets", {}).get(market_key, {})
        teams = {
            str(x.get("id")): x
            for x in market.get("teams", [])
        }
        options = market.get("rules", {}).get("options", {})

        grouped = defaultdict(dict)
        raw_executable_teams = set()

        for block in market.get("books", []):
            bid = str(block.get("book_id"))
            book = action_books.get(bid) or f"Book {bid}"

            if str(book).lower() == "consensus":
                continue

            for odd in block.get("odds", []):
                raw_team = teams.get(str(odd.get("team_id")), {})
                team = resolve_market_team(
                    raw_team.get("display_name")
                    or raw_team.get("full_name")
                    or raw_team.get("location"),
                    canonical_names,
                )
                if not team:
                    raw_label = raw_team.get("display_name") or raw_team.get("full_name")
                    if raw_label:
                        unmatched["playoff_futures"].append(raw_label)
                        unmatched[market_key].append(raw_label)
                    continue

                option = options.get(
                    str(odd.get("option_type_id")), {}
                ).get("option_type")

                if market_key == "make_cfp":
                    if option is None:
                        option = "Yes"
                    if option not in {"Yes", "No"}:
                        continue
                else:
                    option = "Yes"

                if book in approved_books and option == "Yes":
                    raw_executable_teams.add(team)

                price = clean_price(odd.get("money"))
                if price is None:
                    continue

                key = f"{team}|{option}"
                prior = grouped[key].get(book)

                quote = {
                    "price": price,
                    "implied_probability": implied(price),
                    "pulled_at": action.get("pulled_at"),
                    "source": "Action Network",
                    "market_identity": market.get("name"),
                    "action_book_id": int(bid) if bid.isdigit() else bid,
                    "action_book_display_name": (action_book_metadata.get(bid) or {}).get("display_name"),
                    "action_book_state": (action_book_metadata.get(bid) or {}).get("state"),
                    "action_book_source_name": (action_book_metadata.get(bid) or {}).get("source_name"),
                }

                if prior is None or price > prior["price"]:
                    grouped[key][book] = quote

        rows = []

        for key in sorted(grouped):
            team, option = key.rsplit("|", 1)
            quotes = grouped[key]
            annotate_quotes(
                quotes,
                market_domain=market_key,
                segment="all",
                eligibility=eligibility,
            )
            best_all_price, best_all_book = best_price(quotes, eligible_only=False)
            best_exec_price, best_exec_book = best_price(
                quotes, approved_books
            )

            rows.append({
                "team": team,
                "outcome": option,
                "market_domain": market_key,
                "segment": "all",
                "quotes": quotes,
                "books": sorted(quotes),
                "book_count": len(quotes),
                "executable_books": sorted(
                    b for b in quotes if b in approved_books
                ),
                "executable_book_count": sum(
                    1 for b in quotes if b in approved_books
                ),
                "best_observed_price": best_all_price,
                "best_observed_book": best_all_book,
                "best_executable_price": best_exec_price,
                "best_executable_book": best_exec_book,
                "pulled_at": action.get("pulled_at"),
            })

        if kalshi:
            by_key = {(row["team"], row["outcome"]): row for row in rows}
            for source_row in kalshi.get(market_key, []):
                team = resolve_market_team(source_row.get("team"), canonical_names)
                outcome = "Yes"
                quote = kalshi_quote(source_row)
                if not team or not quote:
                    if source_row.get("team"):
                        unmatched["playoff_futures"].append(source_row.get("team"))
                        unmatched[market_key].append(source_row.get("team"))
                    continue
                target = by_key.get((team, outcome))
                if target is None:
                    target = {"team": team, "outcome": outcome, "quotes": {}}
                    rows.append(target)
                    by_key[(team, outcome)] = target
                target["quotes"]["Kalshi"] = quote

            for row in rows:
                quotes = row["quotes"]
                annotate_quotes(
                    quotes,
                    market_domain=market_key,
                    segment="all",
                    eligibility=eligibility,
                )
                best_all_price, best_all_book = best_price(quotes, eligible_only=False)
                best_exec_price, best_exec_book = best_price(quotes, approved_books)
                row.update({
                    "books": sorted(quotes),
                    "book_count": len(quotes),
                    "executable_books": sorted(b for b in quotes if b in approved_books),
                    "executable_book_count": sum(1 for b in quotes if b in approved_books),
                    "best_observed_price": best_all_price,
                    "best_observed_book": best_all_book,
                    "best_executable_price": best_exec_price,
                    "best_executable_book": best_exec_book,
                    "pulled_at": newest(q.get("pulled_at") for q in quotes.values()),
                })

        if market_key == "make_cfp":
            rows = apply_make_cfp_availability(
                canonical_names,
                rows,
                acquisition_succeeded=bool(action.get("pull_succeeded")),
                raw_executable_teams=raw_executable_teams,
                unmatched_labels=unmatched[market_key],
                prior_active_teams=prior_active_by_domain[market_key],
            )

        playoff_domains[market_key] = {
            "source": "Action Network",
            "pull_succeeded": bool(action.get("pull_succeeded")),
            "pulled_at": action.get("pulled_at"),
            "rows": rows,
        }

    payload = {
        "schema_version": "current-futures-market-2026-v2",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "season": 2026,
        "identity_source": "canonical 138-team universe + shared market resolver",
        "market_policy": {
            "schema_version": policy.get("schema_version"),
            "book_eligibility_schema_version": eligibility.get("schema_version"),
            "approved_executable_books": sorted(approved_books),
            "sportsbooks": eligibility.get("sportsbooks", []),
            "exchanges": eligibility.get("exchanges", []),
            "conference_classification": eligibility.get("conference_classification", {}),
            "domains": eligibility.get("domains", {}),
            "provider_types": provider_types,
            "kalshi_status": "current" if kalshi else "unavailable_or_stale",
        },
        "win_totals": {
            "source": "normalized current win totals imports",
            "last_observed_date": newest(
                x["last_observed_date"] for x in win_rows
            ),
            "pulled_at": newest(
                x.get("pulled_at") for x in win_rows
            ),
            "rows": win_rows,
        },
        "conference_titles": {
            "source": "normalized current conference futures import",
            "last_observed_date": newest(
                x["last_observed_date"] for x in conference_rows
            ),
            "pulled_at": newest(
                x.get("pulled_at") for x in conference_rows
            ),
            "rows": conference_rows,
        },
        "make_cfp": playoff_domains["make_cfp"],
        "national_title": playoff_domains["national_title"],
        "audit": {
            "canonical_teams": len(canonical_names),
            "win_total_teams": len(win_rows),
            "conference_title_teams": len(conference_rows),
            "unmatched": {
                k: sorted(set(x for x in values if x))
                for k, values in unmatched.items()
            },
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print("wrote:", OUT)
    print(json.dumps(payload["audit"], indent=2))


if __name__ == "__main__":
    main()
