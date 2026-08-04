#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import json
import re

INDEX = Path("index.html")
CSV = Path("data/coach/game_coach_fav_dog_context.csv")

if not INDEX.exists():
    raise SystemExit("Missing index.html")
if not CSV.exists():
    raise SystemExit("Missing data/coach/game_coach_fav_dog_context.csv")

df = pd.read_csv(CSV, low_memory=False)

needed = [
    "game_id","date","team","opponent","projected_team_role",
    "period","fav_dog","is_applicable","coach","historical_teams",
    "games","ats_record","ats_win_pct","avg_ats_margin",
    "ou_record","over_pct","avg_total_margin"
]
missing = [c for c in needed if c not in df.columns]
if missing:
    raise SystemExit(f"Missing columns in coach fav/dog context: {missing}")

is_app = df["is_applicable"].astype(str).str.lower().eq("true")
is_no_sample = df["ats_record"].astype(str).eq("No 2024-25 HC fav/dog sample")
small = df.loc[is_app | is_no_sample, needed].copy()
small = small.where(pd.notnull(small), "")

records = small.to_dict(orient="records")

s = INDEX.read_text(errors="ignore")

def replace_marker_block(text, start_marker, end_marker, block):
    pat = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
    if pat.search(text):
        return pat.sub(lambda m: block, text)
    return text

data_start = "/* COACH_FAV_DOG_CONTEXT_DATA_START */"
data_end = "/* COACH_FAV_DOG_CONTEXT_DATA_END */"
helper_start = "/* COACH_FAV_DOG_CONTEXT_HELPERS_START */"
helper_end = "/* COACH_FAV_DOG_CONTEXT_HELPERS_END */"
style_start = "/* COACH_FAV_DOG_CONTEXT_STYLE_START */"
style_end = "/* COACH_FAV_DOG_CONTEXT_STYLE_END */"

data_block = (
    data_start + "\n"
    "window.COACH_FAV_DOG_CONTEXT = "
    + json.dumps(records, separators=(",", ":"))
    + ";\n"
    + data_end
    + "\n"
)

helper_block = r'''/* COACH_FAV_DOG_CONTEXT_HELPERS_START */
function matchupCoachFavDogNorm(x) {
  return String(x || '').trim().toLowerCase().replace(/\./g, '').replace(/\s+/g, ' ');
}

function matchupCoachFavDogSigned(x, digits = 1) {
  const n = Number(x);
  if (!Number.isFinite(n)) return '—';
  return `${n >= 0 ? '+' : ''}${n.toFixed(digits)}`;
}

function matchupCoachFavDogPeriodLabel(p) {
  p = String(p || '');
  if (p === 'Full Game') return 'FG';
  return p || '—';
}

function matchupCoachFavDogRows(g, team) {
  const data = window.COACH_FAV_DOG_CONTEXT || [];
  const gid = String(g && g.game_id || '');
  const t = matchupCoachFavDogNorm(team);

  return data.filter(r => {
    const sameGame = gid && String(r.game_id || '') === gid;
    const sameTeam = matchupCoachFavDogNorm(r.team) === t;
    return sameGame && sameTeam;
  });
}

function matchupCoachFavDogTableRow(g, team) {
  const rows = matchupCoachFavDogRows(g, team);
  if (!rows.length) return '';

  const noSample = rows.find(r => String(r.ats_record || '') === 'No 2024-25 HC fav/dog sample');
  if (noSample) {
    return `<tr class="coach-favdog-detail-row">
      <td></td>
      <td colspan="5">
        <div class="coach-favdog-box coach-favdog-muted">
          <b>Fav/Dog split:</b> No 2024–25 HC fav/dog sample
        </div>
      </td>
    </tr>`;
  }

  const order = {'Full Game': 1, '1H': 2, '2H': 3};
  const sorted = rows.slice().sort((a,b) => (order[a.period] || 99) - (order[b.period] || 99));

  const hist = sorted[0] && sorted[0].historical_teams ? sorted[0].historical_teams : '';
  const role = sorted[0] && sorted[0].projected_team_role ? sorted[0].projected_team_role : '';

  const lines = sorted.map(r => {
    const p = matchupCoachFavDogPeriodLabel(r.period);
    const side = r.fav_dog || role || '';
    const atsMargin = matchupCoachFavDogSigned(r.avg_ats_margin, 1);
    const totalMargin = matchupCoachFavDogSigned(r.avg_total_margin, 1);
    const games = r.games ? ` <span class="coach-favdog-games">(${Number(r.games).toFixed(0)}g)</span>` : '';
    return `<div class="coach-favdog-line">
      <span class="coach-favdog-star">★</span>
      <b>${escapeHtml(p)} ${escapeHtml(side)}:</b>
      ${escapeHtml(r.ats_record || '—')} ATS, ${atsMargin} margin${games}
      <span class="coach-favdog-sep">·</span>
      ${escapeHtml(r.ou_record || '—')}, ${totalMargin} total margin
    </div>`;
  }).join('');

  const meta = [
    role ? `Projected role: <b>${escapeHtml(role)}</b>` : '',
    hist ? `Historical teams: ${escapeHtml(hist)}` : ''
  ].filter(Boolean).join(' · ');

  return `<tr class="coach-favdog-detail-row">
    <td></td>
    <td colspan="5">
      <div class="coach-favdog-box">
        <div class="coach-favdog-title">Fav/Dog split</div>
        <div class="coach-favdog-meta">${meta}</div><div class="coach-favdog-source-note">FG: CFBD full-game sample · 1H/2H: SGO 2024–25 sample</div>
        ${lines}
      </div>
    </td>
  </tr>`;
}
/* COACH_FAV_DOG_CONTEXT_HELPERS_END */
'''

