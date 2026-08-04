#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import re

ROOT = Path(".")
INTRADAY_HISTORY = ROOT / "data/market/win_totals_intraday_history.csv"
INTRADAY_MOVES = ROOT / "data/market/win_totals_intraday_moves.csv"
DAILY_MOVES = ROOT / "daily_market_movement_report.csv"

SOURCE_CANDIDATES = [
    ROOT / "market_win_totals_raw.csv",
    ROOT / "data/market/market_win_totals_raw.csv",
    ROOT / "data/odds/market_win_totals_raw.csv",
    ROOT / "market_win_totals_history.csv",
    ROOT / "data/market/market_win_totals_history.csv",
]

TEAM_ALIASES = {
    "san jose st": "San Jose State",
    "san jose st.": "San Jose State",
    "san jose state": "San Jose State",
    "san jose state spartans": "San Jose State",
    "air force": "Air Force",
    "air force falcons": "Air Force",
}

BOOK_ALIASES = {
    "dk": "DraftKings",
    "dk oh": "DraftKings",
    "draftkings": "DraftKings",
    "fanduel": "FanDuel",
    "betmgm": "BetMGM",
    "betmgm oh": "BetMGM",
    "caesars": "Caesars",
}

def norm_text(x):
    return re.sub(r"\s+", " ", str(x or "").strip())

def canon_team(x):
    s = norm_text(x)
    key = s.lower().replace("  ", " ")
    return TEAM_ALIASES.get(key, s)

def canon_book(x):
    s = norm_text(x)
    key = s.lower()
    return BOOK_ALIASES.get(key, s)

def fmt_odds(x):
    try:
        n = int(round(float(x)))
        return f"+{n}" if n > 0 else str(n)
    except Exception:
        return str(x)

def read_current():
    for p in SOURCE_CANDIDATES:
        if not p.exists() or p.stat().st_size == 0:
            continue
        try:
            df = pd.read_csv(p)
        except Exception:
            continue

        if not {"team", "book", "win_total"}.issubset(df.columns):
            continue

        # If this is a history file, use latest snapshot_date.
        if "snapshot_date" in df.columns:
            latest_date = df["snapshot_date"].astype(str).max()
            df = df[df["snapshot_date"].astype(str) == latest_date].copy()

        for c in ["over_odds", "under_odds"]:
            if c not in df.columns:
                df[c] = ""

        out = df[["team", "book", "win_total", "over_odds", "under_odds"]].copy()
        out["team"] = out["team"].map(canon_team)
        out["book"] = out["book"].map(canon_book)

        for c in ["win_total", "over_odds", "under_odds"]:
            out[c] = pd.to_numeric(out[c], errors="coerce")

        out = out.dropna(subset=["team", "book", "win_total"])
        out = out.drop_duplicates(["team", "book"], keep="last")
        if not out.empty:
            return out, str(p)

    raise SystemExit("No usable win-total current source found")

def load_intraday_history():
    if not INTRADAY_HISTORY.exists() or INTRADAY_HISTORY.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(INTRADAY_HISTORY)

def append_to_daily(moves):
    if moves.empty:
        return

    daily_cols = [
        "market", "snapshot_prev", "snapshot_latest", "move_date", "season",
        "conference", "team", "book", "field", "previous", "latest", "change",
        "implied_prob_change_pct", "summary"
    ]

    add = moves.copy()
    add["market"] = "Win Total"
    add["move_date"] = add["snapshot_latest"].astype(str).str.slice(0, 10)
    add["season"] = 2026
    add["conference"] = ""
    add["implied_prob_change_pct"] = ""

    rows = []

    for _, r in add.iterrows():
        team = r["team"]
        book = r["book"]
        prev_ts = r["snapshot_prev"]
        latest_ts = r["snapshot_latest"]

        if pd.notna(r.get("previous_win_total")) and pd.notna(r.get("latest_win_total")) and float(r["previous_win_total"]) != float(r["latest_win_total"]):
            rows.append({
                "market": "Win Total",
                "snapshot_prev": prev_ts,
                "snapshot_latest": latest_ts,
                "move_date": str(latest_ts)[:10],
                "season": 2026,
                "conference": "",
                "team": team,
                "book": book,
                "field": "Win Total",
                "previous": r["previous_win_total"],
                "latest": r["latest_win_total"],
                "change": float(r["latest_win_total"]) - float(r["previous_win_total"]),
                "implied_prob_change_pct": "",
                "summary": f"{team} {book} intraday win total moved {r['previous_win_total']} → {r['latest_win_total']}",
            })

        if pd.notna(r.get("previous_over_odds")) and pd.notna(r.get("latest_over_odds")) and float(r["previous_over_odds"]) != float(r["latest_over_odds"]):
            rows.append({
                "market": "Win Total",
                "snapshot_prev": prev_ts,
                "snapshot_latest": latest_ts,
                "move_date": str(latest_ts)[:10],
                "season": 2026,
                "conference": "",
                "team": team,
                "book": book,
                "field": f"Over {r['latest_win_total']} wins",
                "previous": r["previous_over_odds"],
                "latest": r["latest_over_odds"],
                "change": float(r["latest_over_odds"]) - float(r["previous_over_odds"]),
                "implied_prob_change_pct": "",
                "summary": f"{team} {book} intraday Over {r['latest_win_total']} moved {fmt_odds(r['previous_over_odds'])} → {fmt_odds(r['latest_over_odds'])}",
            })

        if pd.notna(r.get("previous_under_odds")) and pd.notna(r.get("latest_under_odds")) and float(r["previous_under_odds"]) != float(r["latest_under_odds"]):
            rows.append({
                "market": "Win Total",
                "snapshot_prev": prev_ts,
                "snapshot_latest": latest_ts,
                "move_date": str(latest_ts)[:10],
                "season": 2026,
                "conference": "",
                "team": team,
                "book": book,
                "field": f"Under {r['latest_win_total']} wins",
                "previous": r["previous_under_odds"],
                "latest": r["latest_under_odds"],
                "change": float(r["latest_under_odds"]) - float(r["previous_under_odds"]),
                "implied_prob_change_pct": "",
                "summary": f"{team} {book} intraday Under {r['latest_win_total']} moved {fmt_odds(r['previous_under_odds'])} → {fmt_odds(r['latest_under_odds'])}",
            })

    if not rows:
        return

    new_daily = pd.DataFrame(rows, columns=daily_cols)

    if DAILY_MOVES.exists() and DAILY_MOVES.stat().st_size > 0:
        old = pd.read_csv(DAILY_MOVES)
        for c in daily_cols:
            if c not in old.columns:
                old[c] = ""
        combined = pd.concat([old[daily_cols], new_daily[daily_cols]], ignore_index=True)
        combined = combined.drop_duplicates(
            ["market", "snapshot_prev", "snapshot_latest", "team", "book", "field", "previous", "latest"],
            keep="last"
        )
    else:
        combined = new_daily[daily_cols]

    combined.to_csv(DAILY_MOVES, index=False)

