#!/usr/bin/env python3
"""Install validated full-game returning-production rules into Openers pages.

This version embeds the validated 2026 signal payload directly in each HTML
page. It does not depend on the page's init() or fetch() implementation.

Installed full-game rules
-------------------------
1. P4_G6_EITHER_COMPONENT_25_PLUS
   Primary directional edge: 50-31 ATS (61.7%).

2. P4_G6_DEFENSE_15_PLUS
   Supporting context only: 46-32 ATS (59.0%).

3. P4_P4_OVERALL_15_TO_24_9
   Directional only when the RP team is an underdog:
   underdogs 12-5 ATS; favorites 17-17-1 ATS (context only).

Exploratory first-half RP research is intentionally excluded.

Safety
------
- Preflights every discovered Openers HTML file before writing any file.
- Creates timestamped backups.
- Is idempotent.
- Handles both the newer source layout and older published rank-gap layout.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import re
import shutil
import sys
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path.home() / "NCAAF_AUTO"

SOURCE_CSV = (
    ROOT
    / "data/signals/returning_production_validated_matches_2026_with_market_role.csv"
)

PAGE_CANDIDATES = [
    ROOT / "openers_v2.html",
    ROOT / "openers.html",
    ROOT / "build/public_site/openers.html",
    Path.home() / "Sites/NCAAF_SITE/openers.html",
]

JSON_RELATIVE = Path(
    "data/site/returning_production_validated_signals_2026.json"
)

JSON_TARGETS = [
    ROOT / JSON_RELATIVE,
    ROOT / "build/public_site" / JSON_RELATIVE,
    Path.home() / "Sites/NCAAF_SITE" / JSON_RELATIVE,
]

DAILY_SCRIPT = ROOT / "daily_market_update.sh"
PROJECT_INSTALLER = (
    ROOT / "scripts/site/install_validated_full_game_rp_openers.py"
)

JS_START = "/* VALIDATED_FULL_GAME_RP_OPENERS_START */"
JS_END = "/* VALIDATED_FULL_GAME_RP_OPENERS_END */"
CSS_START = "/* VALIDATED_FULL_GAME_RP_OPENERS_CSS_START */"
CSS_END = "/* VALIDATED_FULL_GAME_RP_OPENERS_CSS_END */"


def clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return ""
    return str(value).strip()


def number(value: Any) -> float | None:
    try:
        result = float(value)
        if np.isfinite(result):
            return result
    except (TypeError, ValueError):
        pass
    return None


def consolidate_signals(frame: pd.DataFrame) -> list[dict[str, Any]]:
    required = {
        "game_id",
        "week",
        "date",
        "away_team",
        "home_team",
        "signal_team",
        "signal_opponent",
        "rule_key",
        "rule_label",
        "rule_priority",
        "overall_rp_edge",
        "offense_vs_defense_edge",
        "defense_vs_offense_edge",
    }

    missing = sorted(required - set(frame.columns))
    if missing:
        raise KeyError(f"Signal CSV is missing columns: {missing}")

    work = frame.copy()
    work["rule_priority"] = pd.to_numeric(
        work["rule_priority"],
        errors="coerce",
    )
    work.sort_values(
        ["game_id", "signal_team", "rule_priority"],
        inplace=True,
    )

    signals: list[dict[str, Any]] = []

    for (game_id, signal_team), group in work.groupby(
        ["game_id", "signal_team"],
        dropna=False,
    ):
        rule_keys = set(group["rule_key"].astype(str))

        if "P4_G6_EITHER_COMPONENT_25_PLUS" in rule_keys:
            primary_key = "P4_G6_EITHER_COMPONENT_25_PLUS"
            primary = group[group["rule_key"].eq(primary_key)].iloc[0]
            title = "Strong RP mismatch"
            behavior = "directional"
            record = "50-31"
            ats_pct = 61.7
            games = 81

        elif "P4_P4_OVERALL_15_TO_24_9" in rule_keys:
            primary_key = "P4_P4_OVERALL_15_TO_24_9"
            primary = group[group["rule_key"].eq(primary_key)].iloc[0]
            title = "Role-dependent RP edge"
            behavior = "underdog_only"
            record = "29-22-1"
            ats_pct = 56.9
            games = 52

        elif "P4_G6_DEFENSE_15_PLUS" in rule_keys:
            primary_key = "P4_G6_DEFENSE_15_PLUS"
            primary = group[group["rule_key"].eq(primary_key)].iloc[0]
            title = "Defensive continuity support"
            behavior = "context_only"
            record = "46-32"
            ats_pct = 59.0
            games = 78

        else:
            continue

        signals.append(
            {
                "game_id": clean(game_id),
                "week": int(float(primary["week"])),
                "date": clean(primary["date"]),
                "away_team": clean(primary["away_team"]),
                "home_team": clean(primary["home_team"]),
                "signal_team": clean(signal_team),
                "signal_opponent": clean(primary["signal_opponent"]),
                "primary_rule_key": primary_key,
                "primary_rule_label": clean(primary["rule_label"]),
                "title": title,
                "production_behavior": behavior,
                "overall_record": record,
                "overall_ats_pct": ats_pct,
                "overall_games": games,
                "overall_rp_edge": number(primary["overall_rp_edge"]),
                "offense_vs_defense_edge": number(
                    primary["offense_vs_defense_edge"]
                ),
                "defense_vs_offense_edge": number(
                    primary["defense_vs_offense_edge"]
                ),
                "has_defensive_support": (
                    "P4_G6_DEFENSE_15_PLUS" in rule_keys
                ),
                "matched_rule_count": int(len(group)),
                "history_window": "2021-2025, Weeks 1-4",
            }
        )

    return sorted(
        signals,
        key=lambda row: (
            row["week"],
            row["date"],
            row["away_team"],
            row["home_team"],
            row["signal_team"],
        ),
    )


def build_payload(signals: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "meta": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "history_window": "2021-2025, Weeks 1-4",
            "signal_rows": len(signals),
            "unique_games": len({row["game_id"] for row in signals}),
            "first_half_rules_included": False,
            "rules": {
                "P4_G6_EITHER_COMPONENT_25_PLUS": {
                    "status": "Primary full-game directional signal",
                    "record": "50-31",
                    "ats_pct": 61.7,
                },
                "P4_G6_DEFENSE_15_PLUS": {
                    "status": "Supporting context only",
                    "record": "46-32",
                    "ats_pct": 59.0,
                },
                "P4_P4_OVERALL_15_TO_24_9": {
                    "status": "Directional only when RP team is underdog",
                    "underdog_record": "12-5",
                    "underdog_ats_pct": 70.6,
                    "favorite_record": "17-17-1",
                    "favorite_ats_pct": 50.0,
                },
            },
        },
        "signals": signals,
    }


def strip_marked_block(
    text: str,
    start_marker: str,
    end_marker: str,
) -> str:
    return re.sub(
        re.escape(start_marker)
        + r".*?"
        + re.escape(end_marker)
        + r"\s*",
        "",
        text,
        flags=re.S,
    )


def find_js_function_span(
    text: str,
    function_name: str,
) -> tuple[int, int] | None:
    match = re.search(
        rf"\bfunction\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{",
        text,
    )
    if not match:
        return None

    opening_brace = text.find("{", match.start())
    depth = 0
    in_string = False
    quote = ""
    escaped = False

    for index in range(opening_brace, len(text)):
        char = text[index]

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
                return match.start(), index + 1

    raise ValueError(f"Unclosed JavaScript function: {function_name}")


OLD_RANK_GAP_PATTERNS = [
    re.compile(
        r"const\s+ar\s*=\s*r\.teams\.away\.returning_production"
        r"\?\.overall_rank\s*,\s*hr\s*=\s*r\.teams\.home"
        r"\.returning_production\?\.overall_rank\s*;"
        r"\s*rows\.push\("
        r"ar&&hr&&Math\.abs\(ar-hr\)>=20"
        r"\?\{category:'Returning prod\.',team:ar<hr"
        r"\?r\.game\.away_team:r\.game\.home_team,"
        r"detail:`#\$\{Math\.min\(ar,hr\)\} vs #\$\{Math\.max\(ar,hr\)\} "
        r"overall returning production`\}"
        r":\{category:'Returning prod\.',detail:'No major overall-rank gap'\}"
        r"\)\s*;",
        flags=re.S,
    ),
    re.compile(
        r"rows\.push\(\s*ar\s*&&\s*hr\s*&&\s*Math\.abs\(ar-hr\)\s*>=\s*20"
        r".*?No major overall-rank gap.*?\)\s*;",
        flags=re.S,
    ),
]


def build_js_block(payload: dict[str, Any]) -> str:
    payload_json = json.dumps(
        payload,
        separators=(",", ":"),
        ensure_ascii=True,
    )

    return f"""
{JS_START}
const VALIDATED_FULL_GAME_RP={payload_json};
const VALIDATED_FULL_GAME_RP_BY_ID=new Map();
const VALIDATED_FULL_GAME_RP_BY_MATCHUP=new Map();

