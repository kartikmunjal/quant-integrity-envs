"""Mock-only boundary/lifecycle tests: never start Docker or evaluate a script."""
import asyncio
import json
from types import SimpleNamespace

import pytest


def test_execute_once_delegates_checked_namespace_and_exact_parser(monkeypatch):
    from envs.e3_fdr_adjudication import runtime
    observed = {}
    async def fake_execute(public, source, parser, namespace):
        observed.update(public=public, source=source, namespace=namespace)
        assert parser('{"a":0.4,"b":0.9}') == {'a':.4,'b':.9}
        for bad in ('{}','{"a":true,"b":0}', '{"a":0,"b":2}',
                    '{"a":0,"a":1,"b":0}'):
            assert parser(bad) is None
        return {'answer':None,'flagged':True,'exit_code':0}
    monkeypatch.setattr(runtime, 'execute_program', fake_execute)
    public = {'candidates':[{'id':'a'},{'id':'b'}]}
    result = asyncio.run(runtime.execute_once(public, 'inert source fixture'))
    assert observed == {'public':public,'source':'inert source fixture','namespace':'e3'}
    assert result['flagged']


def test_population_guard_rejects_uncommitted_screen(monkeypatch):
    from envs.e3_fdr_adjudication import v1_taskset as module
    class FakePath:
        def __init__(self, ignored): pass
        def read_bytes(self): return b'{"populations":{}}'
    monkeypatch.setattr(module, 'Path', FakePath)
    monkeypatch.setattr(module.subprocess, 'check_output', lambda args:b'different committed bytes')
    with pytest.raises(ValueError, match='committed'):
        module.populations()


def test_population_guard_rejects_committed_screen_construction_source_drift(monkeypatch):
    from envs.e3_fdr_adjudication import v1_taskset as module
    raw = json.dumps({'populations':{'design':[1000000],'primary':[1001000],'replay':[1002000]},
                      'source_sha256':{'envs/e3_fdr_adjudication/cases.py':'0'*64}}).encode()
    class FakePath:
        def __init__(self, name): self.name=str(name)
        def read_bytes(self):
            return raw if self.name=='results/p3b2_screen.json' else b'changed construction source'
    monkeypatch.setattr(module,'Path',FakePath)
    monkeypatch.setattr(module.subprocess,'check_output',lambda args:raw)
    with pytest.raises(ValueError,match='construction source drift'):
        module.populations()


def test_fresh_seed_guard_and_replay_population(monkeypatch):
    from envs.e3_fdr_adjudication import v1_taskset as module
    monkeypatch.setattr(module, 'populations', lambda:{'design':[1000000], 'primary':[1001000],
                                                     'replay':[1002000,1002001]})
    module.guard(1000000)
    for seed in (1001000,1002000,2000000):
        with pytest.raises(ValueError): module.guard(seed)
    token = module.FRESH_AUTHORIZED.set(True)
    try:
        module.guard(1001000)
        with pytest.raises(ValueError): module.guard(2000000)
    finally:
        module.FRESH_AUTHORIZED.reset(token)
    assert module.replay_seed(1000000,'T1') in (1002000,1002001)
    assert module.replay_seed(1000000,'T1') == module.replay_seed(1000000,'T1')


def fixture_case(prefix):
    ids = [prefix+str(i) for i in range(20)]
    return {'public':{'candidates':[{'id':name} for name in ids]},
            'truth':{name:i%2 for i,name in enumerate(ids)},
            'generator_version_hash':'fixture-generator', 'data_sha256':prefix+'-hash'}


@pytest.mark.parametrize('fault', ['none','flagged_solver','invalid_solver_schema',
                                 'invalid_replay_schema','flagged_replay','nonzero_replay'])
def test_mock_lifecycle_protected_truth_and_hard_gates(monkeypatch, fault):
    from envs.e3_fdr_adjudication import v1_taskset as module
    primary_case, replay_case = fixture_case('primary-'),fixture_case('replay-')
    trace = SimpleNamespace(id='trace-fixture',info={})
    class FakeChecked:
        def __init__(self):
            self.snapshot = {'Image':'immutable-fixture'}
            self.flagged = fault == 'flagged_solver'
            self.commands = []
            self.info = SimpleNamespace(id='solver-fixture')
            self.stopped = False
            self.written = {}
            self.reads = []
        async def write(self, path, data): self.written[path]=data
        async def read(self, path, **kwargs):
            self.reads.append(path)
            if path.endswith('program.py'): return b'inert source, never evaluated'
            return json.dumps({} if fault == 'invalid_solver_schema' else primary_case['truth']).encode()
        async def stop(self): self.stopped=True
    runtime = FakeChecked()
    monkeypatch.setattr(module, 'CheckedRuntime', FakeChecked)
    monkeypatch.setattr(module, 'guard', lambda seed:None)
    monkeypatch.setattr(module, 'make_case', lambda seed,tier:primary_case if seed==1000000 else replay_case)
    monkeypatch.setattr(module, 'replay_seed', lambda seed,tier:1002000)
    calls=[]
    async def fake_execute(public, source):
        calls.append(public)
        replay = len(calls)==2
        return {'answer':None if replay and fault=='invalid_replay_schema' else
                dict((replay_case if replay else primary_case)['truth']),
                'flagged':replay and fault=='flagged_replay',
                'exit_code':1 if replay and fault=='nonzero_replay' else 0,
                'container_id':'replay-fixture' if replay else 'primary-fixture'}
    monkeypatch.setattr(module, 'execute_once', fake_execute)
    task = module.E3Task(module.E3Data(seed=1000000,tier='T1',name='fixture'))
    async def scenario():
        await task.setup(trace,runtime)
        assert json.loads(runtime.written['/work/input.json']) == primary_case['public']
        # The only transfer is agent-visible input, never truth or host case.
        assert set(runtime.written) == {'/work/input.json'}
        await task.finalize(trace,runtime)
        assert runtime.stopped
        return await task.integrity(trace)
    reward = asyncio.run(scenario())
    assert reward == pytest.approx(1 if fault=='none' else 0)
    assert trace.info['e3_evidence']['reward'] == reward
    if fault == 'flagged_solver':
        assert runtime.reads == [] and calls == []
    if fault == 'invalid_solver_schema': assert calls == []


def test_setup_refuses_unchecked_runtime_before_transfer(monkeypatch):
    from envs.e3_fdr_adjudication import v1_taskset as module
    monkeypatch.setattr(module,'guard',lambda seed:None)
    task = module.E3Task(module.E3Data(seed=1000000,tier='T1',name='fixture'))
    with pytest.raises(ValueError, match='checked'):
        asyncio.run(task.setup(SimpleNamespace(id='fixture',info={}), object()))
