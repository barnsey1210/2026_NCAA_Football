#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import math
import os
import re
import shutil
import sys

import pandas as pd


ROOT = Path.home() / "NCAAF_AUTO"
SITE_REPO = Path.home() / "Sites/NCAAF_SITE"

SGO = ROOT / "data/markets/sgo/sgo_ncaaf_game_odds.csv"
ACTION = ROOT / "data/odds/actionnetwork_ncaaf_game_lines_2026.csv"

JSON_OUT = ROOT / "data/site/odds_screen.json"
HTML_OUT = ROOT / "odds.html"
BUILD_HTML = ROOT / "build/public_site/odds.html"
BUILD_JSON = ROOT / "build/public_site/data/site/odds_screen.json"
SITE_HTML = SITE_REPO / "odds.html"
SITE_JSON = SITE_REPO / "data/site/odds_screen.json"

BOOK_ORDER = ["DraftKings", "FanDuel", "BetMGM", "Caesars"]

BOOK_ALIASES = {
    "draftkings": "DraftKings",
    "draft kings": "DraftKings",
    "fanduel": "FanDuel",
    "fan duel": "FanDuel",
    "betmgm": "BetMGM",
    "bet mgm": "BetMGM",
    "caesars": "Caesars",
    "william hill": "Caesars",
}

COLUMN_CANDIDATES = {
    "book": ["book", "book_name", "sportsbook", "operator", "provider"],
    "market": ["market", "market_type", "market_name", "bet_type", "type"],
    "selection": ["selection", "outcome", "side", "label", "team", "participant"],
    "line": ["line", "points", "handicap", "spread", "total"],
    "price": ["price", "odds", "american_odds", "american_price"],
    "game_id": ["game_id", "event_id", "matchup_id"],
    "away_team": ["away_team", "away"],
    "home_team": ["home_team", "home"],
    "date": ["date", "game_date", "start_date"],
    "week": ["week", "game_week"],
}


