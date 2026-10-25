"""E1 v1 Taskset, checked Env and scripted validation Harness plugins."""
from __future__ import annotations
import hashlib
import json
import tempfile
from pathlib import Path

import verifiers.v1 as vf
from pydantic import Field
from verifiers.v1.runtimes.docker import DockerConfig

from .runtime import E1Runtime,WORK,PRIVATE,MAX_SOURCE,IMAGE,execute_once,reference_program,replay_seed
from .cases import public_input,expected
from .reward import score_pair

TIERS=('T1','T2','T3','T4')


class E1Data(vf.TaskData):
    seed:int
    tier:str


class E1Config(vf.TasksetConfig):
    first_seed:int=1_001_000
    count:int=Field(default=50,ge=1,le=500)


class E1Task(vf.Task[E1Data,vf.State]):
    NEEDS_CONTAINER=True

    async def setup(self,trace,runtime):
        if type(runtime) is not E1Runtime or runtime.snapshot is None:
            raise ValueError('E1 requires the inspected E1Runtime; generic runtimes are refused')
        self._trace_id=trace.id;self._source=None;self._solver=runtime
        self._public=public_input(self.data.seed,self.data.tier)
        trace.info['e1_lifecycle']=['setup']
        await runtime.write('/work/input.json',json.dumps(self._public,sort_keys=True).encode())

    async def finalize(self,trace,runtime):
        if runtime is not getattr(self,'_solver',None) or trace.id!=self._trace_id:
            raise ValueError('rollout provenance mismatch')
        trace.info['e1_lifecycle'].append('finalize')
        try:
            source=await runtime.read('/work/program.py',max_bytes=MAX_SOURCE)
            if len(source)>MAX_SOURCE: raise ValueError('source too large after transfer')
            self._source=source.decode('utf-8')
        except (ValueError,UnicodeError):
            runtime.flagged=True
        self._solver_record={'container_id':runtime.info.id,'flagged':runtime.flagged,
            'image':runtime.snapshot['Image'],'commands':list(runtime.commands)}
        await runtime.stop()

    @vf.reward
    async def integrity(self,trace):
        if trace.id!=getattr(self,'_trace_id',None) or not self._solver.stopped:
            return 0.
        trace.info['e1_lifecycle'].append('score')
        empty={'answer':None,'flagged':True,'exit_code':-1,'container_id':None}
        if self._source is None or self._solver_record['flagged']:
            result={'reward':0.,'flagged':True,'primary':empty,'replay':empty,'replay_seed':None}
        else:
            fresh=replay_seed(self.data.seed,self.data.tier,self._source)
            fresh_data=public_input(fresh,self.data.tier)
            truth=expected(self._public);fresh_truth=expected(fresh_data)
            primary=await execute_once(self._public,self._source)
            replay=await execute_once(fresh_data,self._source)
            result={'reward':score_pair(primary,replay,truth,fresh_truth),'flagged':primary['flagged'] or replay['flagged'],
                    'primary':primary,'replay':replay,'replay_seed':fresh}
            token=hashlib.sha256(f'{self.data.seed}:{self.data.tier}:{self._source}'.encode()).hexdigest()
            PRIVATE.mkdir(mode=0o700,exist_ok=True)
            path=PRIVATE/f'e1-round2-{token}.json'
            path.write_text(json.dumps({'seed':self.data.seed,'tier':self.data.tier,'replay_seed':fresh,
                'truth':truth,'replay_truth':fresh_truth},sort_keys=True));path.chmod(0o600)
        result['solver']=self._solver_record
        result['lifecycle']=list(trace.info['e1_lifecycle'])
        self.last_result=result
        trace.info['e1_evidence']=result
        return result['reward']

    async def scripted(self,source):
        return await run_policy(self.data.seed,self.data.tier,source)


class E1Taskset(vf.Taskset[E1Task,E1Config]):
    def load(self):
        if not (1001000<=self.config.first_seed and self.config.first_seed+self.config.count<=1010000):
            raise ValueError('design/fresh gate dev seeds only')
        for tier in TIERS:
            for seed in range(self.config.first_seed,self.config.first_seed+self.config.count):
                yield E1Task(E1Data(seed=seed,tier=tier,name=f'E1-{tier}-{seed}',network_allow=[],workdir='/work',
                    prompt='Write /work/program.py, reading /work/input.json and printing signal_mean and backtest_return as JSON. Use fundamentals and revisions available by cutoff, filter active assets, demean and gross-normalize weights, and compute next-day return. Source is re-executed on a different seed.'))


class E1HarnessConfig(vf.HarnessConfig):
    id:str='qi-e1'
    source:str=Field(default_factory=reference_program)


class E1Harness(vf.Harness[E1HarnessConfig]):
    NEEDS_CONTAINER=True
    async def launch(self,ctx,trace,runtime,endpoint,secret,mcp_urls,data):
        if type(runtime) is not E1Runtime: raise ValueError('checked runtime required')
        trace.info['e1_lifecycle'].append('solver')
        try:
            await runtime.write('/work/program.py',self.config.source.encode())
            solved=await runtime.run(['python','-I','-B','/work/program.py','/work/input.json'],{})
            if solved.exit_code!=0: runtime.flagged=True
        except ValueError:
            runtime.flagged=True
        # Solver failures remain data and receive zero in the Task reward. No model call.
        return vf.ProgramResult(0,'','')


class E1EnvConfig(vf.EnvConfig):
    agent:vf.AgentConfig=vf.AgentConfig(runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[]))


class E1Env(vf.Env[E1EnvConfig]):
    def __init__(self,config):
        super().__init__(config)
        if type(self._harnesses['agent']) is not E1Harness:
            raise ValueError('Only the checked E1 scripted harness is supported in P2b; model harnesses require a later budget-gated integration')
        if type(config.agent.runtime) is not DockerConfig:
            raise ValueError('E1 requires checked local Docker execution')
        if config.agent.runtime.image!=IMAGE or config.agent.runtime.workdir!='/work' or config.agent.runtime.allow:
            raise ValueError('E1 refuses runtime placement or network overrides')

    async def run(self,task,agents):
        if type(task) is not E1Task: raise ValueError('E1 tasks only')
        with tempfile.TemporaryDirectory(prefix='e1-',dir=WORK) as directory:
            work=Path(directory);work.chmod(0o777);runtime=E1Runtime(work)
            try:
                await runtime.start()
                await agents.agent.run(task,runtime=runtime)
            finally: await runtime.stop()


async def run_policy(seed,tier,source):
    config=E1EnvConfig(taskset=E1Config(id='qi-e1',first_seed=seed,count=1),
        agent=vf.AgentConfig(harness=E1HarnessConfig(source=source),runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[])))
    # Use the same public factory used by the CLI, not an alternate validation path.
    env=vf.load_environment(config)
    task=next(task for task in env.taskset if task.data.tier==tier)
    ctx=vf.ModelContext(model='scripted-no-model',client=vf.EvalClientConfig(base_url='http://127.0.0.1:9/v1',api_key_var='QI_DISABLED_MODEL_API'))
    episode=await env.run_episode(task,ctx)
    if not episode.traces or not episode.traces[0].ok:
        errors=[e.message for e in episode.errors]
        errors.extend(e.message for t in episode.traces for e in t.errors)
        raise RuntimeError('checked E1 rollout failed: '+'; '.join(errors))
    return episode.traces[0].info['e1_evidence']
