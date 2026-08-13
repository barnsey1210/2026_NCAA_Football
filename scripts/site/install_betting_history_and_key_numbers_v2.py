#!/usr/bin/env python3
"""
Install historical betting tables on the actual current source owners:

  openers.html
  betting_v2.html

This revision is based on the current repository layout:
  ./openers.html
  ./betting_v2.html

It does NOT touch runtime copies, rollback copies, build/public_site copies,
or old openers_v2 backups.

Source data:
  reports/five_source_backtest_validated/corrected/site_history_v2/
    site_betting_history_v2.json
"""

from pathlib import Path
from datetime import datetime
import html
import json
import re
import shutil
import sys

ROOT = Path("/Users/jameslindesmith/NCAAF_MAIN_REPO")
SOURCE = ROOT / "reports/five_source_backtest_validated/corrected/site_history_v2/site_betting_history_v2.json"
HALF_POINT_VALUES = ROOT / "data/site/ncaaf_spread_half_point_values_2021_2025.json"
SPREAD_EDGE_VALIDATION = ROOT / "data/site/historical_spread_edge_validation_2021_2025.csv"
HISTORICAL_MODEL_PERFORMANCE = ROOT / "data/site/historical_model_performance_2021_2025.json"
TOTALS_EDGE_VALIDATION = ROOT / "data/site/historical_totals_edge_validation_2021_2025.csv"
HISTORICAL_TOTALS_MODEL_PERFORMANCE = ROOT / "data/site/historical_totals_model_performance_2021_2025.json"

# Current source owners confirmed by repo inventory.
OPENERS = ROOT / "openers.html"
BETTING = ROOT / "betting_v2.html"

for path in (SOURCE, HALF_POINT_VALUES, OPENERS, BETTING):
    if not path.exists():
        raise SystemExit(f"STOP: required file missing: {path}")

payload = json.loads(SOURCE.read_text())

if not SPREAD_EDGE_VALIDATION.exists():
    raise SystemExit(
        f"STOP: missing spread validation CSV: {SPREAD_EDGE_VALIDATION}"
    )

import csv

with SPREAD_EDGE_VALIDATION.open(newline="") as f:
    spread_validation_rows = list(csv.DictReader(f))

if not HISTORICAL_MODEL_PERFORMANCE.exists():
    raise SystemExit(
        f"STOP: missing historical model performance JSON: {HISTORICAL_MODEL_PERFORMANCE}"
    )

historical_model_payload = json.loads(
    HISTORICAL_MODEL_PERFORMANCE.read_text()
)

if historical_model_payload.get("schema") != "historical-model-performance-v2":
    raise SystemExit(
        "STOP: unexpected historical model performance schema: "
        f"{historical_model_payload.get('schema')}"
    )

historical_model_rows = historical_model_payload.get("rows") or []

if not TOTALS_EDGE_VALIDATION.exists():
    raise SystemExit(
        f"STOP: missing totals validation CSV: {TOTALS_EDGE_VALIDATION}"
    )

with TOTALS_EDGE_VALIDATION.open(newline="") as f:
    totals_validation_rows = list(csv.DictReader(f))

totals_validation_by_threshold = {
    float(r["edge_threshold"]): r
    for r in totals_validation_rows
}

if not totals_validation_by_threshold:
    raise SystemExit(
        "STOP: totals validation CSV has no threshold rows"
    )

if not HISTORICAL_TOTALS_MODEL_PERFORMANCE.exists():
    raise SystemExit(
        "STOP: missing historical totals model performance JSON: "
        f"{HISTORICAL_TOTALS_MODEL_PERFORMANCE}"
    )

historical_totals_model_payload = json.loads(
    HISTORICAL_TOTALS_MODEL_PERFORMANCE.read_text()
)

if historical_totals_model_payload.get("schema") != "historical-totals-model-performance-v1":
    raise SystemExit(
        "STOP: unexpected historical totals model schema: "
        f"{historical_totals_model_payload.get('schema')}"
    )

historical_totals_model_rows = (
    historical_totals_model_payload.get("rows") or []
)

HISTORICAL_TOTALS_MODEL_NAMES = [
    "40/40/20 + Sagarin",
    "SP+/Massey 50/50",
    "SP+",
    "Massey Total",
    "Massey Pred Sum",
    "Massey Dual",
    "Sagarin",
    "DRatings",
]

HISTORICAL_TOTALS_MODEL_SCOPES = [
    "2021-2025",
    "2021",
    "2022",
    "2023",
    "2024",
    "2025",
]

HISTORICAL_TOTALS_MODEL_VIEWS = [
    "all",
    "3.0",
]

expected_totals_model_rows = (
    len(HISTORICAL_TOTALS_MODEL_NAMES)
    * len(HISTORICAL_TOTALS_MODEL_SCOPES)
    * len(HISTORICAL_TOTALS_MODEL_VIEWS)
)

if len(historical_totals_model_rows) != expected_totals_model_rows:
    raise SystemExit(
        "STOP: expected "
        f"{expected_totals_model_rows} historical totals model rows; "
        f"found {len(historical_totals_model_rows)}"
    )

historical_totals_model_lookup = {
    (r["view"], r["scope"], r["model"]): r
    for r in historical_totals_model_rows
}

HISTORICAL_MODEL_NAMES = [
    "Five-source equal weight",
    "SP+",
    "FPI",
    "TeamRankings",
    "Sagarin",
    "DRatings",
]

HISTORICAL_MODEL_SCOPES = [
    "2021-2025",
    "2021",
    "2022",
    "2023",
    "2024",
    "2025",
]

