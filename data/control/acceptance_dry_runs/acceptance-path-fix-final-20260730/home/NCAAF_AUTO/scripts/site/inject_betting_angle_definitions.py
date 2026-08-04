from pathlib import Path
import json
import re
import pandas as pd

TARGETS = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

DEFS = Path("data/signals/betting_angle_definitions_2026.json")
ANGLES = Path("data/signals/game_betting_angles_2026.csv")

CSS = r'''
<style id="betting-angle-definitions-style">
.betting-angle-definitions-card{
  border:1px solid rgba(148,163,184,.28);
  border-radius:16px;
  padding:12px 14px;
  margin:10px 0 12px;
  background:rgba(15,23,42,.22);
}
.betting-angle-definitions-card summary{
  cursor:pointer;
  font-weight:1000;
  font-size:13px;
}
.betting-angle-definitions-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(220px,1fr));
  gap:8px;
  margin-top:10px;
}
.betting-angle-definition{
  border:1px solid rgba(148,163,184,.22);
  border-radius:12px;
  padding:9px 10px;
  background:rgba(15,23,42,.18);
  font-size:11px;
  line-height:1.35;
}
.betting-angle-definition b{
  display:block;
  color:#f8fafc;
  font-size:12px;
  margin-bottom:3px;
}
.betting-angle-definition .threshold{
  color:#fde68a;
  font-weight:900;
  margin-top:4px;
}
.betting-angle-definition .meaning{
  color:#cbd5e1;
  margin-top:4px;
}
.betting-angle-definition .evidence{
  color:#93c5fd;
  font-weight:900;
  margin-top:4px;
}
@media(max-width:900px){.betting-angle-definitions-grid{grid-template-columns:1fr}}
</style>
'''

