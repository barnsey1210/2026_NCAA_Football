#!/usr/bin/env python3
"""
Patch index.html dashboard game-line move display so American odds/price changes are
shown as implied-probability changes instead of raw odds subtraction.

Run from ~/NCAAF_AUTO after home dashboard data is injected:
    python3 scripts/site/patch_game_line_move_implied_probability_display.py
"""
from pathlib import Path
import re

INDEX = Path("index.html")
if not INDEX.exists():
    raise SystemExit("ERROR: index.html not found; run from ~/NCAAF_AUTO")

s = INDEX.read_text(errors="ignore")

helpers = r'''
function dashboardAmericanToProb(odds) {
  if (odds == null || odds === '') return null;
  const n = Number(String(odds).replace('+',''));
  if (!Number.isFinite(n) || n === 0) return null;
  return n < 0 ? Math.abs(n) / (Math.abs(n) + 100) : 100 / (n + 100);
}
function dashboardFmtProb(p) {
  return p == null || !Number.isFinite(Number(p)) ? '' : `${(Number(p)*100).toFixed(1)}%`;
}
function dashboardPriceMoveMeta(row) {
  const field = String(row.field || row.market || row.title || '');
  const isPrice = /price|odds/i.test(field);
  if (!isPrice) return null;
  const p0 = dashboardAmericanToProb(row.previous);
  const p1 = dashboardAmericanToProb(row.latest);
  if (p0 == null || p1 == null) return null;
  const pp = (p1 - p0) * 100;
  return { pp, text: `Implied probability ${dashboardFmtProb(p0)} → ${dashboardFmtProb(p1)} (${pp >= 0 ? '+' : ''}${pp.toFixed(1)} pp)` };
}
function dashboardMoveScoreText(row) {
  const meta = dashboardPriceMoveMeta(row);
  if (meta) return `${meta.pp >= 0 ? '+' : ''}${meta.pp.toFixed(1)} pp`;
  if (row.implied_prob_change_pct != null && row.implied_prob_change_pct !== '') {
    const n = Number(row.implied_prob_change_pct);
    if (Number.isFinite(n)) return `${n >= 0 ? '+' : ''}${n.toFixed(1)} pp`;
  }
  if (row.change != null && row.change !== '') return String(row.change);
  return '';
}
'''

if 'function dashboardAmericanToProb' not in s:
    marker = 'function dashboardGameMoveCard(row) {'
    if marker not in s:
        raise SystemExit('ERROR: dashboardGameMoveCard not found')
    s = s.replace(marker, helpers + '\n' + marker, 1)

pattern = r"function dashboardGameMoveCard\(row\) \{.*?\n\}"
replacement = r'''function dashboardGameMoveCard(row) {
  if (!row) return '';
  const game = `${row.away_team || ''} at ${row.home_team || ''}`.trim();
  const title = dashboardBestMoveTitle(row) || (game ? `${game} — ${row.market || 'Game line'}` : (row.summary || 'Game line move'));
  const book = row.book || '';
  const prev = row.previous;
  const latest = row.latest;
  const summary = row.summary || '';
  const priceMeta = dashboardPriceMoveMeta(row);
  const moveMeta = priceMeta ? priceMeta.text : `${dashText(book)} moved ${dashText(prev)} → ${dashText(latest)}`;
  const scoreText = dashboardMoveScoreText(row);
  return `<div class="dashboard-angle">
    <div class="dashboard-angle-top">
      <div>
        <div class="dashboard-angle-title">${dashText(title)}</div>
        <div class="dashboard-angle-meta">${dashText(book)} ${dashText(moveMeta)}</div>
      </div>
      ${scoreText ? `<div class="dashboard-angle-score">${dashText(scoreText)}</div>` : ''}
    </div>
    ${summary ? `<div class="dashboard-pill-row"><span class="dashboard-pill">${dashText(summary)}</span></div>` : ''}
  </div>`;
}'''

s2, n = re.subn(pattern, replacement, s, count=1, flags=re.S)
if n == 0:
    raise SystemExit('ERROR: failed to replace dashboardGameMoveCard')
INDEX.write_text(s2)
print('patched game-line move display to use implied probability')
