#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import pandas as pd

OUTDIR = Path("data/agents")
OUTDIR.mkdir(parents=True, exist_ok=True)

ARBS = Path("market_arbitrage_opportunities.csv")
MOVES = Path("daily_market_movement_report.csv")
OUT_CSV = OUTDIR / "daily_betting_angles.csv"
OUT_MD = OUTDIR / "daily_betting_angles.md"

def read_csv(path):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()

def add_angle(rows, category, title, team="", grade="", score="", reason="", action="Watchlist", source=""):
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
    })

def main():
    rows = []

    arbs = read_csv(ARBS)
    moves = read_csv(MOVES)

    # 1. Arbs / no-vig / strong middles
    if not arbs.empty:
        true_arbs = arbs[arbs["type"].eq("Arbitrage")].copy()
        if "edge_pct" in true_arbs.columns:
            true_arbs["edge_pct_num"] = pd.to_numeric(true_arbs["edge_pct"], errors="coerce")
            true_arbs = true_arbs.sort_values("edge_pct_num", ascending=False)

        for _, r in true_arbs.head(15).iterrows():
            add_angle(
                rows,
                category="Arbitrage",
                title=f"{r.get('team')} {r.get('side_1')} / {r.get('side_2')}",
                team=r.get("team", ""),
                grade="ARB",
                score=r.get("edge_pct", ""),
                reason=f"{r.get('book_1')} {r.get('odds_1')} vs {r.get('book_2')} {r.get('odds_2')} on same total {r.get('win_total')}.",
                action="Line check now",
                source="market_arbitrage_opportunities.csv",
            )

        strong_mids = arbs[arbs["quality"].isin(["Strong middle", "Playable middle"])].copy()
        if "middle_score" in strong_mids.columns:
            strong_mids["middle_score_num"] = pd.to_numeric(strong_mids["middle_score"], errors="coerce")
            strong_mids = strong_mids.sort_values("middle_score_num", ascending=False)

        for _, r in strong_mids.head(10).iterrows():
            add_angle(
                rows,
                category="Middle",
                title=f"{r.get('team')} {r.get('side_1')} / {r.get('side_2')}",
                team=r.get("team", ""),
                grade=r.get("quality", ""),
                score=r.get("middle_score", ""),
                reason=f"{r.get('book_1')} {r.get('odds_1')} and {r.get('book_2')} {r.get('odds_2')}; {r.get('notes')}",
                action="Line check",
                source="market_arbitrage_opportunities.csv",
            )

    # 2. Biggest recent market moves
    if not moves.empty:
        moves["abs_imp"] = pd.to_numeric(moves.get("implied_prob_change_pct"), errors="coerce").abs()
        big_moves = moves.sort_values("abs_imp", ascending=False).head(20)

        for _, r in big_moves.iterrows():
            add_angle(
                rows,
                category="Market move",
                title=f"{r.get('team')} {r.get('field')} moved",
                team=r.get("team", ""),
                grade="MOVE",
                score=r.get("implied_prob_change_pct", ""),
                reason=f"{r.get('book')} {r.get('field')}: {r.get('previous')} → {r.get('latest')} on {r.get('move_date', r.get('snapshot_latest', ''))}.",
                action="Review move / search news",
                source="daily_market_movement_report.csv",
            )

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)

    lines = []
    lines.append(f"# Daily NCAAF Betting Angles — {datetime.now().date().isoformat()}")
    lines.append("")
    if out.empty:
        lines.append("No angles generated.")
    else:
        for cat, g in out.groupby("category", sort=False):
            lines.append(f"## {cat}")
            lines.append("")
            for _, r in g.iterrows():
                lines.append(f"- **{r['title']}** — {r['grade']} {r['score']}")
                lines.append(f"  - {r['reason']}")
                lines.append(f"  - Action: {r['action']}")
            lines.append("")

    OUT_MD.write_text("\n".join(lines))

    print(f"Wrote {OUT_CSV}: {len(out)} rows")
    print(f"Wrote {OUT_MD}")

if __name__ == "__main__":
    main()
