#!/usr/bin/env python3
from pathlib import Path
import json
import math
import re
import subprocess
import tempfile

ROOT = Path.cwd()
INDEX = ROOT / "index.html"
DASH = ROOT / "data" / "bets" / "betting_dashboard.json"

if not INDEX.exists():
    raise SystemExit("Missing index.html")
if not DASH.exists():
    raise SystemExit("Missing data/bets/betting_dashboard.json")

html = INDEX.read_text(encoding="utf-8", errors="ignore")
backup = INDEX.with_suffix(".html.bak_betting_safe")
backup.write_text(html, encoding="utf-8")

# Remove prior embedded betting JSON.
html = re.sub(
    r'<script id="betting-dashboard-data" type="application/json">.*?</script>\s*',
    "",
    html,
    flags=re.S,
)

dashboard = json.loads(DASH.read_text(encoding="utf-8"))

def clean_json_obj(obj):
    if obj is None:
        return None
    try:
        import pandas as pd
        if pd.isna(obj):
            return None
    except Exception:
        pass
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {str(k): clean_json_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json_obj(v) for v in obj]
    return obj

payload = clean_json_obj({"dashboard": dashboard})
json_text = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
data_script = f'<script id="betting-dashboard-data" type="application/json">{json_text}</script>'
html = html.replace("</body>", data_script + "\n</body>")

