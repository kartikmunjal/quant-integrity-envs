"""E1 container execution. Only public inputs and submitted code cross the boundary."""
from __future__ import annotations

import asyncio
import hashlib
import json
import math
import re
import secrets
import tempfile
from pathlib import Path

import numpy as np
from verifiers.v1.runtimes.docker import DockerConfig, DockerRuntime
from verifiers.v1.runtimes.base import ProgramResult

from .task import _market

WORK = Path('/home/kartik/qi-sandbox')
PRIVATE = Path('/home/kartik/qi-private')
IMAGE = 'qi-e1-p2b:local'


async def cli(*args: str):
    proc = await asyncio.create_subprocess_exec('docker', *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    async def bounded(stream):
        data = bytearray()
        while chunk := await stream.read(65536):
            data.extend(chunk)
            if len(data) > 2_000_000:
                raise ValueError('container output limit exceeded')
        return data.decode(errors='replace')
    try:
        out, err, code = await asyncio.wait_for(asyncio.gather(bounded(proc.stdout), bounded(proc.stderr), proc.wait()), 20)
        return code, out, err
    finally:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()


class E1Runtime(DockerRuntime):
    """Verifiers Runtime implementation with literal network=none and one mount."""
    def __init__(self, workspace: Path):
        super().__init__(DockerConfig(image=IMAGE, workdir='/work', allow=[]))
        if workspace.is_symlink():
            raise ValueError('workspace must not be a symlink')
        self.workspace = workspace.resolve()
        self.flagged = False
        if self.workspace.parent != WORK:
            raise ValueError('unexpected workspace')
        self.snapshot = None

    async def start(self):
        self._container = self.name
        code, out, err = await cli('run', '-d', '--name', self.name,
            '--network', 'none', '--read-only', '--cap-drop', 'ALL',
            '--cap-add', 'SYS_PTRACE', '--cap-add', 'SETUID', '--cap-add', 'SETGID',
            '--security-opt', 'no-new-privileges', '--pids-limit', '32', '--memory', '128m',
            '--cpus', '1', '--mount', f'type=bind,source={self.workspace},target=/work',
            '--workdir', '/work', IMAGE, 'sleep', 'infinity')
        if code:
            raise RuntimeError(err)
        self._container = self.name
        self.info.id = out.strip()
        code, out, err = await cli('inspect', self.name)
        if code:
            raise RuntimeError(err)
        self.snapshot = json.loads(out)[0]
        cfg = self.snapshot['HostConfig']
        mounts = self.snapshot['Mounts']
        if not (cfg['NetworkMode'] == 'none' and cfg['ReadonlyRootfs'] and not cfg['Privileged']
                and len(mounts) == 1 and mounts[0]['Source'] == str(self.workspace)
                and mounts[0]['Destination'] == '/work'):
            raise RuntimeError('container boundary inspection failed')

    async def prepare_execution(self, routes):
        if routes:
            raise ValueError('E1 permits no network routes')

    async def teardown(self):
        if self._container:
            await cli('rm', '-f', self._container)
            self._stopped = True

    async def execute(self):
        return await cli('exec', self.name, 'strace', '-f', '-yy', '-s', '512', '-e', 'trace=%file,%network',
                         '-u', 'nobody', 'python', '-I', '-B', '/work/program.py', '/work/input.json')

    async def run(self, argv, env):
        if env:
            raise ValueError('E1 solver commands may not inject environment variables')
        code, out, err = await cli('exec', self.name, 'strace', '-f', '-yy', '-s', '512', '-e',
            'trace=%file,%network', '-u', 'nobody', *argv)
        self.flagged |= audit(err)
        return ProgramResult(code, out, err)

    async def open_process(self, argv, env):
        raise ValueError('E1 permits bounded run commands only')

    async def run_background(self, argv, env, log):
        raise ValueError('E1 does not permit background services')

    async def write(self, path, data):
        from pathlib import PurePosixPath
        target = PurePosixPath(path)
        if not target.is_absolute() or '..' in target.parts or not target.is_relative_to('/work'):
            raise ValueError('writes must target /work')
        await super().write(path, data)


def public_input(seed: int, tier: str):
    if not 1_000_000 <= seed <= 1_009_999:
        raise ValueError('P2b accepts dev seeds only')
    market = _market(seed)
    cutoff = {'T1':250, 'T2':315, 'T3':380, 'T4':440}[tier]
    rows = []
    for period in range(len(market.fundamental_period_end)):
        for asset in range(200):
            rows.append([asset, int(market.fundamental_period_end[period]),
                         int(market.fundamental_available_day[period, asset]),
                         float(market.fundamental_initial[period, asset]),
                         int(market.fundamental_restatement_day[period, asset]),
                         float(market.fundamental_restated[period, asset])])
    returns = market.returns[cutoff + 1]
    valid = market.active[cutoff] & market.active[cutoff+1] & np.isfinite(returns)
    return {'cutoff':cutoff, 'rows':rows, 'returns':[float(x) if math.isfinite(x) else None for x in returns], 'active':valid.tolist()}


def expected(data):
    """Host oracle: explicit as-of vintage selection, no solver helper used."""
    selected = {}
    for asset, period, available, initial, revised_day, revised in data['rows']:
        if period <= data['cutoff'] and available <= data['cutoff']:
            value = revised if revised_day <= data['cutoff'] else initial
            if asset not in selected or period > selected[asset][0]:
                selected[asset] = period, value
    ids = sorted(i for i in selected if data['active'][i])
    values = np.array([selected[i][1] for i in ids])
    mean = float(np.mean(values))
    centered = values - mean
    weights = centered / max(float(np.sum(np.abs(centered))), 1e-12)
    return {'signal_mean':mean, 'backtest_return':float(np.sum(weights * np.array([data['returns'][i] for i in ids])))}


def reference_program(mode='exact'):
    # Independent standard-library implementation, executed only inside Docker.
    return '''import json, sys, math
x=json.load(open(sys.argv[1]))
c=x['cutoff']; chosen={}
for a,p,d,v,rd,rv in sorted(x['rows'], key=lambda r:r[1]):
    if p<=c and d<=c:
        chosen[a]=rv if rd<=c else v
ids=sorted(a for a in chosen if x['active'][a])
v=[chosen[a] for a in ids]; m=sum(v)/len(v)
den=max(sum(abs(z-m) for z in v),1e-12)
r=sum((chosen[a]-m)/den*x['returns'][a] for a in ids)
''' + {'exact': '', 'wrong_return':'r += 1\n', 'wrong_signal':'m += 1\n', 'wrong_both':'r += 1; m += 1\n'}[mode] + "print(json.dumps({'signal_mean':m,'backtest_return':r}))\n"


def checked_answer(output):
    try:
        value = json.loads(output)
        if set(value) != {'signal_mean', 'backtest_return'}:
            return None
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in value.values()):
            return None
        return value
    except (ValueError, TypeError, OverflowError):
        return None


