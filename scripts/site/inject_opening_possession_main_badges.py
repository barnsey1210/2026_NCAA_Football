#!/usr/bin/env python3
from pathlib import Path
import json
import re
import pandas as pd
import math

INDEX = Path("index.html")
TENDENCY = Path("data/coach/coach_opening_possession_tendency_2026.csv")

MIN_TOSS_WINS = 5
RECEIVE_BADGE_PCT = 60.0
STRONG_RECEIVE_PCT = 75.0

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

def main():
    if not INDEX.exists():
        raise SystemExit("index.html not found")
    if not TENDENCY.exists():
        raise SystemExit(f"{TENDENCY} not found")

    df = pd.read_csv(TENDENCY, low_memory=False)

    rows = []
    for _, r in df.iterrows():
        toss_wins = float(r.get("toss_wins") or 0)
        receive_pct = float(r.get("receive_pct") or 0)

        if toss_wins < MIN_TOSS_WINS:
            continue
        if receive_pct < RECEIVE_BADGE_PCT:
            continue

        receive = int(float(r.get("receive_take_ball") or 0))
        toss = int(toss_wins)
        strength = "Strong receive" if receive_pct >= STRONG_RECEIVE_PCT else "Receive lean"

        rows.append({
            "team": clean(r.get("team")),
            "head_coach": clean(r.get("head_coach")),
            "toss_wins": toss,
            "receive_take_ball": receive,
            "receive_pct": round(receive_pct, 1),
            "defer": clean(r.get("defer")),
            "defer_pct": clean(r.get("defer_pct")),
            "strength": strength,
            "confidence": clean(r.get("confidence")),
            "summary": f"{strength}: receive {receive}/{toss} ({receive_pct:.1f}%)",
        })

    s = INDEX.read_text(errors="ignore")

    data_block = f'''
<script id="opening-possession-main-badges-data">
// OPENING_POSSESSION_MAIN_BADGES_DATA_START
window.OPENING_POSSESSION_MAIN_BADGES = {json.dumps(rows, ensure_ascii=False, separators=(",", ":"))};
// OPENING_POSSESSION_MAIN_BADGES_DATA_END
</script>
'''

    js_block = r'''
<script id="opening-possession-main-badges-js">
// OPENING_POSSESSION_MAIN_BADGES_JS_START
(function(){
  function opNorm(x){
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

  function opEsc(x){
    return String(x ?? '')
      .replaceAll('&','&amp;')
      .replaceAll('<','&lt;')
      .replaceAll('>','&gt;')
      .replaceAll('"','&quot;')
      .replaceAll("'","&#39;");
  }

  function opBadgeForTeam(team){
    const rows = window.OPENING_POSSESSION_MAIN_BADGES || [];
    const t = opNorm(team);
    return rows.find(r => opNorm(r.team) === t) || null;
  }

  window.openingPossessionMainBadgeForGame = function(g){
    if (!g) return '';

    const away = opBadgeForTeam(g.away_team);
    const home = opBadgeForTeam(g.home_team);

    // Show both if both are outliers, but that will be rare.
    const badges = [];
    for (const r of [away, home]) {
      if (!r) continue;
      const cls = Number(r.receive_pct) >= 75 ? 'op-receive-strong' : 'op-receive-lean';
      const txt = `Toss: ${r.team} receive ${r.receive_take_ball}/${r.toss_wins}`;
      const title = `${r.head_coach || r.team}: ${r.summary || ''}. Context only for 1Q/1H/opening-possession betting.`;
      badges.push(`<div class="op-main-badge ${cls}" title="${opEsc(title)}">
        <span>${opEsc(txt)}</span>
        <span class="op-main-pill">${Number(r.receive_pct).toFixed(0)}%</span>
      </div>`);
    }

    if (!badges.length) return '';
    return `<div class="op-main-badge-wrap">${badges.join('')}</div>`;
  };
})();
// OPENING_POSSESSION_MAIN_BADGES_JS_END
</script>
'''

    css = r'''
<style id="opening-possession-main-badges-css">
/* OPENING_POSSESSION_MAIN_BADGES_CSS_START */
.op-main-badge-wrap{
  display:flex;
  flex-direction:column;
  gap:4px;
  margin-top:5px;
}
.op-main-badge{
  display:inline-flex;
  align-items:center;
  gap:6px;
  width:max-content;
  max-width:100%;
  border-radius:999px;
  padding:3px 7px;
  font-size:11px;
  font-weight:900;
  line-height:1.15;
  border:1px solid rgba(250,204,21,.38);
  background:rgba(250,204,21,.12);
  color:#fde68a;
}
.op-main-badge.op-receive-strong{
  border-color:rgba(251,146,60,.48);
  background:rgba(251,146,60,.16);
  color:#fed7aa;
}
.op-main-pill{
  border-radius:999px;
  padding:1px 5px;
  background:rgba(15,23,42,.55);
  border:1px solid rgba(255,255,255,.16);
  color:#fff7ed;
  font-size:10px;
}
/* OPENING_POSSESSION_MAIN_BADGES_CSS_END */
</style>
'''

    # Remove old copies.
    s = re.sub(r'\n?<script id="opening-possession-main-badges-data"[\s\S]*?</script>\s*', '\n', s)
    s = re.sub(r'\n?<script id="opening-possession-main-badges-js"[\s\S]*?</script>\s*', '\n', s)
    s = re.sub(r'\n?<style id="opening-possession-main-badges-css"[\s\S]*?</style>\s*', '\n', s)

    # Add CSS before </head>.
    if "</head>" in s:
        s = s.replace("</head>", css + "\n</head>", 1)
    else:
        s = css + "\n" + s

    # Add data/js before closing body.
    if "</body>" in s:
        s = s.replace("</body>", data_block + "\n" + js_block + "\n</body>", 1)
    else:
        s += "\n" + data_block + "\n" + js_block

    # Patch ATS Edge cell renderer path.
    # Existing Market Lab row has fmtAtsSideWithCoachHalf(g, ats.side). Append opening possession badge after it.
    old = "fmtAtsSideWithCoachHalf(g, ats.side)}"
    new = "fmtAtsSideWithCoachHalf(g, ats.side)}${openingPossessionMainBadgeForGame(g)}"

    if new not in s:
        if old not in s:
            raise SystemExit("Could not find ATS Edge formatter insertion point")
        s = s.replace(old, new, 1)

    INDEX.write_text(s)

    print("Opening possession main badges injected")
    print("badge rows:", len(rows))
    print("strong receive rows:", sum(1 for r in rows if r["receive_pct"] >= STRONG_RECEIVE_PCT))
    print("receive lean rows:", sum(1 for r in rows if 60 <= r["receive_pct"] < STRONG_RECEIVE_PCT))
    for r in rows[:20]:
        print(f"- {r['team']}: {r['summary']}")

if __name__ == "__main__":
    main()