new_render = r'''function renderBetting() {
  function betDashData() {
    const el = document.getElementById('betting-dashboard-data');
    if (!el) return null;
    try { return JSON.parse(el.textContent || '{}').dashboard || null; }
    catch(e) { return null; }
  }
  function money(v) {
    const n = Number(v || 0);
    return '$' + n.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
  }
  function safe(v) {
    return escapeHtml(v == null || v === '' ? '—' : String(v));
  }
  function odds(v) {
    if (v == null || v === '' || Number.isNaN(Number(v))) return '—';
    const n = Number(v);
    return n > 0 ? '+' + n : String(n);
  }
  function pctValue(v) {
    if (v == null || v === '' || Number.isNaN(Number(v))) return '—';
    return (Number(v) * 100).toFixed(0) + '%';
  }
  function pctSigned(v) {
    if (v == null || v === '' || Number.isNaN(Number(v))) return '—';
    const n = Number(v) * 100;
    return (n > 0 ? '+' : '') + n.toFixed(1) + '%';
  }
  function fmtClv(v, suffix='') {
    if (v == null || v === '' || Number.isNaN(Number(v))) return '—';
    const n = Number(v);
    const sign = n > 0 ? '+' : '';
    return sign + n.toFixed(2) + suffix;
  }
  function clvClass(v) {
    if (v == null || v === '' || Number.isNaN(Number(v))) return '';
    const n = Number(v);
    return n > 0 ? 'gdPos' : n < 0 ? 'gdNeg' : '';
  }
  function beatClvBadge(v) {
    const x = String(v || '').toLowerCase();
    if (x === 'yes') return '<span class="gdBadge gdBadgeYes">Yes</span>';
    if (x === 'no') return '<span class="gdBadge gdBadgeNo">No</span>';
    return '<span class="gdBadge">—</span>';
  }
  function rowBy(arr, key, val) {
    return (arr || []).find(r => String(r[key] || '').toLowerCase() === String(val).toLowerCase()) || {};
  }
  function betCategory(r) {
    const desc = String(r['Bet Description'] || '').toLowerCase();
    if (desc.includes('win total')) return 'win-total';
    if (desc.includes('conf')) return 'future';
    if (desc.includes('week 1')) return 'week1';
    return 'other';
  }
  function chartPointValue(v) {
    if (v == null || v === '' || Number.isNaN(Number(v))) return 0;
    return Number(v);
  }
  function betTable(rows) {
    if (!rows || !rows.length) return '<div class="gdEmpty">No open bets.</div>';
    return `
      <table class="gdTable" id="gdOpenBetsTable">
        <thead>
          <tr>
            <th>Date</th><th>Bet</th><th>Category</th><th>Book</th><th>Stake</th><th>Bet</th><th>Current Market</th><th>Beat CLV?</th><th>No-Vig CLV</th><th>No-Vig EV</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(r=>`
            <tr data-bet-filter-row="1" data-bet-type="${betCategory(r)}">
              <td>${safe(r.Date)}</td>
              <td><b>${safe(r.Bet)}</b><div class="gdSubtle">${safe(r.team_guess)} ${safe(r.side)}</div></td>
              <td>${safe(r.clv_category || r.market_category)}</td>
              <td>${safe(r.Sportsbook)}</td>
              <td>${money(r.stake)}</td>
              <td>${safe(r.bet_line)} / ${odds(r.bet_price)}<div class="gdSubtle">${safe(r['Bet Description'])} · ${safe(r.Source)}</div></td>
              <td>${safe(r.current_market_line)} / ${odds(r.current_market_price)}<div class="gdSubtle">${safe(r.current_market_book || r.current_market_note || 'No match yet')}</div></td>
              <td>${beatClvBadge(r.beat_clv)}</td>
              <td class="${clvClass(r.clv_pct_current)}">${pctSigned(r.clv_pct_current)}<div class="gdSubtle">Line ${fmtClv(r.line_clv_current)}</div></td>
              <td class="${clvClass(r.ev_current_pct)}">${pctSigned(r.ev_current_pct)}<div class="gdSubtle">${money(r.ev_current_dollars)}</div></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }
  function breakdown(rows, labelKey) {
    if (!rows || !rows.length) return '<div class="gdEmpty">No rows.</div>';
    return `
      <table class="gdMiniTable">
        <thead><tr><th>${safe(labelKey)}</th><th>Bets</th><th>Open</th><th>Stake</th></tr></thead>
        <tbody>
          ${rows.map(r=>`
            <tr>
              <td>${safe(r[labelKey])}</td>
              <td>${safe(r.bets)}</td>
              <td>${safe(r.open)}</td>
              <td>${money(r.stake)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }
  function perfChart(history) {
    const phases = ['Preseason','Week 1','Week 2','Week 3','Week 4','Week 5','Week 6','Week 7','Week 8','Week 9','Week 10','Week 11','Week 12','Week 13','Week 14','Week 15','Playoffs'];
    const latest = {};
    (history || []).forEach(r => { if (r.season_phase) latest[r.season_phase] = r; });
    const rows = phases.map(p => latest[p] || {season_phase:p, realized_profit:null, total_ev_current_dollars:null});

    const vals = rows.flatMap(r => [chartPointValue(r.realized_profit), chartPointValue(r.total_ev_current_dollars)]);
    let min = Math.min(0, ...vals);
    let max = Math.max(0, ...vals);
    const pad = Math.max(25, (max - min) * 0.20);
    min -= pad;
    max += pad;

    const w = 920, h = 300, left = 74, right = 24, top = 20, bottom = 66;
    const plotW = w - left - right, plotH = h - top - bottom;
    const y = v => top + (max - chartPointValue(v)) / (max - min) * plotH;
    const x = i => left + (i / (rows.length - 1)) * plotW;

    const profitPoints = rows.map((r,i)=>`${x(i)},${y(r.realized_profit)}`).join(' ');
    const evPoints = rows.map((r,i)=>`${x(i)},${y(r.total_ev_current_dollars)}`).join(' ');
    const zeroY = y(0);
    const tickVals = [max, (max + 0) / 2, 0, (min + 0) / 2, min];

    return `
      <svg class="gdChart" viewBox="0 0 ${w} ${h}" role="img" aria-label="Profit loss and EV over time">
        ${tickVals.map(v=>`
          <line x1="${left}" y1="${y(v)}" x2="${w-right}" y2="${y(v)}" class="gdYGrid"></line>
          <text x="${left-10}" y="${y(v)+4}" text-anchor="end" class="gdYAxis">${money(v)}</text>
        `).join('')}
        <line x1="${left}" y1="${zeroY}" x2="${w-right}" y2="${zeroY}" class="gdAxisZero"></line>
        <polyline points="${evPoints}" class="gdLine gdLineEv"></polyline>
        <polyline points="${profitPoints}" class="gdLine gdLineProfit"></polyline>
        ${rows.map((r,i)=>`<circle cx="${x(i)}" cy="${y(r.total_ev_current_dollars)}" r="3" class="gdDotEv"><title>${safe(r.season_phase)} EV ${money(r.total_ev_current_dollars)}</title></circle>`).join('')}
        ${rows.map((r,i)=>`<circle cx="${x(i)}" cy="${y(r.realized_profit)}" r="3" class="gdDotProfit"><title>${safe(r.season_phase)} P/L ${money(r.realized_profit)}</title></circle>`).join('')}
        ${rows.map((r,i)=> i%2===0 || r.season_phase==='Preseason' || r.season_phase==='Playoffs' ? `<text x="${x(i)}" y="${h-24}" class="gdXAxis" transform="rotate(-35 ${x(i)} ${h-24})">${safe(r.season_phase)}</text>` : '').join('')}
      </svg>
      <div class="gdLegend"><span><b class="profitSwatch"></b> Profit/Loss</span><span><b class="evSwatch"></b> No-Vig EV</span></div>
    `;
  }

  const dash = betDashData();
  const liveSheet = bettingSeason === '2025' ? BETTING_SHEET_URL.replace('gid=938568824','gid=1629429397') : BETTING_SHEET_URL;
  const liveCsv = bettingSeason === '2025' ? BETTING_2025_CSV_URL : BETTING_CSV_URL;

  if (!dash) {
    return `
      <div class="hero">
        <div>
          <div class="page-title">Betting</div>
          <div class="page-sub">No betting dashboard data found. Run the betting pull/build scripts first.</div>
        </div>
      </div>
    `;
  }

  const s = dash.summary || {};
  const openRows = dash.open_bets || [];
  const byType = dash.by_bet_description || [];
  const winTotals = rowBy(byType, 'Bet Description', 'Win Total');
  const confTitles = rowBy(byType, 'Bet Description', 'Conf Title');
  const week1 = rowBy(byType, 'Bet Description', 'Week 1');

  return `
    <style>
      .gdWrap{background:#f6f7f5;color:#102c1d;border-radius:18px;padding:22px;margin-top:4px}
      .gdTop{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin-bottom:20px}
      .gdTitle{font-size:34px;font-weight:900;letter-spacing:-.03em;color:#102c1d}
      .gdSub{font-size:14px;color:#5f6f65;margin-top:5px;max-width:760px}
      .gdActions{display:flex;gap:10px;flex-wrap:nowrap;justify-content:flex-end;align-items:flex-start}
      .gdBtn{background:#d6ff3f;color:#102c1d;border:1px solid #b9e52e;border-radius:4px;padding:11px 16px;font-weight:900;text-decoration:none;white-space:nowrap}
      .gdBtn.secondary{background:#fff;border-color:#cfd6d0}
      .gdGrid2{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:16px}
      .gdPanel{background:#fff;border:1px solid #cfd6d0;min-height:260px;display:grid;grid-template-columns:230px 1fr}
      .gdDark{background:#06351e;color:#fff;padding:24px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
      .gdDark h3{font-size:23px;margin:0 0 18px;color:#fff}
      .gdCircle{width:118px;height:118px;border:6px solid #d6ff3f;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:44px;font-weight:900;margin-bottom:18px}
      .gdDarkMetric{font-size:15px;color:#d7e8dd;margin-top:10px;font-weight:800}
      .gdDarkValue{font-size:19px;color:#fff;margin-top:4px}
      .gdLight{padding:24px}
      .gdTabs{display:flex;gap:28px;border-bottom:1px solid #cad1cb;margin-bottom:22px}
      .gdTabBtn{font-size:18px;font-weight:900;color:#888;padding:0 0 10px;background:transparent;border:0;cursor:pointer;text-align:left}
      .gdTabBtn.active{color:#102c1d;border-bottom:3px solid #102c1d}
      .gdPendingTabContent{min-height:190px}
      .gdPendingSummary{display:grid;grid-template-columns:1fr;gap:10px;margin-bottom:14px}
      .gdPendingMetric{border:1px solid #d7ddd8;background:#fbfcfb;padding:10px 14px;display:flex;align-items:center;justify-content:space-between;gap:16px;text-align:left;min-width:0}
      .gdPendingMetric .k{font-size:11px;color:#718077;text-transform:uppercase;font-weight:900;letter-spacing:.04em;line-height:1.15}
      .gdPendingMetric .v{font-size:20px;color:#06351e;font-weight:900;margin-top:0;white-space:nowrap}
      .gdPendingList{display:grid;gap:8px}
      .gdPendingBet{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;border-bottom:1px solid #e3e7e3;padding:7px 0}
      .gdPendingBet b{color:#102c1d}
      .gdPendingBetRight{text-align:right;font-weight:900;color:#102c1d}
      .gdGradedSummary{display:grid;grid-template-columns:1fr;gap:10px;margin-bottom:18px}
      .gdGradedMetric{border:1px solid #d7ddd8;background:#fbfcfb;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;gap:14px}
      .gdGradedMetric .k{font-size:12px;color:#718077;text-transform:uppercase;font-weight:900;letter-spacing:.04em}
      .gdGradedMetric .v{font-size:22px;color:#06351e;font-weight:900;white-space:nowrap}
      .gdEmpty{height:140px;display:flex;align-items:center;justify-content:center;flex-direction:column;color:#8a8f8b;font-weight:800;font-size:22px;text-align:center}
      .gdTiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:28px;margin-top:28px}
      .gdTile{background:#fff;border:1px solid #cfd6d0;min-height:180px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:18px}
      .gdTileTitle{font-size:21px;font-weight:900;color:#06351e;margin-bottom:22px}
      .gdTileValue{font-size:36px;font-weight:900;color:#102c1d}
      .gdTileSub{font-size:13px;color:#78847b;margin-top:8px}
      .gdSection{background:#fff;border:1px solid #cfd6d0;margin-top:28px;padding:20px}
      .gdSectionTitle{font-size:22px;font-weight:900;color:#102c1d;margin-bottom:6px}
      .gdSectionSub{font-size:13px;color:#69766e;margin-bottom:14px}
      .gdSplit{display:grid;grid-template-columns:2fr 1fr;gap:28px}
      .gdTable,.gdMiniTable{width:100%;border-collapse:collapse;font-size:13px}
      .gdTable th,.gdMiniTable th{text-align:left;color:#f6f7f5;border-bottom:2px solid #cfd6d0;padding:10px 9px;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
      .gdTable thead th{background:#15284f;color:#f6f7f5;text-shadow:none}
      .gdMiniTable thead th{background:#f6f7f5;color:#102c1d}
      .gdTable td,.gdMiniTable td{border-bottom:1px solid #e3e7e3;padding:10px 9px;color:#18251e;vertical-align:top}
      .gdSubtle{color:#7a857e;font-size:12px;margin-top:3px}
      .gdPos{color:#047857;font-weight:900}
      .gdNeg{color:#b91c1c;font-weight:900}
      .gdBadge{display:inline-block;border:1px solid #cfd6d0;border-radius:999px;padding:3px 9px;font-size:12px;font-weight:900;color:#65736a;background:#fff}
      .gdBadgeYes{border-color:#047857;color:#047857;background:#ecfdf5}
      .gdBadgeNo{border-color:#b91c1c;color:#b91c1c;background:#fef2f2}
      .gdMiniStack{display:grid;gap:18px}
      .gdChart{width:100%;height:300px;background:#fff}
      .gdAxisZero{stroke:#cfd6d0;stroke-width:1}
      .gdYGrid{stroke:#e1e6e1;stroke-width:1}
      .gdYAxis{font-size:12px;fill:#65736a;font-weight:800}
      .gdLine{fill:none;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}
      .gdLineProfit{stroke:#06351e}
      .gdLineEv{stroke:#b7f52f}
      .gdDotProfit{fill:#06351e}
      .gdDotEv{fill:#b7f52f;stroke:#06351e;stroke-width:1}
      .gdXAxis{font-size:11px;fill:#65736a;font-weight:700}
      .gdLegend{display:flex;gap:18px;align-items:center;margin-top:8px;color:#415146;font-size:13px;font-weight:800}
      .gdLegend b{display:inline-block;width:14px;height:4px;margin-right:6px;vertical-align:middle}
      .profitSwatch{background:#06351e}
      .evSwatch{background:#b7f52f}
      @media(max-width:1000px){
        .gdGrid2,.gdSplit{grid-template-columns:1fr}
        .gdPanel{grid-template-columns:1fr}
        .gdTiles{grid-template-columns:repeat(2,minmax(0,1fr))}
        .gdTop{flex-direction:column}
        .gdActions{flex-wrap:wrap;justify-content:flex-start}
      }
      @media(max-width:650px){
        .gdTiles{grid-template-columns:1fr}
        .gdTitle{font-size:28px}
      }
    
      .gdWeeklyTable th,.gdWeeklyTable td{font-size:12px;white-space:nowrap}
      .gdWeeklyPerf{margin-top:18px;overflow-x:auto}
</style>

    <div class="gdWrap">
      <div class="gdTop">
        <div>
          <div class="gdTitle">Betting Dashboard</div>
          <div class="gdSub">Portfolio dashboard pulled from your Google Sheet. Built for pending exposure, graded performance, CLV tracking, and no-vig EV.</div>
        </div>
        <div class="gdActions">
          <button class="gdBtn secondary" onclick="setBettingSeason('2026')">2026</button>
          <button class="gdBtn secondary" onclick="setBettingSeason('2025')">2025</button>
          <a class="gdBtn" href="${liveSheet}" target="_blank" rel="noopener">Open Live Sheet</a>
          <a class="gdBtn secondary" href="${liveCsv}" target="_blank" rel="noopener">Open CSV</a>
        </div>
      </div>

      <div class="gdGrid2">
        <div>
          <div class="gdTitle" style="font-size:26px;margin-bottom:12px">Pending Bets</div>
          <div class="gdPanel">
            <div class="gdDark">
              <h3>Open Portfolio</h3>
              <div class="gdCircle">${safe(s.open)}</div>
              <div class="gdDarkMetric">Total Risk</div>
              <div class="gdDarkValue">${money(s.exposure)}</div>
              <div class="gdDarkMetric">Average Bet</div>
              <div class="gdDarkValue">${money(s.avg_bet)}</div>
            </div>
            <div class="gdLight">
              <div class="gdTabs">
                <button class="gdTabBtn active" data-bet-filter="all">All Open</button>
                <button class="gdTabBtn" data-bet-filter="win-total">Win Totals</button>
                <button class="gdTabBtn" data-bet-filter="future">Futures</button>
                <button class="gdTabBtn" data-bet-filter="week1" style="margin-left:auto">Week 1</button>
              </div>
              <div id="gdPendingTabContent" class="gdPendingTabContent"></div>
            </div>
          </div>
        </div>

        <div>
          <div class="gdTitle" style="font-size:26px;margin-bottom:12px">Graded Bets</div>
          <div class="gdPanel">
            <div class="gdDark">
              <h3>Season Results</h3>
              <div class="gdDarkValue" style="font-size:30px">${money(s.profit)}</div>
              <div class="gdDarkMetric">Record</div>
              <div class="gdDarkValue">${safe(s.wins)}-${safe(s.losses)}-${safe(s.pushes)}</div>
              <div class="gdDarkMetric">ROI</div>
              <div class="gdDarkValue">${s.roi == null ? '0.00%' : (Number(s.roi)*100).toFixed(2)+'%'}</div>
            </div>
            <div class="gdLight">
              <div class="gdGradedSummary">
                <div class="gdGradedMetric"><div class="k">Settled</div><div class="v">${safe(s.settled)}</div></div>
                <div class="gdGradedMetric"><div class="k">Profit</div><div class="v">${money(s.profit)}</div></div>
                <div class="gdGradedMetric"><div class="k">ROI</div><div class="v">${s.roi == null ? '—' : pctValue(s.roi)}</div></div>
              </div>
              <div class="gdPendingList">
                <div class="gdPendingBet"><div><b>Today</b><div class="gdSubtle">No graded bets yet</div></div><div class="gdPendingBetRight">0-0-0</div></div>
                <div class="gdPendingBet"><div><b>Last 7 Days</b><div class="gdSubtle">No graded bets yet</div></div><div class="gdPendingBetRight">0-0-0</div></div>
                <div class="gdPendingBet"><div><b>All Tracked</b><div class="gdSubtle">${safe(s.settled)} settled</div></div><div class="gdPendingBetRight">${safe(s.wins)}-${safe(s.losses)}-${safe(s.pushes)}</div></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="gdTiles">
        <div class="gdTile">
          <div class="gdTileTitle">Win Totals</div>
          <div class="gdTileValue">${safe(winTotals.bets || 0)}</div>
          <div class="gdTileSub">${money(winTotals.stake || 0)} exposure</div>
        </div>
        <div class="gdTile">
          <div class="gdTileTitle">Conference Futures</div>
          <div class="gdTileValue">${safe(confTitles.bets || 0)}</div>
          <div class="gdTileSub">${money(confTitles.stake || 0)} exposure</div>
        </div>
        <div class="gdTile">
          <div class="gdTileTitle">% Bets Beating No-Vig CLV</div>
          <div class="gdTileValue">${pctValue(s.pct_bets_beating_current_clv)}</div>
          <div class="gdTileSub">${safe(s.current_clv_matched || 0)} matched · ${safe(s.current_clv_positive || 0)} positive</div>
        </div>
        <div class="gdTile">
          <div class="gdTileTitle">Avg No-Vig EV / Bet</div>
          <div class="gdTileValue">${pctSigned(s.avg_ev_current_pct)}</div>
          <div class="gdTileSub">${money(s.avg_ev_current_dollars)} avg · ${money(s.total_ev_current_dollars)} total EV</div>
        </div>
      </div>

      <div class="gdSection">
        <div class="gdSectionTitle">YTD Profit/Loss vs YTD No-Vig EV</div>
        <div class="gdSectionSub">Cumulative/YTD values by season phase. Profit/Loss updates when bets are graded; EV tracks no-vig, line-adjusted market edge.</div>
        ${perfChart(dash.performance_history || [])}
      </div>

      <div class="gdSplit">
        <div class="gdSection">
          
        <div class="gdSection gdWeeklyPerf">
          <div class="gdSectionTitle">Weekly Betting Performance</div>
          <div class="gdSectionSub">Weekly values plus cumulative/YTD profit and no-vig EV.</div>
          <table class="gdMiniTable gdWeeklyTable">
            <thead>
              <tr>
                <th>Week</th>
                <th>Bets</th>
                <th>Stake</th>
                <th>W-L-P</th>
                <th>Weekly P/L</th>
                <th>YTD P/L</th>
                <th>Beat CLV</th>
                <th>Avg CLV</th>
                <th>No-Vig EV</th>
                <th>YTD EV</th>
              </tr>
            </thead>
            <tbody>
              ${(dash.by_week_performance || []).map(r => `
                <tr>
                  <td>${safe(r.week)}</td>
                  <td>${safe(r.bets)}</td>
                  <td>${money(r.stake)}</td>
                  <td>${safe(r.wins)}-${safe(r.losses)}-${safe(r.pushes)}</td>
                  <td class="${clvClass(r.weekly_profit)}">${money(r.weekly_profit)}</td>
                  <td class="${clvClass(r.ytd_profit)}">${money(r.ytd_profit)}</td>
                  <td>${safe(r.beat_clv_yes)}-${safe(r.beat_clv_no)}<div class="gdSubtle">${pctValue(r.beat_clv_pct)}</div></td>
                  <td class="${clvClass(r.avg_no_vig_clv_pct)}">${pctSigned(r.avg_no_vig_clv_pct)}</td>
                  <td class="${clvClass(r.weekly_no_vig_ev)}">${money(r.weekly_no_vig_ev)}</td>
                  <td class="${clvClass(r.ytd_no_vig_ev)}">${money(r.ytd_no_vig_ev)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

<div class="gdSectionTitle">Bet Details</div>
          <div class="gdSectionSub">Detailed table for the selected category. Pulled from your Google Sheet. Updated ${safe(dash.updated_at)}.</div>
          ${betTable(openRows)}
        </div>

        <div class="gdMiniStack">
          <div class="gdSection">
            <div class="gdSectionTitle">CLV by Category</div>
            <div class="gdSectionSub">No-vig CLV and EV grouped by bet type.</div>
            <table class="gdMiniTable">
              <thead><tr><th>Category</th><th>Beat</th><th>Avg CLV</th><th>EV</th></tr></thead>
              <tbody>
                ${(dash.by_clv_category || []).map(r => `
                  <tr>
                    <td>${safe(r.category)}<div class="gdSubtle">${safe(r.bets)} bets · ${money(r.stake)}</div></td>
                    <td>${safe(r.beat_clv_yes)}-${safe(r.beat_clv_no)}<div class="gdSubtle">${pctValue(r.beat_clv_pct)}</div></td>
                    <td class="${clvClass(r.avg_no_vig_clv_pct)}">${pctSigned(r.avg_no_vig_clv_pct)}</td>
                    <td class="${clvClass(r.avg_no_vig_ev_pct)}">${money(r.total_no_vig_ev_dollars)}<div class="gdSubtle">${pctSigned(r.avg_no_vig_ev_pct)}</div></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
          <div class="gdSection">
            <div class="gdSectionTitle">By Sportsbook</div>
            ${breakdown(dash.by_sportsbook || [], 'Sportsbook')}
          </div>
          <div class="gdSection">
            <div class="gdSectionTitle">By Bet Type</div>
            ${breakdown(dash.by_bet_description || [], 'Bet Description')}
          </div>
          <div class="gdSection">
            <div class="gdSectionTitle">By Source</div>
            ${breakdown(dash.by_source || [], 'Source')}
          </div>
        </div>
      </div>
    </div>
  `;
}'''

