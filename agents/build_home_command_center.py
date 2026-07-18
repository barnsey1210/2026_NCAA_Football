#!/usr/bin/env python3
from pathlib import Path
import json, re
import pandas as pd
from datetime import datetime

INDEX = Path("index.html")
OUT = Path("data/agents/home_command_center.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

DB_RE = re.compile(r'<script id="db" type="application/json">(.*?)</script>', re.S)

def n(v):
    try:
        if pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None

def clean(v):
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)

def fmt_num(v, d=1):
    x = n(v)
    if x is None:
        return "—"
    return f"{x:.{d}f}".replace(".0", "")

def fmt_signed(v, suffix=""):
    x = n(v)
    if x is None:
        return "—"
    return f"{x:+.1f}{suffix}".replace("+0.0", "0").replace("-0.0", "0")

def pct_from_american(odds):
    o = n(odds)
    if o is None or o == 0:
        return None
    return 100 / (o + 100) if o > 0 else abs(o) / (abs(o) + 100)

def fmt_pct(p):
    if p is None:
        return "—"
    x = p * 100 if p <= 1 else p
    return f"{x:.1f}%".replace(".0%", "%")

def load_db():
    s = INDEX.read_text(errors="ignore")
    m = DB_RE.search(s)
    if not m:
        raise SystemExit("DB not found")
    return json.loads(m.group(1))

def add_card(cards, title, subtitle, rows, link="#home"):
    cards.append({
        "title": title,
        "subtitle": subtitle,
        "rows": rows[:12],
        "link": link
    })

def game_week(g):
    x = n(g.get("week"))
    return int(x) if x is not None else None

def team_map(db):
    return {t.get("team"): t for t in db.get("teams", [])}

def game_label(g):
    return f"{g.get('away_team')} at {g.get('home_team')}"

def projected_score_text(g):
    total = n(g.get("projected_total"))
    margin = n(g.get("projected_margin_home"))
    if total is None or margin is None:
        return "Proj score —"
    home_pts = (total + margin) / 2
    away_pts = (total - margin) / 2
    return f"{g.get('away_team')} {away_pts:.0f}, {g.get('home_team')} {home_pts:.0f}"

def model_spread_total_text(g):
    margin = n(g.get("projected_margin_home"))
    total = n(g.get("projected_total"))
    if margin is None:
        spread = "Model spread —"
    else:
        fav = g.get("home_team") if margin > 0 else g.get("away_team")
        spread = f"Model {fav} -{abs(margin):.1f}"
    total_txt = f"model total {total:.1f}" if total is not None else "model total —"
    return f"{spread} · {total_txt}"

def market_spread_total_text(g):
    spread = g.get("market_spread_home")
    total = g.get("market_total")
    spread_txt = f"market {g.get('home_team')} {fmt_signed(spread)}" if n(spread) is not None else "market spread —"
    total_txt = f"market total {fmt_num(total)}" if n(total) is not None else "market total —"
    return f"{spread_txt} · {total_txt}"


def spread_edge_row(g):
    market = n(g.get("market_spread_home"))
    proj_margin = n(g.get("projected_margin_home"))
    if market is None or proj_margin is None:
        return None

    # Home cover edge = projected home margin + home spread.
    home_edge = proj_margin + market
    if abs(home_edge) < 0.1:
        return None

    if home_edge > 0:
        side = g.get("home_team")
        side_line = market
        edge = home_edge
    else:
        side = g.get("away_team")
        side_line = -market
        edge = abs(home_edge)

    home_fair = -proj_margin
    bet = f"Bet {side} {fmt_signed(side_line)}, {edge:.1f} edge"
    return {
        "kind": "Spread",
        "abs_edge": edge,
        "label": game_label(g),
        "value": bet,
        "note": f"Market {g.get('home_team')} {fmt_signed(market)} · model fair {g.get('home_team')} {fmt_signed(home_fair)}",
        "tone": "good"
    }

