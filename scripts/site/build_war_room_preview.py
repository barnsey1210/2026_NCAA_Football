#!/usr/bin/env python3
"""Build the isolated War Room homepage prototype from repository fixtures only."""
from __future__ import annotations

import csv
import html
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build/war_room_preview/index.html"

SOURCES = {
    "health": "data/site/page_health_status.json",
    "matchups": "data/site/matchups_view.json",
    "odds": "data/site/odds_screen_v2.json",
    "futures": "data/site/futures_view.json",
    "ratings": "data/site/ratings_view.json",
    "playoff": "data/site/playoff_model_2026.json",
    "model_performance": "data/site/model_performance_view.json",
    "betting": "data/site/betting_activity_view.json",
    "line_history": "data/history/game_line_model_history.csv",
    "injuries": "data/injuries/injury_alerts.csv",
}

DESTINATIONS = {
    "Dashboard": "../../dashboard.html",
    "Ratings": "../../ratings.html",
    "Openers": "../../openers.html",
    "Matchups": "../../matchups.html",
    "Odds": "../../odds.html",
    "Schedule": "../../schedule.html",
    "Futures": "../../futures.html",
    "Conferences": "../../conferences.html",
    "Playoff": "../../playoff.html",
    "Simulations": "../../simulations.html",
    "Betting": "../../betting.html",
}


def load_json(key: str) -> dict[str, Any]:
    return json.loads((ROOT / SOURCES[key]).read_text())


def load_csv(key: str) -> list[dict[str, str]]:
    path = ROOT / SOURCES[key]
    if not path.is_file():
        return []
    with path.open(newline="", errors="replace") as handle:
        return list(csv.DictReader(handle))


def num(value: Any) -> float | None:
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else "—"))


def fmt(value: Any, digits: int = 1, signed: bool = False) -> str:
    value = num(value)
    if value is None:
        return "—"
    return f"{value:+.{digits}f}" if signed else f"{value:.{digits}f}"


def pct(value: Any) -> str:
    value = num(value)
    if value is None:
        return "—"
    if value <= 1:
        value *= 100
    return f"{value:.1f}%"


def logo(slug: str, team: str, cls: str = "logo") -> str:
    return f'<img class="{cls}" src="../../logos/{esc(slug)}.png" alt="{esc(team)} logo" onerror="this.hidden=true">'


def canonical_week(games: list[dict[str, Any]]) -> int:
    scheduled = [g["game"] for g in games if not g["game"].get("completed")]
    return min(int(g["week"]) for g in scheduled if g.get("week") is not None)


def market_covered(game: dict[str, Any]) -> bool:
    market = game.get("market", {})
    return bool(market.get("spread") or market.get("total"))


def spread_edge(game: dict[str, Any]) -> dict[str, Any] | None:
    model = num(game.get("model", {}).get("home_spread"))
    market = num(game.get("market", {}).get("spread", {}).get("home_line"))
    if model is None or market is None:
        return None
    # Both values are home-team spread conventions; recommend the side with the gap.
    gap = model - market
    # Example: model home -3.5 versus market home -7.5 is +4.0 on this
    # calculation, which is value on the away side at +7.5.
    side = game["game"]["away_team"] if gap > 0 else game["game"]["home_team"]
    return {"game": game, "side": side, "edge": abs(gap), "model": model, "market": market}


def total_edge(game: dict[str, Any]) -> dict[str, Any] | None:
    model = num(game.get("model", {}).get("total"))
    market = num(game.get("market", {}).get("total", {}).get("line"))
    if model is None or market is None:
        return None
    gap = model - market
    return {"game": game, "side": "Over" if gap > 0 else "Under", "edge": abs(gap), "model": model, "market": market}


def best_book_range(odds_game: dict[str, Any], market: str) -> float | None:
    values: list[float] = []
    for quote in odds_game.get("quotes", {}).values():
        item = quote.get(market, {})
        if market == "spread":
            selection = item.get("home", {})
        else:
            selection = item.get("over", {})
        if selection.get("valid") is False:
            continue
        value = num(selection.get("point"))
        if value is not None:
            values.append(value)
    return max(values) - min(values) if len(values) > 1 else None