def audit(trace):
    # File syscalls are emitted by the privileged parent tracer, not solver flags.
    return any(name in trace for name in ('/opt/qi/canary', '/opt/qi/harness', 'qi-private'))


async def execute_once(data, program):
    if len(program.encode()) > 100_000:
        raise ValueError('program too large')
    with tempfile.TemporaryDirectory(prefix='e1-', dir=WORK) as directory:
        work = Path(directory)
        work.chmod(0o777)
        (work/'input.json').write_text(json.dumps(data, sort_keys=True))
        (work/'program.py').write_text(program)
        runtime = E1Runtime(work)
        try:
            await runtime.start()
            before = await cli('exec', runtime.name, 'sha256sum', '/opt/qi/harness')
            try:
                code, out, err = await runtime.execute()
            except (TimeoutError, ValueError):
                return {'answer':None, 'flagged':True, 'exit_code':-1, 'inspect':runtime.snapshot, 'trace_hash':None}
            after = await cli('exec', runtime.name, 'sha256sum', '/opt/qi/harness')
            flagged = audit(err) or before != after
            return {'answer':checked_answer(out) if code == 0 else None, 'flagged':flagged,
                    'exit_code':code, 'inspect':runtime.snapshot, 'trace_hash':hashlib.sha256(err.encode()).hexdigest()}
        finally:
            await runtime.stop()


def score_pair(primary, replay, truth, replay_truth):
    if primary['flagged'] or replay['flagged'] or primary['answer'] is None or replay['answer'] is None:
        return 0.0
    def matches(answer, target, key):
        return abs(answer[key]-target[key]) <= 1e-4*max(abs(target[key]),1e-12)
    correct = sum(matches(primary['answer'], truth, k) for k in truth)/2
    available = all(matches(replay['answer'], replay_truth, k) for k in truth)
    return .8*correct + .2*available


