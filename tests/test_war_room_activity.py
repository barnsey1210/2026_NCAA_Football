import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/war_room/build_war_room_activity.py"
SPEC = importlib.util.spec_from_file_location("war_room_activity", SCRIPT)
activity = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(activity)


def pair(line, price=-110, stamp="2026-08-27T12:00:00Z"):
    return {
        "away": {"line": -line, "price": price, "source": "The Odds API", "last_update": stamp},
        "home": {"line": line, "price": price, "source": "The Odds API", "last_update": stamp},
    }


def total_pair(line, price=-110, stamp="2026-08-27T12:00:00Z"):
    return {
        "over": {"line": line, "price": price, "source": "The Odds API", "last_update": stamp},
        "under": {"line": line, "price": price, "source": "The Odds API", "last_update": stamp},
    }


def matrix(spread=-3.0, spread_price=-110, include_total=True):
    book = {"spread": pair(spread, spread_price)}
    if include_total:
        book["total"] = total_pair(52.5)
    return {
        "schema_version": "war-room-market-matrix-v1",
        "built_at": "2026-08-27T12:01:00Z",
        "fast_market_refresh": {"refresh_id": "fixture-1"},
        "games": [{
            "game_id": "2026-1-a-b", "season": 2026, "week": 1,
            "away_team": "A", "home_team": "B", "scope": {"fbs_vs_fbs": True},
            "state": "SHADOW", "authority": {"spread": "SHADOW", "total": "SHADOW"},
            "models": {"shadow_spread": {}, "shadow_total": {}},
            "market": {"primary_sportsbooks": {"DraftKings": book}},
        }],
    }


