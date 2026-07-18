#!/usr/bin/env python3
from pathlib import Path
import json
import csv
import re
from datetime import datetime, timezone


SITE_BOOKS = {"draftkings", "fanduel", "betmgm", "caesars"}

RAW = Path("data/markets/sgo/sgo_ncaaf_events_curl_raw.json")
OUT = Path("data/markets/sgo/sgo_ncaaf_game_odds.csv")
AUDIT = Path("data/audit/sgo_ncaaf_game_odds_audit.csv")

def strip_headers(raw):
    if "\r\n\r\n" in raw:
        return raw.split("\r\n\r\n", 1)[1]
    if "\n\n" in raw:
        return raw.split("\n\n", 1)[1]
    return raw

def to_float(v):
    if v is None:
        return None
    s = str(v).strip().replace("+", "")
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None

def to_int(v):
    if v is None:
        return None
    s = str(v).strip().replace("+", "")
    if s == "":
        return None
    try:
        return int(float(s))
    except Exception:
        return None

def team_name(e, side):
    return (
        e.get("teams", {})
         .get(side, {})
         .get("names", {})
         .get("long")
    )

def norm_team(t):
    if not t:
        return ""
    s = str(t)
    s = s.replace("Hawai'i", "Hawaii")
    s = s.replace("Miami", "Miami-FL") if s == "Miami" else s
    s = s.replace("San José State", "San Jose State")
    return s

def latest_book(entries, value_key):
    """
    Pick available book row with freshest update.
    Fallback to any row if no available rows.
    """
    candidates = []
    for book, b in (entries or {}).items():
        if book not in SITE_BOOKS:
            continue
        val = b.get(value_key)
        odds = b.get("odds")
        if val is None:
            continue
        candidates.append({
            "book": book,
            "value": val,
            "odds": odds,
            "last_updated": b.get("lastUpdatedAt"),
            "available": bool(b.get("available")),
        })

    if not candidates:
        return None

    avail = [c for c in candidates if c["available"]]
    pool = avail if avail else candidates

    def key(c):
        return c.get("last_updated") or ""

    return sorted(pool, key=key, reverse=True)[0]

def best_book_by_value(entries, value_key, prefer):
    """
    For spread:
      prefer='home' means best home line from home bettor perspective = highest home spread.
      prefer='away' means best away line from away bettor perspective = highest away spread.
    For totals:
      prefer='over' means lowest total.
      prefer='under' means highest total.
    """
    candidates = []
    for book, b in (entries or {}).items():
        if book not in SITE_BOOKS:
            continue
        val = to_float(b.get(value_key))
        if val is None:
            continue
        if not bool(b.get("available")):
            continue
        candidates.append({
            "book": book,
            "value": val,
            "odds": to_int(b.get("odds")),
            "last_updated": b.get("lastUpdatedAt"),
        })

    if not candidates:
        return None

    if prefer in ("home", "away"):
        return sorted(candidates, key=lambda c: (c["value"], c.get("last_updated") or ""), reverse=True)[0]
    if prefer == "over":
        return sorted(candidates, key=lambda c: (c["value"], c.get("last_updated") or ""))[0]
    if prefer == "under":
        return sorted(candidates, key=lambda c: (c["value"], c.get("last_updated") or ""), reverse=True)[0]
    return candidates[0]

def fmt_spread(team, spread):
    if spread is None:
        return None
    if abs(spread) < 1e-9:
        return f"{team} PK"
    return f"{team} {spread:+g}"

