from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "scripts/site/build_war_room_page.py"


class WarRoomCommandCenterUiUpdatesTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text()

    def test_activity_signals_button_is_labeled_coaches(self):
        self.assertIn(
            'data-filter="SIGNALS">COACHES</button>',
            self.source,
        )

    def test_best_tooltip_has_required_books(self):
        for value in (
            "['DraftKings','DK']",
            "['FanDuel','FD']",
            "['BetMGM','MGM']",
            "['Caesars','CZR']",
            "['Pinnacle','PINN']",
        ):
            self.assertIn(value, self.source)

    def test_spread_and_total_best_use_book_tooltip(self):
        self.assertIn(
            "bestBookTooltip(game,'spread',sprSide,sprBest)",
            self.source,
        )
        self.assertIn(
            "bestBookTooltip(game,'total',totSide,totBest)",
            self.source,
        )

    def test_best_tooltip_reuses_viewport_safe_model_tooltip(self):
        block = self.source.split(
            "function bestBookTooltip(game,market,side,bestQuote){", 1
        )[1].split("function compactQuote", 1)[0]

        self.assertIn("model-tooltip-panel", block)
        self.assertIn("positionModelTooltip(this)", block)
        self.assertIn("quoteBundle(game,book)", block)


if __name__ == "__main__":
    unittest.main()
