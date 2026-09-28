import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SportHierarchyTests(unittest.TestCase):
    def test_root_and_ncaaf_pages_link_to_ncaab(self):
        root = (ROOT / "index.html").read_text()
        self.assertIn('class="war-room-sports"', root)
        self.assertIn('href="ncaaf/">NCAAF</a>', root)
        self.assertIn('href="ncaab/">NCAAB</a>', root)
        self.assertIn('@media(max-width:700px)', root)
        for name in ("ratings.html", "war-room.html", "schedule.html"):
            self.assertIn('href="ncaab/">NCAAB</a>', (ROOT / name).read_text())

    def test_ncaab_pages_link_back_and_controls_are_read_only(self):
        landing = (ROOT / "ncaab/index.html").read_text()
        command = (ROOT / "ncaab/command-center/index.html").read_text()
        ratings = (ROOT / "ncaab/ratings/index.html").read_text()
        self.assertIn('href="../"', landing)
        self.assertIn('href="../../"', command)
        self.assertIn('href="../../"', ratings)
        self.assertIn('READ-ONLY', command)
        self.assertIn('refreshMarketBtn" disabled', command)
        self.assertIn('refreshRatingsBtn" disabled', command)
        payload = json.loads((ROOT / "ncaab/data/preview.json").read_text())
        self.assertFalse(payload["operator_controls_enabled"])

    def test_ncaaf_compatibility_entry_preserves_root(self):
        entry = (ROOT / "ncaaf/index.html").read_text()
        self.assertIn('url=../index.html', entry)
        self.assertIn('rel="canonical" href="../index.html"', entry)


if __name__ == "__main__":
    unittest.main()
