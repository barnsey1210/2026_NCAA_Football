from pathlib import Path
import json
import re
import pandas as pd

TARGETS = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

VAR = Path("data/ratings/ratings_system_variance.csv")
CFG = Path("data/projections/game_projection_blend_config.json")

CSS = r'''
<style id="schedule-model-context-style">
.model-context-card{border:1px solid rgba(148,163,184,.28);border-radius:16px;padding:12px 14px;margin:12px 0;background:rgba(15,23,42,.22)}
.model-context-title{font-weight:1000;font-size:14px;margin-bottom:6px}
.model-context-grid{display:grid;grid-template-columns:repeat(4,minmax(120px,1fr));gap:8px}
.model-context-pill{border:1px solid rgba(148,163,184,.25);border-radius:12px;padding:8px 10px;background:rgba(15,23,42,.18);font-size:11px;font-weight:850;color:#cbd5e1}
.model-context-pill b{display:block;color:#f8fafc;font-size:12px}
.variance-badge{display:inline-flex;align-items:center;gap:4px;border-radius:999px;padding:3px 7px;font-size:10px;font-weight:1000;border:1px solid rgba(148,163,184,.25);white-space:nowrap}
.variance-badge.low{background:rgba(22,163,74,.13);color:#86efac;border-color:rgba(34,197,94,.35)}
.variance-badge.medium{background:rgba(245,158,11,.14);color:#fde68a;border-color:rgba(245,158,11,.38)}
.variance-badge.high{background:rgba(239,68,68,.14);color:#fecaca;border-color:rgba(239,68,68,.40)}
.lab-spread-note{display:block;margin-top:3px;font-size:10px;font-weight:900;color:#93c5fd}
.lab-spread-note strong{color:#dbeafe}
@media(max-width:900px){.model-context-grid{grid-template-columns:1fr 1fr}}
</style>
'''

HELPER_JS = r'''
(function(){
  function pct(x){ return `${Math.round(Number(x || 0) * 100)}%`; }
  function fmtNum(x, d=1){
    const n = Number(x);
    return Number.isFinite(n) ? n.toFixed(d) : '—';
  }
  function spreadText(homeTeam, awayTeam, margin){
    const n = Number(margin);
    if (!Number.isFinite(n)) return '—';
    const fav = n >= 0 ? homeTeam : awayTeam;
    return `${fav} -${Math.abs(n).toFixed(1)}`;
  }

  window.ratingVarianceBadge = function(team){
    const v = RATING_VARIANCE_BY_TEAM[team];
    if (!v) return '';
    const tier = v.rating_variance_tier || 'missing';
    const label = tier === 'high' ? 'High variance' : tier === 'medium' ? 'Med variance' : 'Low variance';
    return `<span class="variance-badge ${tier}" title="SP+/FPI/TeamRankings range ${fmtNum(v.rating_range)} pts. High: ${v.highest_source || '—'}, Low: ${v.lowest_source || '—'}">${label} ${fmtNum(v.rating_range)}</span>`;
  };

  window.gameVarianceBadge = function(g){
    if (!g) return '';
    const a = RATING_VARIANCE_BY_TEAM[g.away_team];
    const h = RATING_VARIANCE_BY_TEAM[g.home_team];
    const maxRange = Math.max(Number(a?.rating_range || 0), Number(h?.rating_range || 0));
    const tier = maxRange >= 6 ? 'high' : maxRange >= 3 ? 'medium' : 'low';
    const label = tier === 'high' ? 'High model variance' : tier === 'medium' ? 'Med model variance' : 'Low model variance';
    return `<span class="variance-badge ${tier}" title="${g.away_team} range ${fmtNum(a?.rating_range)}; ${g.home_team} range ${fmtNum(h?.rating_range)}">${label} ${fmtNum(maxRange)}</span>`;
  };

  window.labSpreadForGame = function(g){
    if (!g || typeof gameHomeMarginLab !== 'function') return null;
    const lab = gameHomeMarginLab(g);
    return Number.isFinite(Number(lab)) ? Number(lab) : null;
  };

  window.labSpreadNoteForGame = function(g){
    if (!g || typeof ratingLabWeightsAreDefault !== 'function' || ratingLabWeightsAreDefault()) return '';
    const lab = labSpreadForGame(g);
    const prod = Number(g.projected_margin_home);
    if (!Number.isFinite(lab) || !Number.isFinite(prod)) return '';
    const delta = lab - prod;
    return `<span class="lab-spread-note">Lab: <strong>${spreadText(g.home_team,g.away_team,lab)}</strong> · Δ ${delta >= 0 ? '+' : ''}${delta.toFixed(1)} vs production</span>`;
  };

  window.scheduleTotalsModelStatusCard = function(){
    const tw = GAME_PROJECTION_BLEND_CONFIG.total_weights || {};
    return `<div class="model-context-card" id="scheduleTotalsModelStatusCard">
      <div class="model-context-title">Totals projection model</div>
      <div class="model-context-grid">
        <div class="model-context-pill"><b>Site Projection / SP+ baseline</b>${pct(tw['Site Projection'])} active</div>
        <div class="model-context-pill"><b>Massey totals</b>${pct(tw['Massey Games'])} reference only</div>
        <div class="model-context-pill"><b>DRatings totals</b>${pct(tw['DRatings Predictions'])} unavailable</div>
        <div class="model-context-pill"><b>Sagarin totals</b>${pct(tw['Sagarin Predictor Prediction'])} unavailable</div>
      </div>
    </div>`;
  };

  window.scheduleSpreadModelStatusCard = function(){
    return `<div class="model-context-card" id="scheduleSpreadModelStatusCard">
      <div class="model-context-title">Spread projection model</div>
      <div class="model-context-grid">
        <div class="model-context-pill"><b>Production spread</b>Active 2026 blend: SP+ 33.3% · FPI 33.3% · TeamRankings 33.3%</div>
        <div class="model-context-pill"><b>Display sliders</b>What-if spread impact only. Does not update futures or simulations.</div>
        <div class="model-context-pill"><b>Model variance</b>Green &lt;3 pts · Yellow 3–6 · Red 6+ across active systems</div>
        <div class="model-context-pill"><b>Totals</b>Separate model. Currently Site Projection / SP+ baseline 100%.</div>
      </div>
    </div>`;
  };
})();
'''

