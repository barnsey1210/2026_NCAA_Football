#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import json, re, sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.ncaaf_config import canonical_team

PRESEASON_DB = Path("data/snapshots/preseason/preseason_db.json")
RATINGS = Path("data/ratings/ratings_latest.csv")
OUT = Path("data/projections/game_projection_sources_2026.csv")
AUDIT = Path("data/projections/game_projection_sources_audit_2026.csv")
MASSEY = Path("data/ratings/external_sources/massey_game_projections_2026.csv")
SAGARIN = Path("data/ratings/external_sources/sagarin_game_predictions_latest.csv")
DRATINGS = Path("data/ratings/external_sources/dratings_ncaaf_predictions_latest.csv")
NON_NEUTRAL_HFA = 2.6
RATING_SOURCES = {
    "SP+": "SP+",
    "FPI": "FPI",
    "TeamRankings": "TeamRankings",
    "Sagarin Rating": "Sagarin Predictor",
}

TEAM_ALIASES = {
    "san jose st": "san jose state",
    "north dakota st": "north dakota state",
    "n dakota st": "north dakota state",
    "n dakota": "north dakota",
    "e michigan": "eastern michigan",
    "w michigan": "western michigan",
    "c michigan": "central michigan",
    "n illinois": "northern illinois",
    "appalachian st": "app state",
    "app st": "app state",
    "ga southern": "georgia southern",
    "georgia st": "georgia state",
    "florida st": "florida state",
    "fl atlantic": "florida atlantic",
    "florida intl": "florida international",
    "miami fl": "miami",
    "new mexico st": "new mexico state",
    "oregon st": "oregon state",
    "washington st": "washington state",
    "mississippi st": "mississippi state",
    "sam houston st": "sam houston",
    "south dakota st": "south dakota state",
    "s dakota st": "south dakota state",
    "uconn": "connecticut",
    "jacksonville st": "jacksonville state",
    "new mexico st": "new mexico state",
    "florida st": "florida state",
    "oregon st": "oregon state",
    "ohio st": "ohio state",
    "ball st": "ball state",
    "kent": "kent state",
    "kent st": "kent state",
    "wku": "western kentucky",
    "western ky": "western kentucky",
    "southeast missouri st": "southeast missouri state",
    "se missouri st": "southeast missouri state",
    "charleston so": "charleston southern",
    "alabama st": "alabama state",
    "southern miss": "southern mississippi",
    "southern mississippi": "southern miss",
    "ul monroe": "ulm",
    "ulm": "ulm",
    "ul lafayette": "louisiana",
    "louisiana lafayette": "louisiana",
    "lafayette": "lafayette",
    "ut san antonio": "utsa",
    "utah st": "utah state",
    "washington st": "washington state",
    "mississippi": "ole miss",
    "mississippi st": "mississippi state",
    "sam houston st": "sam houston",
    "cs sacramento": "sacramento state",
    "cal poly": "cal poly",
    "e michigan": "eastern michigan",
    "san jose st": "san jose state",
    "n dakota st": "north dakota state",
    "n illinois": "northern illinois",
    "w michigan": "western michigan",
    "c michigan": "central michigan",
    "ms valley st": "mississippi valley state",
    "nw louisiana": "northwestern state",
    "northwestern la": "northwestern state",
    "florida a and m": "florida a m",
}


def norm(x):
    n = re.sub(r"[^a-z0-9]+", " ", str(x or "").lower()).strip()
    n = TEAM_ALIASES.get(n, n)
    if n.endswith(" st"):
        n = n[:-3] + " state"
    n = TEAM_ALIASES.get(n, n)
    return n

