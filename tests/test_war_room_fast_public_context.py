import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAST = load_module(
    "scripts/war_room/run_fast_market_publication.py",
    "war_room_fast_publication",
)
AUDIT = load_module(
    "scripts/audit/audit_war_room_fast_publication.py",
    "war_room_fast_publication_audit",
)


class WarRoomFastPublicContextTests(unittest.TestCase):
    def test_fast_bundle_rewrites_internal_matchup_context_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            runtime = tmp / "runtime"
            main = tmp / "main"
            bundle = runtime / "build/war_room_public"
            (runtime / "data/site").mkdir(parents=True)
            main.mkdir()
            (main / "war-room.html").write_text(
                "const MATCHUPS_CONTEXT_URL = 'data/site/matchups_view.json';"
            )
            for name in (
                "war_room_health.json",
                "war_room_market_matrix.json",
                "war_room_activity.json",
            ):
                (runtime / "data/site" / name).write_text(json.dumps({"name": name}))

            with patch.object(FAST, "ROOT", runtime), patch.object(
                FAST, "MAIN_REPO", main
            ), patch.object(FAST, "BUNDLE", bundle):
                FAST.build_bundle()

            page = (bundle / "war-room.html").read_text()
            self.assertIn("data/site/matchups_public_view.json", page)
            self.assertNotIn("data/site/matchups_view.json", page)

    def test_fast_validator_requires_public_context_and_rejects_internal_url(self):
        source = (ROOT / "scripts/audit/audit_war_room_fast_publication.py").read_text()
        self.assertIn('"data/site/matchups_public_view.json" not in text', source)
        self.assertIn('"data/site/matchups_view.json" in text', source)


if __name__ == "__main__":
    unittest.main()
