from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- schedule-line-history-tab-start -->"
END = "<!-- schedule-line-history-tab-end -->"

BLOCK = r'''
<!-- schedule-line-history-tab-start -->
<script id="schedule-line-history-tab-js">
(function(){
  if (window.__scheduleLineHistoryTabInstalled) return;
  window.__scheduleLineHistoryTabInstalled = true;

  function normText(x){ return String(x || '').trim().toLowerCase(); }

  function validSpread(v){
    const n = Number(v);
    return Number.isFinite(n) && Math.abs(n) <= 80;
  }

  function validTotal(v){
    const n = Number(v);
    return Number.isFinite(n) && n >= 20 && n <= 100;
  }

  function fmtNum(v){
    const n = Number(v);
    if (!Number.isFinite(n)) return '—';
    return n.toFixed(1).replace(/\.0$/, '');
  }

  function fmtSigned(v){
    const n = Number(v);
    if (!Number.isFinite(n)) return '—';
    if (Math.abs(n) < 0.05) return '0';
    return (n > 0 ? '+' : '') + fmtNum(n);
  }

  function fmtDate(v){
    if (!v) return '—';
    const d = new Date(String(v) + 'T00:00:00');
    if (Number.isNaN(d.getTime())) return String(v);
    return d.toLocaleDateString(undefined, {month:'short', day:'numeric'});
  }

  function spreadText(home, away, spreadHome){
    const n = Number(spreadHome);
    if (!Number.isFinite(n)) return '—';
    if (Math.abs(n) < 0.05) return 'Pick';
    if (n < 0) return `${home} ${fmtNum(n)}`;
    return `${away} +${fmtNum(n)}`;
  }

  function valueRows(rows, key, validator){
    return (rows || [])
      .filter(r => validator(r[key]))
      .map(r => ({
        date: r.snapshot_date,
        value: Number(r[key]),
        price: key.includes('total')
          ? (r.market_total_over_price ?? r.market_total_under_price ?? null)
          : (r.market_spread_price ?? null),
        book: key.includes('total') ? (r.market_total_book || '') : (r.market_spread_book || ''),
        source: r.source || r.market_line_source || ''
      }))
      .sort((a,b) => String(a.date || '').localeCompare(String(b.date || '')));
  }

  function compressDaily(arr){
    const byDate = new Map();
    for (const r of arr || []) byDate.set(r.date || '', r);
    return [...byDate.values()].sort((a,b) => String(a.date || '').localeCompare(String(b.date || '')));
  }

  function stats(arr){
    arr = compressDaily(arr);
    if (!arr.length) return null;
    const open = arr[0];
    const cur = arr[arr.length - 1];
    const low = arr.reduce((a,b) => b.value < a.value ? b : a, arr[0]);
    const high = arr.reduce((a,b) => b.value > a.value ? b : a, arr[0]);
    return { arr, open, cur, low, high, move: cur.value - open.value };
  }

  function moveClass(move){
    const n = Number(move);
    if (!Number.isFinite(n) || Math.abs(n) < 0.25) return 'flat';
    return n > 0 ? 'up' : 'down';
  }

  function moveLabel(move){
    const cls = moveClass(move);
    if (cls === 'flat') return 'Flat';
    return cls === 'up' ? `Up ${fmtNum(Math.abs(move))}` : `Down ${fmtNum(Math.abs(move))}`;
  }

  function edgeSpread(modelSpreadHome, curSpreadHome, home, away){
    if (!validSpread(modelSpreadHome) || !validSpread(curSpreadHome)) return '—';
    const edge = Number(modelSpreadHome) - Number(curSpreadHome);
    if (Math.abs(edge) < 0.25) return 'No edge';
    const side = edge > 0 ? home : away;
    return `${side} +${fmtNum(Math.abs(edge))}`;
  }

  function edgeTotal(modelTotal, curTotal){
    if (!validTotal(modelTotal) || !validTotal(curTotal)) return '—';
    const edge = Number(modelTotal) - Number(curTotal);
    if (Math.abs(edge) < 0.25) return 'No edge';
    return `${edge > 0 ? 'Over' : 'Under'} +${fmtNum(Math.abs(edge))}`;
  }

  function lastModel(rows, key, validator){
    for (let i = (rows || []).length - 1; i >= 0; i--){
      if (validator(rows[i][key])) return Number(rows[i][key]);
    }
    return null;
  }

  function buildGames(){
    const hist = window.MATCHUP_LINE_HISTORY || {};
    const games = [];

    Object.entries(hist).forEach(([gameId, rawRows]) => {
      rawRows = (rawRows || []).slice().sort((a,b) => String(a.snapshot_date || '').localeCompare(String(b.snapshot_date || '')));
      const latest = rawRows[rawRows.length - 1] || {};
      const away = latest.away_team || '';
      const home = latest.home_team || '';
      const gameDate = latest.game_date || latest.date || '';

      const spread = stats(valueRows(rawRows, 'market_spread_home', validSpread));
      const total = stats(valueRows(rawRows, 'market_total', validTotal));

      const modelSpread = lastModel(rawRows, 'model_spread_home', validSpread);
      const modelTotal = lastModel(rawRows, 'projected_total', validTotal);

      const allDates = [...new Set(rawRows.map(r => r.snapshot_date).filter(Boolean))].sort();

      games.push({
        gameId, rawRows, away, home, gameDate,
        count: allDates.length,
        firstDate: allDates[0] || '',
        lastDate: allDates[allDates.length - 1] || '',
        spread, total, modelSpread, modelTotal,
        search: normText(`${away} ${home}`)
      });
    });

    games.sort((a,b) => {
      if (b.count !== a.count) return b.count - a.count;
      return String(a.gameDate).localeCompare(String(b.gameDate));
    });

    return games;
  }

  function detailTable(g, type){
    const isSpread = type === 'spread';
    const s = isSpread ? g.spread : g.total;
    if (!s || !s.arr.length) return `<div class="line-detail-empty">No ${type} history</div>`;

    const rows = s.arr.map(r => {
      const val = isSpread ? spreadText(g.home, g.away, r.value) : fmtNum(r.value);
      const price = Number.isFinite(Number(r.price)) ? Number(r.price).toFixed(0) : '—';
      return `<tr>
        <td>${fmtDate(r.date)}</td>
        <td>${val}</td>
        <td>${price}</td>
        <td>${r.book || '—'}</td>
        <td>${r.source || '—'}</td>
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

  function gameRow(g){
    const sp = g.spread;
    const tot = g.total;

    const spreadSummary = sp
      ? `<strong>${spreadText(g.home, g.away, sp.open.value)}</strong> <span class="arrow">→</span> <strong>${spreadText(g.home, g.away, sp.cur.value)}</strong>`
      : `<span class="muted">No spread</span>`;

    const totalSummary = tot
      ? `<strong>${fmtNum(tot.open.value)}</strong> <span class="arrow">→</span> <strong>${fmtNum(tot.cur.value)}</strong>`
      : `<span class="muted">No total</span>`;

    const spreadMove = sp ? sp.move : null;
    const totalMove = tot ? tot.move : null;

    return `<article class="line-history-row" data-snaps="${g.count}" data-search="${g.search}">
      <div class="line-summary-grid">
        <div class="line-game-cell">
          <div class="line-game-title">${g.away} <span>at</span> ${g.home}</div>
          <div class="muted small">${fmtDate(g.gameDate)} · ${g.count} snapshots · ${fmtDate(g.firstDate)} → ${fmtDate(g.lastDate)}</div>
        </div>

        <div class="line-market-cell">
          <div class="line-label">Spread</div>
          <div>${spreadSummary}</div>
          <div class="muted small">Model ${spreadText(g.home, g.away, g.modelSpread)} · Edge ${sp ? edgeSpread(g.modelSpread, sp.cur.value, g.home, g.away) : '—'}</div>
        </div>

        <div class="line-move-cell">
          <span class="move-pill ${moveClass(spreadMove)}">${sp ? moveLabel(spreadMove) : '—'}</span>
        </div>

        <div class="line-market-cell">
          <div class="line-label">Total</div>
          <div>${totalSummary}</div>
          <div class="muted small">Model ${fmtNum(g.modelTotal)} · Edge ${tot ? edgeTotal(g.modelTotal, tot.cur.value) : '—'}</div>
        </div>

        <div class="line-move-cell">
          <span class="move-pill ${moveClass(totalMove)}">${tot ? moveLabel(totalMove) : '—'}</span>
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

  function renderPanel(){
    const games = buildGames();
    const multi = games.filter(g => g.count > 1).length;

    return `<section id="scheduleLineHistoryPanel" class="schedule-line-history-panel">
      <div class="line-history-header">
        <div>
          <h3>Line History</h3>
          <div class="muted small">${multi} games with multi-snapshot history · click Details for daily line table</div>
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
      </div>

      <div class="line-history-list">
        ${games.map(gameRow).join('')}
      </div>
    </section>`;
  }

  function filterPanel(){
    const panel = document.getElementById('scheduleLineHistoryPanel');
    if (!panel) return;

    const q = normText(document.getElementById('lineHistorySearch')?.value || '');
    const min = Number(document.getElementById('lineHistoryMinSnapshots')?.value || 1);
    const market = document.getElementById('lineHistoryMarketFilter')?.value || 'all';

    panel.querySelectorAll('.line-history-row').forEach(row => {
      const snaps = Number(row.getAttribute('data-snaps') || 0);
      const txt = row.getAttribute('data-search') || '';
      const hasSpread = !row.textContent.includes('No spread');
      const hasTotal = !row.textContent.includes('No total');

      let ok = snaps >= min && (!q || txt.includes(q));
      if (market === 'spread') ok = ok && hasSpread;
      if (market === 'total') ok = ok && hasTotal;

      row.style.display = ok ? '' : 'none';
    });
  }

  function bindPanel(){
    document.getElementById('lineHistorySearch')?.addEventListener('input', filterPanel);
    document.getElementById('lineHistoryMinSnapshots')?.addEventListener('change', filterPanel);
    document.getElementById('lineHistoryMarketFilter')?.addEventListener('change', filterPanel);

    document.querySelectorAll('.line-detail-btn').forEach(btn => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', () => {
        const row = btn.closest('.line-history-row');
        const panel = row?.querySelector('.line-detail-panel');
        if (!panel) return;
        const isHidden = panel.hasAttribute('hidden');
        if (isHidden) {
          panel.removeAttribute('hidden');
          btn.textContent = 'Hide details';
        } else {
          panel.setAttribute('hidden', '');
          btn.textContent = 'Details';
        }
      });
    });
  }

  function hideMainSchedule(){
    document.querySelectorAll('table').forEach(tbl => {
      if (tbl.closest('#scheduleLineHistoryPanel')) return;
      const txt = normText(tbl.textContent);
      if (txt.includes('market spread') || txt.includes('ats edge') || (txt.includes('away') && txt.includes('home'))) {
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
    const panel = document.getElementById('scheduleLineHistoryPanel');
    if (panel) panel.style.display = 'none';
    showMainSchedule();
  }

  function setActive(btn){
    document.querySelectorAll('[data-schedule-tab-button]').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
  }

  function showLineHistory(btn){
    let panel = document.getElementById('scheduleLineHistoryPanel');
    if (!panel) {
      const filters = [...document.querySelectorAll('select,input')].find(el => {
        return normText(el.getAttribute('placeholder')).includes('filter team');
      });
      const anchor = filters ? (filters.closest('.card') || filters.parentElement) : null;
      const html = renderPanel();
      if (anchor) anchor.insertAdjacentHTML('afterend', html);
      else document.body.insertAdjacentHTML('beforeend', html);
      bindPanel();
    }

    panel = document.getElementById('scheduleLineHistoryPanel');
    if (panel) panel.style.display = '';
    hideMainSchedule();
    setActive(btn);
  }

  function ensureButton(){
    const buttons = [...document.querySelectorAll('button,a')];

    buttons.forEach(btn => {
      const t = normText(btn.textContent);
      if (t === 'simple' || t === 'odds compare') {
        btn.style.display = 'none';
      }
    });

    if (document.getElementById('btnScheduleLineHistory')) return;

    const marketLab = buttons.find(btn => normText(btn.textContent) === 'market lab');
    if (!marketLab) return;

    buttons.forEach(btn => {
      const t = normText(btn.textContent);
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
    btn.addEventListener('click', function(e){
      e.preventDefault();
      e.stopPropagation();
      showLineHistory(btn);
    });

    marketLab.insertAdjacentElement('afterend', btn);
  }

  function scheduleEnsure(){
    ensureButton();
    setTimeout(ensureButton, 50);
    setTimeout(ensureButton, 250);
    setTimeout(ensureButton, 750);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scheduleEnsure);
  } else {
    scheduleEnsure();
  }

  const obs = new MutationObserver(() => scheduleEnsure());
  obs.observe(document.documentElement, {childList:true, subtree:true});
})();
</script>

<style id="schedule-line-history-tab-css">
button:is(:not(#btnScheduleLineHistory)) {
}

#btnScheduleLineHistory { margin-left: 8px; }

.schedule-line-history-panel {
  margin-top: 16px;
}

.line-history-header {
  display:flex;
  justify-content:space-between;
  align-items:flex-start;
  gap:12px;
  margin-bottom:12px;
}

.line-history-header h3 {
  margin:0 0 4px;
  font-size:24px;
}

.schedule-line-history-tools {
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  margin: 10px 0 14px;
}

.schedule-line-history-tools input,
.schedule-line-history-tools select {
  border:1px solid var(--border, rgba(255,255,255,.18));
  border-radius:10px;
  padding:9px 11px;
  min-width:160px;
}

.line-history-list {
  display:grid;
  grid-template-columns:1fr;
  gap:10px;
}

.line-history-row {
  border:1px solid rgba(255,255,255,.12);
  border-radius:14px;
  background:rgba(255,255,255,.035);
  overflow:hidden;
}

.line-summary-grid {
  display:grid;
  grid-template-columns: minmax(260px, 1.4fr) minmax(220px, 1fr) 90px minmax(190px, .9fr) 90px 110px;
  gap:12px;
  align-items:center;
  padding:12px 14px;
}

.line-game-title {
  font-size:17px;
  font-weight:900;
}

.line-game-title span {
  color:var(--muted, #aab2c5);
  font-weight:600;
}

.line-label {
  font-size:11px;
  text-transform:uppercase;
  letter-spacing:.08em;
  color:var(--muted, #aab2c5);
  font-weight:900;
  margin-bottom:2px;
}

.arrow {
  color:var(--muted, #aab2c5);
  padding:0 4px;
}

.move-pill {
  border-radius:999px;
  padding:6px 9px;
  font-size:12px;
  font-weight:900;
  white-space:nowrap;
  display:inline-block;
  text-align:center;
  min-width:66px;
  border:1px solid rgba(255,255,255,.14);
}

.move-pill.flat { background:rgba(148,163,184,.14); }
.move-pill.up { background:rgba(34,197,94,.16); border-color:rgba(34,197,94,.35); }
.move-pill.down { background:rgba(248,113,113,.16); border-color:rgba(248,113,113,.35); }

.line-detail-btn {
  border:1px solid rgba(96,165,250,.35);
  background:rgba(96,165,250,.14);
  border-radius:999px;
  padding:8px 12px;
  font-weight:900;
  cursor:pointer;
}

.line-detail-panel {
  border-top:1px solid rgba(255,255,255,.10);
  padding:12px 14px 14px;
  background:rgba(0,0,0,.12);
}

.line-detail-two-col {
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:14px;
}

.line-detail-two-col h4 {
  margin:0 0 8px;
  font-size:15px;
}

.line-detail-table {
  width:100%;
  border-collapse:collapse;
  font-size:13px;
}

.line-detail-table th,
.line-detail-table td {
  border-bottom:1px solid rgba(255,255,255,.09);
  padding:7px 8px;
  text-align:left;
}

.line-detail-table th {
  color:var(--muted, #aab2c5);
  text-transform:uppercase;
  letter-spacing:.06em;
  font-size:11px;
}

.line-detail-empty {
  color:var(--muted, #aab2c5);
  padding:12px;
  border:1px dashed rgba(255,255,255,.15);
  border-radius:10px;
}

@media (max-width: 1200px) {
  .line-summary-grid {
    grid-template-columns:1fr;
    align-items:start;
  }
  .line-detail-two-col {
    grid-template-columns:1fr;
  }
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
    print(path, "injected compact expandable schedule line history tab")

for p in TARGETS:
    inject(p)
