#!/usr/bin/env python3

from __future__ import annotations
import re

import html
from datetime import date
from pathlib import Path

import pandas as pd


OUT = Path("data/agents/daily_betting_angles.html")
MOVES_CSV = Path("daily_market_movement_report.csv")
ARBS_CSV = Path("market_arbitrage_opportunities.csv")
GAME_LINE_MOVES_CSV = Path("data/odds/game_line_movement_report.csv")
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

    # New/cleaned agent schema: category, title, score, reason.
    # Old movement schema: market, team, field, previous, latest, summary.
    is_agent_schema = "title" in df.columns and "reason" in df.columns

    if is_agent_schema:
        def score_sort_value(x):
            try:
                return abs(float(str(x).replace("%", "").strip()))
            except Exception:
                return 0.0

        if "score" in df.columns:
            df["_sort_score"] = df["score"].apply(score_sort_value)
        else:
            df["_sort_score"] = 0.0

        df = df.sort_values("_sort_score", ascending=False).head(limit)

        cards = []
        for _, r in df.iterrows():
            title = esc(r.get("title", "Market move"))
            score = esc(r.get("score", ""))
            reason = esc(r.get("reason", ""))

            score_html = f'<span class="meta-pill">Move: {score}</span>' if score and score.lower() not in {"nan", "none", "null"} else ""

            cards.append(f"""
          <div class="card move-card">
            <div class="card-top">
              <span class="badge move">MOVE</span>
              <span class="title">{title}</span>
            </div>
            <div class="meta">
              {score_html}
              <span class="meta-pill">Market move</span>
            </div>
            <div class="reason">{reason}</div>
          </div>
          """)

        return "\n".join(cards)

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
              <span class="title">{move_date} · {team} — {field}</span>
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


def short_date(x) -> str:
    """Return YYYY-MM-DD from ISO timestamp/date strings."""
    if pd.isna(x):
        return ""
    s = str(x).strip()
    if not s:
        return ""
    return s[:10]


