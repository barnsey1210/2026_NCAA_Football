#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import json
import re

INDEX = Path("index.html")
SRC = Path("data/signals/travel_1h_signals_2026.csv")

DATA_START = "<!-- TRAVEL_1H_SIGNAL_DATA_START -->"
DATA_END = "<!-- TRAVEL_1H_SIGNAL_DATA_END -->"
JS_START = "<!-- TRAVEL_1H_SIGNAL_JS_START -->"
JS_END = "<!-- TRAVEL_1H_SIGNAL_JS_END -->"

def remove_block(s, start, end):
    return re.sub(re.escape(start) + r"[\s\S]*?" + re.escape(end) + r"\n?", "", s)

def main():
    if not INDEX.exists():
        raise SystemExit("Missing index.html")
    if not SRC.exists():
        raise SystemExit(f"Missing {SRC}; run build_travel_1h_signals_2026.py first")

    df = pd.read_csv(SRC, low_memory=False).fillna("")
    records = df.to_dict(orient="records")

    by_game_id = {}
    by_matchup = {}
    for r in records:
        gid = str(r.get("game_id", "")).strip()
        if gid:
            by_game_id[gid] = r
        key = f"{r.get('date','')}|{r.get('away_team','')}|{r.get('home_team','')}"
        by_matchup[key] = r

    payload = {
        "by_game_id": by_game_id,
        "by_matchup": by_matchup,
        "summary": {
            "spread_all_3tz_dogs": "2024-25 Big Ten/ACC 3+ TZ traveler underdogs: 9-22 1H ATS, 29.0%, -3.89 margin",
            "spread_nonwest_west_dogs": "Non-west teams traveling west as 1H dogs: 2-13 ATS, 13.3%, -3.90 margin",
            "spread_travel_favs": "3+ TZ traveler favorites: 17-7 1H ATS, 70.8%, +3.73 margin",
            "total_all_3tz": "3+ TZ 1H totals: 32 O / 23 U, 58.2% over",
            "total_nonwest_west": "Non-west teams traveling west: 17 O / 10 U, 63.0% over",
        }
    }

    data_block = f"""{DATA_START}
<script id="travel-1h-signal-data" type="application/json">{json.dumps(payload, ensure_ascii=False)}</script>
{DATA_END}
"""

    js_block = f"""{JS_START}
<style>
.travel-1h-badge {{
  display:inline-flex;
  align-items:center;
  gap:4px;
  margin-top:4px;
  padding:2px 6px;
  border-radius:999px;
  font-size:10.5px;
  font-weight:800;
  line-height:1.15;
  border:1px solid rgba(15,23,42,.16);
  background:rgba(250,204,21,.16);
  color:#713f12;
  white-space:normal;
  max-width:150px;
}}
.travel-1h-total-badge {{
  background:rgba(14,165,233,.13);
  color:#075985;
}}
.travel-1h-spread-badge {{
  background:rgba(245,158,11,.15);
  color:#7c2d12;
}}
</style>
<script id="travel-1h-signal-js">
(function() {{
  function readTravel1hData() {{
    try {{
      const el = document.getElementById('travel-1h-signal-data');
      return el ? JSON.parse(el.textContent || '{{}}') : {{}};
    }} catch(e) {{
      return {{}};
    }}
  }}

  window.TRAVEL_1H_SIGNALS = readTravel1hData();

  function travel1hSignalForGame(g) {{
    if (!g || !window.TRAVEL_1H_SIGNALS) return null;
    const byId = window.TRAVEL_1H_SIGNALS.by_game_id || {{}};
    const byMatch = window.TRAVEL_1H_SIGNALS.by_matchup || {{}};
    const gid = String(g.game_id || '');
    if (gid && byId[gid]) return byId[gid];
    const key = `${{g.date || ''}}|${{g.away_team || ''}}|${{g.home_team || ''}}`;
    return byMatch[key] || null;
  }}

  function travel1hBadgeHtml(txt, title, cls) {{
    if (!txt) return '';
    const safeTxt = typeof escapeHtml === 'function' ? escapeHtml(txt) : String(txt);
    const safeTitle = typeof escapeHtml === 'function' ? escapeHtml(title || txt) : String(title || txt);
    return `<div class="travel-1h-badge ${{cls || ''}}" title="${{safeTitle}}">${{safeTxt}}</div>`;
  }}

  window.travel1hSpreadBadge = function(g) {{
    const s = travel1hSignalForGame(g);
    if (!s || !s.spread_badge) return '';
    return travel1hBadgeHtml(s.spread_badge, s.spread_title, 'travel-1h-spread-badge');
  }};

  window.travel1hTotalBadge = function(g) {{
    const s = travel1hSignalForGame(g);
    if (!s || !s.total_badge) return '';
    return travel1hBadgeHtml(s.total_badge, s.total_title, 'travel-1h-total-badge');
  }};

  function wrapFormatter(name, badgeFn) {{
    try {{
      const oldFn = window[name] || (typeof globalThis[name] === 'function' ? globalThis[name] : null);
      if (typeof oldFn !== 'function') return false;
      const wrapped = function(g) {{
        return oldFn.call(this, g) + badgeFn(g);
      }};
      window[name] = wrapped;
      globalThis[name] = wrapped;
      return true;
    }} catch(e) {{
      return false;
    }}
  }}

  const spreadWrapped = [
    'fmtSpreadEdgeCell',
    'fmtAtsEdgeCell',
    'fmtMarketLabAtsEdgeCell',
    'fmtAtsEdgeValueCell',
    'fmtSpreadValueCell'
  ].some(name => wrapFormatter(name, window.travel1hSpreadBadge));

  const totalWrapped = [
    'fmtTotalEdgeCell',
    'fmtMarketTotalEdgeCell',
    'fmtTotalValueCell',
    'fmtTotalEdgeValueCell'
  ].some(name => wrapFormatter(name, window.travel1hTotalBadge));

    console.log('travel 1H badges loaded', {{
    games: Object.keys((window.TRAVEL_1H_SIGNALS || {{}}).by_game_id || {{}}).length,
    spreadWrapped,
    totalWrapped
  }});
}})();
</script>
{JS_END}
"""

    s = INDEX.read_text(errors="ignore")
    s = remove_block(s, DATA_START, DATA_END)
    s = remove_block(s, JS_START, JS_END)

    insert = data_block + "\n" + js_block + "\n"

    if "</body>" in s:
        s = s.replace("</body>", insert + "</body>")
    else:
        s += "\n" + insert

    spread_badge_expr = "${typeof travel1hSpreadBadge === 'function' ? travel1hSpreadBadge(g) : ''}"
    total_badge_expr = "${typeof travel1hTotalBadge === 'function' ? travel1hTotalBadge(g) : ''}"

    if "fmtAtsSideWithCoachHalf(g, ats.side)}${typeof travel1hSpreadBadge" not in s:
        s = s.replace(
            "${fmtAtsSideWithCoachHalf(g, ats.side)}</td>",
            "${fmtAtsSideWithCoachHalf(g, ats.side)}" + spread_badge_expr + "</td>",
            1
        )

    if "fmtTotalSideWithCoachHalf(g, tot.side)}${typeof travel1hTotalBadge" not in s:
        s = s.replace(
            "${fmtTotalSideWithCoachHalf(g, tot.side)}</td>",
            "${fmtTotalSideWithCoachHalf(g, tot.side)}" + total_badge_expr + "</td>",
            1
        )

    INDEX.write_text(s)

    print("injected travel 1H badges")
    print("records:", len(records))
    print("index:", INDEX)

if __name__ == "__main__":
    main()
