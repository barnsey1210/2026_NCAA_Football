#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

FILES = [
    Path("market_win_totals_import.csv"),
    Path("market_win_totals_history.csv"),
]

OUTDIR = Path("data/audit")
OUTDIR.mkdir(parents=True, exist_ok=True)

BAD_NOTE_BITS = [
    "brand_mode=state",
    "best_over=DK NJ DK",
    "best_under=DK NJ DK",
]

def is_bad_dk_state_rows(df):
    if "book" not in df.columns:
        return pd.Series(False, index=df.index)

    book_mask = df["book"].astype(str).str.strip().eq("DraftKings")

    notes = df["notes"].astype(str) if "notes" in df.columns else pd.Series("", index=df.index)
    source_url = df["source_url"].astype(str) if "source_url" in df.columns else pd.Series("", index=df.index)

    text = (notes + " " + source_url).str.lower()

    bad_note_mask = pd.Series(True, index=df.index)
    for bit in BAD_NOTE_BITS:
        bad_note_mask = bad_note_mask & text.str.contains(bit.lower(), na=False)

    action_win_total_mask = text.str.contains("actionnetwork", na=False) & text.str.contains("regular_season_total_wins", na=False)

    return book_mask & bad_note_mask & action_win_total_mask

def clean_file(path):
    if not path.exists():
        print(f"{path}: missing")
        return

    df = pd.read_csv(path)
    if df.empty:
        print(f"{path}: empty")
        return

    mask = is_bad_dk_state_rows(df)

    if path.name == "market_win_totals_history.csv" and "snapshot_date" in df.columns:
        latest = df["snapshot_date"].max()
        mask = mask & df["snapshot_date"].eq(latest)

    bad = df[mask].copy()
    good = df[~mask].copy()

    if bad.empty:
        print(f"{path}: no bad DraftKings state-mode rows found")
        return

    qpath = OUTDIR / f"quarantined_{path.stem}.csv"
    bad.to_csv(qpath, index=False)
    good.to_csv(path, index=False)

    print(f"{path}: quarantined {len(bad)} rows -> {qpath}")
    if "team" in bad.columns:
        print("  teams:", ", ".join(sorted(bad["team"].dropna().astype(str).unique())[:40]))
        if bad["team"].nunique() > 40:
            print(f"  ... and {bad['team'].nunique() - 40} more")

def main():
    for f in FILES:
        clean_file(f)

if __name__ == "__main__":
    main()
