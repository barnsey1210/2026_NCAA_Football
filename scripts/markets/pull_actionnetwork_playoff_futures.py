#!/usr/bin/env python3
"""Pull and normalize current Action Network CFP and national-title markets."""
from datetime import datetime, timezone
from pathlib import Path
import json, re, urllib.request, urllib.parse

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/markets/action/action_playoff_futures_2026.json"
AVAILABLE = "https://api.actionnetwork.com/web/v1/leagues/2/futures/available"
BOOKS = "https://api.actionnetwork.com/web/v1/books"
CONFIG = ROOT / "config/action_network_futures.json"
WANTED = {
    "make_cfp": "ncaaf_futures_special_fixture_11018_2027_ncaaf_to_make_the_playoffs",
    "national_title": "ncaaf_futures_special_fixture_10986_2027_ncaaf_championship_to_win",
}

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)

def market_url(market_type, book_ids):
    query = urllib.parse.urlencode({"bookIds": ",".join(str(value) for value in book_ids)})
    return f"https://api.actionnetwork.com/web/v1/leagues/2/futures/{market_type}?{query}"

def brand(book):
    text = " ".join(str(book.get(k) or "") for k in ("display_name", "source_name", "abbr")).lower()
    for needle, label in (
        ("draftkings", "DraftKings"), ("betmgm", "BetMGM"), ("playmgm", "BetMGM"),
        ("fanduel", "FanDuel"), ("caesars", "Caesars"), ("bet365", "bet365"),
        ("betrivers", "BetRivers"), ("hard rock", "Hard Rock"),
        ("sports interaction", "Sports Interaction"),
    ):
        if needle in text:
            return label
    if re.search(r"\bdk\b", text):
        return "DraftKings"
    return str(book.get("display_name") or book.get("source_name") or "").strip()

def main():
    pulled_at = datetime.now(timezone.utc).isoformat()
    config = json.loads(CONFIG.read_text())
    requested_ids = [int(value) for value in config["book_ids"]]
    executable_ids = {int(key) for key, value in config["books"].items() if value.get("executable")}
    available = fetch(AVAILABLE)
    types = {x.get("type") for x in available.get("futures", [])}
    missing = sorted(set(WANTED.values()) - types)
    if missing:
        raise SystemExit("Action futures markets missing: " + ", ".join(missing))

    books_payload = fetch(BOOKS)
    book_metadata = {
        str(x.get("id")): {
            "brand": brand(x),
            "display_name": x.get("display_name"),
            "source_name": x.get("source_name"),
            "abbr": x.get("abbr"),
            "state": (str(x.get("display_name") or "").rsplit(" ", 1)[-1] if re.search(r" [A-Z]{2}$", str(x.get("display_name") or "")) else ""),
        }
        for x in books_payload.get("books", [])
        if x.get("id") is not None
    }
    books = {
        str(x.get("id")): brand(x)
        for x in books_payload.get("books", [])
        if x.get("id") is not None
    }

    markets = {}
    request_urls = {}
    for key, market_type in WANTED.items():
        request_urls[key] = market_url(market_type, requested_ids)
        markets[key] = fetch(request_urls[key])
        represented = {int(block["book_id"]) for block in markets[key].get("books", []) if block.get("book_id") is not None and block.get("odds")}
        if not represented.intersection(executable_ids):
            raise SystemExit(f"Action {key} returned no configured executable sportsbook rows; Consensus-only acquisition rejected")

    represented_book_ids = {
        str(book.get("book_id"))
        for market in markets.values()
        for book in market.get("books", [])
        if book.get("book_id") is not None
    }
    represented_books = sorted({
        books.get(book_id, f"Book {book_id}")
        for book_id in represented_book_ids
        if books.get(book_id, f"Book {book_id}").lower() != "consensus"
    })

    payload = {
        "schema_version": "action-playoff-futures-v2",
        "source": "Action Network",
        "pull_succeeded": True,
        "pulled_at": pulled_at,
        "endpoints": {
            "available": AVAILABLE,
            "books": BOOKS,
            "markets": WANTED,
            "market_request_urls": request_urls,
            "requested_book_ids": requested_ids,
        },
        "represented_books": represented_books,
        "books": books,
        "book_metadata": book_metadata,
        "markets": markets,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUT.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    temp.replace(OUT)

    print(OUT)
    print({
        "source": payload["source"],
        "pulled_at": pulled_at,
        "books": represented_books,
        "market_book_counts": {
            key: len(value.get("books", []))
            for key, value in markets.items()
        },
    })

if __name__ == "__main__":
    main()
