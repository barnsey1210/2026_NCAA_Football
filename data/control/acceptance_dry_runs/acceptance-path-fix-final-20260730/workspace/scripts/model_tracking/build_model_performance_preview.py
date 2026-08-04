#!/usr/bin/env python3
"""Build a non-published Betting preview without changing betting_v2.html."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "betting_v2.html"
OUT = ROOT / "build/previews/betting_model_performance_preview.html"

CSS = r'''<style id="model-performance-preview-css">
.viewSwitch,.modelTabs,.modelFilters{display:flex;gap:7px;flex-wrap:wrap;margin:10px 0}.viewSwitch button,.modelTabs button,.modelFilters button{border:1px solid var(--line);background:#091a34;color:var(--muted);border-radius:999px;padding:8px 13px;font-weight:900;cursor:pointer}.viewSwitch button.active,.modelTabs button.active,.modelFilters button.active{background:#1857a7;color:#fff;border-color:#55a2ff}.modelView[hidden]{display:none}.modelNotice{border:1px solid #28558c;background:#0b2444;border-radius:12px;padding:12px;margin:10px 0;color:#bcd0ec}.modelCards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:12px 0}.modelCard{background:#0a1a35;border:1px solid var(--line);border-radius:12px;padding:12px}.modelCard span{color:var(--muted);font-size:10px;text-transform:uppercase}.modelCard b{display:block;font-size:22px;margin-top:4px}.modelMatrixWrap{overflow:auto}.modelMatrix{width:100%;min-width:1050px;border-collapse:collapse}.modelMatrix th,.modelMatrix td{border-top:1px solid var(--line);padding:8px;text-align:right;white-space:nowrap}.modelMatrix th:first-child,.modelMatrix td:first-child{text-align:left;position:sticky;left:0;background:#0a1a35}.modelMatrix th{cursor:pointer;color:var(--muted)}.statusPill{font-size:9px;border:1px solid #37618f;border-radius:999px;padding:3px 6px}.modelEmpty{text-align:center!important;padding:28px!important;color:var(--muted)}@media(max-width:700px){.modelCards{grid-template-columns:repeat(2,1fr)}.modelMatrix{min-width:760px}.modelAdvanced{display:none}}
</style>'''

HTML = r'''<section id="modelPerformanceView" class="modelView" hidden>
<div class="modelNotice"><b>Prospective 2026 tracker</b> · Model opportunities are separate from personal wagers. Preseason and zero-settlement states are expected.</div>
<div class="modelTabs"><button class="active" data-model-tab="spread">Spread</button><button data-model-tab="totals">Totals</button><button data-model-tab="summary">Summary</button></div>
<div class="modelFilters" id="modelPeriods"></div><div class="modelFilters"><button class="active">All tracked models</button><button>Individual models</button><button>Consensus models</button><button>All opportunities</button><button>Qualified opportunities</button></div>
<div class="modelCards" id="modelCards"></div>
<section class="card"><div class="cardHead"><h2 id="modelMatrixTitle">Spread model matrix</h2><small>Rows under 30 settled selections remain unranked</small></div><div class="modelMatrixWrap"><table class="modelMatrix"><thead><tr><th>Model</th><th>Rank</th><th>Games</th><th>Availability</th><th>Record</th><th>Win %</th><th>ROI</th><th>Avg point CLV</th><th>Positive CLV</th><th>MAE</th><th>Bias</th><th>RMSE</th></tr></thead><tbody id="modelMatrixRows"></tbody></table></div></section>
<section class="card resultsCard"><div class="cardHead"><h2>Model opportunity ledger</h2><small>Read-only; never creates a personal wager</small></div><div class="modelMatrixWrap"><table class="modelMatrix"><thead><tr><th>Week / Game</th><th>Market</th><th>Model</th><th>Prediction</th><th>Opener</th><th>Edge</th><th>Side</th><th>Qualification</th><th>Provenance</th><th>Close</th><th>Point CLV</th><th>Result</th></tr></thead><tbody id="modelLedgerRows"><tr><td colspan="12" class="modelEmpty">No prospective opportunities captured yet.</td></tr></tbody></table></div></section>
</section>'''

JS = r'''<script id="model-performance-preview-js">
(function(){let MP=null,mode='spread';const val=(v,s='—')=>v==null?s:v,pct=v=>v==null?'—':(Number(v)*100).toFixed(1)+'%';
function switchView(name){const mine=name==='bets';document.getElementById('myBetsView').hidden=!mine;document.getElementById('modelPerformanceView').hidden=mine;document.querySelectorAll('.viewSwitch button').forEach(b=>b.classList.toggle('active',b.dataset.view===name))}
function render(){if(!MP)return;const rows=mode==='totals'?MP.total_matrix:MP.spread_matrix;modelMatrixTitle.textContent=mode==='totals'?'Total model matrix':'Spread model matrix';modelMatrixRows.innerHTML=rows.map(r=>`<tr><td><b>${r.model}</b><div><span class="statusPill">${r.ranking_status}</span></div></td><td>${val(r.rank)}</td><td>${r.games}</td><td>${pct(r.availability_pct)}</td><td>${r.record}</td><td>${pct(r.win_pct)}</td><td>${pct(r.roi)}</td><td>${val(r.average_point_clv)}</td><td>${pct(r.positive_clv_pct)}</td><td>${val(r.mae)}</td><td>${val(r.bias)}</td><td>${val(r.rmse)}</td></tr>`).join('');const s=MP.summary[mode==='totals'?'totals':'spread'];modelCards.innerHTML=[['Opportunities',s.opportunities],['Settled selections',s.settled_selections],['Average point CLV','—'],['ATS / O-U ROI','—']].map(x=>`<div class="modelCard"><span>${x[0]}</span><b>${x[1]}</b></div>`).join('')}
document.querySelectorAll('.viewSwitch button').forEach(b=>b.onclick=()=>switchView(b.dataset.view));document.querySelectorAll('[data-model-tab]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-model-tab]').forEach(x=>x.classList.remove('active'));b.classList.add('active');mode=b.dataset.modelTab==='totals'?'totals':'spread';render()});fetch('data/site/model_performance_view.json').then(r=>r.json()).then(d=>{MP=d;modelPeriods.innerHTML=d.periods.map((p,i)=>`<button class="${p==='All'?'active':''}">${p}</button>`).join('');render()}).catch(e=>modelMatrixRows.innerHTML=`<tr><td colspan="12" class="modelEmpty">Unable to load preview data: ${e.message}</td></tr>`);switchView('bets')})();
</script>'''


def main():
    text = SOURCE.read_text()
    text = text.replace("<head>", '<head><base href="../../">', 1)
    text = text.replace("</head>", CSS + "</head>", 1)
    marker = '<section class="hero">'
    switch = '<div class="viewSwitch"><button class="active" data-view="bets">My Bets</button><button data-view="model">Model Performance</button></div><div id="myBetsView" class="modelView">'
    if marker not in text: raise RuntimeError("Betting hero marker missing")
    text = text.replace(marker, switch + marker, 1)
    text = text.replace("</main><script>", "</div>" + HTML + "</main><script>", 1)
    text = text.replace("</body>", JS + "</body>", 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"Wrote preview {OUT}")


if __name__ == "__main__": main()
