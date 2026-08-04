#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from datetime import date
from pathlib import Path

import pandas as pd

HTML = Path("index_auto_market.html")
OUT = Path("data/agents/daily_betting_angles.csv")
HISTORY = Path("data/odds/game_line_history.csv")
MOVES = Path("data/odds/game_line_movement_report.csv")

MIN_EV = 1.0
MAX_GAME_ROWS = 18


def num(x):
    try:
        if x is None or x == "":
            return None
        v = float(x)
        if math.isnan(v):
            return None
        return v
    except Exception:
        return None


def fmt_price(x):
    v = num(x)
    if v is None:
        return "-110"
    return f"{int(v):+d}"


def fmt_points(x):
    v = num(x)
    if v is None:
        return ""
    return f"{v:.1f}".rstrip("0").rstrip(".")


def fmt_pct(x):
    v = num(x)
    if v is None:
        return ""
    return f"{v:+.1f}%"


def norm_team(v):
    s = "" if v is None else str(v).strip().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(university|college|the|of|at)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def ev_from_prob_and_odds(prob, odds):
    odds = num(odds)
    if odds is None:
        odds = -110
    if odds > 0:
        profit = odds / 100.0
    else:
        profit = 100.0 / abs(odds)
    return (prob * profit - (1 - prob)) * 100.0


def bet_score(edge_pts, ev_pct, books_count=None):
    edge_pts = abs(num(edge_pts) or 0)
    ev_pct = num(ev_pct) or 0
    books_count = num(books_count) or 1
    score = 50 + edge_pts * 7 + ev_pct * 1.2 + min(books_count, 8) * 1.5
    return max(0, min(100, score))


def load_db():
    if not HTML.exists():
        raise SystemExit(f"Missing {HTML}. Build index_auto_market.html first.")
    text = HTML.read_text()
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', text, re.S)
    if not m:
        raise SystemExit("Could not find embedded DB in index_auto_market.html")
    return json.loads(m.group(1))


def game_key_from_parts(date_val, away, home):
    return (
        str(date_val or "")[:10],
        norm_team(away),
        norm_team(home),
    )


def load_open_lookup():
    if not HISTORY.exists():
        return {}

    try:
        hist = pd.read_csv(HISTORY)
    except Exception:
        return {}

    if hist.empty:
        return {}

    hist.columns = [str(c).strip() for c in hist.columns]
    if "snapshot_date" not in hist.columns:
        return {}

    if "away_norm" not in hist.columns and "away_team" in hist.columns:
        hist["away_norm"] = hist["away_team"].map(norm_team)
    if "home_norm" not in hist.columns and "home_team" in hist.columns:
        hist["home_norm"] = hist["home_team"].map(norm_team)

    hist["date"] = hist.get("date", "").astype(str).str[:10]
    hist["snapshot_date"] = hist["snapshot_date"].astype(str)

    hist = hist.sort_values("snapshot_date")
    out = {}

    for _, r in hist.iterrows():
        k = game_key_from_parts(r.get("date"), r.get("away_team"), r.get("home_team"))
        if k not in out:
            out[k] = {
                "market_spread_home": num(r.get("market_spread_home")),
                "market_total": num(r.get("market_total")),
                "snapshot_date": r.get("snapshot_date"),
            }

    return out


def load_last_move_lookup():
    if not MOVES.exists():
        return {}

    try:
        df = pd.read_csv(MOVES)
    except Exception:
        return {}

    if df.empty:
        return {}

    df.columns = [str(c).strip() for c in df.columns]
    out = {}

    for _, r in df.iterrows():
        k = game_key_from_parts(r.get("date"), r.get("away_team"), r.get("home_team"))
        market = str(r.get("market", "")).lower()
        move_date = str(r.get("move_date", "") or r.get("snapshot_latest", "") or "")
        if not move_date:
            continue
        if "spread" in market:
            out[(k, "spread")] = max(out.get((k, "spread"), ""), move_date)
        if "total" in market:
            out[(k, "total")] = max(out.get((k, "total"), ""), move_date)

    return out


def team_line_display(team, line):
    v = num(line)
    if v is None:
        return ""
    if abs(v) < 0.0001:
        return f"{team} PK"
    return f"{team} {v:+.1f}".replace("+", "+").rstrip("0").rstrip(".")


def spread_side_info(g, edge):
    proj_home_margin = num(g.get("projected_margin_home"))
    market_home = num(g.get("market_spread_home"))

    if proj_home_margin is None or market_home is None:
        return None

    # Positive edge means value on home team. Negative means value on away team.
    if edge >= 0:
        side_team = g.get("home_team")
        current_side_line = market_home
        projected_side_line = -proj_home_margin
    else:
        side_team = g.get("away_team")
        current_side_line = -market_home
        projected_side_line = proj_home_margin

    return side_team, current_side_line, projected_side_line


def current_spread_title(side_team, current_line, price):
    return f"ATS: {team_line_display(side_team, current_line)} ({fmt_price(price)})"


def projected_spread_text(side_team, projected_line):
    return f"Proj: {team_line_display(side_team, projected_line)}"


def opening_spread_text(side_team, open_home_line, selected_is_home):
    if open_home_line is None:
        return ""
    side_line = open_home_line if selected_is_home else -open_home_line
    return team_line_display(side_team, side_line)