function validatedRpNormalizeTeam(value){{
  return String(value??'')
    .toLowerCase()
    .replace(/&/g,' and ')
    .replace(/[^a-z0-9]+/g,' ')
    .trim();
}}

function validatedRpMatchupKey(away,home){{
  return [
    validatedRpNormalizeTeam(away),
    validatedRpNormalizeTeam(home)
  ].sort().join('||');
}}

for(const row of (VALIDATED_FULL_GAME_RP.signals||[])){{
  const gameId=String(row.game_id||'');

  if(gameId){{
    if(!VALIDATED_FULL_GAME_RP_BY_ID.has(gameId)){{
      VALIDATED_FULL_GAME_RP_BY_ID.set(gameId,[]);
    }}
    VALIDATED_FULL_GAME_RP_BY_ID.get(gameId).push(row);
  }}

  const key=validatedRpMatchupKey(row.away_team,row.home_team);
  if(!VALIDATED_FULL_GAME_RP_BY_MATCHUP.has(key)){{
    VALIDATED_FULL_GAME_RP_BY_MATCHUP.set(key,[]);
  }}
  VALIDATED_FULL_GAME_RP_BY_MATCHUP.get(key).push(row);
}}

function validatedRpRows(r){{
  const gameId=String(r?.game?.game_id||'');
  const byId=VALIDATED_FULL_GAME_RP_BY_ID.get(gameId)||[];
  if(byId.length) return byId;

  const key=validatedRpMatchupKey(
    r?.game?.away_team,
    r?.game?.home_team
  );
  return VALIDATED_FULL_GAME_RP_BY_MATCHUP.get(key)||[];
}}

