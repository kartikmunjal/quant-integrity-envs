"""Pure driver plan/comparison tests, no original policy imports or execution."""
import importlib.util
from pathlib import Path

import pytest


def driver():
    path=Path(__file__).with_name('p5a_docker_validation.py')
    spec=importlib.util.spec_from_file_location('independent_p5a_driver',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plan_has_two_hundred_per_environment_for_every_selected_control(monkeypatch):
    module=driver()
    monkeypatch.setattr(module,'policy_binding',lambda environment:(None,[f'w{i}' for i in range(6)],['c0','c1'],None))
    windows={name:[1000100,1000199] for name in module.ENVIRONMENTS}
    plan=module.build_plan(windows)
    from collections import Counter
    counts=Counter((r['environment'],r['policy'],r['tier']) for r in plan)
    assert len(plan)==4*8*200
    assert all(count==50 for count in counts.values())
    assert {r['policy'] for r in plan}=={'oracle','w0','w1','w2','w3','w4','c0','c1'}


def test_semantic_comparison_excludes_only_operational_metadata():
    module=driver()
    first={'container_id':'one','commands':[{'trace_sha256':'one','exit_code':0}],
           'answer':{'value':1.,'container_id':'semantic answer field'},'flagged':False,
           'exit_code':0,'source_sha256':'source','input_sha256':'input','image':'image'}
    second={**first,'container_id':'two','commands':[{'trace_sha256':'two','exit_code':0}]}
    module.assert_same(first,second)
    for field,value in [('source_sha256','wrong'),('input_sha256','wrong'),('exit_code',1),('flagged',True)]:
        with pytest.raises(AssertionError): module.assert_same(first,{**second,field:value})
    with pytest.raises(AssertionError):
        module.assert_same(first,{**second,'answer':{'value':1.,'container_id':'altered answer'}})


def test_float_comparison_uses_absolute_twelve_decimal_tolerance():
    module=driver()
    module.assert_same({'answer':{'x':.5}},{'answer':{'x':.5+5e-13}})
    with pytest.raises(AssertionError): module.assert_same({'answer':{'x':.5}},{'answer':{'x':.5+5e-11}})


def test_mismatch_result_preserves_both_full_records_instead_of_raising():
    module=driver()
    baseline={'reward':1.,'primary':{'answer':{'x':1.},'container_id':'baseline'},'replay':None}
    model={'reward':.5,'primary':{'answer':{'x':2.},'container_id':'model'},'replay':None}
    result=module.compare_evidence({'environment':'E1','policy':'fixture'},'fixture source',baseline,model)
    assert not result['comparison_pass'] and result['comparison_errors']
    assert result['baseline']==baseline and result['model']==model
    assert result['planned_source']=='fixture source'


def test_compact_proofs_keep_metrics_and_hashes_with_full_raw_retained(tmp_path):
    module=driver()
    value={'index':0,'environment':'E1','policy':'fixture','passed':False,
           'result':{'complete':True,'infrastructure_ok':True,'retried':False,'attempts':[],
                     'value':{'comparison_pass':False,'comparison_errors':['fixture mismatch'],
                              'planned_source':'fixture source','baseline':{'reward':1.,'primary':{'answer':{'x':1.}}},
                              'model':{'reward':0.,'primary':{'answer':{'x':2.}},'harness':{'turns':3}}}}}
    archive=module.ValidationArchive(tmp_path/'raw',tmp_path/'proof',tmp_path/'sources')
    compact=archive.add(value)
    assert compact['passed'] is False
    assert compact['baseline']['reward']==1 and compact['model']['reward']==0
    assert compact['baseline']['primary']['answer_sha256']!=compact['model']['primary']['answer_sha256']
    import gzip,json,hashlib
    packed=Path(compact['raw']['path']).read_bytes()
    assert hashlib.sha256(packed).hexdigest()==compact['raw']['sha256']
    assert json.loads(gzip.decompress(packed))==value
    shards=archive.finish()
    assert all(part['bytes']<=512*1024 for part in shards)


def test_partial_baseline_is_retained_when_model_lifecycle_raises(monkeypatch):
    import asyncio
    from contextlib import nullcontext
    import qi_harness.environments as environments
    module=driver()
    baseline={'reward':1.,'primary':{'answer':{'x':1.}},'replay':None}
    class Task:
        async def run_policy(self,*args): return baseline
    monkeypatch.setattr(module,'policy_binding',lambda environment:(Task(),[],[],lambda *args:'fixture source'))
    monkeypatch.setattr(environments,'validation_context',lambda environment:nullcontext())
    async def fail(*args,**kwargs): raise RuntimeError('fixture model lifecycle failure')
    monkeypatch.setattr(environments,'run_model_episode',fail)
    retained=[]
    with pytest.raises(RuntimeError):
        asyncio.run(module.equivalence({'environment':'E1','seed':1002500,'tier':'T1','policy':'fixture'},retain=retained.append))
    assert retained[-1]['baseline']==baseline and retained[-1]['model'] is None
    assert retained[-1]['lifecycle_error']=='RuntimeError'
