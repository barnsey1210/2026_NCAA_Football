from pathlib import Path
import re

TARGETS = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

CSS = r'''
<style id="schedule-betting-angle-filter-style">
#fAngle{
  height:38px !important;
  font-size:14px !important;
  min-width:220px !important;
  max-width:260px !important;
}
.schedule-angle-note{
  margin:8px 0 10px;
  font-size:11px;
  font-weight:850;
  color:#cbd5e1;
}
.schedule-angle-note b{
  color:#f8fafc;
}
</style>
'''

JS = r'''
<script id="schedule-betting-angle-filter-js">
(function(){
  if (window.__scheduleBettingAngleFilterPatched) return;
  window.__scheduleBettingAngleFilterPatched = true;

  const ANGLES = [
    ['all', 'All betting angles'],
    ['high_variance', 'High model variance'],
    ['medium_variance', 'Medium+ model variance'],
    ['coach_1h', 'Coach 1H support'],
    ['coach_ats', 'Coach ATS support'],
    ['rp_support', 'Returning production support'],
    ['travel_1h', 'Travel / 1H travel angle'],
    ['lookahead', 'Schedule spot: lookahead'],
    ['b2b_road', 'Schedule spot: b2b road'],
    ['coin_toss', 'Coin toss / near pick'],
    ['injury', 'Injury alert']
    ,['pbp_away_dog_move', 'PBP opener move: away dog']
    ,['pbp_under_move', 'PBP opener move: under']
    ,['cross_book_spread_outlier', 'Stale opener: spread']
    ,['cross_book_total_outlier', 'Stale opener: total']
  ];

  function n(v){
    const x = Number(v);
    return Number.isFinite(x) ? x : null;
  }

  function lc(v){
    return String(v ?? '').toLowerCase();
  }

  function fieldText(g){
    return Object.entries(g || {})
      .filter(([k,v]) => /(angle|spot|travel|inj|coach|ats|lookahead|sandwich|rest|road|rp|returning|badge|note|alert)/i.test(k))
      .map(([k,v]) => `${k}:${v}`)
      .join(' ')
      .toLowerCase();
  }

  function maxGameVariance(g){
    const a = window.RATING_VARIANCE_BY_TEAM?.[g.away_team];
    const h = window.RATING_VARIANCE_BY_TEAM?.[g.home_team];
    return Math.max(Number(a?.rating_range || 0), Number(h?.rating_range || 0));
  }

  function hasUsefulHtml(html){
    const x = String(html || '').toLowerCase();
    return !!x && !x.includes('muted') && !x.includes('—') && x !== 'null' && x !== 'undefined';
  }

  function hasCoach1H(g){
    try {
      if (typeof fmtCoachHalfEdgeCell === 'function' && hasUsefulHtml(fmtCoachHalfEdgeCell(g))) return true;
    } catch(e) {}
    const txt = fieldText(g);
    return /coach.*1h|1h.*coach|first half|half ats/.test(txt);
  }

  function hasCoachAts(g){
    const txt = fieldText(g);
    if (/coach.*ats|ats.*coach|coach_betting|coach ats/.test(txt)) return true;
    try {
      if (typeof fmtAtsSideWithCoachHalf === 'function') {
        const probe = fmtAtsSideWithCoachHalf(g, 'probe');
        if (String(probe || '') !== 'probe' && hasUsefulHtml(probe)) return true;
      }
    } catch(e) {}
    return false;
  }

  function hasRpSupport(g){
    try {
      if (typeof rpSupportBadge === 'function') {
        if (hasUsefulHtml(rpSupportBadge(g, g.away_team))) return true;
        if (hasUsefulHtml(rpSupportBadge(g, g.home_team))) return true;
      }
    } catch(e) {}
    try {
      if (typeof rpMarketLabSupportBadgeForTeam === 'function') {
        if (hasUsefulHtml(rpMarketLabSupportBadgeForTeam(g, g.away_team))) return true;
        if (hasUsefulHtml(rpMarketLabSupportBadgeForTeam(g, g.home_team))) return true;
      }
    } catch(e) {}
    return /returning production|rp support|off_vs_def|returning_prod/.test(fieldText(g));
  }

  function hasTravel1H(g){
    try {
      if (typeof travel1hTotalBadge === 'function' && hasUsefulHtml(travel1hTotalBadge(g))) return true;
    } catch(e) {}
    const txt = fieldText(g);
    return /travel|1h travel|road fav start|road dog fade/.test(txt);
  }

  function hasLookahead(g){
    return /lookahead|look ahead|sandwich/.test(fieldText(g));
  }

  function hasB2BRoad(g){
    return /b2b road|back.?to.?back road|consecutive road|2nd straight road/.test(fieldText(g));
  }

  function hasInjury(g){
    const txt = fieldText(g);
    const score = n(g.away_injury_score) || n(g.home_injury_score) || n(g.injury_score) || n(g.game_injury_score);
    if (score && Math.abs(score) > 0) return true;
    return /injury|injuries|inj alert|injury alert|questionable|doubtful|out\b/.test(txt);
  }

  function isCoinToss(g){
    const proj = n(g.projected_margin_home);
    const market = typeof marketSpread === 'function' ? n(marketSpread(g)) : n(g.market_spread_home);
    const pRaw = n(g.win_prob_home ?? g.projected_home_win_prob ?? g.home_win_prob ?? g.projected_win_prob_home);
    const p = pRaw == null ? null : (pRaw > 1.01 ? pRaw / 100 : pRaw);

    return (
      (proj != null && Math.abs(proj) <= 3) ||
      (market != null && Math.abs(market) <= 3) ||
      (p != null && p >= 0.45 && p <= 0.55)
    );
  }

  function matchesAngle(g, angle){
    if (!angle || angle === 'all') return true;
    if (angle === 'high_variance') return maxGameVariance(g) >= 6;
    if (angle === 'medium_variance') return maxGameVariance(g) >= 3;
    if (angle === 'coach_1h') return hasCoach1H(g);
    if (angle === 'coach_ats') return hasCoachAts(g);
    if (angle === 'rp_support') return hasRpSupport(g);
    if (angle === 'travel_1h') return hasTravel1H(g);
    if (angle === 'lookahead') return hasLookahead(g);
    if (angle === 'b2b_road') return hasB2BRoad(g);
    if (angle === 'coin_toss') return isCoinToss(g);
    if (angle === 'injury') return hasInjury(g);
    if (['pbp_away_dog_move','pbp_under_move','cross_book_spread_outlier','cross_book_total_outlier'].includes(angle)) {
      return (window.normalizedAnglesForGame ? window.normalizedAnglesForGame(g, angle) : []).length > 0;
    }
    return true;
  }

  function angleLabel(angle){
    const found = ANGLES.find(x => x[0] === angle);
    return found ? found[1] : 'Selected angle';
  }

  function baseFilteredGames(){
    const weekEl = document.getElementById('fWeek');
    const confEl = document.getElementById('fConf');
    const teamEl = document.getElementById('fTeam');
    const typeEl = document.getElementById('fType');

    const week = weekEl ? weekEl.value : 'all';
    const conf = confEl ? confEl.value : 'all';
    const team = String(teamEl ? teamEl.value : '').toLowerCase().trim();
    const type = typeEl ? typeEl.value : 'all';

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

    if (type === 'conference') {
      games = games.filter(g => {
        const a = teamByName[String(g.away_team || '').toLowerCase()];
        const h = teamByName[String(g.home_team || '').toLowerCase()];
        return a && h && a.conference && a.conference === h.conference;
      });
    } else if (type === 'neutral') {
      games = games.filter(g => !!g.neutral_site);
    } else if (type === 'final') {
      games = games.filter(g => typeof gameState === 'function' && gameState(g).status === 'final');
    } else if (type === 'open') {
      games = games.filter(g => !(typeof gameState === 'function' && gameState(g).status === 'final'));
    } else if (type === 'high_variance') {
      // Backward compatibility with previous patch that added this to the type dropdown.
      games = games.filter(g => maxGameVariance(g) >= 6);
    }

    return games;
  }

  const oldRenderSchedule = window.renderSchedule || renderSchedule;
  window.renderSchedule = function(){
    let html = oldRenderSchedule();

    if (!html.includes('id="fAngle"')) {
      const angleOptions = ANGLES.map(([value,label]) =>
        `<option value="${value}">${label}</option>`
      ).join('');

      html = html.replace(
        '</select>\n    </div>\n    <div id="scheduleWrap">',
        `</select><select id="fAngle">${angleOptions}</select>\n    </div>\n    <div id="scheduleWrap">`
      );
    }

    return html;
  };

  const oldDrawScheduleTableFromCurrentFilters = window.drawScheduleTableFromCurrentFilters || drawScheduleTableFromCurrentFilters;
  window.drawScheduleTableFromCurrentFilters = function(){
    const angleEl = document.getElementById('fAngle');
    const angle = angleEl ? angleEl.value : 'all';

    if (!angleEl || angle === 'all') {
      return oldDrawScheduleTableFromCurrentFilters();
    }

    const wrap = document.getElementById('scheduleWrap');
    if (!wrap) return;

    let games = baseFilteredGames().filter(g => matchesAngle(g, angle));

    if (angle === 'high_variance' || angle === 'medium_variance') {
      games.sort((a,b) => maxGameVariance(b) - maxGameVariance(a));
    }

    const label = angleLabel(angle);
    wrap.innerHTML =
      `<div class="schedule-angle-note">Betting angle filter: <b>${label}</b> · ${games.length} matching games after week/conference/team filters.</div>` +
      scheduleTable(games, scheduleViewMode);

    if (typeof enhanceScheduleStickyHeader === 'function') {
      setTimeout(enhanceScheduleStickyHeader, 0);
    }
  };

  document.addEventListener('change', function(e){
    if (e.target && e.target.id === 'fAngle') {
      try { localStorage.setItem('ncaaf_2026_schedule_angle_filter_v1', e.target.value); } catch(err) {}
      window.drawScheduleTableFromCurrentFilters();
    }
  });

  document.addEventListener('input', function(e){
    if (e.target && e.target.id === 'fTeam') {
      const angleEl = document.getElementById('fAngle');
      if (angleEl && angleEl.value !== 'all') {
        setTimeout(window.drawScheduleTableFromCurrentFilters, 0);
      }
    }
  });

  const oldMountScheduleFilters = window.mountScheduleFilters || mountScheduleFilters;
  window.mountScheduleFilters = function(){
    oldMountScheduleFilters();

    const angleEl = document.getElementById('fAngle');
    if (angleEl) {
      try {
        const saved = localStorage.getItem('ncaaf_2026_schedule_angle_filter_v1');
        if (saved && ANGLES.some(x => x[0] === saved)) angleEl.value = saved;
      } catch(e) {}
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

    s = re.sub(r'\n<style id="schedule-betting-angle-filter-style">.*?</style>\n?', '\n', s, flags=re.S)
    s = re.sub(r'\n<script id="schedule-betting-angle-filter-js">.*?</script>\n?', '\n', s, flags=re.S)

    insert = "\n" + CSS + "\n" + JS + "\n"
    s = s.replace("</body>", insert + "\n</body>", 1)

    if s != orig:
      path.with_suffix(path.suffix + ".bak_schedule_betting_angle_filter").write_text(orig)
      path.write_text(s)
      print("patched", path)
    else:
      print("no changes", path)

def main():
    for p in TARGETS:
        patch(p)

if __name__ == "__main__":
    main()
