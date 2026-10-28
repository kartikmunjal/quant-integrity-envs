"""E2 ordinary verifiers v1 lifecycle with protected host grading."""
import hashlib
import json
import tempfile
from contextvars import ContextVar
from pathlib import Path
import verifiers.v1 as vf
from pydantic import Field
from verifiers.v1.runtimes.docker import DockerConfig
from qi_runtime import CheckedRuntime,WORK,PRIVATE,MAX_SOURCE,IMAGE
from qi.mutate.cases import make_case,digest,TIERS
from qi.mutate.reference import evaluate,relative_error
from .runtime import execute_once,reference_program,replay_seed,design_replay_seed,parse_submission,poison
from .reward import grade_record

FRESH_AUTHORIZED=ContextVar('e2_fresh_authorized',default=False)
EXPONENT=1  # Selected prospectively from [1,2,3] only after design diagnostics.


def guard(seed):
    if not 1000000<=seed<=1001499:raise ValueError('E2 design/primary ranges only')
    if seed>=1001000 and not FRESH_AUTHORIZED.get():raise ValueError('fresh E2 execution requires frozen one-shot gate context')


def prefix(output,cutoff,data):
    start=data['bounds'][2]
    return {'holdings':[p[:cutoff-start+1] for p in output['holdings']],
            'strategy_returns':[p[:max(0,cutoff-start-1)] for p in output['strategy_returns']],
            'returns':output['returns'][:max(0,cutoff-start-1)]}


class E2Data(vf.TaskData):
    seed:int
    tier:str

class E2Config(vf.TasksetConfig):
    first_seed:int=1000000
    count:int=Field(default=1,ge=1,le=500)

class E2Task(vf.Task[E2Data,vf.State]):
    NEEDS_CONTAINER=True
    async def setup(self,trace,runtime):
        guard(self.data.seed)
        if type(runtime) is not CheckedRuntime or runtime.snapshot is None:raise ValueError('checked E2 runtime required')
        self._trace_id=trace.id;self._solver=runtime;self._submission=None
        self._case=make_case(self.data.seed,self.data.tier)
        truth={'environment':'E2','seed':self.data.seed,'tier':self.data.tier,
               'generator_version_hash':self._case['generator_version_hash'],'truth':self._case['truth'],
               'clean':self._case['clean'],'clean_source':self._case['clean_source']}
        raw=json.dumps(truth,sort_keys=True).encode();self._oracle_sha=hashlib.sha256(raw).hexdigest()
        PRIVATE.mkdir(mode=0o700,exist_ok=True)
        path=PRIVATE/('e2-'+self._oracle_sha+'.json');path.write_bytes(raw);path.chmod(0o600)
        await runtime.write('/work/input.json',json.dumps(self._case['public'],sort_keys=True).encode())
        await runtime.write('/work/research.py',self._case['source'].encode())
        trace.info['e2_lifecycle']=['setup']

    async def finalize(self,trace,runtime):
        if runtime is not self._solver or trace.id!=self._trace_id:raise ValueError('E2 provenance mismatch')
        trace.info['e2_lifecycle'].append('finalize')
        self._source_sha=None
        try:
            raw=await runtime.read('/work/program.py',max_bytes=MAX_SOURCE)
            self._source_sha=hashlib.sha256(raw).hexdigest()
            self._submission=parse_submission(await runtime.read('/work/submission.json',max_bytes=500000))
        except (ValueError,UnicodeError):self._submission=None
        self._solver_record={'container_id':runtime.info.id,'image':runtime.snapshot['Image'],
                            'flagged':runtime.flagged,'source_sha256':self._source_sha,'commands':list(runtime.commands)}
        await runtime.stop()

    @vf.reward
    async def integrity(self,trace):
        if trace.id!=self._trace_id or not self._solver.stopped:return 0.
        trace.info['e2_lifecycle'].append('score')
        empty={'answer':None,'flagged':False,'exit_code':-1,'container_id':None}
        result={'primary':dict(empty),'replay':dict(empty),'poison':dict(empty),'replay_seed':None,
                'solver':self._solver_record,'findings':[], 'truth':self._case['truth'],
                'primary_error':1.,'replay_error':1.,'poison_error':1.,
                'schema_ok':False,'security_ok':not self._solver_record['flagged']}
        if self._submission is not None and not self._solver_record['flagged']:
            patch=self._submission['patched_source'];findings=self._submission['findings']
            fresh=(design_replay_seed if self.data.seed<1001000 else replay_seed)(self.data.seed,self.data.tier,patch)
            replay_case=make_case(fresh,'T4')
            replay_data=replay_case['data']
            poisoned,cutoff=poison(self._case['data'],self.data.seed)
            primary=await execute_once(self._case['data'],patch)
            replay=await execute_once(replay_data,patch)
            poisoned_record=await execute_once(poisoned,patch)
            primary_error=relative_error(primary['answer'],self._case['clean'])
            replay_error=relative_error(replay['answer'],replay_case['clean'])
            try:
                expected=prefix(self._case['clean'],cutoff,self._case['data'])
                poison_error=relative_error(prefix(poisoned_record['answer'],cutoff,self._case['data']),expected)
            except (KeyError,TypeError,IndexError):poison_error=1.
            result.update(primary=primary,replay=replay,poison=poisoned_record,replay_seed=fresh,
                          findings=findings,primary_error=primary_error,replay_error=replay_error,poison_error=poison_error,
                          schema_ok=all(r['answer'] is not None and r['exit_code']==0 for r in (primary,replay,poisoned_record)),
                          security_ok=not any(r['flagged'] for r in (primary,replay,poisoned_record)),
                          patch_sha256=hashlib.sha256(patch.encode()).hexdigest(),patched_source=patch)
        result['reward']=grade_record(result,EXPONENT)
        result.update(oracle_sha256=self._oracle_sha,source_sha256=self._source_sha,lifecycle=list(trace.info['e2_lifecycle']),
                      data_sha256=self._case['data_sha256'],generator_version_hash=self._case['generator_version_hash'],
                      mutations=self._case['mutations'],candidate_attempts=self._case['candidate_attempts'],
                      conditional_effects=self._case['conditional_effects'],research_source=self._case['source'])
        trace.info['e2_evidence']=result;self.last_result=result
        return result['reward']

