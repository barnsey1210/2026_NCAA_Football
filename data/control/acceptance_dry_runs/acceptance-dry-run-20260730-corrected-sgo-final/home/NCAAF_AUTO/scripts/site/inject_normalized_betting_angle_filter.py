from pathlib import Path
import re

TARGETS = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

JS = r'''
<script id="normalized-betting-angle-filter-js">
(function(){
  if (window.__normalizedBettingAngleFilterPatched) return;
  window.__normalizedBettingAngleFilterPatched = true;

  function currentAngle(){
    const el = document.getElementById('fAngle');
    return el ? el.value : 'all';
  }

  function normalizedRowsForGame(g, angle){
    const rows = window.GAME_BETTING_ANGLES || [];
    const gid = String(g?.game_id || '');
    return rows.filter(r =>
      String(r.game_id || '') === gid &&
      (!angle || angle === 'all' || String(r.angle_key || '') === String(angle))
    );
  }

  function gameMatchesNormalizedAngle(g, angle){
    if (!angle || angle === 'all') return true;
    return normalizedRowsForGame(g, angle).length > 0;
  }

  function normalizedSortScore(g, angle){
    const rows = normalizedRowsForGame(g, angle);
    if (!rows.length) return 0;
    return Math.max(...rows.map(r => Number(r.sort_score || r.metric_value || 0)));
  }

  function angleLabel(angle){
    const d = window.BETTING_ANGLE_DEFINITIONS?.[angle];
    return d?.label || angle || 'Selected angle';
  }

  function baseFilteredGamesNormalized(){
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
    }

    return games;
  }

  const previousDraw = window.drawScheduleTableFromCurrentFilters || drawScheduleTableFromCurrentFilters;
  window.drawScheduleTableFromCurrentFilters = drawScheduleTableFromCurrentFilters = function(){
    const angle = currentAngle();

    if (!angle || angle === 'all') {
      return previousDraw();
    }

    const wrap = document.getElementById('scheduleWrap');
    if (!wrap) return;

    let games = baseFilteredGamesNormalized()
      .filter(g => gameMatchesNormalizedAngle(g, angle));

    games.sort((a,b) => normalizedSortScore(b, angle) - normalizedSortScore(a, angle));

    const label = angleLabel(angle);
    wrap.innerHTML =
      `<div class="schedule-angle-note">Betting angle filter: <b>${label}</b> · ${games.length} normalized matching games after week/conference/team filters.</div>` +
      scheduleTable(games, scheduleViewMode);

    if (typeof enhanceScheduleStickyHeader === 'function') {
      setTimeout(enhanceScheduleStickyHeader, 0);
    }
  };

  // Prefer normalized reason badges when available.
  const prevAts = window.marketLabAtsMetrics || marketLabAtsMetrics;
  window.marketLabAtsMetrics = marketLabAtsMetrics = function(g){
    const out = prevAts(g);
    if (!out || !g) return out;

    const angle = currentAngle();
    if (!angle || angle === 'all') return out;

    const badge = typeof normalizedAngleReasonBadge === 'function'
      ? normalizedAngleReasonBadge(g, angle)
      : '';

    if (badge && out.side && out.side !== '—' && !String(out.side).includes('angle-reason-badge')) {
      out.side = `<div class="ats-edge-with-coach"><div>${out.side}</div>${badge}</div>`;
    }

    return out;
  };

  const prevTotal = window.marketLabTotalMetrics || marketLabTotalMetrics;
  window.marketLabTotalMetrics = marketLabTotalMetrics = function(g){
    const out = prevTotal(g);
    if (!out || !g) return out;

    const angle = currentAngle();
    if (!angle || angle === 'all') return out;

    const badge = typeof normalizedAngleReasonBadge === 'function'
      ? normalizedAngleReasonBadge(g, angle)
      : '';

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

    s = re.sub(r'\n<script id="normalized-betting-angle-filter-js">.*?</script>\n?', '\n', s, flags=re.S)

    insert = "\n" + JS + "\n"
    s = s.replace("</body>", insert + "\n</body>", 1)

    if s != orig:
        path.with_suffix(path.suffix + ".bak_normalized_betting_angle_filter").write_text(orig)
        path.write_text(s)
        print("patched", path)
    else:
        print("no changes", path)

def main():
    for p in TARGETS:
        patch(p)

if __name__ == "__main__":
    main()