def total_edge_row(g):
    market = n(g.get("market_total"))
    proj = n(g.get("projected_total"))
    if market is None or proj is None:
        return None

    diff = proj - market
    if abs(diff) < 0.1:
        return None

    side = "Over" if diff > 0 else "Under"
    edge = abs(diff)
    return {
        "kind": "Total",
        "abs_edge": edge,
        "label": game_label(g),
        "value": f"Bet {side} {fmt_num(market)}, {edge:.1f} edge",
        "note": f"Market total {fmt_num(market)} · model total {fmt_num(proj)}",
        "tone": "good"
    }

def market_rows_by_team(db):
    market_rows = []
    for key in ["market_futures_edges", "market_conference_futures_edges", "market_conference_futures_raw"]:
        market_rows.extend(db.get(key, []) or [])

    market_by_team = {}
    for r in market_rows:
        team = r.get("team")
        if not team or team in market_by_team:
            continue
        odds = r.get("best_title_odds", r.get("american_odds", r.get("current_american_odds")))
        implied = pct_from_american(odds)
        market_by_team[team] = {
            "odds": odds,
            "implied": implied,
            "book": r.get("best_title_book") or r.get("book") or ""
        }

    wt_rows = []
    for key in ["market_win_totals_edges", "market_win_totals_raw"]:
        wt_rows.extend(db.get(key, []) or [])

    wt_by_team = {}
    for r in wt_rows:
        team = r.get("team")
        if not team or team in wt_by_team:
            continue
        total = n(r.get("market_total", r.get("win_total", r.get("current_win_total"))))
        if total is not None:
            wt_by_team[team] = total

    return market_by_team, wt_by_team

def build_futures_cards(db, cards, prefix="Biggest"):
    teams = db.get("teams", [])
    market_by_team, wt_by_team = market_rows_by_team(db)

    rows = []
    for t in teams:
        model = n(t.get("conference_title_pct"))
        if model is not None and model > 1:
            model /= 100
        mkt = market_by_team.get(t.get("team"), {})
        implied = mkt.get("implied")
        if model is None or implied is None:
            continue
        edge = model - implied
        if edge <= 0.03:
            continue
        rows.append((edge, {
            "label": f"{t.get('team')} conference title",
            "value": f"{edge*100:+.1f} pts",
            "note": f"Model {fmt_pct(model)} vs market {fmt_pct(implied)} · {mkt.get('odds') or '—'} {mkt.get('book') or ''}",
            "tone": "good"
        }))

    add_card(
        cards,
        f"{prefix} Conference Futures Value",
        "Model probability vs best available market price.",
        [x[1] for x in sorted(rows, key=lambda x: x[0], reverse=True)],
        "#futures"
    )

    rows = []
    for t in teams:
        team = t.get("team")
        proj = n(t.get("avg_total_wins"))
        total = wt_by_team.get(team)
        if proj is None or total is None:
            continue
        edge = proj - total
        if abs(edge) < 0.35:
            continue
        side = "Over" if edge > 0 else "Under"
        rows.append((abs(edge), {
            "label": f"{team} {side} {total:g}",
            "value": fmt_signed(edge, " wins"),
            "note": f"Projected {proj:.2f} vs market {total:g}",
            "tone": "good" if abs(edge) >= 0.6 else ""
        }))

    add_card(
        cards,
        f"{prefix} Win Total Value",
        "Projected wins vs current market win total.",
        [x[1] for x in sorted(rows, key=lambda x: x[0], reverse=True)],
        "#futures"
    )


