from pathlib import Path
import argparse
import re, json
import hashlib
import pandas as pd
import math

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]
HISTORY = Path("data/history/matchup_line_history_clean.csv")
ASSET = Path("data/site/matchup_line_history.json")

START = "<!-- matchup-line-history-start -->"
END = "<!-- matchup-line-history-end -->"

def clean_num(x):
    try:
        if x is None or pd.isna(x):
            return None
        v = float(x)
        if math.isnan(v):
            return None
        return round(v, 4)
    except Exception:
        return None

def clean_str(x):
    if x is None or pd.isna(x):
        return None
    return str(x)

def load_site_game_lookup():
    """Read the canonical V2 matchup view for week/conference metadata."""
    import json
    idx = {}
    ip = Path("data/site/matchups_view.json")
    if not ip.exists():
        return idx
    try:
        db = json.loads(ip.read_text())
    except Exception:
        return idx
    for row in db.get("games", []):
        g = row.get("game") or {}
        gid = str(g.get("game_id") or "")
        if gid:
            idx[gid] = g
    return idx

def build_payload():
    if not HISTORY.exists():
        return {}

    df = pd.read_csv(HISTORY)
    if df.empty:
        return {}

    if "snapshot_label" not in df.columns:
        df["snapshot_label"] = df.get("source", "History")
    if "snapshot_ts" not in df.columns:
        df["snapshot_ts"] = df.get("snapshot_date", "")

    sort_cols = [c for c in ["snapshot_date", "snapshot_ts", "snapshot_label"] if c in df.columns]

    site_games = load_site_game_lookup()

    out = {}
    for gid, g in df.groupby("game_id"):
        site_game = site_games.get(str(gid), {})
        rows = []
        for _, r in g.sort_values(sort_cols).iterrows():
            rows.append({
                "snapshot_date": clean_str(r.get("snapshot_date")),
                "snapshot_ts": clean_str(r.get("snapshot_ts") or r.get("snapshot_date")),
                "snapshot_label": clean_str(r.get("snapshot_label")),
                "game_date": clean_str(r.get("game_date")),
                "week": clean_num(r.get("week") if "week" in r.index else r.get("game_week")),
                "site_week": clean_num(site_game.get("week")),
                "conference": clean_str(r.get("conference") if "conference" in r.index else site_game.get("conference") or site_game.get("conf")),
                "away_team": clean_str(r.get("away_team")),
                "home_team": clean_str(r.get("home_team")),
                "market_spread_home": clean_num(r.get("market_spread_home")),
                "market_spread_open_home": clean_num(r.get("market_spread_open_home")),
                "model_spread_home": clean_num(r.get("model_spread_home")),
                "projected_margin_home": clean_num(r.get("projected_margin_home")),
                "market_total": clean_num(r.get("market_total")),
                "market_total_open": clean_num(r.get("market_total_open")),
                "projected_total": clean_num(r.get("projected_total")),
                "market_spread_price": clean_num(r.get("market_spread_price")),
                "market_spread_book": clean_str(r.get("market_spread_book")),
                "market_total_book": clean_str(r.get("market_total_book")),
                "market_total_over_price": clean_num(r.get("market_total_over_price")),
                "market_total_under_price": clean_num(r.get("market_total_under_price")),
                "market_line_source": clean_str(r.get("market_line_source") or r.get("source")),
                "source": clean_str(r.get("source") or r.get("market_line_source")),
                "market_spread_last_update": clean_str(r.get("market_spread_last_update")),
                "market_total_last_update": clean_str(r.get("market_total_last_update")),
            })
        out[str(gid)] = rows

    return out

