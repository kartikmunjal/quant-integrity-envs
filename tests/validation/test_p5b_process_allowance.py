"""Independent prospective P15 evidence/classification contracts; no Docker."""
import asyncio
from types import SimpleNamespace

import pytest


CONTAINER = '1' * 64


def snapshot(events=2, **changes):
    value = {'container_id': CONTAINER, 'init_pid': 12345,
             'cgroup_path': '/sys/fs/cgroup/system.slice/docker-' + CONTAINER + '.scope',
             'pids_max': 32, 'max_events': events}
    return dict(value, **changes)


def test_classifier_requires_fresh_positive_host_counter_and_healthy_daemon():
    from qi_runtime.process_allowance import process_allowance_exhausted
    assert process_allowance_exhausted(snapshot(), snapshot(3), {'success': True}) is True
    assert process_allowance_exhausted(snapshot(0), snapshot(9), {'success': True}) is True


@pytest.mark.parametrize('before,after,health', [
    (None, snapshot(3), {'success': True}),
    (snapshot(), None, {'success': True}),
    (snapshot(), snapshot(), {'success': True}),
    (snapshot(), snapshot(1), {'success': True}),
    (snapshot(), snapshot(3), None),
    (snapshot(), snapshot(3), {}),
    (snapshot(), snapshot(3), {'success': False}),
    (snapshot(), snapshot(3), {'success': 1}),
    (snapshot(), snapshot(3, container_id='2'*64), {'success': True}),
    (snapshot(), snapshot(3, init_pid=12346), {'success': True}),
    (snapshot(), snapshot(3, cgroup_path='/work/pids.events'), {'success': True}),
    (snapshot(), snapshot(3, pids_max=64), {'success': True}),
    (snapshot(pids_max=64), snapshot(3, pids_max=64), {'success': True}),
    (snapshot(max_events='2'), snapshot(3), {'success': True}),
    (snapshot(max_events=True), snapshot(3), {'success': True}),
    (snapshot(), snapshot(max_events='3'), {'success': True}),
    (snapshot(), snapshot(max_events=True), {'success': True}),
    (snapshot(max_events=-1), snapshot(3), {'success': True}),
    (snapshot(init_pid=0), snapshot(3, init_pid=0), {'success': True}),
])
def test_missing_stale_unreadable_or_unhealthy_evidence_never_authorizes_policy_zero(before,after,health):
    from qi_runtime.process_allowance import process_allowance_exhausted
    assert process_allowance_exhausted(before, after, health) is False


@pytest.mark.parametrize('failure_kind', ['missing_status', 'host_timeout', 'successful_exit'])
def test_positive_evidence_is_policy_hard_zero_cleanup_not_retry(monkeypatch,tmp_path,failure_kind):
    import qi_runtime as runtime_module
    from qi_runtime.infrastructure import DockerFailure,HostTimeout,RetryBudget,run_with_retry
    from verifiers.v1.runtimes.base import ProgramResult
    samples = iter([snapshot(), snapshot(3)])
    async def sample(runtime):return next(samples)
    async def health():return {'success': True}
    monkeypatch.setattr(runtime_module, 'host_pids_snapshot', sample)
    monkeypatch.setattr(runtime_module, 'daemon_probe', health)
    events=[]
    async def command(argv,env):
        events.append('command')
        if failure_kind=='missing_status':raise DockerFailure('synthetic missing protected status')
        if failure_kind=='host_timeout':raise HostTimeout('synthetic command client timeout')
        return ProgramResult(0,'{"signal_mean":0,"backtest_return":0}','')
    runtime=SimpleNamespace(flagged=False,commands=[],_process_allowance_violation=False,
                            _run_command=command,name='fixture-runtime',info=SimpleNamespace(id=CONTAINER),
                            _container='fixture-runtime',_stopped=False,stopped=False)
    async def stop():
        events.append('removed');runtime._stopped=True;runtime.stopped=True
    runtime.stop=stop
    async def scenario():
        ledger=RetryBudget(1000)
        async def operation():
            result=await runtime_module.CheckedRuntime.run(runtime,['synthetic'],{})
            assert result.exit_code!=0
            assert runtime.flagged and runtime._process_allowance_violation and runtime.stopped
            assert runtime.commands and runtime.commands[-1].get('policy_outcome')
            return {'reward':0.,'flagged':runtime.flagged}
        result=await run_with_retry(operation,ledger=ledger,journal_root=tmp_path/'journal')
        assert result['complete'] and result['infrastructure_ok'] and not result['retried']
        assert result['value']['reward']==0. and ledger.used==0
        assert all(a['cleanup_complete'] for a in result['attempts'])
    asyncio.run(scenario())
    assert events==['command','removed']