# Only expose the two model-comparison views requested for the site.
HISTORICAL_MODEL_VIEWS = [
    "all",
    "3.0",
]

expected_historical_model_rows = (
    len(HISTORICAL_MODEL_NAMES)
    * len(HISTORICAL_MODEL_SCOPES)
    * 3
)

if len(historical_model_rows) != expected_historical_model_rows:
    raise SystemExit(
        "STOP: expected "
        f"{expected_historical_model_rows} historical model source rows; "
        f"found {len(historical_model_rows)}"
    )

historical_model_lookup = {
    (r["view"], r["scope"], r["model"]): r
    for r in historical_model_rows
}

spread_validation_by_threshold = {
    float(r["edge_threshold"]): r
    for r in spread_validation_rows
}

if not spread_validation_by_threshold:
    raise SystemExit(
        "STOP: spread validation CSV has no threshold rows"
    )
half_point_payload = json.loads(HALF_POINT_VALUES.read_text())
half_point_rows = half_point_payload.get("rows") or []

if not half_point_rows:
    raise SystemExit("STOP: half-point value JSON has no rows")

half_point_lookup = {
    (
        round(float(r["from_spread"]) * 2) / 2,
        round(float(r["to_spread"]) * 2) / 2,
    ): r
    for r in half_point_rows
}
consensus = payload.get("consensus_edge_history") or []
key_hist = payload.get("key_number_signal_history") or []
spread_top5 = (((payload.get("key_numbers") or {}).get("spread") or {}).get("top5") or [])
total_top5 = (((payload.get("key_numbers") or {}).get("total") or {}).get("top5") or [])

if not consensus or not spread_top5 or not total_top5:
    raise SystemExit("STOP: source JSON missing required arrays")

by_threshold = {str(r.get("threshold")): r for r in consensus}

spread_thresholds = [
    0.5,
    1.0,
    1.5,
    2.0,
    2.5,
    3.0,
    3.5,
    4.0,
    4.5,
    5.0,
    6.0,
]

totals_thresholds = [
    0.5,
    1.0,
    1.5,
    2.0,
    2.5,
    3.0,
    3.5,
    4.0,
    4.5,
    5.0,
    6.0,
    7.0,
    8.0,
    10.0,
]

missing_totals_thresholds = [
    x for x in totals_thresholds
    if x not in totals_validation_by_threshold
]

if missing_totals_thresholds:
    raise SystemExit(
        "STOP: missing validated totals thresholds: "
        + ", ".join(str(x) for x in missing_totals_thresholds)
    )

missing_spread_thresholds = [
    x for x in spread_thresholds
    if x not in spread_validation_by_threshold
]

if missing_spread_thresholds:
    raise SystemExit(
        "STOP: missing validated spread thresholds: "
        + ", ".join(str(x) for x in missing_spread_thresholds)
    )

def pct(v, digits=1):
    try:
        return f"{float(v)*100:.{digits}f}%"
    except:
        return "—"

def num(v, digits=2):
    try:
        return f"{float(v):.{digits}f}"
    except:
        return "—"

def signed_num(v, digits=2):
    try:
        x = float(v)
        return f"{x:+.{digits}f}"
    except:
        return "—"

def signed_pct(v, digits=2):
    try:
        x = float(v) * 100
        return f"{x:+.{digits}f}%"
    except:
        return "—"

def integer(v):
    try:
        return f"{int(round(float(v))):,}"
    except:
        return "—"

def esc(v):
    return html.escape(str(v), quote=True)


def hist_tone(v):
    try:
        x = float(v)
    except Exception:
        return ""
    if x > 0:
        return "histPositive"
    if x < 0:
        return "histNegative"
    return ""


def render_historical_model_rows():
    out = []

    for view in HISTORICAL_MODEL_VIEWS:
        for scope in HISTORICAL_MODEL_SCOPES:
            for model in HISTORICAL_MODEL_NAMES:
                r = historical_model_lookup[(view, scope, model)]

                wins = integer(r.get("wins"))
                losses = integer(r.get("losses"))
                pushes = integer(r.get("pushes"))
                record = f"{wins}-{losses}-{pushes}"

                composite = model == "Five-source equal weight"
                row_class = " histModelComposite" if composite else ""
                badge = (
                    ' <span class="histBadge histActionable">Composite</span>'
                    if composite else ""
                )

                out.append(
                    f"""<tr class="histModelRow{row_class}"
                        data-hist-model-view="{esc(view)}"
                        data-hist-model-scope="{esc(scope)}">
                      <td><b>{esc(model)}{badge}</b></td>
                      <td>{integer(r.get("games"))}</td>
                      <td>{record}</td>
                      <td>{pct(r.get("ats_pct"))}</td>
                      <td class="{hist_tone(r.get("roi"))}">
                        {signed_pct(r.get("roi"), 1)}
                      </td>
                      <td>{pct(r.get("beat_close_pct"))}</td>
                      <td class="{hist_tone(r.get("avg_clv"))}">
                        {signed_num(r.get("avg_clv"), 2)}
                      </td>
                      <td>{num(r.get("mae"), 2)}</td>
                      <td class="{hist_tone(-abs(float(r.get("bias") or 0)))}">
                        {signed_num(r.get("bias"), 2)}
                      </td>
                    </tr>"""
                )

    return "".join(out)


