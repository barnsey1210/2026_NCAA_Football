import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.war_room import build_war_room_market_matrix as matrix
from scripts.war_room.build_war_room_activity import game_openers


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "scripts/site/build_war_room_page.py"


def move(event_id, book, market, old, new, detected, refresh="r3"):
    return {
        "event_id": event_id,
        "event_type": "SPREAD_MOVED" if market == "spread" else "TOTAL_MOVED",
        "game_id": "g1",
        "book": book,
        "market": market,
        "side": "home" if market == "spread" else "over",
        "old_line": old,
        "new_line": new,
        "observed_at": detected,
        "detected_at": detected,
        "refresh_id": refresh,
    }


class WarRoomMatrixPhase2Test(unittest.TestCase):
    def test_opener_authority_is_earliest_and_missing_is_not_manufactured(self):
        history = {"g1": [
            {"snapshot_ts": "2026-08-27T12:30:00Z", "market_spread_home": -4.5,
             "market_spread_book": "FanDuel", "market_spread_price": -110},
            {"snapshot_ts": "2026-08-27T12:00:00Z", "market_spread_home": -3.5,
             "market_spread_book": "DraftKings", "market_spread_price": -105},
        ]}
        first = game_openers(history, "g1")
        later = game_openers({"g1": history["g1"] + [{
            "snapshot_ts": "2026-08-27T13:00:00Z", "market_spread_home": -6,
            "market_spread_book": "Caesars", "market_spread_price": -110,
        }]}, "g1")
        self.assertEqual(first["spread"], later["spread"])
        self.assertEqual((first["spread"]["line"], first["spread"]["book"]), (-3.5, "DraftKings"))
        self.assertIsNone(first["total"])

    def test_material_move_threshold_and_latest_selection(self):
        events = [
            move("small", "DraftKings", "spread", -4.5, -4.75, "2026-08-27T12:00:00Z"),
            move("older", "DraftKings", "spread", -4.5, -5, "2026-08-27T12:05:00Z"),
            move("latest", "DraftKings", "spread", -5, -4.5, "2026-08-27T12:10:00Z"),
            move("total", "FanDuel", "total", 56.5, 57, "2026-08-27T12:11:00Z"),
        ]
        indexed = matrix.material_move_index(events)
        spread = indexed[("g1", "DraftKings", "spread")]
        self.assertEqual(spread["event_id"], "latest")
        self.assertEqual(spread["direction"], "DOWN")
        self.assertEqual(spread["previous_qualifying_moves"], 1)
        self.assertEqual(indexed[("g1", "FanDuel", "total")]["direction"], "UP")

    def test_best_book_identity_and_displayed_side_transform(self):
        indexed = matrix.material_move_index([
            move("dk", "DraftKings", "spread", -4.5, -5, "2026-08-27T12:00:00Z"),
        ])
        fd = {"book": "FanDuel", "line": -4.5, "side": "home"}
        self.assertIsNone(matrix.move_for_displayed_quote(indexed, "g1", fd, "spread", "home"))
        dk_away = {"book": "DraftKings", "line": 5, "side": "away"}
        shown = matrix.move_for_displayed_quote(indexed, "g1", dk_away, "spread", "away")
        self.assertEqual((shown["old_line"], shown["new_line"], shown["direction"]), (4.5, 5, "UP"))

    def test_direction_semantics_include_identity_flip(self):
        self.assertEqual(matrix.spread_move_direction(-4.5, -5), "UP")
        self.assertEqual(matrix.spread_move_direction(5, 4.5), "DOWN")
        self.assertEqual(matrix.spread_move_direction(-0.5, 0.5), "NEUTRAL")
        self.assertEqual(matrix.total_move_direction(56.5, 57), "UP")
        self.assertEqual(matrix.total_move_direction(57, 56.5), "DOWN")

    def test_opener_activation_provenance(self):
        rows = matrix.opener_payload({
            "spread": {"observed_at": "2026-08-27T12:00:00Z"},
            "total": {"observed_at": "2026-08-27T14:00:00Z"},
        }, "2026-08-27T13:00:00Z")
        self.assertTrue(rows["spread"]["predates_activity_activation"])
        self.assertFalse(rows["total"]["predates_activity_activation"])

    def test_refresh_generations_are_stable_and_bounded(self):
        ids = matrix.load_recent_refresh_ids(Path("/definitely/missing.csv"), "r3")
        self.assertEqual(ids, ["r3"])
        self.assertEqual(matrix.MOVEMENT_RECENCY_MINUTES["older_recent"], 90)

    def test_desktop_matrix_hides_open_and_pinn_columns_and_excludes_exchange_moves(self):
        source = PAGE.read_text()
        head = source.split("function renderHead(){", 1)[1].split(
            "function modelDisplay", 1
        )[0]
        rows = source.split("function renderMatrix(){", 1)[1].split(
            "function renderActivity", 1
        )[0]
        self.assertNotIn("SPREAD</span><br>OPEN", head)
        self.assertNotIn("TOTAL<br>OPEN", head)
        self.assertNotIn('class="open-col spread-group"', rows)
        self.assertNotIn('class="open-col total-group"', rows)
        self.assertNotIn("SPREAD</span><br>PINN", source)
        self.assertNotIn("TOTAL<br>PINN", source)
        self.assertIn("compactQuote(sprBest, 'spread', game)", source)
        self.assertIn("compactQuote(sprEx, 'spread', game)", source)
        self.assertIn("const move=q.last_material_move", source)
        self.assertIn("setInterval(updateMatrixRecencyMarkers, 30000)", source)
        self.assertIn("minutes>90", source)

    def test_fast_refresh_orders_history_activity_and_final_projection(self):
        source = (ROOT / "scripts/war_room/run_fast_market_refresh.py").read_text()
        base = source.index('"war_room_market_matrix"')
        append = source.index('"append_current_market_book_history"')
        line_history = source.index('"build_matchup_line_history"')
        activity = source.index('"war_room_activity"')
        enriched = source.index('"war_room_market_matrix_enriched"')
        self.assertLess(base, append)
        self.assertLess(append, line_history)
        self.assertLess(line_history, activity)
        self.assertLess(activity, enriched)

    def test_matrix_headers_share_one_canonical_typography_contract(self):
        source = PAGE.read_text()
        head = source.split("function renderHead(){", 1)[1].split(
            "function modelDisplay", 1
        )[0]
        self.assertEqual(head.count("<th"), 14)
        self.assertEqual(head.count('<th class="matrix-header-cell'), 12)
        self.assertEqual(source.count('class="matrix-header-cell edge-col'), 2)
        self.assertIn(".matrix-header-cell .spread-label", source)
        self.assertIn(".matrix-header-cell .matchup-sort-button", source)
        self.assertIn("font-size:9px;", source)
        self.assertIn("line-height:1.12;", source)
        self.assertIn(".matrix-header-cell.edge-focus", source)

    def test_open_cell_matches_quote_first_compact_contract(self):
        source = PAGE.read_text()
        block = source.split("function compactOpen(game,market){", 1)[1].split(
            "function updateMatrixRecencyMarkers", 1
        )[0]
        self.assertIn('class="open-quote"', block)
        self.assertIn('class="open-line"', block)
        self.assertIn('class="open-price"', block)
        self.assertIn('class="open-meta"', block)
        self.assertIn("compactOpenerTimeET(opener.observed_at)", block)
        self.assertNotIn("game.home_team", block)
        self.assertNotIn("pinnacle_", block)
        self.assertNotIn("Provenance:", block)
        self.assertIn("Opened ${fmtDateTimeET(opener.observed_at)}", block)

        self.assertIn("grid-template-columns:18px minmax(26px,1fr)", source)
        self.assertIn(".open-cell .market-book-logo{grid-column:1;grid-row:1 / span 2;display:block;width:18px;height:18px", source)
        self.assertIn(".open-line{grid-column:2;grid-row:1;font-size:12px;font-weight:900", source)
        self.assertIn(".open-price{grid-column:2;grid-row:2;font-size:10px;font-weight:800", source)
        self.assertIn(".open-meta{grid-column:1 / span 2;grid-row:3;display:flex;align-items:center;justify-content:center;gap:1px;min-width:0;font-size:8px", source)
        self.assertIn(".recency-marker{display:none;font-size:7.5px", source)


if __name__ == "__main__":
    unittest.main()
