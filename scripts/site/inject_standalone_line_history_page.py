from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- standalone-line-history-page-start -->"
END = "<!-- standalone-line-history-page-end -->"

BLOCK = r'''
<!-- standalone-line-history-page-start -->
<script id="standalone-line-history-page-js">
(function(){
  if (window.__standaloneLineHistoryInstalled) return;
  window.__standaloneLineHistoryInstalled = true;

  function esc(x){
    if (typeof escapeHtml === 'function') return escapeHtml(String(x ?? ''));
    return String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function txt(x){ return String(x || '').trim(); }
  function norm(x){ return txt(x).toLowerCase(); }

  function nval(x){
    if (x === null || x === undefined || x === '') return null;
    const n = Number(x);
    return Number.isFinite(n) ? n : null;
  }

  function validSpread(x){
    const n = nval(x);
    return n !== null && Math.abs(n) <= 80;
  }

  function validTotal(x){
    const n = nval(x);
    return n !== null && n >= 20 && n <= 100;
  }

  function cleanPrice(x){
    const n = nval(x);
    if (n === null || n === 0) return '—';
    return n.toFixed(0);
  }

  function fmtNum(x){
    const n = nval(x);
    if (n === null) return '—';
    return n.toFixed(1).replace(/\.0$/, '');
  }

  function fmtDate(v){
    if (!v) return '—';
    const d = new Date(String(v) + 'T00:00:00');
    if (Number.isNaN(d.getTime())) return String(v);
    return d.toLocaleDateString(undefined, {month:'short', day:'numeric'});
  }

  function spreadText(home, away, x){
    const n = nval(x);
    if (n === null) return '—';
    if (Math.abs(n) < 0.05) return 'Pick';
    if (n < 0) return `${home} ${fmtNum(n)}`;
    return `${away} +${fmtNum(n)}`;
  }

  function compactSpreadChange(home, away, openVal, curVal){
    const o = nval(openVal);
    const c = nval(curVal);
    if (o === null || c === null) return 'No spread';

    const openTeam = Math.abs(o) < 0.05 ? 'Pick' : (o < 0 ? home : away);
    const curTeam = Math.abs(c) < 0.05 ? 'Pick' : (c < 0 ? home : away);

    const openLine = Math.abs(o) < 0.05 ? 'Pick' : `${openTeam} ${o < 0 ? fmtNum(o) : '+' + fmtNum(o)}`;
    const curLineOnly = Math.abs(c) < 0.05 ? 'Pick' : `${c < 0 ? fmtNum(c) : '+' + fmtNum(c)}`;

    if (openTeam === curTeam && openTeam !== 'Pick') {
      return `${openLine} → ${curLineOnly}`;
    }
    return `${openLine} → ${spreadText(home, away, c)}`;
  }

  function moveLabel(x){
    const n = nval(x);
    if (n === null) return '—';
    if (Math.abs(n) < 0.25) return '—';
    return n > 0 ? `↑ ${fmtNum(Math.abs(n))}` : `↓ ${fmtNum(Math.abs(n))}`;
  }

  function moveClass(x){
    const n = nval(x);
    if (n === null || Math.abs(n) < 0.25) return 'flat';
    return n > 0 ? 'up' : 'down';
  }

  function detailMoveChip(x){
    const n = nval(x);
    if (n === null || Math.abs(n) < 0.25) return '';
    return `<span class="lh2-detail-move ${moveClass(n)}">${moveLabel(n)}</span>`;
  }

  function teamLogoHtml(team){
    try {
      if (typeof teamImageImg === 'function') return teamImageImg(team);
      if (typeof teamWithLogo === 'function') return teamWithLogo(team);
    } catch(e) {}
    const letter = txt(team).charAt(0).toUpperCase() || '?';
    return `<span class="lh2-team-fallback">${letter}</span>`;
  }

  function teamCell(team){
    return `<span class="lh2-team">${teamLogoHtml(team)}<span>${esc(team)}</span></span>`;
  }

  function bookHtml(book){
    if (!book) return '—';
    try {
      if (typeof sportsbookLogo === 'function') return sportsbookLogo(book);
      if (typeof marketBookLogo === 'function') return marketBookLogo(book);
      if (typeof bookLogoBadge === 'function') return bookLogoBadge(book);
    } catch(e) {}
    return esc(book);
  }

  function dbObj(){ return window.DB || window.db || window.__DB || null; }

  function gameIndex(){
    const db = dbObj();
    const games = db && Array.isArray(db.games) ? db.games : [];
    const idx = {};
    games.forEach(g => { idx[String(g.game_id)] = g; });
    return idx;
  }

  function teamConfIndex(){
    const db = dbObj();
    const teams = db && Array.isArray(db.teams) ? db.teams : [];
    const idx = {};
    teams.forEach(t => {
      const name = t.team || t.name || t.school || '';
      idx[norm(name)] = t.conference || t.conf || '';
    });
    return idx;
  }

  function uniqueDaily(rows, kind){
    const out = new Map();

    for (const r of rows || []) {
      const date = r.snapshot_date;
      if (!date) continue;

      const value = kind === 'spread' ? nval(r.market_spread_home) : nval(r.market_total);
      const ok = kind === 'spread' ? validSpread(value) : validTotal(value);
      if (!ok) continue;

      const rec = {
        date,
        value,
        book: kind === 'spread' ? txt(r.market_spread_book) : txt(r.market_total_book),
        source: txt(r.source || r.market_line_source || 'History'),
        spreadPrice: r.market_spread_price,
        overPrice: r.market_total_over_price,
        underPrice: r.market_total_under_price,
        rawPrice: kind === 'spread' ? r.market_spread_price : (r.market_total_over_price ?? r.market_total_under_price)
      };

      const existing = out.get(date);

      function score(x){
        if (!x) return -1;
        let s = 0;
        if (cleanPrice(x.rawPrice) !== '—') s += 10;
        if (norm(x.source).includes('sportsgameodds')) s += 6;
        if (norm(x.source).includes('action')) s += 4;
        if (x.book) s += 1;
        return s;
      }

      if (!existing || score(rec) >= score(existing)) out.set(date, rec);
    }

    return [...out.values()].sort((a,b) => String(a.date).localeCompare(String(b.date)));
  }

  function stats(arr){
    if (!arr.length) return null;
    const open = arr[0];
    const cur = arr[arr.length - 1];
    const low = arr.reduce((a,b) => b.value < a.value ? b : a, arr[0]);
    const high = arr.reduce((a,b) => b.value > a.value ? b : a, arr[0]);
    return { arr, open, cur, low, high, move: cur.value - open.value };
  }

  function lastValid(rows, key, validator){
    for (let i = (rows || []).length - 1; i >= 0; i--) {
      if (validator(rows[i][key])) return Number(rows[i][key]);
    }
    return null;
  }

  function buildLineHistoryGames(){
    const hist = window.MATCHUP_LINE_HISTORY || {};
    const dbGames = gameIndex();
    const confs = teamConfIndex();

    return Object.entries(hist).map(([gameId, raw]) => {
      const rows = (raw || []).slice().sort((a,b) => String(a.snapshot_date || '').localeCompare(String(b.snapshot_date || '')));
      const latest = rows[rows.length - 1] || {};
      const dbGame = dbGames[String(gameId)] || {};

      const away = latest.away_team || dbGame.away_team || '';
      const home = latest.home_team || dbGame.home_team || '';
      const week = nval(dbGame.week ?? latest.site_week ?? latest.week);
      const awayConf = txt(dbGame.away_conference || dbGame.awayConference || confs[norm(away)]);
      const homeConf = txt(dbGame.home_conference || dbGame.homeConference || confs[norm(home)]);
      const conference = txt(dbGame.conference || dbGame.conf || latest.conference || homeConf || awayConf);
      const gameDate = latest.game_date || dbGame.date || latest.date || '';

      const spread = stats(uniqueDaily(rows, 'spread'));
      const total = stats(uniqueDaily(rows, 'total'));
      const modelSpread = lastValid(rows, 'model_spread_home', validSpread);
      const modelTotal = lastValid(rows, 'projected_total', validTotal);

      const dates = [...new Set(rows.map(r => r.snapshot_date).filter(Boolean))].sort();

      return {
        gameId, rows, away, home, week, awayConf, homeConf, conference, gameDate,
        count: dates.length,
        firstDate: dates[0] || '',
        lastDate: dates[dates.length - 1] || '',
        spread, total, modelSpread, modelTotal,
        search: norm(`${away} ${home}`)
      };
    });
  }

  function spreadEdge(g){
    if (!g.spread || !validSpread(g.modelSpread)) return '—';
    const edge = Number(g.modelSpread) - Number(g.spread.cur.value);
    if (Math.abs(edge) < 0.25) return 'No edge';
    return `${edge > 0 ? g.home : g.away} +${fmtNum(Math.abs(edge))}`;
  }

  function totalEdge(g){
    if (!g.total || !validTotal(g.modelTotal)) return '—';
    const edge = Number(g.modelTotal) - Number(g.total.cur.value);
    if (Math.abs(edge) < 0.25) return 'No edge';
    return `${edge > 0 ? 'Over' : 'Under'} +${fmtNum(Math.abs(edge))}`;
  }

  window.__lh2Sort = window.__lh2Sort || {key:'count', dir:'desc'};

  function sortGames(games){
    const s = window.__lh2Sort || {key:'count', dir:'desc'};
    function v(g){
      if (s.key === 'week') return Number(g.week ?? 999);
      if (s.key === 'date') return String(g.gameDate || '');
      if (s.key === 'away') return norm(g.away);
      if (s.key === 'home') return norm(g.home);
      if (s.key === 'spreadMove') return Math.abs(g.spread?.move || 0);
      if (s.key === 'totalMove') return Math.abs(g.total?.move || 0);
      return Number(g.count || 0);
    }

    games.sort((a,b) => {
      const av = v(a), bv = v(b);
      let cmp = (typeof av === 'number' && typeof bv === 'number')
        ? av - bv
        : String(av).localeCompare(String(bv));
      if (s.dir === 'desc') cmp = -cmp;
      return cmp || String(a.gameDate || '').localeCompare(String(b.gameDate || '')) || norm(a.away).localeCompare(norm(b.away));
    });

    return games;
  }

  function detailTable(g, kind){
    const isSpread = kind === 'spread';
    const s = isSpread ? g.spread : g.total;

    if (!s || !s.arr.length) return `<div class="lh2-empty">No ${kind} history</div>`;

    const chronological = s.arr.slice().sort((a,b) => String(a.date).localeCompare(String(b.date)));
    const withMoves = chronological.map((r, i) => ({
      r,
      delta: i > 0 ? Number(r.value) - Number(chronological[i - 1].value) : 0
    })).sort((a,b) => String(b.r.date).localeCompare(String(a.r.date)));

    const rows = withMoves.map(({r, delta}) => {
      const line = isSpread ? spreadText(g.home, g.away, r.value) : fmtNum(r.value);
      const lineWithMove = `${esc(line)} ${detailMoveChip(delta)}`;
      const price = isSpread
        ? cleanPrice(r.spreadPrice ?? r.rawPrice)
        : (() => {
            const op = cleanPrice(r.overPrice);
            const up = cleanPrice(r.underPrice);
            return (op === '—' && up === '—') ? '—' : `O ${op} / U ${up}`;
          })();

      return `<tr>
        <td>${fmtDate(r.date)}</td>
        <td>${lineWithMove}</td>
        <td title="${esc(price)}">${esc(price)}</td>
        <td>${bookHtml(r.book)}</td>
      </tr>`;
    }).join('');

    return `<table class="lh2-detail-table">
      <thead><tr><th>Date</th><th>${isSpread ? 'Line' : 'Total'}</th><th>Price</th><th>Book</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  }

  function rowHtml(g){
    const sp = g.spread;
    const tt = g.total;

    const spMain = sp
      ? compactSpreadChange(g.home, g.away, sp.open.value, sp.cur.value)
      : 'No spread';

    const ttMain = tt
      ? `${fmtNum(tt.open.value)} → ${fmtNum(tt.cur.value)}`
      : 'No total';

    return `<article class="lh2-row"
      data-week="${g.week ?? ''}"
      data-conf="${esc(g.conference)}"
      data-away-conf="${esc(g.awayConf)}"
      data-home-conf="${esc(g.homeConf)}"
      data-search="${esc(g.search)}"
      data-snaps="${g.count}"
      data-has-spread="${sp ? '1' : '0'}"
      data-has-total="${tt ? '1' : '0'}">

      <div class="lh2-grid">
        <div class="lh2-week">W${g.week ?? '—'}</div>
        <div class="lh2-date">${fmtDate(g.gameDate)}</div>
        <div class="lh2-team-cell">${teamCell(g.away)}</div>
        <div class="lh2-team-cell">${teamCell(g.home)}</div>
        <div>
          <div class="lh2-main">${esc(spMain)} <span class="lh2-move ${moveClass(sp?.move)}">${sp ? moveLabel(sp.move) : '—'}</span></div>
          <div class="muted small">Model ${esc(spreadText(g.home, g.away, g.modelSpread))} · Edge ${esc(spreadEdge(g))}</div>
        </div>
        <div>
          <div class="lh2-main">${esc(ttMain)} <span class="lh2-move ${moveClass(tt?.move)}">${tt ? moveLabel(tt.move) : '—'}</span></div>
          <div class="muted small">Model ${fmtNum(g.modelTotal)} · Edge ${esc(totalEdge(g))}</div>
        </div>
        <button class="lh2-details-btn" type="button">Details</button>
      </div>

      <div class="lh2-detail" hidden>
        <div class="lh2-detail-cols">
          <section><h4>Spread history</h4>${detailTable(g, 'spread')}</section>
          <section><h4>Total history</h4>${detailTable(g, 'total')}</section>
        </div>
      </div>
    </article>`;
  }

  function currentFilteredGames(){
    const week = txt(document.getElementById('lh2Week')?.value || 'all');
    const q = norm(document.getElementById('lh2Team')?.value || '');

    return buildLineHistoryGames().filter(g => {
      let ok = true;
      if (week !== 'all') ok = ok && String(g.week ?? '') === week;
      if (q) ok = ok && g.search.includes(q);
      return ok;
    });
  }

  function renderLH2Rows(){
    const list = document.getElementById('lh2Rows');
    if (!list) return;
    const games = sortGames(currentFilteredGames());
    list.innerHTML = games.map(rowHtml).join('');
    document.getElementById('lh2Count').textContent = String(games.length);

    list.querySelectorAll('.lh2-details-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const row = btn.closest('.lh2-row');
        const detail = row.querySelector('.lh2-detail');
        const open = detail.hasAttribute('hidden');
        if (open) {
          detail.removeAttribute('hidden');
          btn.textContent = 'Hide';
        } else {
          detail.setAttribute('hidden', '');
          btn.textContent = 'Details';
        }
      });
    });
  }

  function renderLineHistoryStandalone(){
    const all = buildLineHistoryGames();
    const weeks = [...new Set(all.map(g => g.week).filter(x => x !== null && x !== undefined))].sort((a,b)=>a-b);
    const db = dbObj();
    const dbTeamConfs = db && Array.isArray(db.teams)
      ? db.teams.map(t => t.conference || t.conf).filter(Boolean)
      : [];
    const confs = [...new Set([...all.flatMap(g => [g.conference, g.awayConf, g.homeConf]), ...dbTeamConfs].filter(Boolean))].sort();

    return `<div class="page-title">Line History</div>
      <div class="page-sub">Selected market line by source/book priority. Current rows are SGO-first when available; older rows keep their historical source.</div>

      <div class="card">
        <div class="lh2-filters">
          <select id="lh2Week"><option value="all">All weeks</option>${weeks.map(w => `<option value="${w}">Week ${w}</option>`).join('')}</select>
          <input id="lh2Team" placeholder="Filter team">
          <select id="lh2MoveSort">
            <option value="count">Most history</option>
            <option value="spreadMove">Biggest spread move</option>
            <option value="totalMove">Biggest total move</option>
            <option value="date">Game date</option>
            <option value="away">Away A-Z</option>
            <option value="home">Home A-Z</option>
          </select>
          <span class="pill">Games <b id="lh2Count">${all.length}</b></span>
        </div>

        <div class="lh2-header">
          <button data-lh2-sort="week">Week</button>
          <button data-lh2-sort="date">Date</button>
          <button data-lh2-sort="away">Away</button>
          <button data-lh2-sort="home">Home</button>
          <button data-lh2-sort="spreadMove">Spread / Move</button>
          <button data-lh2-sort="totalMove">Total / Move</button>
          <span></span>
        </div>

        <div id="lh2Rows" class="lh2-list"></div>
      </div>`;
  }

  function bindLH2(){
    ['lh2Week','lh2Team','lh2MoveSort'].forEach(id => {
      const el = document.getElementById(id);
      if (!el || el.dataset.bound) return;
      el.dataset.bound = '1';
      el.addEventListener('input', () => {
        if (id === 'lh2MoveSort') {
          const key = el.value || 'count';
          window.__lh2Sort = {key, dir: key === 'away' || key === 'home' || key === 'date' ? 'asc' : 'desc'};
        }
        renderLH2Rows();
      });
      el.addEventListener('change', () => {
        if (id === 'lh2MoveSort') {
          const key = el.value || 'count';
          window.__lh2Sort = {key, dir: key === 'away' || key === 'home' || key === 'date' ? 'asc' : 'desc'};
        }
        renderLH2Rows();
      });
    });

    document.querySelectorAll('[data-lh2-sort]').forEach(btn => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', () => {
        const key = btn.dataset.lh2Sort;
        const cur = window.__lh2Sort || {key:'count', dir:'desc'};
        const dir = cur.key === key && cur.dir === 'asc' ? 'desc' : 'asc';
        window.__lh2Sort = {key, dir};
        renderLH2Rows();
      });
    });

    renderLH2Rows();
  }

  function installLineHistoryRoute(){
    if (typeof window.renderLineHistoryStandalone !== 'function') {
      window.renderLineHistoryStandalone = renderLineHistoryStandalone;
    }

    if (!window.__lh2HashHooked) {
      window.__lh2HashHooked = true;
      window.addEventListener('hashchange', () => {
        if (location.hash === '#line-history') {
          setTimeout(bindLH2, 50);
          setTimeout(bindLH2, 250);
        }
      });
    }

    setTimeout(() => {
      if (location.hash === '#line-history') bindLH2();
    }, 100);
  }

  installLineHistoryRoute();
})();
</script>

<style id="standalone-line-history-page-css">
.lh2-filters{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.lh2-filters select,.lh2-filters input{padding:9px 10px;border-radius:12px;border:1px solid var(--line);background:#fff;color:#111;min-width:150px}
.lh2-header{display:grid;grid-template-columns:56px 78px 1fr 1fr 1.05fr .75fr 82px;gap:6px;padding:0 9px 7px}
.lh2-header button{appearance:none;border:0;background:transparent;color:var(--muted);text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.08em;font-weight:950;cursor:pointer}
.lh2-header button:hover{color:#fff}
.lh2-list{display:grid;gap:8px}
.lh2-row{border:1px solid rgba(255,255,255,.12);border-radius:13px;background:rgba(255,255,255,.035);overflow:hidden}
.lh2-grid{display:grid;grid-template-columns:56px 78px 1fr 1fr 1.05fr .75fr 82px;gap:6px;align-items:center;padding:8px 9px}
.lh2-week,.lh2-date{font-weight:800;color:#dbeafe}
.lh2-team{display:inline-flex;gap:6px;align-items:center;font-weight:900}
.lh2-team .team-logo-wrap{width:24px!important;height:24px!important}
.lh2-team .team-logo{width:22px!important;height:22px!important}
.lh2-team-fallback{width:22px;height:22px;border-radius:6px;background:rgba(255,255,255,.12);display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:900}
.lh2-label{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:950}
.lh2-main{font-size:15px;font-weight:950;line-height:1.15}
.lh2-move{border-radius:999px;padding:2px 6px;margin-left:5px;font-size:11px;font-weight:950;border:1px solid rgba(255,255,255,.14);background:rgba(148,163,184,.14);white-space:nowrap}
.lh2-move.up{background:rgba(34,197,94,.16);border-color:rgba(34,197,94,.35)}
.lh2-move.down{background:rgba(248,113,113,.16);border-color:rgba(248,113,113,.35)}
.lh2-detail-move{display:inline-flex;margin-left:5px;border-radius:999px;padding:1px 5px;font-size:10px;font-weight:950;border:1px solid rgba(255,255,255,.14);background:rgba(148,163,184,.14);white-space:nowrap}
.lh2-detail-move.up{background:rgba(34,197,94,.16);border-color:rgba(34,197,94,.35)}
.lh2-detail-move.down{background:rgba(248,113,113,.16);border-color:rgba(248,113,113,.35)}
.lh2-details-btn{border:1px solid rgba(96,165,250,.35);background:rgba(96,165,250,.14);border-radius:999px;padding:6px 9px;font-size:12px;font-weight:900;color:var(--text);cursor:pointer}
.lh2-detail{border-top:1px solid rgba(255,255,255,.10);padding:8px;background:rgba(0,0,0,.12)}
.lh2-detail-cols{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px}
.lh2-detail-cols h4{margin:0 0 5px;font-size:14px}
.lh2-detail-table{width:100%;border-collapse:collapse;font-size:10.5px;table-layout:fixed}
.lh2-detail-table th,.lh2-detail-table td{border-bottom:1px solid rgba(255,255,255,.09);padding:4px 5px;text-align:left;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lh2-detail-table th{color:var(--muted);text-transform:uppercase;letter-spacing:.05em;font-size:10px}
.lh2-detail-table th:nth-child(1),.lh2-detail-table td:nth-child(1){width:62px}
.lh2-detail-table th:nth-child(2),.lh2-detail-table td:nth-child(2){width:150px}
.lh2-detail-table th:nth-child(3),.lh2-detail-table td:nth-child(3){width:132px}
.lh2-detail-table th:nth-child(4),.lh2-detail-table td:nth-child(4){width:70px}
.lh2-empty{color:var(--muted);padding:10px;border:1px dashed rgba(255,255,255,.15);border-radius:10px}
@media(max-width:1050px){
  .lh2-header{display:none}
  .lh2-grid{grid-template-columns:1fr}
  .lh2-detail-cols{grid-template-columns:1fr}
}
</style>
<!-- standalone-line-history-page-end -->
'''

