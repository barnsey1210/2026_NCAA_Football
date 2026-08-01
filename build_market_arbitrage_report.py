#!/usr/bin/env python3
import math
from pathlib import Path
import pandas as pd

WIN_FILE = Path("market_win_totals_import.csv")
OUT = Path("market_arbitrage_opportunities.csv")

TEAM_ALIASES = {
    "App State": "Appalachian State",
    "Coastal Car": "Coastal Carolina",
    "E. Michigan": "Eastern Michigan",
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

def canon_team(team):
    s = str(team or "").strip()
    return TEAM_ALIASES.get(s, s)

def implied_prob(odds):
    if pd.isna(odds):
        return None
    o = float(odds)
    if o < 0:
        return abs(o) / (abs(o) + 100)
    return 100 / (o + 100)

def fmt_odds(o):
    if pd.isna(o):
        return ""
    o = int(float(o))
    return f"+{o}" if o > 0 else str(o)

def price_quality(odds):
    """Higher is better. Helps filter awful middles."""
    try:
        o = int(float(odds))
    except Exception:
        return -999
    if o > 0:
        return 100 + o
    return o

def middle_quality(over_odds, under_odds, gap):
    # Simple score: gap matters, plus-money matters, heavy juice hurts.
    oq = price_quality(over_odds)
    uq = price_quality(under_odds)
    score = gap * 25
    for o in [over_odds, under_odds]:
        o = int(float(o))
        if o > 0:
            score += min(25, o / 8)
        elif o >= -130:
            score += 10
        elif o >= -155:
            score += 3
        elif o <= -200:
            score -= 18
        else:
            score -= 8
    return round(score, 1)

def middle_grade(score):
    if score >= 55:
        return "Strong middle"
    if score >= 35:
        return "Playable middle"
    return "Weak middle"

def main():
    df = pd.read_csv(WIN_FILE)

    for col in ["win_total", "over_odds", "under_odds"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["team"] = df["team"].map(canon_team)

    rows = []

    for team, g in df.groupby("team"):
        g = g.copy()

        # Same-line arbitrage/no-vig.
        for total, gt in g.groupby("win_total"):
            overs = gt.dropna(subset=["over_odds"])
            unders = gt.dropna(subset=["under_odds"])

            for _, o in overs.iterrows():
                for _, u in unders.iterrows():
                    if o["book"] == u["book"]:
                        continue

                    po = implied_prob(o["over_odds"])
                    pu = implied_prob(u["under_odds"])
                    if po is None or pu is None:
                        continue

                    hold = po + pu
                    edge_pct = (1 - hold) * 100

                    if edge_pct >= -0.00001:
                        typ = "Arbitrage" if edge_pct > 0.05 else "No-vig / Break-even"
                        rows.append({
                            "type": typ,
                            "quality": typ,
                            "team": team,
                            "win_total": total,
                            "side_1": f"Over {total:g}",
                            "book_1": o["book"],
                            "odds_1": fmt_odds(o["over_odds"]),
                            "side_2": f"Under {total:g}",
                            "book_2": u["book"],
                            "odds_2": fmt_odds(u["under_odds"]),
                            "implied_sum_pct": round(hold * 100, 2),
                            "edge_pct": round(edge_pct, 2),
                            "middle_score": "",
                            "notes": "Same win total, opposite sides.",
                        })

        # Middle opportunities.
        overs = g.dropna(subset=["win_total", "over_odds"])
        unders = g.dropna(subset=["win_total", "under_odds"])

        for _, o in overs.iterrows():
            for _, u in unders.iterrows():
                if o["book"] == u["book"]:
                    continue
                if o["win_total"] < u["win_total"]:
                    gap = u["win_total"] - o["win_total"]
                    if gap < 1:
                        continue

                    score = middle_quality(o["over_odds"], u["under_odds"], gap)
                    grade = middle_grade(score)

                    rows.append({
                        "type": "Middle",
                        "quality": grade,
                        "team": team,
                        "win_total": f"{o['win_total']:g} / {u['win_total']:g}",
                        "side_1": f"Over {o['win_total']:g}",
                        "book_1": o["book"],
                        "odds_1": fmt_odds(o["over_odds"]),
                        "side_2": f"Under {u['win_total']:g}",
                        "book_2": u["book"],
                        "odds_2": fmt_odds(u["under_odds"]),
                        "implied_sum_pct": "",
                        "edge_pct": "",
                        "middle_score": score,
                        "notes": f"Middle gap of {gap:g} wins.",
                    })

    out = pd.DataFrame(rows)

    if not out.empty:
        type_order = {
            "Arbitrage": 0,
            "No-vig / Break-even": 1,
            "Middle": 2,
        }
        quality_order = {
            "Arbitrage": 0,
            "No-vig / Break-even": 1,
            "Strong middle": 2,
            "Playable middle": 3,
            "Weak middle": 4,
        }
        out["_type_order"] = out["type"].map(type_order).fillna(9)
        out["_quality_order"] = out["quality"].map(quality_order).fillna(9)
        out["_edge_sort"] = pd.to_numeric(out["edge_pct"], errors="coerce").fillna(-999)
        out["_middle_sort"] = pd.to_numeric(out["middle_score"], errors="coerce").fillna(-999)

        out = out.sort_values(
            ["_type_order", "_quality_order", "_edge_sort", "_middle_sort", "team"],
            ascending=[True, True, False, False, True]
        ).drop(columns=["_type_order", "_quality_order", "_edge_sort", "_middle_sort"])

    out.to_csv(OUT, index=False)

    print(f"Wrote {OUT}: {len(out)} rows")
    if len(out):
        print("\nCounts:")
        print(out.groupby(["type", "quality"]).size().to_string())
        print("\nTop opportunities:")
        print(out.head(80).to_string(index=False))

if __name__ == "__main__":
    main()
