from pathlib import Path
import re, json, subprocess, sys, math
import pandas as pd

ROOT = Path(".")
ACTIVE_INDEX = ROOT / "index.html"
SPONLY_INDEX = ROOT / "index_spplus_only_sim_compare.html"
MASTER = ROOT / "data/ratings/ratings_master_latest.csv"
OUTDIR = ROOT / "data/audits"
OUTDIR.mkdir(parents=True, exist_ok=True)

def fnum(x, default=None):
    try:
        if x is None or pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default

def win_prob_from_margin(margin):
    # Same style as a logistic spread -> win-prob conversion.
    return 1.0 / (1.0 + math.exp(-margin / 6.5))

def load_db(path):
    s = path.read_text(errors="ignore")
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', s, flags=re.S)
    if not m:
        raise SystemExit(f"DB JSON not found in {path}")
    return s, json.loads(m.group(1)), m

def write_db(path, html, db, m):
    new = json.dumps(db, separators=(",", ":"))
    path.write_text(html[:m.start(1)] + new + html[m.end(1):], encoding="utf-8")

def snapshot(path, out):
    _, db, _ = load_db(path)
    teams = pd.DataFrame(db["teams"])
    cols = [
        "team","conference","rank","combo","rating_spplus","rating_fpi","rating_teamrankings",
        "avg_total_wins","avg_conference_wins",
        "make_title_game_pct","conference_title_pct",
        "lose_title_game_pct","bowl_eligibility_pct"
    ]
    cols = [c for c in cols if c in teams.columns]
    teams[cols].to_csv(out, index=False)
    return teams[cols].copy()

def recalc_game_projections_from_team_combo(db):
    teams = {t.get("team"): t for t in db.get("teams", [])}
    changed = 0

    for g in db.get("games", []):
        away = g.get("away_team")
        home = g.get("home_team")
        at = teams.get(away)
        ht = teams.get(home)
        if not at or not ht:
            continue

        away_rating = fnum(at.get("combo"))
        home_rating = fnum(ht.get("combo"))
        if away_rating is None or home_rating is None:
            continue

        neutral = bool(g.get("neutral_site") or g.get("neutral") or g.get("is_neutral"))
        hfa = 0.0 if neutral else fnum(ht.get("hfa"), 0.0)

        margin_home = home_rating - away_rating + hfa
        wp_home = win_prob_from_margin(margin_home)

        # Existing site fields use home margin in most places.
        for k in [
            "projected_margin_home",
            "projection_spread_home",
            "site_spread_home",
            "blend_spread_home",
        ]:
            if k in g:
                g[k] = round(margin_home, 4)

        # Add/overwrite canonical fields even if absent.
        g["projected_margin_home"] = round(margin_home, 4)

        # IMPORTANT: rerun_conference_sims_2026.py reads win_prob_home first.
        # home_win_prob/away_win_prob are helper/display fields only.
        g["win_prob_home"] = round(wp_home, 12)
        g["home_win_prob"] = round(wp_home, 6)
        g["away_win_prob"] = round(1.0 - wp_home, 6)

        # Human-readable helper if present/used.
        fav = home if margin_home >= 0 else away
        g["projection_spread_text"] = f"{fav} -{abs(margin_home):.1f}"

        changed += 1

    return changed

# 1) active snapshot from current freshly rerun active-blend index.html
active = snapshot(ACTIVE_INDEX, OUTDIR / "active_blend_rerun_sim_snapshot.csv")

# 2) make SP+ only temp index by changing team combo/rank to SP+ and recalculating game projections
html, db, m = load_db(ACTIVE_INDEX)
master = pd.read_csv(MASTER)
sp = master.set_index("team")["spplus"].to_dict()

for t in db["teams"]:
    team = t.get("team")
    if team in sp and pd.notna(sp[team]):
        t["combo"] = round(float(sp[team]), 4)

ranked = sorted(
    [t for t in db["teams"] if t.get("combo") is not None],
    key=lambda x: float(x.get("combo")),
    reverse=True
)
for i, t in enumerate(ranked, 1):
    t["rank"] = i

game_changes = recalc_game_projections_from_team_combo(db)
print("SP+ temp game projections recalculated:", game_changes)

write_db(SPONLY_INDEX, html, db, m)

# 3) rerun conference/season sims on temp SP+ only file
cmd = [sys.executable, "rerun_conference_sims_2026.py", "--index", str(SPONLY_INDEX), "--sims", "10000", "--seed", "20260712"]
print("running:", " ".join(cmd))
subprocess.run(cmd, check=True)

# 4) snapshot SP+ only
sponly = snapshot(SPONLY_INDEX, OUTDIR / "spplus_only_rerun_sim_snapshot.csv")

# 5) compare
cmp = active.merge(
    sponly,
    on=["team","conference"],
    suffixes=("_active","_spplus_only")
)

for c in ["combo","avg_total_wins","avg_conference_wins","make_title_game_pct","conference_title_pct","lose_title_game_pct","bowl_eligibility_pct"]:
    a = f"{c}_active"
    b = f"{c}_spplus_only"
    if a in cmp.columns and b in cmp.columns:
        cmp[f"{c}_delta_active_minus_spplus"] = pd.to_numeric(cmp[a], errors="coerce") - pd.to_numeric(cmp[b], errors="coerce")

cmp.to_csv(OUTDIR / "active_blend_vs_spplus_only_rerun_sim_impact.csv", index=False)

cols = [
    "team","conference",
    "combo_active","combo_spplus_only","combo_delta_active_minus_spplus",
    "avg_total_wins_active","avg_total_wins_spplus_only","avg_total_wins_delta_active_minus_spplus",
    "conference_title_pct_active","conference_title_pct_spplus_only","conference_title_pct_delta_active_minus_spplus"
]

print("\nwrote:")
print(OUTDIR / "active_blend_rerun_sim_snapshot.csv")
print(OUTDIR / "spplus_only_rerun_sim_snapshot.csv")
print(OUTDIR / "active_blend_vs_spplus_only_rerun_sim_impact.csv")

print("\nTop avg win changes from adding FPI/TeamRankings:")
print(cmp.sort_values("avg_total_wins_delta_active_minus_spplus", key=lambda x: x.abs(), ascending=False)[cols].head(35).to_string(index=False))

print("\nTop conference title changes from adding FPI/TeamRankings:")
print(cmp.sort_values("conference_title_pct_delta_active_minus_spplus", key=lambda x: x.abs(), ascending=False)[cols].head(35).to_string(index=False))
