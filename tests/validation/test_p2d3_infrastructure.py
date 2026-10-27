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
        assert classify_exception(error, policy_evidence=True) == 'policy'


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
