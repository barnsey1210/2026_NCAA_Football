#!/usr/bin/env python3
from pathlib import Path
import json
import re
import pandas as pd

ROOT = Path(".")
SRC = ROOT / "data/research/returning_production_2026_broad_trend_games.csv"

TARGETS = [
    ROOT / "index.html",
    ROOT / "matchup.html",
]

DATA_START = "RP_SUPPORT_BADGES_DATA_START"
DATA_END = "RP_SUPPORT_BADGES_DATA_END"
STYLE_START = "RP_SUPPORT_BADGES_STYLE_START"
STYLE_END = "RP_SUPPORT_BADGES_STYLE_END"
HELPER_START = "RP_SUPPORT_BADGES_HELPER_START"
HELPER_END = "RP_SUPPORT_BADGES_HELPER_END"

if not SRC.exists():
    raise SystemExit(f"Missing {SRC}. Re-run the one-off broad trend query first.")

df = pd.read_csv(SRC, low_memory=False)

# Conservative display rule: only the cleaner 48-ish set.
df = df[
    (pd.to_numeric(df["projected_spread"], errors="coerce").abs() <= 21) &
    (pd.to_numeric(df["off_vs_def_gap"], errors="coerce") >= 10)
].copy()

df["projected_spread"] = pd.to_numeric(df["projected_spread"], errors="coerce").round(1)
df["off_vs_def_gap"] = pd.to_numeric(df["off_vs_def_gap"], errors="coerce").round(0)
df["team_off_rp"] = pd.to_numeric(df["team_off_rp"], errors="coerce").round(0)
df["opp_def_rp"] = pd.to_numeric(df["opp_def_rp"], errors="coerce").round(0)

keep = [
    "date",
    "away_team",
    "home_team",
    "team",
    "opponent",
    "projected_spread",
    "team_off_rp",
    "opp_def_rp",
    "off_vs_def_gap",
]
rows = df[keep].sort_values(["date", "off_vs_def_gap"], ascending=[True, False]).to_dict("records")

DATA_JS = f"""
// {DATA_START}
window.RP_SUPPORT_BADGES = {json.dumps(rows, ensure_ascii=False)};
// {DATA_END}
"""

STYLE = f"""
/* {STYLE_START} */
.rp-support-badge {{
  display:inline-flex;
  align-items:center;
  gap:4px;
  margin-left:6px;
  padding:3px 7px;
  border-radius:999px;
  border:1px solid rgba(74,222,128,.55);
  background:rgba(74,222,128,.12);
  color:#b9f8cf;
  font-size:11px;
  font-weight:800;
  letter-spacing:.02em;
  white-space:nowrap;
  vertical-align:middle;
}}
.rp-support-badge .rp-gap {{
  color:#ffffff;
}}
.rp-support-note {{
  color:var(--muted);
  font-size:11px;
  margin-top:4px;
}}
@media (max-width:700px){{
  .rp-support-badge {{
    margin-left:0;
    margin-top:4px;
    display:inline-flex;
    width:max-content;
  }}
}}
/* {STYLE_END} */
"""

HELPER = f"""
// {HELPER_START}
function normRpSupportName(name) {{
  return String(name || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
}}

function rpSupportBadge(g, teamName) {{
  const rows = window.RP_SUPPORT_BADGES || [];
  const gid = g && g.game_id ? String(g.game_id) : '';
  const date = g && g.date ? String(g.date) : '';
  const away = g && g.away_team ? String(g.away_team) : '';
  const home = g && g.home_team ? String(g.home_team) : '';
  const teamKey = normRpSupportName(teamName);

  const r = rows.find(x => {{
    const sameGame =
      (gid && x.game_id && String(x.game_id) === gid) ||
      (String(x.date) === date &&
       normRpSupportName(x.away_team) === normRpSupportName(away) &&
       normRpSupportName(x.home_team) === normRpSupportName(home));

    return sameGame && normRpSupportName(x.team) === teamKey;
  }});

  if (!r) return '';

  const gap = Number(r.off_vs_def_gap);
  const title = `Returning Production Support: ${{r.team}} offense RP ${{r.team_off_rp}}% vs ${{r.opponent}} defense RP ${{r.opp_def_rp}}% = +${{gap.toFixed(0)}}. Historical broad bucket: offense RP gap >=10 favorites went 103-79-1 ATS, 56.6%, +1.32 ATS margin over 183 games. Support only, not standalone bet.`;

  return `<span class="rp-support-badge" title="${{escapeHtml(title)}}">RP <span class="rp-gap">+${{gap.toFixed(0)}}</span></span>`;
}}
// {HELPER_END}
"""

