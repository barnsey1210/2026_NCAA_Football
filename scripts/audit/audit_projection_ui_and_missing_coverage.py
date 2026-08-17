#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd
import subprocess

ROOT = Path("/Users/jameslindesmith/NCAAF_MAIN_REPO")

def section(title):
    print("\n" + "=" * 110)
    print(title)
    print("=" * 110)

section("MISSING / PARTIAL PROJECTION COVERAGE")
db = json.loads((ROOT / "data/snapshots/preseason/preseason_db.json").read_text())
games = db.get("games", [])

rows = []
for g in games:
    rows.append({
        "game_id": g.get("game_id"),
        "date": g.get("date"),
        "week": g.get("week"),
        "away": g.get("away_team"),
        "home": g.get("home_team"),
        "spread": g.get("projected_margin_home"),
        "total": g.get("projected_total"),
        "spread_cov": g.get("projection_spread_coverage"),
        "total_cov": g.get("projection_total_coverage"),
        "spread_sources": g.get("projection_spread_source_label"),
        "total_sources": g.get("projection_total_source_label"),
    })

df = pd.DataFrame(rows)

print("\n-- games with no usable spread or total --")
miss = df[df["spread"].isna() | df["total"].isna()]
print(miss.to_string(index=False, max_rows=200))

print("\n-- 1/4 spread coverage --")
one = df[df["spread_cov"] == "1/4"]
print(one.to_string(index=False, max_rows=200))

print("\n-- coverage counts --")
print(df.groupby(["spread_cov", "total_cov"], dropna=False).size().to_string())

section("MATCHUPS VIEW SHAPE")
mv = ROOT / "data/site/matchups_view.json"
if mv.exists():
    data = json.loads(mv.read_text())
    print("top-level type:", type(data).__name__)
    if isinstance(data, dict):
        print("top-level keys:", sorted(data.keys())[:80])
        recs = data.get("games") or data.get("rows") or data.get("matchups") or []
        if recs:
            print("\nfirst matchup keys:")
            print(sorted(recs[0].keys()))
            print("\nfirst matchup model:")
            print(json.dumps(recs[0].get("model"), indent=2))
            print("\nfirst matchup game:")
            print(json.dumps(recs[0].get("game"), indent=2))
else:
    print("MISSING:", mv)

section("CURRENT UI OWNER REFERENCES")
patterns = [
    "Game Projection Consensus",
    "projected_margin_home",
    "projection_spread_coverage",
    "projection_total_coverage",
    "model.home_spread",
    "model.total",
    "Site Composite",
    "Brad Powers",
    "Donchess",
]
for pat in patterns:
    print(f"\n--- {pat} ---")
    r = subprocess.run(
        ["grep","-RIn","--exclude-dir=.git","--exclude=*.bak",pat,
         "scripts/site","index.html","openers.html","matchups.html","ratings.html"],
        cwd=ROOT, text=True, capture_output=True
    )
    print((r.stdout or "(none)")[:20000])

section("RATINGS SOURCE SAMPLE")
ratings = ROOT / "data/ratings/ratings_latest.csv"
if ratings.exists():
    rdf = pd.read_csv(ratings)
    print(rdf[rdf["source"].isin(["SP+","FPI","TeamRankings","Brad Powers","Donchess Overall","Sagarin Predictor"])]
          [["snapshot_date","source","team","rank","rating","source_url","source_updated_at"]]
          .head(40).to_string(index=False))

print("\nRead-only audit complete. No files changed.")