function validatedRpSignal(r){{
  const rows=validatedRpRows(r);
  return rows.length?rows[0]:null;
}}

function validatedRpNumber(value){{
  const n=Number(value);
  return Number.isFinite(n)?n:null;
}}

function validatedRpHomeMarketSpread(r){{
  const directCandidates=[
    r?.market_spread_home,
    r?.market?.spread_home,
    r?.market?.home_spread,
    r?.market?.spread?.home_line,
    r?.market?.spread?.line_home,
    r?.market?.spread?.current_home,
    r?.market?.spread?.consensus_home,
    r?.market?.current?.spread_home
  ];

  for(const value of directCandidates){{
    const n=validatedRpNumber(value);
    if(n!==null) return n;
  }}

  const gameCandidates=[
    r?.game?.market_spread_home,
    r?.game?.spread_home,
    r?.game?.current_spread_home
  ];

  for(const value of gameCandidates){{
    const n=validatedRpNumber(value);
    if(n!==null) return n;
  }}

  return null;
}}

function validatedRpTeamSpread(r,signal){{
  const homeSpread=validatedRpHomeMarketSpread(r);
  if(homeSpread===null) return null;

  if(signal.signal_team===r?.game?.home_team) return homeSpread;
  if(signal.signal_team===r?.game?.away_team) return -homeSpread;
  return null;
}}

