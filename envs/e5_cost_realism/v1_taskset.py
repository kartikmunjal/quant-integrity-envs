"""E5 v1 Taskset, checked Env and scripted validation Harness plugins."""
from __future__ import annotations
import hashlib
import json
import tempfile
from pathlib import Path

import verifiers.v1 as vf
from pydantic import Field
from verifiers.v1.runtimes.docker import DockerConfig

from qi_runtime import CheckedRuntime as E5Runtime,WORK,PRIVATE,MAX_SOURCE,IMAGE
from .runtime import execute_once,reference_program,replay_seed
from .cases import public_input
from .finance import canonical_weights,metrics
from .reward import score_pair,error_terms

TIERS=('T1','T2','T3','T4')


def annotate(record,data):
    import math
    answer=record.get('answer')
    if answer is None:
        record['computed']=None;record['oracle']=None;record['errors']=None
        return
    def clean(values):
        return {key:value if type(value) is bool or math.isfinite(value) else None for key,value in values.items()}
    record['computed']=clean(metrics(data,answer['weights']))
    record['oracle']=clean(metrics(data,canonical_weights(data)))
    errors=error_terms(record,data)
    record['errors']=errors if errors is None or all(math.isfinite(value) for value in errors) else None


class E5Data(vf.TaskData):
    seed:int
    tier:str


class E5Config(vf.TasksetConfig):
    first_seed:int=1_004_000
    count:int=Field(default=50,ge=1,le=500)


class E5Task(vf.Task[E5Data,vf.State]):
    NEEDS_CONTAINER=True

    async def setup(self,trace,runtime):
        if type(runtime) is not E5Runtime or runtime.snapshot is None:
            raise ValueError('E5 requires the inspected E5Runtime; generic runtimes are refused')
        self._trace_id=trace.id;self._source=None;self._source_hash=None;self._solver=runtime
        self._public=public_input(self.data.seed,self.data.tier)
        trace.info['e5_lifecycle']=['setup']
        await runtime.write('/work/input.json',json.dumps(self._public,sort_keys=True).encode())

    async def finalize(self,trace,runtime):
        if runtime is not getattr(self,'_solver',None) or trace.id!=self._trace_id:
            raise ValueError('rollout provenance mismatch')
        trace.info['e5_lifecycle'].append('finalize')
        try:
            source=await runtime.read('/work/program.py',max_bytes=MAX_SOURCE)
            if len(source)>MAX_SOURCE: raise ValueError('source too large after transfer')
            self._source_hash=hashlib.sha256(source).hexdigest()
            self._source=source.decode('utf-8')
        except (ValueError,UnicodeError):
            runtime.flagged=True
        self._solver_record={'container_id':runtime.info.id,'flagged':runtime.flagged,
            'image':runtime.snapshot['Image'],'commands':list(runtime.commands),'source_sha256':self._source_hash}
        await runtime.stop()

    @vf.reward
    async def integrity(self,trace):
        if trace.id!=getattr(self,'_trace_id',None) or not self._solver.stopped:
            return 0.
        trace.info['e5_lifecycle'].append('score')
        empty={'answer':None,'flagged':True,'exit_code':-1,'container_id':None,'computed':None,'errors':None}
        if self._source is None or self._solver_record['flagged']:
            result={'reward':0.,'flagged':True,'primary':empty,'replay':empty,'replay_seed':None}
        else:
            fresh=replay_seed(self.data.seed,self.data.tier,self._source)
            fresh_data=public_input(fresh,self.data.tier)
            truth=metrics(self._public,canonical_weights(self._public));fresh_truth=metrics(fresh_data,canonical_weights(fresh_data))
            primary=await execute_once(self._public,self._source)
            replay=await execute_once(fresh_data,self._source)
            annotate(primary,self._public);annotate(replay,fresh_data)
            result={'reward':score_pair(primary,replay,self._public,fresh_data),'flagged':primary['flagged'] or replay['flagged'],
                    'primary':primary,'replay':replay,'replay_seed':fresh}
            token=hashlib.sha256(f'{self.data.seed}:{self.data.tier}:{self._source}'.encode()).hexdigest()
            PRIVATE.mkdir(mode=0o700,exist_ok=True)
            path=PRIVATE/f'e5-p2c-{token}.json'
            path.write_text(json.dumps({'seed':self.data.seed,'tier':self.data.tier,'replay_seed':fresh,
                'truth':truth,'replay_truth':fresh_truth},sort_keys=True));path.chmod(0o600)
        result['source_sha256']=self._source_hash
        result['solver']=self._solver_record
        result['lifecycle']=list(trace.info['e5_lifecycle'])
        self.last_result=result
        trace.info['e5_evidence']=result
        return result['reward']

    async def scripted(self,source):
        return await run_policy(self.data.seed,self.data.tier,source)


