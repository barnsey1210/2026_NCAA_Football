#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import html
import pandas as pd

OUT_CSV = Path("data/agents/daily_betting_angles.csv")
OUT_MD = Path("data/agents/daily_betting_angles.md")
OUT_HTML = Path("data/agents/daily_betting_angles.html")
GAME_MOVES = Path("data/odds/game_line_movement_report.csv")

PRIORITY = {
    "Game line move": 0,
    "Game line edge": 1,
    "Arbitrage": 2,
    "Middle": 3,
    "Market move": 4,
}

def esc(x):
    return html.escape(str(x or ""))

def fmt_line(x):
    try:
        v = float(x)
        if abs(v) == int(abs(v)):
            return f"{v:+.0f}"
        return f"{v:+.1f}"
    except Exception:
        return str(x or "")

def fmt_price(x):
    try:
        v = int(float(x))
        return f"{v:+d}" if v > 0 else str(v)
    except Exception:
        return str(x or "")

def clean_ts(x):
    s = str(x or "").strip()
    if not s or s.lower() == "nan":
        return ""
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        et = dt.astimezone(ZoneInfo("America/New_York"))
        return et.strftime("%Y-%m-%d %-I:%M %p %Z")
    except Exception:
        return s.replace("T", " ").replace("+00:00", " UTC").replace("Z", " UTC")

def make_game_line_move_rows():
    if not GAME_MOVES.exists():
        print(f"WARNING: missing {GAME_MOVES}")
        return pd.DataFrame()

    gm = pd.read_csv(GAME_MOVES)
    if gm.empty:
        print(f"WARNING: {GAME_MOVES} has 0 rows")
        return pd.DataFrame()

    rows = []
    for _, r in gm.iterrows():
        away = str(r.get("away_team", "") or "").strip()
        home = str(r.get("home_team", "") or "").strip()
        game = f"{away} at {home}".strip(" at ")
        market = str(r.get("market", "Line") or "Line").strip()
        book = str(r.get("book", "") or "").strip()
        prev = fmt_line(r.get("previous"))
        latest = fmt_line(r.get("latest"))
        change = fmt_line(r.get("change"))
        prev_price = fmt_price(r.get("previous_price"))
        latest_price = fmt_price(r.get("latest_price"))
        snap_prev = clean_ts(r.get("snapshot_prev"))
        snap_latest = clean_ts(r.get("snapshot_latest"))

        title_book = f"{book} " if book else ""
        title = f"{game} — {title_book}{market} {prev} → {latest}"

        reason_parts = []
        reason_parts.append(f"Moved {change} point(s)")
        if prev_price or latest_price:
            reason_parts.append(f"price {prev_price} → {latest_price}")
        if snap_prev or snap_latest:
            reason_parts.append(f"moved between {snap_prev or 'previous pull'} and {snap_latest or 'latest pull'}")

        reason = " · ".join(reason_parts)

        score = abs(float(r.get("change", 0) or 0))

        rows.append({
            "run_date": datetime.now().date().isoformat(),
            "category": "Game line move",
            "title": title,
            "team": "",
            "grade": "LINE MOVE",
            "score": score,
            "reason": reason,
            "action": "",
            "source": str(GAME_MOVES),
            "research_query": "",
        })

    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["score", "title"], ascending=[False, True])
    return out

def order_df(df):
    df = df.copy()
    df["_priority"] = df["category"].map(PRIORITY).fillna(99)
    df = df.sort_values(["_priority"], kind="stable").drop(columns=["_priority"])
    return df

def rewrite_markdown(df):
    lines = []
    lines.append(f"# Daily NCAAF Betting Angles — {datetime.now().date().isoformat()}")
    lines.append("")
    lines.append("Game line moves are listed first, then game-line edges, arbs/middles, and futures market moves.")
    lines.append("")

    if df.empty:
        lines.append("No angles generated.")
    else:
        for cat, group in df.groupby("category", sort=False):
            lines.append(f"## {cat}")
            lines.append("")
            for _, r in group.iterrows():
                score = str(r.get("score", "") or "").strip()
                score_txt = f" {score}" if score and score.lower() != "nan" else ""
                grade = str(r.get("grade", "") or "").strip()
                lines.append(f"- **{r.get('title','')}** — {grade}{score_txt}".rstrip())
                lines.append(f"  - {r.get('reason','')}")
                pass
            lines.append("")

    OUT_MD.write_text("\n".join(lines))

