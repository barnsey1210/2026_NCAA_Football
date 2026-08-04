#!/usr/bin/env python3
"""Provider-free unit checks for the SGO accepted-data mirror adapter."""
from __future__ import annotations
import csv
import tempfile
from pathlib import Path

from scripts.control.sgo_acceptance_dry_run import ROOT, apply_changes, guarded, read_csv


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def main():
    with tempfile.TemporaryDirectory() as td:
        mirror=Path(td); work=mirror/"workspace"; stage=mirror/"stage"
        accepted=read_csv(ROOT/"data/odds/season_game_lines_2026.csv")
        staged=read_csv(ROOT/"data/control/staging/replay-20260730T035405Z-85165416-corrected/normalized.csv")
        write(work/"data/odds/season_game_lines_2026.csv",accepted); write(stage/"normalized.csv",staged)
        before=len(accepted); proposed,unchanged=apply_changes(work,stage,mirror)
        after=read_csv(work/"data/odds/season_game_lines_2026.csv")
        assert len(after)==before, "partial response deleted accepted rows"
        assert {p["market"] for p in proposed}=={"spread","total","away_moneyline","home_moneyline"}
        assert sum(p["market"]=="spread" for p in proposed)==5
        assert sum(p["market"]=="total" for p in proposed)==1
        assert sum("moneyline" in p["market"] for p in proposed)==2
        assert all(p["sportsbook"]=="draftkings" for p in proposed), "cross-book acceptance"
        assert all(p["availability"] and not p["stale_status"] for p in proposed)
        assert all(int(r["week"])==0 for r in staged), "non-canonical-week staged row"
        try: guarded(Path(td).parent/"escape",mirror)
        except RuntimeError: pass
        else: raise AssertionError("path escape was not blocked")
    print("SGO accepted-data dry-run unit tests: PASSED")
    print("- mirror path guard, partial retention, canonical week, expected same-book paired changes: tested")
    return 0

if __name__=="__main__": raise SystemExit(main())
