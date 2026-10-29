"""Prospective P2d3 infrastructure controls; no Docker or generated cases."""
import asyncio
import json

import pytest

import qi_runtime
from qi_runtime.infrastructure import (
    DockerFailure, HostTimeout, InfrastructureError, RetryBudget,
    RetryLimitExceeded, classify_exception, note_resource, record_exception,
    run_with_retry,
)


def test_classification_uses_trusted_types_and_entire_chain():
    assert classify_exception(DockerFailure('daemon failed')) == 'infrastructure'
    assert classify_exception(HostTimeout('host deadline')) == 'infrastructure'
    assert classify_exception(ValueError('docker daemon timeout')) == 'unknown'
    assert classify_exception(TimeoutError('solver timeout')) == 'unknown'
    try:
        try:
            raise DockerFailure('original daemon error')
        except DockerFailure as cause:
            raise ValueError('borrowed runtime stopped') from cause
    except ValueError as error:
        assert classify_exception(error) == 'infrastructure'
        assert classify_exception(error, policy_evidence=True) == 'infrastructure'  # P3a2 terminating operation


@pytest.mark.parametrize("explicit_cause", [False, True])
def test_exception_journal_preserves_long_chain_and_is_json_serializable(tmp_path, explicit_cause):
    marker = 'origin-' + 'x' * 20000
    try:
        try:
            raise DockerFailure(marker)
        except DockerFailure as cause:
            if explicit_cause:
                raise ValueError('context-wrapper') from cause
            raise ValueError('context-wrapper')
    except ValueError as error:
        evidence = record_exception(error, root=tmp_path, metadata={'seed': 1001000})
    json.dumps(evidence)
    files = [path for path in tmp_path.rglob('*') if path.is_file()]
    assert files
    persisted = '\n'.join(path.read_text() for path in files)
    assert marker in persisted
    assert 'context-wrapper' in persisted
    assert 'Traceback (most recent call last)' in persisted


@pytest.mark.parametrize('planned,limit', [(5000, 25), (8400, 42), (199, 0)])
def test_retry_budget_uses_fixed_denominator(planned, limit):
    budget = RetryBudget(planned)
    assert budget.max_retries == limit
    for _ in range(limit):
        budget.reserve()
    assert budget.used == limit
    with pytest.raises(RetryLimitExceeded):
        budget.reserve()
    assert budget.used == limit


def test_infrastructure_retry_uses_fresh_attempt_and_records_both(tmp_path):
    calls = []
    async def rollout():
        number = len(calls)
        calls.append(number)
        note_resource(f'primary-{number}', container_id=f'id-{number}')
        note_resource(f'replay-{number}', container_id=f'replay-id-{number}')
        if number == 0:
            raise DockerFailure('synthetic trusted provisioning failure')
        return {'reward': 1.0}
    budget = RetryBudget(5000)
    result = asyncio.run(run_with_retry(rollout, metadata={'seed': 1001000},
                                      ledger=budget, journal_root=tmp_path))
    assert calls == [0, 1]
    assert result['value'] == {'reward': 1.0}
    assert result['complete'] is True
    assert result['retried'] is True
    assert len(result['attempts']) == 2
    assert budget.used == 1
    evidence = json.dumps(result)
    for expected in ('primary-0', 'primary-1', 'id-0', 'id-1', 'replay-0', 'replay-1'):
        assert expected in evidence


def test_infrastructure_retry_rejects_reused_resource(tmp_path):
    calls = []
    async def rollout():
        calls.append(1)
        note_resource('same-container', container_id='same-id')
        if len(calls) == 1:
            raise InfrastructureError('retryable')
        return {'reward': 1.0}
    result = asyncio.run(run_with_retry(rollout, ledger=RetryBudget(5000), journal_root=tmp_path))
    assert len(calls) == 2
    assert result['complete'] is False


@pytest.mark.parametrize('error,expected_calls', [(ValueError('scorer bug'), 1),
                                                (DockerFailure('persistent daemon failure'), 2)])
