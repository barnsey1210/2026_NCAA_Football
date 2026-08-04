#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

IMPORT_PATH = Path("market_win_totals_import.csv")
DK_PATH = Path("data/odds/actionnetwork_visible_dk_win_totals.csv")
AUDIT_DIR = Path("data/audit")
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

if not IMPORT_PATH.exists():
    raise SystemExit(f"Missing {IMPORT_PATH}")

if not DK_PATH.exists():
    raise SystemExit(f"Missing {DK_PATH}")

imp = pd.read_csv(IMPORT_PATH)
dk = pd.read_csv(DK_PATH)

if dk.empty:
    raise SystemExit("Visible DK file is empty")

non_dk = imp[imp["book"].astype(str).str.lower() != "draftkings"].copy()

snapshot_date = ""
if "snapshot_date" in non_dk.columns and non_dk["snapshot_date"].notna().any():
    snapshot_date = str(non_dk["snapshot_date"].dropna().astype(str).max())
else:
    snapshot_date = datetime.now(timezone.utc).date().isoformat()

dk["snapshot_date"] = snapshot_date
dk["season"] = 2026
dk["book"] = "DraftKings"

needed_cols = list(imp.columns)
for col in needed_cols:
    if col not in dk.columns:
        dk[col] = ""

dk = dk[needed_cols]

merged = pd.concat([non_dk, dk], ignore_index=True)

backup = AUDIT_DIR / f"market_win_totals_import_before_visible_dk_merge_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
imp.to_csv(backup, index=False)
merged.to_csv(IMPORT_PATH, index=False)

bad = merged[
    (merged["book"].astype(str).str.lower() == "draftkings") &
    (merged["notes"].astype(str).str.contains("brand_mode=state|DK NJ DK|best_over", case=False, na=False))
]

print("backup:", backup)
print("snapshot_date used for DK:", snapshot_date)
print("non-DK rows:", len(non_dk))
print("visible DK rows:", len(dk))
print("merged rows:", len(merged))
print("bad DK rows remaining:", len(bad))

teams = ["Alabama", "LSU", "Georgia", "UTEP", "New Mexico", "Wake Forest"]
print(merged[(merged["book"] == "DraftKings") & (merged["team"].isin(teams))].to_string(index=False))
