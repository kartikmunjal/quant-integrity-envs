"""Independent P15 plan/source-construction tests; no Docker or submitted exec."""
import importlib.util
from pathlib import Path
from collections import Counter


def driver():
    path=Path(__file__).with_name('p5b_validation.py')
    spec=importlib.util.spec_from_file_location('independent_p5b_driver',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_probe_plan_covers_all_native_stages_and_forgery_every_environment_tier():
    module=driver();rows=module.rows_for('probes','E1',8)
    assert len(rows)==68
    assert Counter(r['kind'] for r in rows)=={'bomb':52,'forgery':16}
    for env in module.ENVS:
        for tier in module.TIERS:
            cell=[r for r in rows if r['environment']==env and r['tier']==tier]
            assert {r.get('stage') for r in cell if r['kind']=='bomb'}==(
                {'solver','primary','replay','poison'} if env=='E2' else {'solver','primary','replay'})
            assert len([r for r in cell if r['kind']=='forgery'])==1


def test_mixed_cohorts_alternate_bombs_and_normal_neighbors_at_c8_c12():
    module=driver()
    for concurrency in (8,12):
        rows=module.rows_for('mixed','E1',concurrency)
        assert len(rows)==4*concurrency
        assert all(row['kind']==('bomb' if i%2==0 else 'normal') for i,row in enumerate(rows))
        for start in range(0,len(rows),concurrency):
            assert Counter(r['kind'] for r in rows[start:start+concurrency])=={
                'bomb':concurrency//2,'normal':concurrency//2}


def test_e2_selection_balances250_per_tier_without_reward_selection(monkeypatch):
    module=driver();old=[];archive={}
    for tier in module.TIERS:
        for i in range(32):
            for seed in range(1003000,1003010):
                index=len(old);path=f'fake/{index}.json.gz';reward=float(index%2)
                row={'policy':f'policy{i:02d}','tier':tier,'seed':seed,'index':index,
                     'archive':{'path':path,'sha256':'fixture'},'reward':reward,'replay_seed':1004000}
                old.append(row);archive[path]={'run':{'value':{'reward':reward,'replay_seed':1004000}}}
    monkeypatch.setattr(module,'historical_rows',lambda path:old)
    monkeypatch.setattr(module,'checked',lambda path,expected:archive[path])
    rows=module.regression_rows('E2')
    assert len(rows)==1000 and Counter(r['tier'] for r in rows)=={tier:250 for tier in module.TIERS}
    assert len({r['policy'] for r in rows})==32
    assert all(r['expected_reward']==archive[r['baseline_archive']['path']]['run']['value']['reward'] for r in rows)


def test_stage_source_has_explicit_solver_marker_and_hash_guard(monkeypatch):
    import ast
    from types import SimpleNamespace
    module=driver()
    monkeypatch.setattr(module,'module',lambda env:SimpleNamespace(public_input=lambda seed,tier:{'public':seed}))
    monkeypatch.setattr(module,'policy_source',lambda *args:"print('{}')\n")
    for stage in ('primary','replay'):
        source=module.stage_bomb_source('E1',stage,1002500,'T1')
        ast.parse(source)
        assert '/work/p5b-solver-marker' in source
        assert module.sha(module.canonical({'public':1002500})) in source
        assert 'os.fork()' in source


def test_e6_regression_extracts_nested_historical_value_without_losing_none_replay(monkeypatch):
    module=driver()
    old={'baseline_index':0,'baseline_path':'fake.json','baseline_sha256':'fixture',
         'policy':'canary_read','reward':0.,'seed':1005000,'tier':'T1'}
    monkeypatch.setattr(module,'load',lambda path:{'environments':{'E6':[dict(old) for _ in range(1000)]}})
    monkeypatch.setattr(module,'checked',lambda path,expected:{0:{'seed':1005000,'tier':'T1',
        'value':{'reward':0.,'replay_seed':None}}})
    rows=module.regression_rows('E6')
    assert len(rows)==1000
    assert all(row['expected_reward']==0. and row['expected_replay_seed'] is None for row in rows)


def test_regression_difference_stops_new_dispatch_without_fabricating_unrun_rows(monkeypatch,tmp_path):
    import asyncio
    module=driver();started=[]
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module,'sources',lambda:{})
    async def native(row):
        started.append(row['seed'])
        if len(started)>1:await asyncio.sleep(.01)
        return {'passed':False,'evidence':{'reward':0.,'replay_seed':None}}
    monkeypatch.setattr(module,'native',native)
    plan={'mode':'regression','environment':'E1','concurrency':8,'sources':{},
          'generator_version_hash':'synthetic-test-fixture','rows':[
              {'kind':'regression','environment':'E1','tier':'T1','seed':1002500+i,'policy':'oracle'}
              for i in range(20)]}
    summary=asyncio.run(module.execute(plan,tmp_path/'fixture.json'))
    assert summary['passed'] is False and summary['planned']==20
    assert 1<=summary['rows']==len(started)<=8
    assert summary['rows']<summary['planned']
    assert sum(shard['rows'] for shard in summary['row_shards'])==len(started)


def test_plan_environment_identity_covers_actual_row_population(monkeypatch):
    module=driver()
    monkeypatch.setattr(module,'sources',lambda:{})
    monkeypatch.setattr(module,'rows_for',lambda *args:[])
    assert module.make_plan('probes','E1',8)['environment']=='E1/E2/E5/E6'
    assert module.make_plan('mixed','E1',12)['environment']=='E1/E2/E5/E6'
    assert module.make_plan('e2-stress','E1',8)['environment']=='E2'
    assert module.make_plan('regression','E5',8)['environment']=='E5'
