#!/usr/bin/env python3
"""Audit all non-model Openers betting-context rules and historical support.

Read-only audit. It does not modify HTML or JavaScript.

Purpose
-------
Create a complete inventory of the betting angles that can appear in the
expanded matchup workspace, together with any historical record, ATS/O-U
percentage, sample size, source, and current 2026 occurrence count.

The audit is designed to support a later High / Medium / Low priority policy.

Inputs
------
- matchup_workspace.js
- data/site/matchups_view.json
- data/site/returning_production_validated_signals_2026.json

Outputs
-------
- data/audits/openers_context_rule_inventory.csv
- data/audits/openers_context_angle_instances.csv
- data/audits/openers_context_coach_samples.csv
- data/audits/openers_context_priority_candidates.csv
- data/audits/openers_context_rule_audit.txt
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import math
import re
import sys
from typing import Any, Iterable

import numpy as np
import pandas as pd


ROOT = Path.home() / "NCAAF_AUTO"

WORKSPACE_JS = ROOT / "matchup_workspace.js"

MATCHUP_JSON_CANDIDATES = [
    ROOT / "data/site/matchups_view.json",
    ROOT / "build/public_site/data/site/matchups_view.json",
]

RP_JSON_CANDIDATES = [
    ROOT / "data/site/returning_production_validated_signals_2026.json",
    ROOT / "build/public_site/data/site/returning_production_validated_signals_2026.json",
]

OUT_INVENTORY = ROOT / "data/audits/openers_context_rule_inventory.csv"
OUT_INSTANCES = ROOT / "data/audits/openers_context_angle_instances.csv"
OUT_COACH = ROOT / "data/audits/openers_context_coach_samples.csv"
OUT_PRIORITY = ROOT / "data/audits/openers_context_priority_candidates.csv"
OUT_REPORT = ROOT / "data/audits/openers_context_rule_audit.txt"


MODEL_RULE_PATTERNS = [
    "model spread edge",
    "model total edge",
    "spread model edge",
    "total model edge",
]


def first_existing(paths: Iterable[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError(
        "None of these files exist:\n"
        + "\n".join(str(path) for path in paths)
    )


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return ""
    return str(value).strip()


def numeric(value: Any) -> float | None:
    try:
        if value is None or clean(value) == "":
            return None
        result = float(value)
        return result if np.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_dict(
    obj: Any,
    prefix: str = "",
    max_depth: int = 4,
) -> dict[str, Any]:
    out: dict[str, Any] = {}

    if max_depth < 0:
        return out

    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)

            if isinstance(value, (dict, list)):
                out.update(
                    flatten_dict(
                        value,
                        path,
                        max_depth=max_depth - 1,
                    )
                )
            else:
                out[path] = value

    elif isinstance(obj, list):
        for index, value in enumerate(obj[:20]):
            path = f"{prefix}[{index}]"
            if isinstance(value, (dict, list)):
                out.update(
                    flatten_dict(
                        value,
                        path,
                        max_depth=max_depth - 1,
                    )
                )
            else:
                out[path] = value

    return out


def extract_record(text: str) -> tuple[str, int | None, int | None, int | None]:
    patterns = [
        re.compile(
            r"\b(\d+)\s*[-–]\s*(\d+)\s*[-–]\s*(\d+)\b"
        ),
        re.compile(
            r"\b(\d+)\s*[-–]\s*(\d+)\b"
        ),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue

        groups = match.groups()

        if len(groups) == 3:
            wins, losses, pushes = map(int, groups)
        else:
            wins, losses = map(int, groups)
            pushes = 0

        return match.group(0), wins, losses, pushes

    return "", None, None, None


def extract_percent(text: str) -> float | None:
    match = re.search(r"\b(\d{1,3}(?:\.\d+)?)\s*%", text)
    return float(match.group(1)) if match else None


def extract_sample_size(text: str) -> int | None:
    patterns = [
        re.compile(r"\bn\s*=\s*(\d+)\b", re.I),
        re.compile(r"\bover\s+(\d+)\s+games?\b", re.I),
        re.compile(r"\b(\d+)\s+games?\b", re.I),
    ]

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return int(match.group(1))

    record, wins, losses, pushes = extract_record(text)
    if record and wins is not None and losses is not None:
        return wins + losses + (pushes or 0)

    return None


def ats_pct_from_record(
    wins: int | None,
    losses: int | None,
) -> float | None:
    if wins is None or losses is None:
        return None

    decisions = wins + losses
    return wins / decisions * 100 if decisions else None


def normalize_market(value: Any, text: str = "") -> str:
    raw = f"{clean(value)} {text}".lower()

    if "first half" in raw or re.search(r"\b1h\b", raw):
        return "1H"
    if "second half" in raw or re.search(r"\b2h\b", raw):
        return "2H"
    if "total" in raw or "o/u" in raw or "over" in raw or "under" in raw:
        return "Total"
    if "spread" in raw or "ats" in raw or "side" in raw:
        return "Spread"
    if "early season" in raw:
        return "Early season"
    return clean(value) or "Context"


def infer_category(text: str) -> str:
    lowered = text.lower()

    if "returning production" in lowered or "returning-production" in lowered:
        return "Returning production"
    if "coach" in lowered or "ats as favorite" in lowered or "ats as underdog" in lowered:
        return "Coach trend"
    if "injur" in lowered or "quarterback" in lowered or "qb1" in lowered:
        return "Injury"
    if any(
        term in lowered
        for term in [
            "travel",
            "lookahead",
            "sandwich",
            "short rest",
            "back-to-back",
            "b2b",
            "bye",
            "schedule",
            "step up",
            "step down",
        ]
    ):
        return "Schedule spot"
    if "continuity" in lowered or "returning staff" in lowered:
        return "Staff continuity"
    if "weather" in lowered or "wind" in lowered or "rain" in lowered:
        return "Weather"
    if "line move" in lowered or "reverse line" in lowered or "book disagreement" in lowered:
        return "Market information"
    if "model spread" in lowered or "model total" in lowered:
        return "Model edge"
    return "Other"


def recommendation(
    *,
    category: str,
    sample_size: int | None,
    pct: float | None,
    source_quality: str,
    validated: bool,
) -> tuple[str, str]:
    """Return provisional priority and rationale.

    This is intentionally conservative and is not a production policy.
    """

    if category == "Model edge":
        return "Exclude", "Already displayed in the main Openers columns"

    if validated and sample_size is not None and pct is not None:
        if sample_size >= 50 and pct >= 58:
            return "High candidate", "Validated rule with 50+ games and 58%+ ATS"
        if sample_size >= 30 and pct >= 60:
            return "High candidate", "Validated rule with 30+ games and 60%+ ATS"
        if sample_size >= 20 and pct >= 65:
            return "High candidate", "Validated rule with 20+ games and 65%+ ATS"

    if sample_size is not None and pct is not None:
        if sample_size >= 30 and pct >= 55:
            return "Medium candidate", "30+ games and 55%+ ATS/O-U"
        if sample_size >= 20 and pct >= 57.5:
            return "Medium candidate", "20+ games and 57.5%+ ATS/O-U"
        if sample_size >= 15 and pct >= 60:
            return "Medium candidate", "15+ games and 60%+ ATS/O-U"
        if sample_size >= 15 and pct >= 55:
            return "Low candidate", "15+ games and 55%+ ATS/O-U"
        return "Exclude or context", "Historical performance/sample does not clear provisional floor"

    if category in {"Injury", "Schedule spot", "Weather", "Market information"}:
        return "Context pending validation", "Potentially actionable but no historical sample attached"

    if source_quality == "Structural":
        return "Context pending validation", "Structural rule without attached betting record"

    return "Exclude or context", "Insufficient sample-size evidence"


def parse_add_templates(js_text: str) -> list[dict[str, Any]]:
    """Extract literal add({...}) blocks from contextRows source."""

    rows: list[dict[str, Any]] = []

    for match in re.finditer(r"\badd\s*\(\s*\{", js_text):
        start = match.start()
        brace = js_text.find("{", start)
        depth = 0
        in_string = False
        quote = ""
        escaped = False
        end = None

        for index in range(brace, min(len(js_text), brace + 6000)):
            char = js_text[index]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    in_string = False
                continue

            if char in {"'", '"', "`"}:
                in_string = True
                quote = char
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break

        if end is None:
            continue

        block = js_text[brace:end]

        def literal(field: str) -> str:
            patterns = [
                re.compile(
                    rf"\b{re.escape(field)}\s*:\s*'([^']*)'"
                ),
                re.compile(
                    rf'\b{re.escape(field)}\s*:\s*"([^"]*)"'
                ),
                re.compile(
                    rf"\b{re.escape(field)}\s*:\s*`([^`]*)`"
                ),
            ]

            for pattern in patterns:
                found = pattern.search(block)
                if found:
                    return found.group(1)
            return ""

        row_id = literal("id")
        market = literal("market")
        trigger = literal("trigger")
        evidence = literal("evidence")
        team = literal("team")
        score_match = re.search(r"\bscore\s*:\s*(\d+(?:\.\d+)?)", block)

        if not any([row_id, market, trigger, evidence]):
            continue

        rows.append(
            {
                "rule_id": row_id,
                "market": market,
                "team_literal": team,
                "trigger_template": trigger,
                "evidence_template": evidence,
                "score_literal": (
                    float(score_match.group(1))
                    if score_match
                    else None
                ),
                "source": "matchup_workspace.js add() template",
                "source_quality": "Structural",
            }
        )

    return rows


def angle_instances(games: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for game in games:
        game_info = game.get("game", {})
        game_id = clean(game_info.get("game_id"))
        week = numeric(game_info.get("week"))
        away = clean(game_info.get("away_team"))
        home = clean(game_info.get("home_team"))

        for index, angle in enumerate(game.get("angles", []) or []):
            if not isinstance(angle, dict):
                continue

            flat = flatten_dict(angle)
            text = " | ".join(
                clean(value)
                for value in [
                    angle.get("signal_group"),
                    angle.get("signal_type"),
                    angle.get("headline"),
                    angle.get("detail"),
                    angle.get("evidence"),
                    angle.get("strength"),
                    angle.get("direction"),
                    angle.get("team"),
                    angle.get("market"),
                ]
                if clean(value)
            )

            record, wins, losses, pushes = extract_record(text)
            pct = extract_percent(text)
            if pct is None:
                pct = ats_pct_from_record(wins, losses)

            sample_size = extract_sample_size(text)

            rows.append(
                {
                    "game_id": game_id,
                    "week": week,
                    "away_team": away,
                    "home_team": home,
                    "angle_index": index,
                    "signal_group": clean(angle.get("signal_group")),
                    "signal_type": clean(angle.get("signal_type")),
                    "headline": clean(angle.get("headline")),
                    "detail": clean(angle.get("detail")),
                    "evidence": clean(angle.get("evidence")),
                    "strength": clean(angle.get("strength")),
                    "direction": clean(
                        angle.get("direction") or angle.get("team")
                    ),
                    "market": normalize_market(
                        angle.get("market"),
                        text,
                    ),
                    "category": infer_category(text),
                    "record": record,
                    "wins": wins,
                    "losses": losses,
                    "pushes": pushes,
                    "historical_pct": pct,
                    "sample_size": sample_size,
                    "raw_fields": json.dumps(flat, sort_keys=True),
                }
            )

    return pd.DataFrame(rows)


def coach_samples(games: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    for game in games:
        game_info = game.get("game", {})
        game_id = clean(game_info.get("game_id"))
        week = numeric(game_info.get("week"))
        away = clean(game_info.get("away_team"))
        home = clean(game_info.get("home_team"))

        coaches = (
            game.get("matchup", {}).get("coaches", [])
            or []
        )

        for coach in coaches:
            if not isinstance(coach, dict):
                continue

            team = clean(coach.get("team"))
            coach_name = clean(coach.get("coach"))

            # Role splits used by Openers.
            for split in coach.get("role_splits", []) or []:
                if not isinstance(split, dict):
                    continue

                role = clean(split.get("role"))
                record = clean(split.get("ats_record"))
                wins = numeric(split.get("ats_wins"))
                losses = numeric(split.get("ats_losses"))
                pushes = numeric(split.get("ats_pushes"))
                ats_pct = numeric(split.get("ats_pct"))

                if ats_pct is not None and ats_pct <= 1:
                    ats_pct *= 100

                if wins is None or losses is None:
                    _, rw, rl, rp = extract_record(record)
                    wins, losses, pushes = rw, rl, rp

                sample_size = (
                    int(wins + losses + (pushes or 0))
                    if wins is not None and losses is not None
                    else None
                )

                ou_record = clean(split.get("ou_record"))
                _, ow, ol, op = extract_record(ou_record)
                over_pct = numeric(split.get("over_pct"))
                if over_pct is not None and over_pct <= 1:
                    over_pct *= 100

                ou_sample = (
                    int(ow + ol + (op or 0))
                    if ow is not None and ol is not None
                    else None
                )

                key = (
                    coach_name,
                    team,
                    "Full game role",
                    role,
                    record,
                    ou_record,
                )
                if key in seen:
                    continue
                seen.add(key)

                rows.append(
                    {
                        "game_id_example": game_id,
                        "week_example": week,
                        "away_team_example": away,
                        "home_team_example": home,
                        "team": team,
                        "coach": coach_name,
                        "segment": "Full game role",
                        "role": role,
                        "ats_record": record,
                        "ats_pct": ats_pct,
                        "ats_sample_size": sample_size,
                        "ou_record": ou_record,
                        "over_pct": over_pct,
                        "ou_sample_size": ou_sample,
                        "ats_margin": numeric(split.get("ats_margin")),
                        "total_margin": numeric(split.get("total_margin")),
                    }
                )

            # Full-game, 1H and 2H record cards.
            records = coach.get("records", {}) or {}
            if isinstance(records, dict):
                for segment_key, segment_value in records.items():
                    if not isinstance(segment_value, dict):
                        continue

                    record = clean(
                        segment_value.get("ats_record")
                        or segment_value.get("record")
                    )
                    _, wins, losses, pushes = extract_record(record)
                    ats_pct = numeric(segment_value.get("ats_pct"))
                    if ats_pct is not None and ats_pct <= 1:
                        ats_pct *= 100

                    sample_size = (
                        wins + losses + (pushes or 0)
                        if wins is not None and losses is not None
                        else None
                    )

                    key = (
                        coach_name,
                        team,
                        segment_key,
                        "",
                        record,
                        "",
                    )
                    if key in seen:
                        continue
                    seen.add(key)

                    rows.append(
                        {
                            "game_id_example": game_id,
                            "week_example": week,
                            "away_team_example": away,
                            "home_team_example": home,
                            "team": team,
                            "coach": coach_name,
                            "segment": clean(segment_key),
                            "role": "",
                            "ats_record": record,
                            "ats_pct": ats_pct,
                            "ats_sample_size": sample_size,
                            "ou_record": clean(
                                segment_value.get("ou_record")
                            ),
                            "over_pct": numeric(
                                segment_value.get("over_pct")
                            ),
                            "ou_sample_size": None,
                            "ats_margin": numeric(
                                segment_value.get("ats_margin")
                            ),
                            "total_margin": numeric(
                                segment_value.get("total_margin")
                            ),
                        }
                    )

    return pd.DataFrame(rows)


def rp_inventory(
    rp_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    meta = rp_payload.get("meta", {})
    rules = meta.get("rules", {}) or {}
    rows = []

    for rule_id, rule in rules.items():
        if not isinstance(rule, dict):
            continue

        status = clean(rule.get("status"))
        record = clean(
            rule.get("record")
            or rule.get("underdog_record")
        )
        _, wins, losses, pushes = extract_record(record)
        pct = numeric(
            rule.get("ats_pct")
            or rule.get("underdog_ats_pct")
        )
        sample_size = (
            wins + losses + (pushes or 0)
            if wins is not None and losses is not None
            else None
        )

        rows.append(
            {
                "rule_id": rule_id,
                "category": "Returning production",
                "market": "Spread",
                "trigger": status,
                "historical_record": record,
                "historical_pct": pct,
                "sample_size": sample_size,
                "source": "Validated RP 2021-2025",
                "source_quality": "Validated",
                "validated": True,
                "current_2026_occurrences": sum(
                    1
                    for signal in rp_payload.get("signals", []) or []
                    if signal.get("primary_rule_key") == rule_id
                ),
            }
        )

        # Add P4-P4 favorite context separately.
        favorite_record = clean(rule.get("favorite_record"))
        if favorite_record:
            _, fw, fl, fp = extract_record(favorite_record)
            rows.append(
                {
                    "rule_id": rule_id + "__FAVORITE_CONTEXT",
                    "category": "Returning production",
                    "market": "Spread",
                    "trigger": "RP team is favorite; context only",
                    "historical_record": favorite_record,
                    "historical_pct": numeric(
                        rule.get("favorite_ats_pct")
                    ),
                    "sample_size": (
                        fw + fl + (fp or 0)
                        if fw is not None and fl is not None
                        else None
                    ),
                    "source": "Validated RP 2021-2025",
                    "source_quality": "Validated",
                    "validated": True,
                    "current_2026_occurrences": 0,
                }
            )

    return rows


def summarize_angles(
    instances: pd.DataFrame,
) -> list[dict[str, Any]]:
    if instances.empty:
        return []

    grouping = [
        "signal_group",
        "signal_type",
        "headline",
        "market",
        "category",
    ]

    rows = []

    for keys, group in instances.groupby(
        grouping,
        dropna=False,
    ):
        (
            signal_group,
            signal_type,
            headline,
            market,
            category,
        ) = keys

        records = [
            value for value in group["record"].dropna().astype(str)
            if value
        ]
        pcts = pd.to_numeric(
            group["historical_pct"],
            errors="coerce",
        ).dropna()
        samples = pd.to_numeric(
            group["sample_size"],
            errors="coerce",
        ).dropna()

        rule_id = (
            clean(signal_type)
            or clean(signal_group)
            or clean(headline)
            or "angle"
        )

        rows.append(
            {
                "rule_id": rule_id,
                "category": clean(category),
                "market": clean(market),
                "trigger": clean(headline) or clean(signal_type),
                "historical_record": Counter(records).most_common(1)[0][0]
                if records
                else "",
                "historical_pct": float(pcts.median())
                if len(pcts)
                else None,
                "sample_size": int(samples.max())
                if len(samples)
                else None,
                "source": "matchups_view angles",
                "source_quality": "Historical angle"
                if records or len(pcts) or len(samples)
                else "Structural",
                "validated": False,
                "current_2026_occurrences": int(len(group)),
                "strength_values": " | ".join(
                    sorted(
                        {
                            clean(value)
                            for value in group["strength"]
                            if clean(value)
                        }
                    )
                ),
                "example_evidence": clean(
                    group["detail"].replace("", np.nan).dropna().iloc[0]
                )
                if group["detail"].replace("", np.nan).dropna().size
                else "",
            }
        )

    return rows


def template_inventory(
    templates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []

    for template in templates:
        text = " ".join(
            [
                clean(template.get("trigger_template")),
                clean(template.get("evidence_template")),
            ]
        )
        category = infer_category(text)

        rows.append(
            {
                "rule_id": clean(template.get("rule_id"))
                or clean(template.get("trigger_template"))
                or "workspace_template",
                "category": category,
                "market": normalize_market(
                    template.get("market"),
                    text,
                ),
                "trigger": clean(template.get("trigger_template")),
                "historical_record": "",
                "historical_pct": None,
                "sample_size": None,
                "source": clean(template.get("source")),
                "source_quality": clean(
                    template.get("source_quality")
                ),
                "validated": False,
                "current_2026_occurrences": None,
                "score_literal": template.get("score_literal"),
                "example_evidence": clean(
                    template.get("evidence_template")
                ),
            }
        )

    return rows


def model_exclusion_rows() -> list[dict[str, Any]]:
    return [
        {
            "rule_id": "model_spread_edge",
            "category": "Model edge",
            "market": "Spread",
            "trigger": "Model spread edge",
            "historical_record": "",
            "historical_pct": None,
            "sample_size": None,
            "source": "matchup_workspace.js",
            "source_quality": "Model output",
            "validated": False,
            "current_2026_occurrences": None,
        },
        {
            "rule_id": "model_total_edge",
            "category": "Model edge",
            "market": "Total",
            "trigger": "Model total edge",
            "historical_record": "",
            "historical_pct": None,
            "sample_size": None,
            "source": "matchup_workspace.js",
            "source_quality": "Model output",
            "validated": False,
            "current_2026_occurrences": None,
        },
    ]


def build_inventory(
    *,
    rp_rows: list[dict[str, Any]],
    angle_rows: list[dict[str, Any]],
    template_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    combined = (
        rp_rows
        + angle_rows
        + template_rows
        + model_exclusion_rows()
    )

    frame = pd.DataFrame(combined)

    if frame.empty:
        return frame

    for column in [
        "historical_pct",
        "sample_size",
        "current_2026_occurrences",
    ]:
        if column not in frame.columns:
            frame[column] = np.nan

    frame["category"] = frame["category"].fillna("Other")
    frame["source_quality"] = frame[
        "source_quality"
    ].fillna("Unknown")
    frame["validated"] = frame[
        "validated"
    ].fillna(False).astype(bool)

    priorities = frame.apply(
        lambda row: recommendation(
            category=clean(row["category"]),
            sample_size=(
                int(row["sample_size"])
                if pd.notna(row["sample_size"])
                else None
            ),
            pct=(
                float(row["historical_pct"])
                if pd.notna(row["historical_pct"])
                else None
            ),
            source_quality=clean(row["source_quality"]),
            validated=bool(row["validated"]),
        ),
        axis=1,
        result_type="expand",
    )

    frame["provisional_priority"] = priorities[0]
    frame["priority_rationale"] = priorities[1]

    # Deduplicate identical inventory rows from JS templates and angle summaries.
    dedupe_columns = [
        "rule_id",
        "category",
        "market",
        "trigger",
        "source",
    ]

    frame = (
        frame.sort_values(
            [
                "validated",
                "sample_size",
                "historical_pct",
            ],
            ascending=[False, False, False],
        )
        .drop_duplicates(dedupe_columns, keep="first")
        .reset_index(drop=True)
    )

    return frame


def report_text(
    *,
    inventory: pd.DataFrame,
    instances: pd.DataFrame,
    coaches: pd.DataFrame,
    matchup_json: Path,
    rp_json: Path,
) -> str:
    lines: list[str] = []

    lines.append("OPENERS KEY BETTING CONTEXT AUDIT")
    lines.append("=" * 100)
    lines.append(f"Matchup data: {matchup_json}")
    lines.append(f"Validated RP data: {rp_json}")
    lines.append(f"Workspace JS: {WORKSPACE_JS}")
    lines.append("")

    lines.append("PROVISIONAL PRIORITY COUNTS")
    lines.append("-" * 100)

    counts = inventory["provisional_priority"].value_counts()
    for priority, count in counts.items():
        lines.append(f"{priority}: {count}")

    lines.append("")
    lines.append("INVENTORY WITH HISTORICAL SUPPORT")
    lines.append("-" * 100)

    supported = inventory[
        inventory["sample_size"].notna()
        | inventory["historical_pct"].notna()
        | inventory["historical_record"].fillna("").ne("")
    ].copy()

    if supported.empty:
        lines.append("No rule inventory rows included a historical sample.")
    else:
        supported = supported.sort_values(
            [
                "provisional_priority",
                "sample_size",
                "historical_pct",
            ],
            ascending=[True, False, False],
        )

        for _, row in supported.iterrows():
            pct = (
                f"{float(row['historical_pct']):.1f}%"
                if pd.notna(row["historical_pct"])
                else "—"
            )
            sample = (
                str(int(row["sample_size"]))
                if pd.notna(row["sample_size"])
                else "—"
            )
            occurrences = (
                str(int(row["current_2026_occurrences"]))
                if pd.notna(row["current_2026_occurrences"])
                else "—"
            )

            lines.append(
                f"[{row['provisional_priority']}] "
                f"{row['category']} | {row['market']} | "
                f"{row['trigger']} | "
                f"Record {clean(row['historical_record']) or '—'} | "
                f"{pct} | n={sample} | 2026 occurrences={occurrences}"
            )

    lines.append("")
    lines.append("RULES WITHOUT ATTACHED HISTORICAL SAMPLE")
    lines.append("-" * 100)

    unsupported = inventory[
        inventory["sample_size"].isna()
        & inventory["historical_pct"].isna()
        & inventory["historical_record"].fillna("").eq("")
        & inventory["category"].ne("Model edge")
    ].copy()

    for _, row in unsupported.iterrows():
        lines.append(
            f"[{row['provisional_priority']}] "
            f"{row['category']} | {row['market']} | "
            f"{row['trigger'] or row['rule_id']} | "
            f"Source: {row['source']}"
        )

    lines.append("")
    lines.append("COACH SAMPLE COVERAGE")
    lines.append("-" * 100)

    if coaches.empty:
        lines.append("No coach samples were extracted.")
    else:
        ats_samples = pd.to_numeric(
            coaches["ats_sample_size"],
            errors="coerce",
        )
        lines.append(f"Unique coach/sample rows: {len(coaches)}")
        lines.append(
            f"Rows with ATS sample >= 15: "
            f"{int((ats_samples >= 15).sum())}"
        )
        lines.append(
            f"Rows with ATS sample >= 25: "
            f"{int((ats_samples >= 25).sum())}"
        )
        lines.append(
            f"Rows with ATS sample >= 40: "
            f"{int((ats_samples >= 40).sum())}"
        )

        qualified = coaches[
            ats_samples.ge(15)
            & pd.to_numeric(
                coaches["ats_pct"],
                errors="coerce",
            ).notna()
        ].copy()

        qualified["distance_from_50"] = (
            pd.to_numeric(
                qualified["ats_pct"],
                errors="coerce",
            )
            - 50
        ).abs()

        qualified = qualified.sort_values(
            [
                "distance_from_50",
                "ats_sample_size",
            ],
            ascending=[False, False],
        ).head(40)

        lines.append("")
        lines.append("Largest qualifying coach ATS deviations:")
        for _, row in qualified.iterrows():
            lines.append(
                f"{row['team']} | {row['coach']} | "
                f"{row['segment']} {row['role']} | "
                f"{row['ats_record']} | "
                f"{float(row['ats_pct']):.1f}% | "
                f"n={int(row['ats_sample_size'])}"
            )

    lines.append("")
    lines.append("RECOMMENDED NEXT DECISION")
    lines.append("-" * 100)
    lines.append(
        "Use the inventory to approve category-specific High/Medium/Low floors. "
        "Do not apply one universal ATS threshold to injuries, schedule spots, "
        "weather, and market signals because those categories may not carry "
        "historical records in the current data."
    )
    lines.append(
        "Model spread and total edge rows should remain excluded because they "
        "are already displayed in the main Openers columns."
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    if not WORKSPACE_JS.exists():
        raise FileNotFoundError(WORKSPACE_JS)

    matchup_json = first_existing(MATCHUP_JSON_CANDIDATES)
    rp_json = first_existing(RP_JSON_CANDIDATES)

    matchup_payload = load_json(matchup_json)
    rp_payload = load_json(rp_json)

    games = matchup_payload.get("games", [])
    if not isinstance(games, list):
        raise TypeError("matchups_view.json does not contain a games list")

    js_text = WORKSPACE_JS.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    instances = angle_instances(games)
    coaches = coach_samples(games)
    templates = parse_add_templates(js_text)

    inventory = build_inventory(
        rp_rows=rp_inventory(rp_payload),
        angle_rows=summarize_angles(instances),
        template_rows=template_inventory(templates),
    )

    priority = inventory[
        inventory["provisional_priority"].isin(
            [
                "High candidate",
                "Medium candidate",
                "Low candidate",
                "Context pending validation",
            ]
        )
    ].copy()

    priority.sort_values(
        [
            "provisional_priority",
            "sample_size",
            "historical_pct",
            "current_2026_occurrences",
        ],
        ascending=[True, False, False, False],
        inplace=True,
    )

    for path in [
        OUT_INVENTORY,
        OUT_INSTANCES,
        OUT_COACH,
        OUT_PRIORITY,
        OUT_REPORT,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)

    inventory.to_csv(OUT_INVENTORY, index=False)
    instances.to_csv(OUT_INSTANCES, index=False)
    coaches.to_csv(OUT_COACH, index=False)
    priority.to_csv(OUT_PRIORITY, index=False)

    report = report_text(
        inventory=inventory,
        instances=instances,
        coaches=coaches,
        matchup_json=matchup_json,
        rp_json=rp_json,
    )
    OUT_REPORT.write_text(report, encoding="utf-8")

    print("OPENERS CONTEXT RULE AUDIT")
    print("=" * 110)
    print(f"Games scanned: {len(games)}")
    print(f"Angle instances: {len(instances)}")
    print(f"Coach sample rows: {len(coaches)}")
    print(f"Inventory rows: {len(inventory)}")
    print(f"Priority candidates: {len(priority)}")

    print()
    print("PRIORITY CANDIDATES WITH HISTORICAL SUPPORT")
    print("=" * 110)

    display = priority[
        priority["sample_size"].notna()
        | priority["historical_pct"].notna()
        | priority["historical_record"].fillna("").ne("")
    ].copy()

    if display.empty:
        print("No priority candidates with historical support were found.")
    else:
        display["historical_pct"] = pd.to_numeric(
            display["historical_pct"],
            errors="coerce",
        ).round(1)

        columns = [
            "provisional_priority",
            "category",
            "market",
            "rule_id",
            "trigger",
            "historical_record",
            "historical_pct",
            "sample_size",
            "current_2026_occurrences",
            "priority_rationale",
        ]

        print(
            display[columns]
            .sort_values(
                [
                    "provisional_priority",
                    "sample_size",
                    "historical_pct",
                ],
                ascending=[True, False, False],
            )
            .to_string(index=False)
        )

    print()
    print("CONTEXT TYPES WITHOUT HISTORICAL SAMPLE")
    print("=" * 110)

    unsupported = priority[
        priority["sample_size"].isna()
        & priority["historical_pct"].isna()
        & priority["historical_record"].fillna("").eq("")
    ].copy()

    if unsupported.empty:
        print("None")
    else:
        print(
            unsupported[
                [
                    "provisional_priority",
                    "category",
                    "market",
                    "rule_id",
                    "trigger",
                    "source",
                    "priority_rationale",
                ]
            ].to_string(index=False)
        )

    print()
    print("Created:")
    print(OUT_INVENTORY)
    print(OUT_INSTANCES)
    print(OUT_COACH)
    print(OUT_PRIORITY)
    print(OUT_REPORT)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