def total_title(side, total, price):
    return f"Total: {side} {fmt_points(total)} ({fmt_price(price)})"


def projected_total_text(proj_total):
    v = num(proj_total)
    if v is None:
        return ""
    return f"Proj: {fmt_points(v)}"


def read_existing_angles():
    if OUT.exists():
        try:
            df = pd.read_csv(OUT)
        except Exception:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    cols = [
        "run_date", "category", "title", "team", "grade", "score", "reason",
        "action", "source", "research_query", "book", "current_line",
        "projected_line", "opening_line", "last_move_date", "game_date"
    ]

    for c in cols:
        if c not in df.columns:
            df[c] = None

    return df


def main():
    db = load_db()
    games = db.get("games", [])

    run_date = date.today().isoformat()
    open_lookup = load_open_lookup()
    last_move_lookup = load_last_move_lookup()

    rows = []

    for g in games:
        proj_spread = num(g.get("projected_margin_home"))
        market_home = num(g.get("market_spread_home"))
        proj_total = num(g.get("projected_total"))
        market_total = num(g.get("market_total"))

        k = game_key_from_parts(g.get("date"), g.get("away_team"), g.get("home_team"))
        open_rec = open_lookup.get(k, {})
        game_label = f"{g.get('away_team')} at {g.get('home_team')}"
        books_count = g.get("market_books_count")

        # ATS edge.
        if proj_spread is not None and market_home is not None:
            edge = proj_spread + market_home
            side_info = spread_side_info(g, edge)
            if side_info:
                side_team, current_side_line, projected_side_line = side_info
                selected_is_home = side_team == g.get("home_team")
                price = g.get("market_spread_price") or -110
                prob = normal_cdf(abs(edge) / 17.0)
                ev = ev_from_prob_and_odds(prob, price)

                if ev >= MIN_EV:
                    open_line = opening_spread_text(side_team, open_rec.get("market_spread_home"), selected_is_home)
                    last_move_date = last_move_lookup.get((k, "spread"), "")

                    rows.append({
                        "run_date": run_date,
                        "category": "Game line edge",
                        "title": current_spread_title(side_team, current_side_line, price),
                        "team": side_team,
                        "grade": "ATS",
                        "score": round(bet_score(edge, ev, books_count), 2),
                        "reason": f"{game_label} · edge {side_team} {abs(edge):+.1f} · EV {ev:+.1f}%",
                        "action": "Confirm current sportsbook price before betting.",
                        "source": "Market Lab",
                        "research_query": "",
                        "book": g.get("market_spread_book") or "",
                        "current_line": team_line_display(side_team, current_side_line),
                        "projected_line": projected_spread_text(side_team, projected_side_line),
                        "opening_line": open_line,
                        "last_move_date": last_move_date,
                        "game_date": str(g.get("date") or "")[:10],
                        "game_week": g.get("week"),
                        "ev_pct": round(ev, 2),
                    })

        # Total edge.
        if proj_total is not None and market_total is not None:
            total_edge = proj_total - market_total
            side = "Over" if total_edge >= 0 else "Under"
            price = (
                g.get("market_total_over_price")
                if side == "Over"
                else g.get("market_total_under_price")
            ) or -110

            prob = normal_cdf(abs(total_edge) / 14.0)
            ev = ev_from_prob_and_odds(prob, price)

            if ev >= MIN_EV:
                open_total = open_rec.get("market_total")
                last_move_date = last_move_lookup.get((k, "total"), "")

                rows.append({
                    "run_date": run_date,
                    "category": "Game line edge",
                    "title": total_title(side, market_total, price),
                    "team": side,
                    "grade": "TOTAL",
                    "score": round(bet_score(total_edge, ev, books_count), 2),
                    "reason": f"{game_label} · edge {side} {abs(total_edge):+.1f} · EV {ev:+.1f}%",
                    "action": "Confirm current sportsbook price before betting.",
                    "source": "Market Lab",
                    "research_query": "",
                    "book": g.get("market_total_book") or "",
                    "current_line": f"{side} {fmt_points(market_total)}",
                    "projected_line": projected_total_text(proj_total),
                    "opening_line": fmt_points(open_total) if open_total is not None else "",
                    "last_move_date": last_move_date,
                    "game_date": str(g.get("date") or "")[:10],
                })

    new_rows = pd.DataFrame(rows)

    if not new_rows.empty:
        for c in ["ev_pct", "score"]:
            new_rows[c] = pd.to_numeric(new_rows[c], errors="coerce")
        new_rows = new_rows.sort_values(["ev_pct", "score"], ascending=[False, False]).head(MAX_GAME_ROWS)

    df = read_existing_angles()

    # Replace today's game-line rows so reruns do not duplicate.
    if not df.empty and "category" in df.columns:
        df = df[~((df["run_date"].astype(str) == run_date) & (df["category"] == "Game line edge"))]

    out = pd.concat([df, new_rows], ignore_index=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print(f"Appended game line edges: {len(new_rows)}")
    if not new_rows.empty:
        print(new_rows[["title", "projected_line", "book", "opening_line", "last_move_date", "game_week", "ev_pct", "grade", "score", "reason"]].to_string(index=False))


if __name__ == "__main__":
    main()
