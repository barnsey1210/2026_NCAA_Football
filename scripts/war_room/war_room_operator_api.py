#!/usr/bin/env python3
"""Loopback-only origin for authenticated War Room operational actions.

Cloudflare Access and Tunnel provide the public authentication boundary. This
origin accepts only fixed actions and never accepts commands, script paths, or
provider credentials from a request.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[2]
LATEST = ROOT / "data/control/war_room_services/latest.json"
TASKS = ROOT / "data/control/war_room_services/tasks"
HEALTH = ROOT / "data/site/war_room_health.json"
MATRIX = ROOT / "data/site/war_room_market_matrix.json"
PUBLIC_ORIGIN = os.environ.get(
    "WAR_ROOM_PUBLIC_ORIGIN", "https://barnsey1210.github.io"
).rstrip("/")

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


def require_access(
    request: Request,
    cf_access_jwt_assertion: Optional[str] = Header(default=None),
    cf_access_authenticated_user_email: Optional[str] = Header(default=None),
) -> str:
    if request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(status_code=403, detail="origin is loopback-only")
    if not cf_access_jwt_assertion or not cf_access_authenticated_user_email:
        raise HTTPException(status_code=401, detail="Cloudflare Access authentication required")
    return cf_access_authenticated_user_email


def request_action(action: str, requester: str) -> dict[str, Any]:
    command = [
        sys.executable,
        "scripts/control/run_war_room_service.py",
        action,
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
    return {"ok": True, "status": "REQUESTED", "action": action, "dispatcher_pid": process.pid}


@app.get("/war-room/status")
def status(operator: str = Depends(require_access)):
    return {"ok": True, "authenticated": True, "operator": operator, "latest": load_json(LATEST, {"status": "NEVER_RUN"})}


@app.get("/war-room/task/{task_id}")
def task_status(task_id: str, operator: str = Depends(require_access)):
    if not task_id.replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="invalid task id")
    task = load_json(TASKS / f"{task_id}.json", None)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {"ok": True, "operator": operator, "task": task}


@app.post("/war-room/market")
def market(operator: str = Depends(require_access)):
    return request_action("market", operator)


@app.post("/war-room/ratings")
def ratings(operator: str = Depends(require_access)):
    return request_action("ratings", operator)


@app.post("/war-room/postgame")
def postgame(operator: str = Depends(require_access)):
    return request_action("postgame", operator)


@app.get("/war-room/state")
def state(operator: str = Depends(require_access)):
    return {"ok": True, "operator": operator, "health": load_json(HEALTH, {}), "matrix": load_json(MATRIX, {})}