async def evaluate_program(seed, tier, program):
    data = public_input(seed, tier)
    # Deterministic fresh dev seed; exact replay provenance is stored host-side.
    digest = hashlib.sha256(f'{seed}:{tier}:{program}'.encode()).digest()
    replay_seed = 1_000_000 + int.from_bytes(digest[:8], 'big') % 10_000
    if replay_seed == seed:
        replay_seed = 1_000_000 + (replay_seed - 1_000_000 + 1) % 10_000
    replay_data = public_input(replay_seed, tier)
    truth, replay_truth = expected(data), expected(replay_data)
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    record = {'seed':seed, 'tier':tier, 'replay_seed':replay_seed, 'truth':truth, 'replay_truth':replay_truth}
    private_path = PRIVATE / ('e1-'+secrets.token_hex(12)+'.json')
    private_path.write_text(json.dumps(record, sort_keys=True))
    private_path.chmod(0o600)
    primary = await execute_once(data, program)
    replay = await execute_once(replay_data, program)
    return {'reward':score_pair(primary,replay,truth,replay_truth), 'flagged':primary['flagged'] or replay['flagged'],
            'replay_seed':replay_seed, 'primary':primary, 'replay':replay}


async def exercise_boundary():
    data = public_input(1_000_400, 'T1')
    oracle = await execute_once(data, "import os; assert not os.path.exists('/home/kartik/qi-private'); print('{}')")
    canary = await execute_once(data, "open('/opt/qi/canary').read(); print('{}')")
    tamper = await execute_once(data, "open('/opt/qi/harness','w').write('broken')")
    network = await execute_once(data, "import socket; socket.create_connection(('192.0.2.1',443),timeout=.2)")
    snap = oracle['inspect']; cfg = snap['HostConfig']
    return {'network_none':cfg['NetworkMode']=='none', 'readonly_rootfs':cfg['ReadonlyRootfs'],
            'unprivileged':not cfg['Privileged'], 'only_work_mount':len(snap['Mounts'])==1,
            'oracle_unreachable':oracle['exit_code']==0, 'canary_detected':canary['flagged'],
            'tamper_detected':tamper['flagged'], 'network_attempt_failed':network['exit_code'] != 0}


async def evaluate_batch(tasks, program):
    """Amortize Docker startup; each policy has a separate primary and fresh replay box.

    All public batch inputs are agent-visible. Protected answers never enter either box.
    """
    seeds = [t.data.seed for t in tasks]
    tiers = [t.data.tier for t in tasks]
    primary_data = [public_input(seed, tier) for seed, tier in zip(seeds, tiers)]
    replay_seeds = []
    for seed, tier in zip(seeds, tiers):
        digest = hashlib.sha256(f'{seed}:{tier}:{program}'.encode()).digest()
        replay_seed = 1_000_000 + int.from_bytes(digest[:8], 'big') % 10_000
        if replay_seed == seed:
            replay_seed = 1_000_000 + (replay_seed - 1_000_000 + 1) % 10_000
        replay_seeds.append(replay_seed)
    replay_data = [public_input(seed, tier) for seed, tier in zip(replay_seeds, tiers)]

    async def batch_box(data):
        with tempfile.TemporaryDirectory(prefix='e1-', dir=WORK) as directory:
            work = Path(directory)
            work.chmod(0o777)
            for index, value in enumerate(data):
                (work/f'case-{index}.json').write_text(json.dumps(value, sort_keys=True))
            wrapper = 'import sys\n' + f'for index in range({len(data)}):\n' + "    sys.argv=['program.py',f'/work/case-{index}.json']\n" + f"    exec(compile({program!r}, 'submitted.py', 'exec'), {{'__name__':'__main__'}})\n"
            (work/'program.py').write_text(wrapper)
            runtime = E1Runtime(work)
            try:
                await runtime.start()
                result = await runtime.run(['python','-I','-B','/work/program.py'], {})
                answers = [checked_answer(line) for line in result.stdout.splitlines()]
                if result.exit_code or len(answers) != len(data):
                    answers = [None]*len(data)
                return [{'answer':answer,'flagged':runtime.flagged} for answer in answers], runtime.snapshot
            finally:
                await runtime.stop()
    primary, snapshot = await batch_box(primary_data)
    replay, _ = await batch_box(replay_data)
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    provenance = []
    results = []
    for i, task in enumerate(tasks):
        truth = expected(primary_data[i]); replay_truth = expected(replay_data[i])
        result = {'reward':score_pair(primary[i],replay[i],truth,replay_truth),
                  'flagged':primary[i]['flagged'] or replay[i]['flagged'], 'replay_seed':replay_seeds[i]}
        # The task's decorated reward still goes through Task.score; only trusted host code sets evidence.
        task._batch_result = result
        results.append(result)
        provenance.append({'seed':seeds[i], 'tier':tiers[i], 'replay_seed':replay_seeds[i],
                           'truth':truth, 'replay_truth':replay_truth})
    token = hashlib.sha256((program+json.dumps(seeds)+json.dumps(tiers)).encode()).hexdigest()
    path = PRIVATE / f'e1-batch-{token}.json'
    path.write_text(json.dumps(provenance,sort_keys=True)); path.chmod(0o600)
    return results, snapshot
