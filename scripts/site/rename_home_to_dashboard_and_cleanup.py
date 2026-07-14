#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- rename-home-dashboard-cleanup-start -->"
END = "<!-- rename-home-dashboard-cleanup-end -->"

BLOCK = r'''
<!-- rename-home-dashboard-cleanup-start -->
<script id="rename-home-dashboard-cleanup-js">
(function(){
  if (window.__renameHomeDashboardCleanupInstalled) return;
  window.__renameHomeDashboardCleanupInstalled = true;

  function isDashboard(){
    if (!location.hash || location.hash === '#home') return true;
    const title = document.querySelector('.page-title');
    const txt = String(title ? title.textContent : '').trim().toLowerCase();
    return txt === 'daily betting dashboard' || txt === 'home' || txt === 'dashboard';
  }

  function cleanupDashboardHeader(){
    if (!isDashboard()) return;

    // Rename visible page title.
    const title = document.querySelector('.page-title');
    if (title && /daily betting dashboard|home/i.test(title.textContent || '')) {
      title.textContent = 'Dashboard';
    }

    const sub = document.querySelector('.page-sub');
    if (sub && /actionable market edges|automated update|line moves|arbs/i.test(sub.textContent || '')) {
      sub.textContent = 'Current-season and preseason command center for betting, market, matchup, and ratings signals.';
    }

    // Remove the old stat chips and quick-link buttons above the command center.
    const cc = document.getElementById('homeCommandCenter');
    if (!cc) return;

    let node = cc.previousElementSibling;
    while (node) {
      const prev = node.previousElementSibling;
      const text = String(node.textContent || '').toLowerCase();
      const tag = String(node.tagName || '').toLowerCase();

      if (!['script','style'].includes(tag)) {
        if (
          text.includes('game edges') ||
          text.includes('arbs / middles') ||
          text.includes('market moves') ||
          text.includes('action games') ||
          text.includes('open market lab') ||
          text.includes('open arbs') ||
          text.includes('open daily moves') ||
          text.includes('open schedule') ||
          text.includes('latest pull')
        ) {
          node.style.display = 'none';
          node.classList.add('dashboard-old-header-hidden');
        }
      }

      node = prev;
    }
  }

  function renameNav(){
    document.querySelectorAll('.nav button').forEach(btn => {
      if (String(btn.textContent || '').trim() === 'Home') {
        btn.textContent = 'Dashboard';
      }
    });
  }

  function schedule(){
    setTimeout(() => { renameNav(); cleanupDashboardHeader(); }, 50);
    setTimeout(() => { renameNav(); cleanupDashboardHeader(); }, 250);
    setTimeout(() => { renameNav(); cleanupDashboardHeader(); }, 800);
  }

  const oldRender = window.render;
  if (typeof oldRender === 'function' && !oldRender.__renameHomeDashboardCleanupWrapped) {
    const wrapped = function(){
      const result = oldRender.apply(this, arguments);
      schedule();
      return result;
    };
    wrapped.__renameHomeDashboardCleanupWrapped = true;
    window.render = wrapped;
  }

  window.addEventListener('hashchange', schedule);
  document.addEventListener('DOMContentLoaded', schedule);
  schedule();
})();
</script>
<!-- rename-home-dashboard-cleanup-end -->
'''

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    # Static nav text replacement where simple.
    s = s.replace("navBtn('#home','Home')", "navBtn('#home','Dashboard')")

    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")

    path.write_text(s, encoding="utf-8")
    print(path, "renamed Home to Dashboard and cleaned old dashboard header")
