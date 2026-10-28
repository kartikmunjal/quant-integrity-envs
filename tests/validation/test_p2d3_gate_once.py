"""Prospective one-shot gate reservation tests; entirely mocked execution.

These tests never construct cases, policies, rollouts, or Docker resources.
"""
import asyncio
import json
from pathlib import Path

import pytest


class PlannedSetupFailure(RuntimeError):
    """Stop execution before any fresh gate plan or rollout is constructed."""


@pytest.fixture
def isolated_runner(monkeypatch, tmp_path):
    import qi_runtime.experiments as runner
    monkeypatch.chdir(tmp_path)
    Path('logs').mkdir()
    monkeypatch.setattr(runner, 'frozen_sources', lambda: {'synthetic-source': 'fixed'})
    monkeypatch.setattr(runner, 'runtime_version_hash', lambda: 'synthetic-runtime-hash')
    def forbidden_binding(*args, **kwargs):
        pytest.fail('one-shot reservation test reached environment/policy binding')
    monkeypatch.setattr(runner, 'binding', forbidden_binding)
    return runner


@pytest.mark.parametrize('tag,concurrency', [('alternate-tag', 12), ('other-tag', 24), (None, 24)])
def test_existing_global_gate_reservation_blocks_every_tag_and_concurrency(isolated_runner, monkeypatch, tag, concurrency):
    runner = isolated_runner
    marker = Path('logs/p2d3_gate_calls.json')
    original = json.dumps({'status': 'started', 'tag': 'original-gate', 'concurrency': 12})
    marker.write_text(original)
    def forbidden_plan(*args, **kwargs):
        pytest.fail('existing global gate reservation must block before planning')
    monkeypatch.setattr(runner, 'plan_for', forbidden_plan)
    with pytest.raises(FileExistsError):
        asyncio.run(runner.run_batch('gate', 'E6', concurrency, tag=tag))
    assert marker.read_text() == original
    assert not Path('results').exists()


def test_gate_reservation_is_exclusive_before_plan_and_survives_setup_failure(isolated_runner, monkeypatch):
    runner = isolated_runner
    marker = Path('logs/p2d3_gate_calls.json')
    calls = []
    def failing_plan(*args, **kwargs):
        calls.append(args)
        assert marker.is_file(), 'gate reservation must exist before plan construction'
        assert json.loads(marker.read_text())['status'] == 'started'
        # Verify the reservation is an exclusive file, rather than a later log.
        with pytest.raises(FileExistsError):
            with marker.open('x'):
                pass
        raise PlannedSetupFailure('synthetic planning failure before fresh cases')
    monkeypatch.setattr(runner, 'plan_for', failing_plan)
    with pytest.raises(PlannedSetupFailure):
        asyncio.run(runner.run_batch('gate', 'E6', 12, tag='first-tag'))
    retained = marker.read_bytes()
    with pytest.raises(FileExistsError):
        asyncio.run(runner.run_batch('gate', 'E6', 24, tag='replacement-tag'))
    assert len(calls) == 1
    assert marker.read_bytes() == retained
    assert not Path('results').exists()


def test_stress_reservation_keeps_tagged_marker_and_does_not_consume_gate(isolated_runner, monkeypatch):
    runner = isolated_runner
    monkeypatch.setattr(runner, 'plan_for', lambda *args: [{'seed': 1002000, 'tier': 'T1', 'policy': 'synthetic'}])
    def stop_before_execution(*args, **kwargs):
        raise PlannedSetupFailure('synthetic stop before binding or execution')
    monkeypatch.setattr(runner, 'binding', stop_before_execution)
    with pytest.raises(PlannedSetupFailure):
        asyncio.run(runner.run_batch('stress', 'E6', 24, count=1, tag='synthetic-stress-tag'))
    assert Path('logs/p2d3-synthetic-stress-tag_calls.json').is_file()
    assert not Path('logs/p2d3_gate_calls.json').exists()
