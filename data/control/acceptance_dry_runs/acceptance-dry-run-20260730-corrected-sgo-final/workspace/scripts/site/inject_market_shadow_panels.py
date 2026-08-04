#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path.home() / "NCAAF_AUTO"
SHADOW = ROOT / "data/site/saturday_shadow_lines.json"
COMPARISON = ROOT / "data/ratings/fundamental_market_rating_comparison.csv"
PAGES = [ROOT / "ratings_v2.html", ROOT / "openers_v2.html", ROOT / "schedule_v2.html"]
START = "<!-- MARKET_SHADOW_LAYER_START -->"
END = "<!-- MARKET_SHADOW_LAYER_END -->"

def block():
    shadow = json.loads(SHADOW.read_text()) if SHADOW.exists() else {"games": []}
    ratings = pd.read_csv(COMPARISON, low_memory=False).fillna("").to_dict("records") if COMPARISON.exists() else []
    data = json.dumps({"shadow": shadow, "ratings": ratings})
    return f"""{START}
<style>
.market-shadow-panel{{margin:18px 0;padding:16px;border:1px solid rgba(148,163,184,.28);border-radius:16px;background:rgba(15,23,42,.45)}}
.market-shadow-panel h2{{margin:0 0 6px;font-size:18px}}.market-shadow-sub{{opacity:.72;margin-bottom:12px;font-size:13px}}
.market-shadow-scroll{{overflow-x:auto}}.market-shadow-table{{width:100%;border-collapse:collapse;font-size:13px}}
.market-shadow-table th,.market-shadow-table td{{padding:8px 7px;border-bottom:1px solid rgba(148,163,184,.18);text-align:right;white-space:nowrap}}
.market-shadow-table th:first-child,.market-shadow-table td:first-child{{text-align:left}}
.market-shadow-pos{{color:#22c55e;font-weight:700}}.market-shadow-neg{{color:#ef4444;font-weight:700}}.market-shadow-muted{{opacity:.66}}
</style>
<script id="market-shadow-layer-data" type="application/json">{data}</script>
<script>
(function(){{
 const el=document.getElementById('market-shadow-layer-data'); if(!el)return;
 const p=JSON.parse(el.textContent), path=(location.pathname||'').toLowerCase();
 const root=document.querySelector('main')||document.querySelector('.page')||document.body;
 const n=(v,d=1)=>Number.isFinite(Number(v))?Number(v).toFixed(d):'—';
 const cls=v=>!Number.isFinite(Number(v))?'market-shadow-muted':Number(v)>0?'market-shadow-pos':Number(v)<0?'market-shadow-neg':'';
 function insert(panel){{const a=root.querySelector('.page-title,h1,.hero');if(a&&a.parentNode)a.parentNode.insertBefore(panel,a.nextSibling);else root.insertBefore(panel,root.firstChild);}}
 if(path.includes('ratings')){{
  const rows=[...(p.ratings||[])].filter(r=>r.team).sort((a,b)=>Number(b.abs_fundamental_market_gap||0)-Number(a.abs_fundamental_market_gap||0)).slice(0,30);
  const s=document.createElement('section');s.className='market-shadow-panel';
  s.innerHTML=`<h2>Market-Implied Power Ratings</h2><div class="market-shadow-sub">Closing-spread-derived ratings remain separate from the SP+/FPI/TeamRankings/Powers blend. Showing the 30 largest disagreements.</div><div class="market-shadow-scroll"><table class="market-shadow-table"><thead><tr><th>Team</th><th>Fundamental</th><th>Market</th><th>Gap</th><th>Mkt Rank</th><th>1W</th><th>4W</th></tr></thead><tbody>${{rows.map(r=>`<tr><td>${{r.team}}</td><td>${{n(r.fundamental_rating)}}</td><td>${{n(r.market_implied_rating)}}</td><td class="${{cls(r.fundamental_minus_market)}}">${{n(r.fundamental_minus_market)}}</td><td>${{r.market_implied_rank||'—'}}</td><td class="${{cls(r.market_move_1w)}}">${{n(r.market_move_1w)}}</td><td class="${{cls(r.market_move_4w)}}">${{n(r.market_move_4w)}}</td></tr>`).join('')}}</tbody></table></div>`;
  insert(s);
 }}
 if(path.includes('openers')||path.includes('schedule')){{
  const rows=(p.shadow&&p.shadow.games)||[];
  const s=document.createElement('section');s.className='market-shadow-panel';
  s.innerHTML=`<h2>Saturday Shadow Lines</h2><div class="market-shadow-sub"><b>PROJECTED MARKET VALUE.</b> Spread = 50% target-excluded market rating + 50% updated SP+ only with independent market support; otherwise updated SP+ fallback. Preseason SP+ change is 0.00 until a team completes a game. Spread value remains neutral because no tested tier was CLV-monotonic in 2024 selection. Total = 60% predicted SP+ component total + 40% existing projection - 1.1573. Color ranks historically observed closing-line value, not projection certainty or game-result accuracy.</div><div class="market-shadow-scroll"><table class="market-shadow-table"><thead><tr><th>Game</th><th>Current</th><th>Shadow</th><th>Market</th><th>Projected CLV</th><th>Spread value</th><th>Status</th></tr></thead><tbody>${{rows.map(r=>`<tr><td>${{r.away_team}} at ${{r.home_team}}</td><td>${{n(r.official_model_spread)}}</td><td><strong>${{n(r.saturday_shadow_spread)}}</strong></td><td>${{n(r.opening_spread)}}</td><td class="${{cls(r.expected_spread_clv)}}">${{n(r.expected_spread_clv)}}</td><td>Neutral</td><td>${{r.shadow_spread_formula||r.spread_status||'Unavailable'}}</td></tr>`).join('')}}</tbody></table></div>`;
  insert(s);
 }}
}})();
</script>
{END}"""

def patch(path):
    if not path.exists():
        print("skip missing:", path)
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    b = block()
    if START in text and END in text:
        text = re.sub(
            re.escape(START) + r".*?" + re.escape(END),
            lambda _match: b,
            text,
            flags=re.S,
        )
    else:
        text = text.replace("</body>", b + "\n</body>")
    path.write_text(text, encoding="utf-8")
    print("patched:", path)

def main():
    for p in PAGES:
        patch(p)

if __name__ == "__main__":
    main()
