#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import pandas as pd
import re

OUTDIR = Path("data/agents")
OUTDIR.mkdir(parents=True, exist_ok=True)

ARBS = Path("market_arbitrage_opportunities.csv")
MOVES = Path("daily_market_movement_report.csv")
OUT_CSV = OUTDIR / "daily_betting_angles.csv"
OUT_MD = OUTDIR / "daily_betting_angles.md"

TEAM_ALIASES = {
    "ND State": "North Dakota State",
    "N Dakota State": "North Dakota State",
    "E. Michigan": "Eastern Michigan",
    "E Michigan": "Eastern Michigan",
    "App State": "Appalachian State",
    "Appalachian St.": "Appalachian State",
    "Appalachian St": "Appalachian State",
    "Coastal Car": "Coastal Carolina",
    "Middle Tenn": "Middle Tennessee",
    "LA Tech": "Louisiana Tech",
    "Miami (OH)": "Miami-OH",
    "San Jose St": "San Jose State",
    "K State": "Kansas State",
    "UNC": "North Carolina",
    "UConn": "Connecticut",
    "WKU": "Western Kentucky",
    "MTSU": "Middle Tennessee",
    "FIU": "Florida International",
    "GA Tech": "Georgia Tech",
    "Oregon St": "Oregon State",
    "Washington St": "Washington State",
    "Utah St": "Utah State",
    "Boise St": "Boise State",
    "Fresno St": "Fresno State",
    "Colorado St": "Colorado State",
    "San Diego St": "San Diego State",
    "Arkansas St": "Arkansas State",
    "Georgia St": "Georgia State",
    "Kent St": "Kent State",
    "Ball St": "Ball State",
    "New Mexico St": "New Mexico State",
    "Sam Houston St": "Sam Houston",
    "Sacramento St.": "Sacramento State",
    "Sacramento St": "Sacramento State",
}

MAX_BAD_MIDDLE_JUICE = -250


def canon_team(team):
    s = str(team or "").strip()
    return TEAM_ALIASES.get(s, s)


def read_csv(path):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def odds_int(x):
    try:
        return int(float(str(x).replace("+", "")))
    except Exception:
        return None


def american_to_prob(odds):
    o = odds_int(odds)
    if o is None or o == 0:
        return None
    if o < 0:
        return abs(o) / (abs(o) + 100.0)
    return 100.0 / (o + 100.0)


def fmt_prob(p):
    if p is None:
        return ""
    return f"{p*100:.1f}%"


def implied_prob_move_text(prev, latest):
    p0 = american_to_prob(prev)
    p1 = american_to_prob(latest)
    if p0 is None or p1 is None:
        return "", None
    pp = (p1 - p0) * 100.0
    return f"implied probability {fmt_prob(p0)} → {fmt_prob(p1)} ({pp:+.1f} pp)", pp


def fmt_line_or_price_move(field, prev, latest):
    field_s = str(field or "")
    # American odds/price moves should be evaluated by implied probability, not raw odds difference.
    if re.search(r"price|odds", field_s, re.I):
        imp_txt, pp = implied_prob_move_text(prev, latest)
        if imp_txt:
            return f"price {prev} → {latest}; {imp_txt}", pp
    try:
        diff = float(latest) - float(prev)
        return f"line {prev} → {latest} ({diff:+.1f} pts)", abs(diff)
    except Exception:
        return f"{prev} → {latest}", None


def playable_middle(row):
    """Keep only middles that are actually actionable enough to review.

    Hides things like Over 0.5 -10000 / Under 6.5 -175.
    """
    if row.get("type") != "Middle":
        return True

    o1 = odds_int(row.get("odds_1"))
    o2 = odds_int(row.get("odds_2"))

    if o1 is None or o2 is None:
        return False

    if o1 < MAX_BAD_MIDDLE_JUICE or o2 < MAX_BAD_MIDDLE_JUICE:
        return False

    return row.get("quality") in {"Strong middle", "Playable middle"}


def dedupe_arbs(arbs):
    if arbs.empty:
        return arbs

    arbs = arbs.copy()
    arbs["team"] = arbs["team"].map(canon_team)
    arbs["edge_num"] = pd.to_numeric(arbs.get("edge_pct"), errors="coerce")

    # Keep best arb per team + win total.
    arbs = arbs.sort_values("edge_num", ascending=False)
    arbs = arbs.drop_duplicates(subset=["team", "win_total"], keep="first")
    return arbs


