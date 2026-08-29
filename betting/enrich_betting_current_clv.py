#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import json
import math
import re
import pandas as pd

ROOT = Path.cwd()
BETS = ROOT / "data" / "bets" / "bets_enriched.csv"
DASH = ROOT / "data" / "bets" / "betting_dashboard.json"
AUDIT = ROOT / "data" / "bets" / "market_clv_match_audit.csv"

if not BETS.exists():
    raise SystemExit("Missing data/bets/bets_enriched.csv")
if not DASH.exists():
    raise SystemExit("Missing data/bets/betting_dashboard.json")

TEAM_ALIASES = {
    "smu": "SMU",
    "boise": "Boise State",
    "boise state": "Boise State",
    "uconn": "UConn",
    "connecticut": "UConn",
    "miami oh": "Miami-OH",
    "miami ohio": "Miami-OH",
    "miami-oh": "Miami-OH",
    "miami o": "Miami-OH",
    "miami redhawks": "Miami-OH",
    "miami-oh redhawks": "Miami-OH",
    "unlv": "UNLV",
    "ole miss": "Ole Miss",
    "iowa state": "Iowa State",
    "georgia tech": "Georgia Tech",
    "ohio state": "Ohio State",
    "texas tech": "Texas Tech",
    "north dakota state": "North Dakota State",
    "north dakota st": "North Dakota State",
    "north dakota st.": "North Dakota State",
    "ndsu": "North Dakota State",
    "missouri st": "Missouri State",
    "missouri state": "Missouri State",
    "cal": "California",
    "california": "California",
    "southern miss": "Southern Miss",
    "texas state": "Texas State",
    "texas st": "Texas State",
    "texas st.": "Texas State",
    "tx state": "Texas State",
    "james madison": "James Madison",
    "jmu": "James Madison",
    "western kentucky": "Western Kentucky",
    "western ky": "Western Kentucky",
    "w kentucky": "Western Kentucky",
    "wku": "Western Kentucky",
    "navy": "Navy",
    "oregon": "Oregon",
    "georgia": "Georgia",
    "auburn": "Auburn",
    "colorado": "Colorado",
    "duke": "Duke",
    "duke blue devils": "Duke",
    "usc": "USC",
    "nmst": "New Mexico State",
    "nmsu": "New Mexico State",
    "new mexico state": "New Mexico State",
    "chatanooga": "Chattanooga",
    "chattanooga": "Chattanooga",
}

BOOK_ALIASES = {
    "fan duel": "FanDuel",
    "fanduel": "FanDuel",
    "draft kings": "DraftKings",
    "draftkings": "DraftKings",
    "dk": "DraftKings",
    "mgm": "MGM",
    "betmgm": "MGM",
    "caesars": "Caesars",
    "espn bet": "ESPN BET",
}

