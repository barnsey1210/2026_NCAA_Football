#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

import pandas as pd


IN_CSV = Path("data/odds/cfbd_lines_2026.csv")
OUT_CSV = Path("data/odds/season_game_lines_2026.csv")
AUDIT_CSV = Path("data/odds/season_game_lines_2026_audit.csv")

BOOK_PRIORITY = {
    "DraftKings": 1,
    "Bovada": 2,
}


def fmt_spread_text(row) -> str:
    away = row.get("away_team", "")
    home = row.get("home_team", "")
    spread = row.get("market_spread_home")

    if pd.isna(spread):
        return ""

    try:
        spread = float(spread)
    except Exception:
        return ""

    if spread == 0:
        return "PK"

    if spread < 0:
        return f"{home} {spread:g}"

    return f"{away} {-spread:g}"


def main() -> None:
    if not IN_CSV.exists():
        raise SystemExit(f"Missing {IN_CSV}. Run pull_cfbd_lines_2026.py first.")

    df = pd.read_csv(IN_CSV)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    if df.empty:
        pd.DataFrame().to_csv(OUT_CSV, index=False)
        pd.DataFrame().to_csv(AUDIT_CSV, index=False)
        print(f"No CFBD lines available. Wrote empty {OUT_CSV}")
        return

    for col in ["spread", "spread_open", "total", "total_open", "home_moneyline", "away_moneyline"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["book_priority"] = df["book"].map(BOOK_PRIORITY).fillna(99)

    group_cols = ["game_id", "season", "week", "season_type", "date", "away_team", "home_team"]

    rows = []
    audit_rows = []

    for key, g in df.groupby(group_cols, dropna=False):
        game = dict(zip(group_cols, key))
        g = g.copy()
        g["has_spread"] = g["spread"].notna()
        g["has_total"] = g["total"].notna()

        spread_rows = g[g["has_spread"]].sort_values(["book_priority", "book"])
        total_rows = g[g["has_total"]].sort_values(["book_priority", "book"])
        any_rows = g.sort_values(["book_priority", "book"])

        spread_row = spread_rows.iloc[0] if not spread_rows.empty else None
        total_row = total_rows.iloc[0] if not total_rows.empty else None
        display_row = spread_row if spread_row is not None else (total_row if total_row is not None else any_rows.iloc[0])

        market_spread_home = spread_row["spread"] if spread_row is not None else pd.NA
        market_spread_open_home = spread_row["spread_open"] if spread_row is not None else pd.NA
        market_total = total_row["total"] if total_row is not None else pd.NA
        market_total_open = total_row["total_open"] if total_row is not None else pd.NA

        out = {
            **game,
            "market_spread_home": market_spread_home,
            "market_spread_open_home": market_spread_open_home,
            "market_spread_text": "",
            "market_spread_book": spread_row["book"] if spread_row is not None else "",
            "market_formatted_spread": spread_row["formatted_spread"] if spread_row is not None else "",
            "market_total": market_total,
            "market_total_open": market_total_open,
            "market_total_book": total_row["book"] if total_row is not None else "",
            "home_moneyline": display_row.get("home_moneyline", pd.NA),
            "away_moneyline": display_row.get("away_moneyline", pd.NA),
            "home_moneyline_implied": display_row.get("home_moneyline_implied", pd.NA),
            "away_moneyline_implied": display_row.get("away_moneyline_implied", pd.NA),
            "books_count": g["book"].nunique(),
            "books_available": ",".join(sorted(g["book"].dropna().astype(str).unique())),
            "line_source": "CFBD Lines",
            "pulled_at": display_row.get("pulled_at", ""),
        }
        out["market_spread_text"] = fmt_spread_text(out)
        rows.append(out)

        audit_rows.append({
            **game,
            "books_count": g["book"].nunique(),
            "books_available": ",".join(sorted(g["book"].dropna().astype(str).unique())),
            "has_spread": bool(g["has_spread"].any()),
            "has_total": bool(g["has_total"].any()),
            "selected_spread_book": out["market_spread_book"],
            "selected_total_book": out["market_total_book"],
            "line_source": "CFBD Lines",
        })

    out_df = pd.DataFrame(rows)
    audit_df = pd.DataFrame(audit_rows)

    out_df = out_df.sort_values(["week", "date", "away_team", "home_team"])
    audit_df = audit_df.sort_values(["week", "date", "away_team", "home_team"])

    out_df.to_csv(OUT_CSV, index=False)
    audit_df.to_csv(AUDIT_CSV, index=False)

    print(f"Wrote {OUT_CSV}: {len(out_df):,} games with any CFBD line")
    print(f"Wrote {AUDIT_CSV}: {len(audit_df):,} games audited")

    print("\nCoverage:")
    print("games with spread:", int(out_df["market_spread_home"].notna().sum()))
    print("games with total:", int(out_df["market_total"].notna().sum()))

    print("\nSelected spread books:")
    print(out_df["market_spread_book"].replace("", pd.NA).dropna().value_counts())

    print("\nSelected total books:")
    print(out_df["market_total_book"].replace("", pd.NA).dropna().value_counts())

    show = [
        "week", "date", "away_team", "home_team",
        "market_spread_text", "market_spread_home", "market_spread_book",
        "market_total", "market_total_book", "books_available",
    ]
    print("\nSample:")
    print(out_df[show].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
