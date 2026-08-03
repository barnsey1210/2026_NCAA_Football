import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.model_tracking.model_tracking import (
    append_jsonl, available_average, settle_spread, settle_total,
    spread_core, spread_point_clv, total_consensus, total_point_clv, is_trackable_game,
)

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get("NCAAF_RUNTIME_ROOT", ROOT))


class ModelTrackingTests(unittest.TestCase):
    def test_protected_hashes_and_counts(self):
        activity_path = RUNTIME / "data/site/betting_activity_view.json"
        if not activity_path.exists():
            self.skipTest("runtime betting activity is not present in the source worktree")
        activity = json.loads(activity_path.read_text())
        records = activity["records"]
        owned_open = [r for r in records if r.get("is_open") and r.get("actor", {}).get("type") == "owned_wager"]
        self.assertEqual(activity["summary"]["records"], len(records))
        self.assertEqual(activity["summary"]["owned_open"], len(owned_open))
        self.assertAlmostEqual(activity["summary"]["open_exposure"], sum(float(r.get("stake") or 0) for r in owned_open))
        self.assertEqual(activity["summary"]["game_linked"], sum(bool(r.get("game_id")) for r in records))

    def test_my_bets_default_preview(self):
        page = (ROOT/"betting_v2.html").read_text()
        self.assertIn('class="active" data-view="bets">My Bets', page)
        self.assertIn('<div id="myBetsView"', page)
        self.assertIn('id="modelPerformanceView" class="modelView" hidden', page)

    def test_core_requires_four_and_powers_weight(self):
        vals = {"SP+": 4, "FPI": 8, "TeamRankings": 12, "Brad Powers": 16}
        core = spread_core(vals)
        self.assertTrue(core["eligible"]); self.assertEqual(core["value"], 10)
        self.assertEqual(core["weights"]["Brad Powers"], .25)
        vals["FPI"] = None
        self.assertFalse(spread_core(vals)["eligible"])
        self.assertEqual(spread_core(vals)["missing"], ["FPI"])

    def test_variable_membership_and_shadow_separate(self):
        avg = available_average({"SP+": 2, "FPI": None, "Shadow Spread": 99}, ["SP+", "FPI", "Shadow Spread"])
        self.assertEqual(avg["models"], ["SP+"]); self.assertEqual(avg["value"], 2)

    def test_total_consensus_gate(self):
        one = total_consensus({"Production Total": 52}, ["Production Total"], 3)
        self.assertEqual(one["status"], "INDIVIDUAL_MODEL_ONLY"); self.assertFalse(one["eligible"]); self.assertIsNone(one["value"])
        two = total_consensus({"Production Total": 52, "Massey": 54}, ["Production Total", "Massey"], 3)
        self.assertEqual(two["status"], "PARTIAL_TOTAL_SET")
        three = total_consensus({"Production Total": 52, "Massey": 54, "Sagarin": 56, "Shadow Total": 99}, ["Production Total", "Massey", "Sagarin", "Shadow Total"], 3)
        self.assertTrue(three["eligible"]); self.assertEqual(three["value"], 54); self.assertNotIn("Shadow Total", three["models"])

    def test_clv_signs_and_pushes(self):
        self.assertEqual(total_point_clv("over", 51.5, 54), 2.5)
        self.assertEqual(total_point_clv("under", 51.5, 49), 2.5)
        self.assertEqual(spread_point_clv("home", -7, -6), 1)
        self.assertEqual(spread_point_clv("away", -7, -8), 1)
        self.assertTrue(settle_spread(6, -7, 7)["push"])
        self.assertTrue(settle_total(54, 51.5, 51.5)["push"])

    def test_append_only_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"x.jsonl"
            self.assertTrue(append_jsonl(p, {"id": "a", "value": 1}, ["id"]))
            before = p.read_bytes()
            self.assertFalse(append_jsonl(p, {"id": "a", "value": 2}, ["id"]))
            self.assertEqual(before, p.read_bytes())
            self.assertTrue(append_jsonl(p, {"id": "b", "value": 3}, ["id"]))

    def test_context_fields_and_ranking(self):
        schema = json.loads((ROOT/"data/model_tracking/schema.json").read_text())
        fields = schema["datasets"]["model_opportunities.jsonl"]
        for name in ("site_week", "neutral_site", "fcs_opponent_flag", "kickoff_utc"):
            self.assertIn(name, fields)
        view_path = RUNTIME / "data/site/model_performance_view.json"
        if not view_path.exists():
            self.skipTest("generated model view is not available")
        view = json.loads(view_path.read_text())
        self.assertEqual(view["ranking_minimum"], 30)
        self.assertTrue(all(x["rank"] is None and "UNRANKED" in x["ranking_status"] for x in view["spread_matrix"]+view["total_matrix"]))

    def test_postponed_cancelled_policy(self):
        self.assertFalse(is_trackable_game("postponed"))
        self.assertFalse(is_trackable_game("cancelled"))
        self.assertTrue(is_trackable_game("scheduled"))


if __name__ == "__main__": unittest.main()
