#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import json
import re
import pandas as pd

PRESEASON_DB = Path("data/snapshots/preseason/preseason_db.json")
OUT = Path("data/projections/game_projection_sources_2026.csv")
AUDIT = Path("data/projections/game_projection_sources_audit_2026.csv")

MASSEY = Path("data/ratings/external_sources/massey_game_projections_2026.csv")
SAGARIN = Path("data/ratings/external_sources/sagarin_game_predictions_latest.csv")
DRATINGS = Path("data/ratings/external_sources/dratings_ncaaf_predictions_latest.csv")

def norm(x):
    return re.sub(r"[^a-z0-9]+", " ", str(x or "").lower()).strip()

def load_db():
    if not PRESEASON_DB.exists():
        raise SystemExit(f"Missing canonical preseason DB: {PRESEASON_DB}")

    try:
        db = json.loads(PRESEASON_DB.read_text())
    except Exception as exc:
        raise SystemExit(f"Could not parse {PRESEASON_DB}: {exc}") from exc

    if not isinstance(db, dict):
        raise SystemExit(f"{PRESEASON_DB} must contain a JSON object")

    games = db.get("games")
    if not isinstance(games, list) or not games:
        raise SystemExit(f"{PRESEASON_DB} does not contain a non-empty games list")

    return db

def site_game_index(db):
    idx = {}
    for g in db.get("games", []):
        key = (str(g.get("date")), norm(g.get("away_team")), norm(g.get("home_team")))
        idx[key] = g
    return idx

def add_common(row, source, g, spread_home, total, away_score=None, home_score=None, home_win_prob=None, source_url="", notes=""):
    return {
        "snapshot_date": datetime.now().date().isoformat(),
        "season": 2026,
        "source": source,
        "game_id": g.get("game_id") if g else "",
        "week": g.get("week") if g else "",
        "date": g.get("date") if g else row.get("game_date", ""),
        "away_team": g.get("away_team") if g else row.get("away_team"),
        "home_team": g.get("home_team") if g else row.get("home_team"),
        "spread_home": spread_home,
        "total": total,
        "away_score": away_score,
        "home_score": home_score,
        "home_win_prob": home_win_prob,
        "source_url": source_url,
        "pulled_at": row.get("pulled_at", ""),
        "notes": notes,
    }

def load_massey(idx):
    rows = []
    audit = []
    if not MASSEY.exists():
        return rows, [{"source": "Massey Games", "status": "missing", "rows": 0}]

    df = pd.read_csv(MASSEY)

    for _, r in df.iterrows():
        key = (str(r.get("game_date")), norm(r.get("away_team")), norm(r.get("home_team")))
        g = idx.get(key)
        audit.append({
            "source": "Massey Games",
            "date": r.get("game_date"),
            "away": r.get("away_team"),
            "home": r.get("home_team"),
            "matched": bool(g),
            "game_id": g.get("game_id") if g else "",
        })
        if not g:
            continue

        rows.append(add_common(
            r,
            "Massey Games",
            g,
            spread_home=r.get("projected_spread_home"),
            total=r.get("projected_total"),
            away_score=r.get("away_projected_points"),
            home_score=r.get("home_projected_points"),
            home_win_prob=r.get("home_win_prob"),
            source_url=r.get("source_url", "https://masseyratings.com/cf/fbs/games"),
            notes="Massey rendered games page projection; spread_home from projected points.",
        ))

    return rows, audit

def load_dratings(idx):
    rows = []
    audit = []
    if not DRATINGS.exists():
        return rows, [{"source": "DRatings Predictions", "status": "missing/inactive", "rows": 0}]

    df = pd.read_csv(DRATINGS)

    for _, r in df.iterrows():
        key = (str(r.get("game_date")), norm(r.get("away_team")), norm(r.get("home_team")))
        g = idx.get(key)
        audit.append({
            "source": "DRatings Predictions",
            "date": r.get("game_date"),
            "away": r.get("away_team"),
            "home": r.get("home_team"),
            "matched": bool(g),
            "game_id": g.get("game_id") if g else "",
        })
        if not g:
            continue

        rows.append(add_common(
            r,
            "DRatings Predictions",
            g,
            spread_home=r.get("projected_spread_home"),
            total=r.get("projected_total"),
            away_score=r.get("away_projected_points"),
            home_score=r.get("home_projected_points"),
            home_win_prob=r.get("home_win_prob"),
            source_url=r.get("source_url", "https://www.dratings.com/predictor/ncaa-football-predictions/"),
            notes="DRatings game prediction page; active once NCAAF predictions are available.",
        ))

    return rows, audit

