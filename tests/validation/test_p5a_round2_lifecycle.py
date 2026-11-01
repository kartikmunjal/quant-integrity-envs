"""Independent P14 immutable-transfer contracts, no Docker or model calls."""
import asyncio
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('environment',['E1','E2','E5','E6'])
def test_capture_is_audited_once_then_exact_path_cap_only_until_restoration(environment):
    from qi_harness import environments
    events=[]
    files={'/work/program.py':b"print('{}')\n",'/work/submission.json':b'{"fixture":true}'}
    class Runtime:
        flagged=False;stopped=False
        async def read(self,path,max_bytes=None):
            assert not self.stopped
            events.append(('read',path,max_bytes))
            return files[path]
        async def stop(self):
            events.append(('stop',));self.stopped=True
    runtime=Runtime();original=runtime.read
    paths=[('/work/program.py',100000)]
    if environment=='E2':paths.append(('/work/submission.json',500000))
    async def scenario():
        try:
            await environments.capture_solver_artifacts(runtime,environment)
            assert runtime.stopped
            assert events==[('read',path,cap) for path,cap in paths]+[('stop',)]
            # Capture immutable snapshots, not references to a subsequently changed map.
            files['/work/program.py']=b'altered after solver removal'
            assert await runtime.read('/work/program.py',max_bytes=100000)==b"print('{}')\n"
            if environment=='E2':
                assert await runtime.read('/work/submission.json',max_bytes=500000)==b'{"fixture":true}'
            for path,cap in [('/work/program.py',99999),('/work/program.py',None),
                             ('/work/../program.py',100000),('/opt/qi/canary',100000)]:
                with pytest.raises(ValueError):await runtime.read(path,max_bytes=cap)
            assert len(events)==len(paths)+1
        finally:
            environments.restore_solver_reads(runtime)
        assert runtime.read==original
    asyncio.run(scenario())


@pytest.mark.parametrize('error_type',[ValueError,UnicodeError])
def test_capture_replays_original_transfer_error_without_new_reads(error_type):
    from qi_harness import environments
    error=error_type('synthetic rejected source');events=[]
    class Runtime:
        stopped=False;flagged=False
        async def read(self,path,max_bytes=None):
            events.append('read');raise error
        async def stop(self):events.append('stop');self.stopped=True
    runtime=Runtime()
    async def scenario():
        try:
            await environments.capture_solver_artifacts(runtime,'E1')
            assert runtime.stopped
            with pytest.raises(error_type) as caught:
                await runtime.read('/work/program.py',max_bytes=100000)
            assert caught.value is error
            assert events==['read','stop']
        finally:environments.restore_solver_reads(runtime)
    asyncio.run(scenario())


def test_capture_infrastructure_failure_remains_failure_and_tears_down_solver():
    from qi_harness import environments
    from qi_runtime.infrastructure import DockerFailure
    events=[]
    class Runtime:
        stopped=False;flagged=False
        async def read(self,*args,**kwargs):
            events.append('read');raise DockerFailure('synthetic transport failure')
        async def stop(self):events.append('stop');self.stopped=True
    runtime=Runtime()
    async def scenario():
        try:
            with pytest.raises(DockerFailure):
                await environments.capture_solver_artifacts(runtime,'E1')
            assert runtime.stopped and events==['read','stop']
        finally:environments.restore_solver_reads(runtime)
    asyncio.run(scenario())


def test_flagged_e2_skips_transfer_as_unchanged_native_finalize_does():
    from qi_harness import environments
    events=[]
    class Runtime:
        stopped=False;flagged=True
        async def read(self,*args,**kwargs):raise AssertionError('flagged E2 must not transfer')
        async def stop(self):events.append('stop');self.stopped=True
    runtime=Runtime()
    async def scenario():
        try:
            await environments.capture_solver_artifacts(runtime,'E2')
            assert runtime.stopped and events==['stop']
            with pytest.raises(ValueError):await runtime.read('/work/program.py',max_bytes=100000)
        finally:environments.restore_solver_reads(runtime)
    asyncio.run(scenario())


def test_absolute_model_deadline_is_installed_before_native_setup_and_restored(monkeypatch):
    import time
    from qi_harness import environments
    from qi_harness.config import Limits
    seen=[]
    async def execute(*args):
        seen.append(environments._DEADLINE.get())
        return {'reward':0.,'harness':{'reason':'max_turns'}}
    monkeypatch.setattr(environments,'execute_native',execute)
    previous=environments._DEADLINE.get()
    before=time.monotonic()
    asyncio.run(environments.run_model_episode('E1',1002500,'T1',object(),Limits(wall_seconds=.1)))
    after=time.monotonic()
    assert before+.1<=seen[0]<=after+.1
    assert environments._DEADLINE.get()==previous