@pytest.mark.parametrize('failure_type',['daemon_stall','transfer_timeout','missing_evidence','stale_evidence'])
def test_genuine_infrastructure_without_valid_proof_remains_original_failure(monkeypatch,failure_type):
    import qi_runtime as runtime_module
    from qi_runtime.infrastructure import DockerFailure,HostTimeout,classify_exception
    from verifiers.v1.runtimes.base import ProgramResult
    if failure_type=='missing_evidence':samples=iter([None,None])
    elif failure_type=='stale_evidence':samples=iter([snapshot(9),snapshot(9)])
    else:samples=iter([snapshot(),snapshot(3) if failure_type=='daemon_stall' else snapshot()])
    async def sample(runtime):return next(samples)
    async def health():return {'success':failure_type!='daemon_stall'}
    monkeypatch.setattr(runtime_module,'host_pids_snapshot',sample)
    monkeypatch.setattr(runtime_module,'daemon_probe',health)
    original=HostTimeout('synthetic transfer timeout') if failure_type=='transfer_timeout' else DockerFailure('synthetic infrastructure')
    async def command(*args):raise original
    runtime=SimpleNamespace(flagged=False,commands=[],_process_allowance_violation=False,
                            _run_command=command,name='fixture',info=SimpleNamespace(id=CONTAINER),stopped=False)
    async def forbidden_stop():raise AssertionError('no policy cleanup without proof')
    runtime.stop=forbidden_stop
    with pytest.raises(type(original)) as caught:
        asyncio.run(runtime_module.CheckedRuntime.run(runtime,['synthetic'],{}))
    assert caught.value is original and classify_exception(caught.value)=='infrastructure'
    assert not runtime.flagged and not runtime._process_allowance_violation


def test_no_event_delta_preserves_normal_command_record_exactly(monkeypatch):
    import qi_runtime as runtime_module
    from verifiers.v1.runtimes.base import ProgramResult
    async def sample(runtime):return snapshot(7)
    monkeypatch.setattr(runtime_module,'host_pids_snapshot',sample)
    expected=ProgramResult(0,'public exact output','public exact trace')
    async def command(*args):return expected
    runtime=SimpleNamespace(flagged=False,commands=[],_process_allowance_violation=False,_run_command=command)
    result=asyncio.run(runtime_module.CheckedRuntime.run(runtime,['synthetic'],{}))
    assert result is expected and runtime.commands==[] and not runtime.flagged


def test_exhaustion_only_read_fast_failure_avoids_new_container_process(monkeypatch):
    import qi_runtime as runtime_module
    calls=[]
    async def forbidden_run(*args):calls.append(args);raise AssertionError('dead container execution')
    runtime=SimpleNamespace(_process_allowance_violation=True,flagged=True,run=forbidden_run)
    with pytest.raises(ValueError):
        asyncio.run(runtime_module.CheckedRuntime.read(runtime,'/work/program.py',max_bytes=100000))
    assert runtime.flagged and calls==[]


def host_fixture(monkeypatch, *, inspection=None, files=None):
    """All host paths are intercepted; no real proc/sysfs file is opened."""
    import json
    import qi_runtime.process_allowance as module
    entry={'Id':CONTAINER,'State':{'Pid':12345,'Running':True},'HostConfig':{'PidsLimit':32}}
    group='/sys/fs/cgroup/system.slice/docker-'+CONTAINER+'.scope'
    contents={'/proc/12345/cgroup':'0::/system.slice/docker-'+CONTAINER+'.scope\n',
              group+'/pids.max':'32\n',group+'/pids.events':'max 7\n'}
    if files:contents.update(files)
    reads=[];commands=[]
    async def cli(*args,**kwargs):
        commands.append(args)
        assert args==('inspect','fixture-runtime')
        return 0,json.dumps([entry] if inspection is None else inspection),''
    def read(path):
        path=str(path);reads.append(path)
        assert path in contents,'unexpected host-file access'
        value=contents[path]
        if isinstance(value,BaseException):raise value
        return value
    monkeypatch.setattr(module,'cli',cli)
    monkeypatch.setattr(module,'_read_host_text',read)
    runtime=SimpleNamespace(name='fixture-runtime',info=SimpleNamespace(id=CONTAINER))
    return module,runtime,reads,commands,group