def matchup_href(game_id: str) -> str:
    return f"../../matchups.html?game_id={esc(game_id)}"


def opportunity_rows(items: list[dict[str, Any]], market: str, limit: int = 4) -> str:
    rows = []
    for item in items[:limit]:
        info = item["game"]["game"]
        rows.append(
            f'<tr><td><a href="{matchup_href(info["game_id"])}">{esc(info["away_team"])} at {esc(info["home_team"])}</a></td>'
            f'<td>{esc(item["side"])}</td><td>{fmt(item["market"], 1, market == "spread")}</td>'
            f'<td>{fmt(item["model"], 1, market == "spread")}</td><td class="value">+{fmt(item["edge"])}</td></tr>'
        )
    return "".join(rows) or '<tr><td colspan="5" class="empty">No qualifying current opportunities.</td></tr>'


def build_payload() -> dict[str, Any]:
    health = load_json("health")
    matchups = load_json("matchups")
    odds = load_json("odds")
    futures = load_json("futures")
    ratings = load_json("ratings")
    playoff = load_json("playoff")
    performance = load_json("model_performance")
    betting = load_json("betting")
    lines = load_csv("line_history")
    injuries = load_csv("injuries")

    games = matchups.get("games", [])
    week = canonical_week(games)
    slate = [g for g in games if int(g["game"].get("week", -1)) == week and not g["game"].get("completed")]
    spreads = sorted((x for g in slate if (x := spread_edge(g)) and x["edge"] >= 2), key=lambda x: x["edge"], reverse=True)
    totals = sorted((x for g in slate if (x := total_edge(g)) and x["edge"] >= 3), key=lambda x: x["edge"], reverse=True)

    futures_edges = []
    for row in futures.get("rows", []):
        candidates = [
            ("Playoff", row.get("playoff_edge"), row.get("playoff_model_prob"), row.get("playoff_market_prob"), row.get("playoff_price")),
            ("Conference title", row.get("title_edge"), row.get("title_model_prob"), row.get("title_market_prob"), row.get("title_price")),
            ("National title", row.get("national_title_edge"), row.get("national_title_model_prob"), row.get("national_title_market_prob"), row.get("national_title_price")),
        ]
        for market, edge, model, implied, price in candidates:
            if num(edge) is not None and edge > 0:
                futures_edges.append({"team": row["team"], "market": market, "edge": edge, "model": model, "implied": implied, "price": price})
    futures_edges.sort(key=lambda x: x["edge"], reverse=True)

    odds_by_id = {str(g.get("game_id")): g for g in odds.get("games", [])}
    disagreement = []
    for game in slate:
        og = odds_by_id.get(str(game["game"]["game_id"]))
        if not og:
            continue
        spread_range = best_book_range(og, "spread")
        total_range = best_book_range(og, "total")
        best = max(spread_range or 0, total_range or 0)
        if best:
            disagreement.append({"game": game, "spread_range": spread_range, "total_range": total_range, "max": best})
    disagreement.sort(key=lambda x: x["max"], reverse=True)

    health_map = {p["page_id"]: p for p in health.get("pages", [])}
    teams = ratings.get("teams", [])
    variance = sorted(teams, key=lambda x: num(x.get("variance")) or -1, reverse=True)
    composite_market = sorted(
        (t for t in teams if num(t.get("market_delta")) is not None),
        key=lambda x: abs(x["market_delta"]), reverse=True,
    )
    playoff_teams = sorted(playoff.get("teams", []), key=lambda x: num(x.get("playoff_pct")) or 0, reverse=True)

    # Balanced featured selection: edge, national rank, disagreement, market move/history, uncertainty.
    featured: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    def add(reason: str, game: dict[str, Any] | None) -> None:
        if not game:
            return
        gid = str(game["game"]["game_id"])
        if gid not in seen:
            featured.append((reason, game)); seen.add(gid)
    add("Largest model-market edge", (spreads + totals)[0]["game"] if spreads or totals else None)
    ranked = sorted(slate, key=lambda g: min(g["teams"]["away"].get("overall_rank") or 999, g["teams"]["home"].get("overall_rank") or 999))
    add("Highest-ranked team on the slate", ranked[0] if ranked else None)
    add(
        "Largest cross-book disagreement",
        next((row["game"] for row in disagreement if str(row["game"]["game"]["game_id"]) not in seen), None),
    )
    history_games = {r.get("game_id") for r in lines if r.get("game_week") in {str(week), str(week + 1)}}
    add("Deepest retained market history", next((g for g in slate if g["game"]["game_id"] in history_games), None))
    uncertain = sorted(slate, key=lambda g: max(g["teams"]["away"].get("rating_trend", {}).get("rating_trend") or 0, g["teams"]["home"].get("rating_trend", {}).get("rating_trend") or 0), reverse=True)
    add("Highest model uncertainty", uncertain[0] if uncertain else None)
    for g in slate:
        add("Featured matchup", g)
        if len(featured) >= 5:
            break

    return {
        "source_paths": list(SOURCES.values()), "health": health, "health_map": health_map,
        "matchups": matchups, "odds": odds, "futures": futures, "ratings": ratings,
        "playoff": playoff, "performance": performance, "betting": betting,
        "week": week, "slate": slate, "spreads": spreads, "totals": totals,
        "futures_edges": futures_edges, "disagreement": disagreement,
        "variance": variance, "composite_market": composite_market, "playoff_teams": playoff_teams,
        "featured": featured, "injury_state": "unreleased" if not injuries else "active",
    }