def render_historical_totals_model_rows():
    out = []

    for view in HISTORICAL_TOTALS_MODEL_VIEWS:
        for scope in HISTORICAL_TOTALS_MODEL_SCOPES:
            for model in HISTORICAL_TOTALS_MODEL_NAMES:
                r = historical_totals_model_lookup[
                    (view, scope, model)
                ]

                wins = integer(r.get("wins"))
                losses = integer(r.get("losses"))
                pushes = integer(r.get("pushes"))
                record = f"{wins}-{losses}-{pushes}"

                badge_name = r.get("badge")
                limited = bool(r.get("limited_coverage"))

                row_class = (
                    " histModelComposite"
                    if badge_name in ("PRIMARY", "CORE")
                    else ""
                )

                badges = []

                if badge_name == "PRIMARY":
                    badges.append(
                        '<span class="histBadge histStrong">PRIMARY</span>'
                    )
                elif badge_name == "CORE":
                    badges.append(
                        '<span class="histBadge histActionable">CORE</span>'
                    )

                if limited:
                    badges.append(
                        '<span class="histBadge">LIMITED HISTORY</span>'
                    )

                badge_html = (
                    " " + " ".join(badges)
                    if badges else ""
                )

                out.append(
                    f"""<tr class="histTotalsModelRow{row_class}"
                        data-hist-totals-model-view="{esc(view)}"
                        data-hist-totals-model-scope="{esc(scope)}">
                      <td><b>{esc(model)}</b>{badge_html}</td>
                      <td>{integer(r.get("games"))}</td>
                      <td>{record}</td>
                      <td>{pct(r.get("ou_pct"))}</td>
                      <td class="{hist_tone(r.get("roi"))}">
                        {signed_pct(r.get("roi"), 1)}
                      </td>
                      <td>{pct(r.get("beat_close_pct"))}</td>
                      <td class="{hist_tone(r.get("avg_clv"))}">
                        {signed_num(r.get("avg_clv"), 2)}
                      </td>
                      <td>{num(r.get("mae"), 2)}</td>
                      <td>
                        {signed_num(r.get("bias"), 2)}
                      </td>
                    </tr>"""
                )

    return "".join(out)


def totals_signal_badges(t, r):
    badges = []

    try:
        roi = float(r.get("actual_roi"))
    except Exception:
        roi = 0.0

    try:
        ev = float(r.get("ev_pct"))
    except Exception:
        ev = 0.0

    signal = str(r.get("signal") or "")

    if signal == "LEAN":
        badges.append(
            '<span class="histBadge">LEAN</span>'
        )
    elif signal == "BET_SIGNAL":
        badges.append(
            '<span class="histBadge histActionable">BET SIGNAL</span>'
        )
    elif signal == "ACTIONABLE":
        badges.append(
            '<span class="histBadge histActionable">ACTIONABLE</span>'
        )
    elif signal == "STRONG":
        badges.append(
            '<span class="histBadge histStrong">STRONG</span>'
        )

    if roi > 0:
        badges.append(
            '<span class="histBadge histActionable">BET ROI+</span>'
        )

    if ev > 0:
        badges.append(
            '<span class="histBadge histStrong">BET EV+</span>'
        )

    return " ".join(badges)


def render_totals_validation_rows():
    rows = []

    for t in totals_thresholds:
        r = totals_validation_by_threshold[t]

        roi = float(r["actual_roi"])
        ev = float(r["ev_pct"])
        clv = float(r["avg_clv_points"])

        cls = (
            "histCoreRow"
            if roi > 0 and ev > 0
            else (
                "histActionRow"
                if roi > 0 or ev > 0
                else ""
            )
        )

        roi_cls = hist_tone(roi)
        ev_cls = hist_tone(ev)
        clv_cls = hist_tone(clv)

        rows.append(
            f'<tr class="{cls}">'
            f'<td><b>{spread_threshold_label(t)}</b> '
            f'{totals_signal_badges(t, r)}</td>'
            f'<td>{integer(r.get("games"))}</td>'
            f'<td>{esc(r.get("record","—"))}</td>'
            f'<td>{pct(r.get("ou_pct"))}</td>'
            f'<td class="{roi_cls}">{signed_pct(r.get("actual_roi"),1)}</td>'
            f'<td>{pct(r.get("beat_close_pct"))}</td>'
            f'<td>{pct(r.get("won_line_move_pct"))}</td>'
            f'<td class="histEmphasis {clv_cls}">'
            f'{signed_num(r.get("avg_clv_points"),2)}</td>'
            f'<td class="histEmphasis {ev_cls}">'
            f'{signed_pct(r.get("ev_pct"),2)}</td>'
            '</tr>'
        )

    return "".join(rows)


def spread_threshold_label(t):
    if float(t).is_integer():
        return f"{int(t)}+"
    return f"{t:g}+"

def consensus_badge(t, r):
    badges = []

    try:
        roi = float(r.get("actual_roi"))
    except Exception:
        roi = 0.0

    try:
        ev = float(r.get("ev_pct"))
    except Exception:
        ev = 0.0

    if roi > 0:
        badges.append(
            '<span class="histBadge histActionable">BET ROI+</span>'
        )

    if ev > 0:
        badges.append(
            '<span class="histBadge histStrong">BET EV+</span>'
        )

    return " ".join(badges)

