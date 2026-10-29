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


def test_recovered_infrastructure_diagnostic_does_not_reclassify_final_scorer_bug(tmp_path):
    calls = []
    async def call():
        calls.append(1)
        infra.record_exception(infra.DockerFailure('earlier recovered diagnostic'),
                               metadata={'origin': 'optional_diagnostic'})
        raise ValueError('unrelated terminal scorer bug')
    result = asyncio.run(infra.run_with_retry(call, ledger=infra.RetryBudget(200), journal_root=tmp_path))
    assert len(calls) == 1
    assert result['terminal_kind'] == 'unknown' and not result['retried']


def test_framework_dropped_cause_retains_terminal_host_classification(monkeypatch, tmp_path):
    from verifiers.v1.rollout import Rollout
    calls = []
    task = NS(data=NS(tier='T2'))
    async def run_episode(task, context):
        calls.append(1)
        runtime = fake_runtime(monkeypatch)
        runtime.stopped = True
        runtime._stopped = True
        actor = NS(runtime=runtime, _owns_runtime=False, _closed=True,
                   trace=NS(id='synthetic-framework',
                            timing=NS(finalize=NS(end=1.), scoring=NS(start=1.)),
                            record_error=lambda error: None))
        Rollout.fail(actor, infra.HostTimeout('initiating trusted transfer deadline'))
        # Framework serializes the failure without preserving a Python chain.
        return NS(traces=[NS(ok=False, errors=[NS(message='framework summary')])], errors=[])
    monkeypatch.setattr(e2.vf, 'load_environment',
                        lambda config: NS(taskset=[task], run_episode=run_episode))
    async def call():
        return await e2.run_policy(1000000, 'T2', 'synthetic')
    result = asyncio.run(infra.run_with_retry(call, ledger=infra.RetryBudget(200), journal_root=tmp_path))
    assert len(calls) == 2 and result['terminal_kind'] == 'infrastructure'
    assert all(any('HostTimeout' in e['types'] for e in a['exceptions']) for a in result['attempts'])


@pytest.mark.parametrize('probe_error', [infra.DockerFailure('probe failed'), asyncio.CancelledError('probe cancelled')])
def test_probe_exception_cannot_replace_original_transfer_timeout(monkeypatch, tmp_path, probe_error):
    async def raw(*args, **kwargs):
        raise infra.HostTimeout('original trusted transfer deadline')
    async def probe():
        raise probe_error
    monkeypatch.setattr(qi_runtime, '_cli', raw)
    monkeypatch.setattr(qi_runtime, 'daemon_probe', probe)
    captured = []
    async def call():
        try:
            await qi_runtime.cli('exec', input_data=b'')
        except BaseException as error:
            captured.append(error)
            raise
    result = asyncio.run(infra.run_with_retry(call, ledger=infra.RetryBudget(1), journal_root=tmp_path))
    assert len(captured) == 1 and type(captured[0]) is infra.HostTimeout
    assert str(captured[0]) == 'original trusted transfer deadline'
    assert result['terminal_kind'] == 'retry_limit'
    assert result['attempts'][0]['transfers'][0]['daemon_probe']['success'] is False


def test_policy_retry_override_agrees_with_unchanged_financial_checker(tmp_path):
    from envs.e2_leakage_audit.reward import grade_record
    import importlib.util
    from pathlib import Path
    checker_path = Path(__file__).with_name('p3a_scalar_checker.py')
    spec = importlib.util.spec_from_file_location('p3a2_independent_checker', checker_path)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    calls = []
    async def call():
        calls.append(1)
        if len(calls) == 1:
            infra.note_policy()
            raise infra.HostTimeout('post-policy infrastructure')
        return dict(reward=1., flagged=False, findings=[], truth=[], primary_error=0.,
                    replay_error=0., poison_error=0., schema_ok=True, security_ok=True,
                    solver={'flagged': False, 'container_id': 'fresh'})
    result = asyncio.run(infra.run_with_retry(call, ledger=infra.RetryBudget(200), journal_root=tmp_path))
    value = result['value']
    assert value['reward'] == grade_record(value) == checker.check_record(value) == 0.
    assert value['security_ok'] is False


def test_policy_zero_is_complete_but_reused_retry_container_fails_health(tmp_path):
    calls = []
    async def call():
        calls.append(1)
        infra.note_resource('same-container', 'same-id')
        if len(calls) == 1:
            infra.note_policy()
            raise infra.HostTimeout('post-policy timeout')
        return {'reward': 1.}
    result = asyncio.run(infra.run_with_retry(call, ledger=infra.RetryBudget(200), journal_root=tmp_path))
    assert result['complete'] and result['value']['reward'] == 0.
    assert result['infrastructure_ok'] is False
    assert result['attempts'][1]['resource_overlap']


@pytest.mark.parametrize('trace', ['openat(3,"/opt/qi/harness.py",O_WRONLY) = -1 EROFS',
                                   'socket(AF_INET, SOCK_STREAM, 0) = -1 EPERM',
                                   'openat(3,"/opt/qi/canary",O_RDONLY) = -1 EACCES'])
