from pathlib import Path
import re

TARGETS = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

PATCH_JS = r'''
<script id="schedule-spread-lab-display-js">
(function(){
  if (window.__scheduleSpreadLabDisplayPatched) return;
  window.__scheduleSpreadLabDisplayPatched = true;

  const oldMarketLabAtsMetrics = window.marketLabAtsMetrics || marketLabAtsMetrics;
  window.marketLabAtsMetrics = function(g){
    const out = oldMarketLabAtsMetrics(g);
    if (!out || !g) return out;

    const variance = typeof gameVarianceBadge === 'function' ? gameVarianceBadge(g) : '';
    const lab = typeof labSpreadNoteForGame === 'function' ? labSpreadNoteForGame(g) : '';

    if (out.side && out.side !== '—') {
      out.side = `<div class="ats-edge-with-coach"><div>${out.side}</div>${lab}${variance ? `<div style="margin-top:3px">${variance}</div>` : ''}</div>`;
    }
    return out;
  };

  const oldMarketLabTotalMetrics = window.marketLabTotalMetrics || marketLabTotalMetrics;
  window.marketLabTotalMetrics = function(g){
    const out = oldMarketLabTotalMetrics(g);
    if (!out || !g) return out;

    if (out.side && out.side !== '—') {
      const note = `<span class="lab-spread-note">Totals model: <strong>Site Projection / SP+ baseline 100%</strong></span>`;
      out.side = `<div class="total-edge-with-coach"><div>${out.side}</div>${note}</div>`;
    }
    return out;
  };

  const oldMarketLabTeamCellWithRp = window.marketLabTeamCellWithRp || marketLabTeamCellWithRp;
  window.marketLabTeamCellWithRp = function(g, teamName){
    const base = oldMarketLabTeamCellWithRp(g, teamName);
    const badge = typeof ratingVarianceBadge === 'function' ? ratingVarianceBadge(teamName) : '';
    return badge ? `${base}<div style="margin-top:3px">${badge}</div>` : base;
  };

  const oldRenderSchedule = window.renderSchedule || renderSchedule;
  window.renderSchedule = function(){
    let html = oldRenderSchedule();

    const context = (window.scheduleViewMode === 'marketlab')
      ? (window.scheduleMarketLabMode === 'totals'
          ? (typeof scheduleTotalsModelStatusCard === 'function' ? scheduleTotalsModelStatusCard() : '')
          : window.scheduleMarketLabMode === 'spreads'
            ? (typeof scheduleSpreadModelStatusCard === 'function' ? scheduleSpreadModelStatusCard() : '')
            : '')
      : '';

    if (context && html.includes('<div id="scheduleFilterStrip"')) {
      html = html.replace('<div id="scheduleFilterStrip"', context + '\n<div id="scheduleFilterStrip"');
    }

    return html;
  };
})();
</script>
'''

def patch(path):
    if not path.exists():
        print("missing", path)
        return
    s = path.read_text(errors="ignore")
    orig = s

    s = re.sub(r'\n<script id="schedule-spread-lab-display-js">.*?</script>\n?', '\n', s, flags=re.S)

    if "</body>" in s:
        s = s.replace("</body>", "\n" + PATCH_JS + "\n</body>", 1)
    else:
        s += "\n" + PATCH_JS + "\n"

    if s != orig:
        path.with_suffix(path.suffix + ".bak_schedule_spread_lab_display").write_text(orig)
        path.write_text(s)
        print("patched", path)
    else:
        print("no changes", path)

def main():
    for p in TARGETS:
        patch(p)

if __name__ == "__main__":
    main()