def inject(path, asset_version):
    if not path.exists():
        return

    html = path.read_text(errors="ignore")

    block = f"""{START}
<script id="matchup-line-history-js">
window.MATCHUP_LINE_HISTORY = window.MATCHUP_LINE_HISTORY || {{}};
window.MATCHUP_LINE_HISTORY_LOADED = false;
window.MATCHUP_LINE_HISTORY_URL = "data/site/matchup_line_history.json?v={asset_version}";
window.loadMatchupLineHistory = window.loadMatchupLineHistory || function() {{
  if (window.MATCHUP_LINE_HISTORY_READY) return window.MATCHUP_LINE_HISTORY_READY;
  window.MATCHUP_LINE_HISTORY_READY = fetch(window.MATCHUP_LINE_HISTORY_URL, {{cache:'force-cache'}})
  .then(response => {{
    if (!response.ok) throw new Error(`Line history HTTP ${{response.status}}`);
    return response.json();
  }})
  .then(payload => {{
    window.MATCHUP_LINE_HISTORY = payload || {{}};
    window.MATCHUP_LINE_HISTORY_LOADED = true;
    window.dispatchEvent(new CustomEvent('matchup-line-history-ready'));
    return window.MATCHUP_LINE_HISTORY;
  }})
  .catch(error => {{
    console.error('Line history failed to load', error);
    window.dispatchEvent(new CustomEvent('matchup-line-history-error', {{detail:String(error)}}));
    return window.MATCHUP_LINE_HISTORY;
  }});
  return window.MATCHUP_LINE_HISTORY_READY;
}};
window.loadMatchupLineHistory();

function lineHistoryRowsForGame(g) {{
  if (!g) return [];
  return (window.MATCHUP_LINE_HISTORY || {{}})[String(g.game_id)] || [];
}}

function fmtLineNum(v) {{
  const n = Number(v);
  if (!Number.isFinite(n)) return '—';
  return n.toFixed(1).replace(/\\.0$/, '');
}}

function teamLineText(home, away, marginHome) {{
  const n = Number(marginHome);
  if (!Number.isFinite(n)) return '—';
  if (n < 0) return `${{home}} ${{fmtLineNum(n)}}`;
  if (n > 0) return `${{away}} +${{fmtLineNum(n)}}`;
  return 'Pick';
}}

function movementTone(delta) {{
  const d = Number(delta);
  if (!Number.isFinite(d) || Math.abs(d) < 0.25) return 'warn';
  return d > 0 ? 'good' : 'bad';
}}

function miniLineChart(values, modelValue) {{
  const nums = values.filter(v => Number.isFinite(Number(v))).map(Number);
  if (!nums.length) return '<div class="muted small">No history yet</div>';

  const all = nums.slice();
  if (Number.isFinite(Number(modelValue))) all.push(Number(modelValue));

  const min = Math.min(...all);
  const max = Math.max(...all);
  const pad = Math.max(1, (max - min) * 0.18);
  const lo = min - pad;
  const hi = max + pad;
  const w = 320, h = 70, left = 12, right = 12, top = 10, bottom = 16;
  const spanX = w - left - right;
  const spanY = h - top - bottom;
  const x = i => left + (nums.length === 1 ? spanX : i * spanX / (nums.length - 1));
  const y = v => top + (hi - v) * spanY / (hi - lo);

  const pts = nums.map((v,i) => `${{x(i).toFixed(1)}},${{y(v).toFixed(1)}}`).join(' ');
  const dots = nums.map((v,i) => `<circle cx="${{x(i).toFixed(1)}}" cy="${{y(v).toFixed(1)}}" r="2.8"></circle>`).join('');

  let model = '';
  if (Number.isFinite(Number(modelValue))) {{
    const my = y(Number(modelValue)).toFixed(1);
    model = `<line x1="${{left}}" x2="${{w-right}}" y1="${{my}}" y2="${{my}}" stroke-dasharray="4 3"></line>`;
  }}

  return `
    <svg class="mini-line-chart" viewBox="0 0 ${{w}} ${{h}}" role="img">
      <line x1="${{left}}" x2="${{w-right}}" y1="${{h-bottom}}" y2="${{h-bottom}}"></line>
      ${{model}}
      <polyline points="${{pts}}"></polyline>
      ${{dots}}
    </svg>
  `;
}}

function matchupLineHistoryCard(g) {{
  const rows = lineHistoryRowsForGame(g);
  const latest = rows.length ? rows[rows.length - 1] : null;
  const home = g.home_team || (latest && latest.home_team) || 'Home';
  const away = g.away_team || (latest && latest.away_team) || 'Away';

  const curSpread = latest?.market_spread_home ?? g.market_spread_home;
  const openSpread = latest?.market_spread_open_home ?? g.market_spread_open_home;
  const modelSpread = latest?.model_spread_home ?? (-Number(g.projected_margin_home || 0));
  const projectedMargin = latest?.projected_margin_home ?? g.projected_margin_home;

  const curTotal = latest?.market_total ?? g.market_total;
  const openTotal = latest?.market_total_open ?? g.market_total_open;
  const modelTotal = latest?.projected_total ?? g.projected_total;

  const spreadMove = Number.isFinite(Number(openSpread)) && Number.isFinite(Number(curSpread)) ? Number(curSpread) - Number(openSpread) : null;
  const totalMove = Number.isFinite(Number(openTotal)) && Number.isFinite(Number(curTotal)) ? Number(curTotal) - Number(openTotal) : null;

  const spreadEdge = Number.isFinite(Number(projectedMargin)) && Number.isFinite(Number(curSpread))
    ? Number(projectedMargin) + Number(curSpread)
    : null;

  const totalEdge = Number.isFinite(Number(modelTotal)) && Number.isFinite(Number(curTotal))
    ? Number(modelTotal) - Number(curTotal)
    : null;

  const spreadValues = rows.map(r => r.market_spread_home);
  const totalValues = rows.map(r => r.market_total);

  return `
    <section class="card line-history-card">
      <h3>Line Movement</h3>
      <div class="muted small">Market history vs active model projection</div>

      <div class="line-history-grid">
        <div class="line-history-panel">
          <div class="line-history-head">
            <strong>Spread</strong>
            <span class="pill ${{movementTone(spreadMove)}}">Move ${{spreadMove == null ? '—' : fmtLineNum(spreadMove)}}</span>
          </div>
          <div class="small">
            Open: <strong>${{teamLineText(home, away, openSpread)}}</strong> ·
            Current: <strong>${{teamLineText(home, away, curSpread)}}</strong> ·
            Model: <strong>${{teamLineText(home, away, -Number(modelSpread))}}</strong>
          </div>
          <div class="small muted">Edge: ${{spreadEdge == null ? '—' : fmtLineNum(spreadEdge)}} pts vs market</div>
          ${{miniLineChart(spreadValues, curSpread)}}
        </div>

        <div class="line-history-panel">
          <div class="line-history-head">
            <strong>Total</strong>
            <span class="pill ${{movementTone(totalMove)}}">Move ${{totalMove == null ? '—' : fmtLineNum(totalMove)}}</span>
          </div>
          <div class="small">
            Open: <strong>${{fmtLineNum(openTotal)}}</strong> ·
            Current: <strong>${{fmtLineNum(curTotal)}}</strong> ·
            Model: <strong>${{fmtLineNum(modelTotal)}}</strong>
          </div>
          <div class="small muted">Edge: ${{totalEdge == null ? '—' : fmtLineNum(totalEdge)}} pts vs market</div>
          ${{miniLineChart(totalValues, modelTotal)}}
        </div>
      </div>
    </section>
  `;
}}
</script>
<style id="matchup-line-history-css">
.line-history-card {{ margin-top: 14px; }}
.line-history-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:10px; }}
.line-history-panel {{ border:1px solid var(--border); border-radius:12px; padding:12px; background:rgba(255,255,255,.03); }}
.line-history-head {{ display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:6px; }}
.mini-line-chart {{ width:100%; height:70px; margin-top:8px; overflow:visible; }}
.mini-line-chart line {{ stroke: currentColor; opacity:.28; stroke-width:1.2; }}
.mini-line-chart polyline {{ fill:none; stroke: currentColor; stroke-width:2.2; opacity:.9; }}
.mini-line-chart circle {{ fill: currentColor; opacity:.9; }}
@media (max-width: 800px) {{ .line-history-grid {{ grid-template-columns:1fr; }} }}
</style>
{END}"""

    if START in html and END in html:
        html = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\s*", block.strip() + "\n\n", html, flags=re.S)
    else:
        html = html.replace("</body>", block.strip() + "\n\n</body>")

    # Insert card into matchup render if obvious anchor exists.
    if "matchupLineHistoryCard(g)" not in html:
        anchors = [
            "${matchupModelMarketCard(g)}",
            "${modelMarketCard(g)}",
            "modelMarketCard(g)",
        ]
        for a in anchors:
            if a in html:
                html = html.replace(a, a + "\\n${matchupLineHistoryCard(g)}", 1)
                break

    path.write_text(html, encoding="utf-8")
    print(path, "injected external line history loader", asset_version)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--asset-only",
        action="store_true",
        help="refresh only data/site/matchup_line_history.json without changing HTML",
    )
    args = parser.parse_args()
    payload = build_payload()
    serialized = json.dumps(payload, separators=(",", ":"))
    asset_version = hashlib.sha256(serialized.encode()).hexdigest()[:12]
    ASSET.parent.mkdir(parents=True, exist_ok=True)
    ASSET.write_text(serialized + "\n", encoding="utf-8")
    print("games with line history:", len(payload))
    print("history rows:", sum(len(v) for v in payload.values()))
    print("asset:", ASSET, "version:", asset_version, "bytes:", ASSET.stat().st_size)
    if not args.asset_only:
        for p in TARGETS:
            inject(p, asset_version)

if __name__ == "__main__":
    main()
