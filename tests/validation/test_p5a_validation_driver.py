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