def main():
    raw = RAW.read_text(errors="ignore")
    body = strip_headers(raw)
    data = json.loads(body)
    events = data.get("data", []) if isinstance(data, dict) else data

    rows = []
    pulled_at = datetime.now(timezone.utc).isoformat()

    for e in events:
        if e.get("leagueID") != "NCAAF":
            continue

        home = norm_team(team_name(e, "home"))
        away = norm_team(team_name(e, "away"))
        starts_at = e.get("status", {}).get("startsAt")
        date = starts_at[:10] if starts_at else None
        week = e.get("info", {}).get("seasonWeek")

        odds = e.get("odds", {}) or {}

        away_sp = odds.get("points-away-game-sp-away", {})
        home_sp = odds.get("points-home-game-sp-home", {})
        over = odds.get("points-all-game-ou-over", {})
        under = odds.get("points-all-game-ou-under", {})
        away_ml = odds.get("points-away-game-ml-away", {})
        home_ml = odds.get("points-home-game-ml-home", {})

        latest_home_sp = latest_book(home_sp.get("byBookmaker", {}), "spread")
        latest_away_sp = latest_book(away_sp.get("byBookmaker", {}), "spread")
        latest_over = latest_book(over.get("byBookmaker", {}), "overUnder")
        latest_under = latest_book(under.get("byBookmaker", {}), "overUnder")
        latest_home_ml = latest_book(home_ml.get("byBookmaker", {}), "odds")
        latest_away_ml = latest_book(away_ml.get("byBookmaker", {}), "odds")

        # Home perspective spread. Example Stanford -3.5 => market_spread_home = -3.5.
        home_spread = to_float(latest_home_sp["value"]) if latest_home_sp else to_float(home_sp.get("bookSpread"))
        away_spread = to_float(latest_away_sp["value"]) if latest_away_sp else to_float(away_sp.get("bookSpread"))

        # If home spread missing but away spread exists, invert it.
        if home_spread is None and away_spread is not None:
            home_spread = -away_spread

        # SGO includes the first posted number when includeOpenCloseOdds=true.
        # Store it in the same home-team perspective used by current spreads.
        home_open_spread = to_float(home_sp.get("openBookSpread"))
        away_open_spread = to_float(away_sp.get("openBookSpread"))
        if home_open_spread is None and away_open_spread is not None:
            home_open_spread = -away_open_spread

        market_spread_text = fmt_spread(home if home_spread is not None and home_spread <= 0 else away, home_spread if home_spread is not None and home_spread <= 0 else away_spread)

        total = to_float(latest_over["value"]) if latest_over else to_float(over.get("bookOverUnder"))
        if total is None:
            total = to_float(latest_under["value"]) if latest_under else to_float(under.get("bookOverUnder"))

        total_open = to_float(over.get("openBookOverUnder"))
        if total_open is None:
            total_open = to_float(under.get("openBookOverUnder"))

        best_home = best_book_by_value(home_sp.get("byBookmaker", {}), "spread", "home")
        best_away = best_book_by_value(away_sp.get("byBookmaker", {}), "spread", "away")
        best_over = best_book_by_value(over.get("byBookmaker", {}), "overUnder", "over")
        best_under = best_book_by_value(under.get("byBookmaker", {}), "overUnder", "under")

        rows.append({
            "source": "SportsGameOdds",
            "pulled_at": pulled_at,
            "sgo_event_id": e.get("eventID"),
            "date": date,
            "start_time_utc": starts_at,
            "week": week,
            "away_team": away,
            "home_team": home,

            "market_spread_home": home_spread,
            "market_spread_open_home": home_open_spread,
            "market_spread_text": market_spread_text,
            "market_spread_book": latest_home_sp["book"] if latest_home_sp else None,
            "market_spread_price": to_int(latest_home_sp["odds"]) if latest_home_sp else None,
            "market_spread_last_update": latest_home_sp["last_updated"] if latest_home_sp else None,

            "market_best_home_spread_home": to_float(best_home["value"]) if best_home else None,
            "market_best_home_spread_text": fmt_spread(home, to_float(best_home["value"])) if best_home else None,
            "market_best_home_spread_price": to_int(best_home["odds"]) if best_home else None,
            "market_best_home_spread_book": best_home["book"] if best_home else None,

            "market_best_away_spread_home": -to_float(best_away["value"]) if best_away and to_float(best_away["value"]) is not None else None,
            "market_best_away_spread_text": fmt_spread(away, to_float(best_away["value"])) if best_away else None,
            "market_best_away_spread_price": to_int(best_away["odds"]) if best_away else None,
            "market_best_away_spread_book": best_away["book"] if best_away else None,

            "market_total": total,
            "market_total_open": total_open,
            "market_total_book": latest_over["book"] if latest_over else latest_under["book"] if latest_under else None,
            "market_total_over_price": to_int(latest_over["odds"]) if latest_over else None,
            "market_total_under_price": to_int(latest_under["odds"]) if latest_under else None,
            "market_total_last_update": latest_over["last_updated"] if latest_over else latest_under["last_updated"] if latest_under else None,

            "market_best_over_total": to_float(best_over["value"]) if best_over else None,
            "market_best_over_price": to_int(best_over["odds"]) if best_over else None,
            "market_best_over_book": best_over["book"] if best_over else None,

            "market_best_under_total": to_float(best_under["value"]) if best_under else None,
            "market_best_under_price": to_int(best_under["odds"]) if best_under else None,
            "market_best_under_book": best_under["book"] if best_under else None,

            "market_home_moneyline": to_int(latest_home_ml["value"]) if latest_home_ml else None,
            "market_home_moneyline_book": latest_home_ml["book"] if latest_home_ml else None,
            "market_away_moneyline": to_int(latest_away_ml["value"]) if latest_away_ml else None,
            "market_away_moneyline_book": latest_away_ml["book"] if latest_away_ml else None,

            "market_books_available": ",".join(sorted((e.get("links", {}).get("bookmakers", {}) or {}).keys())),
            "market_price_status": "actual" if (home_spread is not None or total is not None) else "missing",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    audit_rows = [
        {"metric": "events", "value": len(rows)},
        {"metric": "events_with_spread", "value": sum(1 for r in rows if r["market_spread_home"] not in (None, ""))},
        {"metric": "events_with_open_spread", "value": sum(1 for r in rows if r["market_spread_open_home"] not in (None, ""))},
        {"metric": "events_with_total", "value": sum(1 for r in rows if r["market_total"] not in (None, ""))},
        {"metric": "events_with_open_total", "value": sum(1 for r in rows if r["market_total_open"] not in (None, ""))},
        {"metric": "events_with_moneyline", "value": sum(1 for r in rows if r["market_home_moneyline"] not in (None, "") or r["market_away_moneyline"] not in (None, ""))},
    ]
    with AUDIT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(audit_rows)

    print("wrote:", OUT, "rows:", len(rows))
    print("wrote:", AUDIT)
    for r in audit_rows:
        print(r["metric"], r["value"])

    print("\nHawaii / Stanford:")
    for r in rows:
        if r["away_team"] == "Hawaii" and r["home_team"] == "Stanford":
            for k, v in r.items():
                print(k, "=", v)

if __name__ == "__main__":
    main()
