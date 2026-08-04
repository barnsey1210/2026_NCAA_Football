#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- openers-page-start -->"
END = "<!-- openers-page-end -->"

BLOCK = r'''
<!-- openers-page-start -->
<script id="openers-page-js">
(function(){
  if (window.__openersPageInstalledV3) return;
  window.__openersPageInstalledV3 = true;

  window.__openersSort = window.__openersSort || {key:'week', dir:'asc'};

  function esc(v){
    return String(v == null ? '' : v)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }
  function n(v){ const x = Number(v); return Number.isFinite(x) ? x : null; }

  function fmtDate(v){
    if (!v) return '—';
    const d = new Date(String(v).slice(0,10) + 'T00:00:00');
    if (Number.isNaN(d.getTime())) return String(v).slice(0,10);
    return d.toLocaleDateString(undefined, {month:'short', day:'numeric'});
  }

  function fmtNum(v, d=1){
    const x = n(v);
    if (x == null) return '—';
    return x.toFixed(d).replace(/\.0$/,'');
  }

  function projSpread(g){
    const margin = n(g.projected_margin_home);
    if (margin == null) return '—';
    const fav = margin >= 0 ? g.home_team : g.away_team;
    return `${esc(fav)} -${Math.abs(margin).toFixed(1).replace(/\.0$/,'')}`;
  }

  function logo(team){
    try {
      if (typeof teamImageImg === 'function') return teamImageImg(team);
      if (typeof advTeamLogo === 'function') return advTeamLogo(team);
    } catch(e) {}
    return '';
  }

  function ratingMoveForTeam(team){
    const data = window.POSTGAME_RATING_IMPACTS || window.OPENERS_RATING_IMPACTS || {};
    return data[team] || null;
  }

  function ratingMoveChip(team){
    const r = ratingMoveForTeam(team);
    if (!r) return '';

    const val = Number(r.projected_rating_delta ?? r.rating_delta ?? r.delta);
    if (!Number.isFinite(val) || Math.abs(val) < 0.05) return '';

    const cls = val > 0 ? 'up' : 'down';
    const arrow = val > 0 ? '▲' : '▼';
    return `<span class="openers-rating-chip ${cls}" title="Projected rating movement from postgame box-score impact model">${arrow} ${Math.abs(val).toFixed(1)}</span>`;
  }

  function boxScoreChip(team){
    const r = ratingMoveForTeam(team);
    if (!r) return '';
    const status = String(r.box_score_status || r.status || '').toLowerCase();
    if (!status) return '';
    const good = status.includes('captured') || status.includes('complete') || status.includes('final');
    return `<span class="openers-box-chip ${good ? 'good' : 'missing'}">${good ? 'Box captured' : 'Box missing'}</span>`;
  }

  function teamCell(team){
    return `<span class="openers-team">${logo(team)}<span>${esc(team || '—')}</span>${ratingMoveChip(team)}${boxScoreChip(team)}</span>`;
  }

  function sortableTh(key, label){
    const st = window.__openersSort || {key:'week', dir:'asc'};
    const arrow = st.key === key ? (st.dir === 'asc' ? '▲' : '▼') : '';
    return `<th class="sortable openers-sort-th" data-openers-sort="${key}">${esc(label)} <span class="sort-arrow">${arrow}</span></th>`;
  }

  function sortVal(g, key){
    if (key === 'week') return n(g.week) ?? 999;
    if (key === 'date') return String(g.date || '');
    if (key === 'away') return String(g.away_team || '').toLowerCase();
    if (key === 'home') return String(g.home_team || '').toLowerCase();
    if (key === 'spread') return Math.abs(n(g.projected_margin_home) ?? 999);
    if (key === 'total') return n(g.projected_total) ?? -999;
    return '';
  }

  function weeks(){
    return [...new Set((DB.games || []).map(g => g.week).filter(w => w !== null && w !== undefined && w !== ''))]
      .map(w => Number(w)).filter(w => Number.isFinite(w)).sort((a,b)=>a-b);
  }

  function filteredGames(){
    const week = document.getElementById('openersWeek')?.value || 'all';
    const team = String(document.getElementById('openersTeam')?.value || '').trim().toLowerCase();

    let games = [...(DB.games || [])];

    if (week !== 'all') games = games.filter(g => String(g.week) === String(week));
    if (team) {
      games = games.filter(g =>
        String(g.away_team || '').toLowerCase().includes(team) ||
        String(g.home_team || '').toLowerCase().includes(team)
      );
    }

    const st = window.__openersSort || {key:'week', dir:'asc'};
    const mult = st.dir === 'asc' ? 1 : -1;

    games.sort((a,b) => {
      const av = sortVal(a, st.key);
      const bv = sortVal(b, st.key);
      if (typeof av === 'number' && typeof bv === 'number') {
        return (av - bv) * mult || String(a.date || '').localeCompare(String(b.date || ''));
      }
      return String(av).localeCompare(String(bv)) * mult || String(a.date || '').localeCompare(String(b.date || ''));
    });

    return games;
  }

  function productionModelText(){
    try {
      const cfg = window.GAME_PROJECTION_BLEND_CONFIG || {};
      const w = cfg.spread_weights || {};
      const active = Object.entries(w)
        .filter(([k,v]) => Number(v) > 0)
        .map(([k,v]) => `${k.replace('Site Projection','Site Projection')} ${Math.round(Number(v)*100)}%`);
      return active.length ? active.join(' · ') : 'Active production projection blend';
    } catch(e) {
      return 'Active production projection blend';
    }
  }

  function lastRatingsDate(){
    try {
      const teams = DB.teams || [];
      const keys = ['ratings_updated_at','rating_updated_at','snapshot_date','updated_at'];
      const vals = [];
      teams.forEach(t => keys.forEach(k => {
        if (t[k]) vals.push(String(t[k]).slice(0,10));
      }));
      return vals.length ? vals.sort().slice(-1)[0] : '';
    } catch(e) {
      return '';
    }
  }

  function modelStatusCard(){
    const ratingDate = lastRatingsDate();
    return `<div class="openers-model-status">
      <div>
        <div class="openers-status-title">Production ratings / opener model</div>
        <div class="openers-status-sub">${esc(productionModelText())}</div>
      </div>
      <div class="openers-status-pills">
        <span>Ratings: SP+ / FPI / TeamRankings active blend</span>
        <span>Projected spread: current production model</span>
        <span>${ratingDate ? `Latest rating date: ${esc(ratingDate)}` : 'Latest rating date: see Rankings'}</span>
        <span>Postgame rating move chips: pending box-score impact model</span>
      </div>
    </div>`;
  }

  function weekButtons(){
    return `<div class="openers-week-buttons">
      <button type="button" data-openers-week="all">All</button>
      ${weeks().map(w => `<button type="button" data-openers-week="${w}">W${w}</button>`).join('')}
    </div>`;
  }

  window.renderOpenersPage = function(){
    return `
      <div class="hero">
        <div>
          <div class="page-title">Openers</div>
          <div class="page-sub">Streamlined opener-betting board. Projection-only view for quickly comparing upcoming games before market openers settle.</div>
        </div>
        <div class="hero-stats">
          <div class="mini"><div class="label">Games</div><div class="value">${(DB.games || []).length}</div></div>
          <div class="mini"><div class="label">Weeks</div><div class="value">${weeks().length}</div></div>
        </div>
      </div>

      ${modelStatusCard()}

      <div class="card openers-card">
        <div class="section-title">Projected Openers Board</div>
        ${weekButtons()}
        <div class="openers-filters">
          <select id="openersWeek">
            <option value="all">All weeks</option>
            ${weeks().map(w => `<option value="${w}">Week ${w}</option>`).join('')}
          </select>
          <input id="openersTeam" placeholder="Filter team">
        </div>
        <div id="openersTableWrap"></div>
      </div>
    `;
  };

  window.mountOpenersPage = function(){
    const weekSelect = document.getElementById('openersWeek');
    const teamInput = document.getElementById('openersTeam');

    function draw(){
      const games = filteredGames();

      document.getElementById('openersTableWrap').innerHTML = `<table class="openers-table">
        <thead><tr>
          ${sortableTh('week','Week')}
          ${sortableTh('date','Date')}
          ${sortableTh('away','Away')}
          ${sortableTh('home','Home')}
          ${sortableTh('spread','Proj Spread')}
          ${sortableTh('total','Proj Total')}
        </tr></thead>
        <tbody>
          ${games.map(g => `<tr>
            <td>${esc(g.week ?? '—')}</td>
            <td>${fmtDate(g.date)}</td>
            <td>${teamCell(g.away_team)}</td>
            <td>${teamCell(g.home_team)}</td>
            <td><b>${projSpread(g)}</b></td>
            <td><b>${fmtNum(g.projected_total, 1)}</b></td>
          </tr>`).join('')}
        </tbody>
      </table>`;

      document.querySelectorAll('[data-openers-sort]').forEach(th => {
        th.addEventListener('click', () => {
          const key = th.dataset.openersSort;
          const cur = window.__openersSort || {key:'week', dir:'asc'};
          window.__openersSort = {key, dir: cur.key === key && cur.dir === 'asc' ? 'desc' : 'asc'};
          draw();
        });
      });

      document.querySelectorAll('[data-openers-week]').forEach(btn => {
        btn.classList.toggle('active', String(btn.dataset.openersWeek) === String(weekSelect.value || 'all'));
      });
    }

    weekSelect.addEventListener('input', draw);
    teamInput.addEventListener('input', draw);

    document.querySelectorAll('[data-openers-week]').forEach(btn => {
      btn.addEventListener('click', () => {
        weekSelect.value = btn.dataset.openersWeek;
        draw();
      });
    });

    draw();
  };

  window.installOpenersNav = function(){
    const nav = document.querySelector('.nav');
    if (!nav) return;

    if ([...nav.querySelectorAll('button')].some(b => String(b.textContent || '').trim() === 'Openers')) return;

    const btn = document.createElement('button');
    btn.textContent = 'Openers';
    btn.onclick = () => { location.hash = '#openers'; };

    const buttons = [...nav.querySelectorAll('button')];
    const lineHistory = buttons.find(b => String(b.textContent || '').trim() === 'Line History');
    const schedule = buttons.find(b => String(b.textContent || '').trim() === 'Season Schedule');
    const anchor = lineHistory || schedule;

    if (anchor && anchor.nextSibling) nav.insertBefore(btn, anchor.nextSibling);
    else nav.appendChild(btn);
  };

  document.addEventListener('DOMContentLoaded', () => setTimeout(window.installOpenersNav, 50));
  window.addEventListener('hashchange', () => setTimeout(window.installOpenersNav, 50));
  setTimeout(window.installOpenersNav, 100);
})();
</script>

<style id="openers-page-css">
.openers-model-status{
  margin-top:14px;
  border:1px solid rgba(96,165,250,.28);
  background:linear-gradient(180deg,rgba(37,99,235,.16),rgba(15,23,42,.58));
  border-radius:18px;
  padding:14px 16px;
}
.openers-status-title{
  font-weight:950;
  font-size:18px;
  color:#f8fafc;
}
.openers-status-sub{
  margin-top:3px;
  color:#aebddd;
  font-weight:750;
}
.openers-status-pills{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin-top:10px;
}
.openers-status-pills span{
  border:1px solid rgba(148,163,184,.22);
  background:rgba(15,23,42,.55);
  border-radius:999px;
  padding:6px 10px;
  color:#cbd5e1;
  font-size:12px;
  font-weight:850;
}
.openers-card{margin-top:16px;}
.openers-week-buttons{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0;}
.openers-week-buttons button{
  border:1px solid rgba(96,165,250,.35);
  background:rgba(15,35,74,.70);
  color:#dbeafe;
  border-radius:999px;
  padding:8px 13px;
  font-weight:950;
  cursor:pointer;
}
.openers-week-buttons button.active{background:#2563eb;color:white;border-color:#60a5fa;}
.openers-filters{display:flex;gap:10px;margin:10px 0 12px;}
.openers-filters select{display:none;}
.openers-filters input{
  max-width:320px;
  width:100%;
  padding:9px 11px;
  border-radius:10px;
  border:1px solid var(--line);
}
.openers-table{width:100%;border-collapse:collapse;table-layout:fixed;}
.openers-table th,.openers-table td{
  padding:7px 8px!important;
  font-size:13px!important;
  border-bottom:1px solid rgba(255,255,255,.08)!important;
  vertical-align:middle!important;
}
.openers-table th{
  color:#c7d2fe!important;
  text-transform:uppercase;
  letter-spacing:.07em;
  font-size:11px!important;
}
.openers-table th:nth-child(1),.openers-table td:nth-child(1){width:58px;}
.openers-table th:nth-child(2),.openers-table td:nth-child(2){width:82px;}
.openers-table th:nth-child(5),.openers-table td:nth-child(5){width:150px;}
.openers-table th:nth-child(6),.openers-table td:nth-child(6){width:105px;}
.openers-team{display:flex;align-items:center;gap:7px;min-width:0;}
.openers-team .team-logo-wrap{width:25px!important;height:25px!important;flex:0 0 25px!important;}
.openers-team .team-logo{width:22px!important;height:22px!important;object-fit:contain!important;}
.openers-team span:last-child{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.openers-rating-chip{
  margin-left:4px;
  border-radius:999px;
  padding:2px 6px;
  font-size:11px;
  font-weight:950;
  white-space:nowrap;
}
.openers-rating-chip.up{background:rgba(34,197,94,.16);color:#4ade80;border:1px solid rgba(34,197,94,.28);}
.openers-rating-chip.down{background:rgba(244,63,94,.14);color:#fb7185;border:1px solid rgba(244,63,94,.28);}
.openers-box-chip{
  margin-left:3px;
  border-radius:999px;
  padding:2px 6px;
  font-size:10px;
  font-weight:900;
  white-space:nowrap;
}
.openers-box-chip.good{background:rgba(34,197,94,.12);color:#86efac;}
.openers-box-chip.missing{background:rgba(245,158,11,.12);color:#fbbf24;}
.openers-sort-th{cursor:pointer;user-select:none;}
.openers-sort-th:hover{color:white!important;}
@media(max-width:900px){
  .openers-table{min-width:920px;}
  #openersTableWrap{overflow-x:auto;}
}
</style>
<!-- openers-page-end -->
'''