def test_host_snapshot_uses_inspect_and_kernel_files_never_container_exec(monkeypatch):
    module,runtime,reads,commands,group=host_fixture(monkeypatch)
    result=asyncio.run(module.host_pids_snapshot(runtime))
    assert result==snapshot(7)
    assert reads==['/proc/12345/cgroup',group+'/pids.max',group+'/pids.events']
    assert commands==[('inspect','fixture-runtime')]
    assert all('/work' not in path for path in reads)


@pytest.mark.parametrize('kind',[
    'unreadable','wrong_container','wrong_membership','agent_file','traversal','cgroup_v1',
    'wrong_limit','duplicate_counter','missing_counter','nonnumeric_counter','negative_counter',
    'stopped_container','missing_pid','malformed_inspect',
])
def test_host_snapshot_rejects_unavailable_forged_or_unsupported_evidence(monkeypatch,kind):
    group='/sys/fs/cgroup/system.slice/docker-'+CONTAINER+'.scope'
    files={}
    inspection=None
    if kind=='unreadable':files[group+'/pids.events']=PermissionError('synthetic unreadable kernel file')
    if kind=='wrong_membership':files['/proc/12345/cgroup']='0::/system.slice/docker-'+('2'*64)+'.scope\n'
    if kind=='agent_file':files['/proc/12345/cgroup']='0::/work/pids.events\n'
    if kind=='traversal':files['/proc/12345/cgroup']='0::/system.slice/docker-'+CONTAINER+'.scope/../../work\n'
    if kind=='cgroup_v1':files['/proc/12345/cgroup']='1:pids:/docker/'+CONTAINER+'\n'
    if kind=='wrong_limit':files[group+'/pids.max']='64\n'
    if kind=='duplicate_counter':files[group+'/pids.events']='max 2\nmax 9\n'
    if kind=='missing_counter':files[group+'/pids.events']='unrelated 9\n'
    if kind=='nonnumeric_counter':files[group+'/pids.events']='max forged\n'
    if kind=='negative_counter':files[group+'/pids.events']='max -1\n'
    if kind in ('wrong_container','stopped_container','missing_pid'):
        entry={'Id':CONTAINER,'State':{'Pid':12345,'Running':True},'HostConfig':{'PidsLimit':32}}
        if kind=='wrong_container':entry['Id']='2'*64
        if kind=='stopped_container':entry['State']['Running']=False
        if kind=='missing_pid':del entry['State']['Pid']
        inspection=[entry]
    if kind=='malformed_inspect':inspection={}
    module,runtime,reads,commands,_=host_fixture(monkeypatch,inspection=inspection,files=files)
    assert asyncio.run(module.host_pids_snapshot(runtime)) is None
    assert all(not path.startswith('/work') for path in reads)
    assert commands==[('inspect','fixture-runtime')]


def test_exhaustion_cleanup_failure_never_becomes_a_completed_defined_zero(monkeypatch,tmp_path):
    import qi_runtime as runtime_module
    from qi_runtime.infrastructure import DockerFailure,RetryBudget,run_with_retry,track_runtime
    from verifiers.v1.runtimes.base import ProgramResult
    samples=iter([snapshot(),snapshot(3)])
    async def sample(runtime):return next(samples)
    async def health():return {'success':True}
    monkeypatch.setattr(runtime_module,'host_pids_snapshot',sample)
    monkeypatch.setattr(runtime_module,'daemon_probe',health)
    async def command(*args):return ProgramResult(0,'public output','')
    runtime=SimpleNamespace(flagged=False,commands=[],_process_allowance_violation=False,
                            _run_command=command,name='fixture',info=SimpleNamespace(id=CONTAINER),
                            _container='fixture',_stopped=False,stopped=False)
    async def stop():raise DockerFailure('synthetic removal not confirmed')
    runtime.stop=stop
    async def scenario():
        async def operation():
            track_runtime(runtime)
            await runtime_module.CheckedRuntime.run(runtime,['synthetic'],{})
            raise AssertionError('failed cleanup must not return policy result')
        ledger=RetryBudget(1)
        result=await run_with_retry(operation,ledger=ledger,journal_root=tmp_path/'journal')
        assert result['complete'] is False
        assert result['infrastructure_ok'] is False
        assert result['value'] is None
        assert not result['retried'] and ledger.used==0
        assert result['attempts'][0]['cleanup_complete'] is False
        assert result['attempts'][0]['policy_evidence'] is False
    asyncio.run(scenario())
    assert not runtime.flagged and not runtime._process_allowance_violation
