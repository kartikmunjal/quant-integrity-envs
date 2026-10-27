"""Runner evidence survives source and post-rollout checker failures."""
import json
import asyncio
import pytest
from qi_runtime import experiments as e

def test_source_exception_is_retained_and_other_rollouts_finish(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);(tmp_path/'logs').mkdir();(tmp_path/'results').mkdir()
    class Policies:
        def source_for(self,name,*args):
            if name=='bad':raise ValueError('source construction failed')
            return 'pass'
    class Task:
        async def run_policy(self,*args):return {'reward':1.,'lifecycle':['setup','solver','finalize','score']}
    monkeypatch.setattr(e,'binding',lambda env:(Task(),Policies(),{'good':None,'bad':None},[],[]))
    monkeypatch.setattr(e,'plan_for',lambda *args:[dict(seed=1001000,tier='T1',policy=n) for n in ('bad','good')])
    result=asyncio.run(e.run_batch('stress','E1',12,count=2,tag='test'))
    rows=[row for p in result['shards'] for row in json.loads((tmp_path/p).read_text())]
    assert len(rows)==2 and result['complete']==1 and not result['passed']
    failure=next(r for r in rows if r['policy']=='bad')
    assert failure['attempts'][0]['exceptions'][0]['types']==['ValueError']
    assert all((tmp_path/p).exists() for p in failure['attempts'][0]['exceptions'][0]['full_traceback_parts'])

def test_plans_preserve_historical_population_and_fit_artifact_limit():
    for env,n in [('E1',6400),('E5',7000),('E6',7000)]:
        rows=e.plan_for('determinism',env,5000)
        assert len(rows)==n
        assert len(json.dumps({'rows':rows},separators=(',',':')).encode())<1048576*2
    rows=e.plan_for('gate','E6',5000)
    assert len(rows)==8400
    assert len(json.dumps({'rows':rows},separators=(',',':')).encode())<1048576

def test_checker_failure_retains_completed_attempt_and_other_rows(tmp_path,monkeypatch):
    from envs.e6_data_traps import cases,checker
    from qi_runtime import gate_summary
    monkeypatch.setattr(e,'frozen_sources',lambda:{'test':'fixed'})
    monkeypatch.chdir(tmp_path);(tmp_path/'logs').mkdir();(tmp_path/'results').mkdir()
    class Policies:
        def source_for(self,*args):return 'pass'
    class Task:
        async def run_policy(self,*args):return {'reward':.5,'replay_seed':1006000,'primary':{},'replay':{}}
    monkeypatch.setattr(e,'binding',lambda env:(Task(),Policies(),{'random':None},[],[]))
    monkeypatch.setattr(e,'plan_for',lambda *args:[dict(seed=1005000,tier='T1',policy='random')])
    monkeypatch.setattr(cases,'make_case',lambda *a:{'truth':{},'diagnostics':{}})
    def fail(*args):raise RuntimeError('checker diagnostic failed')
    monkeypatch.setattr(checker,'score_pair',fail)
    monkeypatch.setattr(gate_summary,'summarize_gate',lambda *a:{'reward_gate_passed':False})
    result=asyncio.run(e.run_batch('gate','E6',12,tag='test-checker'))
    row=json.loads((tmp_path/result['shards'][0]).read_text())[0]
    assert not result['passed'] and row['value']['reward']==.5
    assert len(row['attempts'])==1 and row['terminal_kind']=='orchestrator'
    assert row['orchestration_exception']['types']==['RuntimeError']