def test_unknown_or_second_failure_is_terminal(tmp_path, error, expected_calls):
    calls = []
    async def rollout():
        calls.append(1)
        raise error
    result = asyncio.run(run_with_retry(rollout, ledger=RetryBudget(5000), journal_root=tmp_path))
    assert len(calls) == expected_calls
    assert result['complete'] is False
    assert len(result['attempts']) == expected_calls
    assert result['terminal_kind'] == ('unknown' if expected_calls == 1 else 'infrastructure')


@pytest.mark.parametrize('outcome', [
    {'reward': 0.0, 'flagged': True, 'exit_code': 0},
    {'reward': 0.0, 'flagged': False, 'exit_code': 1},
    {'reward': 0.0, 'flagged': False, 'exit_code': 124},
    {'reward': 0.0, 'flagged': False, 'exit_code': 0},
])
def test_completed_hard_zero_is_never_retried(tmp_path, outcome):
    calls = []
    async def rollout():
        calls.append(1)
        return outcome
    budget = RetryBudget(5000)
    result = asyncio.run(run_with_retry(rollout, ledger=budget, journal_root=tmp_path))
    assert calls == [1]
    assert result['value'] == outcome
    assert result['complete'] is True
    assert result['retried'] is False
    assert budget.used == 0


def test_stop_is_concurrent_and_idempotent(monkeypatch):
    commands = []
    async def fake_cli(*args, **kwargs):
        commands.append(args)
        await asyncio.sleep(0)
        return 0, '', ''
    monkeypatch.setattr(qi_runtime, 'cli', fake_cli)
    runtime = qi_runtime.CheckedRuntime(qi_runtime.WORK / 'synthetic-stop-test')
    runtime._container = 'synthetic-container'
    runtime._stopped = False
    async def twice():
        await asyncio.gather(runtime.stop(), runtime.stop())
    asyncio.run(twice())
    assert commands == [('rm', '-f', 'synthetic-container')]
    assert runtime._stopped is True


def test_failed_cleanup_preserves_extant_state(monkeypatch):
    async def failed_cli(*args, **kwargs):
        return 1, '', 'synthetic daemon unavailable'
    monkeypatch.setattr(qi_runtime, 'cli', failed_cli)
    runtime = qi_runtime.CheckedRuntime(qi_runtime.WORK / 'synthetic-cleanup-test')
    runtime._container = 'synthetic-container'
    runtime._stopped = False
    with pytest.raises(DockerFailure):
        asyncio.run(runtime.stop())
    assert runtime._stopped is False


def test_p3a2_policy_collision_preserves_zero_but_retries_host_failure(tmp_path):
    from qi_runtime.infrastructure import note_policy
    calls=[]
    async def rollout():
        calls.append(1);note_policy();raise DockerFailure('cleanup failure after solver failure')
    result=asyncio.run(run_with_retry(rollout,ledger=RetryBudget(5000),journal_root=tmp_path))
    assert len(calls)==2 and result['value']['reward']==0
    assert result['complete'] is True and result['terminal_kind']=='infrastructure'
    assert result['infrastructure_ok'] is False


def test_real_framework_guard_preserves_scoring_cause_but_rejects_live_shutdown(monkeypatch,tmp_path):
    from types import SimpleNamespace as NS
    from verifiers.v1.rollout import Rollout
    import qi_runtime.infrastructure as infra
    monkeypatch.setattr(infra,'ROOT',tmp_path)
    runtime=qi_runtime.CheckedRuntime(qi_runtime.WORK/'synthetic-guard')
    runtime.stopped=True;runtime._stopped=True
    saved=[]
    trace=NS(id='test-guard',timing=NS(finalize=NS(end=1.),scoring=NS(start=1.)),record_error=saved.append)
    actor=NS(runtime=runtime,_owns_runtime=False,_closed=True,trace=trace)
    original=HostTimeout('initiating host deadline')
    with pytest.raises(ValueError):Rollout.fail._qi_original(actor,original)
    Rollout.fail(actor,original)
    assert actor._failure is original and saved==[original] and not actor._owns_runtime
    actor._closed=False
    with pytest.raises(ValueError):Rollout.fail(actor,original)


