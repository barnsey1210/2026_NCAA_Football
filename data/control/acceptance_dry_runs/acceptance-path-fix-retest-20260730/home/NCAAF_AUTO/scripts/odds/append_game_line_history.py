#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

OUT = Path("data/odds/game_line_history.csv")

SOURCE_FILES = [
    ("The Odds API", Path("data/odds/theodds_season_game_lines_2026.csv")),
    ("Action Network", Path("data/odds/actionnetwork_season_game_lines_2026.csv")),
    ("CFBD Lines", Path("data/odds/season_game_lines_2026.csv")),
]

KEEP_COLS = [
    "snapshot_date", "snapshot_ts", "source", "source_file",
    "game_id", "date", "week", "away_team", "home_team", "away_norm", "home_norm",
    "books_available", "books_count", "market_line_source", "market_price_status",
    "market_spread_home", "market_spread_text", "market_spread_price", "market_spread_book",
    "market_spread_last_update",
    "market_total", "market_total_book", "market_total_over_price", "market_total_under_price",
    "market_total_last_update",
]

def main():
    now = datetime.now(timezone.utc)
    snapshot_date = now.date().isoformat()
    snapshot_ts = now.isoformat(timespec="seconds")

    rows = []
    for source, path in SOURCE_FILES:
        if not path.exists() or path.stat().st_size == 0:
            continue

        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"WARNING: could not read {path}: {e}")
            continue

        if df.empty:
            continue

        df = df.copy()
        df["snapshot_date"] = snapshot_date
        df["snapshot_ts"] = snapshot_ts
        df["source"] = df.get("source", source)
        df["source_file"] = str(path)

        for c in KEEP_COLS:
            if c not in df.columns:
                df[c] = ""

        rows.append(df[KEEP_COLS])

    if not rows:
        print("No game line rows to append.")
        return

    new = pd.concat(rows, ignore_index=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists() and OUT.stat().st_size > 0:
        old = pd.read_csv(OUT)
        for c in KEEP_COLS:
            if c not in old.columns:
                old[c] = ""

        # Append only new/changed game-source states. Snapshot ingestion time is
        # deliberately not part of market identity, making identical replay
        # idempotent while retaining line, price, book, availability/source and
        # provider timestamp changes.
        def effective_snapshot(df):
            ts = df.get("snapshot_ts", "").astype(str).str.strip()
            dt = df.get("snapshot_date", "").astype(str).str.strip()
            ts = ts.where(~ts.str.lower().isin(["", "nan", "none", "nat"]), dt)
            return pd.to_datetime(ts, errors="coerce", utc=True, format="mixed")

        key_cols = ["source_file", "game_id", "date", "away_team", "home_team"]
        state_cols = [
            "source", "books_available", "books_count", "market_line_source", "market_price_status",
            "market_spread_home", "market_spread_text", "market_spread_price", "market_spread_book",
            "market_spread_last_update", "market_total", "market_total_book",
            "market_total_over_price", "market_total_under_price", "market_total_last_update",
        ]
        def normalized(row, cols):
            values=[]
            for col in cols:
                value=row.get(col, "")
                if pd.isna(value): value=""
                # Normalize numeric CSV round-trips without hiding book/source changes.
                try: value=f"{float(value):.10g}"
                except (TypeError, ValueError): value=str(value).strip()
                values.append(value)
            return tuple(values)
        parsed=effective_snapshot(old)
        ordered=old.assign(_parsed=parsed).sort_values("_parsed",na_position="first")
        latest={normalized(row,key_cols):normalized(row,state_cols) for _,row in ordered.iterrows()}
        additions=[]
        for _,row in new.iterrows():
            key=normalized(row,key_cols);state=normalized(row,state_cols)
            if latest.get(key)==state: continue
            additions.append(row[KEEP_COLS]);latest[key]=state
        if not additions:
            print("Current accepted game-line state is identical by game/source. Skipping append.")
            return
        appended=pd.DataFrame(additions,columns=KEEP_COLS)
        out = pd.concat([old[KEEP_COLS], appended], ignore_index=True)
    else:
        out = new

    # Avoid exact duplicate rows within the same timestamp.
    dedupe_cols = [
        "snapshot_ts", "source_file", "game_id", "date", "away_team", "home_team",
        "market_spread_home", "market_spread_price", "market_spread_book",
        "market_total", "market_total_over_price", "market_total_under_price", "market_total_book",
    ]
    out = out.drop_duplicates(subset=[c for c in dedupe_cols if c in out.columns], keep="last")

    out.to_csv(OUT, index=False)
    appended_count = len(out) - (len(old) if 'old' in locals() else 0)
    print(f"Appended {appended_count} changed game/source rows to {OUT}; total rows now {len(out)}")
    print(f"snapshot_ts={snapshot_ts}")

if __name__ == "__main__":
    main()
