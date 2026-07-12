from pathlib import Path
import json
import re
import pandas as pd

TARGETS = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

LATEST = Path("data/ratings/ratings_latest.csv")
MASTER = Path("data/ratings/ratings_master_latest.csv")
STATUS = Path("data/ratings/ratings_source_status.csv")

SOURCE_MAP = {
    "SP+": "spplus",
    "FPI": "fpi",
    "TeamRankings": "teamrankings",
    "KFord": "kford",
    "Brad Powers": "bradpowers",
}

LABELS = {
    "spplus": "SP+",
    "fpi": "FPI",
    "teamrankings": "TeamRankings",
    "kford": "KFord",
    "bradpowers": "Brad Powers",
}

DEFAULT_WEIGHTS = {
    "spplus": 1/3,
    "fpi": 1/3,
    "teamrankings": 1/3,
    "kford": 0.0,
    "bradpowers": 0.0,
}

ACTIVE_KEYS = {"spplus", "fpi", "teamrankings"}

def clean_str(x):
    if pd.isna(x):
        return ""
    return str(x)

def build_payloads():
    latest = pd.read_csv(LATEST)
    master = pd.read_csv(MASTER)

    # Build source values from the active master first so FPI/SP+/TeamRankings
    # match the production model exactly, including new 2026 FBS teams.
    source_values = {}
    for _, r in master.iterrows():
        team = r.get("team")
        if not isinstance(team, str) or not team:
            continue
        source_values.setdefault(team, {})
        for key in ["spplus", "fpi", "teamrankings", "kford", "bradpowers"]:
            if key in r.index:
                val = r.get(key)
                source_values[team][key] = None if pd.isna(val) else round(float(val), 4)

    # Fill/refresh any source values available only in ratings_latest.csv.
    for _, r in latest.iterrows():
        key = SOURCE_MAP.get(r.get("source"))
        if not key:
            continue
        team = r.get("team")
        if not isinstance(team, str) or not team:
            continue
        source_values.setdefault(team, {})
        val = r.get("rating")
        if key not in source_values[team] or source_values[team][key] is None:
            source_values[team][key] = None if pd.isna(val) else round(float(val), 4)

    status_payload = {}
    if STATUS.exists():
        status = pd.read_csv(STATUS)
        for _, r in status.iterrows():
            key = SOURCE_MAP.get(r.get("source"))
            if not key:
                continue

            active = str(r.get("active_2026")).lower() in {"true", "1", "yes"}
            pulled = clean_str(r.get("pulled_at"))
            source_updated = clean_str(r.get("source_updated_at"))
            teams = r.get("teams")
            rows = r.get("rows")

            status_payload[key] = {
                "label": LABELS[key],
                "teams": None if pd.isna(teams) else int(teams),
                "rows": None if pd.isna(rows) else int(rows),
                "pulled_at": pulled,
                "source_updated_at": source_updated,
                "source_updated_label": source_updated if source_updated else "Not provided by source",
                "default_weight": DEFAULT_WEIGHTS.get(key, 0.0),
                "status": "Active 2026" if active else "Stale / reference only",
                "active_2026": active,
            }

    for key, label in LABELS.items():
        status_payload.setdefault(key, {
            "label": label,
            "teams": None,
            "rows": None,
            "pulled_at": "",
            "source_updated_at": "",
            "source_updated_label": "Not provided by source",
            "default_weight": DEFAULT_WEIGHTS.get(key, 0.0),
            "status": "Active 2026" if key in ACTIVE_KEYS else "Stale / reference only",
            "active_2026": key in ACTIVE_KEYS,
        })

    master_payload = {}
    for _, r in master.iterrows():
        team = r["team"]
        master_payload[team] = {
            "power_rating": None if pd.isna(r.get("power_rating")) else round(float(r.get("power_rating")), 4),
            "power_rank": None if pd.isna(r.get("power_rank")) else int(r.get("power_rank")),
            "source_count": None if pd.isna(r.get("source_count")) else int(r.get("source_count")),
            "spplus": None if pd.isna(r.get("spplus")) else round(float(r.get("spplus")), 4),
            "fpi": None if pd.isna(r.get("fpi")) else round(float(r.get("fpi")), 4),
            "teamrankings": None if pd.isna(r.get("teamrankings")) else round(float(r.get("teamrankings")), 4),
        }

    return source_values, status_payload, master_payload

def replace_const_block(s, name, payload):
    js = json.dumps(payload, separators=(",", ":"))
    pattern = re.compile(rf"const\s+{re.escape(name)}\s*=\s*.*?;\n", flags=re.S)
    repl = f"const {name} = {js};\n"
    if not pattern.search(s):
        raise RuntimeError(f"Could not find const {name}")
    return pattern.sub(repl, s, count=1)

