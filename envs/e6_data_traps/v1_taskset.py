"""E6 v1 Taskset, checked Env and scripted validation Harness plugins."""
from __future__ import annotations
import hashlib
import json
import tempfile
from pathlib import Path

import verifiers.v1 as vf
from pydantic import Field
from verifiers.v1.runtimes.docker import DockerConfig

from qi_runtime import CheckedRuntime as E6Runtime,WORK,PRIVATE,MAX_SOURCE,IMAGE
from .runtime import execute_once,reference_program,replay_seed
from .cases import public_input,make_case

from .reward import score_pair,error_terms
from qi.gen import generator_version_hash

TIERS=('T1','T2','T3','T4')


def annotate(record,truth):
    record['errors']=error_terms(record,truth)
    record['false_positive']=bool(record.get('answer') and set(record['answer']['anomalies'])-set(truth['anomalies']))
    if record['errors'] is not None and not __import__('math').isfinite(record['errors'][0]):record['errors']=None


class E6Data(vf.TaskData):
    seed:int
    tier:str


class E6Config(vf.TasksetConfig):
    first_seed:int=1_007_000
    count:int=Field(default=50,ge=1,le=500)


class E6Task(vf.Task[E6Data,vf.State]):
    NEEDS_CONTAINER=True

    async def setup(self,trace,runtime):
        if type(runtime) is not E6Runtime or runtime.snapshot is None:
            raise ValueError('E6 requires the inspected E6Runtime; generic runtimes are refused')
        self._trace_id=trace.id;self._source=None;self._source_hash=None;self._solver=runtime
        case=make_case(self.data.seed,self.data.tier);self._public=case['public'];self._truth=case['truth']
        oracle=json.dumps({'environment':'E6','generator_version_hash':generator_version_hash(),'seed':self.data.seed,'tier':self.data.tier,'truth':self._truth},sort_keys=True).encode()
        self._oracle_sha=hashlib.sha256(oracle).hexdigest()
        PRIVATE.mkdir(mode=0o700,exist_ok=True)
        path=PRIVATE/f'e6-p2d-case-{self._oracle_sha}.json';path.write_bytes(oracle);path.chmod(0o600)
        trace.info['e6_lifecycle']=['setup']
        await runtime.write('/work/input.json',json.dumps(self._public,sort_keys=True).encode())

    async def finalize(self,trace,runtime):
        if runtime is not getattr(self,'_solver',None) or trace.id!=self._trace_id:
            raise ValueError('rollout provenance mismatch')
        trace.info['e6_lifecycle'].append('finalize')
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
        trace.info['e6_lifecycle'].append('score')
        empty={'answer':None,'flagged':True,'exit_code':-1,'container_id':None,'computed':None,'errors':None}
        if self._source is None or self._solver_record['flagged']:
            result={'reward':0.,'flagged':True,'primary':empty,'replay':empty,'replay_seed':None}
        else:
            fresh=replay_seed(self.data.seed,self.data.tier,self._source)
            fresh_data=public_input(fresh,self.data.tier)
            truth=self._truth;fresh_truth=make_case(fresh,self.data.tier)['truth']
            primary=await execute_once(self._public,self._source)
            replay=await execute_once(fresh_data,self._source)
            annotate(primary,truth);annotate(replay,fresh_truth)
            result={'reward':score_pair(primary,replay,truth,fresh_truth),'flagged':primary['flagged'] or replay['flagged'],
                    'primary':primary,'replay':replay,'replay_seed':fresh}
            token=hashlib.sha256(f'{self.data.seed}:{self.data.tier}:{self._source}'.encode()).hexdigest()
            PRIVATE.mkdir(mode=0o700,exist_ok=True)
            path=PRIVATE/f'e6-p2d-{token}.json'
            path.write_text(json.dumps({'seed':self.data.seed,'tier':self.data.tier,'replay_seed':fresh,
                'truth':truth,'replay_truth':fresh_truth},sort_keys=True));path.chmod(0o600)
        result['oracle_sha256']=self._oracle_sha
        result['source_sha256']=self._source_hash
        result['solver']=self._solver_record
        result['lifecycle']=list(trace.info['e6_lifecycle'])
        self.last_result=result
        trace.info['e6_evidence']=result
        return result['reward']

    async def scripted(self,source):
        return await run_policy(self.data.seed,self.data.tier,source)