def render_consensus_rows():
    rows = []

    for t in spread_thresholds:
        r = spread_validation_by_threshold[t]

        roi = float(r["actual_roi"])
        ev = float(r["ev_pct"])
        clv = float(r["avg_clv_points"])

        cls = (
            "histCoreRow"
            if roi > 0 and ev > 0
            else (
                "histActionRow"
                if roi > 0 or ev > 0
                else ""
            )
        )

        ev_cls = (
            "histPositive"
            if ev > 0
            else "histNegative"
            if ev < 0
            else ""
        )

        clv_cls = (
            "histPositive"
            if clv > 0
            else "histNegative"
            if clv < 0
            else ""
        )

        roi_cls = (
            "histPositive"
            if roi > 0
            else "histNegative"
            if roi < 0
            else ""
        )

        rows.append(
            f'<tr class="{cls}">'
            f'<td><b>{spread_threshold_label(t)}</b> {consensus_badge(t, r)}</td>'
            f'<td>{integer(r.get("games"))}</td>'
            f'<td>{esc(r.get("record","—"))}</td>'
            f'<td>{pct(r.get("ats_pct"))}</td>'
            f'<td class="{roi_cls}">{signed_pct(r.get("actual_roi"),1)}</td>'
            f'<td>{pct(r.get("beat_close_pct"))}</td>'
            f'<td>{pct(r.get("won_line_move_pct"))}</td>'
            f'<td class="histEmphasis {clv_cls}">{signed_num(r.get("avg_clv_points"),2)}</td>'
            f'<td class="histEmphasis {ev_cls}">{signed_pct(r.get("ev_pct"),2)}</td>'
            '</tr>'
        )

    return "".join(rows)

def render_key_rows():
    rows=[]
    for r in key_hist:
        rows.append(
            '<tr>'
            f'<td>{esc(r.get("signal","—"))}</td>'
            f'<td>{integer(r.get("games"))}</td>'
            f'<td>{pct(r.get("ats_pct"))}</td>'
            f'<td>{pct(r.get("roi_minus110"))}</td>'
            f'<td>{pct(r.get("beat_close_pct_all_games"))}</td>'
            f'<td>{pct(r.get("positive_clv_pct_nonzero_moves"))}</td>'
            f'<td>{num(r.get("avg_clv_points"),2)}</td>'
            '</tr>'
        )
    return "".join(rows)

def render_key_number_items(rows):
    return "".join(
        '<span class="keyNumItem">'
        f'<b>{integer(r.get("number"))}</b>'
        f'<small>{pct(r.get("landing_pct"))}</small>'
        '</span>'
        for r in rows[:5]
    )


def fair_buy_price(from_spread, to_spread):
    key = (
        round(float(from_spread) * 2) / 2,
        round(float(to_spread) * 2) / 2,
    )
    r = half_point_lookup.get(key)
    if not r:
        return "—"
    try:
        v = round(float(r["fair_break_even_price"]))
    except Exception:
        return "—"
    return f"{v:+d}"


def render_half_point_key_prices():
    """
    ONTO:
      +2.5 -> +3
      -3.5 -> -3

    OFF:
      +3 -> +3.5
      -3 -> -2.5

    Same convention for 7, 10, 14, 17.
    """
    keys = [
        int(round(float(r.get("number"))))
        for r in spread_top5[:5]
    ]

    rows = []

    for k in keys:
        onto_dog = fair_buy_price(
            k - 0.5,
            k,
        )
        onto_fav = fair_buy_price(
            -(k + 0.5),
            -k,
        )

        off_dog = fair_buy_price(
            k,
            k + 0.5,
        )
        off_fav = fair_buy_price(
            -k,
            -(k - 0.5),
        )

        rows.append(
            '<div class="keyPriceItem">'
            f'<b>{k}</b>'
            '<span class="keyPricePair">'
            f'<small>ONTO</small> '
            f'<strong>+{k-0.5:g}→+{k} {onto_dog}</strong> · '
            f'<strong>-{k+0.5:g}→-{k} {onto_fav}</strong>'
            '</span>'
            '<span class="keyPricePair">'
            f'<small>OFF</small> '
            f'<strong>+{k}→+{k+0.5:g} {off_dog}</strong> · '
            f'<strong>-{k}→-{k-0.5:g} {off_fav}</strong>'
            '</span>'
            '</div>'
        )

    return "".join(rows)

