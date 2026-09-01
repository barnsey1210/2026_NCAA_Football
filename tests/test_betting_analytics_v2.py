import json,tempfile,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class BettingAnalyticsV2Tests(unittest.TestCase):
 def test_historical_defaults_and_canonical_cells(self):
  c=json.loads((ROOT/'data/site/historical_betting_analytics_v2.json').read_text());self.assertEqual(c['default_selection']['spread'],{'model_id':'standard_spread_4src_equal_v1','checkpoint':'SUN_9AM_ET','threshold':3.0});s=next(x for x in c['independent_checkpoint_performance'] if x['model_id']=='standard_spread_4src_equal_v1' and x['checkpoint']=='SUN_9AM_ET' and x['threshold']==3.0);self.assertEqual((s['n'],s['record']),(324,'193-130-1'));self.assertAlmostEqual(s['roi'],.138528,places=5)
 def test_total_weekday_history_not_fabricated(self):
  c=json.loads((ROOT/'data/site/historical_betting_analytics_v2.json').read_text());weekday={'MON_9AM_ET','MON_3PM_ET','TUE_2PM_ET','WED_2PM_ET','THU_2PM_ET','FRI_2PM_ET'};self.assertFalse(any(x['market_type']=='total' and x['checkpoint'] in weekday for x in c['independent_checkpoint_performance']))
 def test_exact_candidate_formulas_and_shadow_ids(self):
  c=json.loads((ROOT/'data/site/current_game_projection_contract.json').read_text())['model_definitions'];self.assertEqual(c['standard_spread_4src_equal_v1']['weights'],{'SP+':.25,'FPI':.25,'TeamRankings':.25,'DRatings':.25});self.assertEqual(c['standard_total_sp_massey_dratings_v1']['weights'],{'SP+':.4,'Massey Dual':.4,'DRatings Total':.2});self.assertEqual(c['total_sp50_massey50_v1']['weights'],{'SP+':.5,'Massey Dual':.5});self.assertIn('shadow_spread_sp_sagarin_v1',c);self.assertIn('shadow_total_enhanced_spplus_od_v1',c)
 def test_append_only_content_id_behavior(self):
  p=ROOT/'scripts/model_tracking/v2/immutable_tracking.py';s=importlib.util.spec_from_file_location('immutable_tracking',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'x.jsonl';a={'id':m.stable_id('prediction','g1','state1')};b={'id':m.stable_id('prediction','g1','state2')};m.append_unique(out,[a],'id',True);before=out.read_bytes();self.assertEqual(m.append_unique(out,[a],'id',True)['accepted'],0);self.assertEqual(before,out.read_bytes());self.assertEqual(m.append_unique(out,[b],'id',True)['accepted'],1);self.assertEqual(len(out.read_text().splitlines()),2)
 def test_page_and_performance_contract(self):
  page=(ROOT/'betting.html').read_text();self.assertIn('historicalDecayPanel',page);self.assertIn('betting_analytics.js',page);self.assertIn('Beat Close',page);p=json.loads((ROOT/'data/site/model_performance_view.json').read_text());self.assertEqual(p['schema_version'],'model-performance-view-v3');self.assertFalse(p['tracking_started'])
if __name__=='__main__':unittest.main()
