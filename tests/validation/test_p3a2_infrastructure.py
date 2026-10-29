"""Independent prospective infrastructure validation; synthetic faults, no Docker."""
import asyncio
from types import SimpleNamespace as NS

import pytest

import qi_runtime
import qi_runtime.infrastructure as infra
from envs.e2_leakage_audit import v1_taskset as e2


def test_terminating_typed_host_error_wins_prior_policy():
    policy = infra.PolicyFailure('read-only harness denied')
    host = infra.HostTimeout('trusted submission transfer deadline')
    host.__context__ = policy
    wrapper = RuntimeError('framework summary')
    wrapper.__cause__ = host
    assert infra.classify_exception(wrapper, policy_evidence=True) == 'infrastructure'
    assert infra.classify_exception(asyncio.CancelledError(), policy_evidence=True) == 'unknown'


def fake_runtime(monkeypatch):
    runtime = qi_runtime.CheckedRuntime(qi_runtime.WORK / 'p3a2-synthetic')
    runtime.info.id = 'synthetic-container'
    runtime.snapshot = {'Image': 'synthetic-image'}
    runtime.commands = []
    return runtime


def test_harness_tamper_never_attempts_fault_injected_submission_transfer(monkeypatch):
    runtime = fake_runtime(monkeypatch)
    writes = []
    async def write(self, path, data):
        writes.append(path)
        if path == '/work/submission.json':
            raise infra.HostTimeout('regression: post-tamper trusted transfer timeout')
    async def run(self, argv, env):
        self.flagged = True
        self.commands.append({'exit_code': 1, 'policy_outcome': 'audit_violation'})
        infra.note_policy()
        return qi_runtime.ProgramResult(1, '', 'open /opt/qi/harness.py: read-only')
    monkeypatch.setattr(qi_runtime.CheckedRuntime, 'write', write)
    monkeypatch.setattr(qi_runtime.CheckedRuntime, 'run', run)
    harness = e2.E2Harness(e2.E2HarnessConfig(source='synthetic harness overwrite'))
    trace = NS(info={'e2_lifecycle': ['setup']})
    asyncio.run(harness.launch(None, trace, runtime, None, None, None, None))
    assert writes == ['/work/program.py']
    assert runtime.flagged and runtime.commands


def test_finalize_flagged_skips_every_read_and_preserves_provenance(monkeypatch):
    runtime = fake_runtime(monkeypatch)
    runtime.flagged = True
    runtime.commands = [{'exit_code': 1, 'policy_outcome': 'audit_violation'}]
    reads = []
    async def read(self, *args, **kwargs):
        reads.append(args)
        raise infra.HostTimeout('forbidden finalization read')
    async def stop(self):
        self._stopped = True
    monkeypatch.setattr(qi_runtime.CheckedRuntime, 'read', read)
    monkeypatch.setattr(qi_runtime.CheckedRuntime, 'stop', stop)
    task = e2.E2Task(e2.E2Data(seed=1000000, tier='T2', name='synthetic'))
    task._solver = runtime
    task._trace_id = 'synthetic'
    task._submission = {'findings': [], 'patched_source': 'do not execute'}
    trace = NS(id='synthetic', info={'e2_lifecycle': ['setup', 'solver']})
    asyncio.run(task.finalize(trace, runtime))
    assert reads == [] and task._submission is None
    assert task._solver_record['flagged'] is True
    assert task._solver_record['container_id'] == 'synthetic-container'
    assert task._solver_record['commands'] == runtime.commands
    assert runtime._stopped


def test_policy_then_wrapped_host_timeout_retries_fresh_but_reward_stays_zero(tmp_path):
    seen = []
    async def call():
        number = len(seen)
        seen.append(number)
        infra.note_resource('container-' + str(number), 'id-' + str(number))
        if number == 0:
            infra.note_policy()
            infra.record_exception(infra.PolicyFailure('harness tamper denied'))
            try:
                raise infra.HostTimeout('injected trusted transfer timeout')
            except infra.HostTimeout as error:
                raise RuntimeError('framework wrapper') from error
        return {'reward': 1., 'flagged': False}
    ledger = infra.RetryBudget(200)
    result = asyncio.run(infra.run_with_retry(call, ledger=ledger, journal_root=tmp_path))
    assert seen == [0, 1] and ledger.used == 1
    assert result['complete'] and result['infrastructure_ok']
    assert result['value']['reward'] == 0. and result['value']['flagged']
    assert result['attempts'][0]['kind'] == 'infrastructure'
    assert all(a['cleanup_complete'] and not a['resource_overlap'] for a in result['attempts'])


