#!/usr/bin/env python3
import json
import re
from pathlib import Path

import pandas as pd

INDEX = Path("index.html")
GAME_ALERTS = Path("data/injuries/game_injury_alerts.csv")

DATA_ID = "game-injury-overlay-data"
SCRIPT_ID = "game-injury-overlay-script"
CSS_ID = "game-injury-overlay-css"

CSS = """
<style id="game-injury-overlay-css">
.game-injury-overlay-chip{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  margin-left:6px;
  padding:2px 6px;
  border-radius:999px;
  font-size:10px;
  font-weight:800;
  border:1px solid var(--border);
  white-space:nowrap;
  vertical-align:middle;
}
.game-injury-overlay-none{ opacity:.58; background:rgba(148,163,184,.08); border-color:rgba(148,163,184,.20); }
.game-injury-overlay-low{ background:rgba(234,179,8,.12); border-color:rgba(234,179,8,.35); }
.game-injury-overlay-medium{ background:rgba(249,115,22,.14); border-color:rgba(249,115,22,.45); }
.game-injury-overlay-high{ background:rgba(239,68,68,.16); border-color:rgba(239,68,68,.52); }
.game-injury-overlay-major{ background:rgba(185,28,28,.25); border-color:rgba(239,68,68,.75); }
</style>
"""

SCRIPT = """
<script id="game-injury-overlay-script">
(function(){
  try {
    function norm(s){
      return String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').replace(/\\s+/g, ' ').trim();
    }

    function esc(s){
      return String(s || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function readData(){
      var el = document.getElementById('game-injury-overlay-data');
      if (!el) return [];
      try {
        return JSON.parse(el.textContent || '[]') || [];
      } catch(e) {
        console.warn('Could not parse game injury overlay data', e);
        return [];
      }
    }

    function chip(score, tier, summary){
      var s = Number(score || 0);
      var t = String(tier || 'None');
      if (!s) t = 'None';
      var cls = t.toLowerCase();
      var span = document.createElement('span');

      span.className = 'game-injury-overlay-chip game-injury-overlay-' + cls;

      if (!s) {
        span.title = 'No current injury impact flagged · score 0.0';
        span.textContent = 'INJ 0.0';
      } else {
        span.title = String(summary || t + ' injury impact ' + s.toFixed(1));
        span.textContent = 'INJ ' + s.toFixed(1);
      }

      return span;
    }

    function addChip(cell, score, tier, summary, key){
      if (!cell) return;
      if (cell.querySelector('[data-injury-key="' + key + '"]')) return;

      var c = chip(score, tier, summary);
      if (!c) return;

      c.setAttribute('data-injury-key', key);
      cell.appendChild(c);
    }

    function decorate(){
      var data = readData();
      if (!data.length) return;

      var rows = document.querySelectorAll('table.schedule-table tbody tr');
      if (!rows || !rows.length) return;

      for (var i=0; i<rows.length; i++){
        var row = rows[i];
        var cells = row.querySelectorAll('td');
        if (!cells || cells.length < 4) continue;

        var awayCell = cells[2];
        var homeCell = cells[3];

        var awayTxt = norm(awayCell.textContent);
        var homeTxt = norm(homeCell.textContent);

        for (var j=0; j<data.length; j++){
          var r = data[j];
          var away = norm(r.away_team);
          var home = norm(r.home_team);

          if (!away || !home) continue;
          if (awayTxt.indexOf(away) === -1) continue;
          if (homeTxt.indexOf(home) === -1) continue;

          addChip(
            awayCell,
            r.away_injury_score,
            r.game_injury_tier,
            r.injury_summary,
            'away-' + String(r.game_id)
          );

          addChip(
            homeCell,
            r.home_injury_score,
            r.game_injury_tier,
            r.injury_summary,
            'home-' + String(r.game_id)
          );
        }
      }
    }

    function start(){
      decorate();

      try {
        var obs = new MutationObserver(function(){ decorate(); });
        obs.observe(document.body, { childList:true, subtree:true });
      } catch(e) {
        console.warn('Game injury overlay observer failed', e);
      }
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', start);
    } else {
      start();
    }
  } catch(e) {
    console.warn('Game injury overlay failed safely', e);
  }
})();
</script>
"""

def remove_existing(txt):
    txt = re.sub(r'<style id="game-injury-overlay-css">.*?</style>\s*', '', txt, flags=re.S)
    txt = re.sub(r'<script id="game-injury-overlay-data" type="application/json">.*?</script>\s*', '', txt, flags=re.S)
    txt = re.sub(r'<script id="game-injury-overlay-script">.*?</script>\s*', '', txt, flags=re.S)
    return txt

def main():
    txt = INDEX.read_text(errors="ignore")
    txt = remove_existing(txt)

    if GAME_ALERTS.exists() and GAME_ALERTS.stat().st_size > 0:
        df = pd.read_csv(GAME_ALERTS)
        if "game_injury_score" in df.columns:
            df = df.copy()
        else:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    keep_cols = [
        "game_id",
        "date",
        "away_team",
        "home_team",
        "away_injury_score",
        "home_injury_score",
        "game_injury_score",
        "game_injury_tier",
        "injury_edge_home",
        "injury_summary",
    ]

    if not df.empty:
        for c in keep_cols:
            if c not in df.columns:
                df[c] = None
        df = df[keep_cols]
        records = json.loads(df.where(pd.notnull(df), None).to_json(orient="records"))
    else:
        records = []

    data_json = json.dumps(records, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")

    data_script = f'<script id="{DATA_ID}" type="application/json">{data_json}</script>\\n'

    insert = CSS + "\n" + data_script + SCRIPT + "\n"

    if "</body>" in txt:
        txt = txt.replace("</body>", insert + "</body>", 1)
    else:
        txt += "\n" + insert

    INDEX.write_text(txt)

    print("injected safe injury overlay")
    print("game overlay records:", len(records))
    print("wrote:", INDEX)

if __name__ == "__main__":
    main()
