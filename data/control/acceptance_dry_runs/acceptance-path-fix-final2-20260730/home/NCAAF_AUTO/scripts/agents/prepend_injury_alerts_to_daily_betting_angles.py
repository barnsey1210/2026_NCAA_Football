#!/usr/bin/env python3
from pathlib import Path

import pandas as pd

ANGLES = Path("data/agents/daily_betting_angles.csv")
ALERTS = Path("data/injuries/injury_alerts.csv")

def clean(x):
    return "" if pd.isna(x) else str(x).strip()

def main():
    if not ANGLES.exists():
        print("No daily betting angles file found:", ANGLES)
        return

    if not ALERTS.exists():
        print("No injury alerts file found:", ALERTS)
        return

    angles = pd.read_csv(ANGLES)
    alerts = pd.read_csv(ALERTS)

    if alerts.empty:
        print("No injury alerts to prepend")
        return

    if "alert_tier" in alerts.columns:
        alerts = alerts[~alerts["alert_tier"].astype(str).str.lower().eq("log")].copy()

    if "impact_score" in alerts.columns:
        alerts = alerts[pd.to_numeric(alerts["impact_score"], errors="coerce").fillna(0) > 0].copy()

    if alerts.empty:
        print("No non-log injury alerts to prepend")
        return

    rows = []

    for _, a in alerts.iterrows():
        team = clean(a.get("team"))
        player = clean(a.get("player"))
        pos = clean(a.get("position"))
        status = clean(a.get("status"))
        tier = clean(a.get("alert_tier"))
        impact = clean(a.get("impact_score"))
        importance = clean(a.get("importance_score"))
        url = clean(a.get("item_url"))
        raw = clean(a.get("raw_text"))

        title_parts = [x for x in [team, player, pos, status] if x]
        title = " / ".join(title_parts) if title_parts else clean(a.get("item_title"))

        row = {c: "" for c in angles.columns}

        for c in row:
            lc = c.lower()
            if lc == "category":
                row[c] = "Injury alert"
            elif lc == "title":
                row[c] = f"{tier}: {title}" if tier else title
            elif lc == "edge_type":
                row[c] = "injury_alert"
            elif lc == "edge_value":
                row[c] = impact
            elif lc == "why":
                row[c] = f"Player importance {importance}; injury impact {impact}. {raw[:500]}"
            elif lc == "research":
                row[c] = url
            elif lc == "action":
                row[c] = "Review injury impact against market move, depth chart, and matchup before betting."

        rows.append(row)

    injury_df = pd.DataFrame(rows, columns=angles.columns)

    out = pd.concat([injury_df, angles], ignore_index=True)
    out.to_csv(ANGLES, index=False)

    print("prepended injury alerts:", len(injury_df))
    print("wrote:", ANGLES)

if __name__ == "__main__":
    main()
