"""Independent deadline contracts; P14 excludes native grading from the clock."""
import asyncio
from types import SimpleNamespace

import pytest


def test_model_wall_deadline_never_cancels_native_grading(monkeypatch):
    from qi_harness import environments
    from qi_harness.config import Limits
    events=[]
    async def fake_execute(environment,seed,tier,client,limits):
        events.extend(('setup','model_deadline','solver_removed','finalize'))
        try:
            await asyncio.sleep(.03)
            events.extend(('primary_finished','replay_finished'))
            return {'reward':0.,'native_graded':True,'harness':{'reason':'wall_timeout'}}
        except asyncio.CancelledError:
            events.append('grading_cancelled')
            raise
        finally:events.append('grading_cleanup')
    monkeypatch.setattr(environments,'execute_native',fake_execute)
    result=asyncio.run(environments.run_model_episode('E1',1002500,'T1',object(),Limits(wall_seconds=.01)))
    assert events==['setup','model_deadline','solver_removed','finalize',
                    'primary_finished','replay_finished','grading_cleanup']
    assert result['reward']==0 and result['harness']['reason']=='wall_timeout'
    assert result['native_graded'] is True


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


def test_tool_loop_timeout_removes_solver_then_native_finalize_uses_captured_read(monkeypatch):
    from qi_harness import environments
    from qi_harness.client import MockClient
    events=[]
    class FakeRuntime:
        def __init__(self):
            self.flagged=False;self.stopped=False;self.commands=[]
            self.info=SimpleNamespace(id='fixture-container');self.snapshot={'Image':'fixture-image'}
        async def read(self,path,max_bytes=None):
            assert not self.stopped
            assert path=='/work/program.py' and max_bytes==100000
            events.append('audited_read');self.commands.append({'fixture_audited':True})
            return b"print('{}')\n"
        async def stop(self):
            if not self.stopped:events.append('solver_removed')
            self.stopped=True
    runtime=FakeRuntime()
    monkeypatch.setattr(environments,'CheckedRuntime',FakeRuntime)
    monkeypatch.setattr(environments,'messages_for',lambda *args:[])
    async def fake_loop(*args):
        events.append('model_deadline')
        runtime.flagged=True
        return {'reason':'wall_timeout','submitted':False,'reward':0.,'turns':1,
                'input_tokens':0,'output_tokens':0,'total_tokens':0}
    monkeypatch.setattr(environments,'run_loop',fake_loop)
    trace=SimpleNamespace(id='fixture-trace',info={'e1_lifecycle':['setup']})
    harness=environments.ModelHarness(environments.ModelHarnessConfig(environment='E1'))
    token=environments._CLIENT.set(MockClient([]))
    async def scenario():
        await harness.launch(None,trace,runtime,None,None,None,SimpleNamespace(prompt='fixture'))
        assert runtime.stopped
        from envs.e1_pit_backtest.v1_taskset import E1Task,E1Data
        native=E1Task(E1Data(seed=1002500,tier='T1'))
        native._solver=runtime;native._trace_id=trace.id;native._source=None
        events.append('native_finalize')
        await native.finalize(trace,runtime)
        assert native._solver is runtime and native._source=="print('{}')\n"
        assert native._solver_record['flagged']
        assert native._solver_record['commands']==[{'fixture_audited':True}]
    try:
        asyncio.run(scenario())
    finally:environments._CLIENT.reset(token)
    assert runtime.flagged and runtime.stopped
    assert trace.info['p5a_harness']['reason']=='wall_timeout'
    assert events==['model_deadline','audited_read','solver_removed','native_finalize']


def test_cancelled_provision_finishes_before_removal_so_late_creation_cannot_leak(monkeypatch,tmp_path):
    """A fake uncancellable daemon creation models the Docker-client boundary."""
    from qi_harness import environments
    events=[]
    class Task: pass
    class TemporaryDirectory:
        def __init__(self,*args,**kwargs): pass
        def __enter__(self):return str(tmp_path)
        def __exit__(self,*args):return False
    started=None
    class Runtime:
        stopped=False
        def __init__(self,*args): self.created=False
        async def start(self):
            async def daemon_create():
                await asyncio.sleep(.02)
                self.created=True;events.append('created')
            job=asyncio.create_task(daemon_create())
            started.set()
            await asyncio.shield(job)
        async def stop(self):
            events.append('removed' if self.created else 'removed_before_creation')
            self.stopped=True
    monkeypatch.setattr(environments,'CheckedRuntime',Runtime)
    monkeypatch.setattr(environments,'bindings',lambda:{'E1':SimpleNamespace(E1Task=Task)})
    monkeypatch.setattr(environments.tempfile,'TemporaryDirectory',TemporaryDirectory)
    async def agent_run(*args,**kwargs):events.append('agent')
    async def scenario():
        nonlocal started
        started=asyncio.Event()
        env=SimpleNamespace(config=SimpleNamespace(environment='E1'))
        agents=SimpleNamespace(agent=SimpleNamespace(run=agent_run))
        task=asyncio.create_task(environments.ModelEnv.run(env,Task(),agents))
        await started.wait();task.cancel()
        with pytest.raises(asyncio.CancelledError):await task
        await asyncio.sleep(.03)
    asyncio.run(scenario())
    assert events==['created','removed']
