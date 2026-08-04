#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess, urllib.parse
from pathlib import Path
from datetime import datetime, timezone

BASE="https://api.collegefootballdata.com"

def key_from_env():
    return os.getenv("CFBD_API_KEY") or os.getenv("COLLEGE_FOOTBALL_DATA_API_KEY")

def curl_json(path, params, key):
    query=urllib.parse.urlencode({k:v for k,v in params.items() if v is not None})
    url=BASE+path+("?" + query if query else "")
    print("GET",url,flush=True)
    cmd=[
        "curl","-sS","--fail","--show-error",
        "--connect-timeout","10","--max-time","25",
        "-H",f"Authorization: Bearer {key}",
        "-H","Accept: application/json",
        url
    ]
    proc=subprocess.run(cmd,capture_output=True,text=True)
    if proc.returncode!=0:
        raise RuntimeError(proc.stderr.strip() or f"curl failed with code {proc.returncode}")
    print("  bytes:",len(proc.stdout),flush=True)
    return json.loads(proc.stdout)

def game_id(row):
    return row.get("id") or row.get("gameId") or row.get("game_id")

def completed(row):
    hp=row.get("homePoints") if "homePoints" in row else row.get("home_points")
    ap=row.get("awayPoints") if "awayPoints" in row else row.get("away_points")
    return hp is not None and ap is not None

def flatten_lines(payload):
    if isinstance(payload,dict):
        payload=payload.get("lines") or payload.get("data") or [payload]
    out=[]
    for item in payload or []:
        if not isinstance(item,dict): continue
        nested=item.get("lines")
        if isinstance(nested,list):
            for line in nested:
                if isinstance(line,dict):
                    merged=dict(line)
                    merged.setdefault("game_id",item.get("id") or item.get("gameId"))
                    merged.setdefault("homeTeam",item.get("homeTeam"))
                    merged.setdefault("awayTeam",item.get("awayTeam"))
                    out.append(merged)
        else:
            out.append(item)
    return out

def choose_line(lines, gid):
    candidates=flatten_lines(lines)
    exact=[x for x in candidates if str(x.get("game_id") or x.get("id") or "")==str(gid)]
    pool=exact or candidates
    for line in pool:
        spread=line.get("spread")
        total=line.get("overUnder") if "overUnder" in line else line.get("over_under")
        if spread is not None or total is not None:
            return line
    return {}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--year",type=int,default=2025)
    ap.add_argument("--week",type=int,default=0)
    ap.add_argument("--game-id")
    ap.add_argument("--season-type",default="regular")
    ap.add_argument("--output-root",default="data/replay/cfbd_shadow")
    args=ap.parse_args()

    key=key_from_env()
    if not key:
        raise SystemExit("Set CFBD_API_KEY or COLLEGE_FOOTBALL_DATA_API_KEY first.")

    root=Path.home()/"NCAAF_AUTO"
    out=root/args.output_root/f"{args.year}_week_{args.week}"
    out.mkdir(parents=True,exist_ok=True)

    games=curl_json("/games",{
        "year":args.year,"week":args.week,"seasonType":args.season_type
    },key)
    if not isinstance(games,list):
        raise SystemExit("Unexpected /games response")

    candidates=[g for g in games if completed(g)]
    if args.game_id:
        candidates=[g for g in candidates if str(game_id(g))==str(args.game_id)]
    if not candidates:
        raise SystemExit("No completed games matched.")

    print("Pulling historical lines once for the whole week...",flush=True)
    lines=curl_json("/lines",{
        "year":args.year,"week":args.week,"seasonType":args.season_type
    },key)

    print("Pulling historical plays once for the whole week...",flush=True)
    plays=curl_json("/plays",{
        "year":args.year,"week":args.week,"seasonType":args.season_type
    },key)
    plays_list=plays if isinstance(plays,list) else plays.get("plays",[])

    selected=None
    selected_line=None
    selected_plays=None
    attempts=[]
    for game in candidates:
        gid=game_id(game)
        line=choose_line(lines,gid)
        gp=[p for p in plays_list if str(p.get("gameId") or p.get("game_id") or "")==str(gid)]
        attempts.append({"game_id":gid,"plays":len(gp),"has_line":bool(line)})
        print("candidate",gid,"plays",len(gp),"line",bool(line),flush=True)
        if gp and line:
            selected,selected_line,selected_plays=game,line,gp
            break

    if selected is None:
        raise SystemExit("No game had both line and PBP.\n"+json.dumps(attempts,indent=2))

    gid=str(game_id(selected))
    files={
        "game":out/f"{gid}_game.json",
        "line":out/f"{gid}_line.json",
        "plays":out/f"{gid}_plays.json",
    }
    files["game"].write_text(json.dumps(selected,indent=2),encoding="utf-8")
    files["line"].write_text(json.dumps(selected_line,indent=2),encoding="utf-8")
    files["plays"].write_text(json.dumps(selected_plays,indent=2),encoding="utf-8")

    manifest={
        "schema_version":"cfbd-shadow-replay-v2",
        "captured_at":datetime.now(timezone.utc).isoformat(),
        "mode":"historical_replay_fixture",
        "production_writes":False,
        "year":args.year,
        "week":args.week,
        "game_id":gid,
        "away_team":selected.get("awayTeam") or selected.get("away_team"),
        "home_team":selected.get("homeTeam") or selected.get("home_team"),
        "away_points":selected.get("awayPoints") if "awayPoints" in selected else selected.get("away_points"),
        "home_points":selected.get("homePoints") if "homePoints" in selected else selected.get("home_points"),
        "closing_spread":selected_line.get("spread"),
        "closing_total":selected_line.get("overUnder") if "overUnder" in selected_line else selected_line.get("over_under"),
        "line_provider":selected_line.get("provider"),
        "plays_count":len(selected_plays),
        "files":{k:str(v.relative_to(root)) for k,v in files.items()},
        "attempts":attempts,
    }
    manifest_path=out/f"{gid}_manifest.json"
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding="utf-8")

    print("\nCFBD HISTORICAL REPLAY CAPTURED")
    print(json.dumps(manifest,indent=2))
    print("manifest:",manifest_path)

if __name__=="__main__":
    main()