CSS = r"""
<!-- HISTORICAL_BETTING_UI_CSS_START -->
<style id="HISTORICAL_BETTING_UI_CSS">
.histSection{margin:12px 0}
.histGrid{display:grid;grid-template-columns:1.15fr .85fr;gap:10px}
.histCard{border:1px solid var(--line);background:#081731;border-radius:13px;overflow:hidden}
.histHead{padding:10px 12px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.histHead h2{font-size:14px;margin:0}
.histHead small{color:var(--muted);max-width:760px}
.histTableWrap{overflow:auto}
.histTable{width:100%;border-collapse:collapse;min-width:720px}
.histTable th,.histTable td{padding:7px 8px;border-top:1px solid #17345c;text-align:right;white-space:nowrap;font-size:10px}
.histTable th{color:var(--muted);text-transform:uppercase;font-size:9px}
.histTable th:first-child,.histTable td:first-child{text-align:left}
.histCoreRow{background:rgba(67,223,150,.09)}
.histActionRow{background:rgba(69,156,255,.08)}
.histBadge{display:inline-flex;border-radius:999px;padding:2px 6px;font-size:8px;font-weight:950;text-transform:uppercase;letter-spacing:.04em;margin-left:4px}
.histStrong{color:#baf8d6;border:1px solid #2f7d5a;background:#0c2d25}
.histActionable{color:#cbe5ff;border:1px solid #356fa8;background:#102b50}
.histWatch{color:#ffe2a8;border:1px solid #8a6c31;background:#302711}
.histEmphasis{font-weight:950;background:rgba(255,255,255,.025)}
.histPositive{color:#77e8ad}
.histNegative{color:#ff9a9a}
.histHelp{display:inline-flex;align-items:center;justify-content:center;width:13px;height:13px;margin-left:3px;border:1px solid #40638d;border-radius:50%;font-size:8px;color:#a9c4e8;cursor:help;vertical-align:middle}
.histTotalsPlaceholder{padding:18px 14px;color:var(--muted);font-size:11px;line-height:1.55}
.histTotalsPlaceholder b{display:block;color:var(--text);font-size:13px;margin-bottom:5px}
.histNote{padding:9px 12px;color:var(--muted);font-size:9px;border-top:1px solid #17345c}
.keyRef{margin:10px 0 12px;border:1px solid var(--line);background:#081731;border-radius:12px;padding:10px 12px}
.keyRefTop{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:8px}
.keyRefTop b{font-size:12px}
.keyRefTop small{color:var(--muted);font-size:9px}
.keyRefGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.keyNumGroup{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.keyNumLabel{color:var(--muted);font-size:9px;text-transform:uppercase;font-weight:900;min-width:50px}
.keyNumItem{display:inline-flex;align-items:baseline;gap:3px;border:1px solid #28517d;background:#0d2240;border-radius:8px;padding:4px 7px}
.keyNumItem b{font-size:12px}
.keyNumItem small{font-size:8px;color:var(--muted)}
.keyPriceGrid{margin-top:8px;padding-top:8px;border-top:1px solid #17345c;display:flex;gap:6px;flex-wrap:wrap}
.keyPriceItem{border:1px solid #28517d;background:#0a1d38;border-radius:8px;padding:5px 7px;display:grid;grid-template-columns:auto 1fr;column-gap:7px;row-gap:2px;align-items:center}
.keyPriceItem>b{font-size:13px;grid-row:1/3}
.keyPricePair{font-size:8px;white-space:nowrap;color:#c7d8f2}
.keyPricePair small{font-size:7px;color:var(--muted);font-weight:900;letter-spacing:.06em}
.keyPricePair strong{font-size:8px}
.keyPriceNote{margin-top:6px;color:var(--muted);font-size:8px}
.histModelCard{margin-top:12px}
.histModelControls{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 8px}
.histModelViewControls{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 4px}
.histModelView,.histModelYear{border:1px solid #28517d;background:#0a1d38;color:var(--muted);border-radius:999px;padding:5px 9px;font-size:9px;font-weight:900;cursor:pointer}
.histModelView.active,.histModelYear.active{color:#fff;background:#1857a7;border-color:#55a2ff}
.histModelComposite td{background:rgba(24,87,167,.10)}
.histModelComposite td:first-child{box-shadow:inset 3px 0 0 #55a2ff}
.histModelMeta{margin-top:8px;color:var(--muted);font-size:9px;line-height:1.45}
.spreadEvWarning{color:#ffe2a8!important;font-weight:800;letter-spacing:.03em;margin-top:2px}
@media(max-width:900px){.histGrid,.keyRefGrid{grid-template-columns:1fr}.keyPriceItem{flex:1 1 230px}}
</style>
<!-- HISTORICAL_BETTING_UI_CSS_END -->
"""

BETTING_BLOCK = f"""
<!-- HISTORICAL_BETTING_SECTION_START -->
<section class="histSection" id="historicalBettingResearch">
  <div class="histGrid">

    <div class="histCard">
      <div class="histHead">
        <div>
          <h2>Historical Spread Edge Validation</h2>
          <small>2021–2025 · five-source equal weight · Sunday 9 PM ET market</small>
        </div>
        <small>Results + closing-market validation</small>
      </div>

      <div class="histTableWrap">
        <table class="histTable">
          <thead>
            <tr>
              <th>Edge</th>
              <th>Games</th>
              <th>Record</th>
              <th>ATS</th>
              <th>ROI</th>
              <th>
                Beat Closing Line
                <span class="histHelp"
                  title="Percentage of wagers whose Sunday 9 PM spread finished better than the CFBD historical closing spread. Same-line closes remain in the denominator but are not counted as beats.">?</span>
              </th>
              <th>
                Won Line Move
                <span class="histHelp"
                  title="Among wagers where the closing spread differed from the Sunday 9 PM entry spread, percentage where the move went in the model-selected direction. Same-line closes are excluded.">?</span>
              </th>
              <th>
                Avg CLV
                <span class="histHelp"
                  title="Average spread points gained versus the closing market. Positive means the wager beat the eventual closing number.">?</span>
              </th>
              <th>
                CLV-Implied EV
                <span class="histHelp"
                  title="Estimated expected return implied by the closing-line advantage. Uses actual entry price, the validated 2021–2025 NCAAF half-point value chart, and a standardized -110 closing price because historical closing juice is unavailable.">?</span>
              </th>
            </tr>
          </thead>
          <tbody>{render_consensus_rows()}</tbody>
        </table>
      </div>

      <div class="histNote">
        BET ROI+ identifies cumulative thresholds with positive realized historical ROI.
        BET EV+ identifies cumulative thresholds with positive CLV-Implied EV.
        Thresholds are cumulative and are not automatic betting rules.
        Beat Closing Line includes same-line closes in the denominator; Won Line Move excludes them.
        ATS and ROI show realized results, while Avg CLV and CLV-Implied EV evaluate market value.
      </div>
    </div>

    <div class="histCard">
      <div class="histHead">
        <div>
          <h2>Historical Totals Edge Validation</h2>
          <small>2021–2025 · 40% SP+ / 40% Massey Dual / 20% Sagarin · Sunday 9 PM ET market</small>
        </div>
        <small>Primary totals betting system</small>
      </div>

      <div class="histTableWrap">
        <table class="histTable">
          <thead>
            <tr>
              <th>Edge</th>
              <th>Games</th>
              <th>Record</th>
              <th>O/U Win %</th>
              <th>ROI</th>
              <th>
                Beat Closing Line
                <span class="histHelp"
                  title="Percentage of wagers whose Sunday 9 PM total finished better than the historical closing total. Same-line closes remain in the denominator but are not counted as beats.">?</span>
              </th>
              <th>
                Won Line Move
                <span class="histHelp"
                  title="Among wagers where the closing total differed from the Sunday 9 PM entry total, percentage where the move went in the model-selected direction. Same-line closes are excluded.">?</span>
              </th>
              <th>
                Avg CLV
                <span class="histHelp"
                  title="Average total points gained versus the closing market. Positive means the wager beat the eventual closing number.">?</span>
              </th>
              <th>
                CLV-Implied EV
                <span class="histHelp"
                  title="Temporary totals-specific estimate using a smooth value of roughly 2.8 percentage points of fair win probability per 1 point of total CLV at a -110 benchmark. This is a v1 approximation and will later be replaced by an empirical NCAAF totals point-value curve.">?</span>
              </th>
            </tr>
          </thead>
          <tbody>{render_totals_validation_rows()}</tbody>
        </table>
      </div>

      <div class="histNote">
        Primary model = 40% SP+ + 40% Massey Dual + 20% Sagarin.
        Massey Dual = equal weight of Massey's published Total and predicted-score sum.
        LEAN begins at 2+, BET SIGNAL at 3+, ACTIONABLE at 4+, and STRONG at 5+.
        BET ROI+ identifies positive realized historical ROI.
        BET EV+ uses the temporary totals CLV-implied EV estimate and is intentionally separate from realized ROI.
        Thresholds are cumulative and are not automatic betting rules.
      </div>
    </div>

  </div>
</section>
<!-- HISTORICAL_BETTING_SECTION_END -->
"""