def load_2025_eoy_ratings():
    """
    Build a 2025 EOY team baseline from ratings history/latest files.
    This is intentionally flexible because historical files may have slightly different column names.
    """
    candidates = [
        Path("data/ratings/ratings_history.csv"),
        Path("data/ratings/ratings_master_history.csv"),
        Path("data/ratings/ratings_latest.csv"),
        Path("data/ratings/ratings_master_latest.csv"),
    ]

    frames = []
    for path in candidates:
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path, low_memory=False)
            df["_file"] = str(path)
            frames.append(df)
        except Exception:
            pass

    if not frames:
        return {}

    df = pd.concat(frames, ignore_index=True, sort=False)

    def col(opts):
        for c in opts:
            if c in df.columns:
                return c
        return None

    team_col = col(["team", "Team", "school", "School"])
    rating_col = col(["power_rating", "rating", "combo", "value", "rating_value", "overall_rating"])
    rank_col = col(["rank", "overall_rank", "power_rank"])
    season_col = col(["season", "year"])
    date_col = col(["snapshot_date", "date", "updated_at", "created_at"])
    source_col = col(["source", "rating_system", "system"])

    if not team_col or not rating_col:
        return {}

    work = df.copy()
    work["_team"] = work[team_col].map(clean)
    work["_rating"] = pd.to_numeric(work[rating_col], errors="coerce")
    work["_rank"] = pd.to_numeric(work[rank_col], errors="coerce") if rank_col else None

    # Prefer explicit 2025 season rows.
    if season_col:
        season_vals = pd.to_numeric(work[season_col], errors="coerce")
        work = work[season_vals == 2025]

    # If no explicit 2025 rows survived, infer 2025 from snapshot/date.
    if work.empty and date_col:
        tmp = df.copy()
        tmp["_team"] = tmp[team_col].map(clean)
        tmp["_rating"] = pd.to_numeric(tmp[rating_col], errors="coerce")
        tmp["_rank"] = pd.to_numeric(tmp[rank_col], errors="coerce") if rank_col else None
        dates = tmp[date_col].astype(str)
        work = tmp[dates.str.contains("2025", na=False)]

    if work.empty:
        return {}

    # If multiple systems exist, average by team for a blended EOY baseline.
    # Prefer the latest 2025 snapshot/date per system/team if date exists.
    if date_col and date_col in work.columns:
        work["_date_sort"] = pd.to_datetime(work[date_col], errors="coerce")
        sort_cols = ["_team"]
        if source_col:
            sort_cols.append(source_col)
        work = work.sort_values("_date_sort").drop_duplicates(sort_cols, keep="last")

    out = {}
    for team, g in work.dropna(subset=["_rating"]).groupby("_team"):
        if not team:
            continue
        out[team] = {
            "rating": float(g["_rating"].mean()),
            "rank": float(g["_rank"].mean()) if "_rank" in g and g["_rank"].notna().any() else None,
            "sources": int(g["_rating"].notna().sum()),
        }

    return out


def ratings_mover_rows(db, wk=None):
    teams = db.get("teams", [])
    eoy = load_2025_eoy_ratings()
    rows = []

    for t in teams:
        team = clean(t.get("team"))
        cur_rating = n(t.get("combo")) or n(t.get("power_rating"))
        cur_rank = n(t.get("rank"))

        base = eoy.get(team, {})
        old_rating = base.get("rating")
        old_rank = base.get("rank")
        baseline_label = "2025 EOY"

        # Fallback to DB 2025 fields if history did not provide baseline.
        if old_rating is None:
            old_rating = (
                n(t.get("power_rating_2025")) or
                n(t.get("eoy_2025_combo")) or
                n(t.get("rating_2025")) or
                n(t.get("combo_2025")) or
                n(t.get("final_2025_combo")) or
                n(t.get("prior_combo"))
            )
            old_rank = (
                n(t.get("rank_2025")) or
                n(t.get("eoy_2025_rank")) or
                n(t.get("final_2025_rank")) or
                n(t.get("prior_rank"))
            )

        if cur_rating is None or old_rating is None:
            continue

        rating_delta = cur_rating - old_rating
        if abs(rating_delta) < 0.05:
            continue

        rank_delta = None
        if cur_rank is not None and old_rank is not None:
            rank_delta = old_rank - cur_rank

        rows.append({
            "team": team,
            "conference": clean(t.get("conference")),
            "cur_rating": cur_rating,
            "old_rating": old_rating,
            "rating_delta": rating_delta,
            "cur_rank": cur_rank,
            "old_rank": old_rank,
            "rank_delta": rank_delta,
            "baseline_label": baseline_label,
        })

    if not rows:
        return []

    risers = sorted(rows, key=lambda x: x["rating_delta"], reverse=True)[:6]
    fallers = sorted(rows, key=lambda x: x["rating_delta"])[:6]

    out = []
    for x in risers:
        rank_txt = ""
        if x["rank_delta"] is not None:
            rank_txt = f" · rank {fmt_signed(x['rank_delta'], '')}"
        out.append({
            "label": f"{x['team']} rising",
            "value": fmt_signed(x["rating_delta"], " pts"),
            "note": f"{x['conference']} · {x['baseline_label']} {x['old_rating']:.1f} → current {x['cur_rating']:.1f}{rank_txt}",
            "tone": "good"
        })

    for x in fallers:
        rank_txt = ""
        if x["rank_delta"] is not None:
            rank_txt = f" · rank {fmt_signed(x['rank_delta'], '')}"
        out.append({
            "label": f"{x['team']} falling",
            "value": fmt_signed(x["rating_delta"], " pts"),
            "note": f"{x['conference']} · {x['baseline_label']} {x['old_rating']:.1f} → current {x['cur_rating']:.1f}{rank_txt}",
            "tone": "bad"
        })

    return out


