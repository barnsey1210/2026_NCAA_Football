#!/usr/bin/env python3
from pathlib import Path

p = Path("index.html")
if not p.exists():
    raise SystemExit("index.html not found; run from ~/NCAAF_AUTO")

s = p.read_text(errors="ignore")

helpers = r'''
function dashboardCleanOddsShortV2(v) {
  if (v == null || v === '' || String(v).toLowerCase() === 'nan') return '';
  const n = Number(String(v).replace('+',''));
  if (!Number.isFinite(n)) return String(v);
  return n > 0 ? `+${Math.round(n)}` : `${Math.round(n)}`;
}

function dashboardCleanMoveReasonV2(reason) {
  return String(reason || '')
    .replace(/\s*\(implied probability[^)]*\)/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function dashboardFormatSimpleDateV2(v) {
  if (!v) return '';
  const raw = String(v).trim();

  // Date-only strings should display as the exact market date, not shift by timezone.
  const m = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (m) {
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return `${months[Number(m[2]) - 1]} ${Number(m[3])} ${m[1]}`;
  }

  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw;
  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  }).format(d).replace(',', '');
}


function dashboardExpandableListV2(rows, cardFn, initialCount, idBase) {
  rows = rows || [];
  const total = rows.length;
  const initial = rows.slice(0, initialCount).map(cardFn).join('');
  const rest = rows.slice(initialCount).map(cardFn).join('');

  if (total <= initialCount) return initial;

  return `${initial}
    <div id="${idBase}-extra" style="display:none">${rest}</div>
    <button class="dashboard-action-btn" style="margin-top:10px" onclick="
      const el=document.getElementById('${idBase}-extra');
      const btn=this;
      if (!el) return;
      const open = el.style.display !== 'none';
      el.style.display = open ? 'none' : 'block';
      btn.textContent = open ? 'Show all ${total} moves' : 'Show less';
    ">Show all ${total} moves</button>`;
}

function dashboardMarketMoveCardCleanV2(r) {
  const title = r.title || `${r.team || ''} Market Move`.trim();
  const reason = dashboardCleanMoveReasonV2(r.reason || r.summary || '');

  const lineMatch = reason.match(/line\s+([+-]?\d+(?:\.\d+)?)\s*→\s*([+-]?\d+(?:\.\d+)?)/i);
  const overMatch = reason.match(/Over\s+([+-]?\d+(?:\.\d+)?)\s*(?:wins)?:\s*([+-]?\d+(?:\.\d+)?)\s*→\s*([+-]?\d+(?:\.\d+)?)/i);
  const underMatch = reason.match(/Under\s+([+-]?\d+(?:\.\d+)?)\s*(?:wins)?:\s*([+-]?\d+(?:\.\d+)?)\s*→\s*([+-]?\d+(?:\.\d+)?)/i);
  const dateMatch = reason.match(/\bon\s+(\d{4}-\d{2}-\d{2})/i);

  let moveLine = reason || 'No movement detail available';

  if (lineMatch && (overMatch || underMatch)) {
    const fromPrices = [];
    const toPrices = [];

    if (overMatch) {
      fromPrices.push(`O ${dashboardCleanOddsShortV2(overMatch[2])}`);
      toPrices.push(`O ${dashboardCleanOddsShortV2(overMatch[3])}`);
    }

    if (underMatch) {
      fromPrices.push(`U ${dashboardCleanOddsShortV2(underMatch[2])}`);
      toPrices.push(`U ${dashboardCleanOddsShortV2(underMatch[3])}`);
    }

    moveLine = `Line: ${lineMatch[1]} (${fromPrices.join(' / ')}) → ${lineMatch[2]} (${toPrices.join(' / ')})`;
  } else if (overMatch || underMatch) {
    const parts = [];
    if (overMatch) parts.push(`O ${overMatch[1]} ${dashboardCleanOddsShortV2(overMatch[2])} → ${dashboardCleanOddsShortV2(overMatch[3])}`);
    if (underMatch) parts.push(`U ${underMatch[1]} ${dashboardCleanOddsShortV2(underMatch[2])} → ${dashboardCleanOddsShortV2(underMatch[3])}`);
    moveLine = `Prices: ${parts.join(' · ')}`;
  }

  const moved = dateMatch ? `Moved: ${dashboardFormatSimpleDateV2(dateMatch[1])}` : '';

  return `<div class="dashboard-angle">
    <div class="dashboard-angle-top">
      <div>
        <div class="dashboard-angle-title">${dashText(title)}</div>
        <div class="dashboard-angle-meta">${dashText(moveLine)}</div>
        ${moved ? `<div class="dashboard-angle-meta">${dashText(moved)}</div>` : ''}
      </div>
    </div>
  </div>`;
}

function dashboardArbCardCleanV2(r) {
  const team = r.team || '';
  const type = r.type || r.quality || 'Arb / Middle';
  const edge = r.edge_pct != null && r.edge_pct !== '' && String(r.edge_pct).toLowerCase() !== 'nan'
    ? `${Number(r.edge_pct).toFixed(2)}%`
    : '';

  const title = `${team} ${r.win_total ? `Win Total ${r.win_total}` : ''} ${type}${edge ? ` — ${edge}` : ''}`.replace(/\s+/g, ' ').trim();

  const bet1 = `${r.side_1 || 'Side 1'} at ${r.book_1 || ''} ${dashboardCleanOddsShortV2(r.odds_1)}`.trim();
  const bet2 = `${r.side_2 || 'Side 2'} at ${r.book_2 || ''} ${dashboardCleanOddsShortV2(r.odds_2)}`.trim();

  const scoreLine = /middle/i.test(String(type + ' ' + r.quality))
    ? `Middle score: ${r.middle_score ?? '—'}${r.notes ? ` · ${r.notes}` : ''}`
    : `Arb edge: ${edge || '—'}${r.implied_sum_pct ? ` · Implied sum ${Number(r.implied_sum_pct).toFixed(2)}%` : ''}`;

  return `<div class="dashboard-angle">
    <div class="dashboard-angle-top">
      <div>
        <div class="dashboard-angle-title">${dashText(title)}</div>
        <div class="dashboard-angle-meta">${dashText(bet1)}</div>
        <div class="dashboard-angle-meta">${dashText(bet2)}</div>
        <div class="dashboard-angle-meta">${dashText(scoreLine)}</div>
      </div>
    </div>
  </div>`;
}
'''