MODEL_COMPARISON_BLOCK = f"""
<section class="histCard histModelCard" id="historicalModelPerformance">
  <div class="histHead">
    <div>
      <h2>Historical Model Performance</h2>
      <small>2021–2025 · Sunday 9 PM ET</small>
    </div>
    <small>Composite vs individual systems</small>
  </div>

  <div class="histModelViewControls" id="histModelViews">
    <button class="histModelView active"
      data-hist-model-view="all">All Games</button>
    <button class="histModelView"
      data-hist-model-view="3.0">3.0+ Edge</button>
  </div>

  <div class="histModelControls" id="histModelYears">
    <button class="histModelYear active" data-hist-model-year="2021-2025">2021–2025</button>
    <button class="histModelYear" data-hist-model-year="2021">2021</button>
    <button class="histModelYear" data-hist-model-year="2022">2022</button>
    <button class="histModelYear" data-hist-model-year="2023">2023</button>
    <button class="histModelYear" data-hist-model-year="2024">2024</button>
    <button class="histModelYear" data-hist-model-year="2025">2025</button>
  </div>

  <div class="histTableWrap">
    <table class="histTable">
      <thead>
        <tr>
          <th>Model</th>
          <th>Games</th>
          <th>Record</th>
          <th>ATS</th>
          <th>ROI</th>
          <th>
            Beat Closing Line
            <span class="histHelp"
              title="Percentage of Sunday 9 PM model selections finishing with a better spread than the CFBD historical closing line. Same-line closes remain in the denominator.">?</span>
          </th>
          <th>
            Avg CLV
            <span class="histHelp"
              title="Average spread points gained versus the closing market.">?</span>
          </th>
          <th>
            MAE
            <span class="histHelp"
              title="Mean absolute error between the model projected home margin and the actual final home margin. Lower is better.">?</span>
          </th>
          <th>
            Bias
            <span class="histHelp"
              title="Average projected home margin minus actual home margin. Closest to zero is best calibrated; positive means the model overrated home teams and negative means it underrated them.">?</span>
          </th>
        </tr>
      </thead>
      <tbody id="historicalModelRows">
        {render_historical_model_rows()}
      </tbody>
    </table>
  </div>

  <div class="histModelMeta">
    All Games includes every directional model selection with an executable Sunday 9 PM ET market observation.
    3.0+ Edge includes only games where that model differed from the market by at least 3 points.
    Five-source equal weight = SP+ + FPI + TeamRankings + Sagarin + DRatings.
  </div>
</section>

<section class="histCard histModelCard" id="historicalTotalsModelPerformance">
  <div class="histHead">
    <div>
      <h2>Historical Totals Model Performance</h2>
      <small>2021–2025 · Sunday 9 PM ET</small>
    </div>
    <small>Composite vs individual totals systems</small>
  </div>

  <div class="histModelViewControls" id="histTotalsModelViews">
    <button class="histModelView active"
      data-hist-totals-model-view="all">All Games</button>
    <button class="histModelView"
      data-hist-totals-model-view="3.0">3.0+ Edge</button>
  </div>

  <div class="histModelControls" id="histTotalsModelYears">
    <button class="histModelYear active"
      data-hist-totals-model-year="2021-2025">2021–2025</button>
    <button class="histModelYear"
      data-hist-totals-model-year="2021">2021</button>
    <button class="histModelYear"
      data-hist-totals-model-year="2022">2022</button>
    <button class="histModelYear"
      data-hist-totals-model-year="2023">2023</button>
    <button class="histModelYear"
      data-hist-totals-model-year="2024">2024</button>
    <button class="histModelYear"
      data-hist-totals-model-year="2025">2025</button>
  </div>

  <div class="histTableWrap">
    <table class="histTable">
      <thead>
        <tr>
          <th>Model</th>
          <th>Games</th>
          <th>Record</th>
          <th>O/U Win %</th>
          <th>ROI</th>
          <th>Beat Closing Line</th>
          <th>Avg CLV</th>
          <th>
            MAE
            <span class="histHelp"
              title="Mean absolute error between the projected total and actual final total. Lower is better.">?</span>
          </th>
          <th>
            Bias
            <span class="histHelp"
              title="Average projected total minus actual final total. Closest to zero is best calibrated; positive means the model projected too many points and negative means too few.">?</span>
          </th>
        </tr>
      </thead>

      <tbody id="historicalTotalsModelRows">
        {render_historical_totals_model_rows()}
      </tbody>
    </table>
  </div>

  <div class="histModelMeta">
    PRIMARY = 40% SP+ + 40% Massey Dual + 20% Sagarin.
    CORE = 50% SP+ + 50% Massey Dual.
    All Games includes every directional model selection with an executable Sunday 9 PM ET totals market observation.
    3.0+ Edge includes only games where that model differed from the market by at least 3 points.
    DRatings is retained for reference but has materially smaller provenance-safe historical coverage.
  </div>
</section>

<script>
(function(){{
  const root=document.getElementById('historicalTotalsModelPerformance');
  if(!root)return;

  const rows=[...root.querySelectorAll('.histTotalsModelRow')];
  const viewButtons=[...root.querySelectorAll('[data-hist-totals-model-view]')];
  const yearButtons=[...root.querySelectorAll('[data-hist-totals-model-year]')];

  let currentView='all';
  let currentYear='2021-2025';

  function render(){{
    rows.forEach(row=>{{
      const show=
        row.dataset.histTotalsModelView===currentView &&
        row.dataset.histTotalsModelScope===currentYear;

      row.style.display=show ? '' : 'none';
    }});

    viewButtons.forEach(btn=>{{
      btn.classList.toggle(
        'active',
        btn.dataset.histTotalsModelView===currentView
      );
    }});

    yearButtons.forEach(btn=>{{
      btn.classList.toggle(
        'active',
        btn.dataset.histTotalsModelYear===currentYear
      );
    }});
  }}

  viewButtons.forEach(btn=>{{
    btn.addEventListener('click',()=>{{
      currentView=btn.dataset.histTotalsModelView;
      render();
    }});
  }});

  yearButtons.forEach(btn=>{{
    btn.addEventListener('click',()=>{{
      currentYear=btn.dataset.histTotalsModelYear;
      render();
    }});
  }});

  render();
}})();
</script>

<script>
(function(){{
  const root=document.getElementById('historicalModelPerformance');
  if(!root)return;

  const viewButtons=[
    ...root.querySelectorAll('[data-hist-model-view]')
  ];
  const yearButtons=[
    ...root.querySelectorAll('[data-hist-model-year]')
  ];
  const rows=[
    ...root.querySelectorAll(
      'tr[data-hist-model-view][data-hist-model-scope]'
    )
  ];

  let activeView='all';
  let activeYear='2021-2025';

  function render(){{
    viewButtons.forEach(b=>b.classList.toggle(
      'active',
      b.dataset.histModelView===activeView
    ));

    yearButtons.forEach(b=>b.classList.toggle(
      'active',
      b.dataset.histModelYear===activeYear
    ));

    rows.forEach(r=>{{
      r.style.display =
        r.dataset.histModelView===activeView
        && r.dataset.histModelScope===activeYear
          ? ''
          : 'none';
    }});
  }}

  viewButtons.forEach(b=>b.addEventListener(
    'click',
    ()=>{{
      activeView=b.dataset.histModelView;
      render();
    }}
  ));

  yearButtons.forEach(b=>b.addEventListener(
    'click',
    ()=>{{
      activeYear=b.dataset.histModelYear;
      render();
    }}
  ));

  render();
}})();
</script>
"""