class E6Taskset(vf.Taskset[E6Task,E6Config]):
    def load(self):
        if not (1007000<=self.config.first_seed and self.config.first_seed+self.config.count<=1010000):
            raise ValueError('design/fresh gate dev seeds only')
        for tier in TIERS:
            for seed in range(self.config.first_seed,self.config.first_seed+self.config.count):
                yield E6Task(E6Data(seed=seed,tier=tier,name=f'E6-{tier}-{seed}',network_allow=[],workdir='/work',
                    prompt='Write /work/program.py reading /work/input.json. Reconcile the full listing/session universe from audited returns, anchors, registry and corporate actions. Repair quotes, flag only genuinely corrupted quote record_ids including duplicate copies. Legitimate splits, identifiers, delistings and large moves are not anomalies. Print universe rows and anomaly record_ids. Source is reexecuted on a fresh seed; ticker alone is not identity.'))


class E6HarnessConfig(vf.HarnessConfig):
    id:str='qi-data-traps'
    source:str=Field(default_factory=reference_program)


class E6Harness(vf.Harness[E6HarnessConfig]):
    NEEDS_CONTAINER=True
    async def launch(self,ctx,trace,runtime,endpoint,secret,mcp_urls,data):
        if type(runtime) is not E6Runtime: raise ValueError('checked runtime required')
        trace.info['e6_lifecycle'].append('solver')
        try:
            await runtime.write('/work/program.py',self.config.source.encode())
            solved=await runtime.run(['python','-I','-B','/work/program.py','/work/input.json'],{})
            if solved.exit_code!=0: runtime.flagged=True
        except ValueError:
            runtime.flagged=True
        # Solver failures remain data and receive zero in the Task reward. No model call.
        return vf.ProgramResult(0,'','')


class E6EnvConfig(vf.EnvConfig):
    agent:vf.AgentConfig=vf.AgentConfig(runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[]))


class E6Env(vf.Env[E6EnvConfig]):
    def __init__(self,config):
        super().__init__(config)
        if type(self._harnesses['agent']) is not E6Harness:
            raise ValueError('Only the checked E6 scripted harness is supported in P2d; model harnesses require a later budget-gated integration')
        if type(config.agent.runtime) is not DockerConfig:
            raise ValueError('E6 requires checked local Docker execution')
        if config.agent.runtime.image!=IMAGE or config.agent.runtime.workdir!='/work' or config.agent.runtime.allow:
            raise ValueError('E6 refuses runtime placement or network overrides')

    async def run(self,task,agents):
        if type(task) is not E6Task: raise ValueError('E6 tasks only')
        with tempfile.TemporaryDirectory(prefix='e6-',dir=WORK) as directory:
            work=Path(directory);work.chmod(0o777);runtime=E6Runtime(work)
            try:
                await runtime.start()
                await agents.agent.run(task,runtime=runtime)
            finally: await runtime.stop()


async def run_policy(seed,tier,source):
    config=E6EnvConfig(taskset=E6Config(id='qi-data-traps',first_seed=seed,count=1),
        agent=vf.AgentConfig(harness=E6HarnessConfig(source=source),runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[])))
    # Use the same public factory used by the CLI, not an alternate validation path.
    env=vf.load_environment(config)
    task=next(task for task in env.taskset if task.data.tier==tier)
    ctx=vf.ModelContext(model='scripted-no-model',client=vf.EvalClientConfig(base_url='http://127.0.0.1:9/v1',api_key_var='QI_DISABLED_MODEL_API'))
    episode=await env.run_episode(task,ctx)
    if not episode.traces or not episode.traces[0].ok:
        errors=[e.message for e in episode.errors]
        errors.extend(e.message for t in episode.traces for e in t.errors)
        raise RuntimeError('checked E6 rollout failed: '+'; '.join(errors))
    return episode.traces[0].info['e6_evidence']
