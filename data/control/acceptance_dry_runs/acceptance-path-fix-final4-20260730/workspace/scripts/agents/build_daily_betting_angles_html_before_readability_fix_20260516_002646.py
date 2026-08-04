#!/usr/bin/env python3
from pathlib import Path
from datetime import date
import html
import pandas as pd

CSV = Path("data/agents/daily_betting_angles.csv")
MD = Path("data/agents/daily_betting_angles.md")
OUT = Path("data/agents/daily_betting_angles.html")

df = pd.read_csv(CSV) if CSV.exists() else pd.DataFrame()

def esc(x):
    return html.escape(str(x or ""))

def badge(row):
    grade = str(row.get("grade", ""))
    category = str(row.get("category", ""))
    label = grade or category
    cls = "badge"
    if "ARB" in grade:
        cls += " arb"
    elif "MOVE" in grade or "LINE" in grade:
        cls += " move"
    elif "Middle" in category:
        cls += " mid"
    return f'<span class="{cls}">{esc(label)}</span>'

def score_text(row):
    s = str(row.get("score", "") or "").strip()
    if not s or s.lower() == "nan":
        return ""
    return f" <span class='score'>{esc(s)}</span>"

def card(row):
    research = str(row.get("research_query", "") or "").strip()
    research_html = f'<div class="research">Research: <code>{esc(research)}</code></div>' if research else ""
    return f"""
    <div class="card">
      <div class="card-head">{badge(row)} <strong>{esc(row.get("title",""))}</strong>{score_text(row)}</div>
      <div class="reason">{esc(row.get("reason",""))}</div>
      <div class="action">Action: {esc(row.get("action",""))}</div>
      {research_html}
    </div>
    """

sections = []
if df.empty:
    sections.append("<p>No angles generated.</p>")
else:
    # Compact top summary
    counts = df["category"].value_counts().to_dict()
    summary_items = "".join(
        f"<span class='pill'>{esc(k)}: <b>{v}</b></span>"
        for k, v in counts.items()
    )
    sections.append(f"<div class='pill-row'>{summary_items}</div>")

    # New/changed placeholder until history comparison is wired directly.
    sections.append("""
    <section>
      <h2>New / Changed Since Previous Report</h2>
      <p class="muted">Comparison history will populate after the next scheduled run. Current items below are sorted by priority.</p>
    </section>
    """)

    for cat, g in df.groupby("category", sort=False):
        limit = 8 if cat in {"Arbitrage", "Market move"} else 5
        cards = "\n".join(card(r) for _, r in g.head(limit).iterrows())
        sections.append(f"<section><h2>{esc(cat)}</h2>{cards}</section>")

    if "research_query" in df.columns:
        qs = [q for q in df["research_query"].dropna().astype(str).drop_duplicates().tolist() if q.strip()]
        if qs:
            items = "\n".join(f"<li><code>{esc(q)}</code></li>" for q in qs[:8])
            sections.append(f"<section><h2>Research Queue</h2><ul>{items}</ul></section>")

doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
body {{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
  background:#0b1220;
  color:#e5edf8;
  padding:20px;
  line-height:1.35;
}}
h1 {{ margin:0 0 6px; font-size:24px; }}
h2 {{
  margin:24px 0 10px;
  font-size:18px;
  color:#bfdbfe;
  border-bottom:1px solid #334155;
  padding-bottom:6px;
}}
.muted {{ color:#9fb0c9; }}
.summary {{ margin:8px 0 18px; color:#cbd5e1; }}
.card {{
  background:#111c33;
  border:1px solid #2b3c5f;
  border-radius:12px;
  padding:12px 14px;
  margin:10px 0;
}}
.card-head {{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
  margin-bottom:6px;
}}
.badge {{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  border-radius:999px;
  padding:3px 8px;
  font-size:11px;
  font-weight:800;
  color:#dbeafe;
  background:#334155;
}}
.badge.arb {{ color:#052e16; background:#22c55e; }}
.badge.move {{ color:#172554; background:#93c5fd; }}
.badge.mid {{ color:#422006; background:#eab308; }}
.score {{ color:#4ade80; font-weight:800; }}
.reason {{ color:#e5edf8; margin:4px 0; }}
.action,.research {{ color:#9fb0c9; font-size:13px; margin-top:4px; }}
code {{ color:#fde68a; background:#1e293b; padding:1px 4px; border-radius:4px; }}
li {{ margin:6px 0; }}
.pill-row {{ display:flex; flex-wrap:wrap; gap:8px; margin:14px 0 18px; }}
.pill {{
  display:inline-flex;
  gap:6px;
  padding:6px 10px;
  border-radius:999px;
  background:#111c33;
  border:1px solid #2b3c5f;
  color:#cbd5e1;
}}
.pill b {{ color:#4ade80; }}
</style>
</head>
<body>
<h1>Daily NCAAF Betting Angles — {date.today().isoformat()}</h1>
<div class="summary">Items are listed in priority order based on arb edge, line movement size, implied-probability movement, and stale-price/middle quality.</div>
{''.join(sections)}
</body>
</html>
"""

OUT.write_text(doc)
print(f"Wrote {OUT}")
