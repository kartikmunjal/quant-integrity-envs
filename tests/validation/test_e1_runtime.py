"""Real Docker contracts, written before the runtime implementation."""
from __future__ import annotations

import asyncio
import os

import pytest

pytestmark = pytest.mark.skipif(os.environ.get('QI_REAL_SANDBOX') != '1', reason='requires approved Docker access and P2b directories')


def test_real_boundary_and_attacks():
    from envs.e1_pit_backtest.runtime import exercise_boundary
    result = asyncio.run(exercise_boundary())
    assert result['network_none']
    assert result['readonly_rootfs']
    assert result['unprivileged']
    assert result['only_work_mount']
    assert result['oracle_unreachable']
    assert result['canary_detected']
    assert result['tamper_detected']
    assert result['network_attempt_failed']


def test_real_taskset_replay_and_partial_credit():
    from envs.e1_pit_backtest.runtime import evaluate_program, reference_program
    from envs.e1_pit_backtest.v1_taskset import E1Taskset, E1Config
    tasks = list(E1Taskset(E1Config(count=1)))
    assert len(tasks) == 4
    for task in tasks:
        exact = asyncio.run(evaluate_program(task.data.seed, task.data.tier, reference_program()))
        assert exact['reward'] >= .95
        constant = asyncio.run(evaluate_program(task.data.seed, task.data.tier, "print('{\"signal_mean\":0,\"backtest_return\":0}')"))
        assert constant['reward'] <= .05
        partial = asyncio.run(evaluate_program(task.data.seed, task.data.tier, reference_program('wrong_return')))
        assert 0 < partial['reward'] < exact['reward']
