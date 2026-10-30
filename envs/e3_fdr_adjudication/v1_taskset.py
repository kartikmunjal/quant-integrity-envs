"""Local scripted verifiers lifecycle with protected E3 truth and fresh replay."""
import hashlib
import json
import subprocess
import tempfile
from contextvars import ContextVar
from pathlib import Path

import verifiers.v1 as vf
from pydantic import Field
from verifiers.v1.runtimes.docker import DockerConfig
from qi_runtime import CheckedRuntime, WORK, MAX_SOURCE, IMAGE
from .cases import make_case, TIERS
from .reward import parse_submission, execution_reward, combine_executions
from .runtime import execute_once

FRESH_AUTHORIZED=ContextVar('e3_fresh_authorized',default=False)


def populations():
    path=Path('results/p3b2_screen.json')
    raw=path.read_bytes()
    if subprocess.check_output(['git','show','HEAD:results/p3b2_screen.json']) != raw:
        raise ValueError('screen must be committed before any policy')
    return json.loads(raw)['populations']


def guard(seed):
    lists=populations()
    if seed in lists['primary']:
        if not FRESH_AUTHORIZED.get():
            raise ValueError('fresh primary needs frozen one-shot context')
    elif seed not in lists['design']:
        raise ValueError('outside screened primary/design population')


def replay_seed(seed,tier):
    lists=populations()
    seeds=lists['replay']
    if not seeds:
        raise ValueError('empty replay population')
    return seeds[int.from_bytes(hashlib.sha256(f'E3:{seed}:{tier}'.encode()).digest()[:8],'big')%len(seeds)]


class E3Data(vf.TaskData):
    seed:int
    tier:str


class E3Config(vf.TasksetConfig):
    first_seed:int=1000000
    count:int=Field(default=1,ge=1,le=500)


class E3Task(vf.Task[E3Data,vf.State]):
    NEEDS_CONTAINER=True

    async def setup(self,trace,runtime):
        guard(self.data.seed)
        if type(runtime) is not CheckedRuntime or runtime.snapshot is None:
            raise ValueError('checked E3 runtime required')
        self._trace_id=trace.id
        self._solver=runtime
        self._case=make_case(self.data.seed,self.data.tier)
        self._program=None
        self._schema=False
        await runtime.write('/work/input.json',json.dumps(self._case['public'],sort_keys=True).encode())
        trace.info['e3_lifecycle']=['setup']

    async def finalize(self,trace,runtime):
        if runtime is not self._solver or trace.id!=self._trace_id:
            raise ValueError('E3 provenance mismatch')
        trace.info['e3_lifecycle'].append('finalize')
        try:
            if runtime.flagged:
                raise ValueError('flagged submission, no trusted transfer')
            self._program=(await runtime.read('/work/program.py',max_bytes=MAX_SOURCE)).decode()
            parse_submission(await runtime.read('/work/submission.json',max_bytes=65536),list(self._case['truth']))
            self._schema=True
        except (ValueError,UnicodeError):
            self._schema=False
        self._solver_record={'container_id':runtime.info.id,'image':runtime.snapshot['Image'],
                             'flagged':runtime.flagged,'commands':list(runtime.commands)}
        await runtime.stop()

    @vf.reward
    async def integrity(self,trace):
        if trace.id!=self._trace_id or not self._solver.stopped:
            return 0.
        trace.info['e3_lifecycle'].append('score')
        result={'solver':self._solver_record,'primary':None,'replay':None,'reward':0.,
                'schema_ok':self._schema,'security_ok':not self._solver_record['flagged'],
                'generator_version_hash':self._case['generator_version_hash'],
                'data_sha256':self._case['data_sha256'],'truth':self._case['truth'],
                'replay_truth':None,'replay_seed':None,'source_sha256':None}
        if self._schema and not self._solver_record['flagged'] and self._program is not None:
            fresh=replay_seed(self.data.seed,self.data.tier)
            replay_case=make_case(fresh,self.data.tier)
            primary=await execute_once(self._case['public'],self._program)
            replay=await execute_once(replay_case['public'],self._program)
            schema=all(record['answer'] is not None and record['exit_code']==0 for record in (primary,replay))
            safe=not any(record['flagged'] for record in (primary,replay))
            rewards=[]
            for record,case in ((primary,self._case),(replay,replay_case)):
                ids=list(case['truth'])
                rewards.append(execution_reward([record['answer'][key] for key in ids],list(case['truth'].values())) if record['answer'] is not None else 0.)
            result.update(primary=primary,replay=replay,schema_ok=schema,security_ok=safe,
                          replay_seed=fresh,replay_truth=replay_case['truth'],
                          execution_rewards=rewards,replay_data_sha256=replay_case['data_sha256'],
                          source_sha256=hashlib.sha256(self._program.encode()).hexdigest(),
                          reward=combine_executions(*rewards,valid_schema=schema,safe_execution=safe))
        result['lifecycle']=list(trace.info['e3_lifecycle'])
        trace.info['e3_evidence']=result
        return result['reward']


