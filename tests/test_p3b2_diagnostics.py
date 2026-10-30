"""Mock design-diagnostic retention and bounded evidence storage."""
import gzip
import json
from types import SimpleNamespace
from scripts import p3b2_diagnostics as module


def test_bad_case_gaps_are_retained_without_filtering(monkeypatch):
    def construct(seed,tier):
        return {'seed':seed,'data_sha256':'fixture',
                'public':{'candidates':[{'id':str(seed)+'-a'},{'id':str(seed)+'-b'}]},
                'truth':{str(seed)+'-a':0,str(seed)+'-b':1}}
    def vector(public,mode):
        return {row['id']:.5 for row in public['candidates']}
    fake=SimpleNamespace(WRONG_POLICIES=('wrong',),probability_vectors=vector)
    checker=SimpleNamespace(execution=lambda q,y:module.execution_reward(q,y))
    monkeypatch.setattr(module,'load_independent',lambda name:fake if name.endswith('policies') else checker)
    monkeypatch.setattr(module,'make_case',construct)
    monkeypatch.setattr(module,'replay_seed',lambda seed,tier:seed+1000)
    result=module.diagnostics([1000000,1000001])
    assert len(result['rows'])==8
    assert not result['all_case_gaps_pass']
    assert all(row['honest_minus_wrong_gaps']=={'wrong':0.} for row in result['rows'])
    assert result['agreement']==1


def test_shards_preserve_all_diagnostic_rows(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path/'results').mkdir()
    rows=[{'index':i,'text':'a'*100} for i in range(61)]
    shards=module.store_rows(rows)
    restored=[]
    for shard in shards:
        restored.extend(json.loads(line) for line in gzip.decompress((tmp_path/shard['path']).read_bytes()).splitlines())
        assert shard['bytes']<1024*1024
    assert restored==rows
