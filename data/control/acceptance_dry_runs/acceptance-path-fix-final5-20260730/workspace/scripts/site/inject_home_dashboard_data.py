#!/usr/bin/env python3
import json
import re
from pathlib import Path

import pandas as pd

FILES = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

ANGLES = Path("data/agents/daily_betting_angles.csv")
ARBS = Path("market_arbitrage_opportunities.csv")
GAME_MOVES = Path("data/odds/game_line_movement_report.csv")
ACTION_LINES = Path("data/odds/actionnetwork_season_game_lines_2026.csv")

def load(path):
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def clean_val(v):
    if pd.isna(v):
        return None
    if hasattr(v, "item"):
        try:
            v = v.item()
        except Exception:
            pass
    return v


def first_nonempty(row, names):
    for name in names:
        if name in row.index:
            v = row.get(name)
            if not pd.isna(v) and str(v).strip():
                return str(v).strip()
    return ""

def add_arb_display_fields(df):
    if df.empty:
        return df
    d = df.copy()
    titles = []
    summaries = []
    for _, r in d.iterrows():
        typ = first_nonempty(r, ["type", "category"]) or "Arb"
        team = first_nonempty(r, ["team", "side", "market", "game"])
        book_a = first_nonempty(r, ["book_a", "book1", "over_book", "home_book", "book"])
        book_b = first_nonempty(r, ["book_b", "book2", "under_book", "away_book"])
        edge = r.get("edge_pct") if "edge_pct" in r.index else None
        middle = r.get("middle_score") if "middle_score" in r.index else None

        metric = ""
        try:
            if edge is not None and not pd.isna(edge):
                metric = f"{float(edge):.2f}%"
            elif middle is not None and not pd.isna(middle):
                metric = f"middle score {float(middle):.1f}"
        except Exception:
            metric = ""

        title_parts = [typ]
        if team:
            title_parts.append(team)
        if metric:
            title_parts.append(metric)
        title = ": ".join([title_parts[0], " · ".join(title_parts[1:])]) if len(title_parts) > 1 else typ

        books = " vs ".join([x for x in [book_a, book_b] if x])
        summary_bits = []
        if books:
            summary_bits.append(books)
        for c in ["summary", "reason", "current_line", "bet_a", "bet_b"]:
            val = first_nonempty(r, [c])
            if val and val not in summary_bits:
                summary_bits.append(val)

        titles.append(title)
        summaries.append(" · ".join(summary_bits))

    d["dashboard_title"] = titles
    d["dashboard_summary"] = summaries
    return d

def rows(df, limit=6, cols=None):
    if df.empty:
        return []
    out = []
    d = df.head(limit)
    for _, r in d.iterrows():
        item = {}
        for c in (cols or list(d.columns)):
            if c in d.columns:
                item[c] = clean_val(r.get(c))
        out.append(item)
    return out

angles = load(ANGLES)
arbs = load(ARBS)
game_moves = load(GAME_MOVES)
action = load(ACTION_LINES)

game_edges = pd.DataFrame()
market_moves = pd.DataFrame()
arb_angles = pd.DataFrame()

if not angles.empty and "category" in angles.columns:
    game_edges = angles[angles["category"].astype(str).eq("Game line edge")].copy()
    market_moves = angles[angles["category"].astype(str).eq("Market move")].copy()
    arb_angles = angles[angles["category"].astype(str).eq("Arbitrage")].copy()

for df in [game_edges, market_moves, arb_angles]:
    if "score" in df.columns:
        df["score_num"] = pd.to_numeric(df["score"], errors="coerce")
        df.sort_values("score_num", ascending=False, inplace=True)
    elif "ev_pct" in df.columns:
        df["ev_num"] = pd.to_numeric(df["ev_pct"], errors="coerce")
        df.sort_values("ev_num", ascending=False, inplace=True)

if not arbs.empty:
    for c in ["edge_pct", "middle_score", "implied_sum_pct"]:
        if c in arbs.columns:
            arbs[c] = pd.to_numeric(arbs[c], errors="coerce")
    if "edge_pct" in arbs.columns:
        arbs = arbs.sort_values("edge_pct", ascending=False)

arbs = add_arb_display_fields(arbs)
arb_angles = add_arb_display_fields(arb_angles)

latest_action_pull = None
if not action.empty:
    for c in ["market_spread_last_update", "market_total_last_update", "snapshot_ts", "pulled_at"]:
        if c in action.columns:
            vals = action[c].dropna().astype(str)
            if len(vals):
                latest_action_pull = sorted(vals)[-1]
                break

dashboard = {
    "counts": {
        "game_line_edges": int(len(game_edges)),
        "market_moves": int(len(market_moves)),
        "arbitrage_angles": int(len(arb_angles)),
        "game_line_moves": int(len(game_moves)),
        "action_games": int(len(action)),
    },
    "top_game_edges": rows(game_edges, 6, [
        "title", "team", "book", "current_line", "projected_line", "ev_pct", "score", "reason", "game_week"
    ]),
    "top_arbs": rows(arbs if not arbs.empty else arb_angles, 200, [
        "dashboard_title", "dashboard_summary", "title", "team", "type", "edge_pct", "middle_score", "summary", "reason", "book", "current_line"
    ,
        "quality",
        "win_total",
        "side_1",
        "book_1",
        "odds_1",
        "side_2",
        "book_2",
        "odds_2",
        "implied_sum_pct",
        "notes"]),
    "top_market_moves": rows(market_moves, 300, [
        "title", "team", "book", "reason", "next_step", "score"
    ,
        "market",
        "snapshot_prev",
        "snapshot_latest",
        "move_date",
        "season",
        "conference",
        "field",
        "previous",
        "latest",
        "change",
        "implied_prob_change_pct",
        "summary"]),
    "top_game_moves": rows(game_moves, 6, [
        "date", "week", "away_team", "home_team", "market", "book", "previous", "latest", "change", "summary"
    ,
        "snapshot_prev",
        "snapshot_latest",
        "source_prev",
        "source_latest",
        "previous_price",
        "latest_price"]),
    "data_status": {
        "latest_action_pull": latest_action_pull,
    },
}

for p in FILES:
    if not p.exists():
        continue

    txt = p.read_text(errors="ignore")
    m = re.search(r'(<script id="db" type="application/json">)(.*?)(</script>)', txt, re.S)
    if not m:
        print(f"{p}: DB script not found")
        continue

    db = json.loads(m.group(2))
    db["dashboard"] = dashboard

    new_json = json.dumps(db, separators=(",", ":"), ensure_ascii=False)
    txt = txt[:m.start(2)] + new_json + txt[m.end(2):]
    p.write_text(txt)
    print(f"{p}: injected dashboard data")

print("counts:", dashboard["counts"])
