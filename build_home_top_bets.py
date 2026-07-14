#!/usr/bin/env python3
from pathlib import Path
import json, re
import pandas as pd
from datetime import datetime

INDEX = Path("index.html")
OUT_JSON = Path("data/agents/home_top_bets.json")
OUT_CSV = Path("data/agents/home_top_bets.csv")

DB_RE = re.compile(r'<script id="db" type="application/json">(.*?)</script>', re.S)

def n(v):
    try:
        if pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None

def pct_from_american(odds):
    o = n(odds)
    if o is None or o == 0:
        return None
    return 100 / (o + 100) if o > 0 else abs(o) / (abs(o) + 100)

def fmt_pct(x):
    if x is None:
        return "—"
    return f"{x*100:.1f}%".replace(".0%", "%")

def fmt_signed(x, suffix=""):
    if x is None:
        return "—"
    return f"{x:+.1f}{suffix}".replace("+0.0", "0").replace("-0.0", "0")

def main():
    html = INDEX.read_text(errors="ignore")
    m = DB_RE.search(html)
    if not m:
        raise SystemExit("DB not found")

    db = json.loads(m.group(1))
    teams = db.get("teams", [])
    games = db.get("games", [])

    candidates = []

    # Conference title edges from current model vs market.
    market_rows = []
    for key in ["market_futures_edges", "market_conference_futures_edges", "market_conference_futures_raw"]:
        market_rows.extend(db.get(key, []) or [])

    by_team_market = {}
    for r in market_rows:
        team = r.get("team")
        if not team or team in by_team_market:
            continue
        odds = r.get("best_title_odds", r.get("american_odds", r.get("current_american_odds")))
        implied = pct_from_american(odds)
        by_team_market[team] = {
            "odds": odds,
            "implied": implied,
            "book": r.get("best_title_book") or r.get("book") or "",
        }

    for t in teams:
        team = t.get("team")
        model = n(t.get("conference_title_pct"))
        if model is not None and model > 1:
            model = model / 100

        mkt = by_team_market.get(team, {})
        implied = mkt.get("implied")
        if model is None or implied is None:
            continue

        edge = model - implied
        if edge <= 0.03:
            continue

        candidates.append({
            "rank_score": edge * 100 + model * 15,
            "bucket": "Futures",
            "action": "Watch / compare price",
            "label": f"{team} — Conference Title",
            "market": "Conference Title",
            "edge": f"{edge*100:+.1f} pts",
            "confidence": "Medium",
            "summary": f"Model {fmt_pct(model)} vs market {fmt_pct(implied)} ({mkt.get('odds') or '—'} {mkt.get('book') or ''}).",
            "link_hash": "#simulations",
        })

    # Win total edges.
    wt_rows = []
    for key in ["market_win_totals_edges", "market_win_totals_raw"]:
        wt_rows.extend(db.get(key, []) or [])

    wt_by_team = {}
    for r in wt_rows:
        team = r.get("team")
        if not team or team in wt_by_team:
            continue
        total = n(r.get("market_total", r.get("win_total", r.get("current_win_total"))))
        wt_by_team[team] = {
            "total": total,
            "book": r.get("book") or r.get("best_over_book") or r.get("best_under_book") or "",
            "over": r.get("best_over_odds", r.get("over_odds")),
            "under": r.get("best_under_odds", r.get("under_odds")),
        }

    for t in teams:
        team = t.get("team")
        proj = n(t.get("avg_total_wins"))
        market = wt_by_team.get(team, {})
        total = market.get("total")
        if proj is None or total is None:
            continue

        edge = proj - total
        if abs(edge) < 0.35:
            continue

        side = "Over" if edge > 0 else "Under"
        candidates.append({
            "rank_score": abs(edge) * 10,
            "bucket": "Win Totals",
            "action": "Check best price",
            "label": f"{team} — {side} {total:g}",
            "market": "Win Total",
            "edge": fmt_signed(edge, " wins"),
            "confidence": "Medium" if abs(edge) >= 0.6 else "Low",
            "summary": f"Projected {proj:.2f} wins vs market {total:g}.",
            "link_hash": "#futures",
        })

    # Daily betting angles if available.
    angles_path = Path("data/agents/daily_betting_angles.csv")
    if angles_path.exists():
        a = pd.read_csv(angles_path)
        for _, r in a.head(12).iterrows():
            cat = str(r.get("category", ""))
            title = str(r.get("title", ""))
            reason = str(r.get("reason", ""))

            if "Game line edge" in cat:
                score = 18
                bucket = "Game Lines"
                action = "Check market"
            elif "Game line move" in cat:
                score = 16
                bucket = "Line Moves"
                action = "Monitor move"
            elif "Arbitrage" in cat:
                score = 15
                bucket = "Arbitrage"
                action = "Check availability"
            else:
                score = 8
                bucket = "Market"
                action = "Review"

            candidates.append({
                "rank_score": score,
                "bucket": bucket,
                "action": action,
                "label": title,
                "market": cat,
                "edge": "",
                "confidence": "Medium",
                "summary": reason,
                "link_hash": "#schedule",
            })

    # De-dupe and cap.
    seen = set()
    out = []
    for c in sorted(candidates, key=lambda x: x["rank_score"], reverse=True):
        key = (c["label"], c["market"])
        if key in seen:
            continue
        seen.add(key)
        c["rank"] = len(out) + 1
        out.append(c)
        if len(out) >= 8:
            break

    payload = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "items": out,
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.DataFrame(out).to_csv(OUT_CSV, index=False)

    print("wrote", OUT_JSON, "items:", len(out))
    print(pd.DataFrame(out)[["rank","bucket","label","edge","action"]].to_string(index=False) if out else "no items")

if __name__ == "__main__":
    main()