def test_malformed_trusted_docker_json_is_not_a_policy_zero(monkeypatch):
    async def fake_cli(*args,**kwargs):
        if args[0]=='inspect':return 0,'not JSON',''
        return 1,'','solver failed'
    monkeypatch.setattr(qi_runtime,'cli',fake_cli)
    runtime=qi_runtime.CheckedRuntime(qi_runtime.WORK/'synthetic-json')
    runtime._harness_hash='known'
    with pytest.raises(json.JSONDecodeError):asyncio.run(runtime.run(['python','x'],{}))


def test_startup_exception_is_recorded_before_framework_summary(monkeypatch,tmp_path):
    import qi_runtime.infrastructure as infra
    monkeypatch.setattr(infra,'ROOT',tmp_path)
    async def fake_cli(*args,**kwargs):return 1,'','provisioning synthetic daemon error'
    monkeypatch.setattr(qi_runtime,'cli',fake_cli)
    runtime=qi_runtime.CheckedRuntime(qi_runtime.WORK/'synthetic-startup')
    with pytest.raises(DockerFailure):asyncio.run(runtime.start())
    assert 'provisioning synthetic daemon error' in '\n'.join(p.read_text() for p in tmp_path.rglob('*.txt'))


def test_trusted_write_uses_bounded_local_transport(monkeypatch):
    seen=[]
    async def fake_cli(*args,**kwargs):seen.append((args,kwargs));return 0,'',''
    monkeypatch.setattr(qi_runtime,'cli',fake_cli)
    runtime=qi_runtime.CheckedRuntime(qi_runtime.WORK/'synthetic-write')
    runtime._container='fake'
    asyncio.run(runtime.write('/work/program.py',b'print(1)'))
    assert len(seen)==1 and seen[0][1]['input_data']==b'print(1)'


@pytest.mark.parametrize('exit_code', [125, 126, 127])
@pytest.mark.parametrize('solver_completed', [False, True])
def test_transport_status_is_distinct_from_identical_solver_exit(monkeypatch, tmp_path, exit_code, solver_completed):
    """Only a root-owned durable status authenticates a solver exit code."""
    import qi_runtime.infrastructure as infra
    monkeypatch.setattr(infra, 'ROOT', tmp_path)
    async def fake_cli(*args, **kwargs):
        if args[0] == 'inspect':
            return 0, json.dumps([{'State': {'Running': True, 'OOMKilled': False}}]), ''
        if 'sha256sum' in args:
            return 0, 'known', ''
        if kwargs.get('policy_output'):
            return (0 if solver_completed else exit_code), '', 'synthetic failure'
        # The protected status retrieval is distinct from solver output.
        if solver_completed:
            return 0, json.dumps({'exit_code': exit_code}), ''
        return 1, '', 'no durable solver status'
    monkeypatch.setattr(qi_runtime, 'cli', fake_cli)
    runtime = qi_runtime.CheckedRuntime(qi_runtime.WORK / 'synthetic-transport')
    runtime._harness_hash = 'known'
    if solver_completed:
        result = asyncio.run(runtime.run(['python', 'x'], {}))
        assert result.exit_code == exit_code
        assert runtime.commands[-1]['policy_outcome'] == 'solver_crash'
    else:
        with pytest.raises(DockerFailure):
            asyncio.run(runtime.run(['python', 'x'], {}))
        assert runtime.flagged is False


def test_transport_failure_gets_retry_without_policy_evidence(monkeypatch, tmp_path):
    async def fake_cli(*args, **kwargs):
        if args[0] == 'inspect':
            return 0, json.dumps([{'State': {'Running': True, 'OOMKilled': False}}]), ''
        return 125, '', 'docker exec transport failed'
    monkeypatch.setattr(qi_runtime, 'cli', fake_cli)
    async def rollout():
        runtime = qi_runtime.CheckedRuntime(qi_runtime.WORK / 'synthetic-transport-retry')
        return await runtime.run(['python', 'x'], {})
    result = asyncio.run(run_with_retry(rollout, ledger=RetryBudget(5000), journal_root=tmp_path))
    assert result['retried'] is True
    assert result['terminal_kind'] == 'infrastructure'
    assert all(not attempt['policy_evidence'] for attempt in result['attempts'])


