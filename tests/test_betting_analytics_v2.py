import json,tempfile,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class BettingAnalyticsV2Tests(unittest.TestCase):
 def test_historical_defaults_and_canonical_cells(self):
  c=json.loads((ROOT/'data/site/historical_betting_analytics_v2.json').read_text());self.assertEqual(c['default_selection']['spread'],{'model_id':'standard_spread_4src_equal_v1','checkpoint':'SUN_9AM_ET','threshold':3.0});s=next(x for x in c['independent_checkpoint_performance'] if x['model_id']=='standard_spread_4src_equal_v1' and x['checkpoint']=='SUN_9AM_ET' and x['threshold']==3.0);self.assertLess(s['avg_clv'],1.5);self.assertEqual(s['sample_strength'],'NORMAL')
 def test_known_reversed_events_are_correctly_oriented(self):
  import pandas as pd
  d=pd.read_csv(ROOT/'data/research/historical/comprehensive_market_timing_2021_2025/game_level_spread.csv',low_memory=False)
  ok=d[(d.game_id==401287894)&d.checkpoint.eq('SUN_9AM_ET')&d.model.eq('SP+ + FPI + TR + DRatings')].iloc[0];self.assertEqual(ok.selected_side,'away');self.assertEqual(ok.bet_line,26.5);self.assertEqual(ok.closing_side_spread,31.0);self.assertAlmostEqual(ok.closing_clv_points,-4.5);self.assertLess(ok.edge_points,2)
  clem=d[(d.game_id==401411101)&d.checkpoint.eq('SUN_9AM_ET')&d.model.eq('SP+ + FPI + TR + DRatings')].iloc[0];self.assertEqual(clem.selected_side,'away');self.assertEqual(clem.bet_line,-22.5);self.assertEqual(clem.closing_side_spread,-24.5);self.assertAlmostEqual(clem.closing_clv_points,2.0);self.assertLess(clem.edge_points,2)
 def test_math_atomicity_decay_and_common_sample(self):
  import pandas as pd
  p=ROOT/'scripts/research/historical/analyze_early_window_standard_replacement.py';s=importlib.util.spec_from_file_location('early',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  self.assertEqual(m.spread_clv(3,1),2);self.assertEqual(m.spread_clv(-3,-4),1);self.assertEqual(m.total_clv('OVER',50,52),2);self.assertEqual(m.total_clv('UNDER',50,48),2);self.assertEqual(m.grade_spread('home',-1,1),0);self.assertEqual(m.grade_total('UNDER',49,50),1);self.assertEqual(m.sample_strength(19),'VERY_SMALL_INSUFFICIENT')
  a=pd.read_csv(ROOT/'data/research/historical/comprehensive_market_timing_2021_2025/atomic_spread_market_states.csv');self.assertFalse(a.duplicated(['theodds_event_id','checkpoint','side']).any())
  d=pd.read_csv(ROOT/'data/research/historical/early_window_standard_replacement_2021_2025/spread_edge_decay.csv');self.assertTrue({'origin_side','later_origin_side_line','positive_edge_persisted','reversal'}.issubset(d.columns))
  c=pd.read_csv(ROOT/'data/research/historical/early_window_standard_replacement_2021_2025/spread_common_sample_comparison.csv');self.assertEqual(set(c.cohort),{'FOUR_SOURCE_SELECTED','FIVE_SOURCE_SELECTED','BOTH_QUALIFY','UNION'})
 def test_total_weekday_history_not_fabricated(self):
  c=json.loads((ROOT/'data/site/historical_betting_analytics_v2.json').read_text());weekday={'MON_9AM_ET','MON_3PM_ET','TUE_2PM_ET','WED_2PM_ET','THU_2PM_ET','FRI_2PM_ET'};self.assertFalse(any(x['market_type']=='total' and x['checkpoint'] in weekday for x in c['independent_checkpoint_performance']))
 def test_exact_candidate_formulas_and_shadow_ids(self):
  c=json.loads((ROOT/'data/site/current_game_projection_contract.json').read_text())['model_definitions'];self.assertEqual(c['standard_spread_4src_equal_v1']['weights'],{'SP+':.25,'FPI':.25,'TeamRankings':.25,'DRatings':.25});self.assertEqual(c['standard_total_sp_massey_dratings_v1']['weights'],{'SP+':.4,'Massey Dual':.4,'DRatings Total':.2});self.assertEqual(c['total_sp50_massey50_v1']['weights'],{'SP+':.5,'Massey Dual':.5});self.assertIn('shadow_spread_sp_sagarin_v1',c);self.assertIn('shadow_total_enhanced_spplus_od_v1',c)
 def test_append_only_content_id_behavior(self):
  p=ROOT/'scripts/model_tracking/v2/immutable_tracking.py';s=importlib.util.spec_from_file_location('immutable_tracking',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'x.jsonl';a={'id':m.stable_id('prediction','g1','state1')};b={'id':m.stable_id('prediction','g1','state2')};m.append_unique(out,[a],'id',True);before=out.read_bytes();self.assertEqual(m.append_unique(out,[a],'id',True)['accepted'],0);self.assertEqual(before,out.read_bytes());self.assertEqual(m.append_unique(out,[b],'id',True)['accepted'],1);self.assertEqual(len(out.read_text().splitlines()),2)
 def test_page_and_performance_contract(self):
  page=(ROOT/'betting.html').read_text();self.assertIn('historicalDecayPanel',page);self.assertIn('betting_analytics.js',page);self.assertIn('Beat Close',page);p=json.loads((ROOT/'data/site/model_performance_view.json').read_text());self.assertEqual(p['schema_version'],'model-performance-view-v5')
if __name__=='__main__':unittest.main()
