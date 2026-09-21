from pathlib import Path
import tempfile
import unittest

from scripts.audit.audit_canonical_v2_index import validate


class CanonicalV2IndexTests(unittest.TestCase):
    def test_public_matchup_payload_satisfies_index_contract(self):
        required_markers = [
            'data-war-room-home-release=',
            'WAR<span>ROOM</span>',
            '<header class="war-room-global">',
            '<nav class="nav war-room-nav">',
            'Data Healthy',
            'This Week’s Top Games',
            'Viewer’s Guide',
            'data/site/current_market_contract.json',
            'data/site/matchups_public_view.json',
            'openers.html?game_id=',
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text("\n".join(required_markers))
            self.assertEqual(validate(path), [])

    def test_internal_matchup_payload_does_not_satisfy_public_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text('data/site/matchups_view.json')
            errors = validate(path)
            self.assertIn(
                'missing public matchup payload: data/site/matchups_public_view.json',
                errors,
            )


if __name__ == "__main__":
    unittest.main()
