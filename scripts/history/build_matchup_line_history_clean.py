from pathlib import Path
import re
import json
import math
import pandas as pd
from datetime import datetime, timezone

INDEX = Path("index.html")
OUT = Path("data/history/matchup_line_history_clean.csv")

SOURCES = [
    Path("data/odds/game_line_history.csv"),
    Path("data/history/game_line_model_history.csv"),
    Path("data/odds/actionnetwork_season_game_lines_2026.csv"),
    Path("data/markets/sgo/sgo_ncaaf_game_odds.csv"),
    Path("data/odds/season_game_lines_2026.csv"),
]

TEAM_ALIASES = {
    "hawai i": "hawaii",
    "hawaii rainbow warriors": "hawaii",
    "stanford cardinal": "stanford",
    "north dakota state bison": "north dakota state",
    "jacksonville state gamecocks": "jacksonville state",
    "sacramento state hornets": "sacramento state",
    "eastern michigan eagles": "eastern michigan",
}


def canonical_team_norm(raw, site_norms):
    """
    Resolve raw market team names to site team names.
    Handles mascot suffixes like:
    Akron Zips -> Akron
    Wake Forest Demon Deacons -> Wake Forest
    Texas Tech Red Raiders -> Texas Tech
    """
    v = norm_team(raw)
    if not v:
        return v

    # Exact site team match.
    if v in site_norms:
        return v

    # Mascot suffix / longer raw display name.
    candidates = []
    for site in site_norms:
        if not site:
            continue
        if v.startswith(site + " "):
            candidates.append(site)

    if candidates:
        # Prefer longest site name, e.g. "new mexico state" before "new mexico".
        return sorted(candidates, key=len, reverse=True)[0]

    # Some feeds may reverse the containment pattern.
    candidates = []
    for site in site_norms:
        if site.startswith(v + " "):
            candidates.append(site)

    if candidates:
        return sorted(candidates, key=len, reverse=True)[0]

    return v


def norm_team(x):
    v = re.sub(r"[^a-z0-9]+", " ", str(x or "").lower()).strip()
    return TEAM_ALIASES.get(v, v)

def clean_date(x):
    if x is None or pd.isna(x) or str(x).strip() == "":
        return None
    s = str(x).strip()
    # Prefer YYYY-MM-DD if present.
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", s)
    if m:
        return m.group(1)
    try:
        return pd.to_datetime(s, utc=True).date().isoformat()
    except Exception:
        return None

def clean_ts(x):
    if x is None or pd.isna(x) or str(x).strip() == "":
        return None
    try:
        return pd.to_datetime(x, utc=True).isoformat()
    except Exception:
        return str(x)

def fnum(x):
    try:
        if x is None or pd.isna(x) or str(x).strip() == "":
            return None
        v = float(x)
        if math.isnan(v):
            return None
        return round(v, 4)
    except Exception:
        return None

def load_site_db():
    s = INDEX.read_text(errors="ignore")
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', s, flags=re.S)
    if not m:
        raise SystemExit("index.html DB not found")
    db = json.loads(m.group(1))
    games = db.get("games", [])
    by_pair_date = {}
    by_pair = {}
    for g in games:
        gid = str(g.get("game_id"))
        away = g.get("away_team")
        home = g.get("home_team")
        date = clean_date(g.get("date"))
        key = (norm_team(away), norm_team(home), date)
        key2 = (norm_team(away), norm_team(home))
        by_pair_date[key] = g
        by_pair.setdefault(key2, g)
    return db, by_pair_date, by_pair

def map_game_id(row, by_pair_date, by_pair):
    away = row.get("away_team")
    home = row.get("home_team")
    d = clean_date(row.get("date") or row.get("game_date") or row.get("start_time_utc") or row.get("commence_time"))
    key = (norm_team(away), norm_team(home), d)
    g = by_pair_date.get(key)
    if not g:
        g = by_pair.get((norm_team(away), norm_team(home)))
    if not g:
        return None, d, away, home, None, None
    return str(g.get("game_id")), clean_date(g.get("date")), g.get("away_team"), g.get("home_team"), g.get("week"), g.get("conference") or g.get("conf")

