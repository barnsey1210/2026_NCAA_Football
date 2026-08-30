import csv
import json
import tempfile
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
    def test_shadow_readiness_copies_validated_tooltip_metadata(self):
        ready = matrix.shadow_readiness({
            "away_spread_shadow_ready": True, "home_spread_shadow_ready": True,
            "away_total_shadow_ready": True, "home_total_shadow_ready": True,
            "away_predicted_sp_plus_change": 0.02883061665205832,
            "away_predicted_sagarin_change": 1.8304119127513174,
            "home_predicted_sp_plus_change": 0.6189419327747037,
            "home_predicted_sagarin_change": 0.34978730946048686,
            "away_predicted_sp_plus_offense_change": 1.599047473500665,
            "away_predicted_sp_plus_defense_change": 0.7664458435598123,
            "home_predicted_sp_plus_offense_change": 0.9708464420920678,
            "home_predicted_sp_plus_defense_change": -1.1339951829639203,
            "home_component_reason": "pending postgame",
            "spread_missing_reasons": ["home pending postgame"],
        })
        self.assertEqual(ready["spread_status"], "READY")
        self.assertEqual(ready["total_status"], "READY")
        self.assertAlmostEqual(ready["team_contributions"]["away"]["spread"]["net_impact"], 0.9296212647)
        self.assertAlmostEqual(ready["team_contributions"]["away"]["total"]["net_impact"], 1.1827466585)
        self.assertAlmostEqual(ready["team_contributions"]["home"]["spread"]["net_impact"], 0.4843646211)
        self.assertAlmostEqual(ready["team_contributions"]["home"]["total"]["net_impact"], -0.0815743704)
        self.assertEqual(ready["spread_missing_reasons"], ["home pending postgame"])

    def test_projection_favorite_sort_highlight_and_score_slots_are_presentational(self):
        source = PAGE.read_text()
        self.assertIn("const team=n<0?game.home_team:game.away_team;", source)
        self.assertIn("Math.abs(n)<.05) return '';", source)
        self.assertIn("spreadFavoriteLogo(game,value)", source)
        self.assertIn("`${short} ${signedImpact(row.net_impact)} ${market}`", source)
        self.assertNotIn("SP+ ${signedImpact(row.sp_plus_change)}", source)
        self.assertIn("setSort('model_state')", source)
        self.assertIn("normalizedModelState(a.state)", source)
        self.assertIn("firstMarketRecency(first)", source)
        self.assertIn("minutes!==null && minutes<=60?'market-first-new':''", source)
        self.assertIn("flex:0 0 28px;width:28px", source)
        self.assertIn('class="matchup-team-name" title="${esc(team)}"', source)

    def test_canonical_composite_rank_source_and_strict_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ratings.json"
            path.write_text(json.dumps({"teams": [
                {"team": "Florida State", "overall_rank": 4},
                {"team": "New Mexico State", "overall_rank": 138},
                {"team": "Missing", "overall_rank": None},
            ]}))
            ranks = matrix.load_team_composite_ranks(path)
        self.assertEqual(ranks["florida state"], 4)
        self.assertEqual(ranks["new mexico state"], 138)
        self.assertNotIn("missing", ranks)
        self.assertIn('"source": "ratings_view.teams.overall_rank"', (ROOT / "scripts/war_room/build_war_room_market_matrix.py").read_text())

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

    def test_activity_enrichment_updates_only_activity_owned_market_metadata(self):
        payload = {"games": [{
            "game_id": "g1",
            "market": {
                "first_available": {"spread": None, "total": None},
                "best_sportsbook": {
                    "spread": {
                        "home": {"book": "DraftKings", "line": -5, "side": "home"},
                        "away": None,
                    },
                    "total": {"over": None, "under": None},
                },
            },
            "edges": {"spread": 2.5},
        }]}
        state = {"first_market_availability": {
            "g1|spread": {"detected_at": "2026-08-27T12:00:00Z"},
        }}
        enriched = matrix.enrich_activity_metadata(payload, state, [
            move("dk", "DraftKings", "spread", -4.5, -5, "2026-08-27T12:05:00Z"),
        ])
        game = enriched["games"][0]
        self.assertEqual(game["edges"], {"spread": 2.5})
        self.assertEqual(
            game["market"]["first_available"]["spread"]["detected_at"],
            "2026-08-27T12:00:00Z",
        )
        self.assertEqual(
            game["market"]["best_sportsbook"]["spread"]["home"]
            ["last_material_move"]["event_id"],
            "dk",
        )

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
        self.assertIn("compactQuote(sprBest, 'spread', game, true)", source)
        self.assertIn("compactQuote(sprEx, 'spread', game)", source)
        self.assertIn("const move=q.last_material_move", source)
        self.assertIn("setInterval(updateMatrixRecencyMarkers, 30000)", source)
        self.assertIn("minutes>90", source)

    def test_fast_refresh_builds_matrix_once_and_defers_history_maintenance(self):
        source = (ROOT / "scripts/war_room/run_fast_market_refresh.py").read_text()
        self.assertEqual(source.count('"war_room_market_matrix"'), 1)
        self.assertNotIn('"war_room_market_matrix_enriched"', source)
        self.assertNotIn('run_stage(\n            "append_current_market_book_history"', source)
        self.assertNotIn('run_stage(\n            "build_matchup_line_history"', source)
        self.assertIn('"deferred_to_daily_maintenance"', source)
        self.assertIn('"war_room_market_activity_enrichment"', source)
        self.assertIn('"--activity-enrichment-only"', source)
        self.assertLess(
            source.index('"war_room_market_matrix"'),
            source.index('"war_room_activity"'),
        )
        self.assertLess(
            source.index('"war_room_activity"'),
            source.index('"war_room_market_activity_enrichment"'),
        )

    def test_matrix_summary_keeps_display_and_fast_board_universes_separate(self):
        counts = matrix.market_universe_counts(
            [{"game_id": "g1"}, {"game_id": "g2"}],
            {"g1"},
        )
        self.assertEqual(counts["matrix_games"], 2)
        self.assertEqual(counts["fast_market_games_matched"], 1)

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

    def test_mobile_view_reuses_canonical_rows_without_changing_desktop_matrix(self):
        source = PAGE.read_text()
        self.assertIn('id="mobileMatrix"', source)
        self.assertIn("function renderMobileMatrix(rows)", source)
        self.assertIn("renderMobileMatrix(rows);", source)
        self.assertIn(".matrix-scroll{display:none}", source)
        self.assertIn(".mobile-matrix{display:grid", source)
        self.assertIn("MODEL',modelTooltip", source)
        self.assertIn("SHADOW',shadowDisplay", source)
        self.assertIn("BEST',compactQuote", source)
        self.assertIn("EXCH',compactQuote", source)
        self.assertNotIn("mobileOpen", source)

    def test_mobile_activity_remains_available_and_selection_is_shared(self):
        source = PAGE.read_text()
        mobile_css = source[source.index("@media(max-width:900px)"):source.index("</style>")]
        self.assertIn(".right-rail{display:none}", mobile_css)
        self.assertIn(".mobile-activity-slot .right-rail{", mobile_css)
        self.assertIn("function placeActivityRail()", source)
        self.assertIn("slot.appendChild(rail)", source)
        self.assertIn("if(rail && grid && rail.parentElement!==grid) grid.appendChild(rail);", source)
        self.assertEqual(source.count('class="right-rail"'), 1)
        self.assertIn("tr[data-game-id],.mobile-game-card[data-game-id]", source)
        self.assertIn("row.scrollIntoView", source)

    def test_mobile_sticky_context_and_sort_controls_reuse_canonical_state(self):
        source = PAGE.read_text()
        for control_id in ("mobileStickyHealth", "mobileScopeSelect", "mobileWeekSelect", "mobileSortSelect", "mobileControlsToggle"):
            self.assertIn(f'id="{control_id}"', source)
        for value in ("date", "home_team", "spread_edge", "total_edge"):
            self.assertIn(f'value="{value}"', source)
        self.assertIn("SORT_DIR=(SORT_KEY==='date' || SORT_KEY==='home_team')?'asc':'desc'", source)
        self.assertIn("reconcileSelectedGame();", source)
        self.assertIn("API ${esc(q.status || 'UNKNOWN')} · UPDATED", source)
        self.assertNotIn("mobileStickyHealth.innerHTML=`${esc(HEALTH?.fast_market_refresh?.refresh_id", source)

    def test_mobile_defaults_to_spread_edge_without_changing_desktop_default(self):
        source = PAGE.read_text()
        self.assertIn(
            "const INITIAL_MOBILE_VIEW = window.matchMedia('(max-width:900px)').matches;",
            source,
        )
        self.assertIn(
            "let SORT_KEY = INITIAL_MOBILE_VIEW ? 'spread_edge' : 'best_edge';",
            source,
        )
        self.assertIn("let SORT_DIR = 'desc';", source)

    def test_mobile_spread_edge_uses_canonical_team_abbreviations_only(self):
        source = PAGE.read_text()
        self.assertIn('ROOT / "logos/espn_team_lookup.csv"', source)
        self.assertIn('candidates[0]["abbreviation"]', source)
        self.assertIn("function spreadDecision(game, side, edge, useShortName=false)", source)
        self.assertIn("TEAM_ABBREVIATIONS[team] || team", source)
        self.assertIn("spreadDecision(game,sprSide,sprEdge,true)", source)
        self.assertIn("spreadDecision(game, sprSide, sprEdge)", source)

        with (ROOT / "logos/espn_team_lookup.csv").open(newline="", encoding="utf-8") as handle:
            lookup = list(csv.DictReader(handle))
        for team, abbreviation in {
            "North Carolina": "UNC",
            "Florida State": "FSU",
            "New Mexico State": "NMSU",
            "Eastern Michigan": "EMU",
        }.items():
            self.assertTrue(any(
                row["displayName"].startswith(f"{team} ")
                and row["abbreviation"] == abbreviation
                for row in lookup
            ))

    def test_composite_rank_renders_in_desktop_and_mobile_matchups(self):
        source = PAGE.read_text()
        self.assertIn("function compositeRankClass(rank)", source)
        for boundary, tier in ((28, 1), (56, 2), (83, 3), (111, 4), (138, 5)):
            self.assertIn(f"if(value<={boundary}) return 'rank-tier-{tier}';", source)
            self.assertIn(f".team-composite-rank.rank-tier-{tier}", source)
        self.assertIn("const valid=Number.isInteger(value) && value>=1 && value<=138;", source)
        self.assertIn("if(!Number.isInteger(value) || value<1) return '';", source)
        self.assertIn("if(value<=138) return 'rank-tier-5';\n  return '';", source)
        self.assertIn('class="team-composite-rank ${compositeRankClass(rank)}"', source)
        self.assertIn("${valid?esc(value):'—'}", source)
        self.assertIn("matchupTeam(game.away_team,game.team_composite_rank?.away,live.awayScore)", source)
        self.assertIn("matchupTeam(game.home_team,game.team_composite_rank?.home,live.homeScore)", source)
        self.assertIn("flex:0 0 22px;min-width:22px", source)
        self.assertIn("font-size:9.5px;font-weight:950", source)
        home_sort = source.split("function currentRows(){", 1)[1].split("function sortArrow", 1)[0]
        self.assertIn("av = String(a.home_team || '');", home_sort)
        self.assertIn("bv = String(b.home_team || '');", home_sort)
        self.assertNotIn("team_composite_rank", home_sort)

    def test_composite_rank_five_band_boundaries(self):
        def tier(rank):
            if not isinstance(rank, int) or rank < 1 or rank > 138:
                return ""
            if rank <= 28:
                return "rank-tier-1"
            if rank <= 56:
                return "rank-tier-2"
            if rank <= 83:
                return "rank-tier-3"
            if rank <= 111:
                return "rank-tier-4"
            return "rank-tier-5"

        expected = {
            1: "rank-tier-1", 28: "rank-tier-1",
            29: "rank-tier-2", 56: "rank-tier-2",
            57: "rank-tier-3", 83: "rank-tier-3",
            84: "rank-tier-4", 111: "rank-tier-4",
            112: "rank-tier-5", 138: "rank-tier-5",
        }
        self.assertEqual({rank: tier(rank) for rank in expected}, expected)
        for missing in (None, 0, -1, 139, 1000):
            self.assertEqual(tier(missing), "")

    def test_model_and_shadow_values_use_one_decimal_presentation(self):
        source = PAGE.read_text()
        block = source[
            source.index("function modelDisplay"):source.index("function edgeDisplay")
        ]
        self.assertIn("return n.toFixed(1);", block)
        self.assertNotIn("return 'PK';", block)
        self.assertNotIn("`+${rounded}`", block)
        self.assertIn("modelDisplay(value,market)", source)
        self.assertIn("renderModelSnapshot(game)", source)

    def test_edge_glyphs_are_reserved_for_market_movement(self):
        source = PAGE.read_text()
        edge_block = source[
            source.index("function edgeDisplay"):source.index("const SPREAD_COMPONENTS")
        ]
        self.assertNotIn("▲", edge_block)
        self.assertIn("return Math.abs(n) < .05 ? '0' : n.toFixed(1);", edge_block)
        self.assertIn("return direction==='UP'?'▲':direction==='DOWN'?'▼':'↔';", source)

    def test_activity_uses_compact_et_date_and_time(self):
        source = PAGE.read_text()
        block = source[
            source.index("function activityTime"):source.index("function activityMatchup")
        ]
        self.assertIn("timeZone:'America/New_York'", block)
        self.assertIn("month:'numeric',day:'numeric',hour:'numeric',minute:'2-digit'", block)

    def test_movement_markers_are_large_and_mobile_edges_are_contained(self):
        source = PAGE.read_text()
        self.assertIn(".move-marker{display:none;grid-column:3;grid-row:1 / span 2;align-self:center;justify-self:center;font-size:14px", source)
        self.assertIn(".market-best.has-move{grid-template-columns:22px minmax(30px,1fr) 14px}", source)
        self.assertIn(".mobile-metric.edge-focus{overflow:hidden}", source)
        self.assertIn(".mobile-metric .decision-edge{min-width:0;max-width:100%}", source)
        self.assertIn(".mobile-metric .decision-edge .team-logo-holder{--team-logo-size:18px}", source)
        self.assertIn(".mobile-metric .decision-team-name{width:100%;max-width:100%", source)

    def test_week_zero_dratings_component_coverage_is_eight_of_eight(self):
        payload = json.loads(
            (ROOT / "data/site/war_room_market_matrix.json").read_text()
        )
        games = [
            game for game in payload["games"]
            if game.get("week") == 0
            and game.get("scope", {}).get("fbs_vs_fbs") is True
        ]
        self.assertEqual(len(games), 8)
        for game in games:
            source = (
                game.get("standard_freshness", {}).get("spread", {})
                .get("sources", {}).get("DRatings", {})
            )
            component = (
                game.get("models", {}).get("standard_spread", {})
                .get("component_values", {}).get("DRatings")
            )
            self.assertIs(source.get("participating"), True, game["game_id"])
            self.assertIsInstance(component, (int, float), game["game_id"])


if __name__ == "__main__":
    unittest.main()
