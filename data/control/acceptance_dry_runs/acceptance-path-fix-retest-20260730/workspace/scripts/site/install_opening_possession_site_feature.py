import csv
import json
import re
from pathlib import Path

INDEX = Path("index.html")
COACH_CSV = Path("coach_opening_possession_tendency_2026.csv")

if not INDEX.exists():
    raise SystemExit("index.html not found")

if not COACH_CSV.exists():
    raise SystemExit("coach_opening_possession_tendency_2026.csv not found")

html = INDEX.read_text(errors="ignore")

# ----------------------------
# Embed CSV data into DB
# ----------------------------
m = re.search(r'(<script id="db" type="application/json">)(.*?)(</script>)', html, flags=re.S)
if not m:
    raise SystemExit("Could not find embedded DB script")

db = json.loads(m.group(2))

with COACH_CSV.open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

def clean_num(v):
    if v is None or v == "":
        return None
    try:
        if "." in str(v):
            return float(v)
        return int(v)
    except Exception:
        return v

cleaned = []
for r in rows:
    out = {}
    for k, v in r.items():
        if k in {
            "toss_wins", "receive_take_ball", "defer", "kick", "defend",
            "receive_pct", "defer_pct", "kick_defend_pct"
        }:
            out[k] = clean_num(v)
        else:
            out[k] = v
    cleaned.append(out)

db["coach_opening_possession_tendency_2026"] = cleaned

new_db = json.dumps(db, separators=(",", ":"))
html = html[:m.start(2)] + new_db + html[m.end(2):]

# ----------------------------
# Remove old install if present
# ----------------------------
html = re.sub(
    r'\s*<script>\s*\(function openingPossessionSiteFeature\(\)\{[\s\S]*?\}\)\(\);\s*</script>\s*',
    "\n",
    html,
    flags=re.S
)

html = re.sub(
    r'\s*<style>\s*/\* Opening possession / coin toss feature \*/[\s\S]*?</style>\s*',
    "\n",
    html,
    flags=re.S
)

# ----------------------------
# Add CSS
# ----------------------------
css = r'''
<style>
/* Opening possession / coin toss feature */
.coach-toss-dashboard-box{
  margin-top:14px;
  padding:12px 14px;
  border:1px solid rgba(147,197,253,.20);
  border-radius:14px;
  background:rgba(15,23,42,.42);
}
.coach-toss-dashboard-title{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  margin-bottom:9px;
  color:#dbeafe;
  font-size:12px;
  font-weight:950;
  letter-spacing:.08em;
  text-transform:uppercase;
}
.coach-toss-dashboard-title span{
  color:#9fb3d9;
  font-size:11px;
  font-weight:850;
  letter-spacing:0;
  text-transform:none;
}
.coach-toss-grid{
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:8px;
}
.coach-toss-kpi{
  border:1px solid rgba(148,163,184,.16);
  border-radius:12px;
  background:rgba(255,255,255,.035);
  padding:9px 10px;
}
.coach-toss-kpi .label{
  color:#9fb3d9;
  font-size:10px;
  font-weight:950;
  letter-spacing:.07em;
  text-transform:uppercase;
}
.coach-toss-kpi .value{
  color:#f8fafc;
  font-size:16px;
  font-weight:950;
  margin-top:4px;
}
.coach-toss-kpi .value.good{color:#4ade80}
.coach-toss-kpi .value.warn{color:#facc15}
.coach-toss-note{
  margin-top:8px;
  color:#9fb3d9;
  font-size:11px;
  line-height:1.3;
  font-weight:750;
}
.open-pos-context-main{
  color:#f8fafc;
  font-weight:950;
}
.open-pos-context-sub{
  display:block;
  color:#9fb3d9;
  font-size:11px;
  line-height:1.25;
  margin-top:3px;
}
@media(max-width:800px){
  .coach-toss-grid{grid-template-columns:1fr}
}
</style>
'''

if "Opening possession / coin toss feature" not in html:
    html = html.replace("</head>", css + "\n</head>")