function validatedRpRole(spread){{
  if(spread===null) return 'Unknown';
  if(spread<0) return 'Favorite';
  if(spread>0) return 'Underdog';
  return "Pick'em";
}}

function validatedRpSigned(value,digits=0){{
  const n=validatedRpNumber(value);
  if(n===null) return '—';
  return `${{n>0?'+':''}}${{n.toFixed(digits)}}`;
}}

function validatedRpSpreadText(spread){{
  if(spread===null) return 'market role pending';
  return `${{spread>0?'+':''}}${{Number(spread).toFixed(1)}}`;
}}

function validatedRpEvaluation(r){{
  const signal=validatedRpSignal(r);

  if(!signal){{
    return {{
      signal:null,
      active:false,
      team:null,
      label:'No validated full-game RP rule',
      detail:'No qualifying 2021-2025 returning-production rule',
      status:'none'
    }};
  }}

  const spread=validatedRpTeamSpread(r,signal);
  const role=validatedRpRole(spread);
  const edges=
    `Overall ${{validatedRpSigned(signal.overall_rp_edge)}} · `+
    `Off vs Def ${{validatedRpSigned(signal.offense_vs_defense_edge)}} · `+
    `Def vs Off ${{validatedRpSigned(signal.defense_vs_offense_edge)}}`;

  if(signal.primary_rule_key==='P4_G6_EITHER_COMPONENT_25_PLUS'){{
    return {{
      signal,
      active:true,
      team:signal.signal_team,
      label:'Primary full-game RP lean',
      detail:
        `${{signal.signal_team}} · ${{edges}} · `+
        `50-31 ATS (61.7%, n=81) · `+
        `${{role}}, ${{validatedRpSpreadText(spread)}}`,
      status:'positive'
    }};
  }}

  if(signal.primary_rule_key==='P4_G6_DEFENSE_15_PLUS'){{
    return {{
      signal,
      active:false,
      team:null,
      label:'Supporting RP context',
      detail:
        `${{signal.signal_team}} defensive continuity · ${{edges}} · `+
        `46-32 ATS (59.0%, n=78), supporting context only`,
      status:'supporting'
    }};
  }}

  if(signal.primary_rule_key==='P4_P4_OVERALL_15_TO_24_9'){{
    if(role==='Underdog'){{
      return {{
        signal,
        active:true,
        team:signal.signal_team,
        label:'RP-underdog full-game lean',
        detail:
          `${{signal.signal_team}} · ${{edges}} · `+
          `RP-edge underdogs 12-5 ATS (70.6%, n=17) · `+
          `${{validatedRpSpreadText(spread)}}`,
        status:'positive'
      }};
    }}

    if(role==='Favorite'){{
      return {{
        signal,
        active:false,
        team:null,
        label:'RP context only',
        detail:
          `${{signal.signal_team}} owns the RP edge but is favored · ${{edges}} · `+
          `RP-edge favorites 17-17-1 ATS (50.0%, n=35)`,
        status:'neutral'
      }};
    }}

    return {{
      signal,
      active:false,
      team:null,
      label:'RP line watch',
      detail:
        `${{signal.signal_team}} owns the RP edge · ${{edges}} · `+
        `signal activates only if ${{signal.signal_team}} is the underdog`,
      status:'watch'
    }};
  }}

  return {{
    signal,
    active:false,
    team:null,
    label:'RP context',
    detail:`${{signal.signal_team}} · ${{edges}}`,
    status:'neutral'
  }};
}}

function returningProductionContext(r){{
  const evaluation=validatedRpEvaluation(r);
  return {{
    category:'Returning prod.',
    ...(evaluation.active&&evaluation.team
      ? {{team:evaluation.team}}
      : {{}}),
    detail:`${{evaluation.label}}: ${{evaluation.detail}}`,
    rpValidated:!!evaluation.signal,
    rpStatus:evaluation.status
  }};
}}

