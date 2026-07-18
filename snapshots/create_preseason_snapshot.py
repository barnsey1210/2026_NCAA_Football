#!/usr/bin/env python3
from pathlib import Path
import json, re
import pandas as pd
from datetime import datetime

INDEX = Path("index.html")
OUT_DIR = Path("data/snapshots/preseason")
OUT_DIR.mkdir(parents=True, exist_ok=True)

DB_RE = re.compile(r'<script id="db" type="application/json">(.*?)</script>', re.S)

def pct(v):
    try:
        return float(v)
    except Exception:
        return None

def main():
    html = INDEX.read_text(errors="ignore")
    m = DB_RE.search(html)
    if not m:
        raise SystemExit("DB not found in index.html")

    db = json.loads(m.group(1))
    created_at = datetime.now().isoformat(timespec="seconds")

    snapshot = {
        "meta": {
            "snapshot_type": "preseason",
            "created_at": created_at,
            "source_index": str(INDEX),
            "teams": len(db.get("teams", [])),
            "games": len(db.get("games", [])),
            "conferences": len(db.get("conferences", [])),
        },
        "teams": db.get("teams", []),
        "games": db.get("games", []),
        "conferences": db.get("conferences", []),
    }

    (OUT_DIR / "preseason_db.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    teams = []
    for t in db.get("teams", []):
        teams.append({
            "team": t.get("team"),
            "conference": t.get("conference"),
            "rank": t.get("rank"),
            "combo": t.get("combo"),
            "avg_total_wins": t.get("avg_total_wins"),
            "avg_conference_wins": t.get("avg_conference_wins"),
            "conference_title_pct": t.get("conference_title_pct"),
            "make_title_game_pct": t.get("make_title_game_pct"),
            "bowl_eligibility_pct": t.get("bowl_eligibility_pct"),
            "win_distribution": json.dumps(t.get("win_distribution", {}), separators=(",", ":")),
        })
    pd.DataFrame(teams).to_csv(OUT_DIR / "team_preseason_snapshot.csv", index=False)

    games = []
    for g in db.get("games", []):
        games.append({
            "game_id": g.get("game_id"),
            "date": g.get("date"),
            "week": g.get("week"),
            "away_team": g.get("away_team"),
            "home_team": g.get("home_team"),
            "projected_margin_home": g.get("projected_margin_home"),
            "projected_total": g.get("projected_total"),
            "win_prob_home": g.get("win_prob_home"),
            "market_spread_home": g.get("market_spread_home"),
            "market_total": g.get("market_total"),
        })
    pd.DataFrame(games).to_csv(OUT_DIR / "game_preseason_snapshot.csv", index=False)

    conf_rows = []
    for c in db.get("conferences", []):
        for t in c.get("teams", []):
            conf_rows.append({
                "conference": c.get("conference"),
                "team": t.get("team"),
                "conference_title_pct": t.get("conference_title_pct"),
                "make_title_game_pct": t.get("make_title_game_pct"),
                "avg_conference_wins": t.get("avg_conference_wins"),
                "avg_total_wins": t.get("avg_total_wins"),
            })
    pd.DataFrame(conf_rows).to_csv(OUT_DIR / "conference_preseason_snapshot.csv", index=False)

    print("created preseason snapshot")
    print("wrote", OUT_DIR / "preseason_db.json")
    print("wrote", OUT_DIR / "team_preseason_snapshot.csv")
    print("wrote", OUT_DIR / "game_preseason_snapshot.csv")
    print("wrote", OUT_DIR / "conference_preseason_snapshot.csv")

if __name__ == "__main__":
    main()