class E2Taskset(vf.Taskset[E2Task,E2Config]):
    def load(self):
        for seed in range(self.config.first_seed,self.config.first_seed+self.config.count):
            guard(seed)
            for tier in TIERS:
                yield E2Task(E2Data(seed=seed,tier=tier,name=f'E2-{tier}-{seed}',network_allow=[],workdir='/work',
                    prompt='Audit /work/research.py using /work/input.json data and the declared causal contract. Write a solver /work/program.py that emits JSON findings [{family:F1..F6,line:positive integer}], patched_source. Patches must execute on new data; all required functional outputs must match the clean causal research contract. No private oracle access.'))

class E2HarnessConfig(vf.HarnessConfig):
    id:str='qi-leakage-audit'
    source:str=Field(default_factory=reference_program)

class E2Harness(vf.Harness[E2HarnessConfig]):
    NEEDS_CONTAINER=True
    async def launch(self,ctx,trace,runtime,endpoint,secret,mcp_urls,data):
        if type(runtime) is not CheckedRuntime:raise ValueError('checked runtime required')
        trace.info['e2_lifecycle'].append('solver')
        try:
            await runtime.write('/work/program.py',self.config.source.encode())
            result=await runtime.run(['python','-I','-B','/work/program.py','/work/input.json'],{})
            if result.exit_code:runtime.flagged=True
            await runtime.write('/work/submission.json',result.stdout.encode())
        except ValueError:runtime.flagged=True
        return vf.ProgramResult(0,'','')

class E2EnvConfig(vf.EnvConfig):
    agent:vf.AgentConfig=vf.AgentConfig(runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[]))

class E2Env(vf.Env[E2EnvConfig]):
    def __init__(self,config):
        super().__init__(config)
        if type(self._harnesses['agent']) is not E2Harness or type(config.agent.runtime) is not DockerConfig:raise ValueError('E2 checked local scripted architecture only')
        if config.agent.runtime.image!=IMAGE or config.agent.runtime.workdir!='/work' or config.agent.runtime.allow:raise ValueError('E2 boundary override')
    async def run(self,task,agents):
        if type(task) is not E2Task:raise ValueError('E2 only')
        with tempfile.TemporaryDirectory(prefix='e2-',dir=WORK) as directory:
            work=Path(directory);work.chmod(0o777);runtime=CheckedRuntime(work)
            try:
                await runtime.start();await agents.agent.run(task,runtime=runtime)
            finally:await runtime.stop()

async def run_policy(seed,tier,source):
    guard(seed)
    config=E2EnvConfig(taskset=E2Config(id='qi-leakage-audit',first_seed=seed,count=1),
        agent=vf.AgentConfig(harness=E2HarnessConfig(source=source),runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[])))
    env=vf.load_environment(config)
    task=next(t for t in env.taskset if t.data.tier==tier)
    ctx=vf.ModelContext(model='scripted-no-model',client=vf.EvalClientConfig(base_url='http://127.0.0.1:9/v1',api_key_var='QI_DISABLED_MODEL_API'))
    episode=await env.run_episode(task,ctx)
    if not episode.traces or not episode.traces[0].ok:
        raise RuntimeError('checked E2 rollout failed: '+'; '.join([e.message for e in episode.errors]+[e.message for t in episode.traces for e in t.errors]))
    return episode.traces[0].info['e2_evidence']
