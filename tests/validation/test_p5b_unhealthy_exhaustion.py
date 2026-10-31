"""Independent supplementary P15 contract, outside the running v1 source map.

Positive fresh exhaustion evidence is suspicious even when submitted code
catches fork failure and exits successfully. Failed daemon health cannot turn
that case into either a trusted success or an authorized policy zero.
"""
import asyncio
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize('health',[{'success':False},None,{}, {'success':1}])
def test_positive_delta_with_unhealthy_or_unavailable_daemon_cannot_return_success(monkeypatch,health):
    import qi_runtime as module
    from qi_runtime.infrastructure import InfrastructureError,classify_exception
    from verifiers.v1.runtimes.base import ProgramResult
    identity='3'*64
    before={'container_id':identity,'init_pid':23456,
            'cgroup_path':'/sys/fs/cgroup/docker/'+identity,'pids_max':32,'max_events':0}
    samples=iter([before,dict(before,max_events=1)])
    events=[]
    async def snapshot(runtime):return next(samples)
    async def probe():events.append('health');return health
    async def command(*args):
        events.append('successful_child_after_exhaustion')
        return ProgramResult(0,'{"answer":"untrusted successful output"}','')
    runtime=SimpleNamespace(flagged=False,_process_allowance_violation=False,
                            _run_command=command,commands=[],stopped=False,
                            name='synthetic',info=SimpleNamespace(id=identity))
    async def stop():events.append('outer_cleanup');runtime.stopped=True
    runtime.stop=stop
    monkeypatch.setattr(module,'host_pids_snapshot',snapshot)
    monkeypatch.setattr(module,'daemon_probe',probe)
    async def scenario():
        try:
            with pytest.raises(InfrastructureError) as caught:
                await module.CheckedRuntime.run(runtime,['synthetic'],{})
            assert classify_exception(caught.value)=='infrastructure'
        finally:await runtime.stop()
    asyncio.run(scenario())
    assert events==['successful_child_after_exhaustion','health','outer_cleanup']
    assert runtime.stopped and not runtime.flagged and not runtime._process_allowance_violation
    assert not any(c.get('policy_outcome')=='process_allowance_exhausted' for c in runtime.commands)