JS_TEMPLATE = r'''
<script id="betting-angle-definitions-js">
const BETTING_ANGLE_DEFINITIONS = __DEFS__;
const GAME_BETTING_ANGLES = __ANGLES__;
window.BETTING_ANGLE_DEFINITIONS = BETTING_ANGLE_DEFINITIONS;
window.GAME_BETTING_ANGLES = GAME_BETTING_ANGLES;

(function(){
  function esc(s){
    return String(s ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  }

  window.bettingAngleDefinitionsCard = function(){
    const keys = [
      'high_variance','medium_variance','coin_toss','coach_1h','coach_ats',
      'rp_support','travel_1h','lookahead','b2b_road','injury','market_move'
      ,'pbp_away_dog_move','pbp_under_move'
      ,'cross_book_spread_outlier','cross_book_total_outlier'
      ,'postgame_spread_repricing','postgame_total_repricing'
    ];

    return `<details class="betting-angle-definitions-card">
      <summary>Betting angle definitions / thresholds</summary>
      <div class="betting-angle-definitions-grid">
        ${keys.map(k => {
          const d = BETTING_ANGLE_DEFINITIONS[k] || {};
          return `<div class="betting-angle-definition">
            <b>${esc(d.label || k)}</b>
            <div>${esc(d.definition || '')}</div>
            <div class="threshold">Threshold: ${esc(d.threshold || '—')}</div>
            ${d.evidence_status ? `<div class="evidence">Evidence: ${esc(d.evidence_status)}</div>` : ''}
            <div class="meaning">${esc(d.meaning || '')}</div>
          </div>`;
        }).join('')}
      </div>
    </details>`;
  };

  window.normalizedAnglesForGame = function(g, angleKey){
    const gid = String(g?.game_id || '');
    return GAME_BETTING_ANGLES.filter(a =>
      String(a.game_id || '') === gid &&
      (!angleKey || angleKey === 'all' || String(a.angle_key || '') === String(angleKey))
    );
  };

  window.normalizedAngleReasonBadge = function(g, angleKey){
    const rows = window.normalizedAnglesForGame ? window.normalizedAnglesForGame(g, angleKey) : [];
    if (!rows.length) return '';
    const r = rows[0];
    const tier = String(r.tier || '').toLowerCase();
    const cls = tier === 'high' ? 'hot' : tier === 'medium' ? 'warn' : '';
    const label = r.angle_label || r.angle_key || 'Angle';
    const reason = r.reason || '';
    let shortText = label;
    if (r.angle_key === 'high_variance' || r.angle_key === 'medium_variance') {
      // Variance is already shown in the team cells and ATS edge as model-variance badges.
      // Do not duplicate another angle badge in the ATS Edge cell.
      return '';
    } else if (r.angle_key === 'coin_toss') {
      shortText = 'Coin toss / near pick';
    } else if (r.angle_key === 'coach_1h') {
      shortText = 'Coach 1H support';
    } else if (r.angle_key === 'coach_ats') {
      shortText = 'Coach ATS support';
    } else if (r.angle_key === 'rp_support') {
      shortText = 'Returning production support';
    } else if (r.angle_key === 'travel_1h') {
      shortText = 'Travel / 1H angle';
    } else if (r.angle_key === 'lookahead') {
      shortText = 'Lookahead spot';
    } else if (r.angle_key === 'b2b_road') {
      shortText = 'B2B road spot';
    } else if (r.angle_key === 'injury') {
      shortText = 'Injury alert';
    } else if (r.angle_key === 'pbp_away_dog_move') {
      shortText = 'PBP move: away dog';
    } else if (r.angle_key === 'pbp_under_move') {
      shortText = 'PBP move: under';
    } else if (r.angle_key === 'cross_book_spread_outlier') {
      shortText = 'Stale opener: spread';
    } else if (r.angle_key === 'cross_book_total_outlier') {
      shortText = 'Stale opener: total';
    }
    return `<div><span class="angle-reason-badge ${cls}" title="${esc(reason)}">${esc(shortText)}</span></div>`;
  };

  const oldRenderSchedule = window.renderSchedule || renderSchedule;
  window.renderSchedule = function(){
    let html = oldRenderSchedule();
    const card = typeof bettingAngleDefinitionsCard === 'function' ? bettingAngleDefinitionsCard() : '';
    if (card && html.includes('<div id="scheduleFilterStrip"') && !html.includes('Betting angle definitions / thresholds')) {
      html = html.replace('<div id="scheduleFilterStrip"', card + '\n<div id="scheduleFilterStrip"');
    }
    return html;
  };

  if ((location.hash || '') === '#schedule' && typeof route === 'function') {
    setTimeout(route, 0);
  }
})();
</script>
'''

def load_angles():
    if not ANGLES.exists():
        return []
    df = pd.read_csv(ANGLES)
    rows = []
    for _, r in df.iterrows():
        obj = {}
        for c in df.columns:
            v = r[c]
            if pd.isna(v):
                obj[c] = ""
            elif isinstance(v, (int, float)):
                obj[c] = float(v)
            else:
                obj[c] = str(v)
        rows.append(obj)
    return rows

def patch(path):
    if not path.exists():
        print("missing", path)
        return

    defs = json.loads(DEFS.read_text())
    angles = load_angles()

    s = path.read_text(errors="ignore")
    orig = s

    s = re.sub(r'\n<style id="betting-angle-definitions-style">.*?</style>\n?', '\n', s, flags=re.S)
    s = re.sub(r'\n<script id="betting-angle-definitions-js">.*?</script>\n?', '\n', s, flags=re.S)

    js = JS_TEMPLATE.replace("__DEFS__", json.dumps(defs, separators=(",", ":"))).replace("__ANGLES__", json.dumps(angles, separators=(",", ":")))
    insert = "\n" + CSS + "\n" + js + "\n"

    s = s.replace("</body>", insert + "\n</body>", 1)

    if s != orig:
        path.with_suffix(path.suffix + ".bak_betting_angle_definitions").write_text(orig)
        path.write_text(s)
        print("patched", path, "angles:", len(angles))
    else:
        print("no changes", path)

def main():
    for p in TARGETS:
        patch(p)

if __name__ == "__main__":
    main()
