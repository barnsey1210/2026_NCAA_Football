#!/usr/bin/env python3
"""Pure calculations and append-only helpers for prospective model tracking."""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

CORE_SPREAD_MODELS = ("SP+", "FPI", "TeamRankings", "Brad Powers")
SHADOW_MODELS = ("Shadow Spread", "Shadow Total")
OPENER_GRADES = {"TRUE_EXECUTABLE_OPENER", "EARLIEST_CAPTURED", "LATE_FIRST_CAPTURE", "UNKNOWN"}
CLOSE_GRADES = {"TRUE_CLOSE", "LAST_CAPTURED", "EARLY_LAST_CAPTURE", "UNKNOWN"}
TOTAL_STATUSES = {
    "INDIVIDUAL_MODEL_ONLY", "PARTIAL_TOTAL_SET", "TOTAL_CONSENSUS_ELIGIBLE",
    "INSUFFICIENT_TOTAL_MODELS",
}


def is_trackable_game(status: str) -> bool:
    return str(status or "").strip().lower() not in {"cancelled", "canceled", "postponed"}


def stable_id(*parts: Any, length: int = 24) -> str:
    payload = "|".join("" if p is None else str(p).strip() for p in parts)
    return hashlib.sha256(payload.encode()).hexdigest()[:length]


def spread_core(values: dict[str, float | None]) -> dict[str, Any]:
    missing = [m for m in CORE_SPREAD_MODELS if values.get(m) is None]
    if missing:
        return {"value": None, "version": "spread_core_v1", "eligible": False,
                "models": list(CORE_SPREAD_MODELS), "missing": missing, "weights": {m: .25 for m in CORE_SPREAD_MODELS}}
    return {"value": sum(float(values[m]) * .25 for m in CORE_SPREAD_MODELS),
            "version": "spread_core_v1", "eligible": True, "models": list(CORE_SPREAD_MODELS),
            "missing": [], "weights": {m: .25 for m in CORE_SPREAD_MODELS}}


def available_average(values: dict[str, float | None], approved: Iterable[str]) -> dict[str, Any]:
    members = [m for m in approved if values.get(m) is not None and m not in SHADOW_MODELS]
    return {"value": sum(float(values[m]) for m in members) / len(members) if members else None,
            "version": "spread_available_average_v1", "eligible": bool(members), "models": members,
            "variable_model_set": True}