def render(payload: dict[str, Any]) -> str:
    week = payload["week"]
    slate = payload["slate"]
    covered = sum(market_covered(g) for g in slate)
    ranked_games = sum(min(g["teams"]["away"].get("overall_rank") or 999, g["teams"]["home"].get("overall_rank") or 999) <= 25 for g in slate)
    health = payload["health_map"]
    worst = next((s for s in ("red", "yellow", "gray") if any(p["status"] == s for p in payload["health"]["pages"])), "green")
    futures = payload["futures"]
    performance = payload["performance"]
    betting = payload["betting"]

    future_rows = "".join(
        f'<tr><td>{esc(x["team"])}</td><td>{esc(x["market"])}</td><td>{pct(x["model"])}</td><td>{pct(x["implied"])}</td><td class="value">+{pct(x["edge"])}</td></tr>'
        for x in payload["futures_edges"][:5]
    )
    ineff_rows = "".join(
        f'<tr><td><a href="{matchup_href(x["game"]["game"]["game_id"])}">{esc(x["game"]["game"]["away_team"])} at {esc(x["game"]["game"]["home_team"])}</a></td><td>{fmt(x["spread_range"])}</td><td>{fmt(x["total_range"])}</td><td>Compare books</td></tr>'
        for x in payload["disagreement"][:5]
    ) or '<tr><td colspan="4" class="empty">No multi-book disagreement is currently measurable.</td></tr>'

    feature_cards = []
    for reason, game in payload["featured"]:
        info, model, market = game["game"], game["model"], game["market"]
        away, home = game["teams"]["away"], game["teams"]["home"]
        feature_cards.append(f'''<article class="feature-card">
          <div class="eyebrow">{esc(reason)}</div>
          <div class="match-line">{logo(away["logo_slug"], away["team"])}<b>{esc(away["team"])}</b><span>at</span>{logo(home["logo_slug"], home["team"])}<b>{esc(home["team"])}</b></div>
          <div class="feature-metrics"><span>Model <b>{fmt(model.get("home_spread"),1,True)}</b></span><span>Total <b>{fmt(model.get("total"))}</b></span><span>Home win <b>{pct(model.get("home_win_probability"))}</b></span></div>
          <div class="muted">Market {fmt(market.get("spread",{}).get("home_line"),1,True)} · total {fmt(market.get("total",{}).get("line"))} · injuries {"unreleased" if payload["injury_state"] == "unreleased" else "available"}</div>
          <a class="text-link" href="{matchup_href(info["game_id"])}">Open full matchup →</a>
        </article>''')

    health_cards = []
    descriptions = {
        "Dashboard": "Daily changes and action queue", "Ratings": "Team strength and source disagreement",
        "Openers": "First-pass model versus market", "Matchups": "Full game research workspace",
        "Odds": "Book-by-book prices and history", "Schedule": "Weekly games, results, and readiness",
        "Futures": "Win totals and long-term markets", "Conferences": "Standings, projections, and title races",
        "Playoff": "Projected field and advancement odds", "Simulations": "Season outcome distributions",
        "Betting": "Tracked model performance and positions",
    }
    for name, href in DESTINATIONS.items():
        pid = "dashboard" if name == "Dashboard" else name.lower()
        record = health.get(pid, {})
        metric = (record.get("metrics") or [{"label": "Coverage", "value": "—"}])[0]
        health_cards.append(f'''<a class="explore-card" href="{href}"><div><span class="status-dot {esc(record.get("status","gray"))}"></span><b>{esc(name)}</b></div><p>{esc(descriptions[name])}</p><small>{esc(record.get("status_label","Unavailable"))} · {esc(metric["label"])} {esc(metric["value"])}</small></a>''')

    source_time = payload["matchups"].get("built_at") or payload["health"].get("built_at")
    model_summary = performance.get("summary", {})
    perf_empty = performance.get("status") == "PRESEASON_NOT_STARTED"
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>2026 NCAAF War Room — Prototype</title>
<style>
:root{{--bg:#06142a;--panel:#0d2341;--panel2:#102b4e;--line:#234a75;--text:#f3f7ff;--muted:#9fb3d1;--cyan:#65c7ff;--green:#45e2a0;--yellow:#ffbf55;--red:#ff6678;--gray:#91a0b7}}*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(135deg,#06142a 0%,#071a32 55%,#091f37 100%);color:var(--text);font:14px/1.35 Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}}a{{color:inherit}}.shell{{max-width:1500px;margin:auto;padding:18px}}.topbar{{display:flex;align-items:center;gap:18px;border-bottom:1px solid var(--line);padding-bottom:13px}}.brand{{font-weight:1000;font-size:20px;letter-spacing:.05em}}.prototype{{color:var(--yellow);font-size:11px;text-transform:uppercase;letter-spacing:.12em}}h1{{font-size:36px;margin:20px 0 3px}}h2{{font-size:20px;margin:0}}h3{{font-size:15px;margin:0 0 10px}}.subtitle,.muted,small{{color:var(--muted)}}.section{{margin-top:14px}}.section-head{{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:8px}}.pulse{{display:grid;grid-template-columns:1.2fr repeat(5,1fr);gap:8px;margin-top:16px}}.pulse>div,.metric,.panel,.feature-card,.explore-card{{background:rgba(13,35,65,.92);border:1px solid var(--line);border-radius:12px}}.pulse>div{{padding:10px 12px}}.label,.eyebrow{{color:var(--muted);font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.1em}}.pulse strong{{display:block;font-size:15px;margin-top:3px}}.status-dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px}}.green{{background:var(--green)}}.yellow{{background:var(--yellow)}}.red{{background:var(--red)}}.gray{{background:var(--gray)}}.briefing{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}}.metric{{padding:11px}}.metric b{{display:block;font-size:20px;margin-top:3px}}.grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}}.grid-2{{display:grid;grid-template-columns:1.15fr .85fr;gap:10px}}.panel{{padding:13px;min-width:0}}table{{width:100%;border-collapse:collapse;font-size:12px}}th{{color:var(--muted);text-transform:uppercase;font-size:9px;letter-spacing:.08em;text-align:left;padding:7px;border-bottom:1px solid var(--line)}}td{{padding:8px 7px;border-bottom:1px solid rgba(35,74,117,.55)}}td.value{{color:var(--green);font-weight:900}}.empty{{color:var(--muted)}}.feature-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:9px}}.feature-card{{padding:12px}}.match-line{{display:flex;align-items:center;gap:6px;margin:8px 0;min-height:38px}}.match-line span{{color:var(--muted)}}.logo{{width:26px;height:26px;object-fit:contain}}.feature-metrics{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:7px}}.feature-metrics span{{background:#071a32;padding:4px 6px;border-radius:6px}}.text-link{{display:inline-block;margin-top:9px;color:var(--cyan);font-weight:800;text-decoration:none}}.explore-grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}}.explore-card{{padding:11px;text-decoration:none;min-height:105px}}.explore-card:hover{{border-color:var(--cyan)}}.explore-card p{{margin:8px 0;color:var(--muted);font-size:12px}}.split-label{{display:flex;justify-content:space-between;align-items:center;margin-bottom:7px}}.badge{{border:1px solid var(--line);border-radius:999px;padding:3px 7px;font-size:10px;color:var(--muted)}}details{{border-top:1px solid var(--line);margin-top:12px;padding-top:8px}}summary{{cursor:pointer;color:var(--muted)}}.method{{font-size:12px;color:var(--muted)}}
@media(max-width:1050px){{.pulse{{grid-template-columns:repeat(3,1fr)}}.briefing{{grid-template-columns:repeat(3,1fr)}}.grid-3,.grid-2{{grid-template-columns:1fr}}.feature-grid{{grid-template-columns:repeat(2,1fr)}}.explore-grid{{grid-template-columns:repeat(3,1fr)}}}}
@media(max-width:620px){{.shell{{padding:11px}}h1{{font-size:28px}}.pulse{{grid-template-columns:1fr 1fr}}.briefing{{grid-template-columns:1fr 1fr}}.feature-grid,.explore-grid{{grid-template-columns:1fr}}.panel{{overflow-x:auto}}table{{min-width:510px}}.pulse>div:first-child{{grid-column:1/-1}}.section-head{{align-items:flex-start;gap:8px}}}}
</style></head><body><main class="shell">
<header><div class="topbar"><div class="brand">NCAAF</div><div class="prototype">Isolated prototype · no production navigation</div></div><h1>2026 NCAAF War Room</h1><div class="subtitle">A compact command center for the upcoming week, market value, model performance, and season outlook.</div>
<div class="pulse"><div><span class="label">System readiness</span><strong><span class="status-dot {worst}"></span>{esc(worst.upper())} · page-level warnings active</strong></div><div><span class="label">Upcoming focus</span><strong>Week {week}</strong></div><div><span class="label">Slate</span><strong>{len(slate)} games</strong></div><div><span class="label">Market covered</span><strong>{covered}/{len(slate)}</strong></div><div><span class="label">Open positions</span><strong>{betting.get("summary",{}).get("owned_open",0)}</strong></div><div><span class="label">Data built</span><strong>{esc(str(source_time)[:16].replace("T"," "))}</strong></div></div></header>

<section class="section"><div class="section-head"><h2>Upcoming Week Briefing</h2><span class="badge">Canonical focus: Week {week}</span></div><div class="briefing"><div class="metric"><span class="label">Games</span><b>{len(slate)}</b></div><div class="metric"><span class="label">FBS model games</span><b>{sum(g["model"].get("home_spread") is not None for g in slate)}</b></div><div class="metric"><span class="label">Market available</span><b>{covered}</b></div><div class="metric"><span class="label">Ranked-team games</span><b>{ranked_games}</b></div><div class="metric"><span class="label">Spread values ≥2</span><b>{len(payload["spreads"])}</b></div><div class="metric"><span class="label">Total values ≥3</span><b>{len(payload["totals"])}</b></div></div></section>

<section class="section"><div class="section-head"><h2>Model Opportunities</h2><span class="muted">Model-market gaps; not confidence scores</span></div><div class="grid-3"><div class="panel"><h3>Spread opportunities</h3><table><thead><tr><th>Game</th><th>Side</th><th>Market</th><th>Model</th><th>Gap</th></tr></thead><tbody>{opportunity_rows(payload["spreads"],"spread")}</tbody></table></div><div class="panel"><h3>Total opportunities</h3><table><thead><tr><th>Game</th><th>Side</th><th>Market</th><th>Model</th><th>Gap</th></tr></thead><tbody>{opportunity_rows(payload["totals"],"total")}</tbody></table></div><div class="panel"><h3>Futures opportunities</h3><table><thead><tr><th>Team</th><th>Market</th><th>Model</th><th>Market</th><th>Edge</th></tr></thead><tbody>{future_rows}</tbody></table></div></div></section>

<section class="section"><div class="section-head"><h2>Market Inefficiencies</h2><span class="muted">Price disagreement and uncertainty, separate from model value</span></div><div class="grid-2"><div class="panel"><h3>Cross-book disagreement</h3><table><thead><tr><th>Game</th><th>Spread range</th><th>Total range</th><th>Action</th></tr></thead><tbody>{ineff_rows}</tbody></table></div><div class="panel"><h3>Model disagreement</h3>{''.join(f'<div class="split-label"><span>{esc(t["team"])} <small>{esc(t.get("high_source"))} high · {esc(t.get("low_source"))} low</small></span><b>{fmt(t.get("variance"))} pts</b></div>' for t in payload["variance"][:6])}<div class="muted">Source variance identifies uncertainty; it is not a betting recommendation.</div></div></div></section>

<section class="section"><div class="section-head"><h2>Featured Upcoming Games</h2><span class="muted">Balanced selection rules</span></div><div class="feature-grid">{''.join(feature_cards)}</div></section>

<section class="section"><div class="grid-2"><div class="panel"><div class="section-head"><h2>Model Performance</h2><a class="text-link" href="../../betting.html">View model tracking →</a></div>{f'<div class="empty">Preseason tracking has not started. No fabricated ATS, totals, or CLV results are shown.</div>' if perf_empty else f'<div class="briefing"><div class="metric"><span class="label">Predictions</span><b>{model_summary.get("predictions",0)}</b></div><div class="metric"><span class="label">Settled</span><b>{model_summary.get("settled",0)}</b></div></div>'}<div class="muted" style="margin-top:10px">{esc(performance.get("status","Unavailable").replace("_"," ").title())}</div></div>
<div class="panel"><div class="section-head"><h2>Futures & Simulation Pulse</h2><a class="text-link" href="../../futures.html">Explore futures →</a></div><div class="briefing"><div class="metric"><span class="label">Sim trials</span><b>{payload["playoff"].get("trials",0):,}</b></div><div class="metric"><span class="label">Playoff teams</span><b>{futures.get("summary",{}).get("playoff_markets",0)}</b></div><div class="metric"><span class="label">Win totals</span><b>{futures.get("summary",{}).get("win_markets",0)}</b></div></div><div style="margin-top:10px">{''.join(f'<div class="split-label"><span>{esc(t["team"])}</span><b>{pct(t["playoff_pct"])}</b></div>' for t in payload["playoff_teams"][:4])}</div><div class="muted">Futures markets are currently stale/partial and are labeled accordingly.</div></div></div></section>

<section class="section"><div class="panel"><div class="section-head"><h2>Ratings & Market Pulse</h2><a class="text-link" href="../../ratings.html">Open ratings →</a></div><div class="grid-2"><div><h3>Composite vs market disagreement</h3>{''.join(f'<div class="split-label"><span>{esc(t["team"])} <small>Composite #{esc(t.get("overall_rank"))} · Market #{esc(t.get("market",{}).get("rank"))}</small></span><b>{fmt(t.get("market_delta"),1,True)}</b></div>' for t in payload["composite_market"][:6])}</div><div><h3>Source freshness</h3>{''.join(f'<div class="split-label"><span>{esc(v.get("label"))}</span><b>{esc(v.get("change_status"))}</b></div>' for v in payload["ratings"].get("source_meta",{}).values())}<div class="muted">Market-Derived Ratings remain separate from the composite.</div></div></div></div></section>

<section class="section"><div class="section-head"><h2>Explore the War Room</h2><span class="muted">What each workspace is for</span></div><div class="explore-grid">{''.join(health_cards)}</div></section>

<section class="section panel method"><h2>Methodology & Data Notes</h2><p>Prototype metrics are generated only from the listed repository artifacts. Spread, total, and futures opportunities remain distinct. Market inefficiencies describe book or model disagreement and are not promoted as model opportunities. Injury context is explicitly marked unreleased because the current fixture has no actionable CFBDepth reports.</p><details><summary>Data provenance</summary><ul>{''.join(f'<li>{esc(p)}</li>' for p in payload["source_paths"])}</ul></details></section>
</main></body></html>'''


def main() -> None:
    payload = build_payload()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(payload))
    print(f"Built {OUT.relative_to(ROOT)} from {len(payload['source_paths'])} static artifacts; upcoming week W{payload['week']} ({len(payload['slate'])} games).")


if __name__ == "__main__":
    main()
