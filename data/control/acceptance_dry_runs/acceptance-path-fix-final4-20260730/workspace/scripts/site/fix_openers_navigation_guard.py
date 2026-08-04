#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- openers-navigation-guard-start -->"
END = "<!-- openers-navigation-guard-end -->"

BLOCK = r'''
<!-- openers-navigation-guard-start -->
<script id="openers-navigation-guard-js">
(function(){
  if (window.__openersNavigationGuardInstalled) return;
  window.__openersNavigationGuardInstalled = true;

  function safeRenderOnNav(){
    // Do not render Openers unless the hash is actually #openers.
    if (location.hash !== '#openers') return;
    const app = document.getElementById('app');
    if (!app || typeof renderOpenersPage !== 'function') return;
    app.innerHTML = renderOpenersPage();
    if (typeof mountOpenersPage === 'function') mountOpenersPage();
  }

  window.addEventListener('hashchange', function(){
    if (location.hash === '#openers') {
      setTimeout(safeRenderOnNav, 0);
    }
  });
})();
</script>
<!-- openers-navigation-guard-end -->
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
    print(path, "openers navigation guard injected")