def update_db_teams(s, master_payload):
    pattern = re.compile(r'(<script id="db" type="application/json">)(.*?)(</script>)', flags=re.S)
    m = pattern.search(s)
    if not m:
        return s

    data = json.loads(m.group(2))
    teams = data.get("teams", [])
    for t in teams:
        team = t.get("team")
        r = master_payload.get(team)
        if not r:
            continue
        if r["power_rating"] is not None:
            t["combo"] = r["power_rating"]
        if r["power_rank"] is not None:
            t["rank"] = r["power_rank"]
        t["rating_source_count"] = r["source_count"]
        t["rating_spplus"] = r["spplus"]
        t["rating_fpi"] = r["fpi"]
        t["rating_teamrankings"] = r["teamrankings"]
        t["rating_model_note"] = "Active 2026 blend: SP+ / FPI / TeamRankings"

    new_body = json.dumps(data, separators=(",", ":"))
    return s[:m.start()] + m.group(1) + new_body + m.group(3) + s[m.end():]

CSS = r'''
<style id="active-ratings-rankings-ui-style">
.active-ratings-status-grid{display:grid;grid-template-columns:repeat(5,minmax(140px,1fr));gap:10px;margin:12px 0 10px}
.active-rating-source-card{border:1px solid rgba(148,163,184,.28);border-radius:14px;padding:10px 12px;background:rgba(15,23,42,.035)}
.active-rating-source-card .src-name{font-size:13px;font-weight:1000;letter-spacing:.02em}
.active-rating-source-card .src-status{margin-top:4px;font-size:11px;font-weight:900}
.active-rating-source-card.active .src-status{color:#15803d}
.active-rating-source-card.stale .src-status{color:#b45309}
.active-rating-source-card .src-meta{margin-top:4px;font-size:10px;color:#64748b;line-height:1.35}
.production-model-note{border:1px solid rgba(22,163,74,.28);background:rgba(22,163,74,.08);border-radius:14px;padding:10px 12px;margin:10px 0;font-size:12px;color:#166534;font-weight:800}
.display-only-note{border:1px solid rgba(245,158,11,.25);background:rgba(245,158,11,.08);border-radius:12px;padding:8px 10px;margin:8px 0;font-size:11px;color:#92400e;font-weight:800}
.rank-source-val{font-weight:900;white-space:nowrap}
.rank-source-muted{color:#94a3b8;font-size:11px}
.source-col-th{font-size:11px;line-height:1.15;white-space:nowrap}
.source-col-th span{display:block;color:#64748b;font-size:9px;font-weight:800;margin-top:2px}
@media(max-width:900px){.active-ratings-status-grid{grid-template-columns:1fr 1fr}.active-rating-source-card{padding:9px}}
</style>
'''

