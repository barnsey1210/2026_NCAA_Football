#!/usr/bin/env python3
from pathlib import Path
import sys
import json
import re
import pandas as pd
import math
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.ncaaf_config import canonical_team

MATCHUP = Path("matchup.html")

TENDENCY = Path("data/coach/coach_opening_possession_tendency_2026.csv")
PAIRS = Path("data/signals/opening_possession_projection_pairs_2026.csv")
SUMMARY = Path("data/coach/opening_receiver_1h_ats_summary_2024_2025_combined_cleaned.csv")

def clean(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, float):
        if math.isnan(v):
            return None
        if v.is_integer():
            return int(v)
    return v

def rows(path):
    if not path.exists():
        return []
    df = pd.read_csv(path, low_memory=False)
    return [{k: clean(v) for k, v in r.items()} for r in df.to_dict("records")]

def scheduled_pairs(html):
    match = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        raise SystemExit("matchup.html is missing its embedded DB")
    db = json.loads(match.group(1))
    return {
        frozenset((canonical_team(g.get("away_team")), canonical_team(g.get("home_team"))))
        for g in db.get("games", []) if g.get("away_team") and g.get("home_team")
    }

def scheduled_pair_rows(path, allowed_pairs):
    return [
        row for row in rows(path)
        if frozenset((canonical_team(row.get("team_a")), canonical_team(row.get("team_b")))) in allowed_pairs
    ]

