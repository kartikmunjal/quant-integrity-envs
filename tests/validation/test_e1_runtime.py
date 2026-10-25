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
        partial = asyncio.run(evaluate_program(task.data.seed, task.data.tier, reference_program('near_miss')))
        assert 0 < partial['reward'] < exact['reward']


def test_actual_v1_lifecycle_retains_solver_evidence():
    import tempfile
    from pathlib import Path
    import verifiers.v1 as vf
    from envs.e1_pit_backtest.runtime import E1Runtime, WORK, reference_program
    from envs.e1_pit_backtest.v1_taskset import E1Taskset, E1Config

    async def run():
        task = next(iter(E1Taskset(E1Config(count=1))))
        assert (await task.scripted(reference_program()))['reward'] == 1.
        trace = vf.Trace(task=vf.TraceTask(type=type(task).__name__,data=task.data),agent=vf.AgentInfo(config=vf.AgentConfig()))
        with tempfile.TemporaryDirectory(prefix='e1-',dir=WORK) as directory:
            work=Path(directory); work.chmod(0o777)
            runtime=E1Runtime(work)
            try:
                await runtime.start()
                await task.setup(trace,runtime)
                # The read occurs before clean source is submitted, exercising the original gap.
                await runtime.run(['cat','/opt/qi/canary'],{})
                await runtime.write('/work/program.py',reference_program().encode())
                await task.finalize(trace,runtime)
                await task.score(trace)
                assert trace.rewards['integrity'].score == 0.
            finally:
                await runtime.stop()
    asyncio.run(run())
