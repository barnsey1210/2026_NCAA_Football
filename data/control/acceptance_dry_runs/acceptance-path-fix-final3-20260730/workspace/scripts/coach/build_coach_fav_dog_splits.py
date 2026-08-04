#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import re
import math

ROOT = Path(".")
OUT = ROOT / "data/coach"
AUDIT = ROOT / "data/audit"
OUT.mkdir(parents=True, exist_ok=True)
AUDIT.mkdir(parents=True, exist_ok=True)

TEAM_GAME_CANDIDATES = [
    "data/import/coach_halves_team_games_2024_2025.csv",
    "Coach_betting_data/team_games_2006_2025.csv",
    "data/import/sgo_team_games.csv",
    "data/import/sgo_team_game_betting.csv",
    "data/import/team_game_betting.csv",
]

TENURES_FILE = ROOT / "Coach_betting_data/coach_tenures_2006_2025.csv"

def norm(x):
    s = str(x or "").strip()
    s = re.sub(r"\s+", " ", s)
    s = s.replace(".", "")
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

def ats_result_from_margin(x):
    if pd.isna(x):
        return None
    try:
        v = float(x)
    except Exception:
        return None
    if v > 0:
        return "W"
    if v < 0:
        return "L"
    return "P"

def total_result(points, total):
    try:
        p = float(points)
        t = float(total)
    except Exception:
        return None
    if p > t:
        return "O"
    if p < t:
        return "U"
    return "P"

def side_from_spread(spread):
    try:
        s = float(spread)
    except Exception:
        return None
    if s < 0:
        return "Favorite"
    if s > 0:
        return "Underdog"
    return "Pick"

def load_team_games():
    tried = []
    for f in TEAM_GAME_CANDIDATES:
        p = ROOT / f
        if not p.exists():
            tried.append((f, "missing"))
            continue
        df = pd.read_csv(p, low_memory=False)
        tried.append((f, f"loaded rows={len(df)}"))
        return p, df, tried

    # fallback search
    for p in sorted(ROOT.rglob("*.csv")):
        if any(x in p.parts for x in [".git", "backups", "__pycache__"]):
            continue
        name = p.as_posix().lower()
        if any(k in name for k in ["sgo", "team_game", "game_bet", "halves_team_games"]):
            try:
                df = pd.read_csv(p, low_memory=False)
            except Exception:
                continue
            low = " | ".join(str(c).lower() for c in df.columns)
            if any(k in low for k in ["spread", "ats +/-", "game ats", "team score", "total line"]):
                tried.append((p.as_posix(), f"fallback loaded rows={len(df)}"))
                return p, df, tried

    return None, None, tried

def load_tenures():
    if not TENURES_FILE.exists():
        return None
    df = pd.read_csv(TENURES_FILE, low_memory=False)
    team_col = pick_col(df, exact=["team"], contains=["team"])
    coach_col = pick_col(df, exact=["head coach", "coach"], contains=["coach"])
    season_col = pick_col(df, exact=["season", "year"], contains=["season", "year"])
    if not all([team_col, coach_col, season_col]):
        return None
    out = df[[team_col, coach_col, season_col]].copy()
    out.columns = ["team", "coach", "season"]
    out["team_norm"] = out["team"].map(norm)
    out["season"] = pd.to_numeric(out["season"], errors="coerce")
    return out.dropna(subset=["season"])

src_path, games, tried = load_team_games()

pd.DataFrame(tried, columns=["candidate", "status"]).to_csv(AUDIT / "coach_fav_dog_source_attempts.csv", index=False)

if games is None or games.empty:
    raise SystemExit("No usable team-game betting source found. See data/audit/coach_fav_dog_source_attempts.csv")

cols = list(games.columns)
low_cols = {str(c).strip().lower(): c for c in cols}

team_col = pick_col(games, exact=["current team", "team", "school"], contains=["current team", "team"])
coach_col = pick_col(games, exact=["current coach", "head coach", "coach"], contains=["current coach", "coach"])
season_col = pick_col(games, exact=["season", "year"], contains=["season", "year"])

# Spread from team perspective. Prefer explicit spread. If not available, use ATS margin only for ATS result but cannot classify favorite/dog.
spread_col = pick_col(games, exact=["spread", "closing spread", "team spread", "game spread", "line"], contains=["spread"])
ats_margin_col = pick_col(games, exact=["game ats +/-", "ats +/-", "ats margin"], contains=["game ats +/-", "ats +/-", "ats margin"])
ats_result_col = pick_col(games, exact=["game ats result", "ats result"], contains=["game ats result", "ats result"])

total_line_col = pick_col(games, exact=["game total line", "total line", "closing total"], contains=["game total line", "total line", "closing total"])
total_points_col = pick_col(games, exact=["game total points", "total points"], contains=["game total points", "total points"])
total_result_col = pick_col(games, exact=["game total result", "total result"], contains=["game total result", "total result"])