def build_game_line_move_cards(moves: pd.DataFrame, limit: int = 20) -> str:
    if moves.empty:
        return ""

    df = moves.copy()

    # Only show game-line movement when it matches a current actionable best-line edge.
    # This prevents stale/noisy movement from appearing when a better line exists elsewhere.
    edges = load_csv(ANGLES_CSV)
    if edges.empty or "category" not in edges.columns:
        return ""

    edge_rows = edges[edges["category"].astype(str).eq("Game line edge")].copy()
    if edge_rows.empty:
        return ""

    def norm_line_value(x):
        try:
            v = float(x)
            return f"{v:.1f}".rstrip("0").rstrip(".")
        except Exception:
            return str(x or "").strip()

    def is_actionable_move(r):
        market = str(r.get("market", "")).strip().lower()

        # Current edge builder is ATS-only. When total edge rows are added later,
        # this can be expanded to allow market == "total" too.
        if market != "spread":
            return False

        away = str(r.get("away_team", "")).strip()
        home = str(r.get("home_team", "")).strip()
        game = f"{away} at {home}"
        book = str(r.get("book", "")).strip().lower()
        latest = norm_line_value(r.get("latest", ""))

        if not game.strip() or not book:
            return False

        for _, e in edge_rows.iterrows():
            reason = str(e.get("reason", ""))
            edge_book = str(e.get("book", "")).strip().lower()
            current_line = str(e.get("current_line", ""))

            if game in reason and edge_book == book and latest in current_line:
                return True

        return False

    df = df[df.apply(is_actionable_move, axis=1)].copy()
    if df.empty:
        return ""

    if "change" in df.columns:
        df["change_num"] = pd.to_numeric(df["change"], errors="coerce").abs()
        df = df.sort_values("change_num", ascending=False)

    df = df.head(limit)

    cards = []
    for _, r in df.iterrows():
        market = esc(r.get("market", "Game Line Move"))
        book = esc(r.get("book", ""))
        previous = esc(r.get("previous", ""))
        latest = esc(r.get("latest", ""))

        away = esc(r.get("away_team", ""))
        home = esc(r.get("home_team", ""))
        game = f"{away} at {home}".strip()
        if game == "at":
            game = ""

        game_date = esc(short_date(r.get("date", "")))
        week_raw = r.get("week", "")
        week = ""
        if not pd.isna(week_raw) and str(week_raw).strip():
            try:
                week = str(int(float(week_raw)))
            except Exception:
                week = esc(week_raw)

        prev_snap = esc(short_date(r.get("snapshot_prev", "")))
        latest_snap = esc(short_date(r.get("snapshot_latest", "")))
        move_date = latest_snap

        game_date_html = f'<span class="meta-pill">Game date: {game_date}</span>' if game_date else ""
        week_html = f'<span class="meta-pill">Week {week}</span>' if week else ""
        move_date_html = f'<span class="meta-pill">Move date: {move_date}</span>' if move_date else ""
        snapshots_html = f'<span class="meta-pill">Snapshots: {prev_snap} → {latest_snap}</span>' if prev_snap or latest_snap else ""

        # Betting-focused reason: this movement matches a current actionable best-line edge.
        side_team = ""
        try:
            matched_edges = edge_rows[
                edge_rows["reason"].astype(str).str.contains(game, regex=False, na=False)
                & edge_rows["book"].astype(str).str.lower().eq(str(book).lower())
            ]
            if not matched_edges.empty:
                side_team = str(matched_edges.iloc[0].get("team", "")).strip()
        except Exception:
            side_team = ""

        if market.lower() == "spread" and side_team:
            clean_summary = f"Best current edge line improved to {side_team} {latest} at {book} after moving from {side_team} {previous}."
        elif game:
            clean_summary = f"Best current edge line moved {previous} → {latest} at {book}."
        else:
            clean_summary = f"{market} moved {previous} → {latest}."

        cards.append(f"""
        <div class="card move-card">
          <div class="card-top">
            <span class="badge move">GAME MOVE</span>
            <span class="title">{game} — {market}</span>
          </div>
          <div class="line">{book} moved <strong>{previous}</strong> → <strong>{latest}</strong></div>
          <div class="meta">
            <span class="meta-pill">{market}</span>
            {game_date_html}
            {week_html}
            {move_date_html}
            {snapshots_html}
          </div>
          <div class="reason">{clean_summary}</div>
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

    if "ev_pct" in df.columns:
        df["ev_num"] = pd.to_numeric(df["ev_pct"], errors="coerce")
    else:
        df["ev_num"] = 0

    if "score" in df.columns:
        df["score_num"] = pd.to_numeric(df["score"], errors="coerce")
    else:
        df["score_num"] = 0

    df = df.sort_values(["ev_num", "score_num"], ascending=[False, False])
    df = df.head(limit)

    cards = []
    for _, r in df.iterrows():
        title = esc(r.get("title", ""))
        grade = esc(r.get("grade", ""))
        score = fmt_num(r.get("score", ""))
        reason = esc(r.get("reason", ""))

        projected_line = esc(r.get("projected_line", ""))
        book = esc(r.get("book", ""))
        opening_line = esc(r.get("opening_line", ""))
        last_move_date = esc(r.get("last_move_date", ""))
        game_date = esc(r.get("game_date", ""))
        raw_week = r.get("game_week", "")
        try:
            game_week = str(int(float(raw_week))) if str(raw_week).strip() not in ["", "nan", "None"] else ""
        except Exception:
            game_week = esc(raw_week)
        ev_pct = fmt_num(r.get("ev_pct", ""), "%")

        title_extra = f' <span class="muted">· {projected_line}</span>' if projected_line else ""
        score_html = f'<span class="meta-pill">BetScore: {score}</span>' if score else ""
        ev_html = f'<span class="meta-pill">EV: {ev_pct}</span>' if ev_pct else ""
        book_html = f'<span class="meta-pill">Book: {book}</span>' if book else ""
        open_html = f'<span class="meta-pill">Open: {opening_line}</span>' if opening_line else ""
        last_move_html = f'<span class="meta-pill">Last move: {last_move_date}</span>' if last_move_date else ""
        if game_week and game_date:
            game_date_html = f'<span class="meta-pill">Game: Week {game_week} · {game_date}</span>'
        elif game_date:
            game_date_html = f'<span class="meta-pill">Game: {game_date}</span>'
        else:
            game_date_html = ""

        cards.append(f"""
        <div class="card game-card">
          <div class="card-top">
            <span class="badge game">{grade or "GAME"}</span>
            <span class="title">{title}{title_extra}</span>
          </div>
          <div class="meta">
            {score_html}
            {ev_html}
            {book_html}
            {open_html}
            {last_move_html}
            {game_date_html}
          </div>
          <div class="reason">{reason}</div>
        </div>
        """)

    return "\n".join(cards)


def prepare_agent_game_line_moves(angle_rows, limit=12):
    # Prepare cleaned agent game-line rows for concise email display.
    if angle_rows is None or angle_rows.empty:
        return pd.DataFrame()

    df = angle_rows.copy()
    for column in ["category", "title", "reason", "score", "source"]:
        if column not in df.columns:
            df[column] = ""

    df = df[
        df["category"].fillna("").astype(str).str.casefold().eq("game line move")
    ].copy()

    if df.empty:
        return df

    price_only = df["title"].fillna("").astype(str).str.contains(
        r"\b(?:Spread|Total)\b.*\b(?:Price|Over Price|Under Price)\b",
        case=False,
        regex=True,
    )
    df = df.loc[~price_only].copy()

    extracted = df["title"].fillna("").astype(str).str.extract(
        r"\b(?:Spread|Total)\s+"
        r"(?P<previous>[+-]?\d+(?:\.\d+)?)\s*"
        r"(?:→|->|=>|to)\s*"
        r"(?P<latest>[+-]?\d+(?:\.\d+)?)",
        flags=re.IGNORECASE,
    )

    df["_previous_line"] = pd.to_numeric(extracted["previous"], errors="coerce")
    df["_latest_line"] = pd.to_numeric(extracted["latest"], errors="coerce")
    df = df[
        df["_previous_line"].notna()
        & df["_latest_line"].notna()
        & (df["_latest_line"] - df["_previous_line"]).abs().gt(0)
    ].copy()

    if df.empty:
        return df

    df["_move_size"] = (
        df["_latest_line"] - df["_previous_line"]
    ).abs()

    def clean_reason(value):
        text = "" if pd.isna(value) else str(value)
        text = re.sub(
            r"\s*·\s*price\s*[^·]*",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"\bnan\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip(" ·|")

    df["reason"] = df["reason"].map(clean_reason)
    df["_title_key"] = (
        df["title"].fillna("").astype(str).str.casefold()
        .str.replace(r"\s+", " ", regex=True).str.strip()
    )
    df = df.drop_duplicates("_title_key", keep="first")
    df = df.sort_values(["_move_size", "title"], ascending=[False, True]).head(limit)
    df["score"] = df["_move_size"]

    return df.drop(
        columns=["_previous_line", "_latest_line", "_move_size", "_title_key"],
        errors="ignore",
    )


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    moves_all = load_csv(MOVES_CSV)
    arbs = load_csv(ARBS_CSV)
    angles = load_csv(ANGLES_CSV)
    game_line_moves = load_csv(GAME_LINE_MOVES_CSV)

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

    # CLEANED_GAME_LINE_EMAIL_START
    angle_market_moves = pd.DataFrame()
    angle_game_line_moves = pd.DataFrame()

    if not angles.empty and "category" in angles.columns:
        normalized_category = (
            angles["category"].fillna("").astype(str).str.casefold()
        )
        angle_market_moves = angles[
            normalized_category.eq("market move")
        ].copy()
        angle_game_line_moves = prepare_agent_game_line_moves(
            angles,
            limit=12,
        )

    if not angle_market_moves.empty:
        moves = angle_market_moves.copy()

    if not angle_game_line_moves.empty:
        game_line_moves = angle_game_line_moves.copy()

    move_count = len(moves)
    game_move_count = len(game_line_moves)
    # CLEANED_GAME_LINE_EMAIL_END

    game_count = len(angles[angles["category"].eq("Game line edge")]) if not angles.empty and "category" in angles.columns else 0

    # Email should count/display true arbitrage separately from middle opportunities.
    arbs_display = arbs.copy()
    if not arbs_display.empty:
        if "type" in arbs_display.columns:
            arbs_display = arbs_display[arbs_display["type"].astype(str).str.contains("arb", case=False, na=False)].copy()
        elif "category" in arbs_display.columns:
            arbs_display = arbs_display[arbs_display["category"].astype(str).str.contains("arb", case=False, na=False)].copy()

    arb_count = len(arbs_display)

    if not angle_market_moves.empty:
        move_cards = build_agent_cards(moves, limit=25) if "build_agent_cards" in globals() else build_move_cards(moves, limit=25)
    else:
        move_cards = build_move_cards(moves, limit=25)

    if not angle_game_line_moves.empty:
        game_line_move_cards = build_move_cards(
            angle_game_line_moves,
            limit=12,
        )
    else:
        game_line_move_cards = build_game_line_move_cards(
            game_line_moves,
            limit=12,
        )

    game_cards = build_game_line_cards(angles, limit=18)
    arb_cards = build_arb_cards(arbs_display, limit=15)

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
      Game line moves are listed first so you can quickly see the largest spread and total changes.
      Futures market moves, game line edges, and current arbitrage opportunities follow.
    </div>
    <div class="subline">
      Game line moves in this report: {game_move_count} · Market moves: {move_count} · Game line edges: {game_count} · Arbitrage opportunities: {arb_count}
    </div>

    <h2>Game Line Moves</h2>
    <p class="muted">Largest actual spread and total changes from the latest daily snapshot. Juice-only changes are excluded.</p>
    {game_line_move_cards}

    <h2>Daily Market Moves</h2>
    <p class="muted">Top win total, conference futures, and playoff price moves from the latest daily report.</p>
    {move_cards}

    <h2>Game Line Edges</h2>
    <p class="muted">Top spread and total edges from Market Lab using available market prices. Confirm live prices before betting.</p>
    {game_cards}


    <h2>Arbitrage</h2>
    <p class="muted">Current arbitrage opportunities available on the latest board.</p>
    {arb_cards}
  </div>
</body>
</html>
"""

    OUT.write_text(doc, encoding="utf-8")
    print(f"Wrote {OUT}: {move_count} market moves, {game_move_count} game line moves, {game_count} game line edges, {arb_count} arbitrage opportunities")


if __name__ == "__main__":
    main()
