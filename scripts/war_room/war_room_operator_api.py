#!/usr/bin/env python3
"""Loopback-only origin for authenticated War Room operational actions.

Cloudflare Access and Tunnel provide the public authentication boundary. This
origin accepts only fixed actions and never accepts commands, script paths, or
provider credentials from a request.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import hashlib
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

ROOT = Path(__file__).resolve().parents[2]
LATEST = ROOT / "data/control/war_room_services/latest.json"
TASKS = ROOT / "data/control/war_room_services/tasks"
REQUEST_LOG = ROOT / "data/control/war_room_services/requests.jsonl"
HEALTH = ROOT / "data/site/war_room_health.json"
MATRIX = ROOT / "data/site/war_room_market_matrix.json"
ACTIVITY = ROOT / "data/site/war_room_activity.json"
GAME_ACTIVITY_INDEX = ROOT / "data/war_room/history/war_room_game_activity_index.json"
SCHEDULE = ROOT / "data/site/schedule_live_enrichment.json"
SCOREBOARD = ROOT / "data/canonical/cfbd_scoreboard_live_2026.json"
FINAL_WATCHER_LATEST = ROOT / "data/control/cfbd_final_watcher/latest.json"
PUBLIC_ORIGIN = os.environ.get(
    "WAR_ROOM_PUBLIC_ORIGIN", "https://barnsey1210.github.io"
).rstrip("/")
CONTROL_ORIGIN = os.environ.get(
    "WAR_ROOM_CONTROL_ORIGIN", "https://control.barnseywr.com"
).rstrip("/")
ACTION_PATHS = {
    "/war-room/market",
    "/war-room/ratings",
    "/war-room/postgame",
}

app = FastAPI(title="NCAAF War Room Control Origin", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[PUBLIC_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Cf-Access-Jwt-Assertion"],
    max_age=600,
)


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def append_request_log(value: dict[str, Any]) -> None:
    REQUEST_LOG.parent.mkdir(parents=True, exist_ok=True)
    with REQUEST_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True) + "\n")


@app.middleware("http")
async def request_audit(request: Request, call_next):
    request.state.correlation_id = uuid.uuid4().hex
    request.state.operator = None
    request.state.task_id = None
    response_status = 500
    try:
        response = await call_next(request)
        response_status = response.status_code
        return response
    finally:
        append_request_log(
            {
                "timestamp": utc_now(),
                "correlation_id": request.state.correlation_id,
                "method": request.method,
                "path": request.url.path,
                "origin": request.headers.get("origin"),
                "authenticated_operator": request.state.operator,
                "response_status": response_status,
                "task_id": request.state.task_id,
            }
        )


def require_access(
    request: Request,
    origin: Optional[str] = Header(default=None),
    cf_access_jwt_assertion: Optional[str] = Header(default=None),
    cf_access_authenticated_user_email: Optional[str] = Header(default=None),
) -> str:
    if request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(status_code=403, detail="origin is loopback-only")
    if not cf_access_jwt_assertion or not cf_access_authenticated_user_email:
        raise HTTPException(status_code=401, detail="Cloudflare Access authentication required")
    normalized_origin = origin.rstrip("/") if origin else None
    if request.method == "POST" and request.url.path in ACTION_PATHS:
        if normalized_origin != CONTROL_ORIGIN:
            raise HTTPException(status_code=403, detail="browser origin is not authorized")
    elif normalized_origin and normalized_origin not in {PUBLIC_ORIGIN, CONTROL_ORIGIN}:
        raise HTTPException(status_code=403, detail="browser origin is not authorized")
    request.state.operator = cf_access_authenticated_user_email
    return cf_access_authenticated_user_email


def require_public_read_origin(
    request: Request,
    origin: Optional[str] = Header(default=None),
) -> None:
    if request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(status_code=403, detail="origin is loopback-only")
    if origin and origin.rstrip("/") != PUBLIC_ORIGIN:
        raise HTTPException(status_code=403, detail="browser origin is not authorized")


def public_artifact(path: Path, schema: str) -> dict[str, Any]:
    payload = load_json(path, None)
    if not isinstance(payload, dict) or payload.get("schema_version") != schema:
        raise HTTPException(status_code=503, detail="live artifact unavailable")
    return payload


def live_response(payload: dict[str, Any]) -> JSONResponse:
    return JSONResponse(payload, headers={"Cache-Control": "no-store"})


def json_safe(value: Any) -> Any:
    """Normalize non-finite legacy artifact values at the public JSON boundary."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def request_action(action: str, requester: str, request: Request) -> JSONResponse:
    bucket = int(time.time() // 60)
    identity_seed = f"{action}|cloudflare-access|{requester.lower()}|{bucket}".encode()
    identity = f"{action}-{hashlib.sha256(identity_seed).hexdigest()[:12]}"
    task_path = TASKS / f"{identity}.json"
    prior = load_json(task_path, {})
    known_status = prior.get("status") in {
        "REQUESTED",
        "RUNNING",
        "COMPLETED",
        "COMPLETED_WITH_WARNINGS",
        "FAILED",
        "BLOCKED_BY_OVERLAP",
        "DEFERRED_BY_DAILY_BACKBONE",
    }
    if not known_status:
        prior = {
            "schema_version": 1,
            "task_id": identity,
            "action": action,
            "trigger": "cloudflare-access",
            "requester": requester[:120],
            "requested_at": utc_now(),
            "status": "REQUESTED",
            "correlation_id": request.state.correlation_id,
            "command_owner": "scripts/war_room/run_fast_market_publication.py"
            if action == "market"
            else "scripts/control/run_data_refresh.py",
        }
        atomic_json(task_path, prior)
        atomic_json(LATEST, prior)
    process = None
    if not known_status:
        command = [
            sys.executable,
            "scripts/control/run_war_room_service.py",
            action,
            "--task-id",
            identity,
            "--trigger",
            "cloudflare-access",
            "--requester",
            requester,
        ]
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=os.environ.copy(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    request.state.task_id = identity
    return JSONResponse(
        status_code=202,
        content={
            "ok": True,
            "status": prior.get("status", "REQUESTED"),
            "action": action,
            "task_id": identity,
            "correlation_id": request.state.correlation_id,
            "dispatcher_pid": process.pid if process else None,
        },
    )


@app.get("/war-room/status")
def status(operator: str = Depends(require_access)):
    return {"ok": True, "authenticated": True, "operator": operator, "latest": load_json(LATEST, {"status": "NEVER_RUN"})}


@app.get("/war-room/live/version")
def live_version(_: None = Depends(require_public_read_origin)):
    health = public_artifact(HEALTH, "war-room-health-v1")
    matrix = public_artifact(MATRIX, "war-room-market-matrix-v1")
    activity = public_artifact(ACTIVITY, "war-room-activity-v1")
    health_refresh = health.get("fast_market_refresh") or {}
    matrix_refresh = matrix.get("fast_market_refresh") or {}
    refresh_id = health_refresh.get("refresh_id")
    if not refresh_id or refresh_id != matrix_refresh.get("refresh_id"):
        raise HTTPException(status_code=503, detail="live artifact versions do not match")
    return live_response({
        "schema_version": "war-room-live-version-v1",
        "refresh_id": refresh_id,
        "last_fast_pull_at": health_refresh.get("last_fast_pull_at"),
        "health_built_at": health.get("built_at"),
        "matrix_built_at": matrix.get("built_at"),
        "activity_built_at": activity.get("built_at"),
        "activity_event_count": activity.get("event_count"),
        "scoreboard_pulled_at": load_json(SCOREBOARD, {}).get("pulled_at"),
        "schedule_built_at": load_json(SCHEDULE, {}).get("built_at"),
    })


@app.get("/war-room/live/health")
def live_health(_: None = Depends(require_public_read_origin)):
    return live_response(public_artifact(HEALTH, "war-room-health-v1"))


@app.get("/war-room/live/market-matrix")
def live_market_matrix(_: None = Depends(require_public_read_origin)):
    matrix = public_artifact(MATRIX, "war-room-market-matrix-v1")
    schedule = public_artifact(SCHEDULE, "schedule-live-enrichment-v2")

    live_by_game = {
        str(game.get("game_id")): game
        for game in schedule.get("games", [])
        if isinstance(game, dict) and game.get("game_id") is not None
    }

    live_fields = (
        "live_status",
        "live_home_score",
        "live_away_score",
        "live_period",
        "live_clock",
        "scoreboard_pulled_at",
        "live_score_source",
    )

    for game in matrix.get("games", []):
        if not isinstance(game, dict):
            continue
        live = live_by_game.get(str(game.get("game_id")))
        if not live:
            continue
        for field in live_fields:
            if field in live:
                game[field] = live.get(field)

    return live_response(json_safe(matrix))


@app.get("/war-room/live/activity")
def live_activity(
    game_id: Optional[str] = Query(default=None, min_length=1, max_length=160),
    _: None = Depends(require_public_read_origin),
):
    if game_id is None:
        return live_response(public_artifact(ACTIVITY, "war-room-activity-v1"))
    index = public_artifact(GAME_ACTIVITY_INDEX, "war-room-game-activity-index-v1")
    game = (index.get("games") or {}).get(game_id)
    if not isinstance(game, dict):
        raise HTTPException(status_code=404, detail="game activity not found")
    return live_response({
        "schema_version": "war-room-game-activity-v1",
        "built_at": index.get("built_at"),
        "latest_refresh_id": index.get("latest_refresh_id"),
        **game,
    })


@app.get("/war-room/live/schedule")
def live_schedule(_: None = Depends(require_public_read_origin)):
    schedule = public_artifact(SCHEDULE, "schedule-live-enrichment-v2")
    watcher = load_json(FINAL_WATCHER_LATEST, {})
    scoreboard = load_json(SCOREBOARD, {})
    window = watcher.get("window") if isinstance(watcher.get("window"), dict) else {}
    window_policy = window.get("window_policy")
    schedule["live_data_status"] = {
        "watcher_status": watcher.get("status"),
        "window_policy": window_policy,
        "active_game_window": window_policy in {
            "EXACT_WINDOW",
            "MIXED_FALLBACK_WINDOW",
            "BOUNDED_GAME_DAY_FALLBACK",
        },
        "scoreboard_pulled_at": scoreboard.get("pulled_at"),
        "schedule_built_at": schedule.get("built_at"),
    }
    return live_response(json_safe(schedule))


@app.get("/war-room/bootstrap", response_class=HTMLResponse)
def bootstrap(request: Request, operator: str = Depends(require_access)):
    target_origin = json.dumps(PUBLIC_ORIGIN)
    channel_nonce = request.query_params.get("channel_nonce", "")
    if not channel_nonce.replace("-", "").isalnum() or not (16 <= len(channel_nonce) <= 128):
        raise HTTPException(status_code=400, detail="invalid channel nonce")
    nonce_json = json.dumps(channel_nonce)
    html = f"""<!doctype html>
<html><head><meta charset=\"utf-8\"><title>War Room Operator</title></head>
<body><p id=\"state\">Operator session ready. Keep this window open.</p>
<script>
const TARGET_ORIGIN={target_origin};
const CHANNEL='ncaaf-war-room-control-v1';
const CHANNEL_NONCE={nonce_json};
const ACTION_ROUTES=Object.freeze({{market:'/war-room/market',ratings:'/war-room/ratings',postgame:'/war-room/postgame'}});
const TERMINAL=new Set(['COMPLETED','COMPLETED_WITH_WARNINGS','FAILED','BLOCKED_BY_OVERLAP','DEFERRED_BY_DAILY_BACKBONE']);
function send(message){{if(window.opener)window.opener.postMessage({{channel:CHANNEL,channelNonce:CHANNEL_NONCE,...message}},TARGET_ORIGIN)}}
async function pollTask(taskId,requestId){{
  for(let attempt=0;attempt<240;attempt++){{
    const response=await fetch(`/war-room/task/${{encodeURIComponent(taskId)}}`,{{cache:'no-store',credentials:'same-origin'}});
    const payload=await response.json().catch(()=>({{}}));
    if(!response.ok)throw new Error(payload?.detail || `Task HTTP ${{response.status}}`);
    send({{type:'TASK',requestId,task:payload.task}});
    if(TERMINAL.has(payload.task?.status))return;
    await new Promise(resolve=>setTimeout(resolve,500));
  }}
  throw new Error(`Task ${{taskId}} status timed out`);
}}
addEventListener('message',async event=>{{
  if(event.origin!==TARGET_ORIGIN || event.source!==window.opener)return;
  const message=event.data||{{}};
  if(message.channel!==CHANNEL || message.channelNonce!==CHANNEL_NONCE || message.type!=='REQUEST' || !Object.hasOwn(ACTION_ROUTES,message.action))return;
  try{{
    const response=await fetch(ACTION_ROUTES[message.action],{{method:'POST',cache:'no-store',credentials:'same-origin'}});
    const payload=await response.json().catch(()=>({{}}));
    if(response.status!==202 || !payload.task_id)throw new Error(payload?.detail || `HTTP ${{response.status}}`);
    send({{type:'ACK',requestId:message.requestId,payload}});
    await pollTask(payload.task_id,message.requestId);
  }}catch(error){{send({{type:'ERROR',requestId:message.requestId,message:String(error.message||error)}})}}
}});
send({{type:'READY'}});
setInterval(()=>send({{type:'READY'}}),1000);
</script></body></html>"""
    return HTMLResponse(
        html,
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'none'; script-src 'unsafe-inline'; connect-src 'self'",
            "Referrer-Policy": "no-referrer",
            "X-Frame-Options": "DENY",
        },
    )


@app.get("/war-room/task/{task_id}")
def task_status(task_id: str, operator: str = Depends(require_access)):
    if not task_id.replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="invalid task id")
    task = load_json(TASKS / f"{task_id}.json", None)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {"ok": True, "operator": operator, "task": task}


@app.post("/war-room/market", status_code=202)
def market(request: Request, operator: str = Depends(require_access)):
    return request_action("market", operator, request)


@app.post("/war-room/ratings", status_code=202)
def ratings(request: Request, operator: str = Depends(require_access)):
    return request_action("ratings", operator, request)


@app.post("/war-room/postgame", status_code=202)
def postgame(request: Request, operator: str = Depends(require_access)):
    return request_action("postgame", operator, request)


@app.get("/war-room/state")
def state(operator: str = Depends(require_access)):
    return {"ok": True, "operator": operator, "health": load_json(HEALTH, {}), "matrix": load_json(MATRIX, {})}
