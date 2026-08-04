#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

ROOT = Path(".")
OUT = ROOT / "data/coach"
AUDIT = ROOT / "data/audit"
OUT.mkdir(parents=True, exist_ok=True)
AUDIT.mkdir(parents=True, exist_ok=True)

SGO = OUT / "coach_fav_dog_splits_all_periods.csv"
CFBD = OUT / "coach_full_game_fav_dog_cfbd_splits.csv"

if not SGO.exists():
    raise SystemExit(f"Missing {SGO}")
if not CFBD.exists():
    raise SystemExit(f"Missing {CFBD}")

sgo = pd.read_csv(SGO, low_memory=False)
cfbd = pd.read_csv(CFBD, low_memory=False)

# Keep only 1H/2H from SGO.
sgo_halves = sgo[sgo["period"].astype(str).isin(["1H", "2H"])].copy()

def build_ats_record_from_cols(r):
    if str(r.get("ats_record", "")).strip():
        return str(r.get("ats_record", "")).strip()
    w = int(float(r.get("ats_w", 0) or 0))
    l = int(float(r.get("ats_l", 0) or 0))
    p = int(float(r.get("ats_push", 0) or 0))
    return f"{w}-{l}" + (f"-{p}" if p else "")

def build_ou_record_from_cols(r):
    if str(r.get("ou_record", "")).strip():
        return str(r.get("ou_record", "")).strip()
    o = int(float(r.get("overs", 0) or 0))
    u = int(float(r.get("unders", 0) or 0))
    p = int(float(r.get("total_push", 0) or 0))
    return f"{o} O / {u} U" + (f" / {p} P" if p else "")

sgo_halves["ats_record"] = sgo_halves.apply(build_ats_record_from_cols, axis=1)
sgo_halves["ou_record"] = sgo_halves.apply(build_ou_record_from_cols, axis=1)

# Normalize CFBD full-game columns into same display schema.
cfbd_fg = cfbd.copy()
cfbd_fg["period"] = "Full Game"

# Re-map CFBD full-game rows to the coach's 2026 current team.
# The CFBD builder knows historical coach/team tenure, but not necessarily 2026 moves.
# SGO/current halves file already has the correct 2026 current_team for active coaches.
coach_current_team_map = (
    sgo[["coach", "current_team"]]
    .dropna()
    .drop_duplicates()
    .groupby("coach")["current_team"]
    .first()
    .to_dict()
)

cfbd_fg["source_current_team_before_2026_remap"] = cfbd_fg["current_team"]
cfbd_fg["current_team"] = cfbd_fg["coach"].map(coach_current_team_map).fillna(cfbd_fg["current_team"])
cfbd_fg["remapped_to_2026_current_team"] = (
    cfbd_fg["current_team"].astype(str) != cfbd_fg["source_current_team_before_2026_remap"].astype(str)
)

# Build display records.
def rec_ats(r):
    w = int(float(r.get("ats_w", 0) or 0))
    l = int(float(r.get("ats_l", 0) or 0))
    p = int(float(r.get("ats_push", 0) or 0))
    return f"{w}-{l}" + (f"-{p}" if p else "")

def rec_ou(r):
    o = int(float(r.get("overs", 0) or 0))
    u = int(float(r.get("unders", 0) or 0))
    p = int(float(r.get("total_push", 0) or 0))
    return f"{o} O / {u} U" + (f" / {p} P" if p else "")

cfbd_fg["ats_record"] = cfbd_fg.apply(rec_ats, axis=1)
cfbd_fg["ou_record"] = cfbd_fg.apply(rec_ou, axis=1)

# Ensure all expected columns exist.
expected = [
    "coach", "current_team", "fav_dog", "period", "games",
    "ats_record", "ats_win_pct", "avg_ats_margin",
    "ou_record", "over_pct", "avg_total_margin",
    "avg_spread", "seasons", "historical_teams", "source"
]

for c in expected:
    if c not in sgo_halves.columns:
        sgo_halves[c] = ""
    if c not in cfbd_fg.columns:
        cfbd_fg[c] = ""

sgo_halves["source"] = "SGO half-game lines/results"
if "seasons" not in sgo_halves.columns or sgo_halves["seasons"].isna().all():
    sgo_halves["seasons"] = "2024-2025"

hybrid = pd.concat(
    [cfbd_fg[expected], sgo_halves[expected]],
    ignore_index=True
)

# Keep only the active 2026 coach/team pairs.
# This removes old Auburn/Baylor/Arkansas coaches from the live matchup context.
active_pairs = (
    sgo[["coach", "current_team"]]
    .dropna()
    .drop_duplicates()
    .assign(
        coach_key=lambda x: x["coach"].astype(str).str.strip().str.lower(),
        team_key=lambda x: x["current_team"].astype(str).str.strip().str.lower()
    )
)

hybrid["coach_key"] = hybrid["coach"].astype(str).str.strip().str.lower()
hybrid["team_key"] = hybrid["current_team"].astype(str).str.strip().str.lower()

hybrid = hybrid.merge(
    active_pairs[["coach_key", "team_key"]].drop_duplicates(),
    on=["coach_key", "team_key"],
    how="inner"
)

hybrid = hybrid.drop(columns=["coach_key", "team_key"], errors="ignore")

hybrid = hybrid.sort_values(["current_team", "coach", "fav_dog", "period"])

hybrid.to_csv(OUT / "coach_fav_dog_splits_hybrid.csv", index=False)

audit = pd.DataFrame([
    {
        "source": "CFBD full-game",
        "periods": "Full Game",
        "rows": len(cfbd_fg),
        "games_total": pd.to_numeric(cfbd_fg["games"], errors="coerce").sum(),
        "season_min": str(cfbd_fg.get("seasons", "").astype(str).str.extract(r"(\d{4})")[0].dropna().min()),
        "season_max": str(cfbd_fg.get("seasons", "").astype(str).str.extract(r"(\d{4})(?!.*\d{4})")[0].dropna().max()),
    },
    {
        "source": "SGO",
        "periods": "1H, 2H",
        "rows": len(sgo_halves),
        "games_total": pd.to_numeric(sgo_halves["games"], errors="coerce").sum(),
        "season_min": "2024",
        "season_max": "2025",
    },
    {
        "source": "Hybrid",
        "periods": "Full Game, 1H, 2H",
        "rows": len(hybrid),
        "games_total": pd.to_numeric(hybrid["games"], errors="coerce").sum(),
        "season_min": "",
        "season_max": "",
    },
])

audit.to_csv(AUDIT / "coach_fav_dog_hybrid_audit.csv", index=False)

print("wrote:", OUT / "coach_fav_dog_splits_hybrid.csv", "rows:", len(hybrid))
print("wrote:", AUDIT / "coach_fav_dog_hybrid_audit.csv")
print(audit.to_string(index=False))

print("\nSample Auburn/Baylor/Arkansas:")
mask = hybrid["current_team"].astype(str).isin(["Auburn", "Baylor", "Arkansas", "Alabama"])
print(hybrid[mask].head(80).to_string(index=False))
