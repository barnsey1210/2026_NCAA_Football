#!/usr/bin/env python3
from pathlib import Path

INDEX = Path("index.html")

CSS = r'''
/* Injury score chips for Season Schedule */
.injury-chip{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-width:58px;
  padding:3px 7px;
  border-radius:999px;
  font-size:11px;
  font-weight:800;
  border:1px solid var(--border);
  white-space:nowrap;
}
.injury-chip-none{ opacity:.55; }
.injury-chip-low{ background:rgba(234,179,8,.12); border-color:rgba(234,179,8,.35); }
.injury-chip-medium{ background:rgba(249,115,22,.14); border-color:rgba(249,115,22,.45); }
.injury-chip-high{ background:rgba(239,68,68,.16); border-color:rgba(239,68,68,.52); }
.injury-chip-major{ background:rgba(185,28,28,.25); border-color:rgba(239,68,68,.75); }
.injury-cell{
  text-align:center;
}
.injury-cell details{
  display:inline-block;
}
.injury-cell summary{
  list-style:none;
  cursor:pointer;
}
.injury-cell summary::-webkit-details-marker{
  display:none;
}
.injury-detail-pop{
  margin-top:6px;
  max-width:320px;
  text-align:left;
  font-size:12px;
  line-height:1.35;
  white-space:normal;
}
'''

FUNC = r'''
function gameInjuryCell(g) {
  const score = Number(g.game_injury_score || 0);
  const tier = String(g.game_injury_tier || 'None');
  const cls = tier.toLowerCase();
  const edge = Number(g.injury_edge_home || 0);
  const summary = g.injury_summary || '';

  if (!score || tier === 'None') {
    return '<span class="injury-chip injury-chip-none" title="No current injury impact flagged">INJ —</span>';
  }

  const edgeTxt = Number.isFinite(edge) && edge !== 0 ? ` · home edge ${edge > 0 ? '+' : ''}${edge.toFixed(1)}` : '';
  const label = `INJ ${score.toFixed(1)}`;
  const title = `${tier} injury impact${edgeTxt}`;

  return `<div class="injury-cell"><details><summary><span class="injury-chip injury-chip-${cls}" title="${escapeHtml(title)}">${escapeHtml(label)}</span></summary><div class="injury-detail-pop muted">${escapeHtml(summary || title)}</div></details></div>`;
}

'''

def main():
    txt = INDEX.read_text(errors="ignore")

    if "Injury score chips for Season Schedule" not in txt:
        txt = txt.replace("</style>", CSS + "\n</style>", 1)

    if "function gameInjuryCell(g)" not in txt:
        marker = "function scheduleTable(games, mode='simple') {"
        if marker not in txt:
            raise SystemExit("Could not find scheduleTable function")
        txt = txt.replace(marker, FUNC + "\n" + marker, 1)

    start = txt.find("function scheduleTable(games, mode='simple') {")
    end = txt.find("\n\n\nfunction bookLogoBadge", start)
    if start == -1 or end == -1:
        raise SystemExit("Could not isolate scheduleTable function")

    chunk = txt[start:end]

    if "scheduleTh('injury_score','Injuries')" not in chunk:
        chunk = chunk.replace("'<th>Matchup</th>'", "scheduleTh('injury_score','Injuries'), '<th>Matchup</th>'")
        chunk = chunk.replace("<td>${matchupButton(g)}</td>", "<td>${gameInjuryCell(g)}</td><td>${matchupButton(g)}</td>")
        chunk = chunk.replace(
            "const colSpan = view === 'marketlab' ? (scheduleMarketLabMode === 'totals' ? 10 : 9) : view === 'odds' ? 13 : view === 'results' ? 11 : 11;",
            "const colSpan = view === 'marketlab' ? (scheduleMarketLabMode === 'totals' ? 11 : 10) : view === 'odds' ? 14 : view === 'results' ? 12 : 12;"
        )

    txt = txt[:start] + chunk + txt[end:]

    INDEX.write_text(txt)
    print("patched schedule injury UI in", INDEX)

if __name__ == "__main__":
    main()