# ----------------------------
# Add JS
# ----------------------------
js = r'''
<script>
(function openingPossessionSiteFeature(){
  function clean(s){
    return String(s || '').replace(/\s+/g,' ').trim();
  }

  function rows(){
    return (window.DB && DB.coach_opening_possession_tendency_2026) || [];
  }

  function lower(s){
    return clean(s).toLowerCase();
  }

  function pct(x){
    const n = Number(x);
    return Number.isFinite(n) ? `${n.toFixed(1)}%` : '—';
  }

  function num(x){
    const n = Number(x);
    return Number.isFinite(n) ? n : 0;
  }

  function findByTeam(team){
    const key = lower(team);
    return rows().find(r => lower(r.team) === key) || null;
  }

  function findByCoach(coach, team){
    const coachKey = lower(coach);
    const teamKey = lower(team);
    let hit = rows().find(r => lower(r.head_coach) === coachKey && (!teamKey || lower(r.team) === teamKey));
    if (!hit) hit = rows().find(r => lower(r.head_coach) === coachKey);
    return hit || null;
  }

  function receiveProb(my, opp){
    if (!my || !opp) return null;
    const a = Number(my.receive_pct);
    const b = Number(opp.defer_pct);
    if (!Number.isFinite(a) || !Number.isFinite(b)) return null;
    return Math.round(((a + b) / 2) * 10) / 10;
  }

  function edgeMarks(diff){
    const d = Math.abs(diff);
    if (d >= 25) return '✓✓✓';
    if (d >= 15) return '✓✓';
    if (d >= 8) return '✓';
    return '';
  }

  function edgeBadge(team, marks){
    if (!marks) return '<span class="cfb-edge-pill even">—</span>';
    if (typeof cfbEdgeBadge === 'function') return cfbEdgeBadge(team, marks.length, 'away');
    return `<span class="cfb-edge-pill edge-away">${team} ${marks}</span>`;
  }

  function dash(){
    return '<span class="cfb-edge-pill even">—</span>';
  }

  function teamValueHtml(row, prob){
    if (!row) {
      return `<span class="open-pos-context-main">No sample</span>`;
    }
    const tendency = clean(row.opening_possession_tendency || 'Mixed');
    const tossWins = num(row.toss_wins);
    const recv = num(row.receive_take_ball);
    const defer = num(row.defer);
    return `<span class="open-pos-context-main">${tendency}</span>
      <span class="open-pos-context-sub">Won toss ${tossWins}x · receive ${recv}/${tossWins} (${pct(row.receive_pct)}) · defer ${defer}/${tossWins} (${pct(row.defer_pct)})</span>
      <span class="open-pos-context-sub">Projected receive opening kick: ${prob == null ? '—' : pct(prob)}</span>`;
  }

  function addMatchupRows(){
    document.querySelectorAll('.cfb-context-table').forEach(table => {
      if (table.dataset.openingPossessionAdded === '1') return;

      const theadCells = Array.from(table.querySelectorAll('thead th')).map(th => clean(th.textContent));
      const tbody = table.querySelector('tbody');
      if (!tbody || theadCells.length < 4) return;

      let split = false;
      let away = '';
      let home = '';

      // Split layout: Away Edge | Away | Metric | Home | Home Edge
      if (theadCells.length >= 5 && /metric/i.test(theadCells[2])) {
        split = true;
        away = clean(theadCells[1]);
        home = clean(theadCells[3]);
      } else {
        // Old layout: Category | Away | Home | Edge
        away = clean(theadCells[1]);
        home = clean(theadCells[2]);
      }

      if (!away || !home || away.toLowerCase().includes('edge') || home.toLowerCase().includes('edge')) return;

      const a = findByTeam(away);
      const h = findByTeam(home);
      const aProb = receiveProb(a, h);
      const hProb = receiveProb(h, a);

      let aEdge = dash();
      let hEdge = dash();
      let singleEdge = dash();

      if (aProb != null && hProb != null) {
        const diff = aProb - hProb;
        const marks = edgeMarks(diff);
        if (marks && diff > 0) {
          aEdge = edgeBadge(away, marks);
          singleEdge = aEdge;
        } else if (marks && diff < 0) {
          hEdge = edgeBadge(home, marks);
          singleEdge = hEdge;
        }
      }

      let html = '';
      if (split) {
        html = `<tr>
          <td class="cfb-edge-cell cfb-context-away-edge">${aEdge}</td>
          <td class="cfb-context-team-val">${teamValueHtml(a, aProb)}</td>
          <td class="cfb-context-cat">Opening Possession</td>
          <td class="cfb-context-team-val">${teamValueHtml(h, hProb)}</td>
          <td class="cfb-edge-cell cfb-context-home-edge">${hEdge}</td>
        </tr>`;
      } else {
        html = `<tr>
          <td>Opening Possession</td>
          <td>${teamValueHtml(a, aProb)}</td>
          <td>${teamValueHtml(h, hProb)}</td>
          <td>${singleEdge}</td>
        </tr>`;
      }

      tbody.insertAdjacentHTML('afterbegin', html);
      table.dataset.openingPossessionAdded = '1';
    });
  }

  function findCoachName(card){
    const trs = Array.from(card.querySelectorAll('tr'));
    for (const tr of trs) {
      const cells = Array.from(tr.children);
      if (cells.length >= 2 && /^head coach$/i.test(clean(cells[0].textContent))) {
        return clean(cells[1].textContent);
      }
    }
    const txt = clean(card.textContent);
    const m = txt.match(/Head Coach\s+(.+?)\s+Tracked Teams/i);
    return m ? clean(m[1]) : '';
  }

  function findDashboardTeam(){
    const title = clean(document.querySelector('.page-title')?.textContent || '');
    if (title) return title.replace(/\s+Team Dashboard$/i,'').trim();
    return '';
  }

  function renderDashboardBox(row){
    if (!row) {
      return `<div class="coach-toss-dashboard-box">
        <div class="coach-toss-dashboard-title">Coin Toss / Opening Possession</div>
        <div class="coach-toss-note">No explicit ESPN toss-decision sample found for this current coach.</div>
      </div>`;
    }

    const tossWins = num(row.toss_wins);
    const receive = num(row.receive_take_ball);
    const defer = num(row.defer);
    const tendency = clean(row.opening_possession_tendency || 'Mixed');
    const confidence = clean(row.confidence || '');
    const teams = clean(row.teams_in_sample || '');
    const seasons = clean(row.seasons || '');

    const tendencyClass = tendency.toLowerCase().includes('take-ball') ? 'good'
      : tendency.toLowerCase().includes('defer') ? 'warn'
      : '';

    return `<div class="coach-toss-dashboard-box">
      <div class="coach-toss-dashboard-title">
        <div>Coin Toss / Opening Possession</div>
        <span>${confidence ? `Confidence: ${confidence}` : 'Explicit ESPN sample'}</span>
      </div>
      <div class="coach-toss-grid">
        <div class="coach-toss-kpi">
          <div class="label">Tendency</div>
          <div class="value ${tendencyClass}">${tendency}</div>
        </div>
        <div class="coach-toss-kpi">
          <div class="label">Take ball</div>
          <div class="value">${receive}/${tossWins} · ${pct(row.receive_pct)}</div>
        </div>
        <div class="coach-toss-kpi">
          <div class="label">Defer</div>
          <div class="value">${defer}/${tossWins} · ${pct(row.defer_pct)}</div>
        </div>
      </div>
      <div class="coach-toss-note">
        Won toss sample: <b>${tossWins}</b>${seasons ? ` · Seasons: ${seasons}` : ''}${teams ? ` · Sample teams: ${teams}` : ''}. 
        Source: explicit ESPN toss rows matched to exact team-season head coach.
      </div>
    </div>`;
  }

  function addDashboardBox(){
    document.querySelectorAll('.card').forEach(card => {
      const text = clean(card.textContent);
      if (!text.includes('Head Coach Betting Trends')) return;
      if (card.querySelector('.coach-toss-dashboard-box')) return;

      const coach = findCoachName(card);
      const team = findDashboardTeam();
      const row = findByCoach(coach, team);

      card.insertAdjacentHTML('beforeend', renderDashboardBox(row));
    });
  }

  function run(){
    if (!rows().length) return;
    addMatchupRows();
    addDashboardBox();
  }

  run();
  setTimeout(run, 100);
  setTimeout(run, 500);
  setTimeout(run, 1200);

  document.addEventListener('click', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1200);
  });

  window.addEventListener('hashchange', () => {
    setTimeout(run, 150);
    setTimeout(run, 500);
  });
})();
</script>
'''

if "openingPossessionSiteFeature" not in html:
    html = html.replace("</body>", js + "\n</body>")

INDEX.write_text(html)

print("Embedded rows:", len(cleaned))
print("Installed opening possession site feature")
