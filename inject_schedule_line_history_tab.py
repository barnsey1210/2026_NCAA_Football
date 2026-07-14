from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- schedule-line-history-tab-start -->"
END = "<!-- schedule-line-history-tab-end -->"

BLOCK = r'''
<!-- schedule-line-history-tab-start -->
<script id="schedule-line-history-tab-js">
(function(){
  if (window.__scheduleLineHistoryTabInstalledV3) return;
  window.__scheduleLineHistoryTabInstalledV3 = true;
  window.__lineHistoryActive = false;
  window.__lineHistorySort = window.__lineHistorySort || { key: 'snaps', dir: 'desc' };

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

  function moveClass(x){
    const n = nval(x);
    if (n === null || Math.abs(n) < 0.25) return 'flat';
    return n > 0 ? 'up' : 'down';
  }

  function moveLabel(x){
    const n = nval(x);
    if (n === null) return '—';
    if (Math.abs(n) < 0.25) return 'Flat';
    return n > 0 ? `Up ${fmtNum(Math.abs(n))}` : `Down ${fmtNum(Math.abs(n))}`;
  }

  function dbObj(){
    return window.DB || window.db || window.__DB || null;
  }

  function gameIndex(){
    const db = dbObj();
    const games = db && Array.isArray(db.games) ? db.games : [];
    const idx = {};
    games.forEach(g => { idx[String(g.game_id)] = g; });
    return idx;
  }

  function normTeamName(x){
    return String(x || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  }

  function teamIndex(){
    const db = dbObj();
    const teams = db && Array.isArray(db.teams) ? db.teams : [];
    const idx = {};
    teams.forEach(t => {
      const name = t.team || t.name || t.school || '';
      idx[String(name).toLowerCase()] = t;
      idx[normTeamName(name)] = t;
    });
    return idx;
  }

  function teamConference(team){
    const idx = teamIndex();
    const t = idx[String(team || '').toLowerCase()] || idx[normTeamName(team)] || {};
    return txt(t.conference || t.conf || t.league || '');
  }

  function teamLogo(team){
    const idx = teamIndex();
    const t = idx[String(team || '').toLowerCase()] || idx[normTeamName(team)] || {};
    const url =
      t.logo ||
      t.logo_url ||
      t.logoUrl ||
      t.team_logo ||
      t.teamLogo ||
      t.logo_href ||
      t.espn_logo ||
      t.logo_espn ||
      t.image ||
      t.image_url ||
      t.primary_logo ||
      t.logoDark ||
      t.logo_light;

    if (url) return `<img class="lh-team-logo" src="${url}" alt="">`;

    const letter = String(team || '?').trim().charAt(0).toUpperCase();
    return `<span class="lh-team-logo fallback">${letter}</span>`;
  }

  function bookBadge(book){
    const b = txt(book);
    if (!b) return '—';

    // Use existing site sportsbook logo functions if present.
    try {
      if (typeof window.bookLogoHtml === 'function') return window.bookLogoHtml(b);
      if (typeof window.sportsbookLogoHtml === 'function') return window.sportsbookLogoHtml(b);
      if (typeof window.renderBookLogo === 'function') return window.renderBookLogo(b);
    } catch(e) {}

    const key = norm(b).replace(/[^a-z0-9]/g,'');
    const short = {
      fanduel:'FD',
      draftkings:'DK',
      caesars:'CZR',
      betmgm:'MGM',
      bovada:'BOV',
      sportsbet:'SB',
      betonline:'BO',
      lowvig:'LV'
    }[key] || b;

    return `<span class="lh-book-badge" title="${b}">${short}</span>`;
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
    return {arr, open, cur, low, high, move: cur.value - open.value};
  }

  function lastValid(rows, key, validator){
    for (let i = (rows || []).length - 1; i >= 0; i--) {
      if (validator(rows[i][key])) return Number(rows[i][key]);
    }
    return null;
  }

  function buildGames(){
    const hist = window.MATCHUP_LINE_HISTORY || {};
    const dbGames = gameIndex();

    return Object.entries(hist).map(([gameId, raw]) => {
      const rows = (raw || []).slice().sort((a,b) => String(a.snapshot_date || '').localeCompare(String(b.snapshot_date || '')));
      const latest = rows[rows.length - 1] || {};
      const dbGame = dbGames[String(gameId)] || {};

      const away = latest.away_team || dbGame.away_team || '';
      const home = latest.home_team || dbGame.home_team || '';
      const week = nval(dbGame.week ?? latest.site_week ?? latest.week);
      const awayConf = txt(dbGame.away_conference || dbGame.awayConference || latest.away_conference || teamConference(away));
      const homeConf = txt(dbGame.home_conference || dbGame.homeConference || latest.home_conference || teamConference(home));
      const conference = txt(dbGame.conference || dbGame.conf || latest.conference || homeConf || awayConf);
      const gameDate = latest.game_date || dbGame.date || latest.date || '';

      const spread = stats(uniqueDaily(rows, 'spread'));
      const total = stats(uniqueDaily(rows, 'total'));
      const modelSpread = lastValid(rows, 'model_spread_home', validSpread);
      const modelTotal = lastValid(rows, 'projected_total', validTotal);

      const dates = [...new Set(rows.map(r => r.snapshot_date).filter(Boolean))].sort();

      return {
        gameId, rows, away, home, week, conference, awayConf, homeConf, gameDate,
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

  function detailTable(g, kind){
    const isSpread = kind === 'spread';
    const s = isSpread ? g.spread : g.total;

    if (!s || !s.arr.length) {
      return `<div class="line-detail-empty">No ${kind} history</div>`;
    }

    const rows = s.arr.slice().sort((a,b) => String(b.date).localeCompare(String(a.date))).map(r => {
      const line = isSpread ? spreadText(g.home, g.away, r.value) : fmtNum(r.value);
      const price = isSpread
        ? cleanPrice(r.spreadPrice ?? r.rawPrice)
        : (() => {
            const op = cleanPrice(r.overPrice);
            const up = cleanPrice(r.underPrice);
            return (op === '—' && up === '—') ? '—' : `O ${op} / U ${up}`;
          })();

      return `<tr>
        <td>${fmtDate(r.date)}</td>
        <td>${line}</td>
        <td>${price}</td>
        <td>${bookBadge(r.book)}</td>
        <td title="${r.source || 'History'}">${r.source || 'History'}</td>
      </tr>`;
    }).join('');

    return `<table class="line-detail-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>${isSpread ? 'Line' : 'Total'}</th>
          <th>Price</th>
          <th>Book</th>
          <th>Source</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
  }

  function rowHtml(g){
    const sp = g.spread;
    const tt = g.total;

    const spMain = sp
      ? `${spreadText(g.home, g.away, sp.open.value)} <span class="arrow">→</span> ${spreadText(g.home, g.away, sp.cur.value)}`
      : `<span class="muted">No spread</span>`;

    const ttMain = tt
      ? `${fmtNum(tt.open.value)} <span class="arrow">→</span> ${fmtNum(tt.cur.value)}`
      : `<span class="muted">No total</span>`;

    return `<article class="line-history-row"
      data-week="${g.week ?? ''}"
      data-conf="${g.conference}"
      data-away-conf="${g.awayConf || ''}"
      data-home-conf="${g.homeConf || ''}"
      data-away="${norm(g.away)}"
      data-home="${norm(g.home)}"
      data-search="${g.search}"
      data-snaps="${g.count}"
      data-spread-move="${sp ? sp.move : 0}"
      data-total-move="${tt ? tt.move : 0}"
      data-date="${g.gameDate || ''}"
      data-has-spread="${sp ? '1' : '0'}"
      data-has-total="${tt ? '1' : '0'}">

      <div class="line-summary-grid">
        <div class="line-game-cell">
          <div class="line-game-title">${teamLogo(g.away)} ${g.away} <span>at</span> ${teamLogo(g.home)} ${g.home}</div>
          <div class="muted small">W${g.week ?? '—'} · ${fmtDate(g.gameDate)} · ${g.count} snaps · ${fmtDate(g.firstDate)} → ${fmtDate(g.lastDate)}</div>
        </div>

        <div class="line-market-cell">
          <div class="line-label">Spread <span class="move-pill mini ${moveClass(sp?.move)}">${sp ? moveLabel(sp.move) : '—'}</span></div>
          <div class="line-main-text">${spMain}</div>
          <div class="muted small">Model ${spreadText(g.home, g.away, g.modelSpread)} · Edge ${spreadEdge(g)}</div>
        </div>

        <div class="line-market-cell">
          <div class="line-label">Total <span class="move-pill mini ${moveClass(tt?.move)}">${tt ? moveLabel(tt.move) : '—'}</span></div>
          <div class="line-main-text">${ttMain}</div>
          <div class="muted small">Model ${fmtNum(g.modelTotal)} · Edge ${totalEdge(g)}</div>
        </div>

        <button class="line-detail-btn" type="button">Details</button>
      </div>

      <div class="line-detail-panel" hidden>
        <div class="line-detail-two-col">
          <section>
            <h4>Spread history</h4>
            ${detailTable(g, 'spread')}
          </section>
          <section>
            <h4>Total history</h4>
            ${detailTable(g, 'total')}
          </section>
        </div>
      </div>
    </article>`;
  }

  function sortedGames(){
    const games = buildGames();

    const dropdownSort = document.getElementById('lineHistorySort')?.value || '';
    const headerSort = window.__lineHistorySort || {key:'snaps', dir:'desc'};

    let key = headerSort.key || 'snaps';
    let dir = headerSort.dir || 'desc';

    // Dropdown can override header sort.
    if (dropdownSort === 'away_az') { key = 'away'; dir = 'asc'; }
    if (dropdownSort === 'home_az') { key = 'home'; dir = 'asc'; }
    if (dropdownSort === 'date_asc') { key = 'date'; dir = 'asc'; }
    if (dropdownSort === 'date_desc') { key = 'date'; dir = 'desc'; }
    if (dropdownSort === 'spread_move') { key = 'spreadMove'; dir = 'desc'; }
    if (dropdownSort === 'total_move') { key = 'totalMove'; dir = 'desc'; }
    if (dropdownSort === 'snaps_desc') { key = 'snaps'; dir = 'desc'; }

    function val(g){
      if (key === 'week') return Number(g.week ?? 999);
      if (key === 'date') return String(g.gameDate || '');
      if (key === 'away') return norm(g.away);
      if (key === 'home') return norm(g.home);
      if (key === 'spread') return norm(g.spread ? spreadText(g.home, g.away, g.spread.cur.value) : '');
      if (key === 'spreadMove') return Math.abs(g.spread?.move || 0);
      if (key === 'total') return Number(g.total?.cur.value ?? -999);
      if (key === 'totalMove') return Math.abs(g.total?.move || 0);
      return Number(g.count || 0);
    }

    games.sort((a,b) => {
      const av = val(a), bv = val(b);
      let cmp = 0;
      if (typeof av === 'number' && typeof bv === 'number') cmp = av - bv;
      else cmp = String(av).localeCompare(String(bv));

      if (dir === 'desc') cmp = -cmp;
      return cmp || String(a.gameDate || '').localeCompare(String(b.gameDate || '')) || norm(a.away).localeCompare(norm(b.away));
    });

    return games;
  }

  function renderRows(){
    const list = document.querySelector('#scheduleLineHistoryPanel .line-history-list');
    if (!list) return;
    list.innerHTML = sortedGames().map(rowHtml).join('');
    bindDetails();
    bindHeaderSort();
    filterPanel();
  }

  function renderPanel(){
    const games = buildGames();
    const multi = games.filter(g => g.count > 1).length;

    return `<section id="scheduleLineHistoryPanel" class="schedule-line-history-panel">
      <div class="line-history-header">
        <div>
          <h3>Line History</h3>
          <div class="muted small">${multi} games with multi-snapshot history · selected market line by source/book priority · Details show newest first</div>
        </div>
        <div class="pill">Games ${games.length}</div>
      </div>

      <div class="schedule-line-history-tools">
        <input id="lineHistorySearch" placeholder="Filter team" />
        <select id="lineHistoryMinSnapshots">
          <option value="1">All games</option>
          <option value="2">2+ snapshots</option>
          <option value="5">5+ snapshots</option>
          <option value="10">10+ snapshots</option>
          <option value="30">30+ snapshots</option>
        </select>
        <select id="lineHistoryMarketFilter">
          <option value="all">Spread or total</option>
          <option value="spread">Has spread history</option>
          <option value="total">Has total history</option>
        </select>
        <select id="lineHistorySort">
          <option value="">Sort: Use headers</option>
          <option value="snaps_desc">Sort: Most history</option>
          <option value="date_asc">Sort: Game date ↑</option>
          <option value="date_desc">Sort: Game date ↓</option>
          <option value="away_az">Sort: Away A-Z</option>
          <option value="home_az">Sort: Home A-Z</option>
          <option value="spread_move">Sort: Biggest spread move</option>
          <option value="total_move">Sort: Biggest total move</option>
        </select>
      </div>

      <div class="line-history-header-row">
        <button data-lh-sort="week">Week</button>
        <button data-lh-sort="date">Date</button>
        <button data-lh-sort="away">Away</button>
        <button data-lh-sort="home">Home</button>
        <button data-lh-sort="spread">Spread</button>
        <button data-lh-sort="spreadMove">Spread move</button>
        <button data-lh-sort="total">Total</button>
        <button data-lh-sort="totalMove">Total move</button>
      </div>

      <div class="line-history-list">
        ${sortedGames().map(rowHtml).join('')}
      </div>
    </section>`;
  }

  function scheduleFilters(){
    const selects = [...document.querySelectorAll('select')].filter(s => !s.closest('#scheduleLineHistoryPanel'));

    let week = '';
    let conf = '';

    for (const sel of selects) {
      const labelRaw = txt(sel.options?.[sel.selectedIndex]?.textContent || sel.value);
      const label = norm(labelRaw);
      const val = txt(sel.value);

      if (label.includes('week')) week = labelRaw || val;
      if (label.includes('conference') || label.includes('all conferences')) conf = val || labelRaw;
    }

    const teamInput = [...document.querySelectorAll('input')].find(i => !i.closest('#scheduleLineHistoryPanel') && norm(i.placeholder).includes('filter team'));

    return { week, conf, team: norm(teamInput?.value || '') };
  }

  function filterPanel(){
    const panel = document.getElementById('scheduleLineHistoryPanel');
    if (!panel) return;

    const q = norm(document.getElementById('lineHistorySearch')?.value || '');
    const min = Number(document.getElementById('lineHistoryMinSnapshots')?.value || 1);
    const market = document.getElementById('lineHistoryMarketFilter')?.value || 'all';
    const sf = scheduleFilters();

    panel.querySelectorAll('.line-history-row').forEach(row => {
      const snaps = Number(row.dataset.snaps || 0);
      const hasSpread = row.dataset.hasSpread === '1';
      const hasTotal = row.dataset.hasTotal === '1';
      const search = row.dataset.search || '';

      let ok = snaps >= min;

      if (q) ok = ok && search.includes(q);
      if (sf.team) ok = ok && search.includes(sf.team);

      if (sf.week && !norm(sf.week).includes('all')) {
        const w = String(sf.week).replace(/[^0-9]/g, '');
        const rw = String(row.dataset.week || '').replace(/[^0-9]/g, '');
        if (w !== '') ok = ok && rw === w;
      }

      if (sf.conf && !norm(sf.conf).includes('all')) {
        const c = norm(sf.conf);
        ok = ok && (
          norm(row.dataset.conf) === c ||
          norm(row.dataset.awayConf) === c ||
          norm(row.dataset.homeConf) === c
        );
      }

      if (market === 'spread') ok = ok && hasSpread;
      if (market === 'total') ok = ok && hasTotal;

      row.style.display = ok ? '' : 'none';
    });
  }

  function bindDetails(){
    document.querySelectorAll('.line-detail-btn').forEach(btn => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', () => {
        const row = btn.closest('.line-history-row');
        const panel = row?.querySelector('.line-detail-panel');
        if (!panel) return;
        const opening = panel.hasAttribute('hidden');
        if (opening) {
          panel.removeAttribute('hidden');
          btn.textContent = 'Hide';
        } else {
          panel.setAttribute('hidden', '');
          btn.textContent = 'Details';
        }
      });
    });
  }

  function bindHeaderSort(){
    document.querySelectorAll('[data-lh-sort]').forEach(btn => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', () => {
        const key = btn.dataset.lhSort;
        const cur = window.__lineHistorySort || {key:'snaps', dir:'desc'};
        const nextDir = cur.key === key && cur.dir === 'asc' ? 'desc' : 'asc';
        window.__lineHistorySort = {key, dir: nextDir};

        const sort = document.getElementById('lineHistorySort');
        if (sort) sort.value = '';

        renderRows();
      });
    });
  }

  function bindPanel(){
    const panel = document.getElementById('scheduleLineHistoryPanel');
    if (!panel) return;

    ['lineHistorySearch','lineHistoryMinSnapshots','lineHistoryMarketFilter'].forEach(id => {
      const el = document.getElementById(id);
      if (el && !el.dataset.bound) {
        el.dataset.bound = '1';
        el.addEventListener('input', filterPanel);
        el.addEventListener('change', filterPanel);
      }
    });

    const sort = document.getElementById('lineHistorySort');
    if (sort && !sort.dataset.bound) {
      sort.dataset.bound = '1';
      sort.addEventListener('change', renderRows);
    }

    document.querySelectorAll('select,input').forEach(el => {
      if (el.closest('#scheduleLineHistoryPanel')) return;
      if (el.dataset.lineHistoryFilterBound) return;
      el.dataset.lineHistoryFilterBound = '1';
      el.addEventListener('change', () => {
        if (window.__lineHistoryActive) setTimeout(filterPanel, 80);
      });
      el.addEventListener('input', () => {
        if (window.__lineHistoryActive) setTimeout(filterPanel, 80);
      });
    });

    bindDetails();
    filterPanel();
  }

  function hideMainSchedule(){
    document.querySelectorAll('table').forEach(tbl => {
      if (tbl.closest('#scheduleLineHistoryPanel')) return;
      const t = norm(tbl.textContent);
      if (t.includes('market spread') || t.includes('ats edge') || (t.includes('away') && t.includes('home'))) {
        const wrap = tbl.closest('.card') || tbl.parentElement;
        if (wrap) wrap.style.display = 'none';
      }
    });
  }

  function showMainSchedule(){
    document.querySelectorAll('table').forEach(tbl => {
      if (tbl.closest('#scheduleLineHistoryPanel')) return;
      const wrap = tbl.closest('.card') || tbl.parentElement;
      if (wrap) wrap.style.display = '';
    });
  }

  function hideLineHistory(){
    window.__lineHistoryActive = false;
  window.__lineHistorySort = window.__lineHistorySort || { key: 'snaps', dir: 'desc' };
    const panel = document.getElementById('scheduleLineHistoryPanel');
    if (panel) panel.style.display = 'none';
    showMainSchedule();
  }

  function setActive(btn){
    document.querySelectorAll('[data-schedule-tab-button]').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
  }

  function showLineHistory(btn){
    window.__lineHistoryActive = true;

    const oldPanel = document.getElementById('scheduleLineHistoryPanel');
    if (oldPanel) oldPanel.remove();

    const anchor = [...document.querySelectorAll('input,select')].find(el => norm(el.placeholder).includes('filter team'))?.parentElement;
    const html = renderPanel();

    if (anchor) anchor.insertAdjacentHTML('afterend', html);
    else document.body.insertAdjacentHTML('beforeend', html);

    const panel = document.getElementById('scheduleLineHistoryPanel');
    if (panel) panel.style.display = '';

    hideMainSchedule();
    setActive(btn);
    bindPanel();
  }

  function ensureButton(){
    const buttons = [...document.querySelectorAll('button,a')];

    buttons.forEach(btn => {
      const t = norm(btn.textContent);
      if (t === 'simple' || t === 'odds compare') btn.style.display = 'none';
    });

    if (document.getElementById('btnScheduleLineHistory')) return;

    const marketLab = buttons.find(btn => norm(btn.textContent) === 'market lab');
    if (!marketLab) return;

    buttons.forEach(btn => {
      const t = norm(btn.textContent);
      if (['market lab','results','spreads','totals','moneyline'].includes(t)) {
        btn.setAttribute('data-schedule-tab-button', '1');
        if (!btn.dataset.lineHistoryResetBound) {
          btn.dataset.lineHistoryResetBound = '1';
          btn.addEventListener('click', () => {
            hideLineHistory();
            setActive(btn);
          }, true);
        }
      }
    });

    const btn = document.createElement('button');
    btn.id = 'btnScheduleLineHistory';
    btn.type = 'button';
    btn.textContent = 'Line History';
    btn.className = marketLab.className || '';
    btn.setAttribute('data-schedule-tab-button', '1');
    btn.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      showLineHistory(btn);
    });

    marketLab.insertAdjacentElement('afterend', btn);
  }

  function tick(){
    ensureButton();
    if (window.__lineHistoryActive) {
      const btn = document.getElementById('btnScheduleLineHistory');
      let panel = document.getElementById('scheduleLineHistoryPanel');
      if (!panel) showLineHistory(btn);
      else {
        panel.style.display = '';
        hideMainSchedule();
        setActive(btn);
        bindPanel();
      }
    } else {
      bindPanel();
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', tick);
  else tick();

  const obs = new MutationObserver(() => {
    clearTimeout(window.__scheduleLineHistoryTick);
    window.__scheduleLineHistoryTick = setTimeout(tick, 100);
  });
  obs.observe(document.documentElement, {childList:true, subtree:true});

  setTimeout(tick, 250);
  setTimeout(tick, 1000);
})();
</script>

<style id="schedule-line-history-tab-css">
#btnScheduleLineHistory { margin-left: 8px; }

.schedule-line-history-panel { margin-top: 14px; }

.line-history-header {
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  gap:10px;
  margin-bottom:10px;
}

.line-history-header h3 {
  margin:0 0 2px;
  font-size:22px;
}

.schedule-line-history-tools {
  display:flex;
  gap:8px;
  flex-wrap:wrap;
  margin: 8px 0 12px;
}

.schedule-line-history-tools input,
.schedule-line-history-tools select {
  border:1px solid var(--border, rgba(255,255,255,.18));
  border-radius:10px;
  padding:8px 10px;
  min-width:150px;
}

.line-history-header-row {
  display:grid;
  grid-template-columns:56px 76px 1fr 1fr 1fr 92px .8fr 86px;
  gap:6px;
  align-items:center;
  padding:0 9px 6px;
  color:var(--muted, #aab2c5);
}

.line-history-header-row button {
  appearance:none;
  border:0;
  background:transparent;
  color:inherit;
  text-align:left;
  font-size:11px;
  text-transform:uppercase;
  letter-spacing:.08em;
  font-weight:900;
  cursor:pointer;
  padding:2px 0;
}

.line-history-header-row button:hover {
  color:#fff;
}

.line-history-list { display:grid; gap:8px; }

.line-history-row {
  border:1px solid rgba(255,255,255,.12);
  border-radius:13px;
  background:rgba(255,255,255,.035);
  overflow:hidden;
}

.line-summary-grid {
  display:grid;
  grid-template-columns:minmax(230px, 1.15fr) minmax(245px, 1fr) minmax(185px, .75fr) 72px;
  gap:6px;
  align-items:center;
  padding:8px 9px;
}

.line-game-title {
  font-size:15px;
  font-weight:900;
  line-height:1.15;
  display:flex;
  align-items:center;
  gap:5px;
  flex-wrap:wrap;
}

.line-game-title span {
  color:var(--muted, #aab2c5);
  font-weight:600;
}

.lh-team-logo {
  width:20px;
  height:20px;
  object-fit:contain;
  border-radius:4px;
  vertical-align:middle;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  background:rgba(255,255,255,.08);
  font-size:11px;
  font-weight:900;
}

.lh-book-badge {
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-width:32px;
  max-width:58px;
  height:22px;
  border-radius:7px;
  padding:0 5px;
  background:rgba(255,255,255,.08);
  border:1px solid rgba(255,255,255,.12);
  font-size:10px;
  font-weight:900;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}

.line-label {
  font-size:10.5px;
  text-transform:uppercase;
  letter-spacing:.08em;
  color:var(--muted, #aab2c5);
  font-weight:900;
  margin-bottom:1px;
}

.line-main-text {
  font-size:15px;
  font-weight:900;
  line-height:1.15;
}

.arrow { color:var(--muted, #aab2c5); padding:0 3px; }

.move-pill {
  border-radius:999px;
  padding:5px 8px;
  font-size:11px;
  font-weight:900;
  white-space:nowrap;
  display:inline-block;
  text-align:center;
  border:1px solid rgba(255,255,255,.14);
  background:rgba(148,163,184,.14);
}

.move-pill.flat { background:rgba(148,163,184,.14); }
.move-pill.up { background:rgba(34,197,94,.16); border-color:rgba(34,197,94,.35); }
.move-pill.down { background:rgba(248,113,113,.16); border-color:rgba(248,113,113,.35); }

.move-pill.mini { margin-left:5px; padding:2px 6px; font-size:10px; }

.line-detail-btn {
  border:1px solid rgba(96,165,250,.35);
  background:rgba(96,165,250,.14);
  border-radius:999px;
  padding:6px 9px;
  font-size:12px;
  font-weight:900;
  cursor:pointer;
}

.line-detail-panel {
  border-top:1px solid rgba(255,255,255,.10);
  padding:8px;
  background:rgba(0,0,0,.12);
}

.line-detail-two-col {
  display:grid;
  grid-template-columns:minmax(0, 1fr) minmax(0, 1fr);
  gap:8px;
}

.line-detail-two-col h4 { margin:0 0 5px; font-size:14px; }

.line-detail-table {
  width:100%;
  border-collapse:collapse;
  font-size:10.5px;
  table-layout:fixed;
}

.line-detail-table th,
.line-detail-table td {
  border-bottom:1px solid rgba(255,255,255,.09);
  padding:4px 5px;
  text-align:left;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}

.line-detail-table th {
  color:var(--muted, #aab2c5);
  text-transform:uppercase;
  letter-spacing:.05em;
  font-size:10px;
}

.line-detail-table th:nth-child(1), .line-detail-table td:nth-child(1) { width:54px; }
.line-detail-table th:nth-child(2), .line-detail-table td:nth-child(2) { width:98px; }
.line-detail-table th:nth-child(3), .line-detail-table td:nth-child(3) { width:118px; }
.line-detail-table th:nth-child(4), .line-detail-table td:nth-child(4) { width:58px; }
.line-detail-table th:nth-child(5), .line-detail-table td:nth-child(5) { width:104px; }

.line-detail-empty {
  color:var(--muted, #aab2c5);
  padding:10px;
  border:1px dashed rgba(255,255,255,.15);
  border-radius:10px;
}

@media (max-width: 1050px) {
  .line-summary-grid { grid-template-columns:1fr; align-items:start; }
  .line-detail-two-col { grid-template-columns:1fr; }
}
</style>
<!-- schedule-line-history-tab-end -->
'''

def inject(path):
    if not path.exists():
        return
    html = path.read_text(errors="ignore")
    if START in html and END in html:
        html = re.sub(re.escape(START) + r".*?" + re.escape(END), BLOCK, html, flags=re.S)
    else:
        html = html.replace("</body>", BLOCK + "\n</body>")
    path.write_text(html, encoding="utf-8")
    print(path, "injected V3 line history tab")

for p in TARGETS:
    inject(p)