def current_cards_for_week(db, angles, wk):
    cards = []
    games = [g for g in db.get("games", []) if game_week(g) == int(wk)]
    tmap = team_map(db)

    # Biggest direct model-vs-market game edges.
    edge_rows = []
    for g in games:
        for row in [spread_edge_row(g), total_edge_row(g)]:
            if row:
                edge_rows.append((row["abs_edge"], row))
    edge_rows = [x[1] for x in sorted(edge_rows, key=lambda x: x[0], reverse=True)]

    add_card(
        cards,
        f"Week {wk} Biggest Game Edges",
        "Current spread/total market lines compared directly against the model projection.",
        edge_rows,
        "#schedule"
    )

    # Games of the week.
    ranked = []
    for g in games:
        a = tmap.get(g.get("away_team"), {})
        h = tmap.get(g.get("home_team"), {})
        ar = n(a.get("rank")) or 999
        hr = n(h.get("rank")) or 999
        quality = min(ar, hr) * 2 + max(ar, hr) * 0.25
        ranked.append((quality, g, ar, hr))

    rows = []
    for _, g, ar, hr in sorted(ranked, key=lambda x: x[0])[:12]:
        rows.append({
            "label": game_label(g),
            "value": projected_score_text(g),
            "note": f"{model_spread_total_text(g)} · {market_spread_total_text(g)}",
            "tone": ""
        })

    add_card(
        cards,
        f"Week {wk} Games of the Week",
        "Highest-profile upcoming games by team rank and market availability.",
        rows,
        "#schedule"
    )

    # Week-specific daily betting angles.
    rows = []
    if not angles.empty and "week" in angles.columns:
        aa = angles[angles["week"].astype(str).isin([str(int(wk)), str(float(wk))])]
    else:
        aa = pd.DataFrame()

    if not aa.empty:
        ge = aa[aa["category"].astype(str).str.contains("Game line edge", case=False, na=False)].head(12)
        for _, r in ge.iterrows():
            rows.append({
                "label": clean(r.get("title")),
                "value": "",
                "note": clean(r.get("reason")),
                "tone": "good"
            })

    add_card(
        cards,
        f"Week {wk} Daily Betting Engine Edges",
        "Game edges from the daily betting agent for this selected week.",
        rows,
        "#schedule"
    )

    # Game line moves for selected week.
    rows = []
    if not aa.empty:
        moves = aa[aa["category"].astype(str).str.contains("Game line move", case=False, na=False)].head(12)
        for _, r in moves.iterrows():
            rows.append({
                "label": clean(r.get("title")),
                "value": "",
                "note": clean(r.get("reason")),
                "tone": ""
            })

    add_card(
        cards,
        f"Week {wk} Game Line Moves",
        "Spread/total point moves only; price-only moves are excluded.",
        rows,
        "#line-history"
    )

    # Betting spots for selected week.
    rows = []
    spots = Path("data/signals/game_betting_angles_2026.csv")
    if spots.exists():
        df = pd.read_csv(spots)
        if "week" in df.columns:
            df = df[df["week"].astype(str).isin([str(int(wk)), str(float(wk))])]

        # Pull the broader set of matchup-context items we care about on matchup pages.
        wanted = (
            "coach|1h|2h|half|total|coin|toss|travel|rp|returning|injury|spot|"
            "variance|schedule|lookahead|sandwich|rest|road"
        )
        keep = df[
            df["angle_key"].astype(str).str.contains(wanted, case=False, na=False)
            | df["angle_label"].astype(str).str.contains(wanted, case=False, na=False)
            | df["reason"].astype(str).str.contains(wanted, case=False, na=False)
        ].copy()

        # Prefer clearer/actionable items before generic variance flags.
        def priority(row):
            txt = (clean(row.get("angle_key")) + " " + clean(row.get("angle_label"))).lower()
            if "injury" in txt: return 1
            if "coach_1h" in txt or "1h" in txt: return 2
            if "coach_2h" in txt or "2h" in txt: return 3
            if "coach_ats" in txt: return 4
            if "coin" in txt or "toss" in txt: return 5
            if "travel" in txt or "schedule" in txt or "spot" in txt: return 6
            if "rp" in txt or "returning" in txt: return 7
            if "variance" in txt: return 8
            return 9

        keep["_priority"] = keep.apply(priority, axis=1)
        keep = keep.sort_values(["_priority"]).head(18)

        seen = set()
        for _, r in keep.iterrows():
            game = f"{clean(r.get('away_team'))} at {clean(r.get('home_team'))}"
            key = clean(r.get("angle_key")).lower()
            label = clean(r.get("angle_label"))
            side = clean(r.get("side_team")) or clean(r.get("team"))
            reason = clean(r.get("reason"))

            if "coach_1h" in key or ("1h" in key and "coach" in key):
                value = f"Lean: {side} 1H" if side else "1H coach lean"
                note = f"Takeaway: {value}. {reason}"
            elif "coach_2h" in key or ("2h" in key and "coach" in key):
                value = f"Lean: {side} 2H" if side else "2H coach lean"
                note = f"Takeaway: {value}. {reason}"
            elif "total" in key and "coach" in key:
                value = f"Total lean: {side}" if side else "Coach total lean"
                note = f"Takeaway: {value}. {reason}"
            elif "coach_ats" in key or "coach" in key:
                value = f"Lean: {side} full game" if side else "Coach ATS lean"
                note = f"Takeaway: {value}. {reason}"
            elif "coin" in key or "toss" in key:
                value = "Coin toss / possession edge"
                note = reason
            elif "injury" in key:
                value = "Injury watch"
                note = reason
            elif "travel" in key:
                value = f"Travel spot: {side}" if side else "Travel spot"
                note = reason
            elif "rp" in key or "returning" in key:
                value = f"RP support: {side}" if side else "RP support"
                note = reason
            elif any(x in key for x in ["lookahead", "sandwich", "rest", "road", "schedule", "spot"]):
                value = label or "Schedule spot"
                note = reason
            elif "variance" in key:
                value = "High variance"
                note = "Model disagreement flag. Use as caution/volatility, not a standalone bet. " + reason
            else:
                value = label
                note = reason

            dedupe = (game, value, note[:60])
            if dedupe in seen:
                continue
            seen.add(dedupe)

            rows.append({
                "label": game,
                "value": value,
                "note": note,
                "tone": "good" if any(x in value.lower() for x in ["lean:", "support", "edge"]) else ""
            })

            if len(rows) >= 12:
                break

    add_card(
        cards,
        f"Week {wk} Betting Spots",
        "Clear takeaways from coach ATS, 1H/2H, totals, coin toss, schedule, RP, injury, travel, and variance signals.",
        rows,
        "#schedule"
    )

    # Ratings risers/fallers.
    add_card(
        cards,
        f"Week {wk} Ratings Risers / Fallers",
        "Biggest rating movement versus the frozen preseason baseline. During the season this becomes the weekly movement snapshot after ratings refresh.",
        ratings_mover_rows(db, wk),
        "#rankings"
    )

    # Futures are not week-specific, but keep visible in each weekly view.
    build_futures_cards(db, cards, "Biggest")

    return cards