class E3Taskset(vf.Taskset[E3Task,E3Config]):
    def load(self):
        for seed in range(self.config.first_seed,self.config.first_seed+self.config.count):
            guard(seed)
            for tier in TIERS:
                yield E3Task(E3Data(seed=seed,tier=tier,name=f'E3-{tier}-{seed}',network_allow=[],workdir='/work',
                    prompt='Read /work/input.json. Write a Python analysis program /work/program.py accepting its JSON path as argv[1] and emitting a JSON object mapping every strategy id to its probability of being real. Correct for selection and correlation. The program will run on fresh data. No private oracle access.'))


class E3HarnessConfig(vf.HarnessConfig):
    id:str='qi-fdr-adjudication'
    source:str="print('{}')\n"


class E3Harness(vf.Harness[E3HarnessConfig]):
    NEEDS_CONTAINER=True
    async def launch(self,ctx,trace,runtime,endpoint,secret,mcp_urls,data):
        if type(runtime) is not CheckedRuntime:
            raise ValueError('checked E3 runtime required')
        trace.info['e3_lifecycle'].append('solver')
        await runtime.write('/work/program.py',self.config.source.encode())
        result=await runtime.run(['python','-I','-B','/work/program.py','/work/input.json'],{})
        if result.exit_code:
            runtime.flagged=True
        if not runtime.flagged:
            await runtime.write('/work/submission.json',result.stdout.encode())
        return vf.ProgramResult(0,'','')


class E3EnvConfig(vf.EnvConfig):
    agent:vf.AgentConfig=vf.AgentConfig(runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[]))


class E3Env(vf.Env[E3EnvConfig]):
    def __init__(self,config):
        super().__init__(config)
        if type(self._harnesses['agent']) is not E3Harness or type(config.agent.runtime) is not DockerConfig:
            raise ValueError('E3 checked scripted architecture only')
        if config.agent.runtime.image!=IMAGE or config.agent.runtime.workdir!='/work' or config.agent.runtime.allow:
            raise ValueError('E3 runtime boundary override')
    async def run(self,task,agents):
        if type(task) is not E3Task:
            raise ValueError('E3 tasks only')
        with tempfile.TemporaryDirectory(prefix='e3-',dir=WORK) as directory:
            work=Path(directory)
            work.chmod(0o777)
            runtime=CheckedRuntime(work)
            try:
                await runtime.start()
                await agents.agent.run(task,runtime=runtime)
            finally:
                await runtime.stop()


async def run_policy(seed,tier,source):
    guard(seed)
    config=E3EnvConfig(taskset=E3Config(id='qi-fdr-adjudication',first_seed=seed,count=1),
        agent=vf.AgentConfig(harness=E3HarnessConfig(source=source),runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[])))
    env=vf.load_environment(config)
    task=next(t for t in env.taskset if t.data.tier==tier)
    ctx=vf.ModelContext(model='scripted-no-model',client=vf.EvalClientConfig(base_url='http://127.0.0.1:9/v1',api_key_var='QI_DISABLED_MODEL_API'))
    episode=await env.run_episode(task,ctx)
    if not episode.traces or not episode.traces[0].ok:
        from qi_runtime.infrastructure import _CURRENT
        state=_CURRENT.get()
        cause=state.framework_error if state is not None else None
        raise RuntimeError('checked E3 rollout failed: '+'; '.join([e.message for e in episode.errors]+[e.message for t in episode.traces for e in t.errors])) from cause
    return episode.traces[0].info['e3_evidence']