def test_persistent_infrastructure_after_policy_keeps_complete_zero_and_fails_health(tmp_path):
    calls = []
    async def call():
        calls.append(1)
        infra.note_policy()
        raise infra.HostTimeout('persistent host deadline')
    result = asyncio.run(infra.run_with_retry(call, ledger=infra.RetryBudget(200), journal_root=tmp_path))
    assert len(calls) == 2
    assert result['complete'] and result['value']['reward'] == 0.
    assert result['infrastructure_ok'] is False
    assert result['terminal_kind'] == 'infrastructure'


def test_failed_cleanup_after_policy_is_complete_zero_but_unhealthy(tmp_path):
    async def stop():
        raise infra.DockerFailure('injected cleanup failure')
    async def call():
        infra.note_policy()
        infra.track_runtime(NS(_container='leftover', _stopped=False, stop=stop))
        return {'reward': 0., 'flagged': True}
    result = asyncio.run(infra.run_with_retry(call, ledger=infra.RetryBudget(200), journal_root=tmp_path))
    assert result['complete'] and result['value']['reward'] == 0.
    assert result['infrastructure_ok'] is False
    assert not result['attempts'][0]['cleanup_complete']
    assert any('DockerFailure' in e['types'] for e in result['attempts'][0]['exceptions'])


def test_execute_plan_continues_all_initial_rows_after_retry_budget_exhaustion(tmp_path):
    from scripts.p3a2_support import execute_plan
    seen = []
    async def call(item):
        seen.append(item)
        if item in (0, 1):
            raise infra.HostTimeout('terminal synthetic row')
        return {'reward': 1.}
    ledger = infra.RetryBudget(200)
    rows = asyncio.run(execute_plan(list(range(200)), call, concurrency=8,
                                   ledger=ledger, journal_root=tmp_path))
    assert len(rows) == 200 and set(seen) == set(range(200))
    assert ledger.used == 1
    assert sum(not row['complete'] for row in rows) == 2
    assert all(row['complete'] for row in rows[2:])
    assert any(row['terminal_kind'] == 'retry_limit' for row in rows)


@pytest.mark.parametrize('fail_transfer,fail_probe', [(False, False), (True, False), (True, True)])
def test_transfer_telemetry_preserves_original_failure_and_bounds_payload(monkeypatch, tmp_path, fail_transfer, fail_probe):
    async def raw(*args, **kwargs):
        if fail_transfer:
            raise infra.HostTimeout('original transfer failure')
        return 0, 'abc', ''
    async def probe():
        return {'success': not fail_probe, 'duration_seconds': .002,
                'exception_type': 'DockerFailure' if fail_probe else None}
    monkeypatch.setattr(qi_runtime, '_cli', raw, raising=False)
    monkeypatch.setattr(qi_runtime, 'daemon_probe', probe, raising=False)
    async def call():
        return await qi_runtime.cli('exec', 'secret-command-payload', input_data=b'secret-input')
    result = asyncio.run(infra.run_with_retry(call, ledger=infra.RetryBudget(1), journal_root=tmp_path))
    transfer = result['attempts'][0]['transfers'][0]
    assert transfer['operation'] == 'exec' and transfer['input_bytes'] == 12
    assert transfer['duration_seconds'] >= 0
    assert transfer['success'] == (not fail_transfer)
    assert transfer['exception_type'] == ('HostTimeout' if fail_transfer else None)
    assert transfer['daemon_probe']['success'] == (not fail_probe)
    assert transfer['daemon_probe']['duration_seconds'] == .002
    assert 'secret-' not in str(transfer)
    if fail_transfer:
        assert result['terminal_kind'] == 'retry_limit'
        assert any('original transfer failure' in str(e) for e in result['attempts'][0]['exceptions'])
    else:
        assert transfer['output_bytes'] == 3