JS = r'''
<script id="active-ratings-rankings-ui">
(function(){
  // Reset old pre-active-2026 display-lab settings once.
  // This prevents stale browser localStorage from showing SP+ 100% after production moved to active-three.
  try {
    const versionKey = 'ratingLabModelVersion';
    const currentVersion = 'active-2026-sp-fpi-teamrankings-v2-reset-display-default';
    if (localStorage.getItem(versionKey) !== currentVersion) {
      localStorage.removeItem('ratingLabWeights');
      localStorage.removeItem('ratingLabDraftWeights');
      localStorage.setItem(versionKey, currentVersion);
    }
  } catch(e) {}

  function pct(x){ return Math.round(Number(x || 0) * 1000) / 10; }
  function fmtPulled(x){
    if (!x) return 'Pulled: —';
    return 'Pulled: ' + String(x).replace('T',' ').replace('Z',' UTC');
  }
  window.ratingSourceStatusGrid = function(){
    const systems = ratingLabSystems();
    return `<div class="production-model-note">
      Production model: <b>Active 2026 ratings only</b> — SP+ 33.3% · FPI 33.3% · TeamRankings 33.3%.
      Reference/stale sources are shown for context but excluded from production projections and sims.
    </div>
    <div class="active-ratings-status-grid">
      ${systems.map(s => {
        const st = RATING_SOURCE_STATUS[s] || {};
        const active = !!st.active_2026;
        return `<div class="active-rating-source-card ${active ? 'active' : 'stale'}">
          <div class="src-name">${st.label || s}</div>
          <div class="src-status">${st.status || (active ? 'Active 2026' : 'Reference only')} · ${pct(st.default_weight)}%</div>
          <div class="src-meta">${fmtPulled(st.pulled_at)}<br>Source updated: ${st.source_updated_label || 'Not provided by source'}<br>Teams: ${st.teams ?? '—'}</div>
        </div>`;
      }).join('')}
    </div>`;
  };

  window.ratingsWeightLabPanel = function() {
    const w = getRatingLabWeights();
    const officialTotal = ratingLabSystems().reduce((sum,s)=>sum + Number(DEFAULT_RATING_WEIGHTS[s] || 0), 0);
    const labTotal = ratingLabSystems().reduce((sum,s)=>sum + Number(w[s] || 0), 0);
    const rows = ratingLabSystems().map(s => {
      const pctVal = Math.round(Number(w[s] || 0) * 100);
      const defaultPct = Math.round(Number(DEFAULT_RATING_WEIGHTS[s] || 0) * 100);
      const st = RATING_SOURCE_STATUS[s] || {};
      return `<div class="rating-weight-row compact">
        <div class="rating-weight-label">
          <b>${ratingLabLabel(s)}</b>
          <span>${pctVal}% custom · ${defaultPct}% production · ${st.status || ''} · ${st.source_updated_label || 'Source date unavailable'}</span>
        </div>
        <div class="rating-weight-controls">
          <input id="ratingLabSlider_${s}" type="range" min="0" max="100" value="${pctVal}" oninput="setRatingLabDraftPct('${s}', this.value)">
          <input id="ratingLabInput_${s}" class="rating-weight-input" type="number" min="0" max="100" step="1" value="${pctVal}" oninput="setRatingLabDraftPct('${s}', this.value)">
        </div>
        <div id="ratingLabPct_${s}" class="rating-weight-pct">${pctVal}%</div>
      </div>`;
    }).join('');
    const isOpen = localStorage.getItem('ratingLabOpen') === '1';
    return `<details id="ratingsWeightLab" class="card ratings-weight-lab compact" ${isOpen ? 'open' : ''} ontoggle="localStorage.setItem('ratingLabOpen', this.open ? '1' : '0')">
      <summary>
        <div>
          <b>Display-only Rating Lab</b>
          <span class="small muted">Production/default: ${ratingLabDefaultWeightSummaryText()} · click to expand</span>
        </div>
        <span class="rating-lab-summary-pill">Custom ${Math.round(labTotal*100)}% · Production ${Math.round(officialTotal*100)}%</span>
      </summary>
      <div class="display-only-note">Manual sliders update this Rankings page only. Season simulations, win totals, conference futures, and schedule edges use the latest production rebuild.</div>
      <div class="rating-weight-total">Draft total: <span id="ratingLabDraftTotal">${Math.round(labTotal*100)}%</span></div>
      ${rows}
      <div class="rating-weight-actions">
        <button class="pill" onclick="applyRatingLabDraftWeights()">Apply Display Weights</button>
        <button class="pill" onclick="scaleRatingLabDraftTo100()">Scale Draft to 100%</button>
        <button class="pill" onclick="resetRatingLabWeights()">Reset to Production Default</button>
      </div>
    </details>`;
  };

  window.sourceRatingCell = function(teamName, key) {
    const vals = RATING_SOURCE_VALUES[teamName] || {};
    const v = vals[key];
    if (v == null || !Number.isFinite(Number(v))) return '<span class="rank-source-muted">—</span>';
    return `<span class="rank-source-val">${Number(v).toFixed(1)}</span>`;
  };

  window.rankingsPowerRatingCell = function(t) {
    const useLab = !ratingLabWeightsAreDefault();
    if (!useLab) {
      return `<div class="rankings-power-cell">
        <div>${rankValueColored(Number(t.combo).toFixed(1), comboRankByTeam[t.team])}</div>
        <div class="small muted">active 2026 blend · ${t.rating_source_count || 3}/3</div>
      </div>`;
    }

    const r = calcRatingLab(t.team);
    const ranks = ratingLabRanks();
    if (!r || r.rating == null) return rankValueColored(Number(t.combo).toFixed(1), comboRankByTeam[t.team]);

    return `<div class="rankings-power-cell">
      <div>${rankValueColored(Number(r.rating).toFixed(1), ranks[t.team])}</div>
      <div class="small muted">production: ${Number(t.combo).toFixed(1)} (#${comboRankByTeam[t.team] || '—'})</div>
    </div>`;
  };

  window.renderRankings = function() {
    const rankTeams = sortedRankTeams();
    return `
      <div class="page-title">Rankings</div>
      <div class="page-sub">Production rankings use active 2026 ratings only. Manual sliders are display-only and do not update simulations unless the site is rebuilt.</div>
      <div class="mobile-actions">
        <a class="pill" href="#schedule">Schedule</a>
        <a class="pill" href="#conferences">Conferences</a>
      </div>
      ${ratingSourceStatusGrid()}
      <div class="rank-sort-controls">
        <select id="rankSortSelect">
          ${Object.entries(rankSortLabels).map(([key,label])=>`<option value="${key}">Sort by ${label}</option>`).join('')}
        </select>
        <button id="rankSortDirBtn" type="button">${rankSortState.dir === 'asc' ? 'Ascending' : 'Descending'}</button>
      </div>
      <div class="card desktop-rankings market-board-card" style="margin-top:16px">
        ${ratingsWeightLabPanel()}
        <table><thead><tr>
          ${sortableTh('rank','Rank')}
          ${sortableTh('team','Team')}
          ${sortableTh('conference','Conference')}
          ${rankingsPowerRatingTh('combo','Power Rating')}
          <th class="source-col-th">SP+<span>active</span></th>
          <th class="source-col-th">FPI<span>active</span></th>
          <th class="source-col-th">TeamRankings<span>active</span></th>
          ${sortableTh('sp_offense','SP Off')}
          ${sortableTh('sp_defense','SP Def')}
          ${sortableTh('hfa','HFA')}
          ${sortableTh('overall_sos','OVR SOS')}
          ${sortableTh('conf_sos','CONF SOS')}
          ${sortableTh('avg_total_wins','Avg Wins')}
        </tr></thead><tbody>
        ${rankTeams.map(t=>`<tr>
          <td>${t.rank}</td>
          <td>${linkTeam(t.team)}</td>
          <td>${linkConf(t.conference)}</td>
          <td>${rankingsPowerRatingCell(t)}</td>
          <td>${sourceRatingCell(t.team,'spplus')}</td>
          <td>${sourceRatingCell(t.team,'fpi')}</td>
          <td>${sourceRatingCell(t.team,'teamrankings')}</td>
          <td>${rankValueColored(Number(t.sp_offense).toFixed(1), spOffRankByTeam[t.team])}</td>
          <td>${rankValueColored(Number(t.sp_defense).toFixed(1), spDefRankByTeam[t.team])}</td>
          <td>${rankValueColored(Number(t.hfa).toFixed(1), hfaRankByTeam[t.team])}</td>
          <td>${rankValueColored(fmtSOS(overallSOSByTeam[t.team]), overallSOSRankByTeam[t.team], '', true, 138)}</td>
          <td>${rankValueColored(fmtSOS(confSOSByTeam[t.team]), confSOSRankByTeam[t.team], t.conference && t.conference !== 'Independent' ? ' conf' : '', true, 18)}</td>
          <td>${rankValueColored(Number(t.avg_total_wins).toFixed(2), avgWinsRankByTeam[t.team])}</td>
        </tr>`).join('')}
        </tbody></table>
      </div>
      <div class="card mobile-rankings" style="margin-top:12px">
        ${rankTeams.map(renderRankMobileCard).join('')}
      </div>
    `;
  };

  if ((location.hash || '') === '#rankings' && typeof route === 'function') {
    setTimeout(route, 0);
  }
})();
</script>
'''

