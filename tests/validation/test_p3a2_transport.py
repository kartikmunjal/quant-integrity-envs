"""Synthetic transport/policy collision: Docker wrapper status is not child status."""
import asyncio

import qi_runtime
from qi_runtime.infrastructure import RetryBudget, note_resource, run_with_retry


def test_audited_policy_trace_does_not_hide_nonzero_docker_transport(monkeypatch, tmp_path):
    calls = []
    commands = []
    async def fake_cli(*args, **kwargs):
        commands.append((args, kwargs))
        if kwargs.get('policy_output'):
            # The trusted Python wrapper normally exits zero after recording
            # the traced child status; 125 here belongs to Docker transport.
            return 125, '', 'openat(3,"/opt/qi/canary",O_RDONLY) = -1 EACCES'
        raise AssertionError('policy collision must not trigger status/source reads')
    monkeypatch.setattr(qi_runtime, 'cli', fake_cli)
    async def call():
        index = len(calls)
        calls.append(index)
        runtime = qi_runtime.CheckedRuntime(qi_runtime.WORK / ('p3a2-transport-fault-' + str(index)))
        runtime.info.id = 'synthetic-' + str(index)
        runtime._harness_hash = 'synthetic'
        note_resource(runtime.name, runtime.info.id)
        outcome = await runtime.run(['python', 'synthetic.py'], {})
        return {'reward': 0., 'flagged': runtime.flagged, 'exit_code': outcome.exit_code}
    ledger = RetryBudget(200)
    result = asyncio.run(run_with_retry(call, ledger=ledger, journal_root=tmp_path))
    assert calls == [0, 1]
    assert ledger.used == 1
    assert result['complete'] and result['value']['reward'] == 0.
    assert result['infrastructure_ok'] is False
    assert result['terminal_kind'] == 'infrastructure'
    assert all(a['kind'] == 'infrastructure' and a['policy_evidence'] for a in result['attempts'])
    assert all(not a['resource_overlap'] and a['cleanup_complete'] for a in result['attempts'])
    assert len(commands) == 2


def test_audit_transport_failure_recovers_once_with_fresh_resources_and_zero(monkeypatch, tmp_path):
    calls = []
    async def fake_cli(*args, **kwargs):
        if kwargs.get('policy_output'):
            return (125 if len(calls) == 1 else 0), '', 'openat(3,"/opt/qi/canary",O_RDONLY) = -1 EACCES'
        raise AssertionError('no post-policy transfers')
    monkeypatch.setattr(qi_runtime, 'cli', fake_cli)
    async def call():
        index = len(calls)
        calls.append(index)
        runtime = qi_runtime.CheckedRuntime(qi_runtime.WORK / ('p3a2-transport-recovered-' + str(index)))
        runtime.info.id = 'synthetic-recovery-' + str(index)
        runtime._harness_hash = 'synthetic'
        note_resource(runtime.name, runtime.info.id)
        outcome = await runtime.run(['python', 'synthetic.py'], {})
        return {'reward': 0., 'flagged': runtime.flagged, 'exit_code': outcome.exit_code}
    ledger = RetryBudget(200)
    result = asyncio.run(run_with_retry(call, ledger=ledger, journal_root=tmp_path))
    assert calls == [0, 1] and ledger.used == 1
    assert result['complete'] and result['infrastructure_ok']
    assert result['value']['reward'] == 0. and result['value']['flagged']
    assert result['attempts'][0]['kind'] == 'infrastructure'
    assert result['attempts'][1]['kind'] == 'complete'
    assert all(a['policy_evidence'] and a['cleanup_complete'] and not a['resource_overlap'] for a in result['attempts'])


def test_successful_transfer_failed_optional_daemon_probe_is_diagnostic(monkeypatch, tmp_path):
    # A separately timed optional probe does not replace the completed transfer's
    # status: retain failed probe telemetry without inventing a terminal failure.
    async def raw(*args, **kwargs):
        return 0, 'payload', ''
    async def probe():
        return {'success': False, 'duration_seconds': .003, 'exception_type': 'DockerFailure'}
    monkeypatch.setattr(qi_runtime, '_cli', raw)
    monkeypatch.setattr(qi_runtime, 'daemon_probe', probe)
    async def call():
        code, out, err = await qi_runtime.cli('exec', input_data=b'synthetic')
        assert (code, out, err) == (0, 'payload', '')
        return {'reward': 1.}
    ledger = RetryBudget(200)
    result = asyncio.run(run_with_retry(call, ledger=ledger, journal_root=tmp_path))
    assert result['complete'] and result['infrastructure_ok']
    assert not result['retried'] and ledger.used == 0
    assert result['value']['reward'] == 1.
    transfer = result['attempts'][0]['transfers'][0]
    assert transfer['success'] and transfer['exception_type'] is None
    assert transfer['daemon_probe'] == {'success': False, 'duration_seconds': .003, 'exception_type': 'DockerFailure'}
