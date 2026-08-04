from pathlib import Path
import json
import pandas as pd
import re

TARGETS = [Path("matchup.html")]
CSV = Path("data/history/matchup_line_history_clean.csv")

START = "<!-- matchup-line-history-summary-start -->"
END = "<!-- matchup-line-history-summary-end -->"

def clean(v):
    if pd.isna(v):
        return None
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v

def build_payload():
    df = pd.read_csv(CSV)
    keep = [
        "snapshot_date",
        "source",
        "game_date",
        "week",
        "away_team",
        "home_team",
        "market_spread_home",
        "market_spread_price",
        "market_spread_book",
        "market_total",
        "market_total_over_price",
        "market_total_under_price",
        "market_total_book",
        "model_spread_home",
        "projected_total",
        "game_id",
    ]
    keep = [c for c in keep if c in df.columns]
    out = {}
    for gid, sub in df[keep].sort_values(["game_id", "snapshot_date"]).groupby("game_id", dropna=False):
        gid = str(gid)
        out[gid] = [
            {k: clean(v) for k, v in row.items()}
            for row in sub.drop(columns=["game_id"], errors="ignore").to_dict("records")
        ]
    return out

payload = json.dumps(build_payload(), separators=(",", ":"))

BLOCK = f'''
{START}
<script id="matchup-line-history-summary-data">
window.MATCHUP_LINE_HISTORY_COMPACT = {payload};
</script>

<script id="matchup-line-history-summary-js">
(function(){{
  if (window.__matchupLineHistorySummaryInstalled) return;
  window.__matchupLineHistorySummaryInstalled = true;

  function esc(x){{
    return String(x ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
  }}
  function nval(x){{
    if (x === null || x === undefined || x === '') return null;
    const n = Number(x);
    return Number.isFinite(n) ? n : null;
  }}
  function fmt(x){{
    const n = nval(x);
    if (n === null) return '—';
    return n.toFixed(1).replace(/\\.0$/, '');
  }}
  function price(x){{
    const n = nval(x);
    if (n === null || n === 0) return '—';
    return n.toFixed(0);
  }}
  function dateLabel(v){{
    if (!v) return '—';
    const d = new Date(String(v) + 'T00:00:00');
    if (Number.isNaN(d.getTime())) return String(v);
    return d.toLocaleDateString(undefined, {{month:'short', day:'numeric'}});
  }}
  function validSpread(x){{ const n=nval(x); return n!==null && Math.abs(n)<=80; }}
  function validTotal(x){{ const n=nval(x); return n!==null && n>=20 && n<=100; }}

  function gameIdFromPage(){{
    try {{
      const p = new URLSearchParams(location.search);
      return p.get('game_id') || p.get('gameId') || p.get('id') || '';
    }} catch(e) {{
      return '';
    }}
  }}

  function currentGame(){{
    try {{
      if (typeof findGame === 'function') return findGame();
    }} catch(e) {{}}

    const gid = gameIdFromPage();
    try {{
      const dbScript = document.getElementById('db');
      if (!dbScript) return null;
      const db = JSON.parse(dbScript.textContent);
      return (db.games || []).find(g => String(g.game_id) === String(gid)) || null;
    }} catch(e) {{
      return null;
    }}
  }}

  function teamLine(home, away, x){{
    const n = nval(x);
    if (n === null) return '—';
    if (Math.abs(n) < 0.05) return 'Pick';
    if (n < 0) return `${{home}} ${{fmt(n)}}`;
    return `${{away}} +${{fmt(n)}}`;
  }}

  function compactSpread(home, away, openVal, curVal){{
    const o = nval(openVal), c = nval(curVal);
    if (o === null || c === null) return '—';
    const openTeam = Math.abs(o) < 0.05 ? 'Pick' : (o < 0 ? home : away);
    const curTeam = Math.abs(c) < 0.05 ? 'Pick' : (c < 0 ? home : away);
    const openLine = Math.abs(o) < 0.05 ? 'Pick' : `${{openTeam}} ${{o < 0 ? fmt(o) : '+' + fmt(o)}}`;
    const curOnly = Math.abs(c) < 0.05 ? 'Pick' : `${{c < 0 ? fmt(c) : '+' + fmt(c)}}`;
    if (openTeam === curTeam && openTeam !== 'Pick') return `${{openLine}} → ${{curOnly}}`;
    return `${{openLine}} → ${{teamLine(home, away, c)}}`;
  }}

  function moveChip(delta){{
    const n = nval(delta);
    if (n === null || Math.abs(n) < 0.25) return '<span class="mlh-move flat">—</span>';
    const cls = n > 0 ? 'up' : 'down';
    const arrow = n > 0 ? '↑' : '↓';
    return `<span class="mlh-move ${{cls}}">${{arrow}} ${{fmt(Math.abs(n))}}</span>`;
  }}

  function bookLogo(book){{
    if (!book) return '—';
    try {{
      if (typeof sportsbookLogo === 'function') return sportsbookLogo(book);
      if (typeof marketBookLogo === 'function') return marketBookLogo(book);
      if (typeof bookLogoBadge === 'function') return bookLogoBadge(book);
    }} catch(e) {{}}
    return esc(book);
  }}

  function uniqueDaily(rows, kind){{
    const map = new Map();
    for (const r of rows || []) {{
      const d = r.snapshot_date;
      if (!d) continue;
      const value = kind === 'spread' ? nval(r.market_spread_home) : nval(r.market_total);
      const ok = kind === 'spread' ? validSpread(value) : validTotal(value);
      if (!ok) continue;

      const rec = {{
        date: d,
        value,
        book: kind === 'spread' ? (r.market_spread_book || '') : (r.market_total_book || ''),
        spreadPrice: r.market_spread_price,
        overPrice: r.market_total_over_price,
        underPrice: r.market_total_under_price,
        source: r.source || ''
      }};

      const old = map.get(d);
      function score(x){{
        let s = 0;
        if (kind === 'spread' && price(x.spreadPrice) !== '—') s += 10;
        if (kind === 'total' && (price(x.overPrice) !== '—' || price(x.underPrice) !== '—')) s += 10;
        if (String(x.source).toLowerCase().includes('sportsgameodds')) s += 5;
        if (String(x.source).toLowerCase().includes('action')) s += 3;
        if (x.book) s += 1;
        return s;
      }}

      if (!old || score(rec) >= score(old)) map.set(d, rec);
    }}
    return [...map.values()].sort((a,b)=>String(a.date).localeCompare(String(b.date)));
  }}

  function stat(arr){{
    if (!arr.length) return null;
    const open = arr[0];
    const cur = arr[arr.length - 1];
    return {{open, cur, move: cur.value - open.value, arr}};
  }}

  function lineDetails(g, statObj, kind){{
    if (!statObj || !statObj.arr.length) return '<div class="mlh-empty">No history</div>';
    const chron = statObj.arr.slice().sort((a,b)=>String(a.date).localeCompare(String(b.date)));
    const withMoves = chron.map((r,i)=>({{r, delta:i ? Number(r.value)-Number(chron[i-1].value) : 0}}))
      .sort((a,b)=>String(b.r.date).localeCompare(String(a.r.date)));

    const rows = withMoves.slice(0, 12).map(({{r, delta}}) => {{
      const line = kind === 'spread' ? teamLine(g.home_team, g.away_team, r.value) : fmt(r.value);
      const p = kind === 'spread'
        ? price(r.spreadPrice)
        : (() => {{
            const o = price(r.overPrice), u = price(r.underPrice);
            return (o === '—' && u === '—') ? '—' : `O ${{o}} / U ${{u}}`;
          }})();

      return `<tr>
        <td>${{dateLabel(r.date)}}</td>
        <td>${{esc(line)}} ${{Math.abs(delta) >= 0.25 ? moveChip(delta) : ''}}</td>
        <td>${{esc(p)}}</td>
        <td>${{bookLogo(r.book)}}</td>
      </tr>`;
    }}).join('');

    return `<table class="mlh-table">
      <thead><tr><th>Date</th><th>${{kind === 'spread' ? 'Line' : 'Total'}}</th><th>Price</th><th>Book</th></tr></thead>
      <tbody>${{rows}}</tbody>
    </table>`;
  }}

  function edgeSpread(g, curSpread){{
    const margin = nval(g.projected_margin_home);
    const line = nval(curSpread);
    if (margin === null || line === null) return '—';
    const edge = margin + line;
    if (Math.abs(edge) < 0.25) return 'No edge';
    return edge > 0 ? `${{g.home_team}} +${{fmt(Math.abs(edge))}}` : `${{g.away_team}} +${{fmt(Math.abs(edge))}}`;
  }}

  function edgeTotal(g, curTotal){{
    const proj = nval(g.projected_total);
    const total = nval(curTotal);
    if (proj === null || total === null) return '—';
    const edge = proj - total;
    if (Math.abs(edge) < 0.25) return 'No edge';
    return edge > 0 ? `Over +${{fmt(Math.abs(edge))}}` : `Under +${{fmt(Math.abs(edge))}}`;
  }}

  function buildSummary(){{
    const g = currentGame();
    if (!g || !g.game_id) return '';
    const rows = (window.MATCHUP_LINE_HISTORY_COMPACT || {{}})[String(g.game_id)] || [];
    if (!rows.length) return '';

    const spread = stat(uniqueDaily(rows, 'spread'));
    const total = stat(uniqueDaily(rows, 'total'));
    const snapshots = new Set(rows.map(r => r.snapshot_date).filter(Boolean)).size;

    const spOpen = spread ? spread.open.value : null;
    const spCur = spread ? spread.cur.value : null;
    const ttOpen = total ? total.open.value : null;
    const ttCur = total ? total.cur.value : null;

    return `<div class="mlh-card" id="matchupLineHistorySummary">
      <div class="mlh-head">
        <div>
          <div class="mlh-title">Line History Summary</div>
          <div class="mlh-sub">${{snapshots}} snapshots · selected market line by source/book priority</div>
        </div>
        <button type="button" class="mlh-toggle">Details</button>
      </div>

      <div class="mlh-grid">
        <div class="mlh-box">
          <div class="mlh-label">Spread</div>
          <div class="mlh-main">${{spread ? compactSpread(g.home_team, g.away_team, spOpen, spCur) : '—'}} ${{spread ? moveChip(spread.move) : ''}}</div>
          <div class="mlh-note">Model ${{teamLine(g.home_team, g.away_team, -nval(g.projected_margin_home))}} · Edge ${{edgeSpread(g, spCur)}}</div>
        </div>

        <div class="mlh-box">
          <div class="mlh-label">Total</div>
          <div class="mlh-main">${{total ? `${{fmt(ttOpen)}} → ${{fmt(ttCur)}}` : '—'}} ${{total ? moveChip(total.move) : ''}}</div>
          <div class="mlh-note">Model ${{fmt(g.projected_total)}} · Edge ${{edgeTotal(g, ttCur)}}</div>
        </div>
      </div>

      <div class="mlh-details" hidden>
        <div class="mlh-detail-grid">
          <section><h4>Spread history</h4>${{lineDetails(g, spread, 'spread')}}</section>
          <section><h4>Total history</h4>${{lineDetails(g, total, 'total')}}</section>
        </div>
      </div>
    </div>`;
  }}

  function findMarketCard(){{
    const cards = Array.from(document.querySelectorAll('.card, section, article, div'));
    return cards.find(el => {{
      const t = (el.textContent || '').toLowerCase();
      return t.includes('market betting data') || (t.includes('spread') && t.includes('total') && t.includes('best') && t.includes('market'));
    }});
  }}

  function install(){{
    if (document.getElementById('matchupLineHistorySummary')) return;
    const html = buildSummary();
    if (!html) return;

    const market = findMarketCard();
    if (market) {{
      market.insertAdjacentHTML('beforeend', html);
    }} else {{
      const app = document.getElementById('app') || document.body;
      app.insertAdjacentHTML('beforeend', html);
    }}

    const btn = document.querySelector('#matchupLineHistorySummary .mlh-toggle');
    const detail = document.querySelector('#matchupLineHistorySummary .mlh-details');
    if (btn && detail) {{
      btn.addEventListener('click', () => {{
        const open = detail.hasAttribute('hidden');
        if (open) {{
          detail.removeAttribute('hidden');
          btn.textContent = 'Hide';
        }} else {{
          detail.setAttribute('hidden', '');
          btn.textContent = 'Details';
        }}
      }});
    }}
  }}

  function scheduleInstall(){{
    setTimeout(install, 50);
    setTimeout(install, 300);
    setTimeout(install, 900);
  }}

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scheduleInstall);
  else scheduleInstall();

  const obs = new MutationObserver(() => install());
  obs.observe(document.documentElement, {{childList:true, subtree:true}});
}})();
</script>

<style id="matchup-line-history-summary-css">
.mlh-card{margin-top:14px;border:1px solid rgba(255,255,255,.12);border-radius:16px;background:rgba(15,23,42,.42);padding:12px}
.mlh-head{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:10px}
.mlh-title{font-size:15px;font-weight:950;text-transform:uppercase;letter-spacing:.08em;color:#e5efff}
.mlh-sub{font-size:12px;color:#aab7d4;margin-top:2px}
.mlh-toggle{border:1px solid rgba(96,165,250,.35);background:rgba(96,165,250,.14);border-radius:999px;padding:7px 14px;color:#e5efff;font-weight:900;cursor:pointer}
.mlh-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.mlh-box{border:1px solid rgba(255,255,255,.10);border-radius:14px;background:rgba(2,6,23,.26);padding:10px}
.mlh-label{font-size:11px;color:#aab7d4;text-transform:uppercase;letter-spacing:.1em;font-weight:950}
.mlh-main{font-size:18px;font-weight:950;line-height:1.2;margin-top:4px;color:#f8fafc}
.mlh-note{font-size:13px;color:#aab7d4;margin-top:4px}
.mlh-move{display:inline-flex;align-items:center;margin-left:6px;border-radius:999px;padding:2px 7px;font-size:12px;font-weight:950;border:1px solid rgba(255,255,255,.16);background:rgba(148,163,184,.16);vertical-align:middle}
.mlh-move.up{background:rgba(34,197,94,.18);border-color:rgba(34,197,94,.42);color:#dcfce7}
.mlh-move.down{background:rgba(248,113,113,.18);border-color:rgba(248,113,113,.42);color:#fee2e2}
.mlh-move.flat{color:#cbd5e1}
.mlh-details{margin-top:10px;border-top:1px solid rgba(255,255,255,.10);padding-top:10px}
.mlh-detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.mlh-detail-grid h4{margin:0 0 6px;font-size:14px}
.mlh-table{width:100%;border-collapse:collapse;table-layout:fixed}
.mlh-table th,.mlh-table td{padding:6px 7px;border-bottom:1px solid rgba(255,255,255,.08);font-size:12px;text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mlh-table th{font-size:10px;color:#aab7d4;text-transform:uppercase;letter-spacing:.08em}
.mlh-table th:nth-child(1),.mlh-table td:nth-child(1){width:62px}
.mlh-table th:nth-child(2),.mlh-table td:nth-child(2){width:160px}
.mlh-table th:nth-child(3),.mlh-table td:nth-child(3){width:112px}
.mlh-table th:nth-child(4),.mlh-table td:nth-child(4){width:64px}
@media(max-width:900px){{.mlh-grid,.mlh-detail-grid{{grid-template-columns:1fr}}.mlh-main{{font-size:16px}}}}
</style>
{END}
'''

for path in TARGETS:
    if not path.exists():
        print(path, "missing")
        continue
    s = path.read_text(errors="ignore")
    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")
    path.write_text(s, encoding="utf-8")
    print(path, "injected matchup line history summary")
