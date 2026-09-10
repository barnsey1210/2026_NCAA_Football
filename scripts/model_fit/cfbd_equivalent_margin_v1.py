"""Reference conversion from CFBD postgame win probability to margin.

This is a project-owned, versioned football win%-to-margin lookup.  It is not
an official point margin published by CollegeFootballData.  The middle range
uses the user-approved football table; the 98%+ tail is intentionally widened
so extreme performances remain useful in game and team evaluation.
"""
from __future__ import annotations

import math


CFBD_EQUIVALENT_MARGIN_VERSION = "cfbd_equivalent_margin_v1"
CFBD_EQUIVALENT_MARGIN_DECIMALS = 1
CFBD_EQUIVALENT_MARGIN_PROVENANCE = (
    "project reference conversion of CollegeFootballData /games postgame win probability; "
    "not an official CFBD-published point margin"
)

# Probability percentages for the winning-team perspective.  Values below
# 50% are derived by exact sign symmetry rather than maintained separately.
_MIDDLE = {
    50: 0, 51: .5, 52: 1, 53: 1.5, 54: 2, 55: 2.5, 56: 3,
    57: 3, 58: 3.5, 59: 3.5, 60: 3.5, 61: 4, 62: 4,
    63: 4.5, 64: 4.5, 65: 4.5, 66: 5, 67: 5, 68: 5.5,
    69: 6, 70: 6.5, 71: 7, 72: 7.5, 73: 8, 74: 8.5,
    75: 9, 76: 9, 77: 9.5, 78: 10, 79: 10.5, 80: 11,
    81: 11, 82: 11.5, 83: 11.5, 84: 11.5, 85: 12, 86: 12.5,
    87: 13, 88: 14, 89: 14.5, 90: 15, 91: 16, 92: 17,
    93: 18, 94: 19.5, 95: 21, 96: 22.5, 97: 24,
}
CFBD_EQUIVALENT_MARGIN_ANCHORS = tuple(
    sorted((float(percent), float(margin)) for percent, margin in _MIDDLE.items())
    + [(98.0, 30.0), (98.5, 35.0), (99.0, 40.0), (99.5, 50.0),
       (99.9, 60.0), (100.0, 65.0)]
)


def cfbd_equivalent_margin_v1(probability: float) -> float:
    """Return the team-perspective equivalent margin for a 0-1 probability."""
    try:
        probability = float(probability)
    except (TypeError, ValueError) as exc:
        raise ValueError("CFBD postgame win probability must be a finite number") from exc
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError("CFBD postgame win probability must be in [0, 1]")
    if probability < 0.5:
        return -cfbd_equivalent_margin_v1(1.0 - probability)

    percent = probability * 100.0
    for index, (upper_percent, upper_margin) in enumerate(CFBD_EQUIVALENT_MARGIN_ANCHORS):
        if percent <= upper_percent:
            if index == 0:
                return upper_margin
            lower_percent, lower_margin = CFBD_EQUIVALENT_MARGIN_ANCHORS[index - 1]
            fraction = (percent - lower_percent) / (upper_percent - lower_percent)
            return round(lower_margin + fraction * (upper_margin - lower_margin), CFBD_EQUIVALENT_MARGIN_DECIMALS)
    raise AssertionError("validated probability was not covered by anchors")