def massey_match_key(x):
    """
    Canonical matching layer for Massey game projections.

    Massey uses a large number of abbreviations that the preseason DB
    does not use (St, N Dakota, E Michigan, CS Sacramento, etc.).
    Keep this isolated here so other projection sources are not affected.
    """
    n = norm(canonical_team(x))

    aliases = {
        "san jose st": "san jose state",
        "n dakota st": "north dakota state",
        "north dakota st": "north dakota state",
        "cs sacramento": "sacramento state",
        "e michigan": "eastern michigan",
        "w michigan": "western michigan",
        "c michigan": "central michigan",
        "n illinois": "northern illinois",
        "northern illinois": "northern illinois",
        "boise st": "boise state",
        "fresno st": "fresno state",
        "oregon st": "oregon state",
        "washington st": "washington state",
        "oklahoma st": "oklahoma state",
        "kansas st": "kansas state",
        "michigan st": "michigan state",
        "mississippi st": "mississippi state",
        "missouri st": "missouri state",
        "appalachian st": "app state",
        "app st": "app state",
        "ga southern": "georgia southern",
        "ga state": "georgia state",
        "georgia st": "georgia state",
        "florida st": "florida state",
        "florida intl": "florida international",
        "fl atlantic": "florida atlantic",
        "utsa": "utsa",
        "ut san antonio": "utsa",
        "sam houston st": "sam houston",
        "sam houston state": "sam houston",
        "ul monroe": "ul monroe",
        "ulm": "ul monroe",
        "ul lafayette": "louisiana",
        "la lafayette": "louisiana",
        "la tech": "louisiana tech",
        "louisiana tech": "louisiana tech",
        "mtsu": "middle tennessee",
        "middle tenn": "middle tennessee",
        "wku": "western kentucky",
        "western ky": "western kentucky",
        "s dakota st": "south dakota state",
        "south dakota st": "south dakota state",
        "e kentucky": "eastern kentucky",
        "eastern ky": "eastern kentucky",
        "c michigan": "central michigan",
        "houston chr": "houston christian",
        "houston baptist": "houston christian",
        "nw louisiana": "northwestern state",
        "northwestern la": "northwestern state",
        "ms valley st": "mississippi valley state",
        "ark pine bluff": "arkansas pine bluff",
        "tx southern": "texas southern",
        "tn martin": "tennessee martin",
        "utrgv": "ut rio grande valley",
        "cs sacramento": "sacramento state",
        "sacramento st": "sacramento state",
        "bethune cookman": "bethune cookman",
        "bethune cookman university": "bethune cookman",
        "sunny albany": "albany",
        "suny albany": "albany",
        "albany ny": "albany",
        "e illinois": "eastern illinois",
        "eastern ill": "eastern illinois",
        "uconn": "connecticut",
        "connecticut": "connecticut",
        "li u post": "liu",
        "liupost": "liu",
        "utah tech": "utah tech",
        "charleston so": "charleston southern",
        "ga southern": "georgia southern",
        "nc a t": "north carolina a t",
        "nc a&t": "north carolina a t",
        "florida intl": "florida international",
        "miami fl": "miami florida",
        "miami fl": "miami florida",
        "miami fl": "miami florida",
    }

    n = aliases.get(n, n)

    if n.endswith(" st"):
        n = n[:-3] + " state"

    return n

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

def explicit_spplus_total(game):
    """Return only the authoritative preseason SP+ offense/defense baseline total."""
    preserved = game.get("projection_overlay_previous_total")
    if preserved is not None and str(preserved).strip() not in ("", "nan", "None"):
        try:
            return float(preserved)
        except (TypeError, ValueError):
            pass

    source_label = str(game.get("projection_total_sources") or "").lower()
    model_version = str(game.get("projection_total_model_version") or "").strip().lower()
    value = game.get("projected_total")

    if "sp+" in source_label and not model_version:
        try:
            if value is not None and str(value).strip() not in ("", "nan", "None"):
                return float(value)
        except (TypeError, ValueError):
            pass
    return None

def load_rating_game_projections(db):
    rows, audit = [], []
    if not RATINGS.exists():
        return rows, [{"source":"Rating Game Projections","status":"missing ratings master","rows":0}]
    rdf = pd.read_csv(RATINGS)
    rdf = rdf[rdf["source"].isin(RATING_SOURCES.values())].copy()
    rdf = rdf.sort_values(["snapshot_date", "pulled_at"]).drop_duplicates(
        subset=["source", "team"], keep="last"
    )
    by_source_team = {
        (r["source"], norm(r["team"])): r for r in rdf.to_dict("records")
    }
    for g in db.get("games", []):
        for source, rating_label in RATING_SOURCES.items():
            home = by_source_team.get((rating_label, norm(g.get("home_team"))))
            away = by_source_team.get((rating_label, norm(g.get("away_team"))))
            hv = home.get("rating") if home else None
            av = away.get("rating") if away else None
            ok = pd.notna(hv) and pd.notna(av)
            audit.append({"source":source,"date":g.get("date"),"away":g.get("away_team"),
                          "home":g.get("home_team"),"matched":bool(ok),"game_id":g.get("game_id")})
            if not ok:
                continue
            hfa = 0.0 if bool(g.get("neutral_site")) else NON_NEUTRAL_HFA
            provenance = {
                "pulled_at": max(str(home.get("pulled_at") or ""), str(away.get("pulled_at") or "")),
            }
            source_url = home.get("source_url") or away.get("source_url") or ""
            explicit_total = explicit_spplus_total(g) if source == "SP+" else ""
            total_note = " Explicit SP+ offense/defense baseline total." if source == "SP+" and explicit_total is not None else ""
            rows.append(add_common(provenance, source, g, float(hv)-float(av)+hfa, explicit_total,
                                   source_url=source_url,
                                   notes=f"{source} team-rating projection: home - away + {hfa:g} HFA.{total_note}"))
    return rows, audit

