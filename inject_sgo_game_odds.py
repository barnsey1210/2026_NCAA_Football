#!/usr/bin/env python3
from pathlib import Path
import json, re, html
import pandas as pd
import math
from datetime import datetime, timedelta

CSV = Path("data/markets/sgo/sgo_ncaaf_game_odds.csv")
FILES = [Path("index.html"), Path("matchup.html")]

CLEAR_FIELDS = [
    "market_spread_home",
    "market_spread_open_home",
    "market_spread_text",
    "market_formatted_spread",
    "market_spread_book",
    "market_spread_price",
    "market_spread_last_update",
    "market_line_source",
    "market_pulled_at",
    "market_spread_display_side",
    "market_spread_display_team",

    "market_best_home_spread_home",
    "market_best_home_spread_text",
    "market_best_home_spread_price",
    "market_best_home_spread_book",

    "market_best_away_spread_home",
    "market_best_away_spread_text",
    "market_best_away_spread_price",
    "market_best_away_spread_book",

    "market_total",
    "market_total_book",
    "market_total_over_price",
    "market_total_under_price",
    "market_total_last_update",

    "market_best_over_total",
    "market_best_over_price",
    "market_best_over_book",

    "market_best_under_total",
    "market_best_under_price",
    "market_best_under_book",

    "market_home_moneyline",
    "market_home_moneyline_book",
    "market_away_moneyline",
    "market_away_moneyline_book",

    "market_books_count",
    "market_books_available",
    "market_price_status",
    "market_line_note",
]

def clean(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, float):
        if math.isnan(v):
            return None
        if v.is_integer():
            return int(v)
    if isinstance(v, str):
        v = v.strip()
        if v == "" or v.lower() == "nan":
            return None
    return v

def norm_team(t):
    s = str(t or "").strip()

    aliases = {
        "Hawai'i": "Hawaii",
        "San José State": "San Jose State",
        "Miami": "Miami-FL",
        "Miami (FL)": "Miami-FL",
        "Miami Florida": "Miami-FL",
        "Miami (OH)": "Miami-OH",
        "UMass": "Massachusetts",
        "UL Monroe": "UL-Monroe",
        "Louisiana Monroe": "UL-Monroe",
        "James Madison": "JMU",
    }

    s = aliases.get(s, s)
    return re.sub(r"\s+", " ", s).lower()

def key(date, away, home):
    return (str(date)[:10], norm_team(away), norm_team(home))

def date_offsets(date):
    d = str(date)[:10]
    out = [d]
    try:
        dt = datetime.strptime(d, "%Y-%m-%d")
        out.append((dt - timedelta(days=1)).strftime("%Y-%m-%d"))
        out.append((dt + timedelta(days=1)).strftime("%Y-%m-%d"))
    except Exception:
        pass
    return out

def find_sgo_row(sgo, date, away, home):
    a = norm_team(away)
    h = norm_team(home)
    for d in date_offsets(date):
        r = sgo.get((d, a, h))
        if r is not None:
            return r
    return None

def extract_db(s):
    m = re.search(r'<script[^>]+id=["\']db["\'][^>]*>([\s\S]*?)</script>', s, flags=re.I)
    if not m:
        return None, None, None
    raw = html.unescape(m.group(1).strip())
    db = json.loads(raw)
    return db, m.start(1), m.end(1)

def replace_db(s, start, end, db):
    raw = json.dumps(db, ensure_ascii=False, separators=(",", ":"))
    return s[:start] + raw + s[end:]

def american_to_implied_prob(odds):
    try:
        o = float(odds)
    except Exception:
        return None
    if o < 0:
        return abs(o) / (abs(o) + 100.0)
    if o > 0:
        return 100.0 / (o + 100.0)
    return None

def spread_hold_pct(home_price, away_price):
    hp = american_to_implied_prob(home_price)
    ap = american_to_implied_prob(away_price)
    if hp is None or ap is None:
        return None
    return round((hp + ap - 1.0) * 100.0, 2)

def fmt_side_from_home_spread(home, away, home_spread):
    if home_spread is None:
        return None, None
    try:
        x = float(home_spread)
    except Exception:
        return None, None
    if abs(x) < 1e-9:
        return "pick", "PK"
    if x < 0:
        return "home", home
    return "away", away

