import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "public_site_builder",
    ROOT / "scripts/site/build_public_site.py",
)
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class PublicWarRoomMatrixTests(unittest.TestCase):
    def fixture(self):
        return {
            "schema_version": "war-room-market-matrix-v1",
            "built_at": "2026-09-14T22:30:09Z",
            "season": 2026,
            "summary": {"games": 1},
            "audit": {"current_market_fallbacks": [{"reason": "internal"}]},
            "games": [{
                "game_id": "g186",
                "away_team": "Ohio",
                "home_team": "Rutgers",
                "week": 3,
                "authority": {"spread": {"value": 7.5}},
                "models": {"standard_spread": {"value": 7.5}},
                "market": {"best_sportsbook": {"spread": {"away": {"line": 7.5}}}},
                "standard_freshness": {"spread": {"sources": {"SP+": {"status": "FRESH"}}}},
                "operator_model": {
                    "mode": "AUTO",
                    "manual": {"spread": None},
                    "auto_authority": {"spread": {"value": 7.5}},
                },
                "shadow_readiness": {"spread": {"status": "READY"}},
                "injury_rank": {"away": {"rank": 10}},
                "betting_signals": {"away": {"signals": []}},
            }],
        }

    def test_compaction_is_public_only_and_preserves_ui_contract(self):
        runtime = self.fixture()
        original = copy.deepcopy(runtime)
        public = BUILDER.compact_public_war_room_matrix(copy.deepcopy(runtime))

        self.assertEqual(runtime, original)
        self.assertNotIn("audit", public)
        self.assertNotIn("auto_authority", public["games"][0]["operator_model"])
        for field in (
            "authority", "models", "market", "standard_freshness",
            "shadow_readiness", "injury_rank", "betting_signals",
        ):
            self.assertEqual(public["games"][0][field], original["games"][0][field])
        self.assertEqual(public["games"][0]["operator_model"]["mode"], "AUTO")
        self.assertEqual(
            public["games"][0]["operator_model"]["manual"],
            original["games"][0]["operator_model"]["manual"],
        )

    def test_internal_only_growth_does_not_consume_public_size_budget(self):
        runtime = self.fixture()
        runtime["audit"]["current_market_fallbacks"] = ["x" * 1024] * 20000
        runtime["games"][0]["operator_model"]["auto_authority"] = {
            "diagnostic": "y" * (2 * 1024 * 1024)
        }
        public = BUILDER.compact_public_war_room_matrix(copy.deepcopy(runtime))
        encoded = (json.dumps(public, separators=(",", ":"), ensure_ascii=False) + "\n").encode()

        self.assertLessEqual(len(encoded), BUILDER.PUBLIC_WAR_ROOM_TARGET_BYTES)


if __name__ == "__main__":
    unittest.main()