def badge_class(cat, grade):
    s = f"{cat} {grade}".lower()
    if "game line move" in s:
        return "move"
    if "game line edge" in s:
        return "edge"
    if "arb" in s:
        return "arb"
    if "middle" in s:
        return "mid"
    if "market move" in s:
        return "move"
    return ""

def card(row):
    cat = str(row.get("category", "") or "")
    grade = str(row.get("grade", "") or "")
    score = str(row.get("score", "") or "").strip()
    score_html = f"<span class='score'>{esc(score)}</span>" if score and score.lower() != "nan" else ""
    rq = str(row.get("research_query", "") or "").strip()
    research = f"<div class='research'>Research: <code>{esc(rq)}</code></div>" if rq and rq.lower() != "nan" else ""

    return f"""
    <div class="card">
      <div class="card-head"><span class="badge {badge_class(cat, grade)}">{esc(grade or cat)}</span> <strong>{esc(row.get("title",""))}</strong> {score_html}</div>
      <div class="reason">{esc(row.get("reason",""))}</div>
    </div>
    """

def rewrite_html(df):
    sections = []
    if df.empty:
        sections.append("<p>No angles generated.</p>")
    else:
        counts = df["category"].value_counts(sort=False).to_dict()
        pills = "".join(f"<span class='pill'>{esc(k)}: <b>{v}</b></span>" for k, v in counts.items())
        sections.append(f"<div class='pill-row'>{pills}</div>")

        for cat, group in df.groupby("category", sort=False):
            limit = 20 if cat in ["Game line move", "Game line edge", "Market move"] else 10
            sections.append(f"<section><h2>{esc(cat)}</h2>{''.join(card(r) for _, r in group.head(limit).iterrows())}</section>")

    style = """
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#f3f6fb;color:#0f172a;padding:20px;line-height:1.38;margin:0}
.wrapper{max-width:900px;margin:0 auto}
h1{margin:0 0 8px;font-size:26px;color:#0f172a}
h2{margin:26px 0 12px;font-size:18px;color:#1e3a8a;border-bottom:2px solid #cbd5e1;padding-bottom:7px}
.summary,.muted,.action,.research{color:#475569}
.card{background:#fff;border:1px solid #cbd5e1;border-radius:12px;padding:14px 16px;margin:12px 0;box-shadow:0 1px 2px rgba(15,23,42,.06)}
.card-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;color:#0f172a}
.card-head strong{color:#0f172a;font-size:16px}
.badge{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:4px 9px;font-size:11px;font-weight:800;color:#fff;background:#475569;letter-spacing:.02em}
.badge.move{background:#2563eb}.badge.edge{background:#7c3aed}.badge.arb{background:#16a34a}.badge.mid{background:#ca8a04}
.score{color:#15803d;font-weight:900;font-size:16px}
.reason{color:#1f2937;margin:6px 0;font-size:15px}
code{color:#7c2d12;background:#ffedd5;padding:2px 5px;border-radius:4px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.pill-row{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 18px}
.pill{display:inline-flex;gap:6px;padding:7px 11px;border-radius:999px;background:#fff;border:1px solid #cbd5e1;color:#334155;font-weight:700}
.pill b{color:#16a34a}
</style>
"""
    doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
{style}
</head>
<body>
<div class="wrapper">
<h1>Daily NCAAF Betting Angles — {datetime.now().date().isoformat()}</h1>
<div class="summary">Game line moves are listed first as kickoff approaches.</div>
{''.join(sections)}
</div>
</body>
</html>
"""
    OUT_HTML.write_text(doc)

def main():
    if not OUT_CSV.exists():
        raise SystemExit(f"Missing {OUT_CSV}; run build_daily_betting_angles first.")

    existing = pd.read_csv(OUT_CSV)
    existing = existing[existing["category"].astype(str).ne("Game line move")].copy()

    moves = make_game_line_move_rows()
    combined = pd.concat([moves, existing], ignore_index=True)
    combined = order_df(combined)
    combined.to_csv(OUT_CSV, index=False)

    rewrite_markdown(combined)
    rewrite_html(combined)

    print(f"Game line moves added: {len(moves)}")
    print("Category order/counts:")
    print(combined.groupby("category", sort=False).size().to_string())

if __name__ == "__main__":
    main()
