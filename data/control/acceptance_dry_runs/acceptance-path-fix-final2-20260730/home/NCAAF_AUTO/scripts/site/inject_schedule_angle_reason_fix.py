from pathlib import Path
import re

TARGETS = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

CSS = r'''
<style id="schedule-angle-reason-fix-style">
.angle-reason-badge{
  display:inline-flex;
  align-items:center;
  gap:4px;
  margin-top:4px;
  border-radius:999px;
  padding:3px 7px;
  font-size:10px;
  font-weight:1000;
  border:1px solid rgba(96,165,250,.35);
  background:rgba(59,130,246,.12);
  color:#bfdbfe;
  white-space:nowrap;
}
.angle-reason-badge.hot{
  border-color:rgba(239,68,68,.40);
  background:rgba(239,68,68,.14);
  color:#fecaca;
}
.angle-reason-badge.warn{
  border-color:rgba(245,158,11,.38);
  background:rgba(245,158,11,.14);
  color:#fde68a;
}
</style>
'''

JS = r'''
<script id="schedule-angle-reason-fix-js">
(function(){
  if (window.__scheduleAngleReasonFixPatched) return;
  window.__scheduleAngleReasonFixPatched = true;

  // Expose injected consts to later filter scripts/wrappers.
  try {
    if (typeof RATING_VARIANCE_BY_TEAM !== 'undefined') {
      window.RATING_VARIANCE_BY_TEAM = RATING_VARIANCE_BY_TEAM;
    }
  } catch(e) {}

  try {
    if (typeof GAME_PROJECTION_BLEND_CONFIG !== 'undefined') {
      window.GAME_PROJECTION_BLEND_CONFIG = GAME_PROJECTION_BLEND_CONFIG;
    }
  } catch(e) {}

  function n(v){
    const x = Number(v);
    return Number.isFinite(x) ? x : null;
  }

  function currentAngle(){
    const el = document.getElementById('fAngle');
    return el ? el.value : 'all';
  }

  function varianceRange(team){
    const v = window.RATING_VARIANCE_BY_TEAM?.[team];
    return Number(v?.rating_range || 0);
  }

  function maxGameVariance(g){
    return Math.max(varianceRange(g.away_team), varianceRange(g.home_team));
  }

  function projSpreadText(g){
    const p = n(g.projected_margin_home);
    if (p == null) return 'Proj —';
    const fav = p >= 0 ? g.home_team : g.away_team;
    return `${fav} -${Math.abs(p).toFixed(1)}`;
  }

  function marketSpreadTextShort(g){
    let ms = null;
    try {
      if (typeof marketSpread === 'function') ms = n(marketSpread(g));
    } catch(e) {}
    if (ms == null) ms = n(g.market_spread_home);
    if (ms == null) return 'Market —';
    const fav = ms <= 0 ? g.home_team : g.away_team;
    return `${fav} -${Math.abs(ms).toFixed(1)}`;
  }

  function angleReason(g, angle){
    const maxVar = maxGameVariance(g);

    if (angle === 'high_variance' || angle === 'medium_variance') {
      // Variance is already shown by team/game variance badges.
      // Do not add another angle-reason badge in ATS Edge.
      return null;
    }

    if (angle === 'coin_toss') {
      const p = n(g.projected_margin_home);
      let ms = null;
      try {
        if (typeof marketSpread === 'function') ms = n(marketSpread(g));
      } catch(e) {}
      if (ms == null) ms = n(g.market_spread_home);

      const reasons = [];
      if (p != null && Math.abs(p) <= 3) reasons.push(`model ${projSpreadText(g)}`);
      if (ms != null && Math.abs(ms) <= 3) reasons.push(`market ${marketSpreadTextShort(g)}`);
      return reasons.length ? {text:`Angle: coin toss · ${reasons.join(' · ')}`, cls:'warn'} : null;
    }

    if (angle === 'coach_1h') return {text:'Angle: coach 1H support', cls:''};
    if (angle === 'coach_ats') return {text:'Angle: coach ATS support', cls:''};
    if (angle === 'rp_support') return {text:'Angle: returning production support', cls:''};
    if (angle === 'travel_1h') return {text:'Angle: travel / 1H travel', cls:'warn'};
    if (angle === 'lookahead') return {text:'Angle: schedule lookahead', cls:'warn'};
    if (angle === 'b2b_road') return {text:'Angle: b2b road spot', cls:'warn'};
    if (angle === 'injury') return {text:'Angle: injury alert', cls:'hot'};

    return null;
  }

  window.scheduleAngleReasonBadge = function(g){
    const angle = currentAngle();
    if (!angle || angle === 'all') return '';
    const reason = angleReason(g, angle);
    if (!reason) return '';
    return `<div><span class="angle-reason-badge ${reason.cls || ''}">${reason.text}</span></div>`;
  };

  // Make the prior betting-angle filter use the exposed window variance object.
  const oldDraw = window.drawScheduleTableFromCurrentFilters || drawScheduleTableFromCurrentFilters;
  window.drawScheduleTableFromCurrentFilters = drawScheduleTableFromCurrentFilters = function(){
    return oldDraw();
  };

  // Add a reason badge to the ATS Edge cell for selected betting-angle filters.
  const prevAts = window.marketLabAtsMetrics || marketLabAtsMetrics;
  window.marketLabAtsMetrics = marketLabAtsMetrics = function(g){
    const out = prevAts(g);
    if (!out || !g) return out;

    const badge = window.scheduleAngleReasonBadge ? window.scheduleAngleReasonBadge(g) : '';
    if (badge && out.side && out.side !== '—' && !String(out.side).includes('angle-reason-badge')) {
      out.side = `<div class="ats-edge-with-coach"><div>${out.side}</div>${badge}</div>`;
    }
    return out;
  };

  // Also add reason badge in totals mode.
  const prevTotal = window.marketLabTotalMetrics || marketLabTotalMetrics;
  window.marketLabTotalMetrics = marketLabTotalMetrics = function(g){
    const out = prevTotal(g);
    if (!out || !g) return out;

    const badge = window.scheduleAngleReasonBadge ? window.scheduleAngleReasonBadge(g) : '';
    if (badge && out.side && out.side !== '—' && !String(out.side).includes('angle-reason-badge')) {
      out.side = `<div class="total-edge-with-coach"><div>${out.side}</div>${badge}</div>`;
    }
    return out;
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

    s = re.sub(r'\n<style id="schedule-angle-reason-fix-style">.*?</style>\n?', '\n', s, flags=re.S)
    s = re.sub(r'\n<script id="schedule-angle-reason-fix-js">.*?</script>\n?', '\n', s, flags=re.S)

    insert = "\n" + CSS + "\n" + JS + "\n"
    s = s.replace("</body>", insert + "\n</body>", 1)

    if s != orig:
        path.with_suffix(path.suffix + ".bak_schedule_angle_reason_fix").write_text(orig)
        path.write_text(s)
        print("patched", path)
    else:
        print("no changes", path)

def main():
    for p in TARGETS:
        patch(p)

if __name__ == "__main__":
    main()
