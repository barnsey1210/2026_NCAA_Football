#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- team-preseason-current-card-start -->"
END = "<!-- team-preseason-current-card-end -->"

BLOCK = r'''
<!-- team-preseason-current-card-start -->
<script id="team-preseason-current-card-js">
(function(){
  if (window.__teamPreseasonCurrentCardInstalled) return;
  window.__teamPreseasonCurrentCardInstalled = true;

  function n(v){
    const x = Number(v);
    return Number.isFinite(x) ? x : null;
  }

  function fmt(v, d=1){
    const x = n(v);
    if (x == null) return '—';
    return x.toFixed(d).replace(/\.0$/, '');
  }

  function fmtPctLocal(v){
    const x = n(v);
    if (x == null) return '—';
    if (x <= 1) return (x * 100).toFixed(1).replace(/\.0$/, '') + '%';
    return x.toFixed(1).replace(/\.0$/, '') + '%';
  }

  function delta(cur, pre, d=1, suffix=''){
    const c = n(cur), p = n(pre);
    if (c == null || p == null) return '—';
    const x = c - p;
    if (Math.abs(x) < 0.05) return '—';
    return (x > 0 ? '+' : '') + x.toFixed(d).replace(/\.0$/, '') + suffix;
  }

  function pctDelta(cur, pre){
    const c = n(cur), p = n(pre);
    if (c == null || p == null) return '—';
    const cc = c <= 1 ? c * 100 : c;
    const pp = p <= 1 ? p * 100 : p;
    const x = cc - pp;
    if (Math.abs(x) < 0.05) return '—';
    return (x > 0 ? '+' : '') + x.toFixed(1).replace(/\.0$/, '') + ' pts';
  }

  function teamRecordFromResults(team){
    try {
      const s = (getResultsSummary().teamStats || {})[team];
      if (!s) return '0-0';
      return `${s.wins || 0}-${s.losses || 0}`;
    } catch(e) {
      return '0-0';
    }
  }

  function cardHtml(teamName){
    if (typeof preseasonTeam !== 'function') return '';
    const pre = preseasonTeam(teamName);
    if (!pre) return '';

    const cur = (DB.teams || []).find(t => String(t.team) === String(teamName));
    if (!cur) return '';

    const rows = [
      ['Actual Record', '0-0', teamRecordFromResults(teamName), ''],
      ['Power Rating', fmt(pre.combo,1), fmt(cur.combo,1), delta(cur.combo, pre.combo,1)],
      ['Rank', pre.rank ? '#'+pre.rank : '—', cur.rank ? '#'+cur.rank : '—', (n(cur.rank)!=null && n(pre.rank)!=null && n(cur.rank)!==n(pre.rank)) ? ((n(cur.rank)<n(pre.rank)?'Up ':'Down ') + Math.abs(n(cur.rank)-n(pre.rank))) : '—'],
      ['Projected Wins', fmt(pre.avg_total_wins,2), fmt(cur.avg_total_wins,2), delta(cur.avg_total_wins, pre.avg_total_wins,2)],
      ['Projected Conf Wins', fmt(pre.avg_conference_wins,2), fmt(cur.avg_conference_wins,2), delta(cur.avg_conference_wins, pre.avg_conference_wins,2)],
      ['Conference Title', fmtPctLocal(pre.conference_title_pct), fmtPctLocal(cur.conference_title_pct), pctDelta(cur.conference_title_pct, pre.conference_title_pct)],
      ['Make Title Game', fmtPctLocal(pre.make_title_game_pct), fmtPctLocal(cur.make_title_game_pct), pctDelta(cur.make_title_game_pct, pre.make_title_game_pct)],
      ['Bowl Eligibility', fmtPctLocal(pre.bowl_eligibility_pct), fmtPctLocal(cur.bowl_eligibility_pct), pctDelta(cur.bowl_eligibility_pct, pre.bowl_eligibility_pct)]
    ];

    return `<div class="card preseason-current-card">
      <div class="section-title">Preseason vs Current</div>
      <div class="small muted">Frozen preseason projection compared with the current in-season site state.</div>
      <table class="preseason-current-table">
        <thead><tr><th>Metric</th><th>Preseason</th><th>Current</th><th>Change</th></tr></thead>
        <tbody>
          ${rows.map(r=>`<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td><td class="${String(r[3]).startsWith('+') || String(r[3]).startsWith('Up') ? 'pos' : String(r[3]).startsWith('-') || String(r[3]).startsWith('Down') ? 'neg' : ''}">${r[3]}</td></tr>`).join('')}
        </tbody>
      </table>
    </div>`;
  }

  function inject(){
    if (!location.hash.startsWith('#team/')) return;
    const title = document.querySelector('.page-title, .team-title, h1');
    const teamName = title ? title.textContent.trim().replace(/\s+[A-Z0-9]{2,5}$/, '') : '';
    if (!teamName || document.querySelector('.preseason-current-card')) return;

    const html = cardHtml(teamName);
    if (!html) return;

    const grid = document.querySelector('.team-dashboard-grid') || document.querySelector('.grid') || document.getElementById('app');
    if (grid) grid.insertAdjacentHTML('afterbegin', html);
  }

  function schedule(){
    setTimeout(inject, 50);
    setTimeout(inject, 250);
    setTimeout(inject, 800);
  }

  window.addEventListener('hashchange', schedule);
  document.addEventListener('DOMContentLoaded', schedule);
  schedule();
})();
</script>

<style id="team-preseason-current-card-css">
.preseason-current-card{border-color:rgba(96,165,250,.28)!important}
.preseason-current-table th,.preseason-current-table td{font-size:12px}
.preseason-current-table td:nth-child(2),
.preseason-current-table td:nth-child(3),
.preseason-current-table td:nth-child(4){font-weight:900}
</style>
<!-- team-preseason-current-card-end -->
'''

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")

    path.write_text(s, encoding="utf-8")
    print(path, "injected team preseason/current card")