@pytest.mark.parametrize('cancel_count',[1,2])
def test_caller_cancellation_joins_grading_without_cancelling_it(monkeypatch,cancel_count):
    """Repeated caller cancellation must not escape into shared grading."""
    from qi_harness import environments
    from qi_harness.config import Limits
    events=[]
    async def scenario():
        grading_started=asyncio.Event();release_grading=asyncio.Event()
        async def execute(*args):
            events.extend(('solver_removed','grading_started'));grading_started.set()
            try:
                await release_grading.wait()
                events.extend(('primary_complete','replay_complete'))
                return {'reward':1.,'harness':{'reason':'submitted'}}
            except asyncio.CancelledError:
                events.append('grading_cancelled');raise
            finally:events.append('grading_containers_removed')
        monkeypatch.setattr(environments,'execute_native',execute)
        task=asyncio.create_task(environments.run_model_episode(
            'E1',1002500,'T1',object(),Limits(wall_seconds=.01)))
        try:
            await grading_started.wait()
            for _ in range(cancel_count):
                task.cancel()
                await asyncio.sleep(0)
            release_grading.set()
            with pytest.raises(asyncio.CancelledError):await task
        finally:
            release_grading.set()
            await asyncio.gather(task,return_exceptions=True)
    asyncio.run(scenario())
    assert events==['solver_removed','grading_started','primary_complete',
                    'replay_complete','grading_containers_removed']


def test_grading_host_timeout_is_incomplete_infrastructure_not_clean_model_timeout(monkeypatch):
    from qi_harness import environments
    from qi_harness.config import Limits
    from qi_runtime.infrastructure import HostTimeout,classify_exception
    events=[]
    async def execute(*args):
        events.append('solver_removed')
        try:
            await asyncio.sleep(.02)
            raise HostTimeout('synthetic grading transport timeout')
        finally:events.append('grading_cleanup')
    monkeypatch.setattr(environments,'execute_native',execute)
    with pytest.raises(HostTimeout) as caught:
        asyncio.run(environments.run_model_episode(
            'E1',1002500,'T1',object(),Limits(wall_seconds=.001)))
    assert classify_exception(caught.value)=='infrastructure'
    assert events==['solver_removed','grading_cleanup']


@pytest.mark.parametrize('phase',['provision','setup'])
def test_pre_model_deadline_is_infrastructure_and_confirms_cleanup(monkeypatch,tmp_path,phase):
    import time
    from qi_harness import environments
    from qi_runtime.infrastructure import HostTimeout,classify_exception
    events=[];runtimes=[]
    class Task:
        async def setup(self,trace,runtime):
            events.append('setup_started')
            if phase=='setup':await asyncio.sleep(.02)
            events.append('setup_complete')
    task=Task();original_setup=task.setup
    class Directory:
        def __init__(self,*args,**kwargs):pass
        def __enter__(self):return str(tmp_path)
        def __exit__(self,*args):return False
    class Runtime:
        def __init__(self,*args):
            self.created=False;self.stopped=False;runtimes.append(self)
        async def start(self):
            if phase=='provision':await asyncio.sleep(.02)
            self.created=True;events.append('created')
        async def stop(self):
            assert self.created
            self.created=False;self.stopped=True;events.append('removed')
    monkeypatch.setattr(environments,'CheckedRuntime',Runtime)
    monkeypatch.setattr(environments,'bindings',lambda:{'E1':SimpleNamespace(E1Task=Task)})
    monkeypatch.setattr(environments.tempfile,'TemporaryDirectory',Directory)
    async def agent_run(task,runtime):
        await task.setup(SimpleNamespace(),runtime)
        events.append('model_or_grading_work')
    async def scenario():
        token=environments._DEADLINE.set(time.monotonic()+.005)
        active_token=environments._ACTIVE.set({})
        try:
            env=SimpleNamespace(config=SimpleNamespace(environment='E1'))
            agents=SimpleNamespace(agent=SimpleNamespace(run=agent_run))
            with pytest.raises(HostTimeout) as caught:
                await environments.ModelEnv.run(env,task,agents)
            assert classify_exception(caught.value)=='infrastructure'
        finally:
            environments._ACTIVE.reset(active_token);environments._DEADLINE.reset(token)
    asyncio.run(scenario())
    assert len(runtimes)==1 and runtimes[0].stopped and not runtimes[0].created
    assert events==(['created','removed'] if phase=='provision' else ['created','setup_started','removed'])
    assert task.setup==original_setup