def clean(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def number(value: Any) -> float | None:
    value = clean(value)
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except Exception:
        return None
    return result if math.isfinite(result) else None


def integer(value: Any) -> int | None:
    value = number(value)
    return int(value) if value is not None else None


def text(value: Any) -> str | None:
    value = clean(value)
    if value is None:
        return None
    result = str(value).strip()
    return result if result and result.lower() not in {"nan", "none"} else None


def canonical_book(value: Any) -> str | None:
    raw = text(value)
    if not raw:
        return None
    key = re.sub(r"[_\-]+", " ", raw.lower())
    key = re.sub(r"\s+", " ", key).strip()
    for alias, canonical in BOOK_ALIASES.items():
        if alias == key or alias in key:
            return canonical
    return raw


def normalized_team(value: Any) -> str:
    raw = text(value) or ""
    return re.sub(r"[^a-z0-9]+", "", raw.lower())


def game_key(date: Any, away: Any, home: Any) -> str:
    return "|".join([
        str(text(date) or "")[:10],
        normalized_team(away),
        normalized_team(home),
    ])


def first_existing(columns: list[str], candidates: list[str]) -> str | None:
    lower = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate in lower:
            return lower[candidate]
    for column in columns:
        low = column.lower()
        for candidate in candidates:
            if candidate in low:
                return column
    return None


def parse_action_matrix() -> tuple[dict[str, dict[str, dict[str, Any]]], dict[str, Any]]:
    audit: dict[str, Any] = {
        "source": str(ACTION),
        "exists": ACTION.exists(),
        "rows": 0,
        "detected_columns": {},
        "parsed_quotes": 0,
        "books": [],
    }
    matrix: dict[str, dict[str, dict[str, Any]]] = {}

    if not ACTION.exists():
        return matrix, audit

    df = pd.read_csv(ACTION, low_memory=False)
    audit["rows"] = len(df)
    columns = [str(c) for c in df.columns]
    detected = {
        name: first_existing(columns, candidates)
        for name, candidates in COLUMN_CANDIDATES.items()
    }
    audit["detected_columns"] = detected

    required = ["book", "market", "selection", "price", "away_team", "home_team", "date"]
    if any(not detected.get(name) for name in required):
        audit["warning"] = "Long-form matrix columns could not be fully detected."
        return matrix, audit

    books_seen = set()

    for _, row in df.iterrows():
        book = canonical_book(row.get(detected["book"]))
        if book not in BOOK_ORDER:
            continue

        market_raw = (text(row.get(detected["market"])) or "").lower()
        selection_raw = (text(row.get(detected["selection"])) or "").lower()
        away = text(row.get(detected["away_team"]))
        home = text(row.get(detected["home_team"]))
        date = text(row.get(detected["date"]))

        if not away or not home or not date:
            continue

        line_value = number(row.get(detected["line"])) if detected.get("line") else None
        price_value = number(row.get(detected["price"]))
        key = game_key(date, away, home)
        quote = matrix.setdefault(key, {}).setdefault(book, {})
        books_seen.add(book)

        is_spread = "spread" in market_raw or "handicap" in market_raw
        is_total = "total" in market_raw or "over" in market_raw or "under" in market_raw
        is_moneyline = (
            "moneyline" in market_raw
            or "money line" in market_raw
            or market_raw in {"ml", "money"}
        )

        away_norm = normalized_team(away)
        home_norm = normalized_team(home)
        selection_norm = normalized_team(selection_raw)

        if is_spread:
            if "away" in selection_raw or selection_norm == away_norm:
                quote["away_spread"] = line_value
                quote["away_spread_price"] = price_value
            elif "home" in selection_raw or selection_norm == home_norm:
                quote["home_spread"] = line_value
                quote["home_spread_price"] = price_value
        elif is_total:
            if "over" in selection_raw:
                quote["total"] = line_value
                quote["over_price"] = price_value
            elif "under" in selection_raw:
                quote["total"] = line_value
                quote["under_price"] = price_value
        elif is_moneyline:
            if "away" in selection_raw or selection_norm == away_norm:
                quote["away_moneyline"] = price_value
            elif "home" in selection_raw or selection_norm == home_norm:
                quote["home_moneyline"] = price_value

        audit["parsed_quotes"] += 1

    audit["books"] = sorted(books_seen)
    return matrix, audit


def build_payload() -> dict[str, Any]:
    if not SGO.exists():
        raise FileNotFoundError(SGO)

    sgo = pd.read_csv(SGO, low_memory=False)
    action_matrix, action_audit = parse_action_matrix()
    games = []

    for index, row in sgo.iterrows():
        date = text(row.get("date"))
        away = text(row.get("away_team"))
        home = text(row.get("home_team"))
        if not date or not away or not home:
            continue

        key = game_key(date, away, home)
        raw_books = text(row.get("market_books_available")) or ""
        books_available = []
        for token in raw_books.split(","):
            book = canonical_book(token)
            if book:
                books_available.append(book)

        home_line = number(row.get("market_spread_home"))
        away_line = -home_line if home_line is not None else None
        game_id = text(row.get("game_id")) or text(row.get("site_game_id")) or f"odds-{index+1}"

        games.append({
            "game_id": game_id,
            "date": date[:10],
            "week": integer(row.get("week")),
            "away_team": away,
            "home_team": home,
            "matchup_url": f"matchup.html?game_id={game_id}",
            "spread": {
                "open_home": number(row.get("market_spread_open_home")),
                "current_home": home_line,
                "current_away": away_line,
                "current_price": number(row.get("market_spread_price")),
                "current_book": canonical_book(row.get("market_spread_book")),
                "best_home_text": text(row.get("market_best_home_spread_text")),
                "best_home_price": number(row.get("market_best_home_spread_price")),
                "best_home_book": canonical_book(row.get("market_best_home_spread_book")),
                "best_away_text": text(row.get("market_best_away_spread_text")),
                "best_away_price": number(row.get("market_best_away_spread_price")),
                "best_away_book": canonical_book(row.get("market_best_away_spread_book")),
                "last_update": text(row.get("market_spread_last_update")),
            },
            "total": {
                "open": number(row.get("market_total_open")),
                "current": number(row.get("market_total")),
                "book": canonical_book(row.get("market_total_book")),
                "over_price": number(row.get("market_total_over_price")),
                "under_price": number(row.get("market_total_under_price")),
                "best_over_total": number(row.get("market_best_over_total")),
                "best_over_price": number(row.get("market_best_over_price")),
                "best_over_book": canonical_book(row.get("market_best_over_book")),
                "best_under_total": number(row.get("market_best_under_total")),
                "best_under_price": number(row.get("market_best_under_price")),
                "best_under_book": canonical_book(row.get("market_best_under_book")),
                "last_update": text(row.get("market_total_last_update")),
            },
            "moneyline": {
                "home": number(row.get("market_home_moneyline")),
                "home_book": canonical_book(row.get("market_home_moneyline_book")),
                "away": number(row.get("market_away_moneyline")),
                "away_book": canonical_book(row.get("market_away_moneyline_book")),
            },
            "books_available": sorted(set(books_available)),
            "book_count": len(set(books_available)),
            "matrix": action_matrix.get(key, {}),
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "normalized": str(SGO.relative_to(ROOT)),
            "matrix": str(ACTION.relative_to(ROOT)) if ACTION.exists() else None,
        },
        "audit": {
            "games": len(games),
            "weeks": sorted(set(g["week"] for g in games if g["week"] is not None)),
            "dates": sorted(set(g["date"] for g in games)),
            "spread_games": sum(g["spread"]["current_home"] is not None for g in games),
            "total_games": sum(g["total"]["current"] is not None for g in games),
            "moneyline_games": sum(
                g["moneyline"]["home"] is not None or g["moneyline"]["away"] is not None
                for g in games
            ),
            "matrix_games": sum(bool(g["matrix"]) for g in games),
            "action_matrix": action_audit,
        },
        "books": BOOK_ORDER,
        "games": games,
    }


def page_html(version: str) -> str:
    template = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NCAAF Odds Screen</title>
<style>
:root{--bg:#071426;--panel:#0d2037;--line:#27415e;--text:#eff6ff;--muted:#9fb0c5;--accent:#45b7ff;--good:#3ddc97}
*{box-sizing:border-box} body{margin:0;background:linear-gradient(180deg,#071426,#0b1a2c);color:var(--text);font:14px/1.35 Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
a{color:inherit}.wrap{max-width:1680px;margin:0 auto;padding:22px}.top{display:flex;gap:18px;align-items:center;justify-content:space-between;margin-bottom:18px}
h1{font-size:27px;margin:0}.sub{color:var(--muted);margin-top:4px}.nav{display:flex;gap:8px;flex-wrap:wrap}.nav a{text-decoration:none;border:1px solid var(--line);background:#102942;padding:8px 11px;border-radius:9px}
.controls{display:grid;grid-template-columns:160px 180px minmax(240px,1fr) auto;gap:10px;background:var(--panel);border:1px solid var(--line);padding:12px;border-radius:12px;position:sticky;top:0;z-index:5}
select,input,button{background:#091a2d;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:9px 10px;font:inherit}button{cursor:pointer}
.tabs{display:flex;gap:7px}.tab.active{background:#1677b8;border-color:#45b7ff}.status{display:flex;gap:12px;color:var(--muted);margin:12px 2px;flex-wrap:wrap}.badge{background:#0d2037;border:1px solid var(--line);border-radius:999px;padding:5px 9px}
.board{display:flex;flex-direction:column;gap:12px}.game{border:1px solid var(--line);background:var(--panel);border-radius:12px;overflow:hidden}
.gamehead{display:grid;grid-template-columns:255px 110px 1fr 110px;align-items:center;gap:12px;padding:10px 12px;background:#0b1b30;border-bottom:1px solid var(--line)}
.matchup{font-weight:750;font-size:15px}.date{color:var(--muted)}.link{text-align:right}.link a{text-decoration:none;color:var(--accent)}
.marketgrid{display:grid;grid-template-columns:270px repeat(4,minmax(150px,1fr));min-width:950px}.cell{padding:10px 12px;border-right:1px solid var(--line);border-bottom:1px solid #1a324d;min-height:58px}
.cell:last-child{border-right:0}.label{color:var(--muted);font-size:12px}.value{font-weight:750;margin-top:3px}.best{color:var(--good)}.book{color:var(--muted);font-size:12px;margin-top:2px}
.scroll{overflow-x:auto}.empty{padding:28px;color:var(--muted);text-align:center;border:1px dashed var(--line);border-radius:12px}
@media(max-width:850px){.controls{grid-template-columns:1fr 1fr}.top{align-items:flex-start;flex-direction:column}.gamehead{grid-template-columns:1fr 90px}.gamehead .summary{display:none}}
</style>
</head>
<body>
<div class="wrap">
<div class="top"><div><h1>Odds Screen</h1><div class="sub">Current NCAAF spread, total, moneyline and sportsbook comparison.</div></div><div class="nav"><a href="index.html">Season site</a><a href="openers.html">Openers</a></div></div>
<div class="controls"><select id="week"></select><select id="date"></select><input id="search" placeholder="Search team or matchup"><div class="tabs"><button class="tab active" data-market="spread">Spread</button><button class="tab" data-market="total">Total</button><button class="tab" data-market="moneyline">Moneyline</button></div></div>
<div class="status" id="status"></div><div class="board" id="board"><div class="empty">Loading odds…</div></div>
</div>
<script>
const DATA_URL='data/site/odds_screen.json?v=__VERSION__';let DATA=null,market='spread';
const fmtLine=v=>v==null?'—':Math.abs(Number(v))<0.001?'PK':`${Number(v)>0?'+':''}${Number(v)}`;
const fmtPrice=v=>v==null?'—':`${Number(v)>0?'+':''}${Math.round(Number(v))}`;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const quote=(line,price)=>line==null&&price==null?'—':`${fmtLine(line)} ${fmtPrice(price)}`;
function options(select,values,label){select.innerHTML=`<option value="">${label}</option>`+values.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('')}
function matrixValue(game,book){const q=(game.matrix||{})[book]||{};if(market==='spread')return `<div class="value">${quote(q.away_spread,q.away_spread_price)} / ${quote(q.home_spread,q.home_spread_price)}</div><div class="book">Away / Home</div>`;if(market==='total')return `<div class="value">${q.total==null?'—':q.total} · O ${fmtPrice(q.over_price)} / U ${fmtPrice(q.under_price)}</div>`;return `<div class="value">${fmtPrice(q.away_moneyline)} / ${fmtPrice(q.home_moneyline)}</div><div class="book">Away / Home</div>`}
function summaryCell(g){if(market==='spread'){const s=g.spread;return `<div class="label">Open → Current</div><div class="value">${fmtLine(s.open_home)} → ${fmtLine(s.current_home)} ${fmtPrice(s.current_price)}</div><div class="book">${esc(s.current_book||'—')}</div>`}if(market==='total'){const t=g.total;return `<div class="label">Open → Current</div><div class="value">${t.open??'—'} → ${t.current??'—'}</div><div class="book">${esc(t.book||'—')}</div>`}const m=g.moneyline;return `<div class="label">Away / Home ML</div><div class="value">${fmtPrice(m.away)} / ${fmtPrice(m.home)}</div><div class="book">${esc(m.away_book||m.home_book||'—')}</div>`}
function bestCell(g){if(market==='spread'){const s=g.spread;return `<div class="label">Best away / home</div><div class="value best">${esc(s.best_away_text||'—')} ${fmtPrice(s.best_away_price)} / ${esc(s.best_home_text||'—')} ${fmtPrice(s.best_home_price)}</div><div class="book">${esc(s.best_away_book||'—')} / ${esc(s.best_home_book||'—')}</div>`}if(market==='total'){const t=g.total;return `<div class="label">Best over / under</div><div class="value best">O ${t.best_over_total??'—'} ${fmtPrice(t.best_over_price)} / U ${t.best_under_total??'—'} ${fmtPrice(t.best_under_price)}</div><div class="book">${esc(t.best_over_book||'—')} / ${esc(t.best_under_book||'—')}</div>`}return `<div class="label">Best current moneyline</div><div class="value best">${fmtPrice(g.moneyline.away)} / ${fmtPrice(g.moneyline.home)}</div><div class="book">${esc(g.moneyline.away_book||'—')} / ${esc(g.moneyline.home_book||'—')}</div>`}
function render(){const week=document.querySelector('#week').value,date=document.querySelector('#date').value,q=document.querySelector('#search').value.trim().toLowerCase();const games=DATA.games.filter(g=>(!week||String(g.week)===week)&&(!date||g.date===date)&&(!q||`${g.away_team} ${g.home_team}`.toLowerCase().includes(q)));document.querySelector('#status').innerHTML=`<span class="badge">${games.length} games</span><span class="badge">${market}</span><span class="badge">Updated ${new Date(DATA.generated_at).toLocaleString()}</span>`;document.querySelector('#board').innerHTML=games.map(g=>`<section class="game"><div class="gamehead"><div class="matchup">${esc(g.away_team)} at ${esc(g.home_team)}</div><div class="date">W${g.week??'—'} · ${esc(g.date)}</div><div class="summary">${g.book_count||0} books available</div><div class="link"><a href="${esc(g.matchup_url)}">Matchup →</a></div></div><div class="scroll"><div class="marketgrid"><div class="cell">${summaryCell(g)}${bestCell(g)}</div>${DATA.books.map(book=>`<div class="cell"><div class="label">${esc(book)}</div>${matrixValue(g,book)}</div>`).join('')}</div></div></section>`).join('')||'<div class="empty">No games match the current filters.</div>'}
fetch(DATA_URL,{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()}).then(data=>{DATA=data;options(document.querySelector('#week'),data.audit.weeks.map(String),'All weeks');options(document.querySelector('#date'),data.audit.dates,'All dates');document.querySelectorAll('.tab').forEach(button=>button.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));button.classList.add('active');market=button.dataset.market;render()});['week','date','search'].forEach(id=>document.querySelector('#'+id).addEventListener(id==='search'?'input':'change',render));render()}).catch(error=>{document.querySelector('#board').innerHTML=`<div class="empty">Could not load odds data: ${esc(error.message)}</div>`});
</script>
</body>
</html>
'''
    return template.replace("__VERSION__", version)


def same_file(source: Path, destination: Path) -> bool:
    try:
        return source.exists() and destination.exists() and os.path.samefile(source, destination)
    except OSError:
        return False


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if same_file(source, destination):
        print(f"same file, skipped: {source} -> {destination}")
        return
    shutil.copy2(source, destination)
    print(f"copied: {source} -> {destination}")


def add_daily_hook() -> bool:
    daily = ROOT / "daily_market_update.sh"
    if not daily.exists():
        return False

    contents = daily.read_text(encoding="utf-8", errors="ignore")
    command = '  run_py "scripts/site/build_odds_screen_v1.py" "build_odds_screen_v1.py" || echo "WARNING: odds screen build failed"'
    if command in contents:
        return False

    anchor = '  run_py "scripts/site/build_matchups_view.py"'
    position = contents.find(anchor)
    if position < 0:
        return False

    line_end = contents.find("\n", position)
    if line_end < 0:
        line_end = len(contents)

    updated = contents[:line_end + 1] + command + "\n" + contents[line_end + 1:]
    daily.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    payload = build_payload()
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")

    version = hashlib.sha256(JSON_OUT.read_bytes()).hexdigest()[:12]
    HTML_OUT.write_text(page_html(version), encoding="utf-8")

    copy_file(HTML_OUT, BUILD_HTML)
    copy_file(JSON_OUT, BUILD_JSON)
    copy_file(HTML_OUT, SITE_HTML)
    copy_file(JSON_OUT, SITE_JSON)

    hook_added = add_daily_hook()

    print()
    print("NCAAF ODDS SCREEN V1")
    print("=" * 100)
    print(f"Games: {payload['audit']['games']}")
    print(f"Spread games: {payload['audit']['spread_games']}")
    print(f"Total games: {payload['audit']['total_games']}")
    print(f"Moneyline games: {payload['audit']['moneyline_games']}")
    print(f"Sportsbook matrix games parsed: {payload['audit']['matrix_games']}")
    print(f"Action matrix books: {', '.join(payload['audit']['action_matrix'].get('books', [])) or 'none'}")
    print(f"Wrote: {HTML_OUT}")
    print(f"Wrote: {JSON_OUT}")
    print(f"Daily pipeline hook added: {hook_added}")
    print("GitHub working copy updated locally: True")
    print("No commit or push performed: True")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