def inject(path):
    if not path.exists():
        return
    html = path.read_text(errors="ignore")

    # Add nav button after Season Schedule if missing.
    html = html.replace(
        "navBtn('#schedule','Season Schedule'),\n    navBtn('#results-center','Results Center'),",
        "navBtn('#schedule','Season Schedule'),\n    navBtn('#line-history','Line History'),\n    navBtn('#results-center','Results Center'),"
    )

    # Add route before Results Center route.
    html = html.replace(
        "else if (hash==='#results-center') html = renderResultsCenter();",
        "else if (hash==='#line-history') html = renderLineHistoryStandalone();\n  else if (hash==='#results-center') html = renderResultsCenter();"
    )

    # Ensure bind runs after route render if app has generic render.
    html = html.replace(
        "document.getElementById('app').innerHTML = html;",
        "document.getElementById('app').innerHTML = html;\n  if (location.hash==='#line-history' && typeof bindLH2 === 'function') setTimeout(bindLH2, 50);"
    )

    if START in html and END in html:
        html = re.sub(re.escape(START) + r".*?" + re.escape(END), BLOCK, html, flags=re.S)
    else:
        html = html.replace("</body>", BLOCK + "\n</body>")

    path.write_text(html, encoding="utf-8")
    print(path, "injected standalone Line History page")

for p in TARGETS:
    inject(p)
