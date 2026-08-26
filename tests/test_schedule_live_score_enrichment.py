import importlib.util,unittest
from pathlib import Path

SPEC=importlib.util.spec_from_file_location("schedule_live",Path(__file__).parents[1]/"scripts/site/build_schedule_live_enrichment.py")
module=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(module)

class ScheduleLiveEnrichmentTests(unittest.TestCase):
 def test_scoreboard_overwrites_active_snapshot_and_result_wins(self):
  records={("id","g1"):{"game_id":"g1","status":"scheduled","home_score":None,"away_score":None}}
  module.apply_scoreboard(records,[{"game_id":"g1","status":"Q1","home_points":7,"away_points":0}],"t1")
  module.apply_scoreboard(records,[{"game_id":"g1","status":"Q2","home_points":14,"away_points":7}],"t2")
  self.assertEqual(records[("id","g1")]["live_home_score"],14); self.assertEqual(records[("id","g1")]["scoreboard_pulled_at"],"t2")
  module.apply_canonical_results(records,[{"game_id":"g1","home_score":21,"away_score":17}])
  self.assertEqual(records[("id","g1")]["live_home_score"],21); self.assertEqual(records[("id","g1")]["live_score_source"],"canonical game_results_2026")
 def test_schedule_renderer_keeps_live_grading_pending(self):
  source=(Path(__file__).parents[1]/"schedule.html").read_text(); self.assertIn("return{score:liveScore(r),ats:'Pending',ou:'Pending'}",source); self.assertIn("/war-room/live/schedule",source)
  for label in ("'HALF'","'FINAL'","live_period","live_clock"):self.assertIn(label,source)

if __name__=="__main__":unittest.main()