def total_consensus(values: dict[str, float | None], approved: Iterable[str], minimum: int = 3) -> dict[str, Any]:
    members = [m for m in approved if values.get(m) is not None and m != "Shadow Total"]
    nums = [float(values[m]) for m in members]
    if not nums:
        status = "INSUFFICIENT_TOTAL_MODELS"
    elif len(nums) == 1:
        status = "INDIVIDUAL_MODEL_ONLY"
    elif len(nums) < minimum:
        status = "PARTIAL_TOTAL_SET"
    else:
        status = "TOTAL_CONSENSUS_ELIGIBLE"
    eligible = len(nums) >= minimum
    mean = sum(nums) / len(nums) if eligible else None
    ordered = sorted(nums)
    median = ((ordered[(len(ordered)-1)//2] + ordered[len(ordered)//2]) / 2) if eligible else None
    variance = sum((x - sum(nums)/len(nums)) ** 2 for x in nums) / len(nums) if eligible else None
    return {"status": status, "eligible": eligible, "minimum": minimum, "model_count": len(nums),
            "models": members, "value": mean, "median": median,
            "range": max(nums)-min(nums) if eligible else None,
            "stddev": math.sqrt(variance) if variance is not None else None,
            "version": "totals_consensus_v1" if eligible else None}


def spread_point_clv(selected_side: str, opener_home_line: float, close_home_line: float) -> float:
    side = selected_side.lower()
    if side == "home":
        return float(close_home_line) - float(opener_home_line)
    if side == "away":
        return -float(close_home_line) - (-float(opener_home_line))
    raise ValueError("selected_side must be home or away")


def total_point_clv(selected_side: str, opener_total: float, close_total: float) -> float:
    side = selected_side.lower()
    if side == "over":
        return float(close_total) - float(opener_total)
    if side == "under":
        return float(opener_total) - float(close_total)
    raise ValueError("selected_side must be over or under")


def american_profit(result: str, price: float, stake: float = 1.0) -> float:
    if result == "push": return 0.0
    if result == "loss": return -stake
    return stake * (price / 100 if price > 0 else 100 / abs(price))


def settle_spread(predicted_home_margin: float, opener_home_line: float, final_home_margin: float,
                  close_home_line: float | None = None, opener_price: float = -110) -> dict[str, Any]:
    selected = "home" if predicted_home_margin + opener_home_line > 0 else "away"
    ats_value = final_home_margin + opener_home_line
    selected_margin = ats_value if selected == "home" else -ats_value
    result = "win" if selected_margin > 0 else "loss" if selected_margin < 0 else "push"
    error = final_home_margin - predicted_home_margin
    clv = spread_point_clv(selected, opener_home_line, close_home_line) if close_home_line is not None else None
    closing_edge = (predicted_home_margin + close_home_line) * (1 if selected == "home" else -1) if close_home_line is not None else None
    opening_edge = abs(predicted_home_margin + opener_home_line)
    return {"selected_side": selected, "ats_result_opener": result, "push": result == "push",
            "ats_margin": selected_margin, "signed_error": error, "absolute_error": abs(error),
            "squared_error": error * error, "rmse_contribution": error * error,
            "opening_edge": opening_edge, "closing_edge": closing_edge,
            "point_clv": clv, "positive_clv": clv is not None and clv > 0,
            "clv_ge_0_5": clv is not None and clv >= .5, "clv_ge_1": clv is not None and clv >= 1,
            "clv_ge_2": clv is not None and clv >= 2,
            "market_moved_toward_model": clv is not None and clv > 0,
            "edge_retained": closing_edge/opening_edge if closing_edge is not None and opening_edge else None,
            "hypothetical_profit": american_profit(result, opener_price)}


def settle_total(predicted_total: float, opener_total: float, final_total: float,
                 close_total: float | None = None, opener_price: float = -110) -> dict[str, Any]:
    selected = "over" if predicted_total > opener_total else "under"
    selected_margin = (final_total - opener_total) * (1 if selected == "over" else -1)
    result = "win" if selected_margin > 0 else "loss" if selected_margin < 0 else "push"
    error = final_total - predicted_total
    clv = total_point_clv(selected, opener_total, close_total) if close_total is not None else None
    closing_edge = (predicted_total-close_total) * (1 if selected == "over" else -1) if close_total is not None else None
    opening_edge = abs(predicted_total-opener_total)
    return {"selected_side": selected, "ou_result": result, "push": result == "push",
            "result_margin": selected_margin, "signed_error": error, "absolute_error": abs(error),
            "squared_error": error*error, "rmse_contribution": error*error,
            "opening_edge": opening_edge, "closing_edge": closing_edge, "point_clv": clv,
            "positive_clv": clv is not None and clv > 0, "clv_ge_0_5": clv is not None and clv >= .5,
            "clv_ge_1": clv is not None and clv >= 1, "clv_ge_2": clv is not None and clv >= 2,
            "market_moved_toward_model": clv is not None and clv > 0,
            "edge_retained": closing_edge/opening_edge if closing_edge is not None and opening_edge else None,
            "hypothetical_profit": american_profit(result, opener_price)}


def append_jsonl(path: Path, record: dict[str, Any], identity_fields: Iterable[str]) -> bool:
    """Append once. Existing bytes are never rewritten."""
    path.parent.mkdir(parents=True, exist_ok=True)
    identity = tuple(record.get(k) for k in identity_fields)
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                prior = json.loads(line)
                if tuple(prior.get(k) for k in identity_fields) == identity:
                    return False
    with path.open("a") as fh:
        fh.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return True


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists(): return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w") as fh: json.dump(value, fh, indent=2); fh.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
