from pathlib import Path
import re

TARGETS = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

CSS = r'''
<style id="schedule-variance-filter-style">
#schedule .ratings-weight-lab summary{
  overflow:hidden !important;
}
#schedule .ratings-weight-lab .rating-lab-summary-pill{
  max-width:260px !important;
  overflow:hidden !important;
  text-overflow:ellipsis !important;
  white-space:nowrap !important;
}
#schedule .model-context-card{
  margin:12px 0 12px !important;
}
.schedule-variance-note{
  margin:8px 0 10px;
  font-size:11px;
  font-weight:850;
  color:#cbd5e1;
}
</style>
'''

JS = r'''
<script id="schedule-variance-filter-js">
(function(){
  if (window.__scheduleVarianceFilterPatched) return;
  window.__scheduleVarianceFilterPatched = true;

  function maxGameVariance(g){
    const a = window.RATING_VARIANCE_BY_TEAM?.[g.away_team];
    const h = window.RATING_VARIANCE_BY_TEAM?.[g.home_team];
    return Math.max(Number(a?.rating_range || 0), Number(h?.rating_range || 0));
  }

  function isHighVarianceGame(g){
    return maxGameVariance(g) >= 6;
  }

  const oldRenderSchedule = window.renderSchedule || renderSchedule;
  window.renderSchedule = function(){
    let html = oldRenderSchedule();

    // Add model context card immediately above filters.
    const context = (window.scheduleViewMode === 'marketlab')
      ? (window.scheduleMarketLabMode === 'totals'
          ? (typeof scheduleTotalsModelStatusCard === 'function' ? scheduleTotalsModelStatusCard() : '')
          : window.scheduleMarketLabMode === 'spreads'
            ? (typeof scheduleSpreadModelStatusCard === 'function' ? scheduleSpreadModelStatusCard() : '')
            : '')
      : '';

    if (context && !html.includes('scheduleSpreadModelStatusCard') && !html.includes('scheduleTotalsModelStatusCard')) {
      html = html.replace('<div id="scheduleFilterStrip"', context + '\n<div id="scheduleFilterStrip"');
    }

    // Add High Variance option to All games dropdown.
    html = html.replace(
      '<option value="open">Open only</option></select>',
      '<option value="open">Open only</option><option value="high_variance">High model variance</option></select>'
    );

    return html;
  };

  const oldDrawScheduleTableFromCurrentFilters = window.drawScheduleTableFromCurrentFilters || drawScheduleTableFromCurrentFilters;
  window.drawScheduleTableFromCurrentFilters = function(){
    const typeEl = document.getElementById('fType');
    const wantsHighVariance = typeEl && typeEl.value === 'high_variance';

    if (!wantsHighVariance) {
      return oldDrawScheduleTableFromCurrentFilters();
    }

    const weekEl = document.getElementById('fWeek');
    const confEl = document.getElementById('fConf');
    const teamEl = document.getElementById('fTeam');
    const wrap = document.getElementById('scheduleWrap');
    if (!weekEl || !confEl || !teamEl || !wrap) return;

    const week = weekEl.value;
    const conf = confEl.value;
    const team = String(teamEl.value || '').toLowerCase().trim();

    let games = DB.games.slice();

    if (week !== 'all') games = games.filter(g => String(g.week) === String(week));
    if (conf !== 'all') games = games.filter(g => {
      const a = teamByName[String(g.away_team || '').toLowerCase()];
      const h = teamByName[String(g.home_team || '').toLowerCase()];
      return (a && a.conference === conf) || (h && h.conference === conf);
    });
    if (team) games = games.filter(g =>
      String(g.away_team || '').toLowerCase().includes(team) ||
      String(g.home_team || '').toLowerCase().includes(team)
    );

    games = games.filter(isHighVarianceGame);
    games.sort((a,b) => maxGameVariance(b) - maxGameVariance(a));

    wrap.innerHTML = `<div class="schedule-variance-note">Showing games where at least one team has a 6+ point range across SP+, FPI, and TeamRankings. Sorted by highest model disagreement.</div>` + scheduleTable(games, scheduleViewMode);

    if (typeof enhanceScheduleStickyHeader === 'function') {
      setTimeout(enhanceScheduleStickyHeader, 0);
    }
  };

  if ((location.hash || '') === '#schedule' && typeof route === 'function') {
    setTimeout(route, 0);
  }
})();
</script>
'''

def patch(path):
    if not path.exists():
        print("missing", path)
        return

    s = path.read_text(errors="ignore")
    orig = s

    s = re.sub(r'\n<style id="schedule-variance-filter-style">.*?</style>\n?', '\n', s, flags=re.S)
    s = re.sub(r'\n<script id="schedule-variance-filter-js">.*?</script>\n?', '\n', s, flags=re.S)

    insert = "\n" + CSS + "\n" + JS + "\n"
    s = s.replace("</body>", insert + "\n</body>", 1)

    if s != orig:
        path.with_suffix(path.suffix + ".bak_schedule_variance_filter").write_text(orig)
        path.write_text(s)
        print("patched", path)
    else:
        print("no changes", path)

def main():
    for p in TARGETS:
        patch(p)

if __name__ == "__main__":
    main()