def main():
    if not MATCHUP.exists():
        raise SystemExit("matchup.html not found")

    s = MATCHUP.read_text(errors="ignore")

    allowed_pairs = scheduled_pairs(s)
    data = {
        "tendency": rows(TENDENCY),
        "pairs": scheduled_pair_rows(PAIRS, allowed_pairs),
        "summary": rows(SUMMARY),
    }

    data_block = f'''<script id="opening-possession-matchup-data" type="application/json">{json.dumps(data, ensure_ascii=False, separators=(",", ":"))}</script>'''

    js_block = r'''
<script id="opening-possession-matchup-js">
(function(){
  function norm(x){
    return String(x || '')
      .replace("Hawai'i", "Hawaii")
      .replace("San José State", "San Jose State")
      .replace("Miami (FL)", "Miami-FL")
      .replace("Miami", "Miami-FL")
      .replace("UMass", "Massachusetts")
      .replace("UL Monroe", "UL-Monroe")
      .replace("James Madison", "JMU")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, ' ')
      .trim();
  }

  function esc(x){
    return String(x ?? '')
      .replaceAll('&','&amp;')
      .replaceAll('<','&lt;')
      .replaceAll('>','&gt;')
      .replaceAll('"','&quot;')
      .replaceAll("'","&#39;");
  }

  function num(x, d=1){
    const n = Number(x);
    return Number.isFinite(n) ? n.toFixed(d).replace(/\.0$/, '') : '—';
  }

  function pct(x){
    const n = Number(x);
    return Number.isFinite(n) ? `${n.toFixed(1).replace(/\.0$/, '')}%` : '—';
  }

  function loadOpeningPossessionData(){
    const el = document.getElementById('opening-possession-matchup-data');
    if (!el) return {tendency:[], pairs:[], summary:[]};
    try { return JSON.parse(el.textContent || '{}'); }
    catch(e){ return {tendency:[], pairs:[], summary:[]}; }
  }

  function getGame(){
    if (typeof findGame === 'function') {
      try { return findGame(); } catch(e) {}
    }
    if (window.DB && Array.isArray(DB.games)) {
      const qs = new URLSearchParams(location.search);
      const gid = qs.get('game_id') || qs.get('game') || qs.get('id');
      if (gid) return DB.games.find(g => String(g.game_id) === String(gid));
    }
    return null;
  }

  function rowForTeam(rows, team){
    const t = norm(team);
    return rows.find(r => norm(r.team) === t) || null;
  }

  function pairForGame(rows, away, home){
    const a = norm(away), h = norm(home);
    return rows.find(r =>
      (norm(r.team_a) === a && norm(r.team_b) === h) ||
      (norm(r.team_a) === h && norm(r.team_b) === a)
    ) || null;
  }

  function summaryText(rows){
    const overall = rows.find(r => String(r.group || '').toLowerCase().includes('overall'));
    const home = rows.find(r => String(r.group || '').toLowerCase().includes('home'));
    if (!overall) return '';
    const overallTxt = `Opening receiver overall: ${overall.wins || '—'}-${overall.losses || '—'} ATS, ${pct(overall.cover_pct)}, avg margin ${num(overall.avg_ats_margin, 2)}.`;
    const homeTxt = home ? ` Home opening receiver: ${home.wins || '—'}-${home.losses || '—'} ATS, ${pct(home.cover_pct)}, avg margin ${num(home.avg_ats_margin, 2)}.` : '';
    return overallTxt + homeTxt;
  }

  function teamBlock(label, team, row, projectedPct){
    if (!row) {
      return `<div class="open-pos-team">
        <div class="open-pos-team-title">${esc(label)} · ${esc(team)}</div>
        <div class="small muted">No explicit ESPN toss-decision sample found for current coach.</div>
      </div>`;
    }

    const tendency = row.opening_possession_tendency || (
      Number(row.defer_pct) >= Number(row.receive_pct) ? 'Likely defer' : 'Likely receive'
    );

    return `<div class="open-pos-team">
      <div class="open-pos-team-title">${esc(label)} · ${esc(team)}</div>
      <div><b>${esc(tendency)}</b> <span class="small muted">(${esc(row.confidence || 'sample')})</span></div>
      <div class="small muted">Coach: ${esc(row.head_coach || '')}</div>
      <div class="small muted">Won toss ${esc(row.toss_wins ?? '—')}x · receive ${esc(row.receive_take_ball ?? '—')}/${esc(row.toss_wins ?? '—')} (${pct(row.receive_pct)}) · defer ${esc(row.defer ?? '—')}/${esc(row.toss_wins ?? '—')} (${pct(row.defer_pct)})</div>
      <div class="small muted">Projected receive opening kick: <b>${pct(projectedPct)}</b></div>
    </div>`;
  }

  function openingPossessionCard(g){
    if (!g) return '';
    const data = loadOpeningPossessionData();
    const away = g.away_team;
    const home = g.home_team;

    const awayRow = rowForTeam(data.tendency || [], away);
    const homeRow = rowForTeam(data.tendency || [], home);
    const pair = pairForGame(data.pairs || [], away, home);

    if (!awayRow && !homeRow && !pair) return '';

    let awayProj = null, homeProj = null, projectedReceiver = null, edge = null;

    if (pair) {
      projectedReceiver = pair.projected_opening_receiver;
      edge = pair.edge_pct_points;

      if (norm(pair.team_a) === norm(away)) {
        awayProj = pair.team_a_projected_receive_opening_kick_pct;
        homeProj = pair.team_b_projected_receive_opening_kick_pct;
      } else {
        awayProj = pair.team_b_projected_receive_opening_kick_pct;
        homeProj = pair.team_a_projected_receive_opening_kick_pct;
      }
    }

    const summary = summaryText(data.summary || []);

    return `<div class="card opening-possession-card">
      <div class="card-title">
        <span>Opening possession / 1H context</span>
        <span class="small">coin toss tendencies, context only</span>
      </div>
      <div class="read-box">
        ${projectedReceiver ? `<p><b>Projected opening receiver:</b> ${esc(projectedReceiver)}${edge != null ? ` by ${num(edge,1)} pct pts` : ''}.</p>` : ''}
        <div class="opening-possession-grid">
          ${teamBlock('Away', away, awayRow, awayProj)}
          ${teamBlock('Home', home, homeRow, homeProj)}
        </div>
        ${summary ? `<p class="small muted">${esc(summary)}</p>` : ''}
        <p class="small muted"><b>Use:</b> possession/1H context only. Not a standalone bet signal.</p>
      </div>
    </div>`;
  }

  function installOpeningPossessionCard(){
    const g = getGame();
    const html = openingPossessionCard(g);
    if (!html) return;

    const app = document.getElementById('app');
    if (!app || app.querySelector('.opening-possession-card')) return;

    const cards = Array.from(app.querySelectorAll('.card'));
    const betting = cards.find(c => (c.textContent || '').includes('Betting read summary'));
    const tmp = document.createElement('div');
    tmp.innerHTML = html.trim();
    const card = tmp.firstElementChild;

    if (betting && betting.parentNode) {
      betting.insertAdjacentElement('afterend', card);
    } else {
      app.insertAdjacentElement('afterbegin', card);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', installOpeningPossessionCard);
  } else {
    setTimeout(installOpeningPossessionCard, 0);
  }
})();
</script>
'''

    # Remove old injected copy.
    s = re.sub(r'\n?<script id="opening-possession-matchup-data"[\s\S]*?</script>\s*', '\n', s)
    s = re.sub(r'\n?<script id="opening-possession-matchup-js"[\s\S]*?</script>\s*', '\n', s)

    # Put after the main render script so the DOM exists, but before RP scripts is fine.
    marker = '<script id="rp-support-badges-data">'
    if marker in s:
      s = s.replace(marker, data_block + "\n" + js_block + "\n" + marker, 1)
    else:
      s = s.replace("</body>", data_block + "\n" + js_block + "\n</body>", 1)

    MATCHUP.write_text(s)

    print("injected opening possession matchup card")
    print("tendency rows:", len(data["tendency"]))
    print("pair rows:", len(data["pairs"]))
    print("scheduled pair keys:", len(allowed_pairs))
    print("summary rows:", len(data["summary"]))

if __name__ == "__main__":
    main()
