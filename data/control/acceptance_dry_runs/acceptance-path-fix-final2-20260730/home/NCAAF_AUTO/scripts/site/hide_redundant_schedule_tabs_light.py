from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]
START = "<!-- hide-redundant-schedule-tabs-light-start -->"
END = "<!-- hide-redundant-schedule-tabs-light-end -->"

BLOCK = r'''
<!-- hide-redundant-schedule-tabs-light-start -->
<script id="hide-redundant-schedule-tabs-light-js">
(function(){
  if (window.__hideRedundantScheduleTabsLightInstalled) return;
  window.__hideRedundantScheduleTabsLightInstalled = true;

  const HIDE = new Set(['simple','odds compare','market lab','results']);

  function norm(x){
    return String(x || '').trim().toLowerCase().replace(/\s+/g,' ');
  }

  function cleanupScheduleTabs(){
    const title = document.querySelector('.page-title');
    if (!title || norm(title.textContent) !== 'season schedule') return;

    document.querySelectorAll('button').forEach(btn => {
      const t = norm(btn.textContent);
      if (HIDE.has(t)) {
        btn.style.display = 'none';
        btn.setAttribute('aria-hidden', 'true');
      }
    });
  }

  const oldRender = window.render;
  if (typeof oldRender === 'function' && !oldRender.__scheduleTabLightWrapped) {
    const wrapped = function(){
      const result = oldRender.apply(this, arguments);
      setTimeout(cleanupScheduleTabs, 0);
      setTimeout(cleanupScheduleTabs, 150);
      return result;
    };
    wrapped.__scheduleTabLightWrapped = true;
    window.render = wrapped;
  }

  window.addEventListener('hashchange', () => {
    setTimeout(cleanupScheduleTabs, 50);
    setTimeout(cleanupScheduleTabs, 250);
  });

  document.addEventListener('DOMContentLoaded', () => {
    setTimeout(cleanupScheduleTabs, 50);
    setTimeout(cleanupScheduleTabs, 250);
  });

  setTimeout(cleanupScheduleTabs, 50);
  setTimeout(cleanupScheduleTabs, 250);
})();
</script>
<!-- hide-redundant-schedule-tabs-light-end -->
'''

for path in TARGETS:
    if not path.exists():
        continue
    s = path.read_text(errors="ignore")
    s = re.sub(re.escape(START) + r".*?" + re.escape(END), "", s, flags=re.S)
    s = s.replace("</body>", BLOCK + "\n</body>")
    path.write_text(s, encoding="utf-8")
    print(path, "added light schedule tab cleanup")