def load_massey(idx):
    rows, audit = [], []

    if not MASSEY.exists():
        return rows, [{"source":"Massey Games","status":"missing","rows":0}]

    def team_key(x):
        return massey_match_key(x)

    canonical_idx = {}
    for sg in idx.values():
        key = (
            str(sg.get("date")),
            team_key(sg.get("away_team")),
            team_key(sg.get("home_team"))
        )
        canonical_idx[key] = sg

    for _, r in pd.read_csv(MASSEY).iterrows():
        source_date = str(r.get("game_date"))
        source_away = team_key(r.get("away_team"))
        source_home = team_key(r.get("home_team"))

        key = (source_date, source_away, source_home)
        g = canonical_idx.get(key)
        match_method = "exact" if g else None
        reversed_orientation = False

        if not g:
            # Same teams, same orientation, within one day.
            for sg in idx.values():
                if (
                    team_key(sg.get("away_team")) == source_away
                    and team_key(sg.get("home_team")) == source_home
                ):
                    try:
                        day_delta = abs(
                            (
                                pd.to_datetime(sg.get("date")) -
                                pd.to_datetime(r.get("game_date"))
                            ).days
                        )
                    except Exception:
                        day_delta = 999
                    if day_delta <= 1:
                        g = sg
                        match_method = "date_tolerance"
                        break

        if not g:
            # Massey can reverse orientation for neutral-site games.
            # Accept only exact-date reversals when canonical schedule
            # explicitly marks the matchup neutral.
            for sg in idx.values():
                if not bool(sg.get("neutral_site")):
                    continue
                if str(sg.get("date")) != source_date:
                    continue
                if (
                    team_key(sg.get("away_team")) == source_home
                    and team_key(sg.get("home_team")) == source_away
                ):
                    g = sg
                    match_method = "neutral_reversed"
                    reversed_orientation = True
                    break

        audit.append({
            "source": "Massey Games",
            "date": r.get("game_date"),
            "away": r.get("away_team"),
            "home": r.get("home_team"),
            "matched": bool(g),
            "game_id": g.get("game_id") if g else "",
            "match_method": match_method or "unmatched",
        })

        if not g:
            continue

        spread_home = r.get("projected_spread_home")
        away_score = r.get("away_projected_points")
        home_score = r.get("home_projected_points")
        home_win_prob = r.get("home_win_prob")

        if reversed_orientation:
            if pd.notna(spread_home):
                spread_home = -float(spread_home)
            away_score, home_score = home_score, away_score
            if pd.notna(r.get("away_win_prob")):
                home_win_prob = r.get("away_win_prob")
            elif pd.notna(home_win_prob):
                home_win_prob = 1.0 - float(home_win_prob)

        rows.append(
            add_common(
                r,
                "Massey Games",
                g,
                spread_home,
                r.get("projected_total"),
                away_score,
                home_score,
                home_win_prob,
                r.get("source_url", "https://masseyratings.com/cf/fbs/games"),
                f"Massey rendered games page projection; match_method={match_method}.",
            )
        )

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
        if r.get("projection_variant") == "home_away_experimental":
            continue
        source_name = "Sagarin Game Total"
        rows.append(add_common(r,source_name,g,"",r.get("projected_total"),
                               source_url=r.get("source_url","https://sagarin.com/sports/cfsend.htm#Predictions_with_Totals_and_Moneylines"),
                               notes="Validated Sagarin game-total observation; no Predictor/Golden Mean/Recent/Strong Recent rating variant."))
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