def dedupe_moves(moves):
    if moves.empty:
        return moves

    moves = moves.copy()
    moves["team"] = moves["team"].map(canon_team)
    moves["abs_imp"] = pd.to_numeric(moves.get("implied_prob_change_pct"), errors="coerce").abs()

    # Keep the biggest recent move per team + book + field.
    moves = moves.sort_values("abs_imp", ascending=False)
    moves = moves.drop_duplicates(subset=["team", "book", "field"], keep="first")
    return moves


def add_angle(rows, category, title, team="", grade="", score="", reason="", action="Watchlist", source="", research_query=""):
    team = canon_team(team)
    rows.append({
        "run_date": datetime.now().date().isoformat(),
        "category": category,
        "title": title,
        "team": team,
        "grade": grade,
        "score": score,
        "reason": reason,
        "action": action,
        "source": source,
        "research_query": research_query,
    })


def research_query_for_move(team, field):
    team = canon_team(team)
    field = str(field or "").replace("Win Total", "").replace("wins", "").strip()
    if field:
        return f"{team} football 2026 win total {field} line move injury roster depth chart news"
    return f"{team} football 2026 win total line move injury roster depth chart news"


def main():
    rows = []

    arbs = read_csv(ARBS)
    moves = read_csv(MOVES)

    if not arbs.empty:
        arbs["team"] = arbs["team"].map(canon_team)

        true_arbs = arbs[arbs["type"].eq("Arbitrage")].copy()
        true_arbs = dedupe_arbs(true_arbs)
        true_arbs["edge_num"] = pd.to_numeric(true_arbs.get("edge_pct"), errors="coerce")
        true_arbs = true_arbs.sort_values("edge_num", ascending=False)

        for _, r in true_arbs.head(15).iterrows():
            team = canon_team(r.get("team", ""))
            add_angle(
                rows,
                category="Arbitrage",
                title=f"{team} {r.get('side_1')} / {r.get('side_2')}",
                team=team,
                grade="ARB",
                score=r.get("edge_pct", ""),
                reason=f"{r.get('book_1')} {r.get('odds_1')} vs {r.get('book_2')} {r.get('odds_2')} on same total {r.get('win_total')}.",
                action="Line check now",
                source="market_arbitrage_opportunities.csv",
                research_query="",
            )

        mids = arbs[arbs["type"].eq("Middle")].copy()
        mids = mids[mids.apply(playable_middle, axis=1)]
        if not mids.empty:
            mids["middle_score_num"] = pd.to_numeric(mids.get("middle_score"), errors="coerce")
            mids = mids.sort_values("middle_score_num", ascending=False)
            mids = mids.drop_duplicates(subset=["team", "win_total"], keep="first")

        for _, r in mids.head(10).iterrows():
            team = canon_team(r.get("team", ""))
            add_angle(
                rows,
                category="Middle",
                title=f"{team} {r.get('side_1')} / {r.get('side_2')}",
                team=team,
                grade=r.get("quality", ""),
                score=r.get("middle_score", ""),
                reason=f"{r.get('book_1')} {r.get('odds_1')} and {r.get('book_2')} {r.get('odds_2')}; {r.get('notes')}",
                action="Line check",
                source="market_arbitrage_opportunities.csv",
                research_query="",
            )

    if not moves.empty:
        moves["team"] = moves["team"].map(canon_team)
        moves["abs_imp"] = pd.to_numeric(moves.get("implied_prob_change_pct"), errors="coerce").abs()

        # Combine line moves and opposite-side price moves for same team/book/date into one report row.
        win_moves = moves[moves["market"].astype(str).str.contains("Win", case=False, na=False)].copy()
        combined = []

        def extract_total(field):
            m = re.search(r"(Over|Under)\s+([0-9]+(?:\.[0-9]+)?)", str(field), re.I)
            return m.group(2) if m else ""

        win_moves["move_total"] = win_moves["field"].map(extract_total)
        win_moves["side"] = win_moves["field"].astype(str).str.extract(r"^(Over|Under)", expand=False).fillna("")

        # Fill blank move_total on "Win Total" line moves using the latest total.
        for idx, r in win_moves[win_moves["move_total"].eq("")].iterrows():
            if str(r.get("field")) == "Win Total":
                win_moves.loc[idx, "move_total"] = str(r.get("latest"))

        group_cols = ["team", "book", "move_date", "move_total"]
        for key, g in win_moves.groupby(group_cols, dropna=False):
            team, book, move_date, total = key
            g = g.sort_values("abs_imp", ascending=False)

            line_move = g[g["field"].astype(str).eq("Win Total")]
            over = g[g["side"].eq("Over")]
            under = g[g["side"].eq("Under")]

            pieces = []
            scores = []

            if len(line_move):
                lm = line_move.iloc[0]
                pieces.append(f"line {lm.get('previous')} → {lm.get('latest')}")
                # Give line moves a high review score so they are not nan / lost.
                scores.append(25.0)

            if len(over):
                o = over.iloc[0]
                txt, pp = implied_prob_move_text(o.get("previous"), o.get("latest"))
                pieces.append(f"Over {total}: {o.get('previous')} → {o.get('latest')}" + (f" ({txt})" if txt else ""))
                scores.append(abs(float(pp)) if pp is not None else float(o.get("abs_imp") or 0))

            if len(under):
                u = under.iloc[0]
                txt, pp = implied_prob_move_text(u.get("previous"), u.get("latest"))
                pieces.append(f"Under {total}: {u.get('previous')} → {u.get('latest')}" + (f" ({txt})" if txt else ""))
                scores.append(abs(float(pp)) if pp is not None else float(u.get("abs_imp") or 0))

            if not pieces:
                continue

            title = f"{team} {total} win total moved at {book}"
            reason = "; ".join(pieces) + f" on {move_date}."
            combined.append({
                "team": team,
                "title": title,
                "score": max(scores) if scores else 0,
                "reason": reason,
                "field": f"Win Total {total}",
                "move_date": move_date,
            })

        # Add non-win-total movement rows separately, if any.
        # For game-line price moves, use implied probability change, not raw American-odds subtraction.
        non_win = moves[~moves["market"].astype(str).str.contains("Win", case=False, na=False)].copy()
        for _, r in non_win.iterrows():
            field = r.get("field")
            prev = r.get("previous")
            latest = r.get("latest")
            move_txt, derived_score = fmt_line_or_price_move(field, prev, latest)
            score = float(r.get("abs_imp") or 0)
            if derived_score is not None:
                score = abs(float(derived_score))
            combined.append({
                "team": canon_team(r.get("team", "")),
                "title": f"{canon_team(r.get('team', ''))} {field} moved",
                "score": score,
                "reason": f"{r.get('book')} {field}: {move_txt} on {r.get('move_date', r.get('snapshot_latest', ''))}.",
                "field": field,
                "move_date": r.get("move_date", r.get("snapshot_latest", "")),
            })

        combined = sorted(combined, key=lambda x: x["score"], reverse=True)[:20]

        for r in combined:
            add_angle(
                rows,
                category="Market move",
                title=r["title"],
                team=r["team"],
                grade="MOVE",
                score="",
                reason=r["reason"],
                action="Review move / search news",
                source="daily_market_movement_report.csv",
                research_query=research_query_for_move(r["team"], r["field"]),
            )

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)

    lines = []
    lines.append(f"# Daily NCAAF Betting Angles — {datetime.now().date().isoformat()}")
    lines.append("")
    lines.append("Items are listed in priority order based on arb edge, line movement size, implied-probability movement, and stale-price/middle quality.")
    lines.append("")

    if out.empty:
        lines.append("No angles generated.")
    else:
        for cat, g in out.groupby("category", sort=False):
            lines.append(f"## {cat}")
            lines.append("")
            for _, r in g.iterrows():
                score_txt = f" {r['score']}" if str(r.get('score','')).strip() else ""
                lines.append(f"- **{r['title']}** — {r['grade']}{score_txt}")
                lines.append(f"  - {r['reason']}")
                lines.append(f"  - Action: {r['action']}")
                if r.get("research_query"):
                    lines.append(f"  - Research: `{r['research_query']}`")
            lines.append("")

        research_rows = out[out["research_query"].astype(str).str.len() > 0] if "research_query" in out else pd.DataFrame()
        if not research_rows.empty:
            lines.append("## Research Queue")
            lines.append("")
            for q in research_rows["research_query"].drop_duplicates().head(20):
                lines.append(f"- `{q}`")
            lines.append("")

    OUT_MD.write_text("\n".join(lines))

    print(f"Wrote {OUT_CSV}: {len(out)} rows")
    print(f"Wrote {OUT_MD}")

    if not out.empty:
        print(out.groupby("category").size().to_string())


if __name__ == "__main__":
    main()