new_mount = r'''function mountBettingFilters() {
  const buttons = Array.from(document.querySelectorAll('[data-bet-filter]'));
  const tableRows = Array.from(document.querySelectorAll('[data-bet-filter-row]'));
  const panel = document.getElementById('gdPendingTabContent');
  if (!buttons.length || !panel) return;

  function escLocal(v) {
    return String(v == null || v === '' ? '—' : v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  function moneyLocal(v) {
    const n = Number(v || 0);
    return '$' + n.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
  }
  function pctLocal(v) {
    if (v == null || v === '' || Number.isNaN(Number(v))) return '—';
    const n = Number(v) * 100;
    return (n > 0 ? '+' : '') + n.toFixed(1) + '%';
  }
  function classifyBet(r) {
    const desc = String(r['Bet Description'] || '').toLowerCase();
    if (desc.includes('win total')) return 'win-total';
    if (desc.includes('conf')) return 'future';
    if (desc.includes('week 1')) return 'week1';
    return 'other';
  }
  function labelFor(filter) {
    if (filter === 'win-total') return 'Win Totals';
    if (filter === 'future') return 'Futures';
    if (filter === 'week1') return 'Week 1';
    return 'All Open';
  }
  function getDashboardRows() {
    const el = document.getElementById('betting-dashboard-data');
    if (!el) return [];
    try {
      const d = JSON.parse(el.textContent || '{}').dashboard || {};
      return d.open_bets || [];
    } catch(e) {
      return [];
    }
  }
  function renderPanel(filter) {
    const all = getDashboardRows();
    const rows = filter === 'all' ? all : all.filter(r => classifyBet(r) === filter);
    const exposure = rows.reduce((a,r)=>a + Number(r.stake || 0), 0);
    const matched = rows.filter(r => String(r.current_market_match).toLowerCase() === 'true').length;
    const ev = rows.reduce((a,r)=>a + Number(r.ev_current_dollars || 0), 0);

    const preview = rows.slice(0, 5).map(r => `
      <div class="gdPendingBet">
        <div>
          <b>${escLocal(r.Bet)}</b>
          <div class="gdSubtle">${escLocal(r.Sportsbook)} · ${escLocal(r['Bet Description'])} · CLV ${pctLocal(r.clv_pct_current)}</div>
        </div>
        <div class="gdPendingBetRight">
          ${moneyLocal(r.stake)}
          <div class="gdSubtle">EV ${moneyLocal(r.ev_current_dollars)}</div>
        </div>
      </div>
    `).join('');

    panel.innerHTML = `
      <div class="gdPendingSummary">
        <div class="gdPendingMetric"><div class="k">${escLocal(labelFor(filter))}</div><div class="v">${rows.length}</div></div>
        <div class="gdPendingMetric"><div class="k">Exposure</div><div class="v">${moneyLocal(exposure)}</div></div>
        <div class="gdPendingMetric"><div class="k">Current EV</div><div class="v">${moneyLocal(ev)}</div></div>
      </div>
      <div class="gdPendingList">
        ${preview || '<div class="gdEmpty">No bets in this category.</div>'}
      </div>
      <div class="gdSubtle" style="margin-top:10px">${matched} of ${rows.length} matched to no-vig CLV.</div>
    `;
  }
  function applyFilter(filter) {
    buttons.forEach(b => b.classList.toggle('active', b.getAttribute('data-bet-filter') === filter));
    tableRows.forEach(r => {
      const t = r.getAttribute('data-bet-type');
      r.style.display = (filter === 'all' || t === filter) ? '' : 'none';
    });
    renderPanel(filter);
  }

  buttons.forEach(btn => {
    btn.addEventListener('click', () => applyFilter(btn.getAttribute('data-bet-filter') || 'all'));
  });

  applyFilter('all');
}'''