def direct_patch_router(s):
    # Remove old wrapper markers/route wrappers if any survived outside the block.
    s = s.replace("window.__openersPageInstalledV2", "window.__openersPageInstalledV3")

    # Route.
    if "hash==='#openers') html = renderOpenersPage()" not in s:
        route_patterns = [
            "else if (hash==='#results-center') html = renderResultsCenter();",
            "else if (hash === '#results-center') html = renderResultsCenter();",
        ]
        for pat in route_patterns:
            if pat in s:
                s = s.replace(pat, pat + "\n  else if (hash==='#openers') html = renderOpenersPage();", 1)
                break
        else:
            raise SystemExit("could not find route insertion point")

    # Mount.
    if "hash==='#openers') mountOpenersPage()" not in s:
        mount_patterns = [
            "if (hash==='#results-center') mountResultsCenter();",
            "if (hash === '#results-center') mountResultsCenter();",
        ]
        for pat in mount_patterns:
            if pat in s:
                s = s.replace(pat, pat + "\n  if (hash==='#openers') mountOpenersPage();", 1)
                break

    return s

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")

    s = direct_patch_router(s)

    # Defang any old openers render wrapper text if it somehow exists.
    s = s.replace("__openersRouteWrapped", "__openersRouteWrapped_DISABLED")

    path.write_text(s, encoding="utf-8")
    print(path, "openers v3 direct route + model status injected")