def main():
    if not CSV.exists():
        raise SystemExit(f"Missing {CSV}")

    df = pd.read_csv(CSV)
    sgo = {}
    for _, r in df.iterrows():
        sgo[key(r.get("date"), r.get("away_team"), r.get("home_team"))] = r.to_dict()

    print("SGO rows:", len(sgo))

    for path in FILES:
        if not path.exists():
            print("skip missing:", path)
            continue

        s = path.read_text(errors="ignore")
        db, start, end = extract_db(s)

        if db is None:
            print("skip no db:", path)
            continue

        games = db.get("games", [])
        matched = 0
        cleared = 0

        for g in games:
            r = find_sgo_row(sgo, g.get("date"), g.get("away_team"), g.get("home_team"))

            for f in CLEAR_FIELDS:
                g.pop(f, None)

            if not r:
                g["market_price_status"] = "missing"
                g["market_line_source"] = None
                g["market_line_note"] = "No SportsGameOdds market returned for this game."
                cleared += 1
                continue

            matched += 1

            away = g.get("away_team")
            home = g.get("home_team")

            vals = {
                "market_spread_home": clean(r.get("market_spread_home")),
                "market_spread_text": clean(r.get("market_spread_text")),
                "market_spread_book": clean(r.get("market_spread_book")),
                "market_spread_price": clean(r.get("market_spread_price")),
                "market_spread_last_update": clean(r.get("market_spread_last_update")),

                "market_best_home_spread_home": clean(r.get("market_best_home_spread_home")),
                "market_best_home_spread_text": clean(r.get("market_best_home_spread_text")),
                "market_best_home_spread_price": clean(r.get("market_best_home_spread_price")),
                "market_best_home_spread_book": clean(r.get("market_best_home_spread_book")),

                "market_best_away_spread_home": clean(r.get("market_best_away_spread_home")),
                "market_best_away_spread_text": clean(r.get("market_best_away_spread_text")),
                "market_best_away_spread_price": clean(r.get("market_best_away_spread_price")),
                "market_best_away_spread_book": clean(r.get("market_best_away_spread_book")),

                "market_total": clean(r.get("market_total")),
                "market_total_book": clean(r.get("market_total_book")),
                "market_total_over_price": clean(r.get("market_total_over_price")),
                "market_total_under_price": clean(r.get("market_total_under_price")),
                "market_total_last_update": clean(r.get("market_total_last_update")),

                "market_best_over_total": clean(r.get("market_best_over_total")),
                "market_best_over_price": clean(r.get("market_best_over_price")),
                "market_best_over_book": clean(r.get("market_best_over_book")),

                "market_best_under_total": clean(r.get("market_best_under_total")),
                "market_best_under_price": clean(r.get("market_best_under_price")),
                "market_best_under_book": clean(r.get("market_best_under_book")),

                "market_home_moneyline": clean(r.get("market_home_moneyline")),
                "market_home_moneyline_book": clean(r.get("market_home_moneyline_book")),
                "market_away_moneyline": clean(r.get("market_away_moneyline")),
                "market_away_moneyline_book": clean(r.get("market_away_moneyline_book")),

                "market_books_available": clean(r.get("market_books_available")),
                "market_price_status": "actual",
                "market_line_source": "SportsGameOdds",
                "market_pulled_at": clean(r.get("pulled_at")),
                "sgo_event_id": clean(r.get("sgo_event_id")),
            }

            for kk, vv in vals.items():
                g[kk] = vv

            side, team = fmt_side_from_home_spread(home, away, g.get("market_spread_home"))
            g["market_spread_display_side"] = side
            g["market_spread_display_team"] = team

            books = str(g.get("market_books_available") or "")
            g["market_books_count"] = len([b for b in books.split(",") if b.strip()])

            hold = spread_hold_pct(g.get("market_best_home_spread_price"), g.get("market_best_away_spread_price"))
            if hold is not None:
                g["market_spread_hold_pct"] = hold
                g["market_spread_hold_label"] = f"Hold +{hold:.1f}%"

            if g.get("market_spread_home") is None and g.get("market_total") is None:
                g["market_price_status"] = "missing"
                g["market_line_note"] = "SportsGameOdds event matched, but no spread or total was returned."

        out = replace_db(s, start, end, db)
        path.write_text(out)

        print(path)
        print("  games:", len(games))
        print("  matched SGO:", matched)
        print("  cleared/no SGO:", cleared)

if __name__ == "__main__":
    main()