function validatedRpDrawerHtml(r){{
  const evaluation=validatedRpEvaluation(r);
  const signal=evaluation.signal;
  if(!signal) return '';

  const safe=(value)=>{{
    if(typeof esc==='function') return esc(value);
    return String(value??'')
      .replace(/&/g,'&amp;')
      .replace(/</g,'&lt;')
      .replace(/>/g,'&gt;')
      .replace(/"/g,'&quot;');
  }};

  return `
    <div class="validatedFullGameRpCard ${{safe(evaluation.status)}}">
      <div class="validatedFullGameRpHead">
        <span class="validatedFullGameRpBadge">2021-25 FULL GAME RP</span>
        <b>${{safe(evaluation.label)}}</b>
      </div>
      <div class="validatedFullGameRpTeam">
        ${{safe(signal.signal_team)}}
      </div>
      <div class="validatedFullGameRpRule">
        ${{safe(signal.title)}} · ${{safe(signal.primary_rule_label)}}
      </div>
      <div class="validatedFullGameRpEdges">
        <span>Overall <b>${{safe(validatedRpSigned(signal.overall_rp_edge))}}</b></span>
        <span>Off vs Def <b>${{safe(validatedRpSigned(signal.offense_vs_defense_edge))}}</b></span>
        <span>Def vs Off <b>${{safe(validatedRpSigned(signal.defense_vs_offense_edge))}}</b></span>
      </div>
      <div class="validatedFullGameRpRead">
        ${{safe(evaluation.detail)}}
      </div>
      <div class="validatedFullGameRpHistory">
        ${{safe(signal.history_window)}} · First-half RP research excluded
      </div>
    </div>
  `;
}}
{JS_END}
"""


CSS_BLOCK = f"""
{CSS_START}
.validatedFullGameRpCard{{
  border:1px solid #37618f;
  background:#0a1e3a;
  border-radius:10px;
  padding:10px;
  margin:0 0 8px;
}}
.validatedFullGameRpCard.positive{{
  border-color:#27865f;
  background:#0a2a2a;
}}
.validatedFullGameRpCard.supporting{{
  border-color:#7b6b3c;
  background:#292514;
}}
.validatedFullGameRpCard.neutral,
.validatedFullGameRpCard.watch{{
  border-color:#53657d;
  background:#172130;
}}
.validatedFullGameRpHead{{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
}}
.validatedFullGameRpBadge{{
  display:inline-flex;
  border-radius:999px;
  padding:3px 7px;
  font-size:9px;
  font-weight:950;
  color:#c9dcff;
  border:1px solid #4d78a8;
  background:#15345d;
}}
.validatedFullGameRpCard.positive .validatedFullGameRpBadge{{
  color:#baf8d6;
  border-color:#27865f;
  background:#104b38;
}}
.validatedFullGameRpTeam{{
  margin-top:7px;
  color:#f4f7ff;
  font-weight:900;
}}
.validatedFullGameRpRule,
.validatedFullGameRpHistory,
.validatedFullGameRpRead{{
  margin-top:5px;
  color:#afc1dc;
  font-size:10px;
}}
.validatedFullGameRpRead{{
  color:#f4f7ff;
  font-weight:700;
}}
.validatedFullGameRpEdges{{
  display:flex;
  gap:6px;
  flex-wrap:wrap;
  margin-top:7px;
}}
.validatedFullGameRpEdges span{{
  border:1px solid #315780;
  background:#081932;
  border-radius:7px;
  padding:5px 7px;
  color:#a9bddb;
  font-size:9px;
}}
.validatedFullGameRpEdges b{{
  color:#f4f7ff;
}}
{CSS_END}
"""


def replace_old_rank_gap(text: str) -> tuple[str, bool]:
    for pattern in OLD_RANK_GAP_PATTERNS:
        updated, count = pattern.subn(
            "rows.push(returningProductionContext(r));",
            text,
            count=1,
        )
        if count:
            return updated, True
    return text, False


def add_drawer_card(text: str) -> tuple[str, bool]:
    if "${validatedRpDrawerHtml(r)}" in text:
        return text, False

    insertion_patterns = [
        (
            '<div class="detail"><h3>Consolidated betting context</h3>${contextHtml(r)}',
            '<div class="detail"><h3>Consolidated betting context</h3>'
            '${validatedRpDrawerHtml(r)}${contextHtml(r)}',
        ),
        (
            '<h3>Consolidated betting context</h3>${contextHtml(r)}',
            '<h3>Consolidated betting context</h3>'
            '${validatedRpDrawerHtml(r)}${contextHtml(r)}',
        ),
    ]

    for old, new in insertion_patterns:
        if old in text:
            return text.replace(old, new, 1), True

    return text, False


def patch_page(
    path: Path,
    original: str,
    payload: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    text = strip_marked_block(original, JS_START, JS_END)
    text = strip_marked_block(text, CSS_START, CSS_END)

    if "</style>" not in text:
        raise RuntimeError(f"Missing </style> in {path}")

    advantage_pos = text.find("function advantageRows")
    if advantage_pos < 0:
        raise RuntimeError(f"Missing advantageRows() in {path}")

    source_span = find_js_function_span(
        text,
        "returningProductionContext",
    )
    had_source_function = source_span is not None

    old_rank_gap_present = any(
        pattern.search(text)
        for pattern in OLD_RANK_GAP_PATTERNS
    )

    already_calls_context = bool(
        re.search(
            r"rows\.push\(\s*returningProductionContext\(r\)\s*\)\s*;",
            text,
        )
    )

    if source_span is not None:
        start, end = source_span
        text = text[:start] + text[end:]
        advantage_pos = text.find("function advantageRows")

    elif old_rank_gap_present:
        text, replaced = replace_old_rank_gap(text)
        if not replaced:
            raise RuntimeError(
                f"Old RP rank-gap logic was detected but not replaced in {path}"
            )
        advantage_pos = text.find("function advantageRows")

    elif not already_calls_context:
        raise RuntimeError(
            f"Unsupported Returning Production layout in {path}"
        )

    text = text.replace(
        "</style>",
        CSS_BLOCK + "\n</style>",
        1,
    )

    js_block = build_js_block(payload)
    advantage_pos = text.find("function advantageRows")
    text = (
        text[:advantage_pos]
        + js_block
        + "\n"
        + text[advantage_pos:]
    )

    # Ensure advantageRows actually uses the validated context.
    if not re.search(
        r"rows\.push\(\s*returningProductionContext\(r\)\s*\)\s*;",
        text,
    ):
        # Add it immediately after the opening brace of advantageRows.
        span = find_js_function_span(text, "advantageRows")
        if span is None:
            raise RuntimeError(
                f"Could not relocate advantageRows() in {path}"
            )

        function_start, _ = span
        opening_brace = text.find("{", function_start)
        text = (
            text[:opening_brace + 1]
            + "\n  rows.push(returningProductionContext(r));"
            + text[opening_brace + 1:]
        )

    text, drawer_added = add_drawer_card(text)

    checks = {
        "js_marker": JS_START in text and JS_END in text,
        "css_marker": CSS_START in text and CSS_END in text,
        "validated_payload_embedded": (
            "const VALIDATED_FULL_GAME_RP=" in text
        ),
        "validated_context_function": (
            "function returningProductionContext(r)" in text
        ),
        "advantage_rows_call": bool(
            re.search(
                r"rows\.push\(\s*returningProductionContext\(r\)\s*\)\s*;",
                text,
            )
        ),
        "old_rank_gap_removed": not any(
            pattern.search(text)
            for pattern in OLD_RANK_GAP_PATTERNS
        ),
        "first_half_excluded": (
            "First-half RP research excluded" in text
        ),
    }

    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError(
            f"Post-patch validation failed for {path}: {failed}"
        )

    return text, {
        "path": str(path),
        "had_source_function": had_source_function,
        "had_old_rank_gap": old_rank_gap_present,
        "drawer_added": drawer_added,
        "size_before": len(original),
        "size_after": len(text),
    }


def backup_destination(path: Path, timestamp: str) -> Path:
    base = (
        ROOT
        / "backups/validated_full_game_rp_openers"
        / timestamp
    )

    try:
        relative = path.relative_to(ROOT)
        destination = base / relative
    except ValueError:
        destination = base / "external" / path.name

    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def update_daily_script(timestamp: str) -> bool:
    if not DAILY_SCRIPT.exists():
        return False

    command = (
        "python3 scripts/site/install_validated_full_game_rp_openers.py"
    )
    text = DAILY_SCRIPT.read_text(encoding="utf-8", errors="ignore")

    if command in text:
        return False

    backup = (
        ROOT
        / "backups/validated_full_game_rp_openers"
        / timestamp
        / "daily_market_update.sh"
    )
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DAILY_SCRIPT, backup)

    block = f"""

# Refresh validated 2021-2025 full-game RP context on Openers pages.
# Exploratory first-half RP research is intentionally excluded.
if [ -f scripts/site/install_validated_full_game_rp_openers.py ]; then
  {command}
fi
"""

    DAILY_SCRIPT.write_text(
        text.rstrip() + block + "\n",
        encoding="utf-8",
    )
    return True


def main() -> None:
    if not SOURCE_CSV.exists():
        raise FileNotFoundError(SOURCE_CSV)

    pages = [path for path in PAGE_CANDIDATES if path.exists()]
    if not pages:
        raise FileNotFoundError(
            "No Openers HTML files were found"
        )

    source = pd.read_csv(SOURCE_CSV)
    signals = consolidate_signals(source)
    payload = build_payload(signals)

    # Preflight all pages before writing anything.
    patched_pages: dict[Path, str] = {}
    page_metadata: list[dict[str, Any]] = []

    for page in pages:
        original = page.read_text(
            encoding="utf-8",
            errors="ignore",
        )
        patched, metadata = patch_page(
            page,
            original,
            payload,
        )
        patched_pages[page] = patched
        page_metadata.append(metadata)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for page, patched in patched_pages.items():
        backup = backup_destination(page, timestamp)
        shutil.copy2(page, backup)
        page.write_text(patched, encoding="utf-8")
        print(f"patched: {page}")
        print(f"backup:  {backup}")

    json_text = json.dumps(payload, indent=2) + "\n"

    for target in JSON_TARGETS:
        should_write = (
            target == JSON_TARGETS[0]
            or target.parent.parent.exists()
        )
        if should_write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json_text, encoding="utf-8")
            print(f"wrote JSON: {target}")

    daily_updated = update_daily_script(timestamp)

    print()
    print("VALIDATED FULL-GAME RP OPENERS INSTALLATION")
    print("=" * 100)
    print(f"Signal rows embedded: {len(signals)}")
    print(
        "Unique qualifying games: "
        f"{len({row['game_id'] for row in signals})}"
    )
    print(f"Openers pages patched: {len(patched_pages)}")
    print(f"Daily script hook added: {daily_updated}")
    print("First-half RP rules installed: False")

    for metadata in page_metadata:
        print()
        print(metadata["path"])
        print(
            "  existing returningProductionContext replaced: "
            f"{metadata['had_source_function']}"
        )
        print(
            "  old rank-gap logic replaced: "
            f"{metadata['had_old_rank_gap']}"
        )
        print(
            "  detail drawer card added: "
            f"{metadata['drawer_added']}"
        )
        print(
            f"  size: {metadata['size_before']} -> "
            f"{metadata['size_after']}"
        )

    print()
    print("Installed behavior:")
    print(
        "  P4_G6_EITHER_COMPONENT_25_PLUS: "
        "primary directional full-game edge"
    )
    print(
        "  P4_G6_DEFENSE_15_PLUS: "
        "supporting context only"
    )
    print(
        "  P4_P4_OVERALL_15_TO_24_9: "
        "directional only when RP team is underdog"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
