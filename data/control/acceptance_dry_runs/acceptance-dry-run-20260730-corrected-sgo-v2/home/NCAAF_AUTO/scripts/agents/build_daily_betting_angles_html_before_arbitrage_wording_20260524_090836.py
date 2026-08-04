#!/usr/bin/env python3

from __future__ import annotations

import html
from datetime import date
from pathlib import Path

import pandas as pd


OUT = Path("data/agents/daily_betting_angles.html")
MOVES_CSV = Path("daily_market_movement_report.csv")
ARBS_CSV = Path("market_arbitrage_opportunities.csv")
ANGLES_CSV = Path("data/agents/daily_betting_angles.csv")


def esc(x) -> str:
    if pd.isna(x):
        return ""
    return html.escape(str(x))


def fmt_odds(x) -> str:
    if pd.isna(x):
        return ""
    try:
        v = float(x)
    except Exception:
        return esc(x)
    if abs(v) >= 100:
        return f"{int(v):+d}"
    return f"{v:g}"


def fmt_num(x, suffix: str = "") -> str:
    if pd.isna(x):
        return ""
    try:
        v = float(x)
    except Exception:
        return esc(x)
    if abs(v) >= 100:
        return f"{v:,.0f}{suffix}"
    if abs(v) >= 10:
        return f"{v:,.1f}{suffix}"
    return f"{v:,.2f}{suffix}"


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def build_move_cards(moves: pd.DataFrame, limit: int = 25) -> str:
    if moves.empty:
        return '<p class="muted">No daily market movement file was available for this run.</p>'

    df = moves.copy()

    for col in ["implied_prob_change_pct", "change"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "implied_prob_change_pct" in df.columns:
        df["_sort_prob"] = df["implied_prob_change_pct"].abs()
    else:
        df["_sort_prob"] = 0

    if "change" in df.columns:
        df["_sort_change"] = df["change"].abs()
    else:
        df["_sort_change"] = 0

    df = df.sort_values(["_sort_prob", "_sort_change"], ascending=False).head(limit)

    cards = []
    for _, r in df.iterrows():
        market = esc(r.get("market", "Market Move"))
        team = esc(r.get("team", ""))
        book = esc(r.get("book", ""))
        field = esc(r.get("field", ""))
        conference = esc(r.get("conference", ""))
        prev_date = esc(r.get("snapshot_prev", ""))
        latest_date = esc(r.get("snapshot_latest", ""))
        move_date = esc(r.get("move_date", ""))
        previous = fmt_odds(r.get("previous", ""))
        latest = fmt_odds(r.get("latest", ""))
        change = fmt_num(r.get("change", ""))
        prob_move = fmt_num(r.get("implied_prob_change_pct", ""), "%")
        summary = esc(r.get("summary", ""))

        conf_html = f'<span class="meta-pill">{conference}</span>' if conference else ""
        prob_html = f'<span class="impact">Implied prob move: {prob_move}</span>' if prob_move else ""
        change_html = f'<span class="impact">Odds move: {change}</span>' if change else ""

        cards.append(f"""
        <div class="card move-card">
          <div class="card-top">
            <span class="badge move">MOVE</span>
            <span class="title">{team} — {field}</span>
          </div>
          <div class="line">{book} moved <strong>{previous}</strong> → <strong>{latest}</strong></div>
          <div class="meta">
            <span class="meta-pill">{market}</span>
            {conf_html}
            <span class="meta-pill">Move date: {move_date}</span>
            <span class="meta-pill">Snapshots: {prev_date} → {latest_date}</span>
          </div>
          <div class="impact-row">
            {prob_html}
            {change_html}
          </div>
          <div class="reason">{summary}</div>
        </div>
        """)

    return "\n".join(cards)


def build_arb_cards(arbs: pd.DataFrame, limit: int = 15) -> str:
    if arbs.empty:
        return '<p class="muted">No current arbitrage or middle opportunities were available for this run.</p>'

    df = arbs.copy()
    for col in ["edge_pct", "middle_score", "implied_sum_pct"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    sort_col = "edge_pct" if "edge_pct" in df.columns else "middle_score"
    if sort_col in df.columns:
        df = df.sort_values(sort_col, ascending=False)

    df = df.head(limit)

    cards = []
    for _, r in df.iterrows():
        typ = esc(r.get("type", "Inefficiency"))
        team = esc(r.get("team", ""))
        win_total = esc(r.get("win_total", ""))
        side_1 = esc(r.get("side_1", ""))
        side_2 = esc(r.get("side_2", ""))
        book_1 = esc(r.get("book_1", ""))
        book_2 = esc(r.get("book_2", ""))
        odds_1 = fmt_odds(r.get("odds_1", ""))
        odds_2 = fmt_odds(r.get("odds_2", ""))
        edge = fmt_num(r.get("edge_pct", ""), "%")
        implied_sum = fmt_num(r.get("implied_sum_pct", ""), "%")
        middle_score = fmt_num(r.get("middle_score", ""))
        notes = esc(r.get("notes", ""))

        score_bits = []
        if edge:
            score_bits.append(f"Edge: {edge}")
        if implied_sum:
            score_bits.append(f"Implied sum: {implied_sum}")
        if middle_score:
            score_bits.append(f"Middle score: {middle_score}")
        score_html = " · ".join(score_bits)

        cards.append(f"""
        <div class="card arb-card">
          <div class="card-top">
            <span class="badge arb">{typ.upper()}</span>
            <span class="title">{team} {side_1} / {side_2}</span>
          </div>
          <div class="line">{book_1} <strong>{odds_1}</strong> vs {book_2} <strong>{odds_2}</strong> on total {win_total}</div>
          <div class="meta">
            <span class="meta-pill">Current board</span>
            <span class="meta-pill">{score_html}</span>
          </div>
          <div class="reason">{notes}</div>
        </div>
        """)

    return "\n".join(cards)


def build_game_line_cards(angles: pd.DataFrame, limit: int = 18) -> str:
    if angles.empty or "category" not in angles.columns:
        return '<p class="muted">No game line edges were available for this run.</p>'

    df = angles[angles["category"].eq("Game line edge")].copy()
    if df.empty:
        return '<p class="muted">No game line edges were available for this run.</p>'

    if "score" in df.columns:
        df["score_num"] = pd.to_numeric(df["score"], errors="coerce")
        df = df.sort_values(["score_num"], ascending=False)

    df = df.head(limit)

    cards = []
    for _, r in df.iterrows():
        title = esc(r.get("title", ""))
        grade = esc(r.get("grade", ""))
        score = fmt_num(r.get("score", ""))
        reason = esc(r.get("reason", ""))
        source = esc(r.get("source", ""))

        score_html = f'<span class="meta-pill">BetScore: {score}</span>' if score else ""
        source_html = f'<span class="meta-pill">{source}</span>' if source else ""

        cards.append(f"""
        <div class="card game-card">
          <div class="card-top">
            <span class="badge game">{grade or "GAME"}</span>
            <span class="title">{title}</span>
          </div>
          <div class="meta">
            {score_html}
            {source_html}
          </div>
          <div class="reason">{reason}</div>
        </div>
        """)

    return "\n".join(cards)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    moves_all = load_csv(MOVES_CSV)
    arbs = load_csv(ARBS_CSV)
    angles = load_csv(ANGLES_CSV)

    latest_date = date.today().isoformat()
    moves = moves_all.copy()

    # Email should show only the latest daily changes, not the full multi-day movement report.
    # Prefer snapshot_latest, then move_date if available.
    if not moves.empty:
        if "snapshot_latest" in moves.columns:
            vals = moves["snapshot_latest"].dropna().astype(str)
            if not vals.empty:
                latest_date = vals.max()
                moves = moves[moves["snapshot_latest"].astype(str) == latest_date].copy()
        elif "move_date" in moves.columns:
            vals = moves["move_date"].dropna().astype(str)
            if not vals.empty:
                latest_date = vals.max()
                moves = moves[moves["move_date"].astype(str) == latest_date].copy()

        # Extra guard: if move_date exists, keep only moves that happened on the latest report date.
        if "move_date" in moves.columns:
            moves = moves[moves["move_date"].astype(str) == latest_date].copy()

    move_count = len(moves)
    arb_count = len(arbs)
    game_count = len(angles[angles["category"].eq("Game line edge")]) if not angles.empty and "category" in angles.columns else 0

    move_cards = build_move_cards(moves, limit=25)
    game_cards = build_game_line_cards(angles, limit=18)
    arb_cards = build_arb_cards(arbs, limit=15)

    doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Daily NCAAF Market Alert — {latest_date}</title>
<style>
  body {{
    margin: 0;
    padding: 0;
    background: #f4f7fb;
    color: #111827;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  }}
  .wrap {{
    max-width: 980px;
    margin: 0 auto;
    padding: 28px 22px 40px;
  }}
  h1 {{
    font-size: 34px;
    line-height: 1.15;
    margin: 0 0 14px;
    color: #111827;
  }}
  h2 {{
    font-size: 24px;
    margin: 32px 0 12px;
    color: #1f3c88;
    border-bottom: 3px solid #cbd5e1;
    padding-bottom: 12px;
  }}
  .summary {{
    font-size: 18px;
    line-height: 1.45;
    color: #334155;
    margin-bottom: 18px;
  }}
  .subline {{
    color: #64748b;
    font-size: 15px;
    margin: 0 0 18px;
  }}
  .card {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 14px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.08);
    padding: 18px 20px;
    margin: 14px 0;
  }}
  .card-top {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }}
  .badge {{
    display: inline-block;
    border-radius: 999px;
    color: #fff;
    font-weight: 800;
    font-size: 13px;
    padding: 7px 12px;
    letter-spacing: .02em;
  }}
  .badge.move {{ background: #2563eb; }}
  .badge.arb {{ background: #16a34a; }}
  .title {{
    font-size: 20px;
    font-weight: 800;
    color: #0f172a;
  }}
  .line {{
    font-size: 18px;
    color: #1f2937;
    margin: 6px 0 10px;
  }}
  .meta {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 8px 0;
  }}
  .meta-pill {{
    display: inline-block;
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    border-radius: 999px;
    padding: 5px 9px;
    font-size: 13px;
    color: #334155;
    font-weight: 650;
  }}
  .impact-row {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin: 9px 0;
  }}
  .impact {{
    font-size: 15px;
    font-weight: 800;
    color: #0f766e;
  }}
  .reason {{
    font-size: 15px;
    color: #475569;
    line-height: 1.4;
    margin-top: 6px;
  }}
  .muted {{
    color: #64748b;
    font-size: 16px;
  }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>Daily NCAAF Market Alert — {latest_date}</h1>
    <div class="summary">
      Daily market moves are listed first so you can quickly see what changed since the previous snapshot.
      Game line edges and current arbitrage/middle opportunities are included after the move section.
    </div>
    <div class="subline">
      Market moves in this report: {move_count} · Game line edges: {game_count} · Current inefficiencies: {arb_count}
    </div>

    <h2>Daily Market Moves</h2>
    <p class="muted">Top win total and conference futures moves from the latest daily report. Cards include the move date and snapshot window.</p>
    {move_cards}

    <h2>Game Line Edges</h2>
    <p class="muted">Top spread and total edges from Market Lab using available market prices. Confirm live prices before betting.</p>
    {game_cards}


    <h2>Current Inefficiencies</h2>
    <p class="muted">Current arbitrage or middle opportunities available on the latest board.</p>
    {arb_cards}
  </div>
</body>
</html>
"""

    OUT.write_text(doc, encoding="utf-8")
    print(f"Wrote {OUT}: {move_count} market moves, {game_count} game line edges, {arb_count} inefficiencies")


if __name__ == "__main__":
    main()
