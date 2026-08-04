#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- enhance-openers-table-start -->"
END = "<!-- enhance-openers-table-end -->"

BLOCK = r'''
<!-- enhance-openers-table-start -->
<script id="enhance-openers-table-js">
(function(){
  if (window.__enhanceOpenersTableInstalledV2) return;
  window.__enhanceOpenersTableInstalledV2 = true;

  function esc(v){
    return String(v == null ? '' : v)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }

  function n(v){
    const x = Number(v);
    return Number.isFinite(x) ? x : null;
  }

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

  function logo(team){
    try {
      if (typeof teamImageImg === 'function') return teamImageImg(team);
      if (typeof advTeamLogo === 'function') return advTeamLogo(team);
    } catch(e) {}
    return '';
  }

  function teamRank(team){
    try {
      const row = (DB.teams || []).find(t => t.team === team);
      return row && row.rank ? `#${row.rank}` : '';
    } catch(e) {
      return '';
    }
  }

  function teamLinkHtml(team){
    try {
      if (typeof linkTeam === 'function') {
        return `<span class="openers-team-link-only">${linkTeam(team)}</span>`;
      }
    } catch(e) {}
    return `<span class="openers-team-name">${esc(team || '—')}</span>`;
  }

  function teamCell(team){
    const rank = teamRank(team);
    return `<span class="openers-team tight">
      ${logo(team)}
      ${teamLinkHtml(team)}
      ${rank ? `<small>${esc(rank)}</small>` : ''}
    </span>`;
  }

  function projSpread(g){
    const margin = n(g.projected_margin_home);
    if (margin == null) return '—';
    const fav = margin >= 0 ? g.home_team : g.away_team;
    return `${esc(fav)} -${Math.abs(margin).toFixed(1).replace(/\.0$/,'')}`;
  }

  const SPREAD_CLOSE_CONVERGENCE = 0.20;

  function homeLineText(g, homeLine){
    const line = n(homeLine);
    if (line == null) return '—';
    if (Math.abs(line) < 0.05) return 'Pick';
    const team = line < 0 ? g.home_team : g.away_team;
    return `${esc(team)} -${Math.abs(line).toFixed(1).replace(/\.0$/,'')}`;
  }

  function openingHomeLine(g){
    return n(g.market_spread_open_home ?? g.opening_spread_home ?? g.market_open_spread_home);
  }

  function spreadMarketMoveCell(g){
    const margin = n(g.projected_margin_home);
    if (margin == null) return '<span class="muted">—</span>';

    const fairHomeLine = -margin;
    const opener = openingHomeLine(g);
    const fairText = homeLineText(g, fairHomeLine);
    if (opener == null) {
      return `<div class="openers-spread-stack"><b>${fairText}</b><small>Fair value · opener pending</small></div>`;
    }

    const gap = fairHomeLine - opener;
    const predictedClose = opener + SPREAD_CLOSE_CONVERGENCE * gap;
    const direction = Math.abs(gap) < 0.25
      ? 'No material move'
      : `Toward ${esc(gap < 0 ? g.home_team : g.away_team)}`;

    return `<div class="openers-spread-stack">
      <b>${fairText}</b>
      <small>Open ${homeLineText(g, opener)}</small>
      <small class="openers-est-close">Est close ${homeLineText(g, predictedClose)}</small>
      <small class="openers-move-direction">${direction} · 20% convergence</small>
    </div>`;
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

  function angleRows(g){
    try {
      return (window.GAME_BETTING_ANGLES || []).filter(r => String(r.game_id) === String(g.game_id));
    } catch(e) {
      return [];
    }
  }

  function meaningfulRows(g){
    return angleRows(g).filter(r => {
      const txt = `${r.angle_key || ''} ${r.angle_label || ''} ${r.reason || ''}`.toLowerCase();
      if (/variance|high model variance|medium model variance/.test(txt)) return false;
      if (/coin_toss/.test(txt)) return false;
      if (/1h|2h|first half|second half|travel_1h/.test(txt)) return false;
      return true;
    });
  }

  function findAngle(g, type){
    const rows = meaningfulRows(g);

    const tests = {
      coach: r => /coach_ats|coach ats|full-game coach|full game coach/.test(`${r.angle_key || ''} ${r.angle_label || ''} ${r.reason || ''}`.toLowerCase()),
      total: r => /coach_total|coach totals|total support|over\/under|over under/.test(`${r.angle_key || ''} ${r.angle_label || ''} ${r.reason || ''}`.toLowerCase()),
      rp: r => /rp_support|returning production|rp support/.test(`${r.angle_key || ''} ${r.angle_label || ''} ${r.reason || ''}`.toLowerCase()),
      travel: r => /travel|road trip|distance|body clock/.test(`${r.angle_key || ''} ${r.angle_label || ''} ${r.reason || ''}`.toLowerCase()),
      sched: r => /bye|b2b|back-to-back|lookahead|sandwich|short rest|schedule spot/.test(`${r.angle_key || ''} ${r.angle_label || ''} ${r.reason || ''}`.toLowerCase()),
      injury: r => /injury|injuries|qb out|depth chart|status/.test(`${r.angle_key || ''} ${r.angle_label || ''} ${r.reason || ''}`.toLowerCase())
    };

    return rows.find(tests[type]) || null;
  }

  function angleCell(g, type){
    const a = findAngle(g, type);
    if (!a) return '<td class="openers-angle-cell muted">—</td>';

    const team = a.side_team || a.team || a.side || '';
    const title = [
      a.angle_label || a.angle_key || type,
      team ? `Team: ${team}` : '',
      a.reason || ''
    ].filter(Boolean).join(' · ');

    return `<td class="openers-angle-cell" title="${esc(title)}">
      <span class="openers-angle-logo">${team ? logo(team) : '•'}</span>
    </td>`;
  }

  function ratingImpactForGame(g){
    const data = window.POSTGAME_RATING_IMPACTS || window.OPENERS_RATING_IMPACTS || {};
    const away = data[g.away_team] || null;
    const home = data[g.home_team] || null;
    return {away, home};
  }

  function ratingImpactCell(g){
    const {away, home} = ratingImpactForGame(g);

    function chip(team, row){
      if (!row) return '';
      const delta = n(row.projected_rating_delta ?? row.rating_delta ?? row.delta);
      const status = String(row.box_score_status || row.status || '').toLowerCase();
      const captured = /captured|complete|final/.test(status);
      if (delta == null && !status) return '';

      const cls = delta == null ? 'pending' : (delta >= 0 ? 'up' : 'down');
      const val = delta == null ? '—' : `${delta >= 0 ? '+' : ''}${delta.toFixed(1)}`;
      return `<span class="openers-impact-chip ${cls}" title="${esc(team)} postgame box-score rating-impact estimate. Box score: ${captured ? 'captured' : 'missing/pending'}">${esc(val)}</span>`;
    }

    const html = [chip(g.away_team, away), chip(g.home_team, home)].filter(Boolean).join('');
    if (html) return `<td class="openers-impact-cell">${html}</td>`;

    return `<td class="openers-impact-cell pending" title="Pending postgame box-score impact model">Pending</td>`;
  }

  function weeks(){
    return [...new Set((DB.games || []).map(g => g.week).filter(w => w !== null && w !== undefined && w !== ''))]
      .map(w => Number(w)).filter(w => Number.isFinite(w)).sort((a,b)=>a-b);
  }

  function normalizeTeamType(v){
    const raw = String(v || '').toUpperCase();
    if (raw.includes('FCS')) return 'FCS';
    if (raw.includes('FBS')) return 'FBS';
    return '';
  }

  function teamSubdivision(team){
    try {
      const t = (DB.teams || []).find(x => x.team === team);
      if (!t) return 'FCS';
      const raw = t.subdivision || t.classification || t.division || t.level || t.fbs_fcs || t.team_type || '';
      return normalizeTeamType(raw) || 'FBS';
    } catch(e) {
      return 'FCS';
    }
  }

  function gameType(g){
    const a = teamSubdivision(g.away_team);
    const h = teamSubdivision(g.home_team);
    if (a === 'FBS' && h === 'FBS') return 'fbs_fbs';
    if ((a === 'FBS' && h === 'FCS') || (a === 'FCS' && h === 'FBS')) return 'fbs_fcs';
    if (a === 'FCS' && h === 'FCS') return 'fcs_fcs';
    return 'other';
  }

  function filteredGames(){
    const week = document.getElementById('openersWeek')?.value || 'all';
    const team = String(document.getElementById('openersTeam')?.value || '').trim().toLowerCase();
    const gameTypeFilter = document.getElementById('openersGameType')?.value || 'all';

    let games = [...(DB.games || [])];

    if (week !== 'all') games = games.filter(g => String(g.week) === String(week));
    if (gameTypeFilter !== 'all') games = games.filter(g => gameType(g) === gameTypeFilter);
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

  function drawOpenersEnhanced(){
    const wrap = document.getElementById('openersTableWrap');
    if (!wrap) return;

    const games = filteredGames();

    wrap.innerHTML = `<div class="openers-movement-note">
      <b>Market-movement estimate:</b> spread close = opener + 20% of the gap toward model fair value.
      Existing spread and total edges remain full model-vs-market gaps. Closing-total movement is not estimated yet.
    </div><table class="openers-table openers-table-enhanced">
      <thead><tr>
        ${sortableTh('week','Wk')}
        ${sortableTh('date','Date')}
        ${sortableTh('away','Away')}
        ${sortableTh('home','Home')}
        ${sortableTh('spread','Fair / Est Close')}
        ${sortableTh('total','Fair Total')}
        <th title="Projected rating movement from previous game box score, before ratings systems update">LW Impact</th>
        <th title="Full-game coach ATS edge">Coach ATS</th>
        <th title="Coach over/under or totals edge">Coach Tot</th>
        <th title="Returning production edge, strongest in weeks 0-4">RP</th>
        <th title="Travel/body-clock/road-trip angle">Travel</th>
        <th title="Lookahead, sandwich, B2B road, off bye, or rest spot">Sched</th>
        <th title="Injury/depth-chart alert">Inj</th>
      </tr></thead>
      <tbody>
        ${games.map(g => `<tr>
          <td>${esc(g.week ?? '—')}</td>
          <td>${fmtDate(g.date)}</td>
          <td>${teamCell(g.away_team)}</td>
          <td>${teamCell(g.home_team)}</td>
          <td class="openers-proj-spread">${spreadMarketMoveCell(g)}</td>
          <td class="openers-proj-total"><b>${fmtNum(g.projected_total, 1)}</b></td>
          ${ratingImpactCell(g)}
          ${angleCell(g, 'coach')}
          ${angleCell(g, 'total')}
          ${angleCell(g, 'rp')}
          ${angleCell(g, 'travel')}
          ${angleCell(g, 'sched')}
          ${angleCell(g, 'injury')}
        </tr>`).join('')}
      </tbody>
    </table>`;

    document.querySelectorAll('[data-openers-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.openersSort;
        const cur = window.__openersSort || {key:'week', dir:'asc'};
        window.__openersSort = {key, dir: cur.key === key && cur.dir === 'asc' ? 'desc' : 'asc'};
        drawOpenersEnhanced();
      });
    });

    document.querySelectorAll('[data-openers-week]').forEach(btn => {
      const val = document.getElementById('openersWeek')?.value || 'all';
      btn.classList.toggle('active', String(btn.dataset.openersWeek) === String(val));
    });
  }

  function enhanceMount(){
    const oldMount = window.mountOpenersPage;
    if (typeof oldMount !== 'function' || oldMount.__enhancedOpenersTableV2) return;

    window.mountOpenersPage = function(){
      const result = oldMount.apply(this, arguments);

      const weekSelect = document.getElementById('openersWeek');
      const teamInput = document.getElementById('openersTeam');

      const filters = document.querySelector('.openers-filters');
      if (filters && !document.getElementById('openersGameType')) {
        filters.insertAdjacentHTML('afterbegin', `
          <select id="openersGameType" class="openers-game-type-filter">
            <option value="all">All game types</option>
            <option value="fbs_fbs">FBS vs FBS only</option>
            <option value="fbs_fcs">FBS vs FCS only</option>
          </select>
        `);
      }
      const gameTypeSelect = document.getElementById('openersGameType');

      drawOpenersEnhanced();

      if (weekSelect && !weekSelect.dataset.openersEnhancedBoundV2) {
        weekSelect.dataset.openersEnhancedBoundV2 = '1';
        weekSelect.addEventListener('input', () => setTimeout(drawOpenersEnhanced, 20));
        weekSelect.addEventListener('change', () => setTimeout(drawOpenersEnhanced, 20));
      }

      if (teamInput && !teamInput.dataset.openersEnhancedBoundV2) {
        teamInput.dataset.openersEnhancedBoundV2 = '1';
        teamInput.addEventListener('input', () => setTimeout(drawOpenersEnhanced, 20));
      }

      if (gameTypeSelect && !gameTypeSelect.dataset.openersEnhancedBoundV2) {
        gameTypeSelect.dataset.openersEnhancedBoundV2 = '1';
        gameTypeSelect.addEventListener('input', () => setTimeout(drawOpenersEnhanced, 20));
        gameTypeSelect.addEventListener('change', () => setTimeout(drawOpenersEnhanced, 20));
      }

      document.querySelectorAll('[data-openers-week]').forEach(btn => {
        if (!btn.dataset.openersEnhancedBoundV2) {
          btn.dataset.openersEnhancedBoundV2 = '1';
          btn.addEventListener('click', () => {
            const sel = document.getElementById('openersWeek');
            if (sel) sel.value = btn.dataset.openersWeek;
            setTimeout(drawOpenersEnhanced, 30);
          });
        }
      });

      return result;
    };

    window.mountOpenersPage.__enhancedOpenersTableV2 = true;
  }

  function run(){
    enhanceMount();
    if (location.hash === '#openers') setTimeout(drawOpenersEnhanced, 80);
  }

  window.addEventListener('hashchange', run);
  document.addEventListener('DOMContentLoaded', run);
  run();
})();
</script>

<style id="enhance-openers-table-css">
.openers-week-buttons{
  flex-wrap:nowrap!important;
  overflow-x:auto!important;
  gap:5px!important;
  padding-bottom:2px!important;
}
.openers-week-buttons button{
  padding:7px 10px!important;
  font-size:12px!important;
  min-width:auto!important;
  flex:0 0 auto!important;
}
.openers-table-enhanced{
  table-layout:fixed!important;
  width:100%!important;
}
.openers-movement-note{
  margin:0 0 10px;
  border:1px solid rgba(96,165,250,.25);
  background:rgba(37,99,235,.09);
  color:#aebddd;
  border-radius:12px;
  padding:9px 11px;
  font-size:11px;
  font-weight:800;
}
.openers-movement-note b{color:#dbeafe;}
.openers-table-enhanced th,
.openers-table-enhanced td{
  padding:6px 6px!important;
  font-size:12px!important;
}
.openers-table-enhanced th:nth-child(1),
.openers-table-enhanced td:nth-child(1){
  width:38px!important;
}
.openers-table-enhanced th:nth-child(2),
.openers-table-enhanced td:nth-child(2){
  width:66px!important;
}
.openers-table-enhanced th:nth-child(3),
.openers-table-enhanced td:nth-child(3),
.openers-table-enhanced th:nth-child(4),
.openers-table-enhanced td:nth-child(4){
  width:19%!important;
}
.openers-table-enhanced th:nth-child(5),
.openers-table-enhanced td:nth-child(5){
  width:170px!important;
}
.openers-table-enhanced th:nth-child(6),
.openers-table-enhanced td:nth-child(6){
  width:58px!important;
}
.openers-table-enhanced th:nth-child(n+7),
.openers-table-enhanced td:nth-child(n+7){
  width:50px!important;
  text-align:center!important;
}
.openers-table-enhanced th:nth-child(7),
.openers-table-enhanced td:nth-child(7){
  width:78px!important;
}
.openers-team.tight{
  gap:6px!important;
}
.openers-team.tight .team-logo-wrap{
  width:22px!important;
  height:22px!important;
  flex:0 0 22px!important;
}
.openers-team.tight .team-logo{
  width:20px!important;
  height:20px!important;
}
.openers-team-name{
  max-width:132px;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.openers-team.tight small{
  color:#94a3b8;
  font-weight:850;
  white-space:nowrap;
}
.openers-proj-spread{
  white-space:nowrap!important;
  line-height:1.12!important;
}
.openers-proj-spread b{
  display:inline-block;
  max-width:168px;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.openers-spread-stack{display:flex;flex-direction:column;gap:2px;line-height:1.12;}
.openers-spread-stack b{color:#f8fafc;}
.openers-spread-stack small{color:#94a3b8;font-size:10px;font-weight:800;white-space:nowrap;}
.openers-spread-stack .openers-est-close{color:#bfdbfe;font-weight:950;}
.openers-spread-stack .openers-move-direction{color:#4ade80;}
.openers-proj-total{
  white-space:nowrap!important;
}
.openers-angle-cell{
  text-align:center!important;
  vertical-align:middle!important;
}
.openers-angle-cell.muted{
  color:#475569!important;
}
.openers-angle-logo{
  display:inline-flex;
  align-items:center;
  justify-content:center;
}
.openers-angle-logo .team-logo-wrap{
  width:22px!important;
  height:22px!important;
  flex:0 0 22px!important;
}
.openers-angle-logo .team-logo{
  width:20px!important;
  height:20px!important;
  object-fit:contain!important;
}
.openers-impact-cell{
  text-align:center!important;
  white-space:nowrap!important;
  color:#94a3b8;
  font-size:11px!important;
  font-weight:850;
}
.openers-impact-chip{
  display:inline-block;
  border-radius:999px;
  padding:2px 6px;
  margin:0 1px;
  font-size:10px;
  font-weight:950;
}
.openers-impact-chip.up{
  background:rgba(34,197,94,.15);
  color:#4ade80;
  border:1px solid rgba(34,197,94,.30);
}
.openers-impact-chip.down{
  background:rgba(244,63,94,.14);
  color:#fb7185;
  border:1px solid rgba(244,63,94,.30);
}
.openers-impact-cell.pending{
  color:#64748b!important;
}
@media(max-width:1250px){
  .openers-table-enhanced{
    min-width:1220px!important;
  }
  #openersTableWrap{
    overflow-x:auto!important;
  }
}

.openers-team-link-only .team-logo-wrap,
.openers-team-link-only img{
  display:none!important;
}
.openers-team-link-only a{
  color:#dbeafe!important;
  text-decoration:underline!important;
  font-weight:850!important;
  max-width:132px;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
  display:inline-block;
}
.openers-game-type-filter{
  display:block!important;
  max-width:180px!important;
  padding:9px 11px!important;
  border-radius:10px!important;
  border:1px solid var(--line)!important;
}

</style>
<!-- enhance-openers-table-end -->
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
    print(path, "openers table enhanced v2")
