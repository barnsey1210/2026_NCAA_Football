#!/usr/bin/env python3
from pathlib import Path
import json, re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]
DATA = Path("data/agents/home_command_center.json")

REMOVE_BLOCKS = [
    ("<!-- home-top-bets-start -->", "<!-- home-top-bets-end -->"),
    ("<!-- home-preseason-toggle-fix-start -->", "<!-- home-preseason-toggle-fix-end -->"),
]

START = "<!-- home-command-center-start -->"
END = "<!-- home-command-center-end -->"

payload = json.dumps(json.loads(DATA.read_text()), separators=(",", ":")) if DATA.exists() else '{"current_cards":[],"preseason_cards":[]}'

BLOCK = r'''
<!-- home-command-center-start -->
<script id="home-command-center-data" type="application/json">__HOME_COMMAND_CENTER_PAYLOAD__</script>

<script id="home-command-center-js">
(function(){
  if (window.__homeCommandCenterInstalled) return;
  window.__homeCommandCenterInstalled = true;

  function esc(v){
    if (typeof escapeHtml === 'function') return escapeHtml(String(v ?? ''));
    return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function readData(){
    const el = document.getElementById('home-command-center-data');
    if (!el) return {current_cards:[], preseason_cards:[]};
    try { return JSON.parse(el.textContent || '{}'); } catch(e) { return {current_cards:[], preseason_cards:[]}; }
  }

  function isHome(){
    if (!location.hash || location.hash === '#home') return true;
    const title = document.querySelector('.page-title');
    const txt = String(title ? title.textContent : '').trim().toLowerCase();
    return txt === 'daily betting dashboard' || txt === 'home';
  }

  function rowHtml(r){
    const tone = r.tone ? ` ${r.tone}` : '';
    const value = String(r.value || '').trim();
    return `<a class="home-cmd-row" href="${esc(r.link || '#home')}">
      <div class="home-cmd-row-main">
        <div class="home-cmd-row-topline">
          <span class="home-cmd-row-label">${esc(r.label || '')}</span>
          ${value ? `<span class="home-cmd-row-value${tone}">${esc(value)}</span>` : ''}
        </div>
        <div class="home-cmd-row-note">${esc(r.note || '')}</div>
      </div>
    </a>`;
  }


  function findTeamsInText(text){
    const raw = String(text || '');
    const teams = (DB && DB.teams ? DB.teams : [])
      .map(t => t.team)
      .filter(Boolean)
      .sort((a,b)=>b.length-a.length);
    const found = [];
    for (const t of teams) {
      if (raw.includes(t) && !found.includes(t)) found.push(t);
      if (found.length >= 2) break;
    }
    return found;
  }

  function teamLogoSmall(team){
    try {
      if (typeof teamImageImg === 'function') return teamImageImg(team);
      if (typeof advTeamLogo === 'function') return advTeamLogo(team);
    } catch(e) {}
    return '';
  }

  function teamRank(team){
    try {
      const t = (DB.teams || []).find(x => x.team === team);
      return t && t.rank ? `#${t.rank}` : '#—';
    } catch(e) {
      return '#—';
    }
  }

  function gameTeams(label){
    const parts = String(label || '').split(' at ');
    if (parts.length === 2) return {away:parts[0], home:parts[1]};
    const teams = findTeamsInText(label);
    return {away:teams[0] || '', home:teams[1] || ''};
  }

  function gameEdgeTableCard(c){
    const rows = c.rows || [];
    if (!rows.length) return '';
    const body = rows.map((r, i) => {
      const gt = gameTeams(r.label);
      return `<tr class="${i >= 5 ? 'home-cmd-extra-row' : ''}">
        <td class="hc-game-cell">
          <div class="hc-team-line">${teamLogoSmall(gt.away)}<span>${esc(gt.away || r.label)}</span><em>${teamRank(gt.away)}</em></div>
          <div class="hc-team-line">${teamLogoSmall(gt.home)}<span>${esc(gt.home)}</span><em>${teamRank(gt.home)}</em></div>
        </td>
        <td class="hc-bet-cell good">${esc(r.value || '')}</td>
        <td class="hc-note-cell">${esc(r.note || '')}</td>
      </tr>`;
    }).join('');
    return `<div class="home-cmd-card home-cmd-table-card">
      <div class="home-cmd-card-title">${esc(c.title || '')}</div>
      <div class="home-cmd-card-sub">${esc(c.subtitle || '')}</div>
      <table class="home-cmd-table">
        <thead><tr><th>Game</th><th>Bet</th><th>Market vs model</th></tr></thead>
        <tbody>${body}</tbody>
      </table>
      ${rows.length > 5 ? '<button class="home-cmd-more" type="button">Show more</button>' : ''}
    </div>`;
  }

  function gamesOfWeekTableCard(c){
    const rows = c.rows || [];
    if (!rows.length) return '';
    const body = rows.map((r, i) => {
      const gt = gameTeams(r.label);
      return `<tr class="${i >= 5 ? 'home-cmd-extra-row' : ''}">
        <td class="hc-team-pair">
          <div class="hc-team-line">${teamLogoSmall(gt.away)}<span>${esc(gt.away || r.label)}</span><em>${teamRank(gt.away)}</em></div>
          <div class="hc-team-line">${teamLogoSmall(gt.home)}<span>${esc(gt.home)}</span><em>${teamRank(gt.home)}</em></div>
        </td>
        <td class="hc-rank-cell">${esc(r.value || '')}</td>
        <td class="hc-note-cell">${esc(r.note || '')}</td>
      </tr>`;
    }).join('');
    return `<div class="home-cmd-card home-cmd-table-card">
      <div class="home-cmd-card-title">${esc(c.title || '')}</div>
      <div class="home-cmd-card-sub">${esc(c.subtitle || '')}</div>
      <table class="home-cmd-table">
        <thead><tr><th>Game</th><th>Projected score</th><th>Projection / market</th></tr></thead>
        <tbody>${body}</tbody>
      </table>
      ${rows.length > 5 ? '<button class="home-cmd-more" type="button">Show more</button>' : ''}
    </div>`;
  }


  function cardHtml(c){
    if ((c.title || '').includes('Biggest Game Edges')) return gameEdgeTableCard(c);
    if ((c.title || '').includes('Games of the Week')) return gamesOfWeekTableCard(c);
    const rows = c.rows || [];
    if (!rows.length) return '';
    const rowHtmls = rows.map((r, i) => {
      const html = rowHtml({...r, link:c.link});
      return i >= 5 ? html.replace('class="home-cmd-row"', 'class="home-cmd-row home-cmd-extra-row"') : html;
    }).join('');
    return `<div class="home-cmd-card">
      <div class="home-cmd-card-title">${esc(c.title || '')}</div>
      <div class="home-cmd-card-sub">${esc(c.subtitle || '')}</div>
      <div class="home-cmd-card-rows">
        ${rowHtmls}
      </div>
      ${rows.length > 5 ? '<button class="home-cmd-more" type="button">Show more</button>' : ''}
    </div>`;
  }

  function render(view, week){
    const data = readData();
    const weeks = data.weeks || [];
    const selectedWeek = String(week || data.default_week || (weeks.length ? weeks[0] : ''));
    const cards = view === 'preseason'
      ? (data.preseason_cards || [])
      : ((data.current_cards_by_week || {})[selectedWeek] || []);
    const sub = view === 'preseason'
      ? 'Frozen preseason baseline plus preseason market/edge prep.'
      : `Week ${selectedWeek}: current market edges, futures value, line moves, injuries, and betting spots.`;

    const weekTabs = view === 'current'
      ? `<div class="home-week-tabs" id="homeWeekTabs">
          ${weeks.map(w => `<button type="button" data-week="${esc(w)}" class="${String(w) === selectedWeek ? 'active' : ''}">W${esc(w)}</button>`).join('')}
        </div>`
      : '';

    return `<div class="home-command-center" id="homeCommandCenter" data-view="${esc(view)}" data-week="${esc(selectedWeek)}">
      <div class="home-command-head">
        <div>
          <div class="section-title">${view === 'preseason' ? 'Preseason Command Center' : 'Current Season Command Center'}</div>
          <div class="small muted">${sub}</div>
        </div>
        <div class="home-cmd-updated">Updated ${esc(String(data.updated_at || '').replace('T',' '))}</div>
      </div>

      <div class="home-season-toggle" id="homeSeasonToggle">
        <button type="button" data-view="current" class="${view === 'current' ? 'active' : ''}">Current Season</button>
        <button type="button" data-view="preseason" class="${view === 'preseason' ? 'active' : ''}">Preseason Snapshot</button>
      </div>

      ${weekTabs}

      <div class="home-cmd-grid">
        ${cards.map(cardHtml).join('')}
      </div>
    </div>`;
  }

  function mount(view='current', week=null){
    if (!isHome()) return;
    const app = document.getElementById('app');
    if (!app) return;

    const existing = document.getElementById('homeCommandCenter');
    const priorWeek = existing ? existing.dataset.week : null;
    if (!week) week = priorWeek;

    if (existing) existing.remove();

    const hero = app.querySelector('.hero');
    const firstGrid = app.querySelector('.grid');
    const html = render(view, week);

    if (hero) hero.insertAdjacentHTML('afterend', html);
    else if (firstGrid) firstGrid.insertAdjacentHTML('beforebegin', html);
    else app.insertAdjacentHTML('afterbegin', html);

    const toggle = document.getElementById('homeSeasonToggle');
    if (toggle) {
      toggle.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => mount(btn.dataset.view || 'current', week));
      });
    }

    const weekTabs = document.getElementById('homeWeekTabs');
    if (weekTabs) {
      weekTabs.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => mount('current', btn.dataset.week));
      });
    }

    document.querySelectorAll('.home-cmd-more').forEach(btn => {
      btn.addEventListener('click', () => {
        const card = btn.closest('.home-cmd-card');
        if (!card) return;
        card.classList.toggle('expanded');
        btn.textContent = card.classList.contains('expanded') ? 'Show less' : 'Show more';
      });
    });
  }

  function schedule(){
    setTimeout(() => mount('current'), 50);
    setTimeout(() => {
      if (!document.getElementById('homeCommandCenter')) mount('current');
    }, 300);
  }

  const oldRender = window.render;
  if (typeof oldRender === 'function' && !oldRender.__homeCommandCenterWrapped) {
    const wrapped = function(){
      const result = oldRender.apply(this, arguments);
      schedule();
      return result;
    };
    wrapped.__homeCommandCenterWrapped = true;
    window.render = wrapped;
  }

  window.addEventListener('hashchange', schedule);
  document.addEventListener('DOMContentLoaded', schedule);
  schedule();
})();
</script>

<style id="home-command-center-css">
.home-command-center{margin:14px 0;border:1px solid rgba(96,165,250,.28);border-radius:18px;background:linear-gradient(180deg,rgba(22,47,95,.70),rgba(15,23,42,.50));padding:14px}
.home-command-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.home-cmd-updated{font-size:12px;color:#aab7d4;white-space:nowrap}
.home-season-toggle{display:inline-flex;gap:8px;margin:12px 0;padding:5px;border:1px solid rgba(255,255,255,.12);border-radius:999px;background:rgba(15,23,42,.55)}
.home-season-toggle button{border:0;border-radius:999px;padding:8px 13px;background:transparent;color:#cbd5e1;font-weight:900;cursor:pointer}
.home-season-toggle button.active{background:rgba(37,99,235,.75);color:#fff}
.home-cmd-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.home-cmd-card{border:1px solid rgba(255,255,255,.08);border-radius:15px;background:rgba(2,6,23,.24);padding:11px;min-height:185px}
.home-cmd-card-title{font-weight:950;font-size:16px}
.home-cmd-card-sub{font-size:12px;color:#aab7d4;margin:3px 0 9px;line-height:1.25}
.home-cmd-card-rows{display:grid;gap:7px}
.home-cmd-row{display:flex;justify-content:space-between;gap:8px;text-decoration:none;color:inherit;border-top:1px solid rgba(255,255,255,.07);padding-top:7px}
.home-cmd-row:first-child{border-top:0;padding-top:0}
.home-cmd-row-label{font-weight:900;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:230px}
.home-cmd-row-note{font-size:11px;color:#9fb0d0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:260px;margin-top:2px}
.home-cmd-row-value{font-weight:950;white-space:nowrap;text-align:right;color:#dbeafe}
.home-cmd-row-value.good{color:#4ade80}
.home-cmd-row-value.bad{color:#fb7185}
.home-cmd-empty{font-size:12px;color:#94a3b8;padding-top:8px}
@media(max-width:1200px){.home-cmd-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:800px){.home-cmd-grid{grid-template-columns:1fr}.home-command-head{display:block}.home-cmd-updated{margin-top:4px}.home-cmd-row-label,.home-cmd-row-note{max-width:100%}}
</style>
<!-- home-command-center-end -->
'''.replace('__HOME_COMMAND_CENTER_PAYLOAD__', payload)

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    for a,b in REMOVE_BLOCKS:
        s = re.sub(re.escape(a) + r".*?" + re.escape(b), "", s, flags=re.S)

    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")

    path.write_text(s, encoding="utf-8")
    print(path, "injected home command center")
