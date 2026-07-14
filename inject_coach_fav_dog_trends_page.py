#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import json
import re
import math

HTML = Path("index.html")
CSV = Path("data/coach/coach_fav_dog_splits_hybrid.csv")

if not HTML.exists():
    raise SystemExit("Missing index.html")
if not CSV.exists():
    raise SystemExit("Missing data/coach/coach_fav_dog_splits_hybrid.csv")

df = pd.read_csv(CSV, low_memory=False)
df = df[df["fav_dog"].astype(str).isin(["Favorite", "Underdog"])].copy()

period_map = {
    "Full Game": "game",
    "1H": "1h",
    "2H": "2h",
}

def clean_num(x):
    try:
        if pd.isna(x):
            return None
        n = float(x)
        if not math.isfinite(n):
            return None
        return n
    except Exception:
        return None

def season_min_max(s):
    txt = str(s or "")
    yrs = [int(x) for x in re.findall(r"\b(20\d{2})\b", txt)]
    if not yrs:
        return "", ""
    return str(min(yrs)), str(max(yrs))

def years_count(s):
    a, b = season_min_max(s)
    try:
        return int(b) - int(a) + 1
    except Exception:
        return ""

rows = []
for _, r in df.iterrows():
    period = str(r.get("period", ""))
    role = str(r.get("fav_dog", ""))
    period_key = period_map.get(period)
    if not period_key:
        continue

    first_season, last_season = season_min_max(r.get("seasons", ""))

    rows.append({
        "team": str(r.get("current_team", "")).strip(),
        "head_coach": str(r.get("coach", "")).strip(),
        "teams_tracked": str(r.get("historical_teams", "")).strip(),
        "period": period,
        "period_key": period_key,
        "fav_dog": role,
        "role_key": role.lower(),
        "role_label": role,
        "games": clean_num(r.get("games")),
        "ats_record": str(r.get("ats_record", "")).strip(),
        "ats_pct": clean_num(r.get("ats_win_pct")),
        "avg_ats_margin": clean_num(r.get("avg_ats_margin")),
        "ou_record": str(r.get("ou_record", "")).strip(),
        "over_pct": clean_num(r.get("over_pct")),
        "avg_total_margin": clean_num(r.get("avg_total_margin")),
        "avg_spread": clean_num(r.get("avg_spread")),
        "source": str(r.get("source", "")).strip(),
        "first_season": first_season,
        "last_season": last_season,
        "years": years_count(r.get("seasons", "")),
    })

out = pd.DataFrame(rows)

# ATS rank should behave like the existing page: best ATS margin ranks first.
if not out.empty:
    out["ats_rank"] = ""
    for (period_key, role_key), g in out.groupby(["period_key", "role_key"], dropna=False):
        idxs = g.sort_values("avg_ats_margin", ascending=False, na_position="last").index
        for rank, idx in enumerate(idxs, start=1):
            out.loc[idx, "ats_rank"] = rank

records = out.to_dict(orient="records")

s = HTML.read_text(errors="ignore")

data_start = "/* COACH_FAV_DOG_TRENDS_PAGE_DATA_START */"
data_end = "/* COACH_FAV_DOG_TRENDS_PAGE_DATA_END */"
data_block = (
    data_start + "\n"
    "window.COACH_FAV_DOG_TRENDS_PAGE_ROWS = "
    + json.dumps(records, separators=(",", ":"))
    + ";\n"
    + data_end
    + "\n"
)

pat = re.compile(re.escape(data_start) + r".*?" + re.escape(data_end) + r"\n?", re.S)
if pat.search(s):
    s = pat.sub(lambda m: data_block, s)
else:
    marker = "let coachTrendPeriod = 'game';"
    if marker not in s:
        raise SystemExit("Could not find coachTrendPeriod marker")
    s = s.replace(marker, data_block + marker, 1)

# Add role state.
if "let coachTrendRole = 'all';" not in s:
    s = s.replace(
        "let coachTrendPeriod = 'game';",
        "let coachTrendPeriod = 'game';\nlet coachTrendRole = 'all';",
        1
    )

# Add data accessor.
accessor = r'''
const coachFavDogTrendRows = window.COACH_FAV_DOG_TRENDS_PAGE_ROWS || [];
function currentCoachTrendRoleLabel() {
  if (coachTrendRole === 'favorite') return 'Favorite';
  if (coachTrendRole === 'underdog') return 'Underdog';
  return 'All';
}
function setCoachTrendRole(role) {
  coachTrendRole = role || 'all';
  if ((location.hash || '#/') !== '#coach-betting') location.hash = '#coach-betting';
  else route();
}
'''
if "const coachFavDogTrendRows = window.COACH_FAV_DOG_TRENDS_PAGE_ROWS || [];" not in s:
    s = s.replace(
        "let coachFilterText = '';",
        "let coachFilterText = '';\n" + accessor,
        1
    )

# Replace currentCoachTrendRows.
rows_func = r'''function currentCoachTrendRows() {
  if (coachTrendRole && coachTrendRole !== 'all') {
    return coachFavDogTrendRows.filter(r => r.period_key === coachTrendPeriod && r.role_key === coachTrendRole);
  }
  if (coachTrendPeriod === '1h') return coach1hBettingRows;
  if (coachTrendPeriod === '2h') return coach2hBettingRows;
  return coachBettingRows;
}'''
s = re.sub(r"function currentCoachTrendRows\(\) \{.*?\n\}", rows_func, s, count=1, flags=re.S)

# Replace currentCoachTrendLabel.
label_func = r'''function currentCoachTrendLabel() {
  let base = 'Full Game';
  if (coachTrendPeriod === '1h') base = '1st Half';
  if (coachTrendPeriod === '2h') base = '2nd Half';
  const role = currentCoachTrendRoleLabel();
  return role === 'All' ? base : `${base} · ${role}`;
}'''
s = re.sub(r"function currentCoachTrendLabel\(\) \{.*?\n\}", label_func, s, count=1, flags=re.S)

# Insert role buttons after period buttons, before search input.
role_buttons = r'''
      <button class="pill" onclick="setCoachTrendRole('all')" style="${coachTrendRole==='all'?'background:#183468;border-color:#4470ba':''}">All</button>
      <button class="pill" onclick="setCoachTrendRole('favorite')" style="${coachTrendRole==='favorite'?'background:#183468;border-color:#4470ba':''}">Favorite</button>
      <button class="pill" onclick="setCoachTrendRole('underdog')" style="${coachTrendRole==='underdog'?'background:#183468;border-color:#4470ba':''}">Underdog</button>
'''
if "setCoachTrendRole('favorite')" not in s:
    s = s.replace(
        '      <input id="coachBettingSearch"',
        role_buttons + '      <input id="coachBettingSearch"',
        1
    )

# Update page subtitle.
s = s.replace(
    "Current 2026 team head coaches with ATS and over/under records. Use the period buttons to switch between full game, 1st half, and 2nd half. 1H/2H data is partial through 2025-09-14.",
    "Current 2026 team head coaches with ATS and over/under records. Use period and role buttons to switch full game, 1H, 2H, all games, favorites, and underdogs. Fav/Dog full-game rows use CFBD coach-tenure history; 1H/2H rows use SGO 2024–25."
)

HTML.write_text(s)

print("embedded coach fav/dog trends rows:", len(records))
print("period/role counts:")
if not out.empty:
    print(out.groupby(["period_key", "role_key"]).size().reset_index(name="rows").to_string(index=False))
print("patched:", HTML)