class WarRoomActivityTest(unittest.TestCase):
    def test_first_market_is_one_event_per_domain_and_persists_across_reloads(self):
        health = {"ratings_health": {"sources": {}}}
        empty = matrix(include_total=False)
        empty["games"][0]["market"]["primary_sportsbooks"] = {}
        before = activity.current_snapshot(empty, health, {}, {})
        opened_matrix = matrix()
        opened_matrix["games"][0]["market"]["primary_sportsbooks"]["FanDuel"] = {
            "spread": pair(-3.0), "total": total_pair(52.5)
        }
        after = activity.current_snapshot(opened_matrix, health, {}, {})
        events = activity.detect(before, after, "2026-08-27T12:02:00Z")
        opened = [row for row in events if row["event_type"] == "MARKET_OPENED"]
        self.assertEqual([row["market"] for row in opened], ["spread", "total"])
        self.assertEqual(activity.detect(after, after, "2026-08-27T12:03:00Z"), [])

        first = activity.first_market_availability(before, after, "2026-08-27T12:02:00Z")
        persisted = activity.first_market_availability(
            {**after, "first_market_availability": first}, after, "2026-08-27T12:03:00Z"
        )
        self.assertEqual(first, persisted)
        self.assertFalse(first["2026-1-a-b|spread"]["baseline"])
        self.assertFalse(first["2026-1-a-b|total"]["baseline"])

    def test_startup_inventory_and_legacy_state_are_baselined(self):
        health = {"ratings_health": {"sources": {}}}
        current = activity.current_snapshot(matrix(), health, {}, {})
        startup = activity.first_market_availability({}, current, "2026-08-27T12:02:00Z")
        self.assertTrue(all(row["baseline"] for row in startup.values()))
        legacy = {
            "opened_game_market_keys": current["opened_game_market_keys"],
            "markets": current["markets"],
        }
        migrated = activity.first_market_availability(legacy, current, "2026-08-27T12:02:00Z")
        self.assertTrue(all(row["baseline"] for row in migrated.values()))

    def test_line_change_is_event_but_price_only_change_is_not(self):
        health = {"ratings_health": {"sources": {}}}
        before = activity.current_snapshot(matrix(), health, {}, {})
        after = activity.current_snapshot(matrix(spread=-3.5), health, {}, {})
        events = activity.detect(before, after, "2026-08-27T12:02:00Z")
        moves = [row for row in events if row["event_type"] == "SPREAD_MOVED"]
        self.assertEqual(len(moves), 1)
        self.assertEqual((moves[0]["old_line"], moves[0]["new_line"]), (-3.0, -3.5))
        price_only = activity.current_snapshot(matrix(spread=-3.5, spread_price=-105), health, {}, {})
        self.assertFalse(any("MOVED" in row["event_type"] for row in activity.detect(after, price_only, "2026-08-27T12:03:00Z")))

    def test_removed_pair_and_stable_idempotency(self):
        health = {"ratings_health": {"sources": {}}}
        before = activity.current_snapshot(matrix(), health, {}, {})
        after = activity.current_snapshot(matrix(include_total=False), health, {}, {})
        first = activity.detect(before, after, "2026-08-27T12:02:00Z")
        second = activity.detect(before, after, "2026-08-27T12:02:00Z")
        removed = [row for row in first if row["event_type"] == "BOOK_MARKET_REMOVED"]
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]["event_id"], [row for row in second if row["event_type"] == "BOOK_MARKET_REMOVED"][0]["event_id"])

    def test_ratings_model_shadow_final_and_health_transitions(self):
        before_health = {"ratings_health": {"sources": {"SP+": {
            "source": "SP+", "last_changed_at": "2026-08-20T12:00:00Z", "status": "CURRENT"
        }}}}
        after_health = {"ratings_health": {"sources": {"SP+": {
            "source": "SP+", "last_changed_at": "2026-08-27T12:00:00Z", "status": "CURRENT"
        }}}}
        before_matrix = matrix(include_total=False)
        after_matrix = matrix()
        after_game = after_matrix["games"][0]
        after_game["state"] = "HYBRID"
        after_game["authority"]["spread"] = "HYBRID"
        after_game["models"]["shadow_spread"] = {
            "model_id": "shadow_spread_sp_sagarin_v1", "selection_status": "AVAILABLE",
            "value_home_line": -2.5,
        }
        before = activity.current_snapshot(before_matrix, before_health, {}, {})
        results = {"games": [{
            "game_id": "2026-1-a-b", "season": 2026, "week": 1,
            "away_team": "A", "home_team": "B", "away_score": 21, "home_score": 24,
            "completed_at": "2026-08-27T12:04:00Z", "source": "CFBD",
        }]}
        after = activity.current_snapshot(after_matrix, after_health, results, {})
        events = activity.detect(before, after, "2026-08-27T12:05:00Z")
        kinds = {row["event_type"] for row in events}
        self.assertTrue({"MARKET_OPENED", "RATING_UPDATED", "MODEL_STATE_CHANGED", "SHADOW_SPREAD_READY", "FINAL_POSTED"} <= kinds)
        required = {
            "event_id", "event_type", "event_timestamp", "detected_at", "refresh_id",
            "season", "week", "game_id", "away_team", "home_team", "book", "market",
            "side", "old_line", "new_line", "old_price", "new_price", "source",
            "significance", "metadata",
        }
        self.assertTrue(all(required <= set(row) for row in events))

    def test_public_move_threshold_books_and_aggregation(self):
        def move(book, old, new, at, event_id):
            return {
                "event_id": event_id, "event_type": "SPREAD_MOVED", "event_timestamp": at,
                "observed_at": at, "detected_at": at, "refresh_id": "r2", "season": 2026,
                "week": 1, "game_id": "g1", "away_team": "A", "home_team": "B",
                "book": book, "market": "spread", "side": "home", "old_line": old,
                "new_line": new, "old_price": -110, "new_price": -110, "metadata": {},
            }
        history = [
            move("DraftKings", -4.5, -5.0, "2026-08-27T12:00:00Z", "dk"),
            move("FanDuel", -4.5, -5.0, "2026-08-27T12:00:40Z", "fd"),
            move("Caesars", -4.5, -4.75, "2026-08-27T12:00:45Z", "small"),
            move("Novig", -4.5, -5.0, "2026-08-27T12:00:20Z", "novig"),
        ]
        projected = activity.project_public(history)
        self.assertEqual(len(projected), 1)
        self.assertEqual(projected[0]["event_type"], "MARKET_MOVE")
        self.assertEqual(projected[0]["metadata"]["books"], ["DraftKings", "FanDuel"])
        self.assertEqual(projected[0]["underlying_event_ids"], ["dk", "fd"])

    def test_pinnacle_lead_and_retail_follow(self):
        base = {
            "event_type": "TOTAL_MOVED", "refresh_id": "r3", "season": 2026, "week": 1,
            "game_id": "g1", "away_team": "A", "home_team": "B", "market": "total",
            "side": "over", "old_line": 58.5, "new_line": 59.0, "old_price": -110,
            "new_price": -110, "metadata": {},
        }
        rows = []
        for event_id, book, timestamp in (
            ("p", "Pinnacle", "2026-08-27T12:00:00Z"),
            ("d", "DraftKings", "2026-08-27T12:00:30Z"),
            ("f", "FanDuel", "2026-08-27T12:00:45Z"),
        ):
            rows.append({**base, "event_id": event_id, "book": book, "event_timestamp": timestamp,
                         "observed_at": timestamp, "detected_at": timestamp})
        projected = activity.project_public(rows)
        self.assertEqual({row["event_type"] for row in projected}, {"PINNACLE_MOVE", "MARKET_FOLLOW"})

    def test_ratings_aggregate_and_technical_postgame_is_hidden(self):
        rows = []
        for event_id, source in (("sp", "SP+"), ("fp", "FPI"), ("dr", "DRatings")):
            rows.append({
                "event_id": event_id, "event_type": "RATING_UPDATED",
                "event_timestamp": "2026-08-27T12:00:00Z", "observed_at": "2026-08-27T12:00:00Z",
                "detected_at": "2026-08-27T12:00:02Z", "refresh_id": "ratings-1",
                "source": source, "metadata": {},
            })
        rows.append({
            "event_id": "pg", "event_type": "POSTGAME_REFRESHED",
            "event_timestamp": "2026-08-27T12:00:03Z", "metadata": {},
        })
        projected = activity.project_public(rows)
        self.assertEqual(len(projected), 1)
        self.assertEqual(projected[0]["event_type"], "RATINGS_UPDATED")
        self.assertEqual(projected[0]["metadata"]["sources"], ["SP+", "FPI", "DRatings"])

    def test_game_index_filters_events_and_excludes_global_ratings(self):
        game_event = {
            "event_id": "game", "event_type": "MODEL_STATE_CHANGED",
            "event_timestamp": "2026-08-27T12:00:00Z", "observed_at": "2026-08-27T12:00:00Z",
            "game_id": "g1", "week": 1, "away_team": "A", "home_team": "B", "metadata": {},
        }
        global_rating = {
            "event_id": "rating", "event_type": "RATINGS_UPDATED",
            "event_timestamp": "2026-08-27T12:01:00Z", "observed_at": "2026-08-27T12:01:00Z",
            "game_id": None, "metadata": {"sources": ["SP+"]},
        }
        index = activity.build_game_index(
            [global_rating, game_event], {},
            {"g1": {"season": 2026, "week": 1, "away_team": "A", "home_team": "B"}},
            "2026-08-27T12:02:00Z", "fixture",
        )
        self.assertEqual([row["event_id"] for row in index["games"]["g1"]["events"]], ["game"])

    def test_game_index_adds_canonical_openers_and_immediate_prior_games(self):
        def event(event_id, event_type, game_id, stamp, away, home):
            return {
                "event_id": event_id, "event_type": event_type,
                "event_timestamp": stamp, "observed_at": stamp,
                "game_id": game_id, "away_team": away, "home_team": home,
                "season": 2026, "week": 1, "metadata": {}, "payload": {},
            }

        games = {
            "a-old": {"season": 2026, "week": 0, "away_team": "X", "home_team": "A",
                      "kickoff_time": "2026-08-20T23:00:00Z"},
            "a-latest": {"season": 2026, "week": 0, "away_team": "A", "home_team": "Y",
                         "kickoff_time": "2026-08-24T23:00:00Z"},
            "selected": {"season": 2026, "week": 1, "away_team": "A", "home_team": "B",
                         "kickoff_time": "2026-08-29T23:00:00Z"},
        }
        public = [
            event("old-final", "FINAL_POSTED", "a-old", "2026-08-21T03:00:00Z", "X", "A"),
            event("latest-final", "FINAL_POSTED", "a-latest", "2026-08-25T03:00:00Z", "A", "Y"),
            event("latest-shadow", "SHADOW_SPREAD_READY", "a-latest", "2026-08-25T04:00:00Z", "A", "Y"),
            event("technical", "POSTGAME_REFRESHED", "a-latest", "2026-08-25T04:01:00Z", "A", "Y"),
            event("selected-final", "FINAL_POSTED", "selected", "2026-08-30T03:00:00Z", "A", "B"),
        ]
        line_history = {"selected": [{
            "snapshot_ts": "2026-08-27T12:00:00Z", "market_spread_home": -4.5,
            "market_spread_book": "DraftKings", "market_spread_price": -110,
            "source": "canonical fixture",
        }]}
        index = activity.build_game_index(
            public, line_history, games, "2026-08-27T13:00:00Z", "fixture",
        )
        selected = index["games"]["selected"]
        self.assertEqual(selected["prior_games"]["away"]["game_id"], "a-latest")
        self.assertEqual(selected["prior_games"]["away"]["status"], "SHADOW_READY")
        self.assertEqual(
            {row["event_id"] for row in selected["prior_games"]["away"]["events"]},
            {"latest-final", "latest-shadow"},
        )
        self.assertEqual(selected["prior_games"]["home"]["status"], "NO_PRIOR_GAME")
        self.assertEqual(selected["prior_games"]["home"]["events"], [])
        selected_types = [row["event_type"] for row in selected["events"]]
        self.assertIn("MARKET_OPENED", selected_types)
        self.assertIn("FINAL_POSTED", selected_types)
        self.assertNotIn("POSTGAME_REFRESHED", selected["prior_games"]["away"]["events"])
        self.assertEqual(len({row["event_id"] for row in selected["events"]}), len(selected["events"]))

    def test_opener_authority_uses_earliest_canonical_history(self):
        rows = [
            {"snapshot_ts": "2026-08-25T12:00:00Z", "market_spread_home": -4.5,
             "market_spread_book": "FanDuel", "market_spread_price": -110, "source": "later"},
            {"snapshot_ts": "2026-08-24T12:00:00Z", "market_spread_home": -3.5,
             "market_spread_book": "DraftKings", "market_spread_price": -105, "source": "first"},
        ]
        opener = activity.first_tracked_opener(rows, "spread")
        self.assertEqual((opener["line"], opener["book"], opener["price"]), (-3.5, "DraftKings", -105))
        self.assertEqual(opener["authority"], "FIRST_TRACKED_ACCEPTED")
        self.assertIsNone(activity.first_tracked_opener(rows, "total"))

    def test_game_mode_preserves_public_market_suppression(self):
        def move(event_id, book, old, new):
            return {"event_id": event_id, "event_type": "SPREAD_MOVED",
                    "event_timestamp": "2026-08-27T12:00:00Z", "observed_at": "2026-08-27T12:00:00Z",
                    "detected_at": "2026-08-27T12:00:00Z", "game_id": "g1", "week": 1,
                    "away_team": "A", "home_team": "B", "book": book, "market": "spread",
                    "old_line": old, "new_line": new, "old_price": -110, "new_price": -110,
                    "metadata": {}}
        projected = activity.project_public([
            move("novig", "Novig", -3.0, -4.0),
            move("small", "DraftKings", -3.0, -3.25),
            move("visible", "FanDuel", -3.0, -3.5),
        ])
        index = activity.build_game_index(projected, {}, {"g1": {}}, "2026-08-27T12:01:00Z", "r1")
        underlying = {item for row in index["games"]["g1"]["events"] for item in row["underlying_event_ids"]}
        self.assertEqual(underlying, {"visible"})

    def test_resolved_fallback_pair_does_not_create_false_events(self):
        health = {"ratings_health": {"sources": {}}}
        prior = activity.current_snapshot(matrix(), health, {}, {})
        resolved_after_raw_omission = activity.current_snapshot(matrix(), health, {}, {})
        self.assertEqual(activity.detect(prior, resolved_after_raw_omission, "2026-08-27T12:10:00Z"), [])

    def test_new_book_on_existing_game_market_is_not_false_game_opener(self):
        health = {"ratings_health": {"sources": {}}}
        before_matrix = matrix()
        after_matrix = matrix()
        after_matrix["games"][0]["market"]["primary_sportsbooks"]["FanDuel"] = {
            "spread": pair(-3.0, stamp="2026-08-27T12:10:00Z"),
            "total": total_pair(52.5, stamp="2026-08-27T12:10:00Z"),
        }
        events = activity.detect(
            activity.current_snapshot(before_matrix, health, {}, {}),
            activity.current_snapshot(after_matrix, health, {}, {}),
            "2026-08-27T12:10:01Z",
        )
        market_events = [row for row in events if row.get("entity_type") == "market"]
        self.assertEqual({row["event_type"] for row in market_events}, {"BOOK_MARKET_ADDED"})

    def test_first_run_baselines_without_synthetic_openers(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            (tmp / "matrix.json").write_text(json.dumps(matrix()))
            (tmp / "health.json").write_text(json.dumps({"ratings_health": {"sources": {}}}))
            import subprocess
            command = [
                "python3", str(SCRIPT), "--matrix", str(tmp / "matrix.json"),
                "--health", str(tmp / "health.json"), "--results", str(tmp / "none.json"),
                "--postgame", str(tmp / "none2.json"), "--history", str(tmp / "events.jsonl"),
                "--state", str(tmp / "state.json"), "--output", str(tmp / "activity.json"),
                "--line-history", str(tmp / "line-history.json"),
                "--book-history", str(tmp / "book-history.csv"),
                "--game-index-output", str(tmp / "game-index.json"),
                "--detected-at", "2026-08-27T12:05:00Z",
            ]
            subprocess.run(command, check=True, cwd=ROOT)
            payload = json.loads((tmp / "activity.json").read_text())
            self.assertEqual(payload["new_event_count"], 0)
            self.assertEqual(payload["events"], [])
            self.assertEqual(payload["pipeline_refreshes"]["market"], "2026-08-27T12:01:00Z")
            subprocess.run(command, check=True, cwd=ROOT)
            repeated = json.loads((tmp / "activity.json").read_text())
            self.assertEqual(repeated["new_event_count"], 0)
            self.assertEqual(repeated["event_count"], 0)

    def test_page_uses_activity_contract_and_replaces_old_rail(self):
        source = (ROOT / "scripts/site/build_war_room_page.py").read_text()
        self.assertIn("data/site/war_room_activity.json", source)
        self.assertIn("/war-room/live/activity", source)
        self.assertIn("WAR ROOM ACTIVITY", source)
        self.assertIn('id="activityUpdated"', source)
        self.assertIn("syncWorkingViewport", source)
        self.assertIn("activityBookLogos", source)
        self.assertIn("selectActivityGame", source)
        self.assertIn("clearActivityGame", source)
        self.assertIn("game-selected", source)
        self.assertIn("openerEventsFromSummary", source)
        self.assertIn("PRIOR GAME", source)
        self.assertNotIn('class="opening-market"', source)
        self.assertIn(".team-logo-holder{", source)
        self.assertIn(".activity-summary.has-activity{", source)
        self.assertIn(".activity-summary.has-edge{", source)
        self.assertIn("activity-summary-chip", source)
        self.assertIn('data-filter="EDGE"', source)
        self.assertIn("recent_change_events", source)
        self.assertIn("image-rendering:auto", source)
        self.assertNotIn("drop-shadow(0 0 1px rgba(255,255,255,.90))", source)
        self.assertGreaterEqual(source.count('class="team-logo-holder"'), 4)
        self.assertNotIn(".market-book-logo .team-logo-holder", source)
        self.assertIn('id="activitySnapshot"', source)
        self.assertIn("renderMarketSnapshot", source)
        self.assertIn("renderModelSnapshot", source)
        self.assertIn("renderPostgameSnapshot", source)
        self.assertIn("ACTIVITY_FILTER==='ALL' ? genuineSelectedEvents", source)
        self.assertIn("event.entity_type!=='market_opener'", source)
        self.assertIn('class="decision-team-name"', source)
        self.assertIn("game_id=${encodeURIComponent(game.game_id)}", source)
        self.assertIn("GAME_ACTIVITY_CACHE", source)
        self.assertIn("[data-no-game-select]", source)
        self.assertIn("MARKET HEALTH", source)
        self.assertNotIn("FAST MARKET HEALTH", source)
        self.assertNotIn("fast games", source)
        for stale in ("BETTABLE BOOKS", "SHARP / EXCHANGE", "MOVEMENT STUDY"):
            self.assertNotIn(stale, source)
        ids = set(re.findall(r'id=["\']([^"\']+)', source))
        direct_refs = set(re.findall(r"getElementById\(['\"]([^'\"]+)", source))
        self.assertEqual(direct_refs - ids, set())


if __name__ == "__main__":
    unittest.main()