def replace_between(src, start_marker, end_marker, replacement):
    start = src.find(start_marker)
    end = src.find(end_marker, start)
    if start == -1 or end == -1:
        raise SystemExit(f"Could not locate {start_marker} to {end_marker}")
    return src[:start] + replacement + "\n" + src[end:]

html = replace_between(html, "function renderBetting() {", "\nfunction mountBettingFilters()", new_render)
html = replace_between(html, "function mountBettingFilters() {", "\n\nfunction dashboardCounts()", new_mount)

# Write candidate and syntax-check all script blocks with node if available.
candidate = html

try:
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", candidate, flags=re.S)
    joined = "\n".join(s for s in scripts if "application/json" not in s[:100])
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(joined)
        temp_js = f.name
    check = subprocess.run(["node", "--check", temp_js], text=True, capture_output=True)
    if check.returncode != 0:
        INDEX.write_text(backup.read_text(encoding="utf-8"), encoding="utf-8")
        print(check.stdout)
        print(check.stderr)
        raise SystemExit("JavaScript syntax check failed. Restored backup.")
except FileNotFoundError:
    print("node not found; skipped JS syntax check")

INDEX.write_text(candidate, encoding="utf-8")

print("updated:", INDEX)
print("backup:", backup)
print("bets:", dashboard.get("summary", {}).get("bets"))
print("exposure:", dashboard.get("summary", {}).get("exposure"))
print("clv matched:", dashboard.get("summary", {}).get("current_clv_matched"))