@pytest.mark.skipif(__import__('os').environ.get('QI_REAL_SANDBOX') != '1', reason='requires approved Docker access')
def test_real_protected_status_preserves_solver_exits_and_transport_failure(monkeypatch):
    import tempfile
    from pathlib import Path
    original_cli = qi_runtime.cli
    async def run():
        with tempfile.TemporaryDirectory(prefix='p2d3-status-', dir=qi_runtime.WORK) as directory:
            work = Path(directory)
            work.chmod(0o777)
            runtime = qi_runtime.CheckedRuntime(work)
            try:
                await runtime.start()
                for expected in (0, 1, 125, 126, 127):
                    result = await runtime.run(['python', '-I', '-c', f'raise SystemExit({expected})'], {})
                    assert result.exit_code == expected
                async def transport_failure(*args, **kwargs):
                    if kwargs.get('policy_output'):
                        return 125, '', 'synthetic transport failure with healthy real container'
                    return await original_cli(*args, **kwargs)
                monkeypatch.setattr(qi_runtime, 'cli', transport_failure)
                with pytest.raises(DockerFailure):
                    await runtime.run(['python', '-I', '-c', 'print(1)'], {})
            finally:
                monkeypatch.setattr(qi_runtime, 'cli', original_cli)
                await runtime.stop()
    asyncio.run(run())


def test_trusted_harness_probe_transport_error_is_infrastructure(monkeypatch, tmp_path):
    import qi_runtime.infrastructure as infra
    monkeypatch.setattr(infra, 'ROOT', tmp_path)
    async def fake_cli(*args, **kwargs):
        if kwargs.get('policy_output'):
            return 0, 'answer', ''
        if 'sha256sum' in args:
            return 125, '', 'transport failed'
        if args[0] == 'inspect':
            return 0, json.dumps([{'State': {'Running': True, 'OOMKilled': False}}]), ''
        return 0, json.dumps({'exit_code': 0}), ''
    monkeypatch.setattr(qi_runtime, 'cli', fake_cli)
    runtime = qi_runtime.CheckedRuntime(qi_runtime.WORK / 'synthetic-harness-probe')
    runtime._harness_hash = 'known'
    with pytest.raises(DockerFailure):
        asyncio.run(runtime.run(['python', 'x'], {}))
    assert runtime.flagged is False


@pytest.mark.parametrize('trace', ['openat(3, "/opt/qi/canary", O_RDONLY)',
                                   'socket(AF_INET, SOCK_STREAM, 0)'])
def test_audit_evidence_dominates_failed_completion_marker(monkeypatch, tmp_path, trace):
    """Confirmed policy traces must survive an independent status-read failure."""
    calls = []
    async def fake_cli(*args, **kwargs):
        if kwargs.get('policy_output'):
            return 0, '', trace
        if args[0] == 'inspect':
            return 0, json.dumps([{'State': {'Running': True, 'OOMKilled': False}}]), ''
        return 125, '', 'protected marker transport failed'
    monkeypatch.setattr(qi_runtime, 'cli', fake_cli)
    async def rollout():
        calls.append(1)
        runtime = qi_runtime.CheckedRuntime(qi_runtime.WORK / 'synthetic-audit-status-collision')
        return await runtime.run(['python', 'x'], {})
    result = asyncio.run(run_with_retry(rollout, ledger=RetryBudget(5000), journal_root=tmp_path))
    assert calls == [1]
    assert result['retried'] is False
    assert result['terminal_kind'] is None  # P3a2 audit closes before marker transfer
    assert result['complete'] is True
    assert result['value']['reward'] == 0
    assert result['attempts'][0]['policy_evidence'] is True