class E5Taskset(vf.Taskset[E5Task,E5Config]):
    def load(self):
        if not (1004000<=self.config.first_seed and self.config.first_seed+self.config.count<=1010000):
            raise ValueError('design/fresh gate dev seeds only')
        for tier in TIERS:
            for seed in range(self.config.first_seed,self.config.first_seed+self.config.count):
                yield E5Task(E5Data(seed=seed,tier=tier,name=f'E5-{tier}-{seed}',network_allow=[],workdir='/work',
                    prompt='Write /work/program.py reading /work/input.json. Submit the full weights[session][asset] gross-signal path, net_sharpe and breakeven_holding_days. Demean and gross-normalize signals, then clip position/trade changes by capacity/notional without renormalizing. Charge half-spread plus square-root impact on opening, changes and terminal closing. The verifier computes metrics itself and re-executes source on a fresh seed. The precise holding definition is in input context; no cost_awareness self-attestation is accepted.'))


class E5HarnessConfig(vf.HarnessConfig):
    id:str='qi-cost-realism'
    source:str=Field(default_factory=reference_program)


class E5Harness(vf.Harness[E5HarnessConfig]):
    NEEDS_CONTAINER=True
    async def launch(self,ctx,trace,runtime,endpoint,secret,mcp_urls,data):
        if type(runtime) is not E5Runtime: raise ValueError('checked runtime required')
        trace.info['e5_lifecycle'].append('solver')
        try:
            await runtime.write('/work/program.py',self.config.source.encode())
            solved=await runtime.run(['python','-I','-B','/work/program.py','/work/input.json'],{})
            if solved.exit_code!=0: runtime.flagged=True
        except ValueError:
            runtime.flagged=True
        # Solver failures remain data and receive zero in the Task reward. No model call.
        return vf.ProgramResult(0,'','')


class E5EnvConfig(vf.EnvConfig):
    agent:vf.AgentConfig=vf.AgentConfig(runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[]))


class E5Env(vf.Env[E5EnvConfig]):
    def __init__(self,config):
        super().__init__(config)
        if type(self._harnesses['agent']) is not E5Harness:
            raise ValueError('Only the checked E5 scripted harness is supported in P2c; model harnesses require a later budget-gated integration')
        if type(config.agent.runtime) is not DockerConfig:
            raise ValueError('E5 requires checked local Docker execution')
        if config.agent.runtime.image!=IMAGE or config.agent.runtime.workdir!='/work' or config.agent.runtime.allow:
            raise ValueError('E5 refuses runtime placement or network overrides')

    async def run(self,task,agents):
        if type(task) is not E5Task: raise ValueError('E5 tasks only')
        with tempfile.TemporaryDirectory(prefix='e5-',dir=WORK) as directory:
            work=Path(directory);work.chmod(0o777);runtime=E5Runtime(work)
            try:
                await runtime.start()
                await agents.agent.run(task,runtime=runtime)
            finally: await runtime.stop()


async def run_policy(seed,tier,source):
    config=E5EnvConfig(taskset=E5Config(id='qi-cost-realism',first_seed=seed,count=1),
        agent=vf.AgentConfig(harness=E5HarnessConfig(source=source),runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[])))
    # Use the same public factory used by the CLI, not an alternate validation path.
    env=vf.load_environment(config)
    task=next(task for task in env.taskset if task.data.tier==tier)
    ctx=vf.ModelContext(model='scripted-no-model',client=vf.EvalClientConfig(base_url='http://127.0.0.1:9/v1',api_key_var='QI_DISABLED_MODEL_API'))
    episode=await env.run_episode(task,ctx)
    if not episode.traces or not episode.traces[0].ok:
        errors=[e.message for e in episode.errors]
        errors.extend(e.message for t in episode.traces for e in t.errors)
        from qi_runtime.infrastructure import _CURRENT
        state=_CURRENT.get()
        cause=state.framework_error if state is not None else None
        raise RuntimeError('checked E5 rollout failed: '+'; '.join(errors)) from cause
    return episode.traces[0].info['e5_evidence']