def preseason_cards(db, angles):
    cards = []
    market_by_team, wt_by_team = market_rows_by_team(db)

    snap = Path("data/snapshots/preseason/team_preseason_snapshot.csv")
    pre = pd.read_csv(snap) if snap.exists() else pd.DataFrame()

    rows = []
    if not pre.empty:
        for _, r in pre.iterrows():
            team = clean(r.get("team"))
            proj = n(r.get("avg_total_wins"))
            total = wt_by_team.get(team)
            if proj is None or total is None:
                continue
            edge = proj - total
            if abs(edge) < 0.35:
                continue
            side = "Over" if edge > 0 else "Under"
            rows.append((abs(edge), {
                "label": f"{team} {side} {total:g}",
                "value": fmt_signed(edge, " wins"),
                "note": f"Preseason projection {proj:.2f} vs current market {total:g}",
                "tone": "good" if abs(edge) >= 0.6 else ""
            }))

    add_card(
        cards,
        "Preseason Win Total Value",
        "Frozen preseason projected wins vs current market win totals.",
        [x[1] for x in sorted(rows, key=lambda x: x[0], reverse=True)],
        "#futures"
    )

    rows = []
    if not pre.empty:
        for _, r in pre.iterrows():
            team = clean(r.get("team"))
            model = n(r.get("conference_title_pct"))
            if model is not None and model > 1:
                model /= 100
            mkt = market_by_team.get(team, {})
            implied = mkt.get("implied")
            if model is None or implied is None:
                continue
            edge = model - implied
            if edge <= 0.03:
                continue
            rows.append((edge, {
                "label": f"{team} conference title",
                "value": f"{edge*100:+.1f} pts",
                "note": f"Preseason model {fmt_pct(model)} vs market {fmt_pct(implied)} · {mkt.get('odds') or '—'} {mkt.get('book') or ''}",
                "tone": "good"
            }))

    add_card(
        cards,
        "Preseason Conference Futures Value",
        "Frozen preseason title odds vs current market price.",
        [x[1] for x in sorted(rows, key=lambda x: x[0], reverse=True)],
        "#futures"
    )

    if not angles.empty:
        rows = []
        game_edges = angles[angles["category"].astype(str).str.contains("Game line edge", case=False, na=False)].head(12)
        for _, r in game_edges.iterrows():
            rows.append({
                "label": clean(r.get("title")),
                "value": "",
                "note": clean(r.get("reason")),
                "tone": "good"
            })
        add_card(cards, "Preseason Game Line Edges", "Current market edges shown in preseason mode for betting prep.", rows, "#schedule")

        rows = []
        moves = angles[angles["category"].astype(str).str.contains("Game line move|Market move", case=False, na=False)].head(12)
        for _, r in moves.iterrows():
            rows.append({
                "label": clean(r.get("title")),
                "value": "",
                "note": clean(r.get("reason")),
                "tone": ""
            })
        add_card(cards, "Preseason Market Moves", "Game line moves, win-total moves, and futures movement.", rows, "#line-history")

        rows = []
        arbs = angles[angles["category"].astype(str).str.contains("Arbitrage|Middle", case=False, na=False)].head(12)
        for _, r in arbs.iterrows():
            rows.append({
                "label": clean(r.get("title")),
                "value": "",
                "note": clean(r.get("reason")),
                "tone": "good"
            })
        add_card(cards, "Arbs / Middles", "Best current market inefficiencies.", rows, "#betting")

    return cards

def main():
    db = load_db()
    games = db.get("games", [])
    weeks = sorted({game_week(g) for g in games if game_week(g) is not None})

    angles_path = Path("data/agents/daily_betting_angles.csv")
    angles = pd.read_csv(angles_path) if angles_path.exists() else pd.DataFrame()

    current_cards_by_week = {str(w): current_cards_for_week(db, angles, w) for w in weeks}

    payload = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "weeks": weeks,
        "default_week": weeks[0] if weeks else None,
        "current_cards_by_week": current_cards_by_week,
        "preseason_cards": preseason_cards(db, angles)
    }

    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("weeks:", weeks)
    print("default_week:", payload["default_week"])
    print("preseason cards:", len(payload["preseason_cards"]))
    for w in weeks[:3]:
        print("week", w, "cards", len(current_cards_by_week[str(w)]))

if __name__ == "__main__":
    main()
