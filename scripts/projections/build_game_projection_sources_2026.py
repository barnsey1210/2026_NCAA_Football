#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import json, re
import pandas as pd

PRESEASON_DB = Path("data/snapshots/preseason/preseason_db.json")
RATINGS = Path("data/ratings/ratings_master_latest.csv")
OUT = Path("data/projections/game_projection_sources_2026.csv")
AUDIT = Path("data/projections/game_projection_sources_audit_2026.csv")
MASSEY = Path("data/ratings/external_sources/massey_game_projections_2026.csv")
SAGARIN = Path("data/ratings/external_sources/sagarin_game_predictions_latest.csv")
DRATINGS = Path("data/ratings/external_sources/dratings_ncaaf_predictions_latest.csv")
NON_NEUTRAL_HFA = 2.6
RATING_SOURCES = {"SP+": "spplus", "FPI": "fpi", "TeamRankings": "teamrankings"}

def norm(x):
    return re.sub(r"[^a-z0-9]+", " ", str(x or "").lower()).strip()

def load_db():
    db = json.loads(PRESEASON_DB.read_text())
    games = db.get("games")
    if not isinstance(games, list) or not games:
        raise SystemExit(f"{PRESEASON_DB} does not contain a non-empty games list")
    return db

def site_game_index(db):
    return {(str(g.get("date")), norm(g.get("away_team")), norm(g.get("home_team"))): g
            for g in db.get("games", [])}

def add_common(row, source, g, spread_home, total, away_score=None, home_score=None,
               home_win_prob=None, source_url="", notes=""):
    return {
        "snapshot_date": datetime.now().date().isoformat(),
        "season": 2026, "source": source, "game_id": g.get("game_id") if g else "",
        "week": g.get("week") if g else "", "date": g.get("date") if g else row.get("game_date", ""),
        "away_team": g.get("away_team") if g else row.get("away_team"),
        "home_team": g.get("home_team") if g else row.get("home_team"),
        "spread_home": spread_home, "total": total, "away_score": away_score,
        "home_score": home_score, "home_win_prob": home_win_prob,
        "source_url": source_url, "pulled_at": row.get("pulled_at", ""), "notes": notes,
    }

def load_rating_game_projections(db):
    rows, audit = [], []
    if not RATINGS.exists():
        return rows, [{"source":"Rating Game Projections","status":"missing ratings master","rows":0}]
    rdf = pd.read_csv(RATINGS)
    by_team = {norm(r["team"]): r for r in rdf.to_dict("records")}
    for g in db.get("games", []):
        home, away = by_team.get(norm(g.get("home_team"))), by_team.get(norm(g.get("away_team")))
        for source, col in RATING_SOURCES.items():
            hv = home.get(col) if home else None
            av = away.get(col) if away else None
            ok = pd.notna(hv) and pd.notna(av)
            audit.append({"source":source,"date":g.get("date"),"away":g.get("away_team"),
                          "home":g.get("home_team"),"matched":bool(ok),"game_id":g.get("game_id")})
            if not ok:
                continue
            hfa = 0.0 if bool(g.get("neutral_site")) else NON_NEUTRAL_HFA
            rows.append(add_common({}, source, g, float(hv)-float(av)+hfa, "",
                                   notes=f"{source} team-rating projection: home - away + {hfa:g} HFA."))
    return rows, audit

def load_massey(idx):
    rows, audit = [], []
    if not MASSEY.exists():
        return rows, [{"source":"Massey Games","status":"missing","rows":0}]
    for _, r in pd.read_csv(MASSEY).iterrows():
        g = idx.get((str(r.get("game_date")), norm(r.get("away_team")), norm(r.get("home_team"))))
        audit.append({"source":"Massey Games","date":r.get("game_date"),"away":r.get("away_team"),
                      "home":r.get("home_team"),"matched":bool(g),"game_id":g.get("game_id") if g else ""})
        if g:
            rows.append(add_common(r,"Massey Games",g,r.get("projected_spread_home"),r.get("projected_total"),
                                   r.get("away_projected_points"),r.get("home_projected_points"),
                                   r.get("home_win_prob"),r.get("source_url","https://masseyratings.com/cf/fbs/games"),
                                   "Massey rendered games page projection."))
    return rows, audit

