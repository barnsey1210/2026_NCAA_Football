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

    def test_mobile_health_notes_and_game_footer_stack_without_overlap(self):
        mobile = self.source.rsplit("@media(max-width:900px){", 1)[1].split(
            "@media(min-width:901px){", 1
        )[0]

        self.assertIn("grid-template-columns:minmax(0,1fr) auto !important", mobile)
        self.assertIn("grid-column:1 / -1", mobile)
        self.assertIn("grid-template-columns:94px minmax(0,1fr)", mobile)
        self.assertIn(".mobile-game-foot{", mobile)
        self.assertIn("grid-template-columns:minmax(0,1fr)", mobile)
        self.assertIn(".mobile-foot-injury + .mobile-foot-injury", mobile)

    def test_mobile_command_center_uses_condensed_sortable_edge_table(self):
        source = self.source
        self.assertIn('class="mobile-command-table"', source)
        self.assertIn("SPREAD EDGE ${sortArrow('spread_edge')", source)
        self.assertIn("TOTAL EDGE ${sortArrow('total_edge')", source)
        self.assertIn("grid-template-columns:minmax(0,1.48fr) 50px", source)
        self.assertIn("position:sticky", source)
        self.assertIn('<span>GAME</span>', source)
        self.assertIn(">EDGE ${sortArrow('best_edge')", source)
        self.assertIn("mobile-command-detail mobile-activity-slot", source)
        self.assertIn("mobileMatchupWithMarket(game,live,totSide)", source)
        self.assertIn("mobileCurrentSpread(game,'away')", source)
        self.assertIn("mobileCurrentSpread(game,'home')", source)
        self.assertIn("mobileCurrentTotal(game,totalSide)", source)
        self.assertIn("mobileBookLogo(quote.book)", source)
        self.assertIn("mobileEdgeDisplay(game,'spread'", source)
        self.assertIn("mobileEdgeDisplay(game,'total'", source)
        self.assertIn('data-game-select aria-label=', source)
        self.assertIn('box-shadow:0 0 0 9999px', source)
        self.assertIn("function modelTooltip(game, market, shownOverride=null)", source)

    def test_mobile_authority_tooltips_and_manual_controls_share_live_contract(self):
        source = self.source
        for token in (
            "const authorityWeights = hybridActive",
            "manual?.weights_used?.[name]",
            "weightText=`${(authorityWeight*100).toFixed(1)}% · ACTIVE`",
            "document.getElementById('modelManualBtn').addEventListener",
            "document.getElementById('manualSourcePanel').hidden=false",
            "submitModelOverride('MANUAL'",
        ):
            self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