def inject_css_js(s):
    s = re.sub(r"\n<style id=\"active-ratings-rankings-ui-style\">.*?</style>\n?", "\n", s, flags=re.S)
    s = re.sub(r"\n<script id=\"active-ratings-rankings-ui\">.*?</script>\n?", "\n", s, flags=re.S)

    insert = "\n" + CSS + "\n" + JS + "\n"
    if "</body>" not in s:
        return s + insert
    return s.replace("</body>", insert + "\n</body>", 1)

def patch_file(path, source_values, status_payload, master_payload):
    if not path.exists():
        print("missing", path)
        return

    s = path.read_text(errors="ignore")
    original = s

    s = update_db_teams(s, master_payload)
    s = replace_const_block(s, "RATING_SOURCE_VALUES", source_values)
    s = replace_const_block(s, "RATING_SOURCE_STATUS", status_payload)
    s = replace_const_block(s, "DEFAULT_RATING_WEIGHTS", DEFAULT_WEIGHTS)
    s = inject_css_js(s)

    if s != original:
        bak = path.with_suffix(path.suffix + ".bak_active_ratings_rankings_ui")
        bak.write_text(original)
        path.write_text(s)
        print("patched", path)
    else:
        print("no changes", path)

def main():
    source_values, status_payload, master_payload = build_payloads()
    for p in TARGETS:
        patch_file(p, source_values, status_payload, master_payload)

if __name__ == "__main__":
    main()