BETTING_BLOCK = BETTING_BLOCK.replace(
    "<!-- HISTORICAL_BETTING_SECTION_END -->",
    MODEL_COMPARISON_BLOCK
    + "\\n<!-- HISTORICAL_BETTING_SECTION_END -->",
    1,
)

OPENERS_BLOCK = f"""
<!-- MODERN_KEY_NUMBERS_START -->
<section class="keyRef" id="modernKeyNumbers">
  <div class="keyRefTop">
    <b>Modern NCAAF Key Numbers</b>
    <small>2022–2025 final-score landing frequency</small>
  </div>
  <div class="keyRefGrid">
    <div class="keyNumGroup">
      <span class="keyNumLabel">Spread</span>
      {render_key_number_items(spread_top5)}
    </div>
    <div class="keyNumGroup">
      <span class="keyNumLabel">Totals</span>
      {render_key_number_items(total_top5)}
    </div>
  </div>
</section>
<!-- MODERN_KEY_NUMBERS_END -->
"""

def replace_marked(text, start, end, block):
    pat = re.compile(re.escape(start)+r".*?"+re.escape(end), re.S)
    if pat.search(text):
        return pat.sub(block.strip(), text, count=1)
    return None

def ensure_css(text):
    replaced = replace_marked(
        text,
        "<!-- HISTORICAL_BETTING_UI_CSS_START -->",
        "<!-- HISTORICAL_BETTING_UI_CSS_END -->",
        CSS
    )
    if replaced is not None:
        return replaced
    if "</head>" not in text:
        raise RuntimeError("missing </head>")
    return text.replace("</head>", CSS+"\n</head>", 1)

