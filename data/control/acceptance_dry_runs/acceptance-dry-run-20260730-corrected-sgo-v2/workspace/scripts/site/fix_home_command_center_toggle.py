#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- fix-home-command-center-toggle-start -->"
END = "<!-- fix-home-command-center-toggle-end -->"

BLOCK = r'''
<!-- fix-home-command-center-toggle-start -->
<script id="fix-home-command-center-toggle-js">
(function(){
  if (window.__fixHomeCommandCenterToggleInstalled) return;
  window.__fixHomeCommandCenterToggleInstalled = true;

  function isHomeHash(){
    return !location.hash || location.hash === '#home';
  }

  function findModeButton(mode){
    const want = mode === 'preseason' ? 'preseason snapshot' : 'current season';
    return [...document.querySelectorAll('#homeCommandCenter button, #homeCommandCenter .home-cmd-toggle button, #homeCommandCenter [role="button"]')]
      .find(b => String(b.textContent || '').trim().toLowerCase().includes(want));
  }

  function modeFromButton(btn){
    const txt = String(btn?.textContent || '').trim().toLowerCase();
    if (txt.includes('preseason')) return 'preseason';
    if (txt.includes('current')) return 'current';
    return null;
  }

  function applyMode(mode){
    const root = document.getElementById('homeCommandCenter');
    if (!root) return false;

    root.setAttribute('data-home-season-mode', mode);
    localStorage.setItem('ncaaf_home_command_mode_v1', mode);

    const curBtn = findModeButton('current');
    const preBtn = findModeButton('preseason');

    [curBtn, preBtn].forEach(b => {
      if (!b) return;
      b.classList.remove('active');
      b.setAttribute('aria-pressed', 'false');
    });

    if (mode === 'preseason' && preBtn) {
      preBtn.classList.add('active');
      preBtn.setAttribute('aria-pressed', 'true');
    }
    if (mode === 'current' && curBtn) {
      curBtn.classList.add('active');
      curBtn.setAttribute('aria-pressed', 'true');
    }

    // Hide/show by text and existing section classes.
    const blocks = [...root.children];
    blocks.forEach(el => {
      const txt = String(el.textContent || '').toLowerCase();
      const isPre = txt.includes('preseason command center') || el.className.includes('preseason');
      const isCur = txt.includes('current season command center') || el.className.includes('current');
      if (isPre) el.style.display = mode === 'preseason' ? '' : 'none';
      if (isCur) el.style.display = mode === 'current' ? '' : 'none';
    });

    // Fallback: deeper sections/cards.
    root.querySelectorAll('[class*="preseason"]').forEach(el => {
      if (!el.closest('.home-cmd-toggle')) el.style.display = mode === 'preseason' ? '' : 'none';
    });
    root.querySelectorAll('[class*="current"]').forEach(el => {
      if (!el.closest('.home-cmd-toggle')) el.style.display = mode === 'current' ? '' : 'none';
    });

    return true;
  }

  function restoreMode(){
    if (!isHomeHash()) return;
    const mode = localStorage.getItem('ncaaf_home_command_mode_v1') || 'current';
    setTimeout(() => applyMode(mode), 60);
    setTimeout(() => applyMode(mode), 250);
    setTimeout(() => applyMode(mode), 800);
  }

  document.addEventListener('click', function(e){
    const btn = e.target.closest('#homeCommandCenter button, #homeCommandCenter [role="button"]');
    const mode = modeFromButton(btn);
    if (!mode) return;

    e.preventDefault();
    e.stopPropagation();
    applyMode(mode);
  }, true);

  window.addEventListener('hashchange', restoreMode);
  document.addEventListener('DOMContentLoaded', restoreMode);

  const oldRender = window.render;
  if (typeof oldRender === 'function' && !oldRender.__homeCommandToggleFixWrapped) {
    const wrapped = function(){
      const result = oldRender.apply(this, arguments);
      restoreMode();
      return result;
    };
    wrapped.__homeCommandToggleFixWrapped = true;
    window.render = wrapped;
  }

  restoreMode();
})();
</script>
<!-- fix-home-command-center-toggle-end -->
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
    print(path, "fixed dashboard current/preseason toggle")
