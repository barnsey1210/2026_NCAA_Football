#!/usr/bin/env python3
from pathlib import Path
import csv, json, math
from datetime import datetime, timezone

ROOT = Path.home() / "NCAAF_AUTO"

def num(v):
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def norm_id(v):
    s=str(v or "").strip()
    if s.endswith(".0"):
        s=s[:-2]
    return s

def latest_manifest():
    items=sorted(ROOT.glob("data/replay/cfbd_shadow/**/*_manifest.json"),
                 key=lambda p:p.stat().st_mtime, reverse=True)
    if not items:
        raise SystemExit("No replay manifest found.")
    return items[0]

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_rows(path):
    with path.open(newline="",encoding="utf-8",errors="ignore") as f:
        return list(csv.DictReader(f))

def pbp_metrics(plays, team):
    rows=[p for p in plays if p.get("offense")==team]
    scr=[]
    for p in rows:
        typ=str(p.get("playType") or "").lower()
        if any(x in typ for x in ("kickoff","punt","timeout","penalty","end of")):
            continue
        scr.append(p)
    gains=[num(p.get("yardsGained")) for p in scr]
    gains=[x for x in gains if x is not None]
    ppas=[num(p.get("ppa")) for p in scr]
    ppas=[x for x in ppas if x is not None]
    success=[]
    explosive=0
    for p in scr:
        gain=num(p.get("yardsGained")); down=num(p.get("down")); dist=num(p.get("distance"))
        if gain is None: continue
        typ=str(p.get("playType") or "").lower()
        if ("pass" in typ and gain>=15) or ("rush" in typ and gain>=10):
            explosive+=1
        if down is not None and dist not in (None,0):
            threshold=0.5*dist if down==1 else 0.7*dist if down==2 else dist
            success.append(gain>=threshold)
    return {
        "offensive_plays":len(scr),
        "yards_per_play":round(sum(gains)/len(gains),3) if gains else None,
        "success_rate":round(sum(success)/len(success),4) if success else None,
        "explosive_plays":explosive,
        "mean_ppa":round(sum(ppas)/len(ppas),4) if ppas else None,
        "scoring_plays":sum(bool(p.get("scoring")) for p in rows),
    }

manifest_path=latest_manifest()
manifest=load_json(manifest_path)
plays=load_json(ROOT/manifest["files"]["plays"])
gid=norm_id(manifest["game_id"])
away=manifest["away_team"]; home=manifest["home_team"]

spread_file=ROOT/"data/research/postgame_pbp_market_rating_update_2021_2024/holdout_2025_predictions.csv"
total_file=ROOT/"data/research/postgame_total_market_update_baseline_aware_2021_2025/holdout_2025_predictions_baseline_aware.csv"

spread_rows=[
    r for r in read_rows(spread_file)
    if norm_id(r.get("game_id"))==gid and r.get("team") in {away,home}
]

total_rows=[
    r for r in read_rows(total_file)
    if norm_id(r.get("home_prev_game_id"))==gid
    or norm_id(r.get("away_prev_game_id"))==gid
]

home_score=float(manifest["home_points"])
away_score=float(manifest["away_points"])
home_close=float(manifest["closing_spread"])
closing_total=float(manifest["closing_total"])

spread_updates=[]
for team,opp,margin,team_close in (
    (home,away,home_score-away_score,home_close),
    (away,home,away_score-home_score,-home_close),
):
    exact=next((r for r in spread_rows if r.get("team")==team),None)
    spread_updates.append({
        "team":team,
        "opponent":opp,
        "team_margin":margin,
        "team_closing_spread":team_close,
        "team_ats_margin":margin+team_close,
        "abs_team_closing_spread":abs(team_close),
        "predicted_next_market_innovation":num(exact.get("score_prediction")) if exact else None,
        "actual_next_market_innovation_2025":num(exact.get("target_next_market_innovation")) if exact else None,
        "score_plus_pbp_prediction":num(exact.get("score_pbp_prediction")) if exact else None,
        "evidence_file":str(spread_file.relative_to(ROOT)) if exact else None,
    })

total_predictions=[]
for r in total_rows:
    total_predictions.append({
        "next_game_id":r.get("game_id"),
        "next_home_team":r.get("home_team"),
        "next_away_team":r.get("away_team"),
        "home_prev_game_id":r.get("home_prev_game_id"),
        "away_prev_game_id":r.get("away_prev_game_id"),
        "predicted_next_total_innovation":num(r.get("score_plus_pbp_prediction")),
        "score_only_prediction":num(r.get("score_only_prediction")),
        "actual_next_total_innovation_2025":num(r.get("target_total_innovation")),
        "evidence_file":str(total_file.relative_to(ROOT)),
    })

warnings=[]
if len(spread_updates)!=2 or any(x["predicted_next_market_innovation"] is None for x in spread_updates):
    warnings.append("Exact spread replay rows incomplete.")
if not total_predictions:
    candidate_total_rows=[
        {
            "game_id":norm_id(r.get("game_id")),
            "week":r.get("week"),
            "home_team":r.get("home_team"),
            "away_team":r.get("away_team"),
            "home_prev_game_id":norm_id(r.get("home_prev_game_id")),
            "away_prev_game_id":norm_id(r.get("away_prev_game_id")),
        }
        for r in read_rows(total_file)
        if str(r.get("season")) in {"2025","2025.0"}
        and (
            r.get("home_team") in {away,home}
            or r.get("away_team") in {away,home}
        )
    ][:20]
    warnings.append("No exact total next-game rows linked to the replay game.")
else:
    candidate_total_rows=[]

payload={
    "schema_version":"postgame-shadow-replay-v2",
    "built_at":datetime.now(timezone.utc).isoformat(),
    "mode":"historical_replay_shadow_only",
    "applied_to_ratings":False,
    "applied_to_projections":False,
    "source_manifest":str(manifest_path.relative_to(ROOT)),
    "game":{
        "game_id":gid,
        "season":manifest["year"],
        "week":manifest["week"],
        "away_team":away,
        "home_team":home,
        "away_points":away_score,
        "home_points":home_score,
        "closing_spread_home":home_close,
        "closing_total":closing_total,
        "line_provider":manifest.get("line_provider"),
        "plays_count":manifest.get("plays_count"),
    },
    "spread_updates":spread_updates,
    "total_update":{
        "closing_total":closing_total,
        "actual_total":away_score+home_score,
        "completed_game_total_residual":away_score+home_score-closing_total,
        "next_game_predictions":total_predictions,
        "pbp_metrics":{
            away:pbp_metrics(plays,away),
            home:pbp_metrics(plays,home),
        },
    },
    "matched_research_rows":len(spread_rows)+len(total_rows),
    "total_linkage_candidates":candidate_total_rows,
    "warnings":warnings,
    "status":"complete" if not warnings else "complete_with_warnings",
}

out=ROOT/"data/site/postgame_shadow_replay.json"
out.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
print(json.dumps(payload,indent=2))
print("wrote:",out)
