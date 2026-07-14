#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- openers-ratings-context-start -->"
END = "<!-- openers-ratings-context-end -->"

BLOCK = r'''
<!-- openers-ratings-context-start -->
<script id="openers-ratings-context-js">
(function(){
  if (window.__openersRatingsContextInstalled) return;
  window.__openersRatingsContextInstalled = true;

  function esc(v){
    return String(v == null ? '' : v)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }

  function fmtPct(v){
    const n = Number(v);
    if (!Number.isFinite(n)) return '0%';
    return `${Math.round(n * 1000) / 10}%`;
  }

  function sourceRows(){
    const defaultRows = [
      {name:'SP+', active:true, weight:.333, teams:138},
      {name:'FPI', active:true, weight:.333, teams:138},
      {name:'TeamRankings', active:true, weight:.333, teams:138},
      {name:'KFord', active:false, weight:0, teams:136},
      {name:'Brad Powers', active:false, weight:0, teams:136}
    ];

    try {
      const rows = DB.ratings_source_summary || DB.rating_sources || DB.ratings_sources || [];
      if (Array.isArray(rows) && rows.length) {
        return rows.map(r => {
          const name = r.source || r.system || r.name || r.rating_system || '';
          const weight = Number(r.weight ?? r.production_weight ?? r.active_weight ?? 0);
          const active = weight > 0 || /active/i.test(String(r.status || r.role || ''));
          return {
            name,
            active,
            weight,
            pulled: r.pulled_at || r.snapshot_ts || r.updated_at || r.latest_pull || '',
            sourceUpdated: r.source_updated_at || r.source_updated || r.rating_date || r.snapshot_date || '',
            teams: r.teams || r.team_count || r.count || ''
          };
        }).filter(r => r.name);
      }
    } catch(e) {}

    return defaultRows;
  }

  function productionText(rows){
    const active = rows.filter(r => r.active && Number(r.weight) > 0);
    if (!active.length) return 'Active 2026 ratings only — SP+ 33.3% · FPI 33.3% · TeamRankings 33.3%. Reference/stale sources are shown for context but excluded from production projections/sims.';
    return 'Active 2026 ratings only — ' + active.map(r => `${r.name} ${fmtPct(r.weight)}`).join(' · ') + '. Reference/stale sources are shown for context but excluded from production projections/sims.';
  }

  function renderOpenersRatingsContext(){
    const rows = sourceRows();

    return `
      <div class="openers-ratings-context">
        <div class="openers-ratings-banner">
          <b>Production model:</b> ${esc(productionText(rows))}
        </div>
        <div class="openers-ratings-grid">
          ${rows.map(r => `
            <div class="openers-rating-source-card ${r.active ? 'active' : 'stale'}">
              <div class="openers-rating-source-name">${esc(r.name)}</div>
              <div class="openers-rating-source-status">
                ${r.active ? `Active 2026 · ${fmtPct(r.weight)}` : 'Stale / reference only · 0%'}
              </div>
              <div class="openers-rating-source-meta">Pulled: ${esc(r.pulled || '2026-07-13 12:04:19 UTC')}</div>
              <div class="openers-rating-source-meta">Source updated: ${esc(r.sourceUpdated || 'Not provided by source')}</div>
              <div class="openers-rating-source-meta">Teams: ${esc(r.teams || (r.active ? 138 : 136))}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  const oldRenderOpenersPage = window.renderOpenersPage;
  window.renderOpenersPage = function(){
    let html = typeof oldRenderOpenersPage === 'function' ? oldRenderOpenersPage() : '';

    if (!html || html.includes('openers-ratings-context')) return html;

    // Replace the smaller opener model status card with the full ratings context.
    html = html.replace(
      /<div class="openers-model-status">[\s\S]*?<\/div>\s*<\/div>/,
      renderOpenersRatingsContext()
    );

    // Fallback insert after hero if regex misses.
    if (!html.includes('openers-ratings-context')) {
      html = html.replace('</div>\n\n      <div class="card openers-card">', '</div>\n\n      ' + renderOpenersRatingsContext() + '\n\n      <div class="card openers-card">');
    }

    return html;
  };
})();
</script>

<style id="openers-ratings-context-css">
.openers-ratings-context{
  margin-top:14px;
}
.openers-ratings-banner{
  border:1px solid rgba(34,197,94,.28);
  background:rgba(22,101,52,.16);
  color:#22c55e;
  border-radius:14px;
  padding:13px 16px;
  font-weight:900;
  line-height:1.35;
}
.openers-ratings-grid{
  display:grid;
  grid-template-columns:repeat(5,minmax(210px,1fr));
  gap:12px;
  margin-top:12px;
  overflow-x:auto;
  padding-bottom:2px;
}
.openers-rating-source-card{
  border:1px solid rgba(148,163,184,.22);
  background:rgba(15,23,42,.60);
  border-radius:16px;
  padding:14px 16px;
  min-width:210px;
}
.openers-rating-source-name{
  color:#f8fafc;
  font-size:18px;
  font-weight:950;
  margin-bottom:6px;
}
.openers-rating-source-status{
  font-size:13px;
  font-weight:950;
  margin-bottom:8px;
}
.openers-rating-source-card.active .openers-rating-source-status{
  color:#22c55e;
}
.openers-rating-source-card.stale .openers-rating-source-status{
  color:#fb923c;
}
.openers-rating-source-meta{
  color:#94a3b8;
  font-size:12px;
  line-height:1.3;
  font-weight:750;
}
@media(max-width:1100px){
  .openers-ratings-grid{
    grid-template-columns:repeat(2,minmax(210px,1fr));
  }
}
</style>
<!-- openers-ratings-context-end -->
'''

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")

    path.write_text(s, encoding="utf-8")
    print(path, "openers ratings context injected")
