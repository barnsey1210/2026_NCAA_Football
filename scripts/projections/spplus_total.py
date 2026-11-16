"""Canonical SP+ game-total and projected-score calculations."""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

FORMULA_VERSION = "shadow_total_enhanced_spplus_od_v1"

def finite(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None

def projected_total(team_a_offense: Any, team_b_defense: Any, team_b_offense: Any, team_a_defense: Any) -> float | None:
    """Return the authoritative SP+ total; HFA never enters this formula."""
    values = [finite(team_a_offense), finite(team_b_defense), finite(team_b_offense), finite(team_a_defense)]
    if any(value is None for value in values):
        return None
    a_offense, b_defense, b_offense, a_defense = values
    return (a_offense + b_defense) / 2.0 + (b_offense + a_defense) / 2.0

def projected_scores(total: Any, team_a_margin: Any) -> tuple[float, float] | None:
    """Return Team A and Team B scores from total and signed Team A margin."""
    total_value, margin_value = finite(total), finite(team_a_margin)
    if total_value is None or margin_value is None:
        return None
    return ((total_value + margin_value) / 2.0, (total_value - margin_value) / 2.0)

def load_current_components(path: Path) -> dict[str, dict[str, float]]:
    """Load exactly one current raw SP+ offense/defense row for all 138 teams."""
    components: dict[str, dict[str, float]] = {}
    with path.open() as handle:
        for row in csv.DictReader(handle):
            team = str(row.get("team") or "").strip()
            offense, defense = finite(row.get("spplus_off")), finite(row.get("spplus_def"))
            if not team or team in components or offense is None or defense is None:
                raise ValueError(f"invalid SP+ component row for {team or '<missing team>'}")
            components[team] = {"offense": offense, "defense": defense}
    if len(components) != 138:
        raise ValueError(f"SP+ component input must contain exactly 138 teams, found {len(components)}")
    return components