style_block = r'''/* COACH_FAV_DOG_CONTEXT_STYLE_START */
.coach-favdog-detail-row td {
  border-top: 0 !important;
  padding-top: 0 !important;
}
.coach-favdog-box {
  margin: 2px 0 10px;
  padding: 9px 10px;
  border: 1px solid rgba(148,163,184,.22);
  border-radius: 12px;
  background: rgba(15,23,42,.48);
  font-size: 12px;
  line-height: 1.35;
}
.coach-favdog-title {
  font-weight: 800;
  letter-spacing: .04em;
  text-transform: uppercase;
  color: #dbeafe;
  margin-bottom: 2px;
}
.coach-favdog-meta {
  color: #9ca3af;
  margin-bottom: 5px;
}
.coach-favdog-line {
  color: #d1d5db;
  margin: 2px 0;
}
.coach-favdog-star {
  color: #fbbf24;
  font-weight: 900;
  margin-right: 4px;
}
.coach-favdog-sep {
  color: #64748b;
  margin: 0 5px;
}
.coach-favdog-games {
  color: #94a3b8;
}
.coach-favdog-muted {
  color: #9ca3af;
}
/* COACH_FAV_DOG_CONTEXT_STYLE_END */
'''

s = replace_marker_block(s, data_start, data_end, data_block)
s = replace_marker_block(s, helper_start, helper_end, helper_block)
s = replace_marker_block(s, style_start, style_end, style_block)

if data_start not in s:
    marker = "/* MATCHUP_COACH_GRADE_CARD_END */"
    if marker not in s:
        raise SystemExit("Could not find MATCHUP_COACH_GRADE_CARD_END marker")
    s = s.replace(marker, data_block + "\n" + helper_block + "\n" + marker, 1)

if style_start not in s:
    idx = s.find("</style>")
    if idx == -1:
        head_idx = s.find("</head>")
        if head_idx == -1:
            raise SystemExit("Could not find </style> or </head> for style injection")
        s = s[:head_idx] + "<style>\n" + style_block + "\n</style>\n" + s[head_idx:]
    else:
        s = s[:idx] + style_block + "\n" + s[idx:]

old_row = """  function row(team) {
    return `<tr>
      <td>${linkTeam(team)}</td>
      <td>${matchupCoachGradeCell('FG', matchupCoachAtsGrade(team, 'fg'))}</td>
      <td>${matchupCoachGradeCell('1H', matchupCoachAtsGrade(team, '1h'))}</td>
      <td>${matchupCoachGradeCell('2H', matchupCoachAtsGrade(team, '2h'))}</td>
      <td>${matchupCoachOuCell(team, '1h')}</td>
      <td>${matchupCoachOuCell(team, '2h')}</td>
    </tr>`;
  }"""

new_row = """  function row(team) {
    return `<tr>
      <td>${linkTeam(team)}</td>
      <td>${matchupCoachGradeCell('FG', matchupCoachAtsGrade(team, 'fg'))}</td>
      <td>${matchupCoachGradeCell('1H', matchupCoachAtsGrade(team, '1h'))}</td>
      <td>${matchupCoachGradeCell('2H', matchupCoachAtsGrade(team, '2h'))}</td>
      <td>${matchupCoachOuCell(team, '1h')}</td>
      <td>${matchupCoachOuCell(team, '2h')}</td>
    </tr>${matchupCoachFavDogTableRow(g, team)}`;
  }"""

if old_row in s:
    s = s.replace(old_row, new_row, 1)
elif "matchupCoachFavDogTableRow(g, team)" in s:
    print("row already patched")
else:
    raise SystemExit("Could not find exact coach grade row block to patch")

INDEX.write_text(s)

print("embedded coach fav/dog context rows:", len(records))
print("patched:", INDEX)
