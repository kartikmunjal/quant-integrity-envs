"""Prospective whole-native-lifecycle deadline and cleanup contracts, no Docker."""
import asyncio
from types import SimpleNamespace

import pytest


def test_outer_wall_deadline_cancels_native_workflow_and_waits_for_cleanup(monkeypatch):
    from qi_harness import environments
    from qi_harness.config import Limits
    events=[]
    async def fake_execute(environment,seed,tier,client,limits):
        events.append('setup')
        try:
            await asyncio.sleep(.2)
            events.append('finalize')
            return {'reward':1.,'harness':{'reason':'submitted'}}
        finally:events.append('cleanup')
    monkeypatch.setattr(environments,'execute_native',fake_execute)
    result=asyncio.run(environments.run_model_episode('E1',1002500,'T1',object(),Limits(wall_seconds=.01)))
    assert events==['setup','cleanup']
    assert result['reward']==0 and result['harness']['reason']=='wall_timeout'
    assert result['native_graded'] is False
    assert result.get('primary') is None and result.get('replay') is None
    assert result['harness']['terminal']


def test_outer_wrapper_preserves_successful_native_result(monkeypatch):
    from qi_harness import environments
    from qi_harness.config import Limits
    expected={'reward':.25,'primary':{'answer':{'value':2}},'replay':None,
              'harness':{'reason':'submitted','submitted':True}}
    async def fake_execute(*args):return expected
    monkeypatch.setattr(environments,'execute_native',fake_execute)
    result=asyncio.run(environments.run_model_episode('E1',1002500,'T1',object(),Limits()))
    assert result['reward']==expected['reward'] and result['primary']==expected['primary']
    assert result['harness']['reason']=='submitted'


def test_timeout_cleanup_failure_is_not_hidden_by_a_defined_zero_result(monkeypatch):
    from qi_harness import environments
    from qi_harness.config import Limits
    from qi_runtime.infrastructure import DockerFailure
    async def fake_execute(*args):
        try:await asyncio.sleep(.2)
        finally:raise DockerFailure('fixture cleanup did not complete')
    monkeypatch.setattr(environments,'execute_native',fake_execute)
    with pytest.raises(DockerFailure):
        asyncio.run(environments.run_model_episode('E1',1002500,'T1',object(),Limits(wall_seconds=.01)))


def test_non_submitting_model_marks_native_runtime_flag_before_scoring():
    from qi_harness.client import MockClient,Reply
    from qi_harness.config import Limits
    from qi_harness.harness import run_loop
    class Tools:
        submitted=False;terminal=False;reason='';initial_messages=[];schemas=[]
        runtime=SimpleNamespace(flagged=False)
    tools=Tools()
    result=asyncio.run(run_loop(MockClient([Reply(content='no submission')]),tools,Limits(max_turns=1)))
    assert result['reward']==0 and result['reason']=='max_turns'
    assert tools.runtime.flagged and not result['submitted']


def test_tool_loop_timeout_aborts_native_finalize_with_retained_reason(monkeypatch):
    from qi_harness import environments
    from qi_harness.client import MockClient
    class FakeRuntime:
        def __init__(self):self.flagged=False;self.stopped=False
        async def stop(self):self.stopped=True
    runtime=FakeRuntime()
    monkeypatch.setattr(environments,'CheckedRuntime',FakeRuntime)
    monkeypatch.setattr(environments,'messages_for',lambda *args:[])
    async def fake_loop(*args):
        runtime.flagged=True
        return {'reason':'wall_timeout','submitted':False,'reward':0.,'turns':1,
                'input_tokens':0,'output_tokens':0,'total_tokens':0}
    monkeypatch.setattr(environments,'run_loop',fake_loop)
    trace=SimpleNamespace(info={'e1_lifecycle':['setup']})
    harness=environments.ModelHarness(environments.ModelHarnessConfig(environment='E1'))
    token=environments._CLIENT.set(MockClient([]))
    try:
        with pytest.raises(Exception) as error:
            asyncio.run(harness.launch(None,trace,runtime,None,None,None,SimpleNamespace(prompt='fixture')))
    finally:environments._CLIENT.reset(token)
    assert getattr(error.value,'reason',None)=='wall_timeout'
    assert runtime.flagged and runtime.stopped
    assert trace.info['p5a_harness']['reason']=='wall_timeout'
