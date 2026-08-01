#!/usr/bin/env python3
import math
from pathlib import Path

import pandas as pd


WIN_HISTORY = Path("market_win_totals_history.csv")
CONF_HISTORY = Path("market_conference_futures_history.csv")
OUT = Path("daily_market_movement_report.csv")

DAYS_BACK = 7


def american_to_prob(odds):
    try:
        o = float(odds)
    except Exception:
        return None
    if o == 0 or math.isnan(o):
        return None
    if o < 0:
        return abs(o) / (abs(o) + 100.0)
    return 100.0 / (o + 100.0)


def fmt_odds(x):
    if pd.isna(x):
        return ""
    try:
        n = int(float(x))
        return f"+{n}" if n > 0 else str(n)
    except Exception:
        return str(x)



TEAM_ALIASES = {
    "Sacramento St.": "Sacramento State",
    "Sacramento St": "Sacramento State",
    "K State": "Kansas State",
    "Kansas St.": "Kansas State",
    "Kansas St": "Kansas State",
    "UNC": "North Carolina",
    "JMU": "James Madison",
    "UConn": "Connecticut",
    "Miami Florida": "Miami-FL",
    "Miami (FL)": "Miami-FL",
    "GA Tech": "Georgia Tech",
    "FIU": "Florida International",
    "MTSU": "Middle Tennessee",
    "WKU": "Western Kentucky",
    "NMSU": "New Mexico State",
    "Sam Houston St.": "Sam Houston",
    "Sam Houston St": "Sam Houston",
    "Oregon St.": "Oregon State",
    "Oregon St": "Oregon State",
    "Washington St.": "Washington State",
    "Washington St": "Washington State",
    "San Diego St.": "San Diego State",
    "San Diego St": "San Diego State",
    "Colorado St.": "Colorado State",
    "Colorado St": "Colorado State",
    "Fresno St.": "Fresno State",
    "Fresno St": "Fresno State",
    "Utah St.": "Utah State",
    "Utah St": "Utah State",
    "Boise St.": "Boise State",
    "Boise St": "Boise State",
    "Kennesaw St.": "Kennesaw State",
    "Kennesaw St": "Kennesaw State",
    "Georgia St.": "Georgia State",
    "Georgia St": "Georgia State",
    "San Jose St.": "San Jose State",
    "San Jose St": "San Jose State",
    "Arkansas St.": "Arkansas State",
    "Arkansas St": "Arkansas State",
    "Kent St.": "Kent State",
    "Kent St": "Kent State",
}


def canon_team_name(team):
    if pd.isna(team):
        return team
    s = str(team).strip()
    return TEAM_ALIASES.get(s, s)


def fmt_win_total(x):
    if pd.isna(x):
        return ""
    try:
        n = float(x)
        return f"{n:.1f}".rstrip("0").rstrip(".")
    except Exception:
        return str(x)


def pct_change(prev, latest):
    p0 = american_to_prob(prev)
    p1 = american_to_prob(latest)
    if p0 is None or p1 is None:
        return None
    return round((p1 - p0) * 100, 2)


def norm_date_col(df):
    if "snapshot_date" not in df.columns:
        raise ValueError("Missing snapshot_date column")
    df = df.copy()
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"]).dt.date.astype(str)
    return df