def main():
    now_ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    current, source = read_current()
    current["snapshot_ts"] = now_ts
    current["source_file"] = source

    hist = load_intraday_history()

    moves = []

    if not hist.empty:
        hist["team"] = hist["team"].map(canon_team)
        hist["book"] = hist["book"].map(canon_book)

        hist = hist.sort_values("snapshot_ts")
        prev = hist.drop_duplicates(["team", "book"], keep="last")

        merged = current.merge(
            prev[["team", "book", "snapshot_ts", "win_total", "over_odds", "under_odds"]],
            on=["team", "book"],
            how="left",
            suffixes=("_latest", "_previous")
        )

        for _, r in merged.iterrows():
            if pd.isna(r.get("snapshot_ts_previous")):
                continue

            changed = False
            for latest_col, prev_col in [
                ("win_total_latest", "win_total_previous"),
                ("over_odds_latest", "over_odds_previous"),
                ("under_odds_latest", "under_odds_previous"),
            ]:
                a = r.get(latest_col)
                b = r.get(prev_col)
                if pd.notna(a) and pd.notna(b) and float(a) != float(b):
                    changed = True

            if changed:
                moves.append({
                    "snapshot_prev": r["snapshot_ts_previous"],
                    "snapshot_latest": now_ts,
                    "team": r["team"],
                    "book": r["book"],
                    "previous_win_total": r["win_total_previous"],
                    "latest_win_total": r["win_total_latest"],
                    "previous_over_odds": r["over_odds_previous"],
                    "latest_over_odds": r["over_odds_latest"],
                    "previous_under_odds": r["under_odds_previous"],
                    "latest_under_odds": r["under_odds_latest"],
                    "source_file": source,
                })

    moves_df = pd.DataFrame(moves)
    if not moves_df.empty:
        if INTRADAY_MOVES.exists() and INTRADAY_MOVES.stat().st_size > 0:
            old_moves = pd.read_csv(INTRADAY_MOVES)
            moves_df = pd.concat([old_moves, moves_df], ignore_index=True)
            moves_df = moves_df.drop_duplicates(
                ["snapshot_prev", "snapshot_latest", "team", "book"],
                keep="last"
            )
        moves_df.to_csv(INTRADAY_MOVES, index=False)
        append_to_daily(moves_df)

    if INTRADAY_HISTORY.exists() and INTRADAY_HISTORY.stat().st_size > 0:
        old_hist = pd.read_csv(INTRADAY_HISTORY)
        hist_out = pd.concat([old_hist, current], ignore_index=True)
    else:
        hist_out = current

    hist_out = hist_out.drop_duplicates(
        ["snapshot_ts", "team", "book"],
        keep="last"
    )
    hist_out.to_csv(INTRADAY_HISTORY, index=False)

    print(f"intraday current rows: {len(current)} from {source}")
    print(f"intraday moves detected: {len(moves_df) if not moves_df.empty else 0}")
    print(f"wrote: {INTRADAY_HISTORY}")
    print(f"wrote: {INTRADAY_MOVES}")

if __name__ == "__main__":
    main()
