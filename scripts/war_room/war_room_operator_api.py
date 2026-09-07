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
from urllib.parse import urlsplit

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

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
MODEL_OVERRIDE = ROOT / "data/control/war_room_model_override.json"
def normalize_exact_origin(value: str) -> str:
    """Return one exact HTTPS origin or fail closed on paths and wildcards."""
    candidate = value.strip().rstrip("/")
    parsed = urlsplit(candidate)
    if (
        not candidate
        or "*" in candidate
        or parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError(f"invalid exact public origin: {value!r}")
    return candidate


def configured_public_origins() -> tuple[str, ...]:
    primary = os.environ.get(
        "WAR_ROOM_PUBLIC_ORIGIN", "https://barnsey1210.github.io"
    )
    configured = os.environ.get(
        "WAR_ROOM_PUBLIC_ORIGINS",
        "https://barnsey1210.github.io,https://barnseywr.com",
    )
    pages_origin = os.environ.get("WAR_ROOM_PAGES_ORIGIN", "")
    origins: list[str] = []
    for raw in (primary, *configured.split(","), pages_origin):
        if not raw.strip():
            continue
        normalized = normalize_exact_origin(raw)
        if normalized not in origins:
            origins.append(normalized)
    return tuple(origins)


PUBLIC_ORIGINS = configured_public_origins()
PUBLIC_ORIGIN = PUBLIC_ORIGINS[0]
CONTROL_ORIGIN = os.environ.get(
    "WAR_ROOM_CONTROL_ORIGIN", "https://control.barnseywr.com"
)
CONTROL_ORIGIN = normalize_exact_origin(CONTROL_ORIGIN)
ACTION_PATHS = {
    "/war-room/market",
    "/war-room/ratings",
    "/war-room/postgame",
    "/war-room/model-override",
}

class ModelOverrideRequest(BaseModel):
    mode: str
    spread_sources: list[str] = []
    total_sources: list[str] = []


app = FastAPI(title="NCAAF War Room Control Origin", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(PUBLIC_ORIGINS),
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
    elif normalized_origin and normalized_origin not in {*PUBLIC_ORIGINS, CONTROL_ORIGIN}:
        raise HTTPException(status_code=403, detail="browser origin is not authorized")
    request.state.operator = cf_access_authenticated_user_email
    return cf_access_authenticated_user_email


def require_public_read_origin(
    request: Request,
    origin: Optional[str] = Header(default=None),
) -> None:
    if request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(status_code=403, detail="origin is loopback-only")
    if origin and origin.rstrip("/") not in PUBLIC_ORIGINS:
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


def matrix_game_kickoff(game: dict) -> Optional[datetime]:
    value = game.get("kickoff_time") or game.get("date")
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def matrix_scope_games(games: list[dict], scope: str) -> list[dict]:
    if str(scope).upper() != "FBS":
        return games
    return [
        game
        for game in games
        if (game.get("scope") or {}).get("fbs_vs_fbs") is True
    ]


def matrix_available_weeks(games: list[dict]) -> list:
    values = {
        game.get("week")
        for game in games
        if game.get("week") is not None
    }
    return sorted(values, key=lambda value: int(value))


def matrix_operational_week(games: list[dict], weeks: list) -> Optional[str]:
    if not weeks:
        return None

    now = datetime.now(timezone.utc)
    grace_seconds = 12 * 60 * 60
    candidates = []

    for week in weeks:
        kickoffs = [
            matrix_game_kickoff(game)
            for game in games
            if str(game.get("week")) == str(week)
        ]
        kickoffs = [value for value in kickoffs if value is not None]

        if not kickoffs:
            continue

        candidates.append({
            "week": week,
            "first": min(kickoffs),
            "last": max(kickoffs),
        })

    current = [
        row
        for row in candidates
        if (row["last"] - now).total_seconds() + grace_seconds >= 0
    ]
    current.sort(key=lambda row: row["first"])

    if current:
        return str(current[0]["week"])

    return str(weeks[-1])


@app.get("/war-room/live/market-matrix")
def live_market_matrix(
    week: str = Query(default="AUTO", min_length=1, max_length=16),
    scope: str = Query(default="FBS", min_length=1, max_length=16),
    _: None = Depends(require_public_read_origin),
):
    matrix = public_artifact(MATRIX, "war-room-market-matrix-v1")
    schedule = public_artifact(SCHEDULE, "schedule-live-enrichment-v2")

    all_games = [
        game
        for game in matrix.get("games", [])
        if isinstance(game, dict)
    ]

    scope_games = matrix_scope_games(all_games, scope)
    available_weeks = matrix_available_weeks(scope_games)

    requested_week = str(week).upper()

    if requested_week == "AUTO":
        selected_week = matrix_operational_week(
            scope_games,
            available_weeks,
        )
    elif requested_week == "ALL":
        selected_week = "ALL"
    else:
        if not any(
            str(value) == str(week)
            for value in available_weeks
        ):
            raise HTTPException(
                status_code=404,
                detail=f"War Room week not available: {week}",
            )
        selected_week = str(week)

    if selected_week == "ALL":
        selected_games = scope_games
    else:
        selected_games = [
            game
            for game in scope_games
            if str(game.get("week")) == str(selected_week)
        ]

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

    for game in selected_games:
        live = live_by_game.get(str(game.get("game_id")))
        if not live:
            continue
        for field in live_fields:
            if field in live:
                game[field] = live.get(field)

    matrix["games"] = selected_games
    matrix["available_weeks"] = available_weeks
    matrix["selected_week"] = selected_week
    matrix["delivery_scope"] = str(scope).upper()
    matrix["delivery_mode"] = (
        "FULL_SEASON"
        if selected_week == "ALL"
        else "WEEK_SCOPED"
    )

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
    target_origins = json.dumps(PUBLIC_ORIGINS)
    channel_nonce = request.query_params.get("channel_nonce", "")
    if not channel_nonce.replace("-", "").isalnum() or not (16 <= len(channel_nonce) <= 128):
        raise HTTPException(status_code=400, detail="invalid channel nonce")
    nonce_json = json.dumps(channel_nonce)
    html = f"""<!doctype html>
<html><head><meta charset=\"utf-8\"><title>War Room Operator</title></head>
<body><p id=\"state\">Operator session ready. Keep this window open.</p>
<script>
const TARGET_ORIGINS=Object.freeze({target_origins});
let ACTIVE_TARGET_ORIGIN=null;
const CHANNEL='ncaaf-war-room-control-v1';
const CHANNEL_NONCE={nonce_json};
const ACTION_ROUTES=Object.freeze({{market:'/war-room/market',ratings:'/war-room/ratings',postgame:'/war-room/postgame','model-override':'/war-room/model-override'}});
const TERMINAL=new Set(['COMPLETED','COMPLETED_WITH_WARNINGS','FAILED','BLOCKED_BY_OVERLAP','DEFERRED_BY_DAILY_BACKBONE']);
function send(message){{
  if(!window.opener)return;
  const targets=ACTIVE_TARGET_ORIGIN?[ACTIVE_TARGET_ORIGIN]:TARGET_ORIGINS;
  targets.forEach(target=>window.opener.postMessage({{channel:CHANNEL,channelNonce:CHANNEL_NONCE,...message}},target));
}}
async function pollTask(taskId,requestId){{
  for(let attempt=0;attempt<240;attempt++){{
    let response;
    try{{
      response=await fetch(`/war-room/task/${{encodeURIComponent(taskId)}}`,{{cache:'no-store',credentials:'same-origin'}});
    }}catch(error){{
      send({{type:'SESSION_EXPIRED',requestId,message:'Authenticated operator channel unavailable'}});
      return;
    }}
    const contentType=response.headers.get('content-type') || '';
    if(response.status===401 || response.status===403 || !contentType.includes('application/json')){{
      send({{type:'SESSION_EXPIRED',requestId,message:'Cloudflare Access session expired'}});
      return;
    }}
    const payload=await response.json().catch(()=>({{}}));
    if(!response.ok)throw new Error(payload?.detail || `Task HTTP ${{response.status}}`);
    send({{type:'TASK',requestId,task:payload.task}});
    if(TERMINAL.has(payload.task?.status))return;
    await new Promise(resolve=>setTimeout(resolve,500));
  }}
  throw new Error(`Task ${{taskId}} status timed out`);
}}
addEventListener('message',async event=>{{
  if(!TARGET_ORIGINS.includes(event.origin) || event.source!==window.opener)return;
  ACTIVE_TARGET_ORIGIN=event.origin;
  const message=event.data||{{}};
  if(message.channel!==CHANNEL || message.channelNonce!==CHANNEL_NONCE || message.type!=='REQUEST' || !Object.hasOwn(ACTION_ROUTES,message.action))return;
  try{{
    let response;
    try{{
      response=await fetch(ACTION_ROUTES[message.action],{{
      method:'POST',
      cache:'no-store',
      credentials:'same-origin',
      headers:message.payload?{{'Content-Type':'application/json'}}:undefined,
      body:message.payload?JSON.stringify(message.payload):undefined
    }});
    }}catch(error){{
      send({{type:'SESSION_EXPIRED',requestId:message.requestId,message:'Authenticated operator channel unavailable'}});
      return;
    }}
    const contentType=response.headers.get('content-type') || '';
    if(response.status===401 || response.status===403 || !contentType.includes('application/json')){{
      send({{type:'SESSION_EXPIRED',requestId:message.requestId,message:'Cloudflare Access session expired'}});
      return;
    }}
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


@app.post("/war-room/model-override", status_code=202)
def model_override(
    payload: ModelOverrideRequest,
    request: Request,
    operator: str = Depends(require_access),
):
    mode = str(payload.mode or "").upper()

    spread_allowed = {
        "SP+",
        "FPI",
        "TeamRankings",
        "DRatings",
    }

    total_allowed = {
        "SP+",
        "Massey Dual",
        "DRatings Total",
    }

    spread = [
        source
        for source in payload.spread_sources
        if source in spread_allowed
    ]

    total = [
        source
        for source in payload.total_sources
        if source in total_allowed
    ]

    if mode not in {"AUTO", "MANUAL"}:
        raise HTTPException(
            status_code=400,
            detail="invalid model mode",
        )

    if len(spread) != len(payload.spread_sources):
        raise HTTPException(
            status_code=400,
            detail="invalid spread source",
        )

    if len(total) != len(payload.total_sources):
        raise HTTPException(
            status_code=400,
            detail="invalid total source",
        )

    if mode == "MANUAL" and not spread and not total:
        raise HTTPException(
            status_code=400,
            detail="MANUAL requires selected sources",
        )

    identity = f"model-override-{uuid.uuid4().hex[:12]}"
    task_path = TASKS / f"{identity}.json"

    task = {
        "schema_version": 1,
        "task_id": identity,
        "action": "model-override",
        "trigger": "cloudflare-access",
        "requester": operator[:120],
        "requested_at": utc_now(),
        "status": "REQUESTED",
        "correlation_id": request.state.correlation_id,
        "command_owner":
            "scripts/war_room/apply_war_room_model_override.py",
    }

    atomic_json(task_path, task)
    atomic_json(LATEST, task)

    command = [
        sys.executable,
        "scripts/war_room/apply_war_room_model_override.py",
        "--mode",
        mode,
        "--spread-sources",
        ",".join(spread),
        "--total-sources",
        ",".join(total),
        "--requester",
        operator,
        "--task-id",
        identity,
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

    task["status"] = "RUNNING"
    task["dispatcher_pid"] = process.pid
    atomic_json(task_path, task)
    atomic_json(LATEST, task)

    request.state.task_id = identity

    return {
        "ok": True,
        "status": "RUNNING",
        "action": "model-override",
        "task_id": identity,
        "correlation_id": request.state.correlation_id,
        "dispatcher_pid": process.pid,
    }


@app.get("/war-room/model-override")
def get_model_override(
    operator: str = Depends(require_access),
):
    return {
        "ok": True,
        "operator": operator,
        "override": load_json(
            MODEL_OVERRIDE,
            {
                "schema_version":
                    "war-room-model-override-v1",
                "mode": "AUTO",
                "spread_sources": [
                    "SP+",
                    "FPI",
                    "TeamRankings",
                    "DRatings",
                ],
                "total_sources": [
                    "SP+",
                    "Massey Dual",
                    "DRatings Total",
                ],
            },
        ),
    }


@app.get("/war-room/state")
def state(operator: str = Depends(require_access)):
    return {"ok": True, "operator": operator, "health": load_json(HEALTH, {}), "matrix": load_json(MATRIX, {})}
