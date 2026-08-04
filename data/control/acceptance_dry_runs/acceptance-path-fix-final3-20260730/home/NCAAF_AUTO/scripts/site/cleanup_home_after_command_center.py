#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- cleanup-home-after-command-center-start -->"
END = "<!-- cleanup-home-after-command-center-end -->"

BLOCK = r'''
<!-- cleanup-home-after-command-center-start -->
<script id="cleanup-home-after-command-center-js">
(function(){
  if (window.__cleanupHomeAfterCommandCenterInstalled) return;
  window.__cleanupHomeAfterCommandCenterInstalled = true;

  function isHomeDashboard(){
    if (!location.hash || location.hash === '#home') return true;
    const title = document.querySelector('.page-title');
    const txt = String(title ? title.textContent : '').trim().toLowerCase();
    return txt === 'daily betting dashboard' || txt === 'home';
  }

  function cleanup(){
    if (!isHomeDashboard()) return;

    const cc = document.getElementById('homeCommandCenter');
    if (!cc) return;

    let node = cc.nextElementSibling;
    while (node) {
      const next = node.nextElementSibling;

      // Keep scripts/styles alone; hide visible old dashboard sections only.
      const tag = String(node.tagName || '').toLowerCase();
      if (!['script','style'].includes(tag)) {
        node.classList.add('home-after-command-hidden');
        node.style.display = 'none';
      }

      node = next;
    }
  }

  function schedule(){
    setTimeout(cleanup, 50);
    setTimeout(cleanup, 250);
    setTimeout(cleanup, 800);
  }

  const oldRender = window.render;
  if (typeof oldRender === 'function' && !oldRender.__cleanupHomeAfterCommandCenterWrapped) {
    const wrapped = function(){
      const result = oldRender.apply(this, arguments);
      schedule();
      return result;
    };
    wrapped.__cleanupHomeAfterCommandCenterWrapped = true;
    window.render = wrapped;
  }

  window.addEventListener('hashchange', schedule);
  document.addEventListener('DOMContentLoaded', schedule);
  schedule();
})();
</script>
<!-- cleanup-home-after-command-center-end -->
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
    print(path, "injected home cleanup after command center")
