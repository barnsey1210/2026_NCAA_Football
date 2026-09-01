import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class HistoricalExplorerTest(unittest.TestCase):
 def setUp(self):
  self.payload=json.loads((ROOT/'data/site/historical_betting_explorer_v1.json').read_text())
  self.cols=self.payload['columns'];self.dicts=self.payload['dictionaries']
 def decoded(self):
  for row in self.payload['records']:
   out=dict(zip(self.cols,row))
   for key,values in self.dicts.items():
    if out[key] is not None:out[key]=values[out[key]]
   yield out
 def test_contract_grain_and_default(self):
  self.assertEqual(self.payload['default'],{'model_id':'standard_spread_4src_equal_v1','threshold':3,'row_dimension':'week','column_dimension':'checkpoint','metric':'roi','mode':'checkpoint'})
  rows=list(self.decoded());keys={(r['game_id'],r['model_id'],r['checkpoint']) for r in rows}
  self.assertEqual(len(keys),len(rows));self.assertLess((ROOT/'data/site/historical_betting_explorer_v1.json').stat().st_size,16*1024*1024)
 def test_corrected_reference_and_week_checkpoint_cube(self):
  rows=[r for r in self.decoded() if r['model_id']=='standard_spread_4src_equal_v1' and abs(r['edge'])>=3]
  ref=[r for r in rows if r['checkpoint']=='SUN_9AM_ET']
  self.assertEqual(len(ref),324);self.assertEqual((sum(r['result']>0 for r in ref),sum(r['result']<0 for r in ref),sum(r['result']==0 for r in ref)),(193,130,1))
  checkpoints={r['checkpoint'] for r in rows}
  self.assertEqual(checkpoints,set(self.payload['checkpoint_order']));self.assertEqual(self.payload['week_domain'],list(range(17)))

if __name__=='__main__':unittest.main()
