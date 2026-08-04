#!/usr/bin/env python3
from pathlib import Path
import re

p = Path("index.html")
if not p.exists():
    raise SystemExit("index.html not found; run from ~/NCAAF_AUTO")

s = p.read_text(errors="ignore")

helpers = r'''
function dashboardPick(row, keys) {
  for (const k of keys) {
    if (row && row[k] != null && row[k] !== '' && String(row[k]).toLowerCase() !== 'nan') return row[k];
  }
  return '';
}

function dashboardFormatEasternDate(v) {
  if (v == null || v === '' || String(v).toLowerCase() === 'nan') return '';
  const raw = String(v).trim();
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw;

  const fmt = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short'
  });

  return fmt.format(d).replace(',', '').replace(',', '').replace(/\s+/g, ' ').trim();
}

function dashboardAmericanToProb(odds) {
  if (odds == null || odds === '') return null;
  const n = Number(String(odds).replace('+',''));
  if (!Number.isFinite(n) || n === 0 || Math.abs(n) > 500) return null;
  return n < 0 ? Math.abs(n) / (Math.abs(n) + 100) : 100 / (n + 100);
}

function dashboardFmtProb(p) {
  return p == null || !Number.isFinite(Number(p)) ? '' : `${(Number(p) * 100).toFixed(1)}%`;
}

function dashboardCleanOdds(v) {
  if (v == null || v === '' || String(v).toLowerCase() === 'nan') return '';
  const n = Number(String(v).replace('+',''));
  if (!Number.isFinite(n)) return String(v);
  return n > 0 ? `+${Math.round(n)}` : `${Math.round(n)}`;
}

function dashboardMarketBase(row) {
  const m = String(row.market || '').toLowerCase();
  if (m.includes('total')) return 'Total';
  if (m.includes('spread')) return 'Spread';
  return String(row.market || 'Game Line').replace(/\s+/g, ' ').trim();
}

function dashboardIsPriceMove(row) {
  return /price/i.test(String(row.market || ''));
}

function dashboardCleanMarketName(row) {
  const market = String(row.market || 'Game Line').replace(/_/g, ' ').replace(/\s+/g, ' ').trim();

  // Collapse Total Over Price / Total Under Price to Total if it survives filtering.
  if (/total/i.test(market) && /price/i.test(market)) {
    if (/over/i.test(market)) return 'Total Over';
    if (/under/i.test(market)) return 'Total Under';
    return 'Total';
  }

  return market;
}

function dashboardMoveDateText(row) {
  const prevRaw = dashboardPick(row, [
    'snapshot_prev','previous_snapshot','prev_snapshot','snapshot_prev_at',
    'previous_time','prev_time','prev_pulled_at','previous_pulled_at',
    'from_date','from_time','from_snapshot'
  ]);

  const latestRaw = dashboardPick(row, [
    'snapshot_latest','latest_snapshot','current_snapshot','snapshot_latest_at',
    'latest_time','current_time','latest_pulled_at','current_pulled_at',
    'to_date','to_time','to_snapshot'
  ]);

  const prevDate = dashboardFormatEasternDate(prevRaw);
  const latestDate = dashboardFormatEasternDate(latestRaw);

  if (prevDate || latestDate) {
    return `Moved between ${prevDate || 'previous pull'} and ${latestDate || 'latest pull'}`;
  }

  return '';
}

function dashboardFromToText(row) {
  const prev = row.previous;
  const latest = row.latest;

  if (prev == null || latest == null) return '';

  if (dashboardIsPriceMove(row)) {
    return `From ${dashboardCleanOdds(prev)} to ${dashboardCleanOdds(latest)}`;
  }

  const p = Number(prev);
  const l = Number(latest);
  const from = Number.isFinite(p) ? String(p).replace(/\.0$/, '') : String(prev);
  const to = Number.isFinite(l) ? String(l).replace(/\.0$/, '') : String(latest);
  return `From ${from} to ${to}`;
}

function dashboardMoveProbText(row) {
  if (!dashboardIsPriceMove(row)) return '';
  const p0 = dashboardAmericanToProb(row.previous);
  const p1 = dashboardAmericanToProb(row.latest);
  if (p0 == null || p1 == null) return '';
  const pp = (p1 - p0) * 100;
  return `Implied probability ${dashboardFmtProb(p0)} → ${dashboardFmtProb(p1)} (${pp >= 0 ? '+' : ''}${pp.toFixed(1)} pp)`;
}

function dashboardBookLogo(book) {
  const b = String(book || '').toLowerCase();
  let txt = book || '';
  if (b.includes('caesars')) txt = 'CZR';
  else if (b.includes('draft')) txt = 'DK';
  else if (b.includes('fanduel') || b.includes('fan duel')) txt = 'FD';
  else if (b.includes('mgm')) txt = 'MGM';
  return txt ? `<span class="dashboard-book-logo">${dashText(txt)}</span>` : '';
}

function dashboardMoveCoreKey(row) {
  const away = row.away_team || row.away || '';
  const home = row.home_team || row.home || '';
  const book = row.book || row.sportsbook || row.book_name || '';
  const base = dashboardMarketBase(row);
  return `${away}|${home}|${book}|${base}`.toLowerCase();
}

function dashboardDedupeGameMoves(arr) {
  const rows = arr || [];

  // Attach Total Over/Under Price rows to the true Total line row instead of showing duplicates.
  const priceMap = new Map();
  rows.forEach(r => {
    const market = String(r.market || '').toLowerCase();
    if (market.includes('price')) {
      const key = dashboardMoveCoreKey(r);
      if (!priceMap.has(key)) priceMap.set(key, []);
      priceMap.get(key).push(r);
    }
  });

  const out = [];
  const seen = new Set();

  for (const row of rows) {
    const key = dashboardMoveCoreKey(row);
    const market = String(row.market || '').toLowerCase();

    // Skip standalone price rows if a true line row for same game/book/market exists.
    if (market.includes('price')) {
      const hasTrueLine = rows.some(r => dashboardMoveCoreKey(r) === key && !String(r.market || '').toLowerCase().includes('price'));
      if (hasTrueLine) continue;
    }

    if (seen.has(key)) continue;
    seen.add(key);

    const related = priceMap.get(key) || [];
    if (related.length) row._relatedPriceMoves = related;

    out.push(row);
  }

  return out;
}
'''