def replace_block(text, start, end, block):
    pat = re.compile(rf"\n?// {re.escape(start)}[\s\S]*?// {re.escape(end)}\n?", re.M)
    if pat.search(text):
        return pat.sub("\n" + block.strip() + "\n", text)
    return None

def replace_style_block(text):
    pat = re.compile(rf"\n?/\* {re.escape(STYLE_START)} \*/[\s\S]*?/\* {re.escape(STYLE_END)} \*/\n?", re.M)
    if pat.search(text):
        return pat.sub("\n" + STYLE.strip() + "\n", text)
    if "</style>" not in text:
        raise SystemExit("Could not find </style>")
    return text.replace("</style>", STYLE + "\n</style>", 1)

def inject_js_data(text):
    updated = replace_block(text, DATA_START, DATA_END, DATA_JS)
    if updated is not None:
        return updated

    # Put data before the first non-JSON script closes if possible; otherwise before helper/main JS.
    marker = "<script>"
    if marker in text:
        return text.replace(marker, DATA_JS + "\n" + marker, 1)

    raise SystemExit("Could not find <script> for RP data injection")

def inject_helper(text):
    updated = replace_block(text, HELPER_START, HELPER_END, HELPER)
    if updated is not None:
        return updated

    # Prefer inserting after escapeHtml so title escaping exists.
    m = re.search(r"function escapeHtml\([^)]*\)\s*\{[\s\S]*?\n\}", text)
    if m:
        return text[:m.end()] + "\n\n" + HELPER + text[m.end():]

    # Fallback before first render function.
    marker = "function renderHome("
    if marker in text:
        return text.replace(marker, HELPER + "\n" + marker, 1)

    raise SystemExit("Could not find insertion point for RP helper")

def patch_team_cells(text):
    replacements = [
        ("${linkTeam(g.away_team)}", "${linkTeam(g.away_team)}${rpSupportBadge(g, g.away_team)}"),
        ("${linkTeam(g.home_team)}", "${linkTeam(g.home_team)}${rpSupportBadge(g, g.home_team)}"),
        ("${linkTeamWithRank(g.away_team)}", "${linkTeamWithRank(g.away_team)}${rpSupportBadge(g, g.away_team)}"),
        ("${linkTeamWithRank(g.home_team)}", "${linkTeamWithRank(g.home_team)}${rpSupportBadge(g, g.home_team)}"),
        ("${linkTeamWithComboRank(g.away_team)}", "${linkTeamWithComboRank(g.away_team)}${rpSupportBadge(g, g.away_team)}"),
        ("${linkTeamWithComboRank(g.home_team)}", "${linkTeamWithComboRank(g.home_team)}${rpSupportBadge(g, g.home_team)}"),
        ("${teamLogo(g.away_team)} ${linkTeam(g.away_team)}", "${teamLogo(g.away_team)} ${linkTeam(g.away_team)}${rpSupportBadge(g, g.away_team)}"),
        ("${teamLogo(g.home_team)} ${linkTeam(g.home_team)}", "${teamLogo(g.home_team)} ${linkTeam(g.home_team)}${rpSupportBadge(g, g.home_team)}"),
    ]

    changed = 0
    for old, new in replacements:
        if old in text and new not in text:
            text = text.replace(old, new)
            changed += 1

    return text, changed

def main():
    print("RP badge rows:", len(rows))
    Path("data/site/rp_support_badges.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("wrote: data/site/rp_support_badges.json")

    for p in TARGETS:
        if not p.exists():
            print("skip missing:", p)
            continue

        s = p.read_text(errors="ignore")
        before = s

        s = replace_style_block(s)
        s = inject_js_data(s)
        s = inject_helper(s)
        s, changed = patch_team_cells(s)

        p.write_text(s)

        print("patched:", p)
        print("  render replacements:", changed)
        print("  data marker:", DATA_START in s)
        print("  helper marker:", HELPER_START in s)
        print("  style marker:", STYLE_START in s)
        print("  file changed:", s != before)

if __name__ == "__main__":
    main()