def load_sagarin(idx):
    rows = []
    audit = []
    if not SAGARIN.exists():
        return rows, [{"source": "Sagarin Predictions", "status": "missing", "rows": 0}]

    df = pd.read_csv(SAGARIN)
    if df.empty:
        return rows, [{"source": "Sagarin Predictions", "status": "empty/no active games", "rows": 0}]

    for _, r in df.iterrows():
        # Sagarin current parsed file may not have date for 2026 page yet.
        # Try matchup-only fallback if date is unavailable.
        key_candidates = []
        if "game_date" in r and pd.notna(r.get("game_date")):
            key_candidates.append((str(r.get("game_date")), norm(r.get("away_team")), norm(r.get("home_team"))))

        # fallback to team pair only
        g = None
        for key in key_candidates:
            g = idx.get(key)
            if g:
                break

        if not g:
            for sg in idx.values():
                if norm(sg.get("away_team")) == norm(r.get("away_team")) and norm(sg.get("home_team")) == norm(r.get("home_team")):
                    g = sg
                    break

        audit.append({
            "source": "Sagarin Predictions",
            "date": r.get("game_date", ""),
            "away": r.get("away_team"),
            "home": r.get("home_team"),
            "variant": r.get("projection_variant", ""),
            "matched": bool(g),
            "game_id": g.get("game_id") if g else "",
        })
        if not g:
            continue

        # Use Sagarin Predictor spread by default.
        favorite = r.get("favorite")
        fav_spread = r.get("favorite_spread_pred")
        spread_home = ""
        if pd.notna(fav_spread):
            fav_spread = float(fav_spread)
            if norm(favorite) == norm(g.get("home_team")):
                spread_home = fav_spread
            elif norm(favorite) == norm(g.get("away_team")):
                spread_home = -fav_spread

        source_name = "Sagarin Predictor Prediction"
        if r.get("projection_variant") == "home_away_experimental":
            source_name = "Sagarin Predictor Home/Away Experimental"

        rows.append(add_common(
            r,
            source_name,
            g,
            spread_home=spread_home,
            total=r.get("projected_total"),
            away_score="",
            home_score="",
            home_win_prob="",
            source_url=r.get("source_url", "https://sagarin.com/sports/cfsend.htm#Predictions_with_Totals_and_Moneylines"),
            notes="Sagarin predictions section. Uses favorite_spread_pred and projected_total; raw score split ignored.",
        ))

    return rows, audit

def main():
    db = load_db()
    idx = site_game_index(db)

    all_rows = []
    all_audit = []

    for loader in [load_massey, load_sagarin, load_dratings]:
        rows, audit = loader(idx)
        all_rows.extend(rows)
        all_audit.extend(audit)

    out = pd.DataFrame(all_rows)
    if not out.empty:
        out = out.drop_duplicates(subset=["source", "game_id"], keep="last")
        out = out.sort_values(["date", "week", "away_team", "home_team", "source"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    aud = pd.DataFrame(all_audit)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    aud.to_csv(AUDIT, index=False)

    print(f"Wrote {OUT}: {len(out)} rows")
    print(f"Wrote {AUDIT}: {len(aud)} rows")
    if len(out):
        print(out.head(80).to_string(index=False))
    print("\nAudit status:")
    if len(aud):
        print(aud.groupby("source")["matched"].sum() if "matched" in aud.columns else aud.groupby("source").size())

if __name__ == "__main__":
    main()
