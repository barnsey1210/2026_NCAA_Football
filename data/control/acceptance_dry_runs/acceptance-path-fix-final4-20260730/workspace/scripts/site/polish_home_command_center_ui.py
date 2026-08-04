#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- polish-home-command-center-ui-start -->"
END = "<!-- polish-home-command-center-ui-end -->"

BLOCK = r'''
<!-- polish-home-command-center-ui-start -->
<script id="polish-home-command-center-ui-js">
(function(){
  if (window.__polishHomeCommandCenterUIInstalled) return;
  window.__polishHomeCommandCenterUIInstalled = true;

  function esc(v){
    if (typeof escapeHtml === 'function') return escapeHtml(String(v ?? ''));
    return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function teamLogoSafe(text){
    const raw = String(text || '');
    const teams = (DB && DB.teams) ? DB.teams.map(t => t.team).sort((a,b)=>b.length-a.length) : [];
    const found = teams.find(t => raw.includes(t));
    if (!found) return '';
    try {
      if (typeof teamImageImg === 'function') return teamImageImg(found);
      if (typeof advTeamLogo === 'function') return advTeamLogo(found);
    } catch(e) {}
    return '';
  }

  function bookLogoSafe(text){
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

  function enhanceRows(){
    document.querySelectorAll('.home-cmd-row').forEach(row => {
      if (row.dataset.logoEnhanced === '1') return;
      row.dataset.logoEnhanced = '1';

      const labelEl = row.querySelector('.home-cmd-row-label');
      const noteEl = row.querySelector('.home-cmd-row-note');
      if (!labelEl) return;

      const label = labelEl.textContent || '';
      const note = noteEl ? noteEl.textContent || '' : '';

      const tLogo = teamLogoSafe(label + ' ' + note);
      const bLogo = bookLogoSafe(label + ' ' + note);

      if (tLogo || bLogo) {
        row.insertAdjacentHTML('afterbegin', `<div class="home-cmd-logo-stack">${tLogo}${bLogo}</div>`);
      }
    });
  }

  function schedule(){
    setTimeout(enhanceRows, 50);
    setTimeout(enhanceRows, 250);
    setTimeout(enhanceRows, 800);
  }

  const oldRender = window.render;
  if (typeof oldRender === 'function' && !oldRender.__polishHomeCommandCenterUIWrapped) {
    const wrapped = function(){
      const result = oldRender.apply(this, arguments);
      schedule();
      return result;
    };
    wrapped.__polishHomeCommandCenterUIWrapped = true;
    window.render = wrapped;
  }

  window.addEventListener('hashchange', schedule);
  document.addEventListener('DOMContentLoaded', schedule);
  schedule();
})();
</script>

<style id="polish-home-command-center-ui-css">
/* Home Command Center expanded card layout */
.home-command-center{
  padding:18px!important;
  border-radius:22px!important;
}

.home-command-head .section-title{
  font-size:28px!important;
}

.home-cmd-grid{
  display:grid!important;
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  gap:16px!important;
}

.home-cmd-card{
  min-height:260px!important;
  padding:16px!important;
  border-radius:18px!important;
  background:linear-gradient(180deg,rgba(15,35,75,.72),rgba(5,12,30,.42))!important;
}

.home-cmd-card-title{
  font-size:22px!important;
  line-height:1.1!important;
  margin-bottom:4px!important;
}

.home-cmd-card-sub{
  font-size:14px!important;
  line-height:1.3!important;
  margin-bottom:14px!important;
  color:#b9c7e5!important;
}

.home-cmd-card-rows{
  gap:10px!important;
}

.home-cmd-row{
  display:grid!important;
  grid-template-columns:auto minmax(0,1fr) auto!important;
  align-items:center!important;
  gap:12px!important;
  min-height:56px!important;
  padding:10px 0!important;
}

.home-cmd-logo-stack{
  display:flex;
  align-items:center;
  gap:5px;
  min-width:42px;
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

.home-cmd-row-label{
  font-size:16px!important;
  line-height:1.18!important;
  white-space:normal!important;
  overflow:visible!important;
  text-overflow:clip!important;
  max-width:none!important;
}

.home-cmd-row-note{
  font-size:13px!important;
  line-height:1.25!important;
  white-space:normal!important;
  overflow:visible!important;
  text-overflow:clip!important;
  max-width:none!important;
  margin-top:3px!important;
}

.home-cmd-row-value{
  font-size:20px!important;
  min-width:92px!important;
}

.home-cmd-empty{
  font-size:14px!important;
  padding:14px 0!important;
}

@media(max-width:1200px){
  .home-cmd-grid{grid-template-columns:1fr!important}
}

@media(max-width:800px){
  .home-cmd-row{
    grid-template-columns:auto minmax(0,1fr)!important;
  }
  .home-cmd-row-value{
    grid-column:2;
    text-align:left!important;
    min-width:0!important;
  }
}

/* Home command center readability fix */
.home-cmd-row{
  grid-template-columns:auto minmax(0,1fr) minmax(125px,180px)!important;
  overflow:hidden!important;
}

.home-cmd-row-value{
  white-space:normal!important;
  overflow-wrap:anywhere!important;
  line-height:1.1!important;
  text-align:right!important;
  font-size:17px!important;
  min-width:0!important;
}

.home-cmd-extra-row{
  display:none!important;
}

.home-cmd-card.expanded .home-cmd-extra-row{
  display:grid!important;
}

.home-cmd-more{
  margin-top:10px;
  border:1px solid rgba(96,165,250,.35);
  border-radius:999px;
  padding:7px 12px;
  background:rgba(37,99,235,.28);
  color:#dbeafe;
  font-weight:900;
  cursor:pointer;
}

.home-cmd-more:hover{
  background:rgba(37,99,235,.45);
}

</style>
<!-- polish-home-command-center-ui-end -->
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
    print(path, "polished home command center UI")
