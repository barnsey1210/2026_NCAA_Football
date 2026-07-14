#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- fix-home-command-center-logos-start -->"
END = "<!-- fix-home-command-center-logos-end -->"

BLOCK = r'''
<!-- fix-home-command-center-logos-start -->
<script id="fix-home-command-center-logos-js">
(function(){
  if (window.__fixHomeCommandCenterLogosInstalledV2) return;
  window.__fixHomeCommandCenterLogosInstalledV2 = true;

  function escRe(s){
    return String(s || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function allTeams(){
    try {
      return (DB.teams || [])
        .map(t => t.team)
        .filter(Boolean)
        .sort((a,b)=>b.length-a.length);
    } catch(e) {
      return [];
    }
  }

  function logo(team){
    if (!team) return '';
    try {
      if (typeof teamImageImg === 'function') return teamImageImg(team);
      if (typeof advTeamLogo === 'function') return advTeamLogo(team);
    } catch(e) {}
    return '';
  }

  function bookLogo(text){
    const raw = String(text || '').toLowerCase();
    const books = [
      ['fanduel','FanDuel'],
      ['draftkings','DraftKings'],
      ['betmgm','BetMGM'],
      ['caesars','Caesars'],
      ['espn bet','ESPN BET'],
      ['bet365','bet365']
    ];
    const found = books.find(([k]) => raw.includes(k));
    if (!found) return '';
    try {
      if (typeof sportsbookLogo === 'function') return sportsbookLogo(found[1]);
      if (typeof marketBookLogo === 'function') return marketBookLogo(found[1]);
    } catch(e) {}
    return '';
  }

  function exactTeamsInText(text, maxTeams){
    let raw = String(text || '');
    const found = [];

    // Longest names first, then mask matched spans so Georgia does not match inside Georgia State.
    for (const team of allTeams()) {
      const re = new RegExp(`(^|[^A-Za-z0-9])(${escRe(team)})(?=$|[^A-Za-z0-9])`, 'i');
      const m = raw.match(re);
      if (!m) continue;

      found.push(team);
      raw = raw.replace(new RegExp(escRe(m[2]), 'i'), ' '.repeat(String(m[2]).length));

      if (found.length >= maxTeams) break;
    }

    return found;
  }

  function teamsForRow(row){
    const label = row.querySelector('.home-cmd-row-label')?.textContent || '';
    const note = row.querySelector('.home-cmd-row-note')?.textContent || '';
    const value = row.querySelector('.home-cmd-row-value')?.textContent || '';

    // Game rows: use exact “Away at Home” only.
    if (label.includes(' at ')) {
      const parts = label.split(' at ');
      return parts.slice(0, 2).map(x => x.trim()).filter(Boolean);
    }

    // Futures / win-total rows: use only the first exact team in the label.
    return exactTeamsInText(label || `${note} ${value}`, 1);
  }

  function enhanceRows(){
    document.querySelectorAll('.home-cmd-row').forEach(row => {
      row.querySelector('.home-cmd-logo-stack')?.remove();

      const label = row.querySelector('.home-cmd-row-label')?.textContent || '';
      const note = row.querySelector('.home-cmd-row-note')?.textContent || '';
      const value = row.querySelector('.home-cmd-row-value')?.textContent || '';
      const text = `${label} ${note} ${value}`;

      const teams = teamsForRow(row);
      const logos = teams.map(logo).join('') + bookLogo(text);

      if (logos) {
        row.insertAdjacentHTML('afterbegin', `<div class="home-cmd-logo-stack">${logos}</div>`);
      }
    });
  }

  function enhanceTables(){
    // Table cards already render team logos directly. Do not add duplicate row logos there.
    document.querySelectorAll('.home-cmd-table-card .home-cmd-logo-stack').forEach(x => x.remove());
  }

  function run(){
    enhanceRows();
    enhanceTables();
  }

  function schedule(){
    setTimeout(run, 50);
    setTimeout(run, 250);
    setTimeout(run, 800);
  }

  window.addEventListener('hashchange', schedule);
  document.addEventListener('DOMContentLoaded', schedule);
  document.addEventListener('click', function(e){
    if (e.target.closest('#homeCommandCenter')) setTimeout(schedule, 50);
  });

  schedule();
})();
</script>

<style id="fix-home-command-center-logos-css">
.home-cmd-logo-stack{
  display:flex!important;
  align-items:center!important;
  gap:6px!important;
  min-width:70px!important;
  max-width:90px!important;
  flex-wrap:nowrap!important;
}
.home-cmd-logo-stack .team-logo-wrap{
  width:34px!important;
  height:34px!important;
  flex:0 0 34px!important;
}
.home-cmd-logo-stack .team-logo{
  width:31px!important;
  height:31px!important;
  object-fit:contain!important;
}
.home-cmd-logo-stack .sportsbook-logo-wrap{
  width:34px!important;
  height:28px!important;
  flex:0 0 34px!important;
}
.home-cmd-logo-stack .sportsbook-logo{
  max-width:29px!important;
  max-height:23px!important;
}
.home-cmd-table-card .home-cmd-logo-stack{
  display:none!important;
}
</style>
<!-- fix-home-command-center-logos-end -->
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
    print(path, "fixed exact-match dashboard logos")