def test_compaction_failure_preserves_attempt_resources(tmp_path,monkeypatch):
    from qi_runtime.infrastructure import note_resource
    monkeypatch.chdir(tmp_path);(tmp_path/'logs').mkdir();(tmp_path/'results').mkdir()
    class Policies:
        def source_for(self,*args):return 'pass'
    class Task:
        async def run_policy(self,*args):
            note_resource('solver','container-id')
            return {'reward':1.,'primary':{'answer':{'anomalies':[]}}}
    monkeypatch.setattr(e,'binding',lambda env:(Task(),Policies(),{'random':None},[],[]))
    monkeypatch.setattr(e,'plan_for',lambda *args:[dict(seed=1001000,tier='T1',policy='random')])
    result=asyncio.run(e.run_batch('stress','E1',12,tag='test-compact'))
    row=json.loads((tmp_path/result['shards'][0]).read_text())[0]
    assert row['attempts'][0]['resources'][0]['container_id']=='container-id'
    assert not row['complete'] and row['terminal_kind']=='orchestrator'
    assert row['orchestration_exception']['types']==['KeyError']

@pytest.mark.parametrize('mutate', [False, True])
def test_end_of_gate_source_check_retains_rows_and_blocks_mutation(tmp_path, monkeypatch, mutate):
    """An end-of-run source edit must fail even when every other check passes."""
    from envs.e6_data_traps import cases, checker
    from qi_runtime import gate_summary
    monkeypatch.chdir(tmp_path)
    (tmp_path/'logs').mkdir();(tmp_path/'results').mkdir()
    state={'hash':'before'}
    monkeypatch.setattr(e,'frozen_sources',lambda:dict(state))
    class Policies:
        def source_for(self,*args):return 'pass'
    class Task:
        async def run_policy(self,*args):
            if mutate:state['hash']='after'
            return {'reward':.5,'replay_seed':1006000,'primary':{},'replay':{}}
    monkeypatch.setattr(e,'binding',lambda env:(Task(),Policies(),{'random':None},[],[]))
    monkeypatch.setattr(e,'plan_for',lambda *args:[dict(seed=1005000+i,tier='T1',policy='random') for i in range(50)])
    monkeypatch.setattr(cases,'make_case',lambda *a:{'truth':{},'diagnostics':{}})
    monkeypatch.setattr(checker,'score_pair',lambda *a:.5)
    monkeypatch.setattr(gate_summary,'summarize_gate',lambda *a:{'reward_gate_passed':True})
    result=asyncio.run(e.run_batch('gate','E6',12,tag='end-source-check'))
    assert result['complete']==result['planned']==result['sample_count']==50
    assert result['source_hashes_unchanged'] is (not mutate)
    assert result['passed'] is (not mutate)
    rows=[row for p in result['shards'] for row in json.loads((tmp_path/p).read_text())]
    assert len(rows)==50 and all(row['complete'] and len(row['attempts'])==1 for row in rows)

def test_interruption_retains_inflight_attempt_and_marks_unstarted(tmp_path,monkeypatch):
    from qi_runtime.infrastructure import note_resource
    monkeypatch.chdir(tmp_path);(tmp_path/'logs').mkdir();(tmp_path/'results').mkdir()
    started=asyncio.Event()
    class Policies:
        def source_for(self,*args):return 'pass'
    class Task:
        async def run_policy(self,*args):
            note_resource('active','active-id');started.set();await asyncio.sleep(100)
    monkeypatch.setattr(e,'binding',lambda env:(Task(),Policies(),{'random':None},[],[]))
    monkeypatch.setattr(e,'plan_for',lambda *args:[dict(seed=1001000+i,tier='T1',policy='random') for i in range(3)])
    async def run():
        batch=asyncio.create_task(e.run_batch('stress','E1',1,tag='test-interrupt'))
        await started.wait();batch.cancel();return await batch
    result=asyncio.run(run())
    rows=[row for p in result['shards'] for row in json.loads((tmp_path/p).read_text())]
    assert result['interrupted'] and not result['passed'] and len(rows)==3
    active=next(r for r in rows if r['index']==0)
    assert active['attempts'][0]['resources'][0]['container_id']=='active-id'
    assert active['attempts'][0]['exceptions'][0]['types']==['CancelledError']
    assert all(not r['started'] for r in rows if r['index']!=0)
