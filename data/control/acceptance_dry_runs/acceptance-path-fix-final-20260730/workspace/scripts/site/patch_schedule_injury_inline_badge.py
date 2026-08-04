#!/usr/bin/env python3
from pathlib import Path

INDEX = Path("index.html")

CSS = r'''
/* Inline injury badge inside existing schedule cells */
.injury-inline-chip{
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
.injury-inline-low{ background:rgba(234,179,8,.12); border-color:rgba(234,179,8,.35); }
.injury-inline-medium{ background:rgba(249,115,22,.14); border-color:rgba(249,115,22,.45); }
.injury-inline-high{ background:rgba(239,68,68,.16); border-color:rgba(239,68,68,.52); }
.injury-inline-major{ background:rgba(185,28,28,.25); border-color:rgba(239,68,68,.75); }
'''

FUNC = r'''
function gameInjuryInlineBadge(g) {
  const score = Number(g.game_injury_score || 0);
  const tier = String(g.game_injury_tier || 'None');
  if (!score || tier === 'None') return '';

  const cls = tier.toLowerCase();
  const edge = Number(g.injury_edge_home || 0);
  const edgeTxt = Number.isFinite(edge) && edge !== 0 ? ` · home injury edge ${edge > 0 ? '+' : ''}${edge.toFixed(1)}` : '';
  const summary = g.injury_summary || `${tier} injury impact ${score.toFixed(1)}${edgeTxt}`;
  const label = `INJ ${score.toFixed(1)}`;

  return `<span class="injury-inline-chip injury-inline-${cls}" title="${escapeHtml(summary)}">${escapeHtml(label)}</span>`;
}

'''

def main():
    txt = INDEX.read_text(errors="ignore")

    if "Inline injury badge inside existing schedule cells" not in txt:
        txt = txt.replace("</style>", CSS + "\n</style>", 1)

    if "function gameInjuryInlineBadge(g)" not in txt:
        marker = "function scheduleTable(games, mode='simple') {"
        if marker not in txt:
            raise SystemExit("Could not find scheduleTable function")
        txt = txt.replace(marker, FUNC + "\n" + marker, 1)

    start = txt.find("function scheduleTable(games, mode='simple') {")
    end = txt.find("\n\n\nfunction bookLogoBadge", start)
    if start == -1 or end == -1:
        raise SystemExit("Could not isolate scheduleTable function")

    chunk = txt[start:end]

    replacements = {
        "<td>${fmtMarketSpreadCell(g)}</td><td>${fmtEdge(spreadEdge)}</td>":
        "<td>${fmtMarketSpreadCell(g)}${gameInjuryInlineBadge(g)}</td><td>${fmtEdge(spreadEdge)}</td>",

        "<td>${fmtMarketSpreadCompactCell(g)}</td><td>${ats.side}</td>":
        "<td>${fmtMarketSpreadCompactCell(g)}${gameInjuryInlineBadge(g)}</td><td>${ats.side}</td>",

        "<td>${fmtMarketTotalTwoSideCell(g)}</td><td>${tot.side}</td>":
        "<td>${fmtMarketTotalTwoSideCell(g)}${gameInjuryInlineBadge(g)}</td><td>${tot.side}</td>",

        "<td>${scheduleSpreadCell(g)}</td>\n      <td>${Number(g.projected_total).toFixed(1)}</td>":
        "<td>${scheduleSpreadCell(g)}${gameInjuryInlineBadge(g)}</td>\n      <td>${Number(g.projected_total).toFixed(1)}</td>",
    }

    applied = 0
    for old, new in replacements.items():
        if old in chunk and new not in chunk:
            chunk = chunk.replace(old, new)
            applied += 1

    txt = txt[:start] + chunk + txt[end:]

    INDEX.write_text(txt)

    print("patched inline injury badge UI")
    print("replacements applied:", applied)
    print("badge function exists:", "function gameInjuryInlineBadge(g)" in txt)
    print("old table-column injury function exists:", "function gameInjuryCell(g)" in txt)
    print("old injury header exists:", "scheduleTh('injury_score','Injuries')" in txt)

if __name__ == "__main__":
    main()
