#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import re

ROOT = Path(".")
OUT_DIR = ROOT / "data/coach"
AUDIT_DIR = ROOT / "data/audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

SPLITS_FILE = ROOT / "data/coach/coach_fav_dog_splits_hybrid.csv"

GAME_CANDIDATES = [
    "data/projections/game_projection_blend_2026.csv",
    "data/projections/game_projection_sources_2026.csv",
    "data/games/game_projection_blend_2026.csv",
    "game_projection_blend_2026.csv",
    "data/site/game_rows_2026.csv",
]

TEAM_CANDIDATES = [
    "teams.csv",
    "data/teams.csv",
    "data/import/teams.csv",
    "Coach_betting_data/coach_team_mapping_review.csv",
    "data/import/coach_halves_missing_teams.csv",
]

def norm(x):
    s = str(x or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace(".", "")
    s = s.replace("&", "and")
    return s.lower()

def pick_col(df, exact=(), contains=()):
    for e in exact:
        for c in df.columns:
            if str(c).strip().lower() == e:
                return c
    for k in contains:
        for c in df.columns:
            if k in str(c).strip().lower():
                return c
    return None

def find_file(candidates):
    for f in candidates:
        p = ROOT / f
        if p.exists():
            return p
    return None

def spread_side_for_team(row, team, away_col, home_col, spread_col):
    """
    Projection file convention:
    - blend_spread_home / site_spread_home is a home-team edge value.
    - Positive = home team favored.
    - Negative = away team favored.
    - Zero = pick.

    Example:
    Baylor at Auburn, blend_spread_home = +6.7, text = Auburn -6.7.
    Auburn is Favorite, Baylor is Underdog.
    """
    spread = pd.to_numeric(row.get(spread_col), errors="coerce")
    if pd.isna(spread):
        return ""

    team_norm = norm(team)
    away = norm(row.get(away_col, ""))
    home = norm(row.get(home_col, ""))
    colname = str(spread_col).lower()

    if team_norm not in {away, home}:
        return ""

    # Our projection columns ending in _home are home-team edge, not betting spread.
    if "spread_home" in colname or colname.endswith("_home"):
        if spread > 0:
            favorite = home
        elif spread < 0:
            favorite = away
        else:
            return "Pick"

        return "Favorite" if team_norm == favorite else "Underdog"

    # Fallback for true betting-spread columns:
    # Negative team spread = favorite; positive team spread = underdog.
    if "home" in colname:
        team_spread = spread if team_norm == home else -spread
    elif "away" in colname:
        team_spread = spread if team_norm == away else -spread
    else:
        # Default to home-edge convention for generic projection spread.
        if spread > 0:
            favorite = home
        elif spread < 0:
            favorite = away
        else:
            return "Pick"
        return "Favorite" if team_norm == favorite else "Underdog"

    if team_spread < 0:
        return "Favorite"
    if team_spread > 0:
        return "Underdog"
    return "Pick"

if not SPLITS_FILE.exists():
    raise SystemExit(f"Missing {SPLITS_FILE}. Run build_coach_fav_dog_splits_all_periods.py first.")

splits = pd.read_csv(SPLITS_FILE, low_memory=False)


# Preserve prebuilt display fields from hybrid splits.
for _c in ["ats_record", "ou_record", "source"]:
    if _c not in splits.columns:
        splits[_c] = ""

splits["team_norm"] = splits["current_team"].map(norm)

game_file = find_file(GAME_CANDIDATES)
if not game_file:
    raise SystemExit("Could not find game projection file.")

games = pd.read_csv(game_file, low_memory=False)

away_col = pick_col(games, exact=["away_team", "away", "visitor"], contains=["away_team", "away"])
home_col = pick_col(games, exact=["home_team", "home"], contains=["home_team", "home"])

spread_col = pick_col(
    games,
    exact=[
        "projected_spread",
        "proj_spread",
        "blend_spread",
        "site_spread",
        "home_spread",
        "spread",
    ],
    contains=[
        "projected_spread",
        "proj_spread",
        "blend_spread",
        "site spread",
        "spread",
    ],
)

game_id_col = pick_col(games, exact=["game_id", "id"], contains=["game_id"])
date_col = pick_col(games, exact=["date", "game_date"], contains=["date"])
total_col = pick_col(games, exact=["projected_total", "proj_total", "blend_total", "total"], contains=["total"])

audit = {
    "game_file": str(game_file),
    "game_rows": len(games),
    "away_col": away_col or "",
    "home_col": home_col or "",
    "spread_col": spread_col or "",
    "total_col": total_col or "",
    "game_id_col": game_id_col or "",
    "date_col": date_col or "",
    "splits_file": str(SPLITS_FILE),
    "split_rows": len(splits),
}

pd.DataFrame([audit]).to_csv(AUDIT_DIR / "game_coach_fav_dog_context_audit.csv", index=False)

if not all([away_col, home_col, spread_col]):
    print("Column audit:")
    for k, v in audit.items():
        print(f"{k}: {v}")
    raise SystemExit("Missing away/home/spread column. See data/audit/game_coach_fav_dog_context_audit.csv")

rows = []

for _, g in games.iterrows():
    game_id = g.get(game_id_col, "") if game_id_col else ""
    date = g.get(date_col, "") if date_col else ""
    away = str(g.get(away_col, "")).strip()
    home = str(g.get(home_col, "")).strip()

    for side, team in [("away", away), ("home", home)]:
        applicable = spread_side_for_team(g, team, away_col, home_col, spread_col)
        team_splits = splits[splits["team_norm"] == norm(team)].copy()

        if team_splits.empty:
            rows.append({
                "game_id": game_id,
                "date": date,
                "team_side": side,
                "team": team,
                "opponent": home if side == "away" else away,
                "projected_team_role": applicable,
                "period": "",
                "fav_dog": "",
                "is_applicable": False,
                "coach": "",
                "historical_teams": "",
                "games": "",
                "ats_record": "No 2024-25 HC fav/dog sample",
                "ats_win_pct": "",
                "ou_record": "",
                "over_pct": "",
                "avg_spread": "",
            })
            continue

        for _, r in team_splits.iterrows():
            fav_dog = str(r.get("fav_dog", "")).strip()
            is_app = fav_dog == applicable

            ats_record = f"{int(r.get('ats_w', 0))}-{int(r.get('ats_l', 0))}"
            if int(r.get("ats_push", 0) or 0):
                ats_record += f"-{int(r.get('ats_push', 0))}"

            ou_record = f"{int(r.get('overs', 0))} O / {int(r.get('unders', 0))} U"
            if int(r.get("total_push", 0) or 0):
                ou_record += f" / {int(r.get('total_push', 0))} P"

            rows.append({
                "game_id": game_id,
                "date": date,
                "team_side": side,
                "team": team,
                "opponent": home if side == "away" else away,
                "projected_team_role": applicable,
                "period": r.get("period", ""),
                "fav_dog": fav_dog,
                "is_applicable": is_app,
                "coach": r.get("coach", ""),
                "historical_teams": r.get("historical_teams", ""),
                "games": r.get("games", ""),
                "ats_record": ats_record,
                "ats_win_pct": r.get("ats_win_pct", ""),
                "avg_ats_margin": r.get("avg_ats_margin", ""),
                "ou_record": ou_record,
                "over_pct": r.get("over_pct", ""),
                "avg_total_margin", "source": r.get("avg_total_margin", "source", ""),
                "avg_spread": r.get("avg_spread", ""),
            })

out = pd.DataFrame(rows)

# Defensive fix: preserve hybrid split display records/source after context expansion.
_key_cols = ["coach", "current_team", "fav_dog", "period"]
_display_cols = ["ats_record", "ou_record", "source"]
if all(c in splits.columns for c in _key_cols):
    _lookup_cols = [c for c in _key_cols + _display_cols if c in splits.columns]
    _lookup = splits[_lookup_cols].drop_duplicates()
    if "current_team" not in out.columns and "team" in out.columns:
        out["current_team"] = out["team"]
    out = out.merge(
        _lookup,
        on=[c for c in _key_cols if c in out.columns and c in _lookup.columns],
        how="left",
        suffixes=("", "_split")
    )
    for _c in _display_cols:
        _sc = _c + "_split"
        if _sc in out.columns:
            bad = out.get(_c, "").astype(str).isin(["", "0-0", "0 O / 0 U", "nan"])
            out.loc[bad, _c] = out.loc[bad, _sc]
            out = out.drop(columns=[_sc])
    out = out.drop(columns=["current_team"], errors="ignore")

if "source" not in out.columns:
    out["source"] = ""


out.to_csv(OUT_DIR / "game_coach_fav_dog_context.csv", index=False)

print("wrote:", OUT_DIR / "game_coach_fav_dog_context.csv", "rows:", len(out))
print("wrote:", AUDIT_DIR / "game_coach_fav_dog_context_audit.csv")

print("\nAudit:")
for k, v in audit.items():
    print(f"{k}: {v}")

print("\nSample applicable rows:")
sample = out[out["is_applicable"] == True].head(40)
print(sample.to_string(index=False))