@pytest.mark.parametrize('boundary', ['open', 'fail'])
def test_genuine_borrowed_lifetime_guard_has_typed_retry_evidence(tmp_path, boundary):
    from types import SimpleNamespace as NS
    from verifiers.v1.rollout import Rollout
    seen = []
    async def rollout():
        runtime = qi_runtime.CheckedRuntime(qi_runtime.WORK / 'synthetic-lifetime')
        runtime.stopped = True
        runtime._stopped = True
        actor = NS(runtime=runtime, _owns_runtime=False, _closed=False,
                   trace=NS(id='lifetime-test', timing=NS(boot=NS(start=None),
                            finalize=NS(end=None), scoring=NS(start=None))))
        try:
            if boundary == 'open':
                await Rollout.open(actor)
            else:
                Rollout.fail(actor, ValueError('unknown initiating failure'))
        except ValueError as error:
            seen.append(error)
            raise
    result = asyncio.run(run_with_retry(rollout, ledger=RetryBudget(5000), journal_root=tmp_path))
    assert len(seen) == 2 and all(type(error) is ValueError for error in seen)
    assert result['retried'] is True
    assert result['terminal_kind'] == 'infrastructure'
    assert all(any('InfrastructureError' in item['types'] for item in attempt['exceptions'])
               for attempt in result['attempts'])
    if boundary == 'fail':
        assert all(type(error.__cause__) is ValueError for error in seen)
        evidence = '\n'.join(path.read_text() for path in tmp_path.rglob('*.txt'))
        assert 'unknown initiating failure' in evidence


def test_closed_scoring_unknown_failure_keeps_unknown_classification(tmp_path):
    from types import SimpleNamespace as NS
    from verifiers.v1.rollout import Rollout
    async def rollout():
        runtime = qi_runtime.CheckedRuntime(qi_runtime.WORK / 'synthetic-scoring-unknown')
        runtime.stopped = True
        runtime._stopped = True
        actor = NS(runtime=runtime, _owns_runtime=False, _closed=True,
                   trace=NS(id='scoring-test', timing=NS(finalize=NS(end=1.), scoring=NS(start=1.)),
                            record_error=lambda error: None))
        error = ValueError('unknown scorer bug')
        Rollout.fail(actor, error)
        assert actor._failure is error
        raise error
    result = asyncio.run(run_with_retry(rollout, ledger=RetryBudget(5000), journal_root=tmp_path))
    assert result['retried'] is False
    assert result['terminal_kind'] == 'unknown'


def test_cancelled_attempt_is_journaled_and_terminal_without_retry(tmp_path):
    calls = []
    async def rollout():
        calls.append(1)
        note_resource('cancelled-container', container_id='cancelled-id')
        raise asyncio.CancelledError('synthetic cancellation')
    result = asyncio.run(run_with_retry(rollout, ledger=RetryBudget(5000), journal_root=tmp_path))
    assert calls == [1]
    assert result['complete'] is False and result['retried'] is False
    assert result['terminal_kind'] == 'unknown'
    assert result['attempts'][0]['resources'][0]['container_id'] == 'cancelled-id'
    assert 'CancelledError' in result['attempts'][0]['exceptions'][0]['types']


def test_cancellation_overrides_prior_infrastructure_journal(tmp_path):
    calls = []
    async def rollout():
        calls.append(1)
        record_exception(DockerFailure('earlier diagnostic symptom'))
        raise asyncio.CancelledError('stop now')
    result = asyncio.run(run_with_retry(rollout, ledger=RetryBudget(5000), journal_root=tmp_path))
    assert calls == [1]
    assert result['terminal_kind'] == 'unknown' and result['retried'] is False


def test_cancelled_cleanup_is_recorded_and_attempt_context_restored(tmp_path):
    from types import SimpleNamespace as NS
    import qi_runtime.infrastructure as infra
    async def cleanup():
        raise asyncio.CancelledError('cleanup interrupted')
    async def rollout():
        infra.track_runtime(NS(_container='fake', _stopped=False, stop=cleanup))
        return {'reward': 1.0}
    result = asyncio.run(run_with_retry(rollout, ledger=RetryBudget(5000), journal_root=tmp_path))
    assert result['complete'] is False and result['retried'] is False
    assert result['terminal_kind'] == 'unknown'
    assert any('CancelledError' in item['types'] for item in result['attempts'][0]['exceptions'])
    assert infra._CURRENT.get() is None
