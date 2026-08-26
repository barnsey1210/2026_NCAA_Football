import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.schedule.kickoff_quality import classify_kickoff

ROOT=Path(__file__).parents[1]; SPEC=importlib.util.spec_from_file_location("overlay",ROOT/"scripts/schedule/apply_cfbd_schedule_overlay_2026.py"); overlay=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(overlay)

class KickoffQualityTests(unittest.TestCase):
 def test_quality_states(self):
  self.assertEqual(classify_kickoff("2026-08-29T16:00:00Z",False),"VERIFIED_KICKOFF")
  self.assertEqual(classify_kickoff("2026-08-29T04:00:00Z",True),"DATE_PLACEHOLDER")
  self.assertEqual(classify_kickoff("2026-08-29T16:00:00Z",True),"TBD")
  self.assertEqual(classify_kickoff(None,False),"MISSING")
  self.assertEqual(classify_kickoff("bad",False),"UNRESOLVED")
 def test_placeholder_does_not_overwrite_verified_canonical_kickoff(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary); db=root/"db.json"; schedule=root/"schedule.json"; audit=root/"audit.json"
   db.write_text(json.dumps({"games":[{"game_id":"g1","cfbd_game_id":99,"date":"2026-08-29","away_team":"Away","home_team":"Home","cfbd_start_date":"2026-08-29T16:00:00Z","cfbd_start_time_tbd":False,"cfbd_kickoff_status":"VERIFIED_KICKOFF","cfbd_kickoff_time_verified":True}]}))
   schedule.write_text(json.dumps({"games":[{"cfbd_game_id":99,"date":"2026-08-29","away_team":"Away","home_team":"Home","start_date":"2026-08-29T04:00:00Z","start_time_tbd":True,"kickoff_status":"DATE_PLACEHOLDER","kickoff_time_verified":False}]}))
   with patch.object(overlay,"DB",db),patch.object(overlay,"SCHEDULE",schedule),patch.object(overlay,"AUDIT",audit),patch.object(sys,"argv",["overlay","--apply"]):overlay.main()
   result=json.loads(db.read_text())["games"][0]; self.assertEqual(result["cfbd_start_date"],"2026-08-29T16:00:00Z"); self.assertTrue(result["cfbd_kickoff_time_verified"]); self.assertEqual(result["cfbd_kickoff_status"],"VERIFIED_KICKOFF")

if __name__=="__main__":unittest.main()
