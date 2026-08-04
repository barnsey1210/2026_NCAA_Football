#!/usr/bin/env python3
from pathlib import Path
import json, re
import pandas as pd

DB_RE = re.compile(r'<script id="db" type="application/json">(.*?)</script>', re.S)

def norm_team(x):
    v = re.sub(r"[^a-z0-9]+", " ", str(x or "").lower()).strip()
    aliases = {
        "hawai i": "hawaii",
        "hawaii rainbow warriors": "hawaii",
        "stanford cardinal": "stanford",
        "north dakota state bison": "north dakota state",
        "jacksonville state gamecocks": "jacksonville state",
        "sacramento state hornets": "sacramento state",
        "eastern michigan eagles": "eastern michigan",
        "miami hurricanes": "miami fl",
        "miami fl hurricanes": "miami fl",
        "miami florida": "miami fl",
        "miami fl": "miami fl",
        "san jose state spartans": "san jose state",
        "new mexico state aggies": "new mexico state",
        "florida state seminoles": "florida state",
        "north carolina tar heels": "north carolina",
        "tcu horned frogs": "tcu",
        "nc state wolfpack": "nc state",
        "virginia cavaliers": "virginia",
    }
    return aliases.get(v, v)

def date10(x):
    if pd.isna(x):
        return ""
    return str(x)[:10]

html = Path("index.html").read_text(errors="ignore")
db = json.loads(DB_RE.search(html).group(1))

site_games = []
site_key_to_game = {}
for g in db.get("games", []):
    away = g.get("away_team")
    home = g.get("home_team")
    d = date10(g.get("date"))
    gid = g.get("game_id")
    key = (d, norm_team(away), norm_team(home))
    site_games.append({"site_game_id": gid, "date": d, "away_team": away, "home_team": home, "key": key})
    site_key_to_game[key] = gid

raw_files = [
    "data/odds/game_line_history.csv",
    "data/odds/actionnetwork_season_game_lines_2026.csv",
    "data/markets/sgo/sgo_ncaaf_game_odds.csv",
    "data/odds/season_game_lines_2026.csv",
    "data/odds/theodds_season_game_lines_2026.csv",
]

raw_parts = []
for f in raw_files:
    p = Path(f)
    if not p.exists():
        continue
    df = pd.read_csv(p)
    if not {"away_team","home_team"}.issubset(df.columns):
        continue
    if "date" not in df.columns and "game_date" not in df.columns:
        continue

    df = df.copy()
    df["_source_file"] = f
    df["_game_date"] = df["date"].map(date10) if "date" in df.columns else df["game_date"].map(date10)
    df["_away_norm"] = df["away_team"].map(norm_team)
    df["_home_norm"] = df["home_team"].map(norm_team)
    df["_site_gid"] = [
        site_key_to_game.get((d, a, h))
        for d, a, h in zip(df["_game_date"], df["_away_norm"], df["_home_norm"])
    ]
    raw_parts.append(df)

raw = pd.concat(raw_parts, ignore_index=True) if raw_parts else pd.DataFrame()

clean = pd.read_csv("data/history/matchup_line_history_clean.csv")
clean_keys = set(zip(
    clean["snapshot_date"].astype(str),
    clean["game_id"].astype(str)
))

# Raw rows that matched a site game but do not appear in clean history for same snapshot/game.
raw["_snapshot_date"] = raw.get("snapshot_date", pd.Series("", index=raw.index)).astype(str)
raw["_clean_key"] = list(zip(raw["_snapshot_date"], raw["_site_gid"].astype(str)))
raw["_in_clean"] = raw["_clean_key"].isin(clean_keys)

matched_missing = raw[(raw["_site_gid"].notna()) & (~raw["_in_clean"])].copy()
unmatched = raw[raw["_site_gid"].isna()].copy()

summary = []

if len(matched_missing):
    grp = matched_missing.groupby(
        ["_source_file","_game_date","away_team","home_team","_away_norm","_home_norm"],
        dropna=False
    ).agg(
        rows=("away_team","size"),
        snapshots=("_snapshot_date","nunique"),
        first_snapshot=("_snapshot_date","min"),
        last_snapshot=("_snapshot_date","max")
    ).reset_index().sort_values(["snapshots","rows"], ascending=False)
    grp.to_csv("data/audits/line_history_matched_but_missing_clean.csv", index=False)
    summary.append(("matched_but_missing_clean", len(grp)))
else:
    pd.DataFrame().to_csv("data/audits/line_history_matched_but_missing_clean.csv", index=False)
    summary.append(("matched_but_missing_clean", 0))

if len(unmatched):
    grp2 = unmatched.groupby(
        ["_source_file","_game_date","away_team","home_team","_away_norm","_home_norm"],
        dropna=False
    ).agg(
        rows=("away_team","size"),
        snapshots=("_snapshot_date","nunique"),
        first_snapshot=("_snapshot_date","min"),
        last_snapshot=("_snapshot_date","max")
    ).reset_index().sort_values(["snapshots","rows"], ascending=False)
    grp2.to_csv("data/audits/line_history_unmapped_raw_games.csv", index=False)
    summary.append(("unmapped_raw_games", len(grp2)))
else:
    pd.DataFrame().to_csv("data/audits/line_history_unmapped_raw_games.csv", index=False)
    summary.append(("unmapped_raw_games", 0))

print("Raw rows:", len(raw))
print("Raw rows matched to site game:", int(raw["_site_gid"].notna().sum()))
print("Raw rows unmatched:", int(raw["_site_gid"].isna().sum()))
print("Clean rows:", len(clean))
print("Wrote:")
for name, count in summary:
    print(f"  data/audits/line_history_{name if name.startswith('unmapped') else name}.csv rows={count}")

print("\nTop unmatched raw game groups:")
if Path("data/audits/line_history_unmapped_raw_games.csv").exists():
    u = pd.read_csv("data/audits/line_history_unmapped_raw_games.csv")
    if len(u):
        print(u.head(40).to_string(index=False))
    else:
        print("none")

print("\nTop matched-but-missing clean groups:")
m = pd.read_csv("data/audits/line_history_matched_but_missing_clean.csv")
if len(m):
    print(m.head(40).to_string(index=False))
else:
    print("none")