if "function dashboardMarketMoveCardCleanV2" not in s:
    marker = "function renderHome()"
    if marker not in s:
        raise SystemExit("Could not find renderHome() marker")
    s = s.replace(marker, helpers + "\n" + marker, 1)

# Replace original dashboardList renderers.
s = s.replace(
    "${dashboardList(dash.top_arbs, 'arb', 6)}",
    "${dashboardExpandableListV2(dash.top_arbs || [], r => dashboardArbCardCleanV2(r), 6, 'dashboard-arbs')}"
)
s = s.replace(
    '${dashboardList(dash.top_arbs, "arb", 6)}',
    "${dashboardExpandableListV2(dash.top_arbs || [], r => dashboardArbCardCleanV2(r), 6, 'dashboard-arbs')}"
)
s = s.replace(
    "${dashboardList(dash.top_market_moves, 'move', 6)}",
    "${dashboardExpandableListV2(dash.top_market_moves || [], r => dashboardMarketMoveCardCleanV2(r), 6, 'dashboard-market-moves')}"
)
s = s.replace(
    '${dashboardList(dash.top_market_moves, "move", 6)}',
    "${dashboardExpandableListV2(dash.top_market_moves || [], r => dashboardMarketMoveCardCleanV2(r), 6, 'dashboard-market-moves')}"
)

# Replace earlier clean helper renderers too.
s = s.replace(
    "${(dash.top_arbs || []).slice(0,6).map(r => dashboardArbCardClean(r)).join('')}",
    "${dashboardExpandableListV2(dash.top_arbs || [], r => dashboardArbCardCleanV2(r), 6, 'dashboard-arbs')}"
)
s = s.replace(
    "${(dash.top_market_moves || []).slice(0,6).map(r => dashboardMarketMoveCardClean(r)).join('')}",
    "${dashboardExpandableListV2(dash.top_market_moves || [], r => dashboardMarketMoveCardCleanV2(r), 6, 'dashboard-market-moves')}"
)

p.write_text(s)
print("patched Win Total/Futures Moves and Arbs/Middles display with V2 helpers")
