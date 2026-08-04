#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- home-preseason-toggle-fix-start -->"
END = "<!-- home-preseason-toggle-fix-end -->"

BLOCK = r'''
<!-- home-preseason-toggle-fix-start -->
<script id="home-preseason-toggle-fix-js">
(function(){
  if (window.__homePreseasonToggleFixInstalled) return;
  window.__homePreseasonToggleFixInstalled = true;

  function esc(v){
    if (typeof escapeHtml === 'function') return escapeHtml(String(v ?? ''));
    return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function n(v){
    const x = Number(v);
    return Number.isFinite(x) ? x : null;
  }

  function fmt(v, d=1){
    const x = n(v);
    if (x == null) return '—';
    return x.toFixed(d).replace(/\.0$/,'');
  }

  function pct(v){
    const x = n(v);
    if (x == null) return '—';
    const y = x <= 1 ? x * 100 : x;
    return y.toFixed(1).replace(/\.0$/,'') + '%';
  }

  function teamLinkSafe(team){
    try { if (typeof linkTeam === 'function') return linkTeam(team); } catch(e) {}
    return esc(team);
  }

  function currentMarketWinTotals(){
    const rows = [];
    try {
      rows.push(...(DB.market_win_totals_edges || []));
      rows.push(...(DB.market_win_totals_raw || []));
    } catch(e) {}

    const out = {};
    rows.forEach(r => {
      const team = r.team;
      if (!team || out[team]) return;
      const total = n(r.market_total ?? r.win_total ?? r.current_win_total);
      if (total == null) return;
      out[team] = total;
    });
    return out;
  }

  function preseasonTeams(){
    const snap = window.PRESEASON_SNAPSHOT;
    if (!snap || !Array.isArray(snap.teams)) return [];
    return snap.teams.slice();
  }

  function row(label, team, value, note){
    return `<div class="home-pre-row">
      <div>
        <div class="home-pre-label">${esc(label)}</div>
        <div class="home-pre-team">${teamLinkSafe(team)}</div>
      </div>
      <div class="home-pre-value">${esc(value)}</div>
      <div class="home-pre-note">${esc(note || '')}</div>
    </div>`;
  }

  function preseasonCardHtml(){
    const teams = preseasonTeams();
    if (!teams.length) {
      return `<div class="card home-preseason-card" id="homePreseasonSnapshotCard">
        <div class="section-title">Preseason Snapshot</div>
        <div class="small muted">No frozen preseason snapshot is embedded yet.</div>
      </div>`;
    }

    const wt = currentMarketWinTotals();

    const topWins = teams
      .filter(t => n(t.avg_total_wins) != null)
      .sort((a,b) => n(b.avg_total_wins) - n(a.avg_total_wins))
      .slice(0,5);

    const topConfTitle = teams
      .filter(t => n(t.conference_title_pct) != null)
      .sort((a,b) => n(b.conference_title_pct) - n(a.conference_title_pct))
      .slice(0,5);

    const topMakeTitle = teams
      .filter(t => n(t.make_title_game_pct) != null)
      .sort((a,b) => n(b.make_title_game_pct) - n(a.make_title_game_pct))
      .slice(0,5);

    const wtEdges = teams
      .map(t => {
        const market = wt[t.team];
        const proj = n(t.avg_total_wins);
        if (market == null || proj == null) return null;
        return {team:t.team, proj, market, edge:proj-market};
      })
      .filter(Boolean)
      .filter(x => Math.abs(x.edge) >= 0.35)
      .sort((a,b) => Math.abs(b.edge) - Math.abs(a.edge))
      .slice(0,5);

    return `<div class="card home-preseason-card" id="homePreseasonSnapshotCard">
      <div class="home-top-bets-head">
        <div>
          <div class="section-title">Preseason Snapshot</div>
          <div class="small muted">Frozen baseline from before results are applied. Use this to compare original projections against the current season view.</div>
        </div>
      </div>

      <div class="home-pre-grid">
        <div class="home-pre-section">
          <div class="home-pre-section-title">Top Projected Wins</div>
          ${topWins.map(t => row('Projected wins', t.team, fmt(t.avg_total_wins,2), `${esc(t.conference || '')} · rank #${t.rank || '—'}`)).join('')}
        </div>

        <div class="home-pre-section">
          <div class="home-pre-section-title">Top Conference Title</div>
          ${topConfTitle.map(t => row('Conference title', t.team, pct(t.conference_title_pct), `${esc(t.conference || '')} · make CG ${pct(t.make_title_game_pct)}`)).join('')}
        </div>

        <div class="home-pre-section">
          <div class="home-pre-section-title">Top Make Title Game</div>
          ${topMakeTitle.map(t => row('Make title game', t.team, pct(t.make_title_game_pct), `${esc(t.conference || '')} · title ${pct(t.conference_title_pct)}`)).join('')}
        </div>

        <div class="home-pre-section">
          <div class="home-pre-section-title">Preseason Win Total Edges</div>
          ${wtEdges.length ? wtEdges.map(x => row('Win total edge', x.team, `${x.edge > 0 ? '+' : ''}${fmt(x.edge,2)}`, `Pre ${fmt(x.proj,2)} vs market ${fmt(x.market,1)}`)).join('') : '<div class="small muted">No preseason win-total edges found at current threshold.</div>'}
        </div>
      </div>
    </div>`;
  }

  function setHomeView(view){
    const watch = document.getElementById('homeTopBetsCard');
    const oldPre = document.getElementById('homePreseasonSnapshotCard');

    if (view === 'preseason') {
      if (watch) watch.style.display = 'none';
      if (!oldPre) {
        const toggle = document.getElementById('homeSeasonToggle');
        if (toggle) toggle.insertAdjacentHTML('afterend', preseasonCardHtml());
      }
    } else {
      if (oldPre) oldPre.remove();
      if (watch) {
        watch.style.display = '';
        watch.style.opacity = '1';
      }
    }
  }

  function bind(){
    const toggle = document.getElementById('homeSeasonToggle');
    if (!toggle || toggle.dataset.preseasonFixBound === '1') return;
    toggle.dataset.preseasonFixBound = '1';

    toggle.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', () => {
        setTimeout(() => setHomeView(btn.dataset.view), 0);
      });
    });

    const active = toggle.querySelector('button.active');
    setHomeView(active && active.dataset.view === 'preseason' ? 'preseason' : 'current');
  }

  function schedule(){
    setTimeout(bind, 50);
    setTimeout(bind, 250);
    setTimeout(bind, 800);
  }

  const oldRender = window.render;
  if (typeof oldRender === 'function' && !oldRender.__homePreseasonToggleFixWrapped) {
    const wrapped = function(){
      const result = oldRender.apply(this, arguments);
      schedule();
      return result;
    };
    wrapped.__homePreseasonToggleFixWrapped = true;
    window.render = wrapped;
  }

  window.addEventListener('hashchange', schedule);
  document.addEventListener('DOMContentLoaded', schedule);
  schedule();
})();
</script>

<style id="home-preseason-toggle-fix-css">
.home-preseason-card{margin-top:14px;border-color:rgba(167,139,250,.28)!important}
.home-pre-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.home-pre-section{border:1px solid rgba(255,255,255,.08);border-radius:14px;background:rgba(2,6,23,.22);padding:10px}
.home-pre-section-title{font-weight:950;text-transform:uppercase;letter-spacing:.08em;font-size:12px;color:#dbeafe;margin-bottom:8px}
.home-pre-row{display:grid;grid-template-columns:minmax(0,1fr) 82px minmax(0,1fr);gap:8px;align-items:center;border-top:1px solid rgba(255,255,255,.07);padding:8px 0}
.home-pre-row:first-of-type{border-top:0}
.home-pre-label{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:#93a4c7;font-weight:900}
.home-pre-team{font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.home-pre-value{font-weight:950;font-size:17px;text-align:right;color:#f8fafc}
.home-pre-note{font-size:12px;color:#aab7d4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media(max-width:900px){.home-pre-grid{grid-template-columns:1fr}.home-pre-row{grid-template-columns:1fr 72px}.home-pre-note{grid-column:1 / -1}}
</style>
<!-- home-preseason-toggle-fix-end -->
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
    print(path, "injected home preseason toggle fix")
