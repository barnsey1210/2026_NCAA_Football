#!/usr/bin/env python3
"""Build the scoped production Odds Screen V2 futures payload."""

from __future__ import annotations

import csv
import json
import math
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from team_identity import team_logo_path

ROOT = Path(__file__).resolve().parents[2]
ACTION = ROOT / "data/markets/action/action_playoff_futures_2026.json"
FUTURES_VIEW = ROOT / "data/site/futures_view.json"
CONF_CURRENT = ROOT / "market_conference_futures_import.csv"
CONF_HISTORY = ROOT / "market_conference_futures_history.csv"
WINS_CURRENT = ROOT / "market_win_totals_import.csv"
WINS_HISTORY = ROOT / "market_win_totals_history.csv"
TITLE_OPEN = ROOT / "actionnetwork_futures_raw_clean.csv"
OUT = ROOT / "data/site/odds_futures_v2.json"
AUDIT = ROOT / "data/audits/odds_futures_v2_build_audit.json"
BOOKS = ("DraftKings", "FanDuel", "BetMGM", "Caesars")


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def source_build_time(paths: tuple[Path, ...]) -> str:
    """Return a stable build timestamp derived from the newest canonical input."""
    modified = max(path.stat().st_mtime for path in paths if path.exists())
    return datetime.fromtimestamp(modified, timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def clean_price(value):
    value = number(value)
    return int(value) if value is not None and value != 0 and abs(value) <= 1_000_000 else None


def norm(value: str | None) -> str:
    value = (value or "").lower().replace("&", "and").replace("hawai'i", "hawaii")
    value = re.sub(r"\b(cardinals|tigers|bulldogs|wildcats|crimson tide|buckeyes|ducks|longhorns|fighting irish|nittany lions|hurricanes|aggies|rebels|volunteers|wolverines|broncos|horned frogs|red raiders|cougars|seminoles|panthers|yellow jackets|razorbacks|gamecocks|hokies|cavaliers|wolfpack|wolf pack|mountaineers|bears|knights|mustangs|utes|cyclones|jayhawks|terrapins|spartans|boilermakers|badgers|cornhuskers|golden gophers|scarlet knights|demon deacons|orange|blue devils|tar heels|golden bears|sun devils|huskies|buffaloes|beavers|cardinal)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    aliases = {
        "ohio st": "ohio state", "penn st": "penn state", "florida st": "florida state",
        "miami fl": "miami florida", "miami": "miami florida", "nc state": "north carolina state",
        "ole miss": "mississippi", "ok state": "oklahoma state", "k state": "kansas state",
        "ga tech": "georgia tech", "va tech": "virginia tech", "s florida": "south florida",
        "e carolina": "east carolina", "n illinois": "northern illinois", "w michigan": "western michigan",
        "n mexico st": "new mexico state", "app state": "appalachian state", "central fl": "central florida",
        "unc": "north carolina", "fl atlantic": "florida atlantic", "michigan st": "michigan state",
        "fiu": "florida international", "jax state": "jacksonville state", "jacksonville st": "jacksonville state",
        "middle tenn": "middle tennessee", "missouri st": "missouri state", "w kentucky": "western kentucky",
        "c michigan": "central michigan", "e michigan": "eastern michigan", "sac state": "sacramento state",
        "sacramento st": "sacramento state", "umass": "massachusetts", "nd state": "north dakota state",
        "north dakota st": "north dakota state", "oregon st": "oregon state", "washington st": "washington state",
        "mississippi st": "mississippi state", "s carolina": "south carolina", "coastal car": "coastal carolina",
        "ga southern": "georgia southern", "la monroe": "ul monroe", "louisiana monroe": "ul monroe", "louisiana monroe warhawks": "ul monroe",
        "s alabama": "south alabama", "appalachian st": "appalachian state", "arkansas st": "arkansas state",
        "ball st": "ball state", "boise st": "boise state", "colorado st": "colorado state",
        "fresno st": "fresno state", "georgia st": "georgia state", "kent st": "kent state",
        "new mexico st": "new mexico state", "san diego st": "san diego state", "san jose st": "san jose state",
        "texas st": "texas state", "uconn": "connecticut", "wv": "west virginia", "la tech": "louisiana tech",
        "ucf": "central florida", "jmu": "james madison", "uab": "uab", "uab blazers": "uab",
        "arkansas state red wolves": "arkansas state", "kennesaw st": "kennesaw state",
        "texas state bobcats": "texas state", "umass minutemen": "massachusetts",
    }
    cleaned = " ".join(value.split())
    return aliases.get(cleaned, cleaned)


def implied(price):
    price = clean_price(price)
    if price is None:
        return None
    return 100 / (price + 100) if price > 0 else abs(price) / (abs(price) + 100)


def team_meta(rows: list[dict]) -> tuple[dict, dict]:
    by_norm, aliases = {}, {}
    for row in rows:
        meta = {
            "team": row.get("team"), "slug": row.get("slug"), "conference": row.get("conference"),
            "logo": team_logo_path(row.get("team")),
            "model": {
                "national_title": number(row.get("national_title_model_prob")),
                "playoff_yes": number(row.get("playoff_model_prob")),
                "conference_title": number(row.get("title_model_prob")),
            },
        }
        by_norm[norm(row.get("team"))] = meta
        aliases[row.get("team")] = meta
    return by_norm, aliases


def resolve(name, by_norm):
    key = norm(name)
    exact = by_norm.get(key)
    if exact:
        return exact
    # Raw brand exports sometimes append a mascot or truncate the canonical
    # school name. Only accept a unique prefix relationship.
    candidates = [meta for canonical, meta in by_norm.items()
                  if len(key) >= 3 and (key.startswith(canonical + " ") or canonical.startswith(key + " "))]
    return candidates[0] if len(candidates) == 1 else None


def best_price(quotes: dict) -> tuple[int | None, str | None]:
    candidates = [(q.get("price"), book) for book, q in quotes.items() if clean_price(q.get("price")) is not None]
    return max(candidates) if candidates else (None, None)


def build_action(action: dict, key: str, by_norm: dict, pulled_at: str) -> tuple[list[dict], dict]:
    market = action["markets"][key]
    teams = {int(t["id"]): t for t in market.get("teams", [])}
    book_names = {int(k): v for k, v in action.get("books", {}).items()}
    option_names = {int(k): v.get("option_type") for k, v in market.get("rules", {}).get("options", {}).items()}
    grouped = defaultdict(dict)
    duplicates = 0
    malformed = 0
    for block in market.get("books", []):
        book = book_names.get(int(block.get("book_id")))
        if book not in BOOKS:
            continue
        for odd in block.get("odds", []):
            team = teams.get(int(odd.get("team_id") or -1))
            price = clean_price(odd.get("money"))
            if not team or price is None:
                malformed += 1
                continue
            meta = resolve(team.get("display_name") or team.get("full_name"), by_norm)
            if not meta:
                continue
            outcome = option_names.get(int(odd.get("option_type_id") or -1)) if key == "make_cfp" else "Yes"
            # The retained Action response labels FanDuel's make-CFP outcomes as
            # Yes; several other brand feeds omit option_type_id but contain the
            # same one-price-per-team market. Treat those unlabelled rows as Yes,
            # and never manufacture a No quote.
            if key == "make_cfp" and outcome is None:
                outcome = "Yes"
            if key == "make_cfp" and outcome not in {"Yes", "No"}:
                continue
            group_key = (meta["team"], outcome)
            prior = grouped[group_key].get(book)
            if prior:
                duplicates += 1
            if not prior or price > prior["price"]:
                grouped[group_key][book] = {"price": price, "updated_at": pulled_at, "source": "Action Network retained feed"}
    rows = []
    for (team, outcome), quotes in sorted(grouped.items()):
        meta = resolve(team, by_norm)
        best, best_book = best_price(quotes)
        model = meta["model"]["national_title"] if key == "national_title" else meta["model"]["playoff_yes"]
        if key == "make_cfp" and outcome == "No" and model is not None:
            model = 1 - model
        market_prob = implied(best)
        rows.append({**{k: meta[k] for k in ("team", "slug", "conference", "logo")}, "outcome": outcome,
                     "quotes": quotes, "best_price": best, "best_book": best_book,
                     "best_highlight_eligible": len(quotes) >= 2,
                     "market_implied_probability": market_prob, "model_probability": model,
                     "edge": model - market_prob if model is not None and market_prob is not None else None,
                     "last_updated": pulled_at})
    return rows, {"duplicate_brand_team_outcomes_collapsed_to_best_price": duplicates, "malformed_rows": malformed}


def earliest_by_team(rows: list[dict], price_field: str) -> dict:
    found = {}
    for row in sorted(rows, key=lambda r: (r.get("snapshot_date") or "9999", r.get("book") or "")):
        if row.get("book") not in BOOKS or clean_price(row.get(price_field)) is None:
            continue
        key = norm(row.get("team"))
        found.setdefault(key, {"price": clean_price(row.get(price_field)), "book": row.get("book"),
                               "observed_at": row.get("snapshot_date"),
                               "note": "Earliest retained local snapshot; actual sportsbook posting time may be earlier"})
    return found


def attach_title_open(rows: list[dict], source: list[dict]) -> int:
    openers = earliest_by_team(source, "american_odds")
    count = 0
    for row in rows:
        row["open"] = openers.get(norm(row["team"]))
        count += row["open"] is not None
    return count


def build_conference(current: list[dict], history: list[dict], by_norm: dict) -> tuple[list[dict], dict]:
    grouped = defaultdict(dict)
    duplicates = 0
    malformed = 0
    unmatched = Counter()
    for row in current:
        if row.get("book") not in BOOKS:
            continue
        meta = resolve(row.get("team"), by_norm)
        price = clean_price(row.get("american_odds"))
        if not meta:
            unmatched[row.get("team") or ""] += 1
            continue
        if price is None:
            malformed += 1
            continue
        key = meta["team"]
        if row["book"] in grouped[key]:
            duplicates += 1
        grouped[key][row["book"]] = {"price": price, "updated_at": row.get("snapshot_date"), "source": "normalized conference futures import"}
    openers = earliest_by_team(history, "american_odds")
    output = []
    for team, quotes in sorted(grouped.items()):
        meta = resolve(team, by_norm)
        best, book = best_price(quotes)
        market_prob = implied(best)
        model = meta["model"]["conference_title"]
        output.append({**{k: meta[k] for k in ("team", "slug", "conference", "logo")}, "outcome": "Yes", "quotes": quotes,
                       "open": openers.get(norm(team)), "best_price": best, "best_book": book,
                       "best_highlight_eligible": len(quotes) >= 2,
                       "market_implied_probability": market_prob, "model_probability": model,
                       "edge": model - market_prob if model is not None and market_prob is not None else None,
                       "last_updated": max((q["updated_at"] or "" for q in quotes.values()), default=None)})
    return output, {"duplicates": duplicates, "malformed_rows": malformed, "unmatched_teams": dict(unmatched)}


def build_wins(current: list[dict], history: list[dict], by_norm: dict) -> tuple[list[dict], dict]:
    grouped = defaultdict(dict)
    duplicates = malformed = 0
    unmatched = Counter()
    for row in current:
        if row.get("book") not in BOOKS:
            continue
        meta = resolve(row.get("team"), by_norm)
        line, over, under = number(row.get("win_total")), clean_price(row.get("over_odds")), clean_price(row.get("under_odds"))
        if not meta:
            unmatched[row.get("team") or ""] += 1
            continue
        if line is None or (over is None and under is None):
            malformed += 1
            continue
        if row["book"] in grouped[meta["team"]]:
            duplicates += 1
        grouped[meta["team"]][row["book"]] = {"number": line, "over_price": over, "under_price": under,
            "updated_at": row.get("snapshot_date"), "source": "normalized win totals import"}
    first = {}
    for row in sorted(history, key=lambda r: (r.get("snapshot_date") or "9999", r.get("book") or "")):
        if row.get("book") not in BOOKS:
            continue
        line = number(row.get("win_total")); over = clean_price(row.get("over_odds")); under = clean_price(row.get("under_odds"))
        if line is None or (over is None and under is None):
            continue
        first.setdefault(norm(row.get("team")), {"number": line, "over_price": over, "under_price": under,
            "book": row.get("book"), "observed_at": row.get("snapshot_date"),
            "note": "Earliest retained local snapshot; actual sportsbook posting time may be earlier"})
    output = []
    for team, quotes in sorted(grouped.items()):
        meta = resolve(team, by_norm)
        over_candidates = [((-(q["number"]), q.get("over_price") or -1_000_000), b, q) for b, q in quotes.items() if q.get("over_price") is not None]
        under_candidates = [((q["number"], q.get("under_price") or -1_000_000), b, q) for b, q in quotes.items() if q.get("under_price") is not None]
        bo = max(over_candidates, default=(None, None, None)); bu = max(under_candidates, default=(None, None, None))
        numbers = Counter(q["number"] for q in quotes.values())
        reference_number = numbers.most_common(1)[0][0] if numbers else None
        output.append({**{k: meta[k] for k in ("team", "slug", "conference", "logo")}, "quotes": quotes,
            "open": first.get(norm(team)),
            "best_over": ({"book": bo[1], **bo[2]} if bo[2] else None),
            "best_under": ({"book": bu[1], **bu[2]} if bu[2] else None),
            "best_over_highlight_eligible": len(over_candidates) >= 2,
            "best_under_highlight_eligible": len(under_candidates) >= 2,
            "reference_number": reference_number,
            "last_updated": max((q["updated_at"] or "" for q in quotes.values()), default=None)})
    return output, {"duplicates": duplicates, "malformed_rows": malformed, "unmatched_teams": dict(unmatched)}


def coverage(rows: list[dict]) -> dict:
    return {book: sum(book in row.get("quotes", {}) for row in rows) for book in BOOKS}


def main() -> None:
    sources = [ACTION, FUTURES_VIEW, CONF_CURRENT, CONF_HISTORY, WINS_CURRENT, WINS_HISTORY, TITLE_OPEN]
    missing = [str(p.relative_to(ROOT)) for p in sources if not p.exists()]
    if missing:
        raise SystemExit("Missing read-only inputs: " + ", ".join(missing))
    action = json.loads(ACTION.read_text())
    view = json.loads(FUTURES_VIEW.read_text())
    by_norm, _ = team_meta(view.get("rows", []))
    pulled = action.get("pulled_at")
    playoff, playoff_audit = build_action(action, "make_cfp", by_norm, pulled)
    national, national_audit = build_action(action, "national_title", by_norm, pulled)
    title_open_count = attach_title_open(national, read_csv(TITLE_OPEN))
    conference, conference_audit = build_conference(read_csv(CONF_CURRENT), read_csv(CONF_HISTORY), by_norm)
    wins, wins_audit = build_wins(read_csv(WINS_CURRENT), read_csv(WINS_HISTORY), by_norm)
    heisman = {
        "available": False,
        "message": "Heisman odds are not yet available in the current normalized futures pipeline.",
        "required_pipeline": "Extend the Action Network futures reader from https://api.actionnetwork.com/web/v1/leagues/2/futures/available to ingest market ncaaf_futures_special_fixture_11016_2027_ncaaf_heisman_trophy_winner with player ID/name, team/position, book ID/name, American price, and pull timestamp. Historical audit-page text is not used as current odds.",
    }
    built_at = source_build_time((ACTION, FUTURES_VIEW, CONF_CURRENT, CONF_HISTORY, WINS_CURRENT, WINS_HISTORY, TITLE_OPEN))
    payload = {
        "schema_version": "odds-futures-v2-production-1", "prototype_only": False, "built_at": built_at,
        "books": list(BOOKS), "history_scope": "Open is the earliest retained normalized local snapshot when available; full futures history is intentionally deferred.",
        "categories": {"national_title": national, "playoff": playoff, "conference_title": conference, "win_totals": wins},
        "heisman": heisman,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(OUT, payload)
    audit = {
        "schema_version": "odds-futures-v2-build-audit-1", "prototype_only": False, "built_at": built_at,
        "output": str(OUT.relative_to(ROOT)),
        "inputs": [
            {"file": str(ACTION.relative_to(ROOT)), "fields": ["markets.*.books[].book_id", "markets.*.books[].odds[].team_id", "option_type_id", "money", "pulled_at"], "use": "current book-specific CFP and national title"},
            {"file": str(FUTURES_VIEW.relative_to(ROOT)), "fields": ["team", "slug", "conference", "*_model_prob"], "use": "canonical team identity plus existing model probabilities/edges"},
            {"file": str(CONF_CURRENT.relative_to(ROOT)), "fields": ["snapshot_date", "team", "conference", "book", "american_odds"], "use": "current conference title"},
            {"file": str(CONF_HISTORY.relative_to(ROOT)), "fields": ["snapshot_date", "team", "book", "american_odds"], "use": "earliest retained conference title snapshot only"},
            {"file": str(WINS_CURRENT.relative_to(ROOT)), "fields": ["snapshot_date", "team", "conference", "book", "win_total", "over_odds", "under_odds"], "use": "current win totals"},
            {"file": str(WINS_HISTORY.relative_to(ROOT)), "fields": ["snapshot_date", "team", "book", "win_total", "over_odds", "under_odds"], "use": "earliest retained win total snapshot only"},
            {"file": str(TITLE_OPEN.relative_to(ROOT)), "fields": ["snapshot_date", "team", "book", "american_odds"], "use": "earliest retained national-title snapshot"},
        ],
        "coverage": {
            "national_title": {"rows": len(national), "books": coverage(national), "opener_rows": title_open_count, "last_update_rows": sum(bool(r.get("last_updated")) for r in national), "model_rows": sum(r.get("model_probability") is not None for r in national), "edge_rows": sum(r.get("edge") is not None for r in national)},
            "playoff": {"rows": len(playoff), "books": coverage(playoff), "opener_rows": 0, "last_update_rows": sum(bool(r.get("last_updated")) for r in playoff), "model_rows": sum(r.get("model_probability") is not None for r in playoff), "edge_rows": sum(r.get("edge") is not None for r in playoff)},
            "conference_title": {"rows": len(conference), "books": coverage(conference), "opener_rows": sum(r.get("open") is not None for r in conference), "last_update_rows": sum(bool(r.get("last_updated")) for r in conference), "model_rows": sum(r.get("model_probability") is not None for r in conference), "edge_rows": sum(r.get("edge") is not None for r in conference)},
            "win_totals": {"rows": len(wins), "books": coverage(wins), "opener_rows": sum(r.get("open") is not None for r in wins), "last_update_rows": sum(bool(r.get("last_updated")) for r in wins)},
            "heisman": heisman,
        },
        "quality": {"national_title": national_audit, "playoff": playoff_audit, "conference_title": conference_audit, "win_totals": wins_audit},
        "history": {"full_history_built": False, "reason": "Current board plus earliest retained open only; full book-level futures history is not available in normalized sources"},
        "production_files_unchanged": True,
        "files_written": [str(OUT.relative_to(ROOT)), str(AUDIT.relative_to(ROOT))],
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(AUDIT, audit)
    print(f"Built {OUT.relative_to(ROOT)}: national={len(national)}, playoff={len(playoff)}, conference={len(conference)}, wins={len(wins)}")


if __name__ == "__main__":
    main()
