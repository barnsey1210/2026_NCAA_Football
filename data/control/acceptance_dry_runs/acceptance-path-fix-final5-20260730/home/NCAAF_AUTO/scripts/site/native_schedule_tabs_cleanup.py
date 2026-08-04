#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    # Make Market Lab the native/default schedule view, since Spreads/Totals/Moneyline
    # are the only schedule tabs we want visible now.
    s = s.replace(
        "let scheduleViewMode = localStorage.getItem('ncaaf_2026_schedule_view_mode_v1') || 'simple';",
        "let scheduleViewMode = 'marketlab';"
    )

    # Replace old Simple/Odds/Market Lab/Results toggle with native Spreads/Totals/Moneyline toggle.
    old = """    <div class="view-toggle" id="scheduleViewToggle">
      <button data-mode="simple" class="${scheduleViewMode==='simple'?'active':''}">Simple</button>
      <button data-mode="odds" class="${scheduleViewMode==='odds'?'active':''}">Odds Compare</button>
      <button data-mode="marketlab" class="${scheduleViewMode==='marketlab'?'active':''}">Market Lab</button>
      <button data-mode="results" class="${scheduleViewMode==='results'?'active':''}">Results</button>
    </div>
      ${scheduleViewMode === 'marketlab' ? `
      <div class="view-toggle marketlab-sub-toggle" id="marketLabSubToggle">
        <button onclick="setMarketLabMode('spreads')" class="${scheduleMarketLabMode==='spreads'?'active':''}">Spreads</button>
        <button onclick="setMarketLabMode('totals')" class="${scheduleMarketLabMode==='totals'?'active':''}">Totals</button>
        <button onclick="setMarketLabMode('moneyline')" class="${scheduleMarketLabMode==='moneyline'?'active':''}">Moneyline</button>
      </div>` : ''}"""

    new = """    <div class="view-toggle marketlab-sub-toggle schedule-native-market-tabs" id="marketLabSubToggle">
      <button onclick="setMarketLabMode('spreads')" class="${scheduleMarketLabMode==='spreads'?'active':''}">Spreads</button>
      <button onclick="setMarketLabMode('totals')" class="${scheduleMarketLabMode==='totals'?'active':''}">Totals</button>
      <button onclick="setMarketLabMode('moneyline')" class="${scheduleMarketLabMode==='moneyline'?'active':''}">Moneyline</button>
    </div>
    <div id="scheduleViewToggle" style="display:none"></div>"""

    if old not in s:
      raise SystemExit(f"target schedule toggle block not found in {path}")

    s = s.replace(old, new, 1)

    # The existing mount handler still expects scheduleViewToggle buttons.
    # Since those are gone, make it safely no-op.
    s = s.replace(
        """  const toggle = byId('scheduleViewToggle');
  if (toggle) toggle.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {
    scheduleViewMode = btn.dataset.mode;
    localStorage.setItem('ncaaf_2026_schedule_view_mode_v1', scheduleViewMode);
    toggle.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.dataset.mode === scheduleViewMode));
    drawScheduleTableFromCurrentFilters();
  }));""",
        """  const toggle = byId('scheduleViewToggle');
  if (toggle) toggle.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {
    scheduleViewMode = 'marketlab';
    drawScheduleTableFromCurrentFilters();
  }));"""
    )

    # Remove the post-render schedule cleanup block now that the source render is clean.
    s = re.sub(
        r"<!-- hide-redundant-schedule-tabs-light-start -->.*?<!-- hide-redundant-schedule-tabs-light-end -->",
        "",
        s,
        flags=re.S
    )

    path.write_text(s, encoding="utf-8")
    print(path, "native schedule tabs cleaned")
