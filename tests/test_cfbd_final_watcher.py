from __future__ import annotations
import importlib.util,json,os,subprocess,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).parents[1]; SPEC=importlib.util.spec_from_file_location("cfbd_final_watcher",ROOT/"scripts/war_room/run_cfbd_final_watcher.py")
watcher=importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(watcher)
def ok(command): return subprocess.CompletedProcess(command,0,"","")

class FinalWatcherTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name); self.db=self.root/"preseason.json"
  self.db.write_text(json.dumps({"games":[{"season":2026,"game_id":"g1","cfbd_game_id":99,"cfbd_start_date":"2026-08-29T16:00:00Z","cfbd_start_time_tbd":False,"cfbd_kickoff_status":"VERIFIED_KICKOFF","date":"2026-08-29","away_team":"Away","home_team":"Home"}]}))
  self.patches=[patch.object(watcher,"DB",self.db),patch.object(watcher,"SCOREBOARD",self.root/"scoreboard.json"),patch.object(watcher,"RESULTS",self.root/"results.json"),patch.object(watcher,"STATE_DIR",self.root/"state"),patch.object(watcher,"STATE",self.root/"state/state.json"),patch.dict(os.environ,{"CFBD_API_KEY":"fixture-only"},clear=False)]
  for item in self.patches:item.start()
  self.cfg={"enabled":True,"monthly_call_limit":5000,"protected_reserve_calls":500,"monitor_window":{"minutes_before_first_kickoff":30,"hours_after_last_kickoff":5},"retry_policy":{"delays_minutes":[5,10,30],"max_attempts":4}}
 def tearDown(self):
  for item in reversed(self.patches):item.stop()
  self.temp.cleanup()
 def score(self,status="in_progress",away=7,home=14):
  return [{"id":99,"startDate":"2026-08-29T16:00:00Z","awayTeam":{"name":"Away","points":away,"classification":"fbs"},"homeTeam":{"name":"Home","points":home,"classification":"fbs"},"status":status,"period":2,"clock":"03:21"}]
 def execute(self,**kwargs):
  return watcher.execute(now=kwargs.pop("now",datetime(2026,8,29,16,tzinfo=timezone.utc)),cfg=kwargs.pop("cfg",self.cfg),trigger="test",**kwargs)
 def test_disabled_and_outside_window_make_zero_calls(self):
  calls=[]; code,r=self.execute(cfg={**self.cfg,"enabled":False},fetch=lambda *a:calls.append(a),runner=ok); self.assertEqual((code,r["status"],calls),(0,"DISABLED",[]))
  code,r=self.execute(now=datetime(2026,8,28,16,tzinfo=timezone.utc),fetch=lambda *a:calls.append(a),runner=ok); self.assertEqual((code,r["status"],r["api_calls_this_run"],calls),(0,"OUTSIDE_GAME_WINDOW",0,[]))
 def test_active_poll_calls_scoreboard_once_and_no_games(self):
  calls=[]; commands=[]; code,r=self.execute(fetch=lambda e,p,k:(calls.append(e) or self.score()),runner=lambda c:(commands.append(c) or ok(c)))
  self.assertEqual((code,r["status"],calls),(0,"NO_NEW_FINALS",["/scoreboard"])); self.assertEqual(len(commands),1); self.assertIn("build_schedule_live_enrichment.py",commands[0][1])
  payload=json.loads(watcher.SCOREBOARD.read_text()); self.assertEqual(payload["games"][0]["home_points"],14); self.assertNotIn("fixture-only",watcher.SCOREBOARD.read_text())
 def test_new_final_requires_acceptance_and_dispatches_once(self):
  commands=[]
  def runner(command):
   commands.append(command)
   if command[1].endswith("build_game_results_2026.py"):watcher.RESULTS.write_text(json.dumps({"games":[{"game_id":"g1","cfbd_game_id":99,"home_score":14,"away_score":7}]}))
   return ok(command)
  code,r=self.execute(fetch=lambda *_:self.score("final"),runner=runner); self.assertEqual((code,r["status"],r["api_calls_this_run"]),(0,"POSTGAME_DISPATCHED",2)); self.assertEqual(sum("pull_cfbd_schedule_2026.py" in x for c in commands for x in c),1); self.assertIn("--prepared-results",commands[-1])
  commands.clear(); code,r=self.execute(now=datetime(2026,8,29,16,5,tzinfo=timezone.utc),fetch=lambda *_:self.score("final"),runner=lambda c:(commands.append(c) or ok(c))); self.assertEqual(r["status"],"NO_NEW_FINALS"); self.assertEqual(len(commands),1)
 def test_unaccepted_final_remains_retryable(self):
  commands=[]; code,r=self.execute(fetch=lambda *_:self.score("final"),runner=lambda c:(commands.append(c) or ok(c))); self.assertEqual((code,r["status"]),(0,"FINAL_CANDIDATE")); self.assertFalse(any("run_war_room_service.py" in x for c in commands for x in c))
  state=json.loads(watcher.STATE.read_text()); self.assertEqual(state["candidates"]["g1"]["attempts"],1); self.assertIn("next_retry_at",state["candidates"]["g1"])
 def test_failed_postgame_is_bounded_and_does_not_revalidate_final(self):
  commands=[]
  def runner(command):
   commands.append(command)
   if command[1].endswith("build_game_results_2026.py"):watcher.RESULTS.write_text(json.dumps({"games":[{"game_id":"g1","cfbd_game_id":99,"home_score":14,"away_score":7}]}))
   return subprocess.CompletedProcess(command,1,"","") if "run_war_room_service.py" in command[1] else ok(command)
  code,r=self.execute(fetch=lambda *_:self.score("final"),runner=runner); self.assertEqual((code,r["status"]),(2,"POSTGAME_FAILED"))
  commands.clear(); code,r=self.execute(now=datetime(2026,8,29,16,2,tzinfo=timezone.utc),fetch=lambda *_:self.score("final"),runner=lambda c:(commands.append(c) or ok(c)))
  self.assertEqual(r["status"],"POSTGAME_FAILED"); self.assertEqual(len(commands),1); self.assertIn("build_schedule_live_enrichment.py",commands[0][1])
 def test_budget_reserve_blocks_before_provider(self):
  usage=self.root/"state/usage_2026-08.json"; usage.parent.mkdir(); usage.write_text(json.dumps({"calls_used":4500,"operations":[]})); calls=[]; code,r=self.execute(fetch=lambda *a:calls.append(a),runner=ok); self.assertEqual((code,r["status"],calls),(2,"BUDGET_BLOCKED",[]))
 def test_schedule_windows_cover_weekday_and_cross_midnight(self):
  games=[{"date":"2026-10-20","cfbd_start_date":"2026-10-20T23:00:00Z","cfbd_start_time_tbd":False},{"date":"2026-10-20","cfbd_start_date":"2026-10-21T03:30:00Z","cfbd_start_time_tbd":False}]; active,detail=watcher.monitoring_window(games,datetime(2026,10,21,5,tzinfo=timezone.utc),self.cfg); self.assertTrue(active); self.assertIn("window_end_et",detail)
  active,_=watcher.monitoring_window(games,datetime(2026,10,22,5,tzinfo=timezone.utc),self.cfg); self.assertFalse(active)
 def test_placeholder_tbd_and_mixed_day_safety(self):
  placeholder={"date":"2026-08-29","cfbd_start_date":"2026-08-29T04:00:00Z","cfbd_start_time_tbd":True}
  active,detail=watcher.monitoring_window([placeholder],datetime(2026,8,29,16,tzinfo=timezone.utc),self.cfg); self.assertTrue(active); self.assertEqual(detail["window_policy"],"BOUNDED_GAME_DAY_FALLBACK"); self.assertEqual(detail["window_start_et"],"2026-08-29T10:30:00-04:00"); self.assertEqual(detail["window_end_et"],"2026-08-30T02:30:00-04:00")
  verified={"date":"2026-08-29","cfbd_start_date":"2026-08-29T16:00:00Z","cfbd_start_time_tbd":False}
  active,detail=watcher.monitoring_window([verified,placeholder],datetime(2026,8,30,6,tzinfo=timezone.utc),self.cfg); self.assertTrue(active); self.assertTrue(detail["mixed_quality_fallback"]); self.assertEqual(detail["window_policy"],"MIXED_FALLBACK_WINDOW"); self.assertEqual(detail["window_end_et"],"2026-08-30T02:30:00-04:00")
  active,_=watcher.monitoring_window([verified,placeholder],datetime(2026,8,30,7,tzinfo=timezone.utc),self.cfg); self.assertFalse(active)
 def test_no_game_day_checks_before_credential_budget_and_provider(self):
  self.db.write_text(json.dumps({"games":[{"season":2026,"game_id":"g1","date":"2026-08-29","cfbd_start_date":"2026-08-29T04:00:00Z","cfbd_start_time_tbd":True}]})); calls=[]
  with patch.dict(os.environ,{},clear=True): code,r=self.execute(now=datetime(2026,8,28,16,tzinfo=timezone.utc),fetch=lambda *a:calls.append(a),runner=ok)
  self.assertEqual((code,r["status"],calls),(0,"OUTSIDE_GAME_WINDOW",[])); self.assertFalse((self.root/"state").exists())
 def test_all_unresolved_known_game_day_does_not_suppress_polling(self):
  self.db.write_text(json.dumps({"games":[{"season":2026,"game_id":"g1","cfbd_game_id":99,"date":"2026-08-29","cfbd_start_date":"2026-08-29T04:00:00Z","cfbd_start_time_tbd":True,"away_team":"Away","home_team":"Home"}]})); calls=[]
  code,r=self.execute(fetch=lambda endpoint,*_:(calls.append(endpoint) or self.score()),runner=ok)
  self.assertEqual((code,r["status"],calls),(0,"NO_NEW_FINALS",["/scoreboard"])); self.assertEqual(r["window"]["window_policy"],"BOUNDED_GAME_DAY_FALLBACK")
 def test_week_zero_exact_verified_window_is_unchanged(self):
  games=[
   {"date":"2026-08-29","cfbd_start_date":"2026-08-29T16:00:00Z","cfbd_start_time_tbd":False},
   {"date":"2026-08-29","cfbd_start_date":"2026-08-30T02:00:00Z","cfbd_start_time_tbd":False},
  ]
  active,detail=watcher.monitoring_window(games,datetime(2026,8,29,16,tzinfo=timezone.utc),self.cfg)
  self.assertTrue(active); self.assertEqual(detail["window_policy"],"EXACT_WINDOW"); self.assertEqual(detail["window_start_et"],"2026-08-29T11:30:00-04:00"); self.assertEqual(detail["window_end_et"],"2026-08-30T03:00:00-04:00")

if __name__=="__main__":unittest.main()