def build_variance_payload():
    df = pd.read_csv(VAR)
    payload = {}
    for _, r in df.iterrows():
        payload[str(r["team"])] = {
            "rating_range": None if pd.isna(r.get("rating_range")) else round(float(r.get("rating_range")), 3),
            "rating_stddev": None if pd.isna(r.get("rating_stddev")) else round(float(r.get("rating_stddev")), 3),
            "rating_variance_tier": "" if pd.isna(r.get("rating_variance_tier")) else str(r.get("rating_variance_tier")),
            "highest_source": "" if pd.isna(r.get("highest_source")) else str(r.get("highest_source")),
            "lowest_source": "" if pd.isna(r.get("lowest_source")) else str(r.get("lowest_source")),
        }
    return payload

def build_config_payload():
    if CFG.exists():
        return json.loads(CFG.read_text())
    return {"spread_weights": {"Site Projection": 1.0}, "total_weights": {"Site Projection": 1.0}}

def patch(path, variance_payload, cfg_payload):
    if not path.exists():
        print("missing", path)
        return

    s = path.read_text(errors="ignore")
    orig = s

    # Remove bad or old injected pieces.
    s = re.sub(r'\s*const\s+RATING_VARIANCE_BY_TEAM\s*=\s*.*?;\s*', '', s, flags=re.S)
    s = re.sub(r'\s*const\s+GAME_PROJECTION_BLEND_CONFIG\s*=\s*.*?;\s*', '', s, flags=re.S)
    s = re.sub(r'\n<style id="schedule-model-context-style">.*?</style>\n?', '\n', s, flags=re.S)
    s = re.sub(r'\n<script id="schedule-model-context-js">.*?</script>\n?', '\n', s, flags=re.S)

    js = (
        '<script id="schedule-model-context-js">\n'
        f'const RATING_VARIANCE_BY_TEAM = {json.dumps(variance_payload, separators=(",", ":"))};\n'
        f'const GAME_PROJECTION_BLEND_CONFIG = {json.dumps(cfg_payload, separators=(",", ":"))};\n'
        + HELPER_JS +
        '\n</script>'
    )

    insert = "\n" + CSS + "\n" + js + "\n"
    if "</body>" in s:
        s = s.replace("</body>", insert + "\n</body>", 1)
    else:
        s += insert

    if s != orig:
        path.with_suffix(path.suffix + ".bak_schedule_model_context").write_text(orig)
        path.write_text(s)
        print("patched", path)
    else:
        print("no changes", path)

def main():
    variance_payload = build_variance_payload()
    cfg_payload = build_config_payload()
    for p in TARGETS:
        patch(p, variance_payload, cfg_payload)

if __name__ == "__main__":
    main()
