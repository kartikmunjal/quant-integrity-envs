"""Concrete Verifiers v1 taskset with server-side replay scoring."""
from __future__ import annotations

import verifiers.v1 as vf
from pydantic import Field

from .runtime import evaluate_program
from .task import TIERS


class E1Data(vf.TaskData):
    seed: int
    tier: str


class E1Config(vf.TasksetConfig):
    first_seed: int = 1_000_400
    count: int = Field(default=50, ge=1, le=500)


class E1Task(vf.Task[E1Data, vf.State]):
    NEEDS_CONTAINER = True

    async def setup(self, trace, runtime):
        from .runtime import E1Runtime, public_input
        import json
        if not isinstance(runtime, E1Runtime):
            raise ValueError('E1 requires its inspected container runtime')
        await runtime.write('/work/input.json', json.dumps(public_input(self.data.seed, self.data.tier)).encode())

    async def finalize(self, trace, runtime):
        # Read source through Docker; no agent-supplied path is dereferenced on host.
        source = await runtime.read('/work/program.py')
        if len(source) > 100_000:
            raise ValueError('program too large')
        self._source = source.decode()
        self._solver_flagged = runtime.flagged
        await runtime.stop()

    @vf.reward
    async def integrity(self, trace):
        if hasattr(self, '_batch_result'):
            self.last_result = self._batch_result
            return self._batch_result['reward']
        source = getattr(self, '_source', None)
        if source is None:
            return 0.0
        result = await evaluate_program(self.data.seed, self.data.tier, source)
        if getattr(self, '_solver_flagged', False):
            result['flagged'] = True
            result['reward'] = 0.0
        self.last_result = result
        trace.info['e1_evidence'] = result
        return result['reward']

    async def scripted(self, source):
        """No-model validation through the framework's actual Task.score hooks."""
        import tempfile
        from pathlib import Path
        from .runtime import E1Runtime, WORK
        trace = vf.Trace(task=vf.TraceTask(type=type(self).__name__, data=self.data), agent=vf.AgentInfo(config=vf.AgentConfig()))
        with tempfile.TemporaryDirectory(prefix='e1-', dir=WORK) as directory:
            work = Path(directory)
            work.chmod(0o777)
            runtime = E1Runtime(work)
            try:
                await runtime.start()
                await self.setup(trace, runtime)
                await runtime.write('/work/program.py', source.encode())
                await runtime.run(['python', '-I', '-B', '/work/program.py', '/work/input.json'], {})
                await self.finalize(trace, runtime)
            finally:
                await runtime.stop()
        await self.score(trace)
        return self.last_result


class E1Taskset(vf.Taskset[E1Task, E1Config]):
    def load(self):
        if not (1_000_000 <= self.config.first_seed and self.config.first_seed+self.config.count <= 1_010_000):
            raise ValueError('P2b accepts dev seeds only')
        for tier in TIERS:
            for seed in range(self.config.first_seed, self.config.first_seed+self.config.count):
                yield E1Task(E1Data(seed=seed, tier=tier, name=f'E1-{tier}-{seed}', network_allow=[], workdir='/work',
                    prompt='Read /work/input.json. Write /work/program.py to print JSON with signal_mean and backtest_return. Use only fundamentals available at cutoff, including restatements available by cutoff. Filter active assets; demean and gross-normalize signals; compute next-day return. Submitted source is re-executed on a fresh dev case.'))
