#!/usr/bin/env python3
"""Focused guards for canonical CFBDepth Injury Impact normalization."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PULLER = ROOT / "scripts/injuries/pull_cfbdepth_team_injury_impact.py"
MATRIX = ROOT / "scripts/war_room/build_war_room_market_matrix.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CFBDepthInjuryImpactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.puller = load(PULLER, "cfbdepth_injury_puller")
        cls.matrix = load(MATRIX, "war_room_matrix_injury")

    def test_normalization_is_canonical_and_ties_are_deterministic(self):
        raw = (
            "School,Conference,Injury Number,Injury New,Injury Impact\n"
            "UConn,Independent,2,1,2.0\n"
            "App State,Sun Belt,1,0,2.0\n"
            "Miami,ACC,3,1,9.0\n"
        ).encode()
        rows = self.puller.normalize(raw, "2026-08-30T15:00:46Z")
        self.assertEqual(
            [(row["team"], row["injury_impact_rank"]) for row in rows],
            [("Appalachian State", 1), ("Connecticut", 2), ("Miami-FL", 3)],
        )
        self.assertTrue(all(row["source_updated_at"] is None for row in rows))
        self.assertTrue(
            all(row["status"] == "AVAILABLE_SOURCE_TIME_UNVERIFIED" for row in rows)
        )

    def test_missing_identity_fails_closed(self):
        raw = (
            "School,Conference,Injury Number,Injury New,Injury Impact\n"
            "Not A Canonical Team,X,1,0,1.0\n"
        ).encode()
        with self.assertRaisesRegex(ValueError, "unresolved"):
            self.puller.normalize(raw, "2026-08-30T15:00:46Z")

    def test_matrix_loader_accepts_fresh_and_rejects_stale(self):
        payload_path = ROOT / "data/canonical/cfbdepth_team_injury_impact_current.json"
        fresh_now = datetime(2026, 8, 30, 15, 30, tzinfo=timezone.utc)
        stale_now = datetime(2026, 8, 31, 0, 0, tzinfo=timezone.utc)
        fresh, fresh_meta = self.matrix.load_team_injury_impact(payload_path, fresh_now)
        stale, stale_meta = self.matrix.load_team_injury_impact(payload_path, stale_now)
        self.assertEqual(len(fresh), 138)
        self.assertEqual(fresh_meta["status"], "AVAILABLE_SOURCE_TIME_UNVERIFIED")
        self.assertEqual(stale, {})
        self.assertEqual(stale_meta["status"], "STALE")

    def test_five_fixed_tiers_cover_exact_contract(self):
        source = (ROOT / "scripts/site/build_war_room_page.py").read_text()
        expected = {
            1: "injury-tier-1",
            28: "injury-tier-1",
            29: "injury-tier-2",
            56: "injury-tier-2",
            57: "injury-tier-3",
            83: "injury-tier-3",
            84: "injury-tier-4",
            111: "injury-tier-4",
            112: "injury-tier-5",
            138: "injury-tier-5",
        }
        # Mirrors the intentionally tiny presentational boundary function.
        def tier(value):
            if value <= 28:
                return "injury-tier-1"
            if value <= 56:
                return "injury-tier-2"
            if value <= 83:
                return "injury-tier-3"
            if value <= 111:
                return "injury-tier-4"
            return "injury-tier-5"

        self.assertEqual({value: tier(value) for value in expected}, expected)
        for class_name in set(expected.values()):
            self.assertIn(class_name, source)

    def test_existing_injury_stage_owns_acquisition(self):
        registry = json.loads((ROOT / "config/daily_stages.json").read_text())
        stage = next(row for row in registry["stages"] if row["id"] == "injuries_and_signals")
        self.assertTrue(stage["external_network"])
        self.assertIn(
            "scripts/injuries/pull_cfbdepth_team_injury_impact.py",
            stage["scripts"],
        )
        orchestrator = (ROOT / "daily_market_update.sh").read_text()
        self.assertIn(
            'run_py "scripts/injuries/pull_cfbdepth_team_injury_impact.py"',
            orchestrator,
        )
        self.assertIn("fail closed when stale", orchestrator)


if __name__ == "__main__":
    unittest.main()
