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
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  background: #f3f6fb;
  color: #0f172a;
  padding: 20px;
  line-height: 1.38;
  margin: 0;
}
.wrapper {
  max-width: 900px;
  margin: 0 auto;
}
h1 {
  margin: 0 0 8px;
  font-size: 26px;
  color: #0f172a;
}
h2 {
  margin: 26px 0 12px;
  font-size: 18px;
  color: #1e3a8a;
  border-bottom: 2px solid #cbd5e1;
  padding-bottom: 7px;
}
.muted {
  color: #475569;
}
.summary {
  margin: 8px 0 18px;
  color: #334155;
  font-size: 14px;
}
.card {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 14px 16px;
  margin: 12px 0;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}
.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
  color: #0f172a;
}
.card-head strong {
  color: #0f172a;
  font-size: 16px;
}
.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 11px;
  font-weight: 800;
  color: #ffffff;
  background: #475569;
  letter-spacing: .02em;
}
.badge.arb {
  background: #16a34a;
  color: #ffffff;
}
.badge.move {
  background: #2563eb;
  color: #ffffff;
}
.badge.mid {
  background: #ca8a04;
  color: #ffffff;
}
.score {
  color: #15803d;
  font-weight: 900;
  font-size: 16px;
}
.reason {
  color: #1f2937;
  margin: 6px 0;
  font-size: 15px;
}
.action,
.research {
  color: #475569;
  font-size: 13px;
  margin-top: 5px;
}
code {
  color: #7c2d12;
  background: #ffedd5;
  padding: 2px 5px;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
li {
  margin: 7px 0;
  color: #1f2937;
}
.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0 18px;
}
.pill {
  display: inline-flex;
  gap: 6px;
  padding: 7px 11px;
  border-radius: 999px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #334155;
  font-weight: 700;
}
.pill b {
  color: #16a34a;
}
.new-list {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 12px 18px;
}
@media (prefers-color-scheme: dark) {
  body {
    background: #f3f6fb !important;
    color: #0f172a !important;
  }
  .card,
  .pill,
  .new-list {
    background: #ffffff !important;
    color: #0f172a !important;
  }
  h1, h2, .card-head strong, .reason, li {
    color: #0f172a !important;
  }
  .summary, .muted, .action, .research {
    color: #475569 !important;
  }
}
</style>
</head>
<body><div class="wrapper">
<h1>Daily NCAAF Betting Angles — {date.today().isoformat()}</h1>
<div class="summary">Items are listed in priority order based on arb edge, line movement size, implied-probability movement, and stale-price/middle quality.</div>
{''.join(sections)}
</div></body>
</html>
"""

OUT.write_text(doc)
print(f"Wrote {OUT}")
