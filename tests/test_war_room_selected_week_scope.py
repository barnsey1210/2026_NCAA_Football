#!/usr/bin/env python3
"""Focused guards for Command Center selected-week view scoping."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/site/build_war_room_page.py"


class WarRoomSelectedWeekScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = BUILDER.read_text(encoding="utf-8")

    def test_market_and_book_health_use_current_rows(self):
        self.assertIn("const rows = currentRows();", self.source)
        self.assertIn("selectedBookCoverage(book,rows)", self.source)
        self.assertIn("${coverage.games}/${coverage.required}", self.source)
        self.assertNotIn("${games}g${age", self.source)

    def test_connectivity_remains_global_but_coverage_is_scoped(self):
        self.assertIn("${healthDot(h.color)}", self.source)
        self.assertIn("Global acquisition coverage:", self.source)
        self.assertIn("Selected scope coverage:", self.source)

    def test_model_health_has_exact_canonical_rows(self):
        spread = re.search(
            r"const spreadSources = \[(.*?)\]\.join\(''\);",
            self.source,
            re.S,
        )
        total = re.search(
            r"const totalSources = \[(.*?)\]\.join\(''\);",
            self.source,
            re.S,
        )
        self.assertIsNotNone(spread)
        self.assertIsNotNone(total)
        self.assertEqual(spread.group(1).count("sourceItem("), 5)
        self.assertEqual(total.group(1).count("sourceItem("), 3)
        for label in (
            "'SP+'",
            "'FPI'",
            "'TeamRankings'",
            "'Sagarin Rating'",
            "'DRatings'",
        ):
            self.assertIn(label, spread.group(1))
        for label in ("'SP+ Total'", "'Massey Dual'", "'Sagarin Total'"):
            self.assertIn(label, total.group(1))

    def test_default_health_omits_raw_universe_counts(self):
        self.assertNotIn("function ratingStatusDetail", self.source)
        self.assertNotIn("${h.teams}t", self.source)
        self.assertNotIn("${h.games_available}g", self.source)

    def test_tooltips_include_selected_week_diagnostics(self):
        for marker in (
            "Freshness:",
            "Availability:",
            "Missing:",
            "Source is not complete for the selected week.",
        ):
            self.assertIn(marker, self.source)

    def test_week_change_is_view_only(self):
        handler = re.search(
            r"weekSelect'\)\.addEventListener\((.*?)\n\);",
            self.source,
            re.S,
        )
        self.assertIsNotNone(handler)
        body = handler.group(1)
        self.assertIn("renderHealth();", body)
        self.assertIn("renderMatrix();", body)
        self.assertNotIn("fetch(", body)
        self.assertNotIn("dispatch", body.lower())

    def test_global_quota_and_manual_controls_remain(self):
        self.assertIn("HEALTH?.api_quota", self.source)
        for control in ("refreshBtn", "acquireBtn", "ratingsBtn", "postgameBtn"):
            self.assertIn(control, self.source)
        self.assertIn("LIVE_VERSION_URL", self.source)


if __name__ == "__main__":
    unittest.main()
