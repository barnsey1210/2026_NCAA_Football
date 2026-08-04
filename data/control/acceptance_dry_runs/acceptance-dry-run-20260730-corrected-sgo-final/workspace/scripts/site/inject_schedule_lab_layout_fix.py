from pathlib import Path
import re

TARGETS = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

CSS = r'''
<style id="schedule-lab-layout-fix-style">
#schedule .ratings-weight-lab{
  margin:10px 0 12px !important;
}
#schedule .ratings-weight-lab summary{
  min-height:42px !important;
}
#schedule .ratings-weight-lab .rating-weight-row{
  grid-template-columns:minmax(150px,220px) 310px 58px !important;
}
#schedule .ratings-weight-lab .rating-weight-label span{
  font-size:10px !important;
  line-height:1.15 !important;
}
#schedule .ratings-weight-lab input[type="range"]{
  max-width:210px !important;
}
#schedule .model-context-card{
  margin:10px 0 12px !important;
}
</style>
'''

JS = r'''
<script id="schedule-lab-layout-fix-js">
(function(){
  if (window.__scheduleLabLayoutFixed) return;
  window.__scheduleLabLayoutFixed = true;

  const oldRatingsWeightLabPanel = window.ratingsWeightLabPanel || ratingsWeightLabPanel;
  window.scheduleRatingsWeightLabPanel = function(){
    let html = oldRatingsWeightLabPanel();

    html = html
      .replace('Display-only Rating Lab', 'Schedule What-If Spread Lab')
      .replace('Production/default:', 'Production spread model:')
      .replace('Manual sliders update this Rankings page only. Season simulations, win totals, conference futures, and schedule edges use the latest production rebuild.',
        'Manual sliders update displayed upcoming-game spreads/ATS edges only. Futures, win totals, conference sims, and official projections still require a rebuild.')
      .replace('Apply Display Weights', 'Apply What-If Weights');

    // Keep schedule lab collapsed by default unless user opens it.
    html = html.replace('id="ratingsWeightLab" class="card ratings-weight-lab compact" open', 'id="ratingsWeightLab" class="card ratings-weight-lab compact"');
    return html;
  };

  const oldRenderSchedule = window.renderSchedule || renderSchedule;
  window.renderSchedule = function(){
    let html = oldRenderSchedule();

    // Replace the generic rankings lab with schedule-specific copy.
    html = html.replace(oldRatingsWeightLabPanel(), window.scheduleRatingsWeightLabPanel());

    const context = (window.scheduleViewMode === 'marketlab')
      ? (window.scheduleMarketLabMode === 'totals'
          ? (typeof scheduleTotalsModelStatusCard === 'function' ? scheduleTotalsModelStatusCard() : '')
          : window.scheduleMarketLabMode === 'spreads'
            ? (typeof scheduleSpreadModelStatusCard === 'function' ? scheduleSpreadModelStatusCard() : '')
            : '')
      : '';

    if (context && !html.includes('id="scheduleSpreadModelStatusCard"') && !html.includes('id="scheduleTotalsModelStatusCard"')) {
      html = html.replace('<div id="scheduleFilterStrip"', context + '\n<div id="scheduleFilterStrip"');
    }

    return html;
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

    s = re.sub(r'\n<style id="schedule-lab-layout-fix-style">.*?</style>\n?', '\n', s, flags=re.S)
    s = re.sub(r'\n<script id="schedule-lab-layout-fix-js">.*?</script>\n?', '\n', s, flags=re.S)

    insert = "\n" + CSS + "\n" + JS + "\n"
    s = s.replace("</body>", insert + "\n</body>", 1)

    if s != orig:
        path.with_suffix(path.suffix + ".bak_schedule_lab_layout_fix").write_text(orig)
        path.write_text(s)
        print("patched", path)
    else:
        print("no changes", path)

def main():
    for p in TARGETS:
        patch(p)

if __name__ == "__main__":
    main()