def build_win_total_moves():
    if not WIN_HISTORY.exists():
        return []

    df = norm_date_col(pd.read_csv(WIN_HISTORY))
    if df.empty:
        return []

    required = ["snapshot_date", "season", "team", "book", "win_total", "over_odds", "under_odds"]
    for c in required:
        if c not in df.columns:
            df[c] = pd.NA

    rows = []
    keys = ["season", "team", "book"]

    df = df.sort_values(keys + ["snapshot_date"])

    latest_date = max(df["snapshot_date"])
    cutoff = (pd.to_datetime(latest_date) - pd.Timedelta(days=DAYS_BACK - 1)).date().isoformat()

    for key, g in df.groupby(keys, dropna=False):
        g = g.drop_duplicates("snapshot_date", keep="last").sort_values("snapshot_date")
        prev = None
        for _, cur in g.iterrows():
            if prev is not None and cur["snapshot_date"] >= cutoff:
                season, team, book = key
                team_display = canon_team_name(team)
                conf = cur.get("conference", "")

                # Line movement
                if not pd.isna(prev.get("win_total")) and not pd.isna(cur.get("win_total")):
                    if float(prev.get("win_total")) != float(cur.get("win_total")):
                        rows.append({
                            "market": "Win Total",
                            "snapshot_prev": prev["snapshot_date"],
                            "snapshot_latest": cur["snapshot_date"],
                            "move_date": cur["snapshot_date"],
                            "season": season,
                            "conference": conf,
                            "team": team_display,
                            "book": book,
                            "field": "Win Total",
                            "previous": str(prev.get("win_total")),
                            "latest": str(cur.get("win_total")),
                            "change": round(float(cur.get("win_total")) - float(prev.get("win_total")), 2),
                            "implied_prob_change_pct": "",
                            "summary": f"{team_display} {book} win total moved {prev.get('win_total')} → {cur.get('win_total')}",
                        })

                # Over odds movement
                if not pd.isna(prev.get("over_odds")) and not pd.isna(cur.get("over_odds")):
                    if int(float(prev.get("over_odds"))) != int(float(cur.get("over_odds"))):
                        imp = pct_change(prev.get("over_odds"), cur.get("over_odds"))
                        rows.append({
                            "market": "Win Total",
                            "snapshot_prev": prev["snapshot_date"],
                            "snapshot_latest": cur["snapshot_date"],
                            "move_date": cur["snapshot_date"],
                            "season": season,
                            "conference": conf,
                            "team": team_display,
                            "book": book,
                            "field": f"Over {fmt_win_total(cur.get('win_total'))} wins",
                            "previous": fmt_odds(prev.get("over_odds")),
                            "latest": fmt_odds(cur.get("over_odds")),
                            "change": int(float(cur.get("over_odds"))) - int(float(prev.get("over_odds"))),
                            "implied_prob_change_pct": imp,
                            "summary": f"{team_display} {book} Over {fmt_win_total(cur.get('win_total'))} moved {fmt_odds(prev.get('over_odds'))} → {fmt_odds(cur.get('over_odds'))}",
                        })

                # Under odds movement
                if not pd.isna(prev.get("under_odds")) and not pd.isna(cur.get("under_odds")):
                    if int(float(prev.get("under_odds"))) != int(float(cur.get("under_odds"))):
                        imp = pct_change(prev.get("under_odds"), cur.get("under_odds"))
                        rows.append({
                            "market": "Win Total",
                            "snapshot_prev": prev["snapshot_date"],
                            "snapshot_latest": cur["snapshot_date"],
                            "move_date": cur["snapshot_date"],
                            "season": season,
                            "conference": conf,
                            "team": team_display,
                            "book": book,
                            "field": f"Under {fmt_win_total(cur.get('win_total'))} wins",
                            "previous": fmt_odds(prev.get("under_odds")),
                            "latest": fmt_odds(cur.get("under_odds")),
                            "change": int(float(cur.get("under_odds"))) - int(float(prev.get("under_odds"))),
                            "implied_prob_change_pct": imp,
                            "summary": f"{team_display} {book} Under {fmt_win_total(cur.get('win_total'))} moved {fmt_odds(prev.get('under_odds'))} → {fmt_odds(cur.get('under_odds'))}",
                        })

            prev = cur

    return rows


def build_conference_future_moves():
    if not CONF_HISTORY.exists():
        return []

    df = norm_date_col(pd.read_csv(CONF_HISTORY))
    if df.empty:
        return []

    required = ["snapshot_date", "season", "conference", "team", "book", "american_odds"]
    for c in required:
        if c not in df.columns:
            df[c] = pd.NA

    rows = []
    keys = ["season", "conference", "team", "book"]

    df = df.sort_values(keys + ["snapshot_date"])

    latest_date = max(df["snapshot_date"])
    cutoff = (pd.to_datetime(latest_date) - pd.Timedelta(days=DAYS_BACK - 1)).date().isoformat()

    for key, g in df.groupby(keys, dropna=False):
        g = g.drop_duplicates("snapshot_date", keep="last").sort_values("snapshot_date")
        prev = None
        for _, cur in g.iterrows():
            if prev is not None and cur["snapshot_date"] >= cutoff:
                season, conf, team, book = key
                team_display = canon_team_name(team)
                if not pd.isna(prev.get("american_odds")) and not pd.isna(cur.get("american_odds")):
                    if int(float(prev.get("american_odds"))) != int(float(cur.get("american_odds"))):
                        imp = pct_change(prev.get("american_odds"), cur.get("american_odds"))
                        rows.append({
                            "market": "Conference Future",
                            "snapshot_prev": prev["snapshot_date"],
                            "snapshot_latest": cur["snapshot_date"],
                            "move_date": cur["snapshot_date"],
                            "season": season,
                            "conference": conf,
                            "team": team_display,
                            "book": book,
                            "field": "Title Odds",
                            "previous": fmt_odds(prev.get("american_odds")),
                            "latest": fmt_odds(cur.get("american_odds")),
                            "change": int(float(cur.get("american_odds"))) - int(float(prev.get("american_odds"))),
                            "implied_prob_change_pct": imp,
                            "summary": f"{team_display} {book} conference title moved {fmt_odds(prev.get('american_odds'))} → {fmt_odds(cur.get('american_odds'))}",
                        })

            prev = cur

    return rows


def main():
    rows = build_win_total_moves() + build_conference_future_moves()
    out = pd.DataFrame(rows)

    cols = [
        "market",
        "snapshot_prev",
        "snapshot_latest",
        "move_date",
        "season",
        "conference",
        "team",
        "book",
        "field",
        "previous",
        "latest",
        "change",
        "implied_prob_change_pct",
        "summary",
    ]

    if out.empty:
        out = pd.DataFrame(columns=cols)
    else:
        # Biggest implied-probability moves first; line moves without implied change go lower.
        out["_abs_imp"] = pd.to_numeric(out["implied_prob_change_pct"], errors="coerce").abs().fillna(0)
        out = out.sort_values(["move_date", "_abs_imp"], ascending=[False, False]).drop(columns=["_abs_imp"])
        out = out[cols]

    out.to_csv(OUT, index=False)

    print(f"Wrote {OUT}: {len(out)} rows")
    if len(out):
        print("Move dates:")
        print(out["move_date"].value_counts().sort_index().to_string())
        print("\nMarkets:")
        print(out["market"].value_counts().to_string())


if __name__ == "__main__":
    main()
