from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- safe-simulations-page-start -->"
END = "<!-- safe-simulations-page-end -->"

BLOCK = r'''
<!-- safe-simulations-page-start -->
<script id="safe-simulations-page-js">
(function(){
  if (window.__safeSimulationsPageInstalled) return;
  window.__safeSimulationsPageInstalled = true;

  window.__simBoardSort = window.__simBoardSort || {key:'conf_title', dir:'desc'};

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
    if (typeof fmtPct === 'function') return fmtPct(x);
    return (x <= 1 ? x * 100 : x).toFixed(1).replace(/\.0$/,'') + '%';
  }

  function probNumber(v){
    const x = n(v);
    if (x == null) return null;
    return x <= 1 ? x : x / 100;
  }

  function americanFromProb(p){
    const x = probNumber(p);
    if (x == null || x <= 0 || x >= 1) return '—';
    if (x >= 0.5) return '-' + Math.round((x / (1 - x)) * 100);
    return '+' + Math.round(((1 - x) / x) * 100);
  }

  function delta(cur, pre, d=2){
    const c = n(cur), p = n(pre);
    if (c == null || p == null) return {txt:'—', val:null, cls:''};
    const x = c - p;
    if (Math.abs(x) < 0.005) return {txt:'—', val:0, cls:''};
    return {txt:(x > 0 ? '+' : '') + x.toFixed(d).replace(/\.00$/,'').replace(/\.0$/,''), val:x, cls:x > 0 ? 'pos' : 'neg'};
  }

  function pctDelta(cur, pre){
    const c = probNumber(cur), p = probNumber(pre);
    if (c == null || p == null) return {txt:'—', val:null, cls:''};
    const x = (c - p) * 100;
    if (Math.abs(x) < 0.05) return {txt:'—', val:0, cls:''};
    return {txt:(x > 0 ? '+' : '') + x.toFixed(1).replace(/\.0$/,'') + ' pts', val:x, cls:x > 0 ? 'pos' : 'neg'};
  }

  function teamLinkSafe(team){
    try { if (typeof linkTeam === 'function') return linkTeam(team); } catch(e) {}
    return esc(team);
  }

  function currentRecord(team){
    try {
      const s = (getResultsSummary().teamStats || {})[team] || {};
      return `${s.wins || 0}-${s.losses || 0}`;
    } catch(e) {
      return '0-0';
    }
  }

  function preseasonForTeam(team){
    try {
      if (typeof preseasonTeam === 'function') return preseasonTeam(team);
    } catch(e) {}
    return null;
  }

  function bestWinTotalMarket(team){
    const rows = DB.market_win_totals_edges || DB.market_win_totals_raw || [];
    const r = rows.find(x => String(x.team) === String(team));
    if (!r) return {};
    return {
      total: r.market_total ?? r.win_total ?? r.best_win_total ?? r.current_win_total,
      edge: r.win_edge ?? r.edge ?? r.over_edge,
      overOdds: r.best_over_odds ?? r.over_odds,
      underOdds: r.best_under_odds ?? r.under_odds,
      book: r.best_over_book || r.best_under_book || r.book
    };
  }

  function bestConfTitleMarket(team){
    const rows = DB.market_futures_edges || DB.market_conference_futures_edges || DB.market_conference_futures_raw || [];
    const r = rows.find(x => String(x.team) === String(team));
    if (!r) return {};
    const odds = r.best_title_odds ?? r.american_odds ?? r.current_american_odds;
    let implied = null;
    const o = n(odds);
    if (o != null && o !== 0) implied = o > 0 ? 100 / (o + 100) : Math.abs(o) / (Math.abs(o) + 100);
    return {
      odds,
      implied,
      book: r.best_title_book || r.book,
      edge: r.title_edge ?? r.edge
    };
  }

  function simRows(){
    return (DB.teams || []).map(t => {
      const pre = preseasonForTeam(t.team) || {};
      const winDelta = delta(t.avg_total_wins, pre.avg_total_wins, 2);
      const confWinDelta = delta(t.avg_conference_wins, pre.avg_conference_wins, 2);
      const titleDelta = pctDelta(t.conference_title_pct, pre.conference_title_pct);
      const makeTitleDelta = pctDelta(t.make_title_game_pct, pre.make_title_game_pct);
      const winMarket = bestWinTotalMarket(t.team);
      const confMarket = bestConfTitleMarket(t.team);

      const confTitleProb = probNumber(t.conference_title_pct);
      const confMarketProb = probNumber(confMarket.implied);
      const confEdge = confTitleProb != null && confMarketProb != null ? confTitleProb - confMarketProb : null;

      // Placeholders until CFP/national-title market feeds are wired.
      const playoffMarketProb = probNumber(t.playoff_market_implied ?? t.cfp_market_implied);
      const natTitleMarketProb = probNumber(t.national_title_market_implied ?? t.natty_market_implied);
      const playoffProb = probNumber(t.playoff_pct ?? t.cfp_pct);
      const natTitleProb = probNumber(t.national_title_pct ?? t.natty_pct);
      const playoffEdge = playoffProb != null && playoffMarketProb != null ? playoffProb - playoffMarketProb : null;
      const natTitleEdge = natTitleProb != null && natTitleMarketProb != null ? natTitleProb - natTitleMarketProb : null;

      const wt = n(winMarket.total);
      const wtEdge = wt != null && n(t.avg_total_wins) != null ? n(t.avg_total_wins) - wt : null;

      return {
        team: t.team,
        conf: t.conference,
        actual: currentRecord(t.team),
        avg_wins: n(t.avg_total_wins),
        pre_wins: n(pre.avg_total_wins),
        win_delta: winDelta,
        conf_wins: n(t.avg_conference_wins),
        pre_conf_wins: n(pre.avg_conference_wins),
        conf_win_delta: confWinDelta,
        conf_title: probNumber(t.conference_title_pct),
        pre_conf_title: probNumber(pre.conference_title_pct),
        conf_title_delta: titleDelta,
        make_title: probNumber(t.make_title_game_pct),
        make_title_delta: makeTitleDelta,
        playoff: probNumber(t.playoff_pct ?? t.cfp_pct),
        nat_title: probNumber(t.national_title_pct ?? t.natty_pct),
        win_market: winMarket,
        conf_market: confMarket,
        conf_edge: confEdge
      };
    });
  }

  function sortVal(r, key){
    if (key === 'team') return String(r.team || '').toLowerCase();
    if (key === 'conf') return String(r.conf || '').toLowerCase();
    if (key === 'actual') {
      const m = String(r.actual || '0-0').match(/(\d+)-(\d+)/);
      return m ? Number(m[1]) - Number(m[2]) + Number(m[1]) / 100 : 0;
    }
    if (key === 'wins') return r.avg_wins ?? -999;
    if (key === 'win_delta') return r.win_delta.val ?? -999;
    if (key === 'conf_wins') return r.conf_wins ?? -999;
    if (key === 'conf_win_delta') return r.conf_win_delta.val ?? -999;
    if (key === 'conf_title') return r.conf_title ?? -999;
    if (key === 'conf_title_delta') return r.conf_title_delta.val ?? -999;
    if (key === 'make_title') return r.make_title ?? -999;
    if (key === 'playoff') return r.playoff ?? -999;
    if (key === 'playoff_edge') return r.playoff_edge ?? -999;
    if (key === 'nat_title') return r.nat_title ?? -999;
    if (key === 'nat_title_edge') return r.nat_title_edge ?? -999;
    if (key === 'win_total') return n(r.win_market.total) ?? -999;
    if (key === 'win_edge') return r.win_edge ?? -999;
    if (key === 'conf_market') return probNumber(r.conf_market.implied) ?? -999;
    if (key === 'conf_edge') return r.conf_edge ?? -999;
    return 0;
  }

  function sortRows(rows){
    const s = window.__simBoardSort || {key:'conf_title', dir:'desc'};
    const mult = s.dir === 'asc' ? 1 : -1;
    return rows.sort((a,b) => {
      const av = sortVal(a, s.key), bv = sortVal(b, s.key);
      if (typeof av === 'string' || typeof bv === 'string') return String(av).localeCompare(String(bv)) * mult;
      return ((av || 0) - (bv || 0)) * mult;
    });
  }

  function th(key, label){
    const s = window.__simBoardSort || {};
    const arrow = s.key === key ? (s.dir === 'asc' ? '▲' : '▼') : '';
    return `<th class="sortable" onclick="setSimBoardSort('${key}')">${label}<span class="sort-arrow">${arrow}</span></th>`;
  }

  window.setSimBoardSort = function(key){
    const cur = window.__simBoardSort || {key:'conf_title', dir:'desc'};
    window.__simBoardSort = {key, dir: cur.key === key && cur.dir === 'desc' ? 'asc' : 'desc'};
    const wrap = document.getElementById('simBoardWrap');
    if (wrap) wrap.innerHTML = simBoardTable();
  };

  function simBoardTable(){
    const conf = document.getElementById('simConfFilter')?.value || 'all';
    const q = String(document.getElementById('simTeamFilter')?.value || '').trim().toLowerCase();

    let rows = simRows();
    if (conf !== 'all') rows = rows.filter(r => String(r.conf) === String(conf));
    if (q) rows = rows.filter(r => String(r.team).toLowerCase().includes(q));

    rows = sortRows(rows);

    const body = rows.map(r => {
      const confMarketTxt = r.conf_market.odds == null ? '—' : `${r.conf_market.odds > 0 ? '+' : ''}${r.conf_market.odds}`;
      const confEdgeTxt = r.conf_edge == null ? '—' : ((r.conf_edge * 100) >= 0 ? '+' : '') + (r.conf_edge * 100).toFixed(1).replace(/\.0$/,'') + ' pts';
      const confEdgeCls = r.conf_edge == null ? '' : r.conf_edge > 0 ? 'pos' : r.conf_edge < 0 ? 'neg' : '';

      return `<tr>
        <td>${teamLinkSafe(r.team)}</td>
        <td>${esc(r.conf || '')}</td>
        <td>${esc(r.actual)}</td>
        <td>${fmt(r.avg_wins,2)}</td>
        <td>${fmt(r.pre_wins,2)}</td>
        <td class="${r.win_delta.cls}">${r.win_delta.txt}</td>
        <td>${fmt(r.conf_wins,2)}</td>
        <td class="${r.conf_win_delta.cls}">${r.conf_win_delta.txt}</td>
        <td>${pct(r.conf_title)}</td>
        <td class="${r.conf_title_delta.cls}">${r.conf_title_delta.txt}</td>
        <td>${pct(r.make_title)}</td>
        <td>${pct(r.playoff)}</td>
        <td>${americanFromProb(r.playoff)}</td>
        <td class="${r.playoff_edge == null ? '' : r.playoff_edge > 0 ? 'pos' : r.playoff_edge < 0 ? 'neg' : ''}">${r.playoff_edge == null ? '—' : ((r.playoff_edge * 100) >= 0 ? '+' : '') + (r.playoff_edge * 100).toFixed(1).replace(/\.0$/,'') + ' pts'}</td>
        <td>${pct(r.nat_title)}</td>
        <td>${americanFromProb(r.nat_title)}</td>
        <td class="${r.nat_title_edge == null ? '' : r.nat_title_edge > 0 ? 'pos' : r.nat_title_edge < 0 ? 'neg' : ''}">${r.nat_title_edge == null ? '—' : ((r.nat_title_edge * 100) >= 0 ? '+' : '') + (r.nat_title_edge * 100).toFixed(1).replace(/\.0$/,'') + ' pts'}</td>
        <td>${fmt(r.win_market.total,1)}</td>
        <td class="${r.win_edge == null ? '' : r.win_edge > 0 ? 'pos' : r.win_edge < 0 ? 'neg' : ''}">${r.win_edge == null ? '—' : (r.win_edge > 0 ? '+' : '') + r.win_edge.toFixed(2).replace(/\.00$/,'').replace(/\.0$/,'')}</td>
        <td>${confMarketTxt}</td>
        <td class="${confEdgeCls}">${confEdgeTxt}</td>
      </tr>`;
    }).join('');

    return `<div class="sim-board-scroll"><table class="sim-board-table">
      <thead><tr>
        ${th('team','Team')}
        ${th('conf','Conf')}
        ${th('actual','Actual')}
        ${th('wins','Avg Wins')}
        ${th('wins','Pre Wins')}
        ${th('win_delta','Δ Wins')}
        ${th('conf_wins','Conf Wins')}
        ${th('conf_win_delta','Δ Conf')}
        ${th('conf_title','Conf Title')}
        ${th('conf_title_delta','Δ Title')}
        ${th('make_title','Make CG')}
        ${th('playoff','CFP %')}
        <th>CFP Fair</th>
        ${th('playoff_edge','CFP Edge')}
        ${th('nat_title','Nat Title')}
        <th>Nat Fair</th>
        ${th('nat_title_edge','Nat Edge')}
        ${th('win_total','Mkt WT')}
        ${th('win_edge','WT Edge')}
        ${th('conf_market','Mkt Conf')}
        ${th('conf_edge','Conf Edge')}
      </tr></thead>
      <tbody>${body}</tbody>
    </table></div>`;
  }

  window.mountSimulationsPage = function(){
    const confSel = document.getElementById('simConfFilter');
    const teamInput = document.getElementById('simTeamFilter');
    function redraw(){
      const wrap = document.getElementById('simBoardWrap');
      if (wrap) wrap.innerHTML = simBoardTable();
    }
    if (confSel && !confSel.dataset.bound) {
      confSel.dataset.bound = '1';
      confSel.addEventListener('change', redraw);
    }
    if (teamInput && !teamInput.dataset.bound) {
      teamInput.dataset.bound = '1';
      teamInput.addEventListener('input', redraw);
    }
    redraw();
  };

  window.renderSimulations = function(){
    const confs = [...new Set((DB.teams || []).map(t => t.conference).filter(Boolean))].sort();
    const rows = simRows();
    const topConf = [...rows].sort((a,b)=>(b.conf_title || 0) - (a.conf_title || 0))[0];
    const playoffReady = rows.some(r => r.playoff != null);
    const natReady = rows.some(r => r.nat_title != null);

    return `
      <div class="page-title">Simulations</div>
      <div class="page-sub">All-team simulation board with current projections, preseason deltas, and market-value placeholders.</div>

      <div class="hero-stats" style="margin-top:14px">
        <div class="mini"><div class="label">Teams</div><div class="value">${rows.length}</div></div>
        <div class="mini"><div class="label">Top Conf Title</div><div class="value">${topConf ? esc(topConf.team) : '—'}</div></div>
        <div class="mini"><div class="label">CFP Model</div><div class="value">${playoffReady ? 'Live' : 'Pending'}</div></div>
        <div class="mini"><div class="label">Nat Title Model</div><div class="value">${natReady ? 'Live' : 'Pending'}</div></div>
      </div>

      <div class="card" style="margin-top:16px">
        <div class="section-title">Simulation Board</div>
        <div class="small muted">Sort columns to compare current projections against frozen preseason expectations. CFP and national-title fields are placeholders until playoff/title simulation is wired.</div>
        <div class="filters" style="margin-top:12px">
          <select id="simConfFilter">
            <option value="all">All conferences</option>
            ${confs.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join('')}
          </select>
          <input id="simTeamFilter" placeholder="Filter team">
        </div>
        <div id="simBoardWrap" style="margin-top:12px"></div>
      </div>
    `;
  };

  const oldRender = window.render;
  if (typeof oldRender === 'function' && !oldRender.__simBoardMountWrapped) {
    const wrapped = function(){
      const result = oldRender.apply(this, arguments);
      if (location.hash === '#simulations') setTimeout(() => {
        if (typeof mountSimulationsPage === 'function') mountSimulationsPage();
      }, 0);
      return result;
    };
    wrapped.__simBoardMountWrapped = true;
    window.render = wrapped;
  }

  window.addEventListener('hashchange', () => {
    if (location.hash === '#simulations') setTimeout(() => {
      if (typeof mountSimulationsPage === 'function') mountSimulationsPage();
    }, 50);
  });
})();
</script>

<style id="safe-simulations-page-css">
.sim-board-scroll{overflow:auto;border:1px solid rgba(255,255,255,.08);border-radius:14px}
.sim-board-table{min-width:1800px}
.sim-board-table th,.sim-board-table td{white-space:nowrap}
.sim-board-table th{position:sticky;top:0;background:#14295a;z-index:2}
.sim-board-table td:nth-child(1),.sim-board-table th:nth-child(1){position:sticky;left:0;background:#102348;z-index:3;min-width:210px}
.sim-board-table th:nth-child(1){z-index:4}
</style>
<!-- safe-simulations-page-end -->
'''

for p in TARGETS:
    if not p.exists():
        continue
    s = p.read_text(errors="ignore")
    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")
    p.write_text(s, encoding="utf-8")
    print(p, "injected simulations board page")
