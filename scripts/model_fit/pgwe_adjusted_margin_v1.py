"""Research-only SP+ calibration from PGWE probability to performance margin.

This historical calibration is not authorized for the public/team CFBD Model
Fit contract.  Production evaluation uses ``cfbd_equivalent_margin_v1`` and
keeps direct SP+ adjusted margin as a separate source lens.

Calibration authority:
https://docs.google.com/spreadsheets/d/1vwoVl-Dxy0es87Z9I1RTvFzr72Lb1fAkREfbLxbK-eg/edit?gid=0#gid=0

The 2026 ``POSTGAME WIN EXPECTANCY`` sheet contains 198 mirrored team rows.
Its displayed PGWE is rounded to three decimals and adjusted margin to one
decimal.  Those rounding bins identify a compatible scale interval of about
9.16384 to 9.18769; 9.18 standard-normal units is compatible with every row:

    adjusted margin = round(9.18 * Phi^-1(PGWE), 1)

The sheet displays some underlying probabilities as 0.000 or 1.000 while
retaining different finite margins.  That proves the source uses additional
hidden precision and does not support inferring a single endpoint cap.  This
utility therefore converts only strictly interior probabilities.
"""
from __future__ import annotations

import math
from statistics import NormalDist


PGWE_ADJUSTED_MARGIN_SCALE = 9.18
PGWE_ADJUSTED_MARGIN_DECIMALS = 1
PGWE_CALIBRATION_REFERENCE = (
    "https://docs.google.com/spreadsheets/d/"
    "1vwoVl-Dxy0es87Z9I1RTvFzr72Lb1fAkREfbLxbK-eg/edit?gid=0#gid=0"
)


def pgwe_adjusted_margin_v1(probability: float) -> float:
    """Convert a strictly interior 0-1 PGWE probability to team margin.

    Exact 0 and 1 cannot be converted without inventing a cap or hidden source
    precision, so they fail explicitly along with out-of-range/non-finite data.
    """
    try:
        probability = float(probability)
    except (TypeError, ValueError) as exc:
        raise ValueError("PGWE probability must be a finite number") from exc
    if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ValueError("PGWE probability must be in the inclusive range [0, 1]")
    if probability in (0.0, 1.0):
        raise ValueError("exact endpoint PGWE has no source-supported finite margin")
    return round(PGWE_ADJUSTED_MARGIN_SCALE * NormalDist().inv_cdf(probability), PGWE_ADJUSTED_MARGIN_DECIMALS)
