import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).parents[1] / "scripts/markets/audit_futures_market_reliability.py"
SPEC = importlib.util.spec_from_file_location("futures_reliability", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def row(date, team, book, price="-110", line="7.5"):
    return {
        "snapshot_date": date,
        "team": team,
        "book": book,
        "win_total": line,
        "over_odds": price,
        "under_odds": price,
    }


class FuturesMarketReliabilityTests(unittest.TestCase):
    def test_material_drop_ignores_small_books_but_catches_large_regression(self):
        self.assertFalse(MODULE.material_drop(0, 2))
        self.assertFalse(MODULE.material_drop(92, 100))
        self.assertTrue(MODULE.material_drop(80, 100))

    def test_normalized_coverage_reports_ambiguous_brand_lines(self):
        rows = [
            row("2026-09-10", "Navy", "BetMGM", line="7.5"),
            row("2026-09-10", "Navy Midshipmen", "BetMGM", line="8.5"),
        ]
        teams, unmatched, invalid, ambiguous = MODULE.normalized_coverage(
            rows, ["Navy"], ("over_odds", "under_odds")
        )
        self.assertEqual(teams, {"Navy": {"BetMGM"}})
        self.assertEqual(unmatched, [])
        self.assertEqual(invalid, [])
        self.assertEqual(
            ambiguous,
            [{"team": "Navy", "book": "BetMGM", "lines": ["7.5", "8.5"]}],
        )

    def test_csv_domain_fails_when_provider_family_disappears(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            current = tmp_path / "current.csv"
            history = tmp_path / "history.csv"
            header = "snapshot_date,team,book,win_total,over_odds,under_odds\n"
            prior = [row("2026-09-09", f"Team {i}", "FanDuel") for i in range(12)]
            now = [row("2026-09-10", f"Team {i}", "DraftKings") for i in range(12)]
            for path, records in ((current, now), (history, prior)):
                path.write_text(header + "".join(
                    f"{r['snapshot_date']},{r['team']},{r['book']},{r['win_total']},{r['over_odds']},{r['under_odds']}\n"
                    for r in records
                ))
            canonical = [f"Team {i}" for i in range(12)]
            result = MODULE.audit_csv_domain(
                "win_totals", current, history, canonical, canonical,
                ("over_odds", "under_odds"), "2026-09-10"
            )
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["provider_wide_disappearances"], ["FanDuel"])

    def test_contract_domain_requires_current_executable_quotes(self):
        contract = {"make_cfp": {"rows": [
            {"team": "A", "outcome": "Yes", "executable_book_count": 2,
             "executable_books": ["FanDuel", "Caesars"]}
        ]}}
        result = MODULE.contract_domain(
            contract, "make_cfp", ["A", "B"], "2026-09-10T12:00:00+00:00",
            MODULE.datetime(2026, 9, 10, 13, tzinfo=MODULE.timezone.utc),
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["missing_teams"], ["B"])

    def test_contract_domain_detects_large_book_regression(self):
        current = {"national_title": {"rows": [
            {"team": f"Team {i}", "outcome": "Yes", "executable_book_count": 1,
             "executable_books": ["FanDuel"]}
            for i in range(12)
        ]}}
        prior = [
            {"team": f"Team {i}", "outcome": "Yes", "executable_book_count": 2,
             "executable_books": ["FanDuel", "DraftKings"]}
            for i in range(12)
        ]
        result = MODULE.contract_domain(
            current, "national_title", [f"Team {i}" for i in range(12)],
            "2026-09-10T12:00:00+00:00",
            MODULE.datetime(2026, 9, 10, 13, tzinfo=MODULE.timezone.utc), prior,
        )
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["provider_wide_disappearances"], ["DraftKings"])


if __name__ == "__main__":
    unittest.main()