def load_dratings(idx):
    rows, audit = [], []
    if not DRATINGS.exists():
        return rows, [{"source":"DRatings Predictions","status":"missing/inactive","rows":0}]
    for _, r in pd.read_csv(DRATINGS).iterrows():
        g = idx.get((str(r.get("game_date")), norm(r.get("away_team")), norm(r.get("home_team"))))
        audit.append({"source":"DRatings Predictions","date":r.get("game_date"),"away":r.get("away_team"),
                      "home":r.get("home_team"),"matched":bool(g),"game_id":g.get("game_id") if g else ""})
        if g:
            rows.append(add_common(r,"DRatings Predictions",g,r.get("projected_spread_home"),r.get("projected_total"),
                                   r.get("away_projected_points"),r.get("home_projected_points"),
                                   r.get("home_win_prob"),r.get("source_url","https://www.dratings.com/predictor/ncaa-football-predictions/"),
                                   "DRatings live NCAA football game prediction."))
    return rows, audit

def load_sagarin(idx):
    rows, audit = [], []
    if not SAGARIN.exists():
        return rows, [{"source":"Sagarin Predictions","status":"missing","rows":0}]
    df = pd.read_csv(SAGARIN)
    if df.empty:
        return rows, [{"source":"Sagarin Predictions","status":"empty/no active games","rows":0}]
    for _, r in df.iterrows():
        g = None
        if pd.notna(r.get("game_date")):
            g = idx.get((str(r.get("game_date")), norm(r.get("away_team")), norm(r.get("home_team"))))
        if not g:
            for sg in idx.values():
                if norm(sg.get("away_team")) == norm(r.get("away_team")) and norm(sg.get("home_team")) == norm(r.get("home_team")):
                    g = sg
                    break
        audit.append({"source":"Sagarin Predictions","date":r.get("game_date",""),"away":r.get("away_team"),
                      "home":r.get("home_team"),"matched":bool(g),"game_id":g.get("game_id") if g else ""})
        if not g:
            continue
        favorite, fav_spread = r.get("favorite"), r.get("favorite_spread_pred")
        spread_home = ""
        if pd.notna(fav_spread):
            fav_spread = float(fav_spread)
            if norm(favorite) == norm(g.get("home_team")): spread_home = fav_spread
            elif norm(favorite) == norm(g.get("away_team")): spread_home = -fav_spread
        source_name = "Sagarin Predictor Home/Away Experimental" if r.get("projection_variant") == "home_away_experimental" else "Sagarin Predictor Prediction"
        rows.append(add_common(r,source_name,g,spread_home,r.get("projected_total"),
                               source_url=r.get("source_url","https://sagarin.com/sports/cfsend.htm#Predictions_with_Totals_and_Moneylines"),
                               notes="Sagarin prediction."))
    return rows, audit

def main():
    db = load_db()
    idx = site_game_index(db)
    all_rows, all_audit = [], []
    rows, audit = load_rating_game_projections(db)
    all_rows += rows; all_audit += audit
    for loader in [load_massey, load_sagarin, load_dratings]:
        rows, audit = loader(idx)
        all_rows += rows; all_audit += audit
    out = pd.DataFrame(all_rows)
    if not out.empty:
        out = out.drop_duplicates(subset=["source","game_id"], keep="last").sort_values(
            ["date","week","away_team","home_team","source"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    aud = pd.DataFrame(all_audit)
    aud.to_csv(AUDIT, index=False)
    print(f"Wrote {OUT}: {len(out)} rows")
    print(f"Wrote {AUDIT}: {len(aud)} rows")
    if len(aud) and "matched" in aud.columns:
        print(aud.groupby("source")["matched"].sum().to_string())

if __name__ == "__main__":
    main()