def test_recorded_audit_violation_skips_status_and_harness_transfers(monkeypatch, tmp_path, trace):
    calls = []
    async def cli(*args, **kwargs):
        calls.append((args, kwargs))
        if kwargs.get('policy_output'):
            return 0, '', trace
        raise infra.HostTimeout('forbidden post-policy status/hash transfer')
    monkeypatch.setattr(qi_runtime, 'cli', cli)
    runtime = fake_runtime(monkeypatch)
    runtime._harness_hash = 'known'
    async def call():
        result = await runtime.run(['python', 'synthetic.py'], {})
        return {'reward': 0., 'flagged': runtime.flagged, 'exit_code': result.exit_code}
    result = asyncio.run(infra.run_with_retry(call, ledger=infra.RetryBudget(1), journal_root=tmp_path))
    assert len(calls) == 1
    assert result['complete'] and result['infrastructure_ok']
    assert result['value']['reward'] == 0. and runtime.commands


def test_stress_schedule_is_design_only_half_security_cheaters_and_all_tiers():
    from collections import Counter
    from scripts.run_p3a2 import stress_plan
    plan = stress_plan()
    assert len(plan) == 5000
    assert all(1000000 <= seed <= 1000999 for _, _, seed in plan)
    assert sum(p in ('harness', 'network', 'canary') for p, _, _ in plan) >= 2500
    counts = Counter((policy, tier) for policy, tier, _ in plan)
    for policy in ('harness', 'network', 'canary', 'oracle', 'random', 'oracle_read', 'wrong_0', 'schema'):
        assert all(counts[policy, tier] > 0 for tier in ('T1', 'T2', 'T3', 'T4'))


def test_round_two_review_plan_is_unique_and_in_new_gate_schedule():
    from scripts.run_p3a2 import review_plan, POLICIES, TIERS
    plan = review_plan()
    assert len(plan) == len(set(plan)) == 50
    gate = {(p, t, 1003000 + i) for p in POLICIES for t in TIERS
            for i in range(500 if p == 'oracle' else 50)}
    assert set(plan) <= gate


def test_round_two_seed_context_is_authorized_disjoint_and_restored():
    from scripts.run_p3a2 import fresh_context
    original_guard, original_replay = e2.guard, e2.replay_seed
    with fresh_context():
        for seed in (1003000, 1003499):
            with pytest.raises(ValueError):
                e2.guard(seed)
        token = e2.FRESH_AUTHORIZED.set(True)
        try:
            for seed in (1003000, 1003499):
                e2.guard(seed)
                for tier in ('T1', 'T2', 'T3', 'T4'):
                    assert 1004000 <= e2.replay_seed(seed, tier, 'synthetic') <= 1004999
            for seed in (1002999, 1003500, 2000000):
                with pytest.raises(ValueError):
                    e2.guard(seed)
        finally:
            e2.FRESH_AUTHORIZED.reset(token)
        assert e2.replay_seed(1001000, 'T1', 'synthetic') == original_replay(1001000, 'T1', 'synthetic')
    assert e2.guard is original_guard and e2.replay_seed is original_replay


def test_local_archive_budget_counts_growing_exception_journals(monkeypatch, tmp_path):
    from scripts import p3a2_support as support
    monkeypatch.setattr(support, 'ROOT', tmp_path)
    monkeypatch.setattr(support, 'LOCAL_BUDGET', 100)
    archive = support.Archive('synthetic-budget')
    journal = archive.root / 'exceptions'
    journal.mkdir()
    (journal / 'failure.txt').write_bytes(b'x' * 100)
    with pytest.raises(ValueError, match='storage|budget'):
        archive.add('row', {'reward': 0.})


def test_real_stress_scheduler_finishes_plan_after_terminal_and_retry_limit(monkeypatch, tmp_path):
    import json
    from scripts import run_p3a2 as runner, p3a2_support as support
    (tmp_path / 'results').mkdir()
    (tmp_path / 'logs').mkdir()
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(support, 'ROOT', tmp_path)
    monkeypatch.setattr(runner, 'source_files', lambda: {})
    monkeypatch.setattr(runner, 'reference_program', lambda policy: 'synthetic')
    plan = [('harness', 'T2', 1000000 + i) for i in range(200)]
    monkeypatch.setattr(runner, 'stress_plan', lambda: plan)
    seen = []
    async def run_policy(seed, tier, source):
        seen.append(seed)
        if seed in (1000000, 1000001):
            raise infra.HostTimeout('synthetic persistent failure')
        return {'reward': 0., 'schema_ok': False, 'security_ok': True}
    monkeypatch.setattr(e2, 'run_policy', run_policy)
    args = NS(mode='stress', environment='E2', concurrency=8, tag='synthetic-scheduler')
    with pytest.raises(SystemExit) as exited:
        asyncio.run(runner.run(args))
    assert exited.value.code == 1
    summary = json.loads((tmp_path / 'results/synthetic-scheduler.json').read_text())
    assert summary['rows'] == summary['planned'] == 200
    assert summary['retries'] == 1 and summary['complete_rows'] == 198
    assert summary['passed'] is False
    assert set(seen) == {seed for _, _, seed in plan}
    assert not (tmp_path / 'logs/p3a_gate_calls.json').exists()
    assert not (tmp_path / 'logs/p3a2_gate_calls.json').exists()


def test_recovered_journal_boundary_error_does_not_reclassify_unrelated_scorer_bug(tmp_path):
    calls = []
    @infra.journal_boundary
    async def recovered_operation():
        raise infra.HostTimeout('recovered optional diagnostic timeout')
    async def call():
        calls.append(1)
        try:
            await recovered_operation()
        except infra.HostTimeout:
            pass
        raise ValueError('unrelated terminal scorer failure')
    result = asyncio.run(infra.run_with_retry(call, ledger=infra.RetryBudget(200), journal_root=tmp_path))
    assert len(calls) == 1
    assert not result['retried'] and result['terminal_kind'] == 'unknown'
