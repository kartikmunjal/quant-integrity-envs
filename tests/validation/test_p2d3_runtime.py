"""Controlled real-runtime faults; design seed only, no reward changes."""
import asyncio,os
import pytest
import qi_runtime
from qi_runtime.infrastructure import DockerFailure,HostTimeout,RetryBudget,run_with_retry
from envs.e6_data_traps.v1_taskset import run_policy
from envs.e6_data_traps.runtime import reference_program

pytestmark=pytest.mark.skipif(os.environ.get('QI_REAL_SANDBOX')!='1',reason='Docker required')

def test_scoring_failure_preserves_chain_and_retries_fresh(monkeypatch,tmp_path):
    original=qi_runtime.cli;starts=0
    async def injected(*args,**kwargs):
        nonlocal starts
        if args[0]=='run':
            starts+=1
            if starts==2:
                try:raise OSError('injected initiating daemon cause')
                except OSError as cause:raise DockerFailure('injected scoring provisioning failure') from cause
        return await original(*args,**kwargs)
    monkeypatch.setattr(qi_runtime,'cli',injected)
    async def call():return await run_policy(1002000,'T4',reference_program())
    result=asyncio.run(run_with_retry(call,ledger=RetryBudget(5000),journal_root=tmp_path))
    assert result['complete'] and result['retried'] and result['value']['reward']==1
    assert len(result['attempts'])==2
    files='\n'.join(p.read_text() for p in tmp_path.rglob('*.txt'))
    assert 'injected initiating daemon cause' in files and 'injected scoring provisioning failure' in files
    assert result['attempts'][0]['cleanup_complete']
    first={x['name'] for x in result['attempts'][0]['resources']}
    second={x['name'] for x in result['attempts'][1]['resources']}
    assert first.isdisjoint(second)


def test_host_timeout_is_retried_without_solver_timeout(monkeypatch,tmp_path):
    original=qi_runtime.cli;injected_once=False
    async def injected(*args,**kwargs):
        nonlocal injected_once
        if 'strace' in args and not injected_once:
            injected_once=True
            try:raise TimeoutError('injected host client deadline')
            except TimeoutError as cause:raise HostTimeout('host-load timeout') from cause
        return await original(*args,**kwargs)
    monkeypatch.setattr(qi_runtime,'cli',injected)
    async def call():return await run_policy(1002000,'T4',reference_program())
    result=asyncio.run(run_with_retry(call,ledger=RetryBudget(5000),journal_root=tmp_path))
    assert result['complete'] and result['retried'] and result['value']['reward']==1


def test_real_solver_timeout_is_policy_zero_never_retried(tmp_path):
    async def call():return await run_policy(1002000,'T4','import time;time.sleep(30)')
    result=asyncio.run(run_with_retry(call,ledger=RetryBudget(5000),journal_root=tmp_path))
    assert result['complete'] and not result['retried'] and result['value']['reward']==0
    assert result['attempts'][0]['policy_evidence']
