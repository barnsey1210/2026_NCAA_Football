#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
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
POLICY_PATH = ROOT / "config/futures_market_policy.json"

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


def best_price(quotes, approved_books=None):
    candidates = []

    for book, quote in quotes.items():
        if approved_books is not None and book not in approved_books:
            continue

        price = clean_price(quote.get("price"))
        if price is not None:
            candidates.append((price, book))

    if not candidates:
        return None, None

    return max(candidates)


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


def main():
    sim = json.loads(SEASON_SIM.read_text())
    canonical_names = [x["team"] for x in sim["teams"]]

    policy = json.loads(POLICY_PATH.read_text())
    approved_books = set(policy.get("approved_executable_books", []))

    unmatched = {
        "win_totals": [],
        "conference_titles": [],
        "playoff_futures": [],
    }

    # ---------------- WIN TOTALS ----------------
    wins = defaultdict(dict)

    for row in read_csv(WIN_CURRENT):
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
            "source_url": row.get("source_url") or None,
            "source": "normalized win totals import",
        }

    win_rows = []
    for team in sorted(wins):
        quotes = wins[team]

        executable_quotes = {
            book: quote
            for book, quote in quotes.items()
            if book in approved_books
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
        })

    # ------------- CONFERENCE TITLES -------------
    conference = defaultdict(dict)

    for row in read_csv(CONF_CURRENT):
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
            "source_url": row.get("source_url") or None,
            "source": "normalized conference futures import",
        }

    conference_rows = []
    for team in sorted(conference):
        quotes = conference[team]
        best_all_price, best_all_book = best_price(quotes)
        best_exec_price, best_exec_book = best_price(
            quotes, approved_books
        )

        conference_rows.append({
            "team": team,
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
        })

    # ---------------- PLAYOFF FUTURES ----------------
    action = json.loads(PLAYOFF_CURRENT.read_text())
    action_books = {
        str(k): v for k, v in action.get("books", {}).items()
    }

    playoff_domains = {}

    for market_key in ("make_cfp", "national_title"):
        market = action.get("markets", {}).get(market_key, {})
        teams = {
            str(x.get("id")): x
            for x in market.get("teams", [])
        }
        options = market.get("rules", {}).get("options", {})

        grouped = defaultdict(dict)

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
                    unmatched["playoff_futures"].append(
                        raw_team.get("display_name")
                        or raw_team.get("full_name")
                    )
                    continue

                price = clean_price(odd.get("money"))
                if price is None:
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

                key = f"{team}|{option}"
                prior = grouped[key].get(book)

                quote = {
                    "price": price,
                    "implied_probability": implied(price),
                    "pulled_at": action.get("pulled_at"),
                    "source": "Action Network",
                }

                if prior is None or price > prior["price"]:
                    grouped[key][book] = quote

        rows = []

        for key in sorted(grouped):
            team, option = key.rsplit("|", 1)
            quotes = grouped[key]
            best_all_price, best_all_book = best_price(quotes)
            best_exec_price, best_exec_book = best_price(
                quotes, approved_books
            )

            rows.append({
                "team": team,
                "outcome": option,
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

        playoff_domains[market_key] = {
            "source": "Action Network",
            "pull_succeeded": bool(action.get("pull_succeeded")),
            "pulled_at": action.get("pulled_at"),
            "rows": rows,
        }

    payload = {
        "schema_version": "current-futures-market-2026-v1",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "season": 2026,
        "identity_source": "canonical 138-team universe + shared market resolver",
        "market_policy": {
            "schema_version": policy.get("schema_version"),
            "approved_executable_books": sorted(approved_books),
        },
        "win_totals": {
            "source": "normalized current win totals imports",
            "last_observed_date": newest(
                x["last_observed_date"] for x in win_rows
            ),
            "rows": win_rows,
        },
        "conference_titles": {
            "source": "normalized current conference futures import",
            "last_observed_date": newest(
                x["last_observed_date"] for x in conference_rows
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
