from pathlib import Path
import importlib.util
P=Path(__file__).parents[1]/'scripts/model_tracking/v2/immutable_tracking.py';S=importlib.util.spec_from_file_location('immutable_tracking',P);M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
def test_stable_id_is_deterministic(): assert M.stable_id('x',1,None)==M.stable_id('x',1,None)
def test_preview_does_not_write(tmp_path):
 p=tmp_path/'x.jsonl';r=M.append_unique(p,[{'id':'a'}],'id',False);assert r['would_append']==1 and not p.exists()
def test_accept_is_idempotent(tmp_path):
 p=tmp_path/'x.jsonl';rows=[{'id':'a','v':1}];M.append_unique(p,rows,'id',True);r=M.append_unique(p,rows,'id',True);assert r['accepted']==0 and len(p.read_text().splitlines())==1
