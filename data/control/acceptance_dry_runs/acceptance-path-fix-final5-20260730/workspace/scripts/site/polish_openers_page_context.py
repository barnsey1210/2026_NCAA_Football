#!/usr/bin/env python3
from pathlib import Path
import sys
import re
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.ncaaf_config import model_summary

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- polish-openers-page-context-start -->"
END = "<!-- polish-openers-page-context-end -->"

BLOCK = r'''
<!-- polish-openers-page-context-start -->
<script id="polish-openers-page-context-js">
(function(){
  if (window.__polishOpenersPageContextInstalled) return;
  window.__polishOpenersPageContextInstalled = true;

  function esc(v){
    return String(v == null ? '' : v)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }

  function n(v){
    const x = Number(v);
    return Number.isFinite(x) ? x : null;
  }

  function normalizeTeamType(v){
    const s = String(v || '').toUpperCase();
    if (s.includes('FCS')) return 'FCS';
    if (s.includes('FBS')) return 'FBS';
    return '';
  }

  function teamRow(team){
    try {
      return (DB.teams || []).find(t => t.team === team) || {};
    } catch(e) {
      return {};
    }
  }

  function teamSubdivision(team){
    const t = teamRow(team);
    const raw = t.subdivision || t.classification || t.division || t.level || t.fbs_fcs || t.team_type || '';
    const norm = normalizeTeamType(raw);
    if (norm) return norm;

    // Site DB mainly tracks FBS teams. If team exists in DB.teams, treat as FBS.
    if (t && t.team) return 'FBS';

    return 'FCS';
  }

  function gameClass(g){
    const a = teamSubdivision(g.away_team);
    const h = teamSubdivision(g.home_team);
    if (a === 'FBS' && h === 'FBS') return 'FBS vs FBS';
    if ((a === 'FBS' && h === 'FCS') || (a === 'FCS' && h === 'FBS')) return 'FBS vs FCS';
    if (a === 'FCS' && h === 'FCS') return 'FCS vs FCS';
    return 'Other';
  }

  function selectedWeek(){
    return document.getElementById('openersWeek')?.value || 'all';
  }

  function gamesForSelectedWeek(){
    const week = selectedWeek();
    let games = [...(DB.games || [])];
    if (week !== 'all') games = games.filter(g => String(g.week) === String(week));
    return games;
  }

  function updateOpenersHeroCounts(){
    const games = gamesForSelectedWeek();
    const fbsFbs = games.filter(g => gameClass(g) === 'FBS vs FBS').length;
    const fbsFcs = games.filter(g => gameClass(g) === 'FBS vs FCS').length;

    const minis = [...document.querySelectorAll('.hero-stats .mini')];
    const gamesMini = minis.find(m => /games/i.test(m.textContent || ''));
    const weeksMini = minis.find(m => /weeks/i.test(m.textContent || ''));

    if (gamesMini) {
      const val = gamesMini.querySelector('.value');
      const lab = gamesMini.querySelector('.label');
      if (val) val.textContent = String(games.length);
      if (lab) lab.textContent = selectedWeek() === 'all' ? 'Games' : `Week ${selectedWeek()} Games`;
    }

    if (weeksMini) {
      const val = weeksMini.querySelector('.value');
      const lab = weeksMini.querySelector('.label');
      if (val) val.textContent = selectedWeek() === 'all' ? String([...new Set((DB.games || []).map(g => g.week))].length) : '1';
      if (lab) lab.textContent = selectedWeek() === 'all' ? 'Weeks' : 'Selected Week';
    }

    let chipWrap = document.getElementById('openersGameTypeChips');
    const hero = document.querySelector('.hero');
    if (!chipWrap && hero) {
      chipWrap = document.createElement('div');
      chipWrap.id = 'openersGameTypeChips';
      chipWrap.className = 'openers-game-type-chips';
      hero.insertAdjacentElement('afterend', chipWrap);
    }
    if (chipWrap) {
      chipWrap.innerHTML = `
        <span>${selectedWeek() === 'all' ? 'All weeks' : 'Week ' + esc(selectedWeek())}</span>
        <span>FBS vs FBS: <b>${fbsFbs}</b></span>
        <span>FBS vs FCS: <b>${fbsFcs}</b></span>
        <span>Total games: <b>${games.length}</b></span>
      `;
    }
  }

  function latestChangeText(r){
    const candidates = [
      r.latest_change_date,
      r.last_change_date,
      r.value_changed_at,
      r.rating_change_date,
      r.snapshot_date,
      r.source_updated,
      r.source_updated_at
    ].filter(Boolean);
    return candidates.length ? String(candidates[0]).slice(0, 19).replace('T',' ') : 'Not detected yet';
  }

  function makeRatingsContextCollapsible(){
    const ctx = document.querySelector('.openers-ratings-context');
    if (!ctx || ctx.dataset.polished === '1') return;

    ctx.dataset.polished = '1';

    const banner = ctx.querySelector('.openers-ratings-banner');
    const grid = ctx.querySelector('.openers-ratings-grid');
    if (!banner || !grid) return;

    const details = document.createElement('details');
    details.className = 'openers-ratings-details';

    const summary = document.createElement('summary');
    summary.innerHTML = `<span>Production ratings context</span><small>__MODEL_SUMMARY__ · click to expand</small>`;

    const body = document.createElement('div');
    body.className = 'openers-ratings-details-body';

    body.appendChild(banner);
    body.appendChild(grid);

    details.appendChild(summary);
    details.appendChild(body);

    ctx.innerHTML = '';
    ctx.appendChild(details);

    // Remove redundant old opener status pills below the ratings cards.
    document.querySelectorAll('.openers-status-pills, .openers-model-status').forEach(el => {
      if (!el.closest('.openers-ratings-context')) el.remove();
    });

    // Reword any remaining source-card Pulled labels.
    ctx.querySelectorAll('.openers-rating-source-meta').forEach(el => {
      el.innerHTML = el.innerHTML
        .replace(/^Pulled:/i, 'Current site value date:')
        .replace(/^Source updated:/i, 'Latest detected change:');
      if (/Latest detected change:\s*Not provided by source/i.test(el.textContent || '')) {
        el.textContent = 'Latest detected change: Not detected yet';
      }
    });
  }

  function patchOpenersDraw(){
    const oldMount = window.mountOpenersPage;
    if (typeof oldMount !== 'function' || oldMount.__polishedOpenersMount) return;

    window.mountOpenersPage = function(){
      const result = oldMount.apply(this, arguments);

      makeRatingsContextCollapsible();
      updateOpenersHeroCounts();

      const weekSelect = document.getElementById('openersWeek');
      if (weekSelect && !weekSelect.dataset.heroCountsBound) {
        weekSelect.dataset.heroCountsBound = '1';
        weekSelect.addEventListener('input', () => setTimeout(updateOpenersHeroCounts, 30));
        weekSelect.addEventListener('change', () => setTimeout(updateOpenersHeroCounts, 30));
      }

      document.querySelectorAll('[data-openers-week]').forEach(btn => {
        if (!btn.dataset.heroCountsBound) {
          btn.dataset.heroCountsBound = '1';
          btn.addEventListener('click', () => setTimeout(updateOpenersHeroCounts, 60));
        }
      });

      return result;
    };

    window.mountOpenersPage.__polishedOpenersMount = true;
  }

  function run(){
    patchOpenersDraw();
    if (location.hash === '#openers') {
      setTimeout(makeRatingsContextCollapsible, 50);
      setTimeout(updateOpenersHeroCounts, 80);
      setTimeout(makeRatingsContextCollapsible, 250);
      setTimeout(updateOpenersHeroCounts, 300);
    }
  }

  window.addEventListener('hashchange', run);
  document.addEventListener('DOMContentLoaded', run);
  run();
})();
</script>

<style id="polish-openers-page-context-css">
.openers-ratings-context{
  margin-top:12px!important;
}
.openers-ratings-details{
  border:1px solid rgba(96,165,250,.26);
  background:rgba(15,23,42,.40);
  border-radius:16px;
  overflow:hidden;
}
.openers-ratings-details summary{
  list-style:none;
  cursor:pointer;
  padding:12px 16px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  font-weight:950;
  color:#f8fafc;
}
.openers-ratings-details summary::-webkit-details-marker{
  display:none;
}
.openers-ratings-details summary span{
  font-size:17px;
}
.openers-ratings-details summary small{
  color:#aebddd;
  font-size:12px;
  font-weight:800;
}
.openers-ratings-details summary:after{
  content:'▸';
  color:#93c5fd;
  font-weight:950;
}
.openers-ratings-details[open] summary:after{
  content:'▾';
}
.openers-ratings-details-body{
  padding:0 14px 14px;
}
.openers-ratings-banner{
  margin-top:0!important;
}
.openers-ratings-grid{
  grid-template-columns:repeat(5,minmax(180px,1fr))!important;
  gap:10px!important;
}
.openers-rating-source-card{
  min-width:180px!important;
  padding:11px 13px!important;
}
.openers-rating-source-name{
  font-size:16px!important;
}
.openers-rating-source-meta{
  font-size:11px!important;
}
.openers-game-type-chips{
  display:flex;
  flex-wrap:wrap;
  gap:8px;
  margin:10px 0 0;
}
.openers-game-type-chips span{
  border:1px solid rgba(96,165,250,.25);
  background:rgba(15,35,74,.62);
  color:#dbeafe;
  border-radius:999px;
  padding:6px 10px;
  font-size:12px;
  font-weight:900;
}
.openers-game-type-chips b{
  color:#f8fafc;
}
</style>
<!-- polish-openers-page-context-end -->
'''

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    block = BLOCK.replace("__MODEL_SUMMARY__", model_summary())
    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: block, s, flags=re.S)
    else:
        s = s.replace("</body>", block + "\n</body>")

    path.write_text(s, encoding="utf-8")
    print(path, "openers context polished")
