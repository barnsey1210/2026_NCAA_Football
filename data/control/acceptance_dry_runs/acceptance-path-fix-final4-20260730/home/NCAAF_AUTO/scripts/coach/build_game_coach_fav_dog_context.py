#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import re

ROOT = Path(".")
SPLITS = ROOT / "data/coach/coach_fav_dog_splits_hybrid.csv"
OUT = ROOT / "data/coach/game_coach_fav_dog_context.csv"
AUDIT = ROOT / "data/audit/game_coach_fav_dog_context_audit.csv"

PROJECTION_CANDIDATES = [
    ROOT / "data/projections/game_projection_blend_2026.csv",
    ROOT / "data/projections/game_projection_sources_2026.csv",
    ROOT / "game_projection_blend_2026.csv",
]

def norm(x):
    return re.sub(r"\s+", " ", str(x or "").strip()).lower()

def pick_projection_file():
    for p in PROJECTION_CANDIDATES:
        if p.exists():
            return p
    raise SystemExit("Missing game projection file")

def num(x):
    return pd.to_numeric(x, errors="coerce")

def role_for_side(home_edge, side):
    """
    blend_spread_home / projected_margin_home convention:
    positive = home favored
    negative = away favored
    """
    try:
        v = float(home_edge)
    except Exception:
        return "Pick"

    if abs(v) < 0.05:
        return "Pick"

    if side == "home":
        return "Favorite" if v > 0 else "Underdog"
    return "Underdog" if v > 0 else "Favorite"

def load_games():
    p = pick_projection_file()
    df = pd.read_csv(p, low_memory=False)

    away_col = "away_team" if "away_team" in df.columns else "away"
    home_col = "home_team" if "home_team" in df.columns else "home"
    game_col = "game_id" if "game_id" in df.columns else None
    date_col = "date" if "date" in df.columns else None

    spread_candidates = [
        "blend_spread_home",
        "projected_margin_home",
        "model_spread_home",
        "market_spread_home",
    ]
    spread_col = next((c for c in spread_candidates if c in df.columns), None)

    if not spread_col:
        raise SystemExit(f"No home-edge spread column found. Columns: {list(df.columns)}")

    out = pd.DataFrame({
        "game_id": df[game_col].astype(str) if game_col else df.index.astype(str),
        "date": df[date_col] if date_col else "",
        "away_team": df[away_col],
        "home_team": df[home_col],
        "home_edge": num(df[spread_col]),
    })

    return out

def main():
    if not SPLITS.exists():
        raise SystemExit(f"Missing {SPLITS}")

    games = load_games()
    splits = pd.read_csv(SPLITS, low_memory=False)

    required = [
        "coach", "current_team", "fav_dog", "period", "games",
        "ats_record", "ats_win_pct", "ou_record", "over_pct",
        "avg_spread", "avg_ats_margin", "avg_total_margin",
        "historical_teams", "source",
    ]
    for c in required:
        if c not in splits.columns:
            splits[c] = ""

    splits["team_key"] = splits["current_team"].map(norm)

    rows = []

    for _, g in games.iterrows():
        for side, team, opp in [
            ("away", g["away_team"], g["home_team"]),
            ("home", g["home_team"], g["away_team"]),
        ]:
            projected_role = role_for_side(g["home_edge"], side)
            team_splits = splits[splits["team_key"].eq(norm(team))].copy()

            if team_splits.empty:
                rows.append({
                    "game_id": g["game_id"],
                    "date": g["date"],
                    "team_side": side,
                    "team": team,
                    "opponent": opp,
                    "projected_team_role": projected_role,
                    "period": "",
                    "fav_dog": projected_role,
                    "is_applicable": False,
                    "coach": "",
                    "historical_teams": "",
                    "games": "",
                    "ats_record": "No current coach fav/dog sample",
                    "ats_win_pct": "",
                    "ou_record": "",
                    "over_pct": "",
                    "avg_spread": "",
                    "avg_ats_margin": "",
                    "avg_total_margin": "",
                    "source": "",
                })
                continue

            for _, r in team_splits.iterrows():
                fav_dog = str(r.get("fav_dog", "")).strip()
                applicable = fav_dog == projected_role

                rows.append({
                    "game_id": g["game_id"],
                    "date": g["date"],
                    "team_side": side,
                    "team": team,
                    "opponent": opp,
                    "projected_team_role": projected_role,
                    "period": r.get("period", ""),
                    "fav_dog": fav_dog,
                    "is_applicable": bool(applicable),
                    "coach": r.get("coach", ""),
                    "historical_teams": r.get("historical_teams", ""),
                    "games": r.get("games", ""),
                    "ats_record": r.get("ats_record", ""),
                    "ats_win_pct": r.get("ats_win_pct", ""),
                    "ou_record": r.get("ou_record", ""),
                    "over_pct": r.get("over_pct", ""),
                    "avg_spread": r.get("avg_spread", ""),
                    "avg_ats_margin": r.get("avg_ats_margin", ""),
                    "avg_total_margin": r.get("avg_total_margin", ""),
                    "source": r.get("source", ""),
                })

    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)

    out.to_csv(OUT, index=False)

    audit = pd.DataFrame([
        {"metric": "games", "value": len(games)},
        {"metric": "teams", "value": len(games) * 2},
        {"metric": "context_rows", "value": len(out)},
        {"metric": "applicable_rows", "value": int(out["is_applicable"].sum())},
        {"metric": "no_sample_rows", "value": int(out["ats_record"].astype(str).eq("No current coach fav/dog sample").sum())},
    ])
    audit.to_csv(AUDIT, index=False)

    print("wrote:", OUT, "rows:", len(out))
    print("wrote:", AUDIT)
    print(audit.to_string(index=False))

if __name__ == "__main__":
    main()
