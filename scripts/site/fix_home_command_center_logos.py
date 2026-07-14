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
  if (window.__fixHomeCommandCenterLogosInstalled) return;
  window.__fixHomeCommandCenterLogosInstalled = true;

  function allTeams(){
    try {
      return (DB.teams || []).map(t => t.team).filter(Boolean).sort((a,b)=>b.length-a.length);
    } catch(e) {
      return [];
    }
  }

  function logo(team){
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

  function teamsInText(text){
    const txt = String(text || '');
    const found = [];
    for (const t of allTeams()) {
      if (txt.includes(t) && !found.includes(t)) found.push(t);
      if (found.length >= 2) break;
    }
    return found;
  }

  function enhance(){
    document.querySelectorAll('.home-cmd-row').forEach(row => {
      const old = row.querySelector('.home-cmd-logo-stack');
      if (old) old.remove();

      const label = row.querySelector('.home-cmd-row-label')?.textContent || '';
      const note = row.querySelector('.home-cmd-row-note')?.textContent || '';
      const value = row.querySelector('.home-cmd-row-value')?.textContent || '';
      const text = `${label} ${note} ${value}`;

      const teams = teamsInText(text);
      const logos = teams.map(logo).join('') + bookLogo(text);

      if (logos) {
        row.insertAdjacentHTML('afterbegin', `<div class="home-cmd-logo-stack">${logos}</div>`);
      }
    });
  }

  function schedule(){
    setTimeout(enhance, 50);
    setTimeout(enhance, 250);
    setTimeout(enhance, 800);
  }

  const oldRender = window.render;
  if (typeof oldRender === 'function' && !oldRender.__fixHomeCommandCenterLogosWrapped) {
    const wrapped = function(){
      const result = oldRender.apply(this, arguments);
      schedule();
      return result;
    };
    wrapped.__fixHomeCommandCenterLogosWrapped = true;
    window.render = wrapped;
  }

  window.addEventListener('hashchange', schedule);
  document.addEventListener('DOMContentLoaded', schedule);
  schedule();
})();
</script>

<style id="fix-home-command-center-logos-css">
.home-cmd-logo-stack{
  display:flex!important;
  align-items:center!important;
  gap:5px!important;
  min-width:76px!important;
  max-width:96px!important;
  flex-wrap:wrap!important;
}
.home-cmd-logo-stack .team-logo-wrap{
  width:34px!important;
  height:34px!important;
}
.home-cmd-logo-stack .team-logo{
  width:31px!important;
  height:31px!important;
  object-fit:contain!important;
}
.home-cmd-logo-stack .sportsbook-logo-wrap{
  width:34px!important;
  height:28px!important;
}
.home-cmd-logo-stack .sportsbook-logo{
  max-width:29px!important;
  max-height:23px!important;
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
    print(path, "fixed home command center logos")
