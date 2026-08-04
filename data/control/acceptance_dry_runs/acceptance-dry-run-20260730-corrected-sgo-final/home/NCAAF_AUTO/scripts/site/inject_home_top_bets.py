#!/usr/bin/env python3
from pathlib import Path
import json, re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]
DATA = Path("data/agents/home_top_bets.json")

START = "<!-- home-top-bets-start -->"
END = "<!-- home-top-bets-end -->"

payload = json.dumps(json.loads(DATA.read_text()), separators=(",", ":")) if DATA.exists() else '{"updated_at":"","items":[]}'

BLOCK = r'''
<!-- home-top-bets-start -->
<script id="home-top-bets-data" type="application/json">__HOME_TOP_BETS_PAYLOAD__</script>

<script id="home-top-bets-js">
(function(){
  if (window.__homeTopBetsInstalled) return;
  window.__homeTopBetsInstalled = true;

  function esc(v){
    if (typeof escapeHtml === 'function') return escapeHtml(String(v ?? ''));
    return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function readData(){
    const el = document.getElementById('home-top-bets-data');
    if (!el) return {items:[]};
    try { return JSON.parse(el.textContent || '{"items":[]}'); } catch(e) { return {items:[]}; }
  }

  function isHome(){
    return !location.hash || location.hash === '#home';
  }

  function toggleHtml(){
    return `<div class="home-season-toggle" id="homeSeasonToggle">
      <button type="button" data-view="current" class="active">Current Season</button>
      <button type="button" data-view="preseason">Preseason Snapshot</button>
    </div>`;
  }

  function cardHtml(){
    const data = readData();
    const items = data.items || [];
    if (!items.length) return '';

    return `<div class="card home-top-bets-card" id="homeTopBetsCard">
      <div class="home-top-bets-head">
        <div>
          <div class="section-title">Top Betting Watchlist</div>
          <div class="small muted">Compact alert feed from model edges, market movement, and current futures value. Full details stay on Simulations, Line History, Futures, and Schedule.</div>
        </div>
        <div class="home-top-bets-updated">Updated ${esc(String(data.updated_at || '').replace('T',' '))}</div>
      </div>

      <div class="home-top-bets-list">
        ${items.map(x=>`<a class="home-top-bet-row" href="${esc(x.link_hash || '#home')}">
          <div class="home-top-bet-rank">${x.rank}</div>
          <div class="home-top-bet-main">
            <div class="home-top-bet-title"><span class="home-top-bet-bucket">${esc(x.bucket)}</span>${esc(x.label)}</div>
            <div class="home-top-bet-summary">${esc(x.summary)}</div>
          </div>
          <div class="home-top-bet-side">
            <div class="home-top-bet-edge">${esc(x.edge || '')}</div>
            <div class="home-top-bet-action">${esc(x.action || '')}</div>
          </div>
        </a>`).join('')}
      </div>
    </div>`;
  }

  function install(){
    if (!isHome()) return;
    if (document.getElementById('homeTopBetsCard')) return;

    const app = document.getElementById('app');
    if (!app) return;

    const html = toggleHtml() + cardHtml();

    // On the current Home page, this is the Daily Betting Dashboard.
    // Put the watchlist near the top, after the hero summary if present.
    const hero = app.querySelector('.hero');
    const stats = app.querySelector('.hero-stats');
    const firstGrid = app.querySelector('.grid');

    if (hero) hero.insertAdjacentHTML('afterend', html);
    else if (stats) stats.insertAdjacentHTML('afterend', html);
    else if (firstGrid) firstGrid.insertAdjacentHTML('beforebegin', html);
    else app.insertAdjacentHTML('afterbegin', html);

    const toggle = document.getElementById('homeSeasonToggle');
    if (toggle) {
      toggle.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
          toggle.querySelectorAll('button').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');

          const card = document.getElementById('homeTopBetsCard');
          if (card) {
            if (btn.dataset.view === 'preseason') {
              card.style.opacity = '0.55';
              card.querySelector('.small.muted').textContent = 'Preseason snapshot mode: betting watchlist is intentionally dimmed because it reflects current/live market context.';
            } else {
              card.style.opacity = '1';
              card.querySelector('.small.muted').textContent = 'Compact alert feed from model edges, market movement, and current futures value. Full details stay on Simulations, Line History, Futures, and Schedule.';
            }
          }
        });
      });
    }
  }

  function schedule(){
    setTimeout(install, 50);
    setTimeout(install, 250);
    setTimeout(install, 800);
  }

  const oldRender = window.render;
  if (typeof oldRender === 'function' && !oldRender.__homeTopBetsWrapped) {
    const wrapped = function(){
      const result = oldRender.apply(this, arguments);
      schedule();
      return result;
    };
    wrapped.__homeTopBetsWrapped = true;
    window.render = wrapped;
  }

  window.addEventListener('hashchange', schedule);
  document.addEventListener('DOMContentLoaded', schedule);
  schedule();
})();
</script>

<style id="home-top-bets-css">
.home-season-toggle{display:inline-flex;gap:8px;margin:14px 0 0;padding:5px;border:1px solid rgba(255,255,255,.12);border-radius:999px;background:rgba(15,23,42,.55)}
.home-season-toggle button{border:0;border-radius:999px;padding:8px 13px;background:transparent;color:#cbd5e1;font-weight:900;cursor:pointer}
.home-season-toggle button.active{background:rgba(37,99,235,.75);color:#fff}
.home-top-bets-card{margin-top:14px;border-color:rgba(96,165,250,.28)!important}
.home-top-bets-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:10px}
.home-top-bets-updated{font-size:12px;color:#aab7d4;white-space:nowrap}
.home-top-bets-list{display:grid;gap:8px}
.home-top-bet-row{display:grid;grid-template-columns:34px minmax(0,1fr) 150px;gap:10px;align-items:center;text-decoration:none;color:inherit;border:1px solid rgba(255,255,255,.08);border-radius:14px;background:rgba(2,6,23,.22);padding:9px 10px}
.home-top-bet-row:hover{background:rgba(59,130,246,.13);border-color:rgba(96,165,250,.35)}
.home-top-bet-rank{width:28px;height:28px;border-radius:999px;background:rgba(37,99,235,.7);display:flex;align-items:center;justify-content:center;font-weight:950}
.home-top-bet-title{font-weight:950;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.home-top-bet-bucket{display:inline-flex;margin-right:7px;border-radius:999px;padding:2px 7px;background:rgba(96,165,250,.18);color:#bfdbfe;font-size:11px;text-transform:uppercase;letter-spacing:.04em}
.home-top-bet-summary{font-size:12px;color:#aab7d4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}
.home-top-bet-side{text-align:right}
.home-top-bet-edge{font-weight:950;color:#4ade80}
.home-top-bet-action{font-size:12px;color:#cbd5e1;margin-top:2px}
@media(max-width:800px){.home-top-bet-row{grid-template-columns:30px minmax(0,1fr)}.home-top-bet-side{grid-column:2;text-align:left}.home-top-bets-head{display:block}}
</style>
<!-- home-top-bets-end -->
'''.replace('__HOME_TOP_BETS_PAYLOAD__', payload)

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")

    path.write_text(s, encoding="utf-8")
    print(path, "injected home top bets")
