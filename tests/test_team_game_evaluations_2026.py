import importlib.util
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("model_fit", ROOT / "scripts/model_fit/build_team_game_evaluations_2026.py")
MF = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MF)


class ModelFitMathTests(unittest.TestCase):
    def game(self):
        return {"game_id":"g1", "cfbd_game_id":1, "week":0, "start_date":"2026-08-29T16:00:00Z", "home_team":"Home", "away_team":"Away", "home_margin_actual":7, "home_score":24, "away_score":17, "source":"fixture"}

    def test_team_sign_symmetry_and_math(self):
        model={"model_margin_home":4.0,"component_values":dict.fromkeys(MF.COMPONENTS,4.0),"component_snapshot_timestamps":dict.fromkeys(MF.COMPONENTS,"2026-08-29T12:00:00Z"),"model_observed_at":"2026-08-29T12:00:00Z","model_provenance":MF.SNAPSHOT_PROVENANCE,"source_artifacts":[]}
        market={"market_margin_home":2.0,"close_book":"Pinnacle","close_provider":"fixture","close_timestamp":"2026-08-29T15:00:00Z","close_provenance":"RECONSTRUCTED_FROM_PREKICKOFF_MARKET_SNAPSHOT","market_source_artifact":"fixture"}
        home=MF.grade("Home","Away","home",self.game(),model,market,None); away=MF.grade("Away","Home","away",self.game(),model,market,None)
        for key in ("model_margin","market_margin","actual_margin","model_market_edge","directional_bias_actual","realized_market_residual"):
            self.assertEqual(home[key], -away[key])
        for component in MF.COMPONENTS:
            self.assertEqual(home["component_values"][component], -away["component_values"][component])
        self.assertEqual(home["model_abs_error_actual"],3); self.assertEqual(home["market_abs_error_actual"],5)
        self.assertEqual(home["model_advantage_vs_market_actual"],2); self.assertEqual(home["qualified_edge_result"],"WIN")
        self.assertEqual(away["qualified_edge_result"],"WIN")
        self.assertEqual(home["qualified_edge_side"], away["qualified_edge_side"])

    def test_push_and_timestamp_guard(self):
        self.assertTrue(MF.timestamps_pre_kickoff(["2026-08-29T15:59:59Z"], datetime(2026,8,29,16,tzinfo=timezone.utc)))
        self.assertFalse(MF.timestamps_pre_kickoff(["2026-08-29T16:00:00Z"], datetime(2026,8,29,16,tzinfo=timezone.utc)))

    def test_pgwe_is_complementary_probability(self):
        valid=MF.pgwe_index({"pulled_at":"t","games":[{"id":1,"homePostgameWinProbability":.8,"awayPostgameWinProbability":.2}]})
        invalid=MF.pgwe_index({"games":[{"id":2,"homePostgameWinProbability":.8,"awayPostgameWinProbability":.3}]})
        self.assertEqual(valid["1"][:2],(.8,.2)); self.assertNotIn("2",invalid)

    def test_sp_plus_match_uses_date_pair_and_explicit_alias(self):
        game = {**self.game(), "game_id": "g80", "date": "2026-09-05",
                "home_team": "South Florida", "away_team": "Florida International"}
        rows = [
            {"date":"2026-09-05","team":"USF","opponent":"Florida International","sp_plus_pgwe":.814,"sp_plus_adjusted_margin":8.2},
            {"date":"2026-09-05","team":"Florida International","opponent":"USF","sp_plus_pgwe":.186,"sp_plus_adjusted_margin":-8.2},
        ]
        matched, audit = MF.sp_plus_index({"rows": rows}, [game])
        self.assertEqual(audit["matched_games"], 1)
        self.assertEqual(audit["unmatched"], [])
        self.assertEqual(matched["g80"][MF.sp_plus_team_key("South Florida")]["sp_plus_adjusted_margin"], 8.2)

    def test_cfbd_reference_conversion_examples_and_widened_tail(self):
        examples = ((.5, 0), (.7, 6.5), (.8, 11), (.97, 24), (.98, 30),
                    (.985, 35), (.99, 40), (.995, 50), (.999, 60), (1, 65))
        for probability, expected in examples:
            self.assertEqual(MF.cfbd_equivalent_margin_v1(probability), expected)
        self.assertEqual(MF.cfbd_equivalent_margin_v1(.9805747270584106), 30.6)

    def test_pgwe_conversion_symmetry_monotonicity_and_center(self):
        probabilities = (.001, .01, .1, .49, .5, .51, .9, .99, .999)
        margins = [MF.cfbd_equivalent_margin_v1(p) for p in probabilities]
        self.assertEqual(margins, sorted(margins))
        self.assertEqual(MF.cfbd_equivalent_margin_v1(.5), 0.0)
        for probability in (.01, .1, .49):
            self.assertEqual(MF.cfbd_equivalent_margin_v1(probability), -MF.cfbd_equivalent_margin_v1(1-probability))

    def test_cfbd_conversion_rejects_invalid_values(self):
        for probability in (-.01, 1.01, float("nan"), None):
            with self.assertRaises(ValueError):
                MF.cfbd_equivalent_margin_v1(probability)

    def test_pgwe_margin_team_symmetry_and_error_math(self):
        model={"model_margin_home":4.0,"component_values":dict.fromkeys(MF.COMPONENTS,4.0),"component_snapshot_timestamps":{},"model_observed_at":"t","model_provenance":MF.SNAPSHOT_PROVENANCE,"source_artifacts":[]}
        market={"market_margin_home":2.0,"close_book":"Pinnacle","close_provider":"fixture","close_timestamp":"t","close_provenance":"fixture","market_source_artifact":"fixture"}
        pgwe=(.767,.233,"t")
        sp_home={"sp_plus_pgwe":.8,"sp_plus_adjusted_margin":7,"source":"fixture","collected_at":"t"}
        sp_away={"sp_plus_pgwe":.2,"sp_plus_adjusted_margin":-7,"source":"fixture","collected_at":"t"}
        home=MF.grade("Home","Away","home",self.game(),model,market,pgwe,sp_home); away=MF.grade("Away","Home","away",self.game(),model,market,pgwe,sp_away)
        self.assertEqual(home["cfbd_equivalent_margin"],9.4)
        self.assertEqual(away["cfbd_equivalent_margin"],-9.4)
        self.assertEqual(home["sp_plus_adjusted_margin"],7)
        self.assertEqual(away["sp_plus_adjusted_margin"],-7)
        self.assertEqual(home["model_delta_vs_sp_plus_margin"],-3)
        self.assertEqual(home["model_delta_vs_cfbd_margin"],-5.4)

    def test_missing_pgwe_does_not_change_score_metrics(self):
        model={"model_margin_home":4.0,"component_values":dict.fromkeys(MF.COMPONENTS,4.0),"component_snapshot_timestamps":{},"model_observed_at":"t","model_provenance":MF.SNAPSHOT_PROVENANCE,"source_artifacts":[]}
        market={"market_margin_home":2.0,"close_book":"Pinnacle","close_provider":"fixture","close_timestamp":"t","close_provenance":"fixture","market_source_artifact":"fixture"}
        row=MF.grade("Home","Away","home",self.game(),model,market,None)
        self.assertEqual((row["model_abs_error_actual"],row["market_abs_error_actual"],row["model_advantage_vs_market_actual"]),(3.0,5.0,2.0))
        self.assertIsNone(row["cfbd_equivalent_margin"])
        self.assertIsNone(row["model_abs_error_cfbd_margin"])
        self.assertIsNone(row["sp_plus_adjusted_margin"])

    def test_postgame_lifecycle_matures_and_ages_without_immediate_degradation(self):
        model={"model_margin_home":4.0,"component_values":dict.fromkeys(MF.COMPONENTS,4.0),"component_snapshot_timestamps":{},"model_observed_at":"t","model_provenance":MF.SNAPSHOT_PROVENANCE,"source_artifacts":[]}
        market={"market_margin_home":2.0,"close_book":"Pinnacle","close_provider":"fixture","close_timestamp":"t","close_provenance":"fixture","market_source_artifact":"fixture"}
        fresh=datetime(2026,8,30,12,tzinfo=timezone.utc)
        stale=datetime(2026,9,2,12,tzinfo=timezone.utc)
        score=MF.grade("Home","Away","home",self.game(),model,market,None,now=fresh)
        self.assertEqual(score["lifecycle_state"],"SCORE_READY")
        cfbd=MF.grade("Home","Away","home",self.game(),model,market,(.8,.2,"t"),now=fresh)
        self.assertEqual(cfbd["lifecycle_state"],"CFBD_READY")
        sp={"sp_plus_pgwe":.8,"sp_plus_adjusted_margin":7,"source":"fixture","collected_at":"t"}
        complete=MF.grade("Home","Away","home",self.game(),model,market,(.8,.2,"t"),sp,now=fresh)
        self.assertEqual(complete["lifecycle_state"],"COMPLETE")
        self.assertEqual(MF.grade("Home","Away","home",self.game(),model,market,None,now=stale)["lifecycle_state"],"DEGRADED")

    def test_refresh_preserves_accepted_lens_and_frozen_inputs(self):
        model={"model_margin_home":4.0,"component_values":dict.fromkeys(MF.COMPONENTS,4.0),"component_snapshot_timestamps":{},"model_observed_at":"t","model_provenance":MF.SNAPSHOT_PROVENANCE,"source_artifacts":[]}
        market={"market_margin_home":2.0,"close_book":"Pinnacle","close_provider":"fixture","close_timestamp":"t","close_provenance":"fixture","market_source_artifact":"fixture"}
        sp={"sp_plus_pgwe":.8,"sp_plus_adjusted_margin":7,"source":"fixture","collected_at":"t"}
        first=MF.grade("Home","Away","home",self.game(),model,market,(.8,.2,"t"),sp,now=datetime(2026,8,30,tzinfo=timezone.utc))
        repeated=MF.grade("Home","Away","home",self.game(),model,market,None,None,now=datetime(2026,8,30,tzinfo=timezone.utc),previous=first)
        self.assertEqual(repeated["lifecycle_state"],"COMPLETE")
        self.assertEqual((repeated["model_margin"],repeated["market_margin"]),(4.0,2.0))
        self.assertEqual((repeated["sp_plus_adjusted_margin"],repeated["cfbd_equivalent_margin"]),(7,11.0))

    def test_team_health_rank_agreement_and_sample_are_separate(self):
        base={"model_abs_error_actual":1.0,"market_abs_error_actual":2.0,"model_advantage_vs_market_actual":1.0,"qualified_edge":False,"directional_bias_actual":3.0,"model_market_edge":1.0,"model_abs_error_sp_plus_margin":1.0,"market_abs_error_sp_plus_margin":2.0,"model_advantage_vs_market_sp_plus":1.0,"model_abs_error_cfbd_margin":1.0,"market_abs_error_cfbd_margin":2.0,"model_advantage_vs_market_cfbd":1.0}
        rows=[{**base,"team":"Alpha","lifecycle_state":"COMPLETE","sp_plus_adjusted_margin":8,"directional_bias_sp_plus":4,"cfbd_equivalent_margin":6,"directional_bias_cfbd":2},
              {**base,"team":"Beta","lifecycle_state":"CFBD_READY","sp_plus_adjusted_margin":None,"directional_bias_sp_plus":None,"cfbd_equivalent_margin":1,"directional_bias_cfbd":-3}]
        result={row["team"]:row for row in MF.aggregate(rows)}
        self.assertEqual((result["Alpha"]["model_fit_health"],result["Alpha"]["sample_state"],result["Alpha"]["model_fit_rank"]),("COMPLETE","LOW_SAMPLE",1))
        self.assertEqual((result["Beta"]["model_fit_health"],result["Beta"]["display_model_fit"],result["Beta"]["model_fit_rank"]),("PARTIAL",None,None))
        self.assertEqual(result["Alpha"]["agreement"],"AGREE")
        self.assertEqual(result["Alpha"]["performance_vs_model"], 3)
        self.assertEqual(result["Alpha"]["display_model_fit"], result["Alpha"]["performance_vs_model"])

    def test_pgwe_aggregate_keeps_score_and_pgwe_lenses_separate(self):
        row = {
            "team":"Home", "model_abs_error_actual":3.0, "market_abs_error_actual":5.0,
            "model_advantage_vs_market_actual":2.0, "qualified_edge":False,
            "directional_bias_actual":3.0, "model_market_edge":2.0,
            "sp_plus_adjusted_margin":6.7, "model_abs_error_sp_plus_margin":2.7,
            "market_abs_error_sp_plus_margin":4.7, "model_advantage_vs_market_sp_plus":2.0,
            "directional_bias_sp_plus":2.7, "cfbd_equivalent_margin":8.5,
            "model_abs_error_cfbd_margin":4.5, "market_abs_error_cfbd_margin":6.5,
            "model_advantage_vs_market_cfbd":2.0, "directional_bias_cfbd":4.5,
        }
        result = MF.aggregate([row])[0]
        self.assertEqual((result["model_mae_vs_actual"], result["market_mae_vs_actual"], result["advantage_actual"], result["bias_actual"]), (3.0,5.0,2.0,3.0))
        self.assertEqual((result["model_mae_vs_sp_plus_margin"], result["market_mae_vs_sp_plus_margin"], result["model_advantage_vs_market_sp_plus"], result["directional_bias_sp_plus"]), (2.7,4.7,2.0,2.7))
        self.assertEqual((result["sp_plus_games_available"], result["model_beat_market_sp_plus_games"], result["sp_plus_ties"]), (1,1,0))
        self.assertEqual((result["cfbd_games_available"], result["model_mae_vs_cfbd_margin"]), (1,4.5))

    def test_captured_selected_side_line_normalizes_to_home_margin(self):
        base={"canonical_game_id":"g1","market_type":"spread","checkpoint":"CLOSE","selection_status":"OFFICIAL","market_benchmark":"FROZEN_CLOSE","market_observed_at":"2026-08-29T15:00:00Z","market_line":2.5,"market_book":"Pinnacle"}
        away=MF.captured_close(self.game(), [{**base,"bet_side":"away"}])
        home=MF.captured_close(self.game(), [{**base,"bet_side":"home"}])
        self.assertEqual(away["market_margin_home"],2.5)
        self.assertEqual(home["market_margin_home"],-2.5)


class HistoricalModelRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.game = {"game_id":"g12", "start_date":"2026-09-03T23:30:00Z"}
        self.projection = {
            "model_id": MF.MODEL_ID, "authority":"OFFICIAL",
            "formula_status":"PRODUCTION_VALIDATED", "formula_version":"v1",
            "value_home_margin": 2.5, "build_timestamp":"2026-09-01T02:13:57Z",
            "component_values":{"SP+":1.0,"FPI":2.0,"TeamRankings":3.0,"DRatings":4.0},
            "component_status":dict.fromkeys(MF.COMPONENTS,"PRESENT"),
            "weights":dict(MF.WEIGHTS),
            "component_source_timestamps":dict.fromkeys(MF.COMPONENTS,"2026-08-31T13:19:11Z"),
        }
        self.contract = {
            "artifact_path":MF.RECONSTRUCTED_CONTRACT_PATH,
            "source_git_commit":"cad503f9754f4ee057ef2040e5c297e8fdae08e7",
            "source_path":"data/site/current_game_projection_contract.json",
            "source_commit_timestamp":"2026-08-31T22:25:26-04:00",
            "games":[{"game_id":"g12","projection":self.projection}],
        }

    def assert_rejected(self, mutate):
        payload=deepcopy(self.contract); mutate(payload["games"][0]["projection"])
        model, gap=MF.reconstructed_contract_model(self.game,payload)
        self.assertIsNone(model); self.assertEqual(gap,"no_valid_prekickoff_projection_contract")

    def test_valid_contract_preserves_reconstructed_provenance(self):
        model,gap=MF.reconstructed_contract_model(self.game,self.contract)
        self.assertIsNone(gap); self.assertEqual(model["model_margin_home"],2.5)
        self.assertEqual(model["model_provenance"],MF.CONTRACT_PROVENANCE)
        self.assertEqual(model["source_git_commit"],"cad503f9754f4ee057ef2040e5c297e8fdae08e7")

    def test_rejects_post_kickoff_source_or_build_timestamp(self):
        self.assert_rejected(lambda p:p["component_source_timestamps"].update({"SP+":self.game["start_date"]}))
        self.assert_rejected(lambda p:p.update({"build_timestamp":self.game["start_date"]}))

    def test_rejects_missing_or_nonpresent_component(self):
        self.assert_rejected(lambda p:p["component_values"].pop("DRatings"))
        self.assert_rejected(lambda p:p["component_status"].update({"DRatings":"MISSING"}))

    def test_rejects_wrong_weights(self):
        self.assert_rejected(lambda p:p["weights"].update({"SP+":0.20}))
        self.assert_rejected(lambda p:p["weights"].update({"Sagarin Rating":0.25}))

    def test_rejects_wrong_identity_and_authority_fields(self):
        for key,value in (("model_id","other"),("authority","LEGACY_COMPARISON"),("formula_status","DRAFT"),("formula_version","v2")):
            self.assert_rejected(lambda p,k=key,v=value:p.update({k:v}))

    def test_rejects_arithmetic_mismatch(self):
        self.assert_rejected(lambda p:p.update({"value_home_margin":2.6}))

    def test_captured_precedes_contract_and_component_snapshot(self):
        captured={"canonical_game_id":"g12","model_id":MF.MODEL_ID,"formula_version":"v1","lifecycle_state":"PRODUCTION_VALIDATED","provenance_flags":{"authority":"OFFICIAL"},"projection":9.0,"component_values":dict.fromkeys(MF.COMPONENTS,9.0),"source_snapshot_timestamps":dict.fromkeys(MF.COMPONENTS,"2026-09-01T00:00:00Z"),"observed_at":"2026-09-01T01:00:00Z"}
        snapshots = {
            "games": [{
                "game_id": "g12",
                "observed_at": "2026-09-01T00:00:00Z",
                "component_values": dict.fromkeys(MF.COMPONENTS, 1.0),
                "component_source_timestamps": dict.fromkeys(
                    MF.COMPONENTS, "2026-09-01T00:00:00Z"
                ),
            }]
        }
        model,gap=MF.recover_model(self.game,[captured],self.contract,snapshots)
        self.assertIsNone(gap); self.assertEqual(model["model_margin_home"],9.0)
        self.assertEqual(model["model_provenance"],"CAPTURED")

    def test_contract_precedes_component_snapshot(self):
        snapshots = {
            "games": [{
                "game_id": "g12",
                "observed_at": "2026-09-01T00:00:00Z",
                "component_values": dict.fromkeys(MF.COMPONENTS, 1.0),
                "component_source_timestamps": dict.fromkeys(
                    MF.COMPONENTS, "2026-09-01T00:00:00Z"
                ),
            }]
        }
        model,gap=MF.recover_model(self.game,[],self.contract,snapshots)
        self.assertIsNone(gap); self.assertEqual(model["model_margin_home"],2.5)
        self.assertEqual(model["model_provenance"],MF.CONTRACT_PROVENANCE)

    def test_unavailable_when_all_sources_reject(self):
        model,gap=MF.recover_model(self.game,[],{"games":[]},{"games":[]})
        self.assertIsNone(model); self.assertEqual(gap,"no_complete_prekickoff_four_component_snapshot")


if __name__ == "__main__": unittest.main()
