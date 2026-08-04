#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- schedule-week-buttons-start -->"
END = "<!-- schedule-week-buttons-end -->"

BLOCK = r'''
<!-- schedule-week-buttons-start -->
<script id="schedule-week-buttons-js">
(function(){
  if (window.__scheduleWeekButtonsInstalledSafe) return;
  window.__scheduleWeekButtonsInstalledSafe = true;

  function onSchedule(){
    const title = document.querySelector('.page-title');
    return location.hash === '#schedule' || String(title ? title.textContent : '').trim() === 'Season Schedule';
  }

  function weeksFromDB(){
    try {
      return [...new Set((DB.games || []).map(g => g.week).filter(w => w !== null && w !== undefined && w !== ''))]
        .map(w => Number(w))
        .filter(w => Number.isFinite(w))
        .sort((a,b)=>a-b);
    } catch(e) {
      return [];
    }
  }

  function findWeekSelect(){
    const selects = [...document.querySelectorAll('select')];
    return selects.find(sel => {
      const opts = [...sel.options].map(o => String(o.textContent || '').trim().toLowerCase());
      return opts.includes('all weeks') || opts.some(x => /^week\s*\d+$/.test(x));
    }) || null;
  }

  function setWeek(value){
    localStorage.setItem('ncaaf_schedule_week_button_safe_v1', String(value));

    const sel = findWeekSelect();
    if (sel) {
      sel.value = String(value);
      sel.dispatchEvent(new Event('input', {bubbles:true}));
      sel.dispatchEvent(new Event('change', {bubbles:true}));
    }

    document.querySelectorAll('.schedule-week-pill').forEach(btn => {
      btn.classList.toggle('active', String(btn.dataset.week) === String(value));
    });
  }

  function install(){
    if (!onSchedule()) return;

    const sel = findWeekSelect();
    if (!sel) return;

    const filters = sel.closest('.filters') || sel.parentElement;
    if (!filters) return;

    if (!document.getElementById('scheduleWeekButtonBar')) {
      const weeks = weeksFromDB();
      if (!weeks.length) return;

      const html = `<div id="scheduleWeekButtonBar" class="schedule-week-button-bar">
        <button type="button" class="schedule-week-pill" data-week="all">All</button>
        ${weeks.map(w => `<button type="button" class="schedule-week-pill" data-week="${w}">W${w}</button>`).join('')}
      </div>`;

      filters.insertAdjacentHTML('beforebegin', html);

      document.querySelectorAll('.schedule-week-pill').forEach(btn => {
        btn.addEventListener('click', () => setWeek(btn.dataset.week));
      });
    }

    sel.classList.add('schedule-week-select-hidden');

    const saved = localStorage.getItem('ncaaf_schedule_week_button_safe_v1') || sel.value || 'all';
    document.querySelectorAll('.schedule-week-pill').forEach(btn => {
      btn.classList.toggle('active', String(btn.dataset.week) === String(saved));
    });
  }

  function scheduleInstall(){
    if (!onSchedule()) return;
    [50, 200, 500, 1000].forEach(ms => setTimeout(install, ms));
  }

  window.addEventListener('hashchange', scheduleInstall);
  document.addEventListener('DOMContentLoaded', scheduleInstall);

  // Let the native router render first, then install buttons.
  document.addEventListener('click', function(e){
    const txt = String(e.target && e.target.textContent || '').trim();
    if (txt === 'Season Schedule') {
      setTimeout(scheduleInstall, 80);
    }
  }, true);

  scheduleInstall();
})();
</script>

<style id="schedule-week-buttons-css">
.schedule-week-button-bar{
  display:flex;
  flex-wrap:wrap;
  gap:9px;
  margin:14px 0 14px;
  align-items:center;
}
.schedule-week-pill{
  border:1px solid rgba(96,165,250,.35);
  background:rgba(15,35,74,.70);
  color:#dbeafe;
  border-radius:999px;
  padding:9px 15px;
  font-weight:950;
  cursor:pointer;
}
.schedule-week-pill.active{
  background:#2563eb;
  color:white;
  border-color:#60a5fa;
  box-shadow:0 0 0 2px rgba(96,165,250,.20) inset;
}
.schedule-week-select-hidden{
  display:none!important;
}
@media(max-width:800px){
  .schedule-week-button-bar{
    overflow-x:auto;
    flex-wrap:nowrap;
    padding-bottom:4px;
  }
  .schedule-week-pill{
    flex:0 0 auto;
  }
}
</style>
<!-- schedule-week-buttons-end -->
'''

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    # Replace old week-button block entirely, including the MutationObserver version.
    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")

    path.write_text(s, encoding="utf-8")
    print(path, "safe schedule week buttons injected")