def clean_key(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    s = str(x).strip().lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def normalize_team(x):
    k = clean_key(x)
    return TEAM_ALIASES.get(k, str(x).strip() if x is not None and str(x).strip() else "")

def normalize_book(x):
    k = clean_key(x)
    return BOOK_ALIASES.get(k, str(x).strip() if x is not None and str(x).strip() else "")

def american_implied(odds):
    try:
        o = float(odds)
    except Exception:
        return None
    if o == 0 or not math.isfinite(o):
        return None
    if o > 0:
        return 100.0 / (o + 100.0)
    return abs(o) / (abs(o) + 100.0)

def american_profit_on_stake(stake, odds):
    try:
        stake = float(stake)
        o = float(odds)
    except Exception:
        return None
    if not math.isfinite(stake) or not math.isfinite(o) or stake <= 0 or o == 0:
        return None
    if o > 0:
        return stake * (o / 100.0)
    return stake * (100.0 / abs(o))

def no_vig_prob(side_odds, other_side_odds):
    """
    Convert two-way market prices into no-vig fair probability for the selected side.
    """
    p1 = american_implied(side_odds)
    p2 = american_implied(other_side_odds)
    if p1 is None or p2 is None or (p1 + p2) <= 0:
        return None
    return p1 / (p1 + p2)

def clamp_prob(p):
    if p is None:
        return None
    return max(0.01, min(0.99, float(p)))

def line_value_pp(market_kind):
    """
    Heuristic probability value of one point/win of CLV.
    Win totals move in whole/half season wins and are much more valuable than a normal spread point.
    """
    if market_kind == "win_total":
        return 0.15
    if market_kind == "spread":
        return 0.03
    if market_kind == "game_total":
        return 0.02
    return 0.0

def line_adjusted_fair_prob(current_no_vig_prob, line_clv, market_kind):
    if current_no_vig_prob is None:
        return None
    adj = (line_clv or 0) * line_value_pp(market_kind)
    return clamp_prob(current_no_vig_prob + adj)

def ev_from_fair_prob(stake, bet_odds, fair_prob):
    """
    EV using no-vig / line-adjusted fair probability.
    """
    p = clamp_prob(fair_prob)
    win_profit = american_profit_on_stake(stake, bet_odds)
    try:
        stake = float(stake)
    except Exception:
        return None, None
    if p is None or win_profit is None or stake <= 0:
        return None, None
    ev_dollars = p * win_profit - (1.0 - p) * stake
    ev_pct = ev_dollars / stake
    return ev_dollars, ev_pct

def market_edge_vs_bet_breakeven(bet_odds, fair_prob):
    """
    CLV/edge as probability points versus the bet's break-even probability.
    Positive means the bet price is better than the no-vig fair estimate.
    """
    bi = american_implied(bet_odds)
    fp = clamp_prob(fair_prob)
    if bi is None or fp is None:
        return None, None
    edge_pp = (fp - bi) * 100.0
    return edge_pp, edge_pp / 100.0


def categorize_bet(row):
    resolved = clean_key(row.get("resolved_market_type"))

    if resolved == "moneyline":
        return "Moneyline"
    if resolved == "spread":
        return "Spread"
    if resolved == "total":
        return "Game Total"

    desc = clean_key(row.get("Bet Description"))
    typ = clean_key(row.get("Bet Type"))
    bet = clean_key(row.get("Bet"))
    side = clean_key(row.get("side"))

    if "win total" in desc:
        return "Win Total"
    if "conf title" in desc or typ == "future" or " win " in f" {bet} ":
        return "Conference Future"

    first_half = ("1h" in typ or "1h" in desc or "first half" in typ or "first half" in desc or "1st half" in typ or "1st half" in desc)
    second_half = ("2h" in typ or "2h" in desc or "second half" in typ or "second half" in desc or "2nd half" in typ or "2nd half" in desc)

    is_total = typ in {"total", "game total"} or side in {"over", "under"} or "over" in bet or "under" in bet
    is_spread = typ in {"side", "spread"} or "week" in desc

    if first_half and is_total:
        return "1H Total"
    if first_half and is_spread:
        return "1H Spread"
    if second_half and is_total:
        return "2H Total"
    if second_half and is_spread:
        return "2H Spread"
    if is_total:
        return "Game Total"
    if is_spread:
        return "Spread"

    return "Other"

def season_phase_for_date(dt=None):
    from datetime import datetime, date
    if dt is None:
        dt = datetime.now().date()
    elif hasattr(dt, "date"):
        dt = dt.date()
    start = date(2026, 8, 29)
    if dt < start:
        return "Preseason"
    week = ((dt - start).days // 7) + 1
    if week <= 15:
        return f"Week {week}"
    return "Playoffs"

def parse_num(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    s = str(x).replace("$","").replace(",","").strip()
    if s in {"", "nan", "None"}:
        return None
    try:
        return float(s)
    except Exception:
        return None

def infer_side(row):
    raw_side = row.get("side")
    side = "" if raw_side is None or (isinstance(raw_side, float) and math.isnan(raw_side)) else str(raw_side).strip()
    if side.lower() == "nan":
        side = ""
    if side:
        return side
    bet = clean_key(row.get("Bet"))
    desc = clean_key(row.get("Bet Description"))
    if "under" in bet:
        return "Under"
    if "over" in bet:
        return "Over"
    if "conf title" in desc or "conference" in desc:
        return "Yes"
    if " win " in f" {bet} " or bet.startswith("win ") or bet.endswith(" win"):
        return "Yes"
    return ""

def infer_bet_type(row):
    existing = str(row.get("Bet Type") or "").strip()
    desc = clean_key(row.get("Bet Description"))
    bet = clean_key(row.get("Bet"))
    if "conf title" in desc:
        return "Future"
    if "win total" in desc:
        return "Total"
    if "week 1" in desc:
        if "over" in bet or "under" in bet:
            return "Total"
        return "Side"
    return existing

def find_col(cols, candidates):
    low = {str(c).strip().lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in low:
            return low[cand.lower()]
    for c in cols:
        key = str(c).strip().lower()
        for cand in candidates:
            if cand.lower() in key:
                return c
    return None

def read_market_file(path):
    out = []
    try:
        if path.suffix.lower() == ".csv":
            out.append((path.name, pd.read_csv(path)))
        elif path.suffix.lower() in {".xlsx", ".xlsm"}:
            xls = pd.ExcelFile(path)
            for sheet in xls.sheet_names:
                try:
                    out.append((f"{path.name}:{sheet}", pd.read_excel(path, sheet_name=sheet)))
                except Exception:
                    pass
    except Exception:
        return []
    return out

def collect_market_rows():
    win_rows = []
    fut_rows = []
    audit = []

    candidates = []
    for pat in ["*.csv", "*.xlsx", "*.xlsm"]:
        candidates.extend(ROOT.rglob(pat))

    for path in candidates:
        rel = path.relative_to(ROOT)
        name = str(rel).lower()

        if "data/bets" in name:
            continue

        # Use current market import/export files only.
        # Exclude history, movement, debug, backups, templates, audits, and old game odds files.
        excluded = any(x in name for x in [
            "history", "movement", "debug", "backup", "template", "audit",
            "sgo_", "halves", "before_", "raw", "metadata"
        ])
        current_market = any(x in name for x in [
            "market_win_totals_import.csv",
            "actionnetwork_win_totals_all_brand_rows.csv",
            "fanduel_win_totals_import",
            "bettingpros_caesars_win_totals",
            "market_conference_futures_import.csv",
            "actionnetwork_conference_futures_all_brand_rows.csv"
        ])
        if excluded or not current_market:
            continue

        for label, df in read_market_file(path):
            if df is None or df.empty:
                continue

            cols = list(df.columns)
            team_col = find_col(cols, ["team", "team_name", "participant", "selection"])
            book_col = find_col(cols, ["book", "sportsbook", "operator", "brand"])
            total_col = find_col(cols, ["win_total", "market_total", "total", "line"])
            over_col = find_col(cols, ["over_odds", "over_price", "over"])
            under_col = find_col(cols, ["under_odds", "under_price", "under"])
            odds_col = find_col(cols, ["odds", "price", "american_odds", "best_price", "conference_title_odds"])
            conf_col = find_col(cols, ["conference", "conf"])

            added_win = 0
            added_fut = 0

            if team_col and total_col and (over_col or under_col):
                for _, r in df.iterrows():
                    team = normalize_team(r.get(team_col))
                    if not team:
                        continue
                    win_rows.append({
                        "team": team,
                        "team_key": clean_key(team),
                        "book": normalize_book(r.get(book_col)) if book_col else "",
                        "line": parse_num(r.get(total_col)),
                        "over_odds": parse_num(r.get(over_col)) if over_col else None,
                        "under_odds": parse_num(r.get(under_col)) if under_col else None,
                        "source": label,
                    })
                    added_win += 1

            # Futures rows usually have team + book + one odds/price column.
            if team_col and odds_col and ("future" in name or "conference" in name or "futures" in name):
                for _, r in df.iterrows():
                    team = normalize_team(r.get(team_col))
                    price = parse_num(r.get(odds_col))
                    if not team or price is None:
                        continue
                    fut_rows.append({
                        "team": team,
                        "team_key": clean_key(team),
                        "book": normalize_book(r.get(book_col)) if book_col else "",
                        "price": price,
                        "conference": str(r.get(conf_col)).strip() if conf_col and pd.notna(r.get(conf_col)) else "",
                        "source": label,
                    })
                    added_fut += 1

            if added_win or added_fut:
                audit.append({
                    "source": label,
                    "win_total_rows": added_win,
                    "futures_rows": added_fut,
                    "columns": ", ".join(map(str, cols[:18])),
                })

    return win_rows, fut_rows, audit



def parse_bet_week(row):
    desc = clean_key(row.get("Bet Description"))
    m = re.search(r"\bweek\s+(\d+)\b", desc)
    if m:
        return int(m.group(1))
    return None


def canonical_market_games():
    """
    Read the canonical current-market contract.

    Current game-bet CLV/EV consumes this contract rather than independently
    selecting stale provider CSV rows.
    """
    path = ROOT / "data" / "site" / "current_market_contract.json"

    if not path.exists():
        return [], [{
            "source": str(path.relative_to(ROOT)),
            "status": "MISSING",
        }]

    try:
        payload = json.loads(path.read_text())
    except Exception as exc:
        return [], [{
            "source": str(path.relative_to(ROOT)),
            "status": "INVALID",
            "error": str(exc),
        }]

    games = payload.get("games") or []

    return games, [{
        "source": str(path.relative_to(ROOT)),
        "status": "AVAILABLE",
        "games": len(games),
        "market_authority": "Pinnacle",
    }]


def canonical_team_side(game, team):
    tk = clean_key(normalize_team(team))

    if not tk:
        return None

    away = normalize_team(game.get("away_team"))
    home = normalize_team(game.get("home_team"))

    if tk == clean_key(away):
        return "away"

    if tk == clean_key(home):
        return "home"

    return None


def wager_team_tokens(row):
    """
    Extract team tokens for totals such as:
      USC/NMST Over 59.5
    """
    bet = str(row.get("Bet") or "")

    head = re.split(
        r"\bover\b|\bunder\b",
        bet,
        flags=re.I,
    )[0]

    parts = [
        x.strip()
        for x in re.split(
            r"[/@]|(?:\s+vs\.?\s+)|(?:\s+at\s+)",
            head,
            flags=re.I,
        )
    ]

    out = []

    for part in parts:
        if not part:
            continue

        n = normalize_team(part)

        if clean_key(n):
            out.append(n)

    return out


def resolve_canonical_game(row, games):
    """
    Resolve a wager to exactly one canonical game.

    Week + participant identity are required for current weekly bets.

    Team-only matching across the entire schedule is explicitly forbidden.
    That prior behavior caused the Stanford Week 0 wager to match
    Miami (FL) at Stanford in Week 1 instead of Hawaii at Stanford in Week 0.
    """
    week = parse_bet_week(row)

    team = normalize_team(row.get("team_guess"))
    bet_type = clean_key(row.get("Bet Type"))
    bet = clean_key(row.get("Bet"))

    pool = [
        g for g in games
        if week is None or parse_num(g.get("week")) == week
    ]

    is_total = (
        bet_type in {"total", "game total"}
        or " over " in f" {bet} "
        or " under " in f" {bet} "
    )

    if is_total:
        tokens = wager_team_tokens(row)
        token_keys = {
            clean_key(x)
            for x in tokens
            if clean_key(x)
        }

        matches = []

        for g in pool:
            participants = {
                clean_key(normalize_team(g.get("away_team"))),
                clean_key(normalize_team(g.get("home_team"))),
            }

            if token_keys and token_keys.issubset(participants):
                matches.append(g)

        return matches[0] if len(matches) == 1 else None

    tk = clean_key(team)

    if not tk:
        return None

    matches = []

    for g in pool:
        participants = {
            clean_key(normalize_team(g.get("away_team"))),
            clean_key(normalize_team(g.get("home_team"))),
        }

        if tk in participants:
            matches.append(g)

    return matches[0] if len(matches) == 1 else None


def resolve_game_market_kind(row, game):
    """
    Resolve Spread / Total / Moneyline.

    A Side wager with Bet Line 0 is treated as moneyline only when:
      - the selected team resolves to the canonical game,
      - Pinnacle has a moneyline for that side, and
      - Pinnacle's spread for that side is non-zero.

    This avoids globally converting genuine pick'em spreads to moneylines.
    """
    typ = clean_key(row.get("Bet Type"))
    bet = clean_key(row.get("Bet"))
    side = clean_key(row.get("side"))
    line = parse_num(row.get("bet_line"))

    if (
        typ in {"total", "game total"}
        or side in {"over", "under"}
        or "over" in bet
        or "under" in bet
    ):
        return "total"

    team_side = canonical_team_side(
        game,
        row.get("team_guess"),
    )

    pinnacle = (
        (game.get("quotes") or {})
        .get("Pinnacle", {})
    )

    if (
        typ in {"side", "spread"}
        and line == 0
        and team_side
    ):
        ml = (
            pinnacle.get("moneyline", {})
            .get(team_side)
        )

        spread = (
            pinnacle.get("spread", {})
            .get(team_side)
        )

        spread_line = parse_num(
            (spread or {}).get("line")
        )

        if (
            ml
            and spread_line is not None
            and abs(spread_line) > 0
        ):
            return "moneyline"

    if typ in {"side", "spread"}:
        return "spread"

    return None


def pinnacle_pair(game, market_kind, selected_side):
    """
    Return the selected and opposite Pinnacle quotes required for a
    two-sided no-vig probability calculation.
    """
    pinnacle = (
        (game.get("quotes") or {})
        .get("Pinnacle", {})
    )

    market = pinnacle.get(market_kind) or {}

    if market_kind == "total":
        if selected_side not in {"over", "under"}:
            return None, None

        other_side = (
            "under"
            if selected_side == "over"
            else "over"
        )

    else:
        if selected_side not in {"home", "away"}:
            return None, None

        other_side = (
            "away"
            if selected_side == "home"
            else "home"
        )

    selected = market.get(selected_side)
    opposite = market.get(other_side)

    if not selected or not opposite:
        return None, None

    if (
        parse_num(selected.get("price")) is None
        or parse_num(opposite.get("price")) is None
    ):
        return None, None

    return selected, opposite


def collect_game_line_rows():
    """
    Current game-line market rows for sides/totals.
    Preferred file: data/odds/actionnetwork_ncaaf_game_lines_2026.csv
    Granular rows contain one row per book/market/side.
    """
    rows = []
    audit = []

    files = [
        ROOT / "data" / "odds" / "actionnetwork_ncaaf_game_lines_2026.csv",
        ROOT / "data" / "odds" / "action_ncaaf_game_lines_2026.csv",
        ROOT / "data" / "odds" / "theodds_ncaaf_lines_2026.csv",
    ]

    for path in files:
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)
        except Exception:
            continue

        added = 0
        for _, r in df.iterrows():
            market = clean_key(r.get("market"))
            if market not in {"spread", "spreads", "total", "totals"}:
                continue

            away = normalize_team(r.get("away_team"))
            home = normalize_team(r.get("home_team"))
            book = normalize_book(r.get("book"))
            side_raw = clean_key(r.get("side"))
            point = parse_num(r.get("point"))
            price = parse_num(r.get("price"))

            selected_team = ""
            side_kind = ""

            if market in {"spread", "spreads"}:
                if side_raw == "home":
                    selected_team = home
                    side_kind = "spread"
                elif side_raw == "away":
                    selected_team = away
                    side_kind = "spread"
                else:
                    # The Odds API style has team name in side.
                    side_team = normalize_team(r.get("side"))
                    if clean_key(side_team) == clean_key(home):
                        selected_team = home
                        side_kind = "spread"
                    elif clean_key(side_team) == clean_key(away):
                        selected_team = away
                        side_kind = "spread"

            elif market in {"total", "totals"}:
                if side_raw in {"over", "under"}:
                    selected_team = side_raw.title()
                    side_kind = "total"

            if not selected_team or point is None:
                continue

            rows.append({
                "source": str(path.relative_to(ROOT)),
                "game_id": r.get("game_id"),
                "date": str(r.get("date") or r.get("commence_time") or "")[:10],
                "week": parse_num(r.get("week")),
                "away_team": away,
                "home_team": home,
                "team": selected_team,
                "team_key": clean_key(selected_team),
                "book": book,
                "market": "spread" if side_kind == "spread" else "total",
                "side": side_raw,
                "point": point,
                "price": price,
                "pulled_at": r.get("pulled_at"),
            })
            added += 1

        audit.append({
            "source": str(path.relative_to(ROOT)),
            "game_line_rows": added,
            "columns": ", ".join(map(str, df.columns[:22])),
        })

    return rows, audit


def choose_game_line(rows, sportsbook):
    """
    Prefer same book. If same book is unavailable, choose the most favorable current spread
    for the bet side, then best price.
    """
    if not rows:
        return None

    book = normalize_book(sportsbook)
    same = [r for r in rows if normalize_book(r.get("book")) == book]
    pool = same if same else rows

    # For selected-team spread, higher point is better for the bettor:
    # +16.5 beats +14.5; -9.5 beats -11.5 because -9.5 is higher.
    return sorted(
        pool,
        key=lambda r: (
            r.get("point") if r.get("point") is not None else -999999,
            r.get("price") if r.get("price") is not None else -999999,
        ),
        reverse=True
    )[0]

def choose_same_book_or_first(rows, sportsbook):
    if not rows:
        return None
    book = normalize_book(sportsbook)
    same = [r for r in rows if normalize_book(r.get("book")) == book]
    return same[0] if same else rows[0]

def choose_futures_price(rows, sportsbook):
    if not rows:
        return None
    book = normalize_book(sportsbook)
    same = [r for r in rows if normalize_book(r.get("book")) == book]
    if same:
        return same[0]
    # Best currently available Yes price for the bettor is highest American odds.
    return sorted(rows, key=lambda r: (r.get("price") if r.get("price") is not None else -999999), reverse=True)[0]

df = pd.read_csv(BETS)
dash = json.loads(DASH.read_text())

# Normalize core betting fields.
df["team_guess"] = df["team_guess"].apply(normalize_team)
df["book_norm"] = df["Sportsbook"].apply(normalize_book)
df["side"] = df.apply(infer_side, axis=1)
df["Bet Type"] = df.apply(infer_bet_type, axis=1)

for c in [
    "current_market_match", "current_market_source", "current_market_book",
    "current_market_line", "current_market_price", "current_market_note",
    "line_clv_current", "price_clv_current_pp", "clv_pct_current",
    "current_no_vig_prob", "line_adjusted_fair_prob",
    "ev_current_dollars", "ev_current_pct",
    "beat_clv", "clv_category", "market_category", "clv_grade",
    "resolved_market_type", "current_market_authority",
    "current_market_game_id", "current_market_updated_at"
]:
    if c not in df.columns:
        df[c] = None

win_rows, fut_rows, audit_rows = collect_market_rows()
game_rows, game_audit_rows = collect_game_line_rows()

canonical_games, canonical_game_audit = canonical_market_games()
game_audit_rows.extend(canonical_game_audit)

matched = 0

for idx, row in df.iterrows():
    desc = clean_key(row.get("Bet Description"))
    team = normalize_team(row.get("team_guess"))
    team_key = clean_key(team)
    side = str(row.get("side") or "").strip()
    book = row.get("Sportsbook")
    bet_line = parse_num(row.get("bet_line"))
    bet_price = parse_num(row.get("bet_price"))

    if not team_key:
        continue

    if "win total" in desc and side in {"Over", "Under"}:
        candidates = [r for r in win_rows if r["team_key"] == team_key and r.get("line") is not None]
        m = choose_same_book_or_first(candidates, book)
        if not m:
            df.at[idx, "current_market_note"] = "No current win-total market match"
            continue

        current_line = m.get("line")
        current_price = m.get("over_odds") if side == "Over" else m.get("under_odds")

        line_clv = None
        if bet_line is not None and current_line is not None:
            line_clv = current_line - bet_line if side == "Over" else bet_line - current_line

        other_price = m.get("under_odds") if side == "Over" else m.get("over_odds")
        current_no_vig = no_vig_prob(current_price, other_price)
        fair_prob = line_adjusted_fair_prob(current_no_vig, line_clv, "win_total")
        price_clv, clv_pct = market_edge_vs_bet_breakeven(bet_price, fair_prob)
        ev_dollars, ev_pct = ev_from_fair_prob(row.get("stake"), bet_price, fair_prob)

        df.at[idx, "current_market_match"] = True
        df.at[idx, "current_market_source"] = m.get("source")
        df.at[idx, "current_market_book"] = m.get("book")
        df.at[idx, "current_market_line"] = current_line
        df.at[idx, "current_market_price"] = current_price
        df.at[idx, "line_clv_current"] = line_clv
        df.at[idx, "price_clv_current_pp"] = price_clv
        df.at[idx, "clv_pct_current"] = clv_pct
        df.at[idx, "current_no_vig_prob"] = current_no_vig
        df.at[idx, "line_adjusted_fair_prob"] = fair_prob
        df.at[idx, "ev_current_dollars"] = ev_dollars
        df.at[idx, "ev_current_pct"] = ev_pct
        df.at[idx, "clv_grade"] = "Positive" if ((clv_pct or 0) > 0) else "Neutral/Negative"
        matched += 1

    elif "conf title" in desc or side == "Yes":
        candidates = [r for r in fut_rows if r["team_key"] == team_key and r.get("price") is not None]
        m = choose_futures_price(candidates, book)
        if not m:
            df.at[idx, "current_market_note"] = "No current futures market match"
            continue

        current_price = m.get("price")
        price_clv = None
        clv_pct = None
        bi = american_implied(bet_price)
        ci = american_implied(current_price)
        if bi is not None and ci is not None:
            price_clv = (ci - bi) * 100.0
            clv_pct = price_clv / 100.0

        # Futures are not a simple two-way market; keep current price-implied EV until
        # we build a full no-vig conference-field normalizer.
        fair_prob = american_implied(current_price)
        price_clv, clv_pct = market_edge_vs_bet_breakeven(bet_price, fair_prob)
        ev_dollars, ev_pct = ev_from_fair_prob(row.get("stake"), bet_price, fair_prob)

        df.at[idx, "current_market_match"] = True
        df.at[idx, "current_market_source"] = m.get("source")
        df.at[idx, "current_market_book"] = m.get("book")
        df.at[idx, "current_market_line"] = None
        df.at[idx, "current_market_price"] = current_price
        df.at[idx, "line_clv_current"] = None
        df.at[idx, "price_clv_current_pp"] = price_clv
        df.at[idx, "clv_pct_current"] = clv_pct
        df.at[idx, "current_no_vig_prob"] = None
        df.at[idx, "line_adjusted_fair_prob"] = fair_prob
        df.at[idx, "ev_current_dollars"] = ev_dollars
        df.at[idx, "ev_current_pct"] = ev_pct
        df.at[idx, "clv_grade"] = "Positive" if ((clv_pct or 0) > 0) else "Neutral/Negative"
        matched += 1

    else:
        # Canonical current-game matcher.
        #
        # Authority:
        #   data/site/current_market_contract.json
        #     -> exact week + participant identity
        #     -> Pinnacle two-sided market
        #
        # Do not silently use stale legacy game-line CSVs here.
        # If Pinnacle cannot be resolved deterministically, current CLV/EV
        # remains unavailable rather than publishing a misleading value.

        game = resolve_canonical_game(
            row,
            canonical_games,
        )

        if not game:
            df.at[
                idx,
                "current_market_note"
            ] = "No unique canonical game match"
            continue

        market_kind = resolve_game_market_kind(
            row,
            game,
        )

        df.at[
            idx,
            "resolved_market_type"
        ] = (
            market_kind.title()
            if market_kind
            else None
        )

        df.at[
            idx,
            "current_market_game_id"
        ] = game.get("game_id")

        df.at[
            idx,
            "current_market_updated_at"
        ] = game.get("current_market_updated_at")

        if market_kind not in {
            "spread",
            "total",
            "moneyline",
        }:
            df.at[
                idx,
                "current_market_note"
            ] = "No supported canonical market classification"
            continue

        if market_kind == "total":
            selected_side = clean_key(side)

            if selected_side not in {
                "over",
                "under",
            }:
                bet_key = clean_key(
                    row.get("Bet")
                )

                if "over" in bet_key:
                    selected_side = "over"

                elif "under" in bet_key:
                    selected_side = "under"

        else:
            selected_side = canonical_team_side(
                game,
                team,
            )

        selected_quote, opposite_quote = pinnacle_pair(
            game,
            market_kind,
            selected_side,
        )

        if not selected_quote or not opposite_quote:
            df.at[
                idx,
                "current_market_note"
            ] = (
                f"No Pinnacle {market_kind} pair for "
                f"{game.get('away_team')} at "
                f"{game.get('home_team')}"
            )
            continue

        current_line = parse_num(
            selected_quote.get("line")
        )

        current_price = parse_num(
            selected_quote.get("price")
        )

        opposite_price = parse_num(
            opposite_quote.get("price")
        )

        current_no_vig = no_vig_prob(
            current_price,
            opposite_price,
        )

        line_clv = None

        if market_kind == "spread":

            if (
                bet_line is None
                or current_line is None
            ):
                df.at[
                    idx,
                    "current_market_note"
                ] = "Spread line unavailable"
                continue

            # Selected-team perspective:
            #
            # ticket +16.5 vs current +14.5 -> +2.0
            # ticket -6.5  vs current -7.0  -> +0.5
            line_clv = (
                bet_line
                - current_line
            )

            fair_prob = line_adjusted_fair_prob(
                current_no_vig,
                line_clv,
                "spread",
            )

        elif market_kind == "total":

            if (
                bet_line is None
                or current_line is None
            ):
                df.at[
                    idx,
                    "current_market_note"
                ] = "Total line unavailable"
                continue

            if selected_side == "over":
                line_clv = (
                    current_line
                    - bet_line
                )

            else:
                line_clv = (
                    bet_line
                    - current_line
                )

            fair_prob = line_adjusted_fair_prob(
                current_no_vig,
                line_clv,
                "game_total",
            )

        else:
            # Moneyline:
            # no point-line CLV.
            # Fair probability is the de-vigged Pinnacle ML pair.
            line_clv = None
            fair_prob = current_no_vig

        price_clv, clv_pct = (
            market_edge_vs_bet_breakeven(
                bet_price,
                fair_prob,
            )
        )

        ev_dollars, ev_pct = (
            ev_from_fair_prob(
                row.get("stake"),
                bet_price,
                fair_prob,
            )
        )

        df.at[
            idx,
            "current_market_match"
        ] = True

        df.at[
            idx,
            "current_market_source"
        ] = selected_quote.get("source")

        df.at[
            idx,
            "current_market_book"
        ] = "Pinnacle"

        df.at[
            idx,
            "current_market_authority"
        ] = "PINNACLE"

        df.at[
            idx,
            "current_market_line"
        ] = current_line

        df.at[
            idx,
            "current_market_price"
        ] = current_price

        df.at[
            idx,
            "current_market_note"
        ] = (
            f"{game.get('away_team')} at "
            f"{game.get('home_team')}"
        )

        df.at[
            idx,
            "line_clv_current"
        ] = line_clv

        df.at[
            idx,
            "price_clv_current_pp"
        ] = price_clv

        df.at[
            idx,
            "clv_pct_current"
        ] = clv_pct

        df.at[
            idx,
            "current_no_vig_prob"
        ] = current_no_vig

        df.at[
            idx,
            "line_adjusted_fair_prob"
        ] = fair_prob

        df.at[
            idx,
            "ev_current_dollars"
        ] = ev_dollars

        df.at[
            idx,
            "ev_current_pct"
        ] = ev_pct

        df.at[
            idx,
            "clv_grade"
        ] = (
            "Positive"
            if ((clv_pct or 0) > 0)
            else "Neutral/Negative"
        )

        matched += 1

# Summary CLV stats.
# Per-bet CLV flags and categories.
df["clv_category"] = df.apply(categorize_bet, axis=1)
df["market_category"] = df["clv_category"]

_clv = pd.to_numeric(df["clv_pct_current"], errors="coerce")
_matched_flag = df["current_market_match"].astype(str).str.lower().eq("true")
df["beat_clv"] = None
df.loc[_matched_flag & (_clv > 0), "beat_clv"] = "Yes"
df.loc[_matched_flag & (_clv <= 0), "beat_clv"] = "No"

matched_df = df[df["current_market_match"].astype(str).str.lower().eq("true")].copy()
price_vals = pd.to_numeric(matched_df["price_clv_current_pp"], errors="coerce").dropna()
line_vals = pd.to_numeric(matched_df["line_clv_current"], errors="coerce").dropna()
ev_dollar_vals = pd.to_numeric(matched_df["ev_current_dollars"], errors="coerce").dropna()
ev_pct_vals = pd.to_numeric(matched_df["ev_current_pct"], errors="coerce").dropna()

# Positive CLV now means positive no-vig / line-adjusted edge.
# Line movement is included inside clv_pct_current, but line movement alone
# does not count as positive unless the vig-free fair edge is positive.
positive_mask = (
    pd.to_numeric(matched_df["clv_pct_current"], errors="coerce").fillna(0) > 0
)
positive_count = int(positive_mask.sum()) if len(matched_df) else 0

best = None
if len(matched_df):
    tmp = matched_df.copy()
    tmp["_clv_score"] = pd.to_numeric(tmp["price_clv_current_pp"], errors="coerce").fillna(0) + pd.to_numeric(tmp["line_clv_current"], errors="coerce").fillna(0)
    best_row = tmp.sort_values("_clv_score", ascending=False).iloc[0].to_dict()
    best = {
        "bet": best_row.get("Bet"),
        "book": best_row.get("Sportsbook"),
        "team": best_row.get("team_guess"),
        "side": best_row.get("side"),
        "line_clv_current": parse_num(best_row.get("line_clv_current")),
        "price_clv_current_pp": parse_num(best_row.get("price_clv_current_pp")),
        "current_market_book": best_row.get("current_market_book"),
        "current_market_price": parse_num(best_row.get("current_market_price")),
        "current_market_line": parse_num(best_row.get("current_market_line")),
    }

summary = dash.get("summary", {})
summary["missing_bet_type"] = int((df["Bet Type"].fillna("").astype(str).str.strip() == "").sum())
summary["current_clv_matched"] = int(len(matched_df))
summary["current_clv_positive"] = positive_count
summary["pct_bets_beating_current_clv"] = round(positive_count / len(matched_df), 4) if len(matched_df) else None
summary["avg_line_clv_current"] = round(float(line_vals.mean()), 3) if len(line_vals) else None
summary["avg_price_clv_current_pp"] = round(float(price_vals.mean()), 3) if len(price_vals) else None
summary["avg_ev_current_dollars"] = round(float(ev_dollar_vals.mean()), 2) if len(ev_dollar_vals) else None
summary["total_ev_current_dollars"] = round(float(ev_dollar_vals.sum()), 2) if len(ev_dollar_vals) else None
summary["avg_ev_current_pct"] = round(float(ev_pct_vals.mean()), 4) if len(ev_pct_vals) else None
summary["best_current_clv_bet"] = best

# CLV / EV by category for dashboard tracking.
cat_rows = []
for cat, g in df.groupby("clv_category", dropna=False):
    matched_g = g[g["current_market_match"].astype(str).str.lower().eq("true")]
    clv_vals = pd.to_numeric(matched_g["clv_pct_current"], errors="coerce").dropna()
    ev_vals = pd.to_numeric(matched_g["ev_current_dollars"], errors="coerce").dropna()
    ev_pct_vals = pd.to_numeric(matched_g["ev_current_pct"], errors="coerce").dropna()
    beat_yes = int((matched_g["beat_clv"].astype(str) == "Yes").sum()) if len(matched_g) else 0
    matched_n = int(len(matched_g))
    cat_rows.append({
        "category": cat if cat and str(cat) != "nan" else "Other",
        "bets": int(len(g)),
        "matched": matched_n,
        "beat_clv_yes": beat_yes,
        "beat_clv_no": int((matched_g["beat_clv"].astype(str) == "No").sum()) if matched_n else 0,
        "beat_clv_pct": round(beat_yes / matched_n, 4) if matched_n else None,
        "stake": round(float(pd.to_numeric(g["stake"], errors="coerce").fillna(0).sum()), 2),
        "avg_no_vig_clv_pct": round(float(clv_vals.mean()), 4) if len(clv_vals) else None,
        "avg_no_vig_clv_pp": round(float(clv_vals.mean() * 100), 3) if len(clv_vals) else None,
        "total_no_vig_ev_dollars": round(float(ev_vals.sum()), 2) if len(ev_vals) else None,
        "avg_no_vig_ev_pct": round(float(ev_pct_vals.mean()), 4) if len(ev_pct_vals) else None,
    })

dash["by_clv_category"] = sorted(cat_rows, key=lambda r: (-r["bets"], str(r["category"])))

# Weekly / phase performance summary.
# Profit is realized only when bets are graded. EV/CLV tracks open or matched bets.
def week_bucket(row):
    desc = clean_key(row.get("Bet Description"))
    date_s = str(row.get("Date") or "").strip()

    import re
    m = re.search(r"week\s+(\d+)", desc)
    if m:
        return f"Week {int(m.group(1))}"

    if "win total" in desc or "conf title" in desc:
        return "Preseason"

    try:
        dt = pd.to_datetime(date_s, errors="coerce")
        if pd.isna(dt):
            return "Unassigned"
        # Until we have exact settled game weeks for every bet, keep dated non-week bets grouped.
        return "Preseason"
    except Exception:
        return "Unassigned"

def week_sort_key(label):
    if label == "Preseason":
        return 0
    if label == "Playoffs":
        return 99
    m = re.search(r"Week\s+(\d+)", str(label))
    if m:
        return int(m.group(1))
    return 98

df["week_bucket"] = df.apply(week_bucket, axis=1)

week_rows = []
for wk, g in df.groupby("week_bucket", dropna=False):
    stake = pd.to_numeric(g["stake"], errors="coerce").fillna(0)
    # Realized P/L should only count settled bets.
    # Open bets may show -stake in the sheet Profit column, but dashboard P/L stays $0 until graded.
    if "status" in g.columns:
        settled_mask = ~g["status"].fillna("").astype(str).str.lower().eq("open")
    elif "Result" in g.columns:
        settled_mask = g["Result"].fillna("").astype(str).str.strip().ne("")
    else:
        settled_mask = pd.Series([False] * len(g), index=g.index)

    if "Profit" in g.columns:
        raw_profit = pd.to_numeric(
            g["Profit"].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False),
            errors="coerce"
        ).fillna(0)
    elif "profit" in g.columns:
        raw_profit = pd.to_numeric(g["profit"], errors="coerce").fillna(0)
    else:
        raw_profit = pd.Series([0] * len(g), index=g.index)

    profit = raw_profit.where(settled_mask, 0)
    ev = pd.to_numeric(g["ev_current_dollars"], errors="coerce").fillna(0)
    clv = pd.to_numeric(g["clv_pct_current"], errors="coerce")
    matched_g = g[g["current_market_match"].astype(str).str.lower().eq("true")]
    beat_yes = int((matched_g["beat_clv"].astype(str) == "Yes").sum())
    beat_no = int((matched_g["beat_clv"].astype(str) == "No").sum())
    matched_n = int(len(matched_g))

    result = g.get("Result")
    if result is not None:
        result_s = result.fillna("").astype(str).str.lower()
        wins = int(result_s.isin(["win", "won", "w"]).sum())
        losses = int(result_s.isin(["loss", "lost", "l"]).sum())
        pushes = int(result_s.isin(["push", "p"]).sum())
    else:
        wins = losses = pushes = 0

    week_rows.append({
        "week": wk if wk and str(wk) != "nan" else "Unassigned",
        "sort": week_sort_key(wk),
        "bets": int(len(g)),
        "open": int(g["status"].fillna("").astype(str).str.lower().eq("open").sum()) if "status" in g.columns else int(len(g)),
        "settled": int(g["status"].fillna("").astype(str).str.lower().ne("open").sum()) if "status" in g.columns else 0,
        "stake": round(float(stake.sum()), 2),
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "weekly_profit": round(float(profit.sum()), 2),
        "weekly_no_vig_ev": round(float(ev.sum()), 2),
        "matched": matched_n,
        "beat_clv_yes": beat_yes,
        "beat_clv_no": beat_no,
        "beat_clv_pct": round(beat_yes / matched_n, 4) if matched_n else None,
        "avg_no_vig_clv_pct": round(float(clv.dropna().mean()), 4) if len(clv.dropna()) else None,
        "avg_no_vig_clv_pp": round(float(clv.dropna().mean() * 100), 3) if len(clv.dropna()) else None,
    })

week_rows = sorted(week_rows, key=lambda r: r["sort"])

ytd_profit = 0.0
ytd_ev = 0.0
for r in week_rows:
    ytd_profit += r["weekly_profit"]
    ytd_ev += r["weekly_no_vig_ev"]
    r["ytd_profit"] = round(ytd_profit, 2)
    r["ytd_no_vig_ev"] = round(ytd_ev, 2)

dash["by_week_performance"] = week_rows

# Chart points: cumulative/YTD values across season buckets.
chart_labels = ["Preseason"] + [f"Week {i}" for i in range(1, 16)] + ["Playoffs"]
week_map = {r["week"]: r for r in week_rows}
chart_rows = []
last_profit = 0.0
last_ev = 0.0
for lab in chart_labels:
    if lab in week_map:
        last_profit = week_map[lab].get("ytd_profit") or last_profit
        last_ev = week_map[lab].get("ytd_no_vig_ev") or last_ev
    chart_rows.append({
        "phase": lab,
        "profit_loss": round(float(last_profit), 2),
        "no_vig_ev": round(float(last_ev), 2),
    })

dash["performance_chart"] = chart_rows


dash["summary"] = summary
dash["open_bets"] = df[df["status"].fillna("").astype(str).str.lower().eq("open")].where(pd.notna(df), None).to_dict("records")
dash["updated_at"] = datetime.now().replace(microsecond=0).isoformat()

# Append dashboard history for CLV/EV vs realized results tracking.
HISTORY = ROOT / "data" / "bets" / "betting_performance_history.csv"
now_dt = datetime.now()
hist_row = {
    "snapshot_at": now_dt.replace(microsecond=0).isoformat(),
    "season_phase": season_phase_for_date(now_dt),
    "bets": summary.get("bets"),
    "open": summary.get("open"),
    "settled": summary.get("settled"),
    "exposure": summary.get("exposure"),
    "realized_profit": summary.get("profit"),
    "current_clv_matched": summary.get("current_clv_matched"),
    "current_clv_positive": summary.get("current_clv_positive"),
    "pct_bets_beating_current_clv": summary.get("pct_bets_beating_current_clv"),
    "avg_line_clv_current": summary.get("avg_line_clv_current"),
    "avg_price_clv_current_pp": summary.get("avg_price_clv_current_pp"),
    "total_ev_current_dollars": summary.get("total_ev_current_dollars"),
    "avg_ev_current_dollars": summary.get("avg_ev_current_dollars"),
    "avg_ev_current_pct": summary.get("avg_ev_current_pct"),
}
hist_df = pd.DataFrame([hist_row])
if HISTORY.exists():
    old_hist = pd.read_csv(HISTORY)
    hist_df = pd.concat([old_hist, hist_df], ignore_index=True)
hist_df.to_csv(HISTORY, index=False)

# Add compact history to dashboard for the website chart.
dash["performance_history"] = hist_df.tail(250).where(pd.notna(hist_df), None).to_dict("records")

df.to_csv(BETS, index=False)

# Also write updated dashboard.
def deep_json_clean(obj):
    import math
    try:
        import pandas as pd
        if pd.isna(obj):
            return None
    except Exception:
        pass
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {str(k): deep_json_clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_json_clean(v) for v in obj]
    return obj

dash = deep_json_clean(dash)
DASH.write_text(json.dumps(dash, indent=2, ensure_ascii=False, allow_nan=False))

audit_combined = []
audit_combined.extend(audit_rows or [])
for r in game_audit_rows:
    audit_combined.append({
        "source": r.get("source"),
        "win_total_rows": 0,
        "futures_rows": 0,
        "game_line_rows": r.get("game_line_rows"),
        "columns": r.get("columns"),
    })

pd.DataFrame(audit_combined or [{"source":"none", "win_total_rows":0, "futures_rows":0, "game_line_rows":0, "columns":""}]).to_csv(AUDIT, index=False)

print("wrote:", BETS)
print("wrote:", DASH)
print("wrote:", AUDIT)
print("win market rows:", len(win_rows))
print("futures market rows:", len(fut_rows))
print("game line rows:", len(game_rows))
print("clv matched:", summary["current_clv_matched"])
print("clv positive:", summary["current_clv_positive"])
print("pct beating clv:", summary["pct_bets_beating_current_clv"])
print("avg line clv:", summary["avg_line_clv_current"])
print("avg price clv pp:", summary["avg_price_clv_current_pp"])