# Remove older versions of these helper functions from index.html.
for fn in [
    "dashboardPick",
    "dashboardFormatEasternDate",
    "dashboardAmericanToProb",
    "dashboardFmtProb",
    "dashboardCleanOdds",
    "dashboardMarketBase",
    "dashboardIsPriceMove",
    "dashboardCleanMarketName",
    "dashboardMoveDateText",
    "dashboardFromToText",
    "dashboardMoveProbText",
    "dashboardBookLogo",
    "dashboardMoveCoreKey",
    "dashboardDedupeGameMoves",
]:
    s = re.sub(rf"\n?function {fn}\([^)]*\) \{{.*?\n\}}", "", s, flags=re.S)

# Insert helpers before card function.
marker = "function dashboardGameMoveCard(row) {"
if marker not in s:
    raise SystemExit("Could not find dashboardGameMoveCard")
s = s.replace(marker, helpers + "\n" + marker, 1)

# Replace card renderer.
pattern = r"function dashboardGameMoveCard\(row\) \{.*?\n\}"
replacement = r'''function dashboardGameMoveCard(row) {
  if (!row) return '';

  const away = row.away_team || row.away || '';
  const home = row.home_team || row.home || '';
  const game = `${away} at ${home}`.trim() || row.game || row.matchup || 'Game line move';
  const book = row.book || row.sportsbook || row.book_name || '';
  const market = dashboardCleanMarketName(row);

  const title = `${game}${book ? ` — ${book}` : ''}${market ? ` ${market}` : ''}`;

  const related = row._relatedPriceMoves || [];
  const overMove = related.find(pm => /over/i.test(String(pm.market || '')));
  const underMove = related.find(pm => /under/i.test(String(pm.market || '')));

  function compactNum(v) {
    const n = Number(v);
    return Number.isFinite(n) ? String(n).replace(/\.0$/, '') : String(v || '');
  }

  function priceStackFrom(moveSide, which) {
    if (!moveSide) return '';
    const v = which === 'from' ? moveSide.previous : moveSide.latest;
    return dashboardCleanOdds(v);
  }

  const fromLine = compactNum(row.previous);
  const toLine = compactNum(row.latest);

  const fromOver = priceStackFrom(overMove, 'from');
  const fromUnder = priceStackFrom(underMove, 'from');
  const toOver = priceStackFrom(overMove, 'to');
  const toUnder = priceStackFrom(underMove, 'to');

  let moveLine = '';

  if (!dashboardIsPriceMove(row)) {
    const fromPrices = [fromOver ? `O ${fromOver}` : '', fromUnder ? `U ${fromUnder}` : ''].filter(Boolean).join(' / ');
    const toPrices = [toOver ? `O ${toOver}` : '', toUnder ? `U ${toUnder}` : ''].filter(Boolean).join(' / ');

    moveLine = `Line: ${fromLine}${fromPrices ? ` (${fromPrices})` : ''} → ${toLine}${toPrices ? ` (${toPrices})` : ''}`;
  } else {
    const priceOnlyFrom = [
      fromOver ? `O ${fromOver}` : '',
      fromUnder ? `U ${fromUnder}` : ''
    ].filter(Boolean).join(' / ');

    const priceOnlyTo = [
      toOver ? `O ${toOver}` : '',
      toUnder ? `U ${toUnder}` : ''
    ].filter(Boolean).join(' / ');

    moveLine = priceOnlyFrom || priceOnlyTo
      ? `Prices: ${priceOnlyFrom || dashboardCleanOdds(row.previous)} → ${priceOnlyTo || dashboardCleanOdds(row.latest)}`
      : dashboardFromToText(row);
  }

  const details = [
    moveLine,
    dashboardMoveDateText(row)
  ].filter(Boolean).map(x => `<div class="dashboard-angle-meta">${dashText(x)}</div>`).join('');

  return `<div class="dashboard-angle">
    <div class="dashboard-angle-top">
      <div>
        <div class="dashboard-angle-title">${dashboardBookLogo(book)}${dashText(title)}</div>
        ${details || `<div class="dashboard-angle-meta">${dashText(row.summary || row.reason || '')}</div>`}
      </div>
    </div>
  </div>`;
}'''
s, n = re.subn(pattern, replacement, s, count=1, flags=re.S)
if n == 0:
    raise SystemExit("Failed to replace dashboardGameMoveCard")

# Force render list to dedupe.
s = s.replace(
    "return `<div class=\"dashboard-angle-list\">${arr.map(r => dashboardGameMoveCard(r)).join('')}</div>`;",
    "const cleanArr = dashboardDedupeGameMoves(arr); return `<div class=\"dashboard-angle-list\">${cleanArr.map(r => dashboardGameMoveCard(r)).join('')}</div>`;"
)

# Add logo CSS if missing.
css = '''
.dashboard-book-logo{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-width:42px;
  height:28px;
  padding:0 9px;
  margin-right:10px;
  border-radius:999px;
  background:#eef3ff;
  color:#1f3a8a;
  font-size:13px;
  font-weight:900;
  letter-spacing:.03em;
  vertical-align:middle;
}
'''
if ".dashboard-book-logo" not in s:
    pos = s.find("</style>")
    if pos != -1:
        s = s[:pos] + css + s[pos:]

p.write_text(s)
print("patched game line moves: Eastern dates, no duplicate total price rows, cleaner line/price display")
