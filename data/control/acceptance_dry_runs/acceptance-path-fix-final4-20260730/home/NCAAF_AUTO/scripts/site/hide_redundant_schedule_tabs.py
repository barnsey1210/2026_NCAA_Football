from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- hide-redundant-schedule-tabs-start -->"
END = "<!-- hide-redundant-schedule-tabs-end -->"

BLOCK = r'''
<!-- hide-redundant-schedule-tabs-start -->
<style id="hide-redundant-schedule-tabs-css">
/* Season Schedule cleanup:
   Keep only Spreads / Totals / Moneyline.
   Hide redundant Simple, Odds Compare, Market Lab, Results buttons. */
.schedule-view-tabs button,
.schedule-tabs button,
.view-tabs button,
.tab-row button,
button {
}

/* JS below handles exact button text safely after render. */
</style>

<script id="hide-redundant-schedule-tabs-js">
(function(){
  if (window.__hideRedundantScheduleTabsInstalled) return;
  window.__hideRedundantScheduleTabsInstalled = true;

  const HIDE_TOP_SCHEDULE_TABS = new Set([
    'simple',
    'odds compare',
    'market lab',
    'results'
  ]);

  const KEEP_SUBTABS = new Set([
    'spreads',
    'totals',
    'moneyline'
  ]);

  function norm(x){
    return String(x || '').trim().toLowerCase().replace(/\s+/g, ' ');
  }

  function isSchedulePage(){
    const title = document.querySelector('.page-title');
    return title && norm(title.textContent) === 'season schedule';
  }

  function hideTabs(){
    if (!isSchedulePage()) return;

    document.querySelectorAll('button').forEach(btn => {
      const t = norm(btn.textContent);

      if (HIDE_TOP_SCHEDULE_TABS.has(t)) {
        btn.style.display = 'none';
        btn.setAttribute('aria-hidden', 'true');
        return;
      }

      if (KEEP_SUBTABS.has(t)) {
        btn.style.display = '';
        btn.removeAttribute('aria-hidden');
      }
    });

    // If the hidden Market Lab button was the active high-level tab,
    // leave the underlying market-lab data visible because Spreads/Totals/Moneyline
    // are the only controls the user needs.
    try {
      if (typeof setMarketLabMode === 'function') {
        const activeSub = window.scheduleMarketLabMode || 'spreads';
        setMarketLabMode(activeSub);
      }
    } catch(e) {}
  }

  function scheduleHide(){
    setTimeout(hideTabs, 25);
    setTimeout(hideTabs, 150);
    setTimeout(hideTabs, 500);
  }

  document.addEventListener('DOMContentLoaded', scheduleHide);
  window.addEventListener('hashchange', scheduleHide);

  const obs = new MutationObserver(scheduleHide);
  obs.observe(document.documentElement, {childList:true, subtree:true});

  scheduleHide();
})();
</script>
<!-- hide-redundant-schedule-tabs-end -->
'''

def inject(path):
    if not path.exists():
        return

    s = path.read_text(errors="ignore")

    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")

    path.write_text(s, encoding="utf-8")
    print(path, "patched schedule tab cleanup")

for p in TARGETS:
    inject(p)