def patch_betting(text):
    text = ensure_css(text)
    replaced = replace_marked(
        text,
        "<!-- HISTORICAL_BETTING_SECTION_START -->",
        "<!-- HISTORICAL_BETTING_SECTION_END -->",
        BETTING_BLOCK
    )
    if replaced is not None:
        return replaced

    # Preferred insertion immediately after hero.
    hero = re.compile(r'(<section class="hero">.*?</section>)', re.S)
    m = hero.search(text)
    if m:
        return text[:m.end()]+"\n"+BETTING_BLOCK+text[m.end():]

    # Fallback before first main content section after page heading.
    body = text.find("<body")
    if body < 0:
        raise RuntimeError("Betting insertion anchor not found")
    first_section = text.find("<section", body)
    if first_section < 0:
        raise RuntimeError("Betting insertion anchor not found")
    end = text.find("</section>", first_section)
    if end < 0:
        raise RuntimeError("Betting first section malformed")
    end += len("</section>")
    return text[:end]+"\n"+BETTING_BLOCK+text[end:]

def patch_openers(text):
    text = ensure_css(text)
    replaced = replace_marked(
        text,
        "<!-- MODERN_KEY_NUMBERS_START -->",
        "<!-- MODERN_KEY_NUMBERS_END -->",
        OPENERS_BLOCK
    )
    if replaced is not None:
        return replaced

    hero = re.compile(r'(<section class="hero">.*?</section>)', re.S)
    m = hero.search(text)
    if m:
        return text[:m.end()]+"\n"+OPENERS_BLOCK+text[m.end():]

    # Fallback: after top/header shell.
    close_header = text.find("</header>")
    if close_header >= 0:
        close_header += len("</header>")
        return text[:close_header]+"\n"+OPENERS_BLOCK+text[close_header:]

    body = text.find("<body")
    if body < 0:
        raise RuntimeError("Openers insertion anchor not found")
    gt = text.find(">", body)
    return text[:gt+1]+"\n"+OPENERS_BLOCK+text[gt+1:]

stamp=datetime.now().strftime("%Y%m%d_%H%M%S")

for path,patcher in [(OPENERS,patch_openers),(BETTING,patch_betting)]:
    original=path.read_text()
    updated=patcher(original)
    if updated == original:
        print(f"UNCHANGED: {path}")
        continue
    backup=path.with_name(path.name+f".before_history_keys_{stamp}.bak")
    shutil.copy2(path,backup)
    path.write_text(updated)
    print(f"UPDATED: {path}")
    print(f"BACKUP : {backup}")

# Validate exact source owners only.
checks = [
    ("Openers source owner", "MODERN_KEY_NUMBERS_START" in OPENERS.read_text()),
    ("Openers spread keys", "Modern NCAAF Key Numbers" in OPENERS.read_text()),
    ("Openers totals", "Totals" in OPENERS.read_text()),
    ("Betting source owner", "HISTORICAL_BETTING_SECTION_START" in BETTING.read_text()),
    ("Betting 3.5+", "3.5+" in BETTING.read_text()),
    ("Betting Beat Closing Line", "Beat Closing Line" in BETTING.read_text()),
    ("Betting CLV-Implied EV", "CLV-Implied EV" in BETTING.read_text()),
    ("Betting Won Line Move", "Won Line Move" in BETTING.read_text()),
    ("Betting ROI badge", "BET ROI+" in BETTING.read_text()),
    ("Betting EV badge", "BET EV+" in BETTING.read_text()),
    ("Betting historical model comparison", "Historical Model Performance" in BETTING.read_text()),
    ("Betting five-source model row", "Five-source equal weight" in BETTING.read_text()),
    ("Betting all-games model view", 'data-hist-model-view="all"' in BETTING.read_text()),
    ("Betting 3.0 model view", 'data-hist-model-view="3.0"' in BETTING.read_text()),
    ("Betting MAE", ">MAE" in BETTING.read_text() or "MAE" in BETTING.read_text()),
    ("Betting Bias", ">Bias" in BETTING.read_text() or "Bias" in BETTING.read_text()),
    ("Betting 2025 model selector", 'data-hist-model-year="2025"' in BETTING.read_text()),
    ("Betting totals edge validation", "Historical Totals Edge Validation" in BETTING.read_text()),
    ("Betting totals primary model", "40% SP+ / 40% Massey Dual / 20% Sagarin" in BETTING.read_text()),
    ("Betting totals model comparison", "Historical Totals Model Performance" in BETTING.read_text()),
    ("Betting totals primary badge", ">PRIMARY<" in BETTING.read_text()),
    ("Betting totals core badge", ">CORE<" in BETTING.read_text()),
    ("Betting totals all-games view", 'data-hist-totals-model-view="all"' in BETTING.read_text()),
    ("Betting totals 3.0 view", 'data-hist-totals-model-view="3.0"' in BETTING.read_text()),
    ("Betting totals 2025 selector", 'data-hist-totals-model-year="2025"' in BETTING.read_text()),
]
failed=[]
for label,ok in checks:
    print(f"{'PASS' if ok else 'FAIL'}: {label}")
    if not ok:
        failed.append(label)

if failed:
    raise SystemExit("STOP: validation failed: "+", ".join(failed))

print("\nINSTALL COMPLETE")
print("Changed only:")
print(" ", OPENERS)
print(" ", BETTING)
print("Nothing was published and no runtime files were modified.")
print("\nNext: inspect git diff before any build/publish:")
print("git diff -- openers.html betting_v2.html")
