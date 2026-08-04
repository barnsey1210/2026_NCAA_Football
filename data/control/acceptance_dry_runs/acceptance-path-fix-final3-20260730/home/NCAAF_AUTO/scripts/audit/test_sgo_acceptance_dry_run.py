#!/usr/bin/env python3
"""Provider-free unit checks for the SGO accepted-data mirror adapter."""
from __future__ import annotations
import csv, json, hashlib
import tempfile
from pathlib import Path

from scripts.control.sgo_acceptance_dry_run import ROOT, guarded
from scripts.markets.build_sgo_canonical_artifacts import build


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def main():
    with tempfile.TemporaryDirectory() as td:
        mirror=Path(td)
        stage=ROOT/"data/control/staging/replay-20260730T035405Z-85165416-corrected"
        observations=list(csv.DictReader((stage/"quote_observations.csv").open()))
        manifest=json.loads((stage/"manifest.json").read_text())
        games=json.loads((ROOT/"data/site/matchups_view.json").read_text())
        quotes,display,excluded,global_ok=build(observations,manifest,games,"fixture-hash","2026-07-30T00:00:00Z")
        assert not global_ok, "partial cursor coverage must block global acceptance"
        assert quotes and display
        assert all(q["canonical_site_week"]==0 for q in quotes)
        assert all(q["market_eligibility"] and not q["acceptance_eligibility"] for q in quotes)
        assert all(q["available"] and not q["suspended"] and not q["stale_flag"] for q in quotes)
        for pid in {q["paired_market_id"] for q in quotes}:
            pair=[q for q in quotes if q["paired_market_id"]==pid];m=pair[0]["market_type"]
            assert len(pair)==2 and len({q["sportsbook"] for q in pair})==1
            if m=="spread":assert abs(sum(float(q["line"]) for q in pair))<.001
            if m=="total":assert len({float(q["line"]) for q in pair})==1
        assert all(d["selected_sportsbook"] in {"draftkings","bovada"} for d in display)
        assert not any(d["selected_sportsbook"]=="bovada" and any(q["canonical_game_id"]==d["canonical_game_id"] and q["market_type"]==d["market_type"] and q["sportsbook"]=="draftkings" for q in quotes) for d in display),"Bovada selected over DraftKings"
        assert any(q["neutral_site"] for q in quotes),"neutral-site metadata lost"
        try: guarded(Path(td).parent/"escape",mirror)
        except RuntimeError: pass
        else: raise AssertionError("path escape was not blocked")
    print("SGO accepted-data dry-run unit tests: PASSED")
    print("- schema, coverage gate, canonical week, pairing, priority, availability/staleness, neutral site, path guard: tested")
    return 0

if __name__=="__main__": raise SystemExit(main())