def read_source(path, by_pair_date, by_pair):
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    if df.empty:
        return pd.DataFrame()

    rows = []
    source_name = path.name

    for _, r in df.iterrows():
        gid, game_date, away, home, site_week, site_conf = map_game_id(r, by_pair_date, by_pair)
        if not gid:
            continue

        snapshot_date = (
            clean_date(r.get("snapshot_date"))
            or clean_date(r.get("snapshot_ts"))
            or clean_date(r.get("pulled_at"))
            or clean_date(r.get("market_spread_last_update"))
            or clean_date(r.get("market_total_last_update"))
            or datetime.now(timezone.utc).date().isoformat()
        )

        snapshot_ts = (
            clean_ts(r.get("snapshot_ts"))
            or clean_ts(r.get("pulled_at"))
            or clean_ts(r.get("market_spread_last_update"))
            or clean_ts(r.get("market_total_last_update"))
            or snapshot_date
        )

        rows.append({
            "snapshot_date": snapshot_date,
            "snapshot_ts": snapshot_ts,
            "source_file": str(path),
            "source": str(r.get("source") or r.get("market_line_source") or source_name),
            "game_id": gid,
            "game_date": game_date,
            "week": fnum(site_week if site_week is not None else (r.get("week") or r.get("game_week"))),
            "conference": site_conf,
            "away_team": away,
            "home_team": home,

            "market_spread_home": fnum(r.get("market_spread_home")),
            "market_spread_open_home": fnum(r.get("market_spread_open_home")),
            "market_spread_text": r.get("market_spread_text") if "market_spread_text" in r.index else None,
            "market_spread_price": fnum(r.get("market_spread_price")),
            "market_spread_book": r.get("market_spread_book") if "market_spread_book" in r.index else None,
            "market_spread_last_update": clean_ts(r.get("market_spread_last_update")),

            "market_total": fnum(r.get("market_total")),
            "market_total_open": fnum(r.get("market_total_open")),
            "market_total_book": r.get("market_total_book") if "market_total_book" in r.index else None,
            "market_total_over_price": fnum(r.get("market_total_over_price")),
            "market_total_under_price": fnum(r.get("market_total_under_price")),
            "market_total_last_update": clean_ts(r.get("market_total_last_update")),

            "projected_margin_home": fnum(r.get("projected_margin_home")),
            "model_spread_home": fnum(r.get("model_spread_home")),
            "projected_total": fnum(r.get("projected_total")),

            "books_available": r.get("books_available") if "books_available" in r.index else r.get("market_books_available") if "market_books_available" in r.index else None,
        })

    return pd.DataFrame(rows)

def main():
    db, by_pair_date, by_pair = load_site_db()

    parts = []
    for p in SOURCES:
        got = read_source(p, by_pair_date, by_pair)
        if not got.empty:
            print(p, "rows:", len(got), "games:", got["game_id"].nunique())
            parts.append(got)

    if not parts:
        raise SystemExit("no source line history found")

    hist = pd.concat(parts, ignore_index=True)

    # Fill current model fields from current site DB when source row does not have model fields.
    game_by_id = {str(g.get("game_id")): g for g in db.get("games", [])}
    for i, r in hist.iterrows():
        g = game_by_id.get(str(r["game_id"]))
        if not g:
            continue

        if pd.isna(hist.at[i, "projected_margin_home"]):
            hist.at[i, "projected_margin_home"] = fnum(g.get("projected_margin_home"))

        if pd.isna(hist.at[i, "model_spread_home"]):
            pmh = fnum(hist.at[i, "projected_margin_home"])
            hist.at[i, "model_spread_home"] = None if pmh is None else round(-pmh, 4)

        if pd.isna(hist.at[i, "projected_total"]):
            hist.at[i, "projected_total"] = fnum(g.get("projected_total"))

    # Remove duplicate same-day same-game same-source-ish snapshots, keep latest timestamp.
    hist["_sort_ts"] = pd.to_datetime(hist["snapshot_ts"], errors="coerce", utc=True)
    hist = hist.sort_values(["game_id", "snapshot_date", "_sort_ts"])
    dedupe_cols = [
        "game_id", "snapshot_date", "source",
        "market_spread_home", "market_total",
        "market_spread_book", "market_total_book"
    ]
    hist = hist.drop_duplicates(subset=dedupe_cols, keep="last").copy()

    # Prefer one row per game/date for the chart:
    # 1) has spread/total
    # 2) has real prices
    # 3) SportsGameOdds / Action before CFBD-only rows
    # 4) latest timestamp
    source_priority = {
        "SportsGameOdds": 1,
        "sgo_ncaaf_game_odds.csv": 1,
        "Action Network": 2,
        "actionnetwork_season_game_lines_2026.csv": 2,
        "CFBD Lines": 3,
        "The Odds API": 4,
    }

    hist["_priority"] = hist["source"].map(source_priority).fillna(9)
    hist["_has_spread"] = hist["market_spread_home"].notna().astype(int)
    hist["_has_total"] = hist["market_total"].notna().astype(int)

    def has_price(row):
        vals = [
            row.get("market_spread_price"),
            row.get("market_total_over_price"),
            row.get("market_total_under_price"),
        ]
        for v in vals:
            try:
                if pd.notna(v) and float(v) != 0:
                    return 1
            except Exception:
                pass
        return 0

    hist["_has_price"] = hist.apply(has_price, axis=1)

    hist = hist.sort_values(
        ["game_id", "snapshot_date", "_has_spread", "_has_total", "_has_price", "_priority", "_sort_ts"],
        ascending=[True, True, False, False, False, True, False]
    )

    chart = hist.drop_duplicates(subset=["game_id", "snapshot_date"], keep="first").copy()

    chart = chart.drop(columns=[c for c in ["_sort_ts", "_priority", "_has_spread", "_has_total"] if c in chart.columns])
    chart = chart.sort_values(["game_id", "snapshot_date"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    chart.to_csv(OUT, index=False)

    print()
    print("wrote:", OUT)
    print("rows:", len(chart))
    print("games:", chart["game_id"].nunique())
    print("snapshot dates:", chart["snapshot_date"].min(), "to", chart["snapshot_date"].max())
    print("snapshots per game:")
    print(chart.groupby("game_id").size().value_counts().sort_index().to_string())

if __name__ == "__main__":
    main()