# If current half-game file is used, it may not have season, but has Seasons Covered in aggregate; game rows usually should have season.
audit = {
    "source_file": src_path.as_posix(),
    "rows": len(games),
    "columns": ", ".join(map(str, cols)),
    "team_col": team_col or "",
    "coach_col": coach_col or "",
    "season_col": season_col or "",
    "spread_col": spread_col or "",
    "ats_margin_col": ats_margin_col or "",
    "ats_result_col": ats_result_col or "",
    "total_line_col": total_line_col or "",
    "total_points_col": total_points_col or "",
    "total_result_col": total_result_col or "",
}

pd.DataFrame([audit]).to_csv(AUDIT / "coach_fav_dog_column_audit.csv", index=False)

if team_col is None:
    raise SystemExit("Could not identify team column. See data/audit/coach_fav_dog_column_audit.csv")

df = games.copy()

df["team"] = df[team_col].astype(str).str.strip()
df["team_norm"] = df["team"].map(norm)

if coach_col:
    df["coach"] = df[coach_col].astype(str).str.strip()
else:
    ten = load_tenures()
    if ten is None or season_col is None:
        raise SystemExit("No coach column and could not map via coach tenures.")
    df["season"] = pd.to_numeric(df[season_col], errors="coerce")
    df = df.merge(ten, on=["team_norm", "season"], how="left")

if season_col and "season" not in df.columns:
    df["season"] = pd.to_numeric(df[season_col], errors="coerce")

# We need a spread to classify fav/dog.
if spread_col is None:
    msg = (
        "No team-perspective spread column found. "
        "Can compute ATS records if ATS result exists, but cannot split Favorite/Underdog. "
        "Need SGO/CFBD game lines with team spread."
    )
    print(msg)
    pd.DataFrame([{"error": msg, **audit}]).to_csv(AUDIT / "coach_fav_dog_build_error.csv", index=False)
    raise SystemExit(msg)

df["team_spread"] = pd.to_numeric(df[spread_col], errors="coerce")
df["fav_dog"] = df["team_spread"].map(side_from_spread)

if ats_result_col:
    df["ats_result"] = df[ats_result_col].astype(str).str.upper().str[0]
elif ats_margin_col:
    df["ats_result"] = pd.to_numeric(df[ats_margin_col], errors="coerce").map(ats_result_from_margin)
else:
    df["ats_result"] = None

if total_result_col:
    df["total_result"] = df[total_result_col].astype(str).str.upper().str[0]
elif total_line_col and total_points_col:
    df["total_result"] = [
        total_result(p, t) for p, t in zip(df[total_points_col], df[total_line_col])
    ]
else:
    df["total_result"] = None

usable = df[
    df["coach"].astype(str).str.strip().ne("")
    & df["team"].astype(str).str.strip().ne("")
    & df["fav_dog"].isin(["Favorite", "Underdog", "Pick"])
].copy()

usable.to_csv(OUT / "coach_fav_dog_game_rows.csv", index=False)

def agg_group(g):
    ats_w = (g["ats_result"] == "W").sum()
    ats_l = (g["ats_result"] == "L").sum()
    ats_p = (g["ats_result"] == "P").sum()
    ats_games = ats_w + ats_l + ats_p

    over = (g["total_result"] == "O").sum()
    under = (g["total_result"] == "U").sum()
    total_p = (g["total_result"] == "P").sum()
    total_games = over + under + total_p

    return pd.Series({
        "games": len(g),
        "ats_games": ats_games,
        "ats_w": ats_w,
        "ats_l": ats_l,
        "ats_push": ats_p,
        "ats_win_pct": ats_w / (ats_w + ats_l) if (ats_w + ats_l) else None,
        "over_games": total_games,
        "overs": over,
        "unders": under,
        "total_push": total_p,
        "over_pct": over / (over + under) if (over + under) else None,
        "avg_spread": pd.to_numeric(g["team_spread"], errors="coerce").mean(),
        "seasons": ", ".join(map(str, sorted(set(int(x) for x in g["season"].dropna())))) if "season" in g else "",
    })

summary = (
    usable
    .groupby(["coach", "team", "fav_dog"], dropna=False)
    .apply(agg_group)
    .reset_index()
    .sort_values(["coach", "team", "fav_dog"])
)

summary.to_csv(OUT / "coach_fav_dog_splits.csv", index=False)

print("source:", src_path)
print("wrote:", OUT / "coach_fav_dog_game_rows.csv", "rows:", len(usable))
print("wrote:", OUT / "coach_fav_dog_splits.csv", "rows:", len(summary))
print("wrote:", AUDIT / "coach_fav_dog_column_audit.csv")

print("\nColumn audit:")
for k, v in audit.items():
    print(f"{k}: {v}")

print("\nSample summary:")
print(summary.head(40).to_string(index=False))
