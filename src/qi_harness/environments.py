"""Separate v1 Env adapter over unchanged native tasksets and checked runtime."""
from contextlib import contextmanager
from contextvars import ContextVar
import importlib
from pathlib import Path
import tempfile
import verifiers.v1 as vf
from verifiers.v1.runtimes.docker import DockerConfig
from qi_runtime import CheckedRuntime,WORK,IMAGE
from .config import Limits
from .tools import ToolSession
from .harness import run_loop
from .prompts import messages_for

_CLIENT=ContextVar('p5a_host_client')
_LIMITS=ContextVar('p5a_episode_limits',default=Limits())
WINDOWS={'E1':[1002500,1002599],'E2':[1000800,1000899],'E5':[1005500,1005599],'E6':[1003500,1003599]}
FAMILIES={'E1':'e1_pit_backtest','E2':'e2_leakage_audit','E5':'e5_cost_realism','E6':'e6_data_traps'}
PLUGIN_IDS={'E1':'qi-e1','E2':'qi-leakage-audit','E5':'qi-cost-realism','E6':'qi-data-traps'}


def bindings():
    return {name:importlib.import_module('envs.'+family+'.v1_taskset') for name,family in FAMILIES.items()}


@contextmanager
def validation_context(environment):
    if environment not in FAMILIES:raise ValueError('supported main-branch tasksets only')
    # Native development windows require no guard replacement or frozen context.
    yield


class ModelHarnessConfig(vf.HarnessConfig):
    id:str='qi-harness'
    environment:str='E1'


class ModelHarness(vf.Harness[ModelHarnessConfig]):
    NEEDS_CONTAINER=True
    async def launch(self,ctx,trace,runtime,endpoint,secret,mcp_urls,data):
        if type(runtime) is not CheckedRuntime:raise ValueError('exact checked runtime required')
        environment=self.config.environment
        lifecycle=environment.lower()+'_lifecycle'
        trace.info[lifecycle].append('solver')
        tools=ToolSession(runtime,environment,_LIMITS.get(),messages_for(environment,data.prompt))
        loop=await run_loop(_CLIENT.get(),tools,_LIMITS.get())
        trace.info['p5a_harness']={**loop,'terminal':tools.terminal or not tools.submitted,'tools':tools.records,
                                   'provider_execution':'locked during P5a','environment':environment,'hack_monitors':tools.hack_monitors,'trace_refs':tools.trace_refs}
        return vf.ProgramResult(0,'','')


class ModelEnvConfig(vf.EnvConfig):
    environment:str='E1'
    agent:vf.AgentConfig=vf.AgentConfig(runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[]))


class ModelEnv(vf.Env[ModelEnvConfig]):
    def __init__(self,config):
        if config.environment not in FAMILIES:raise ValueError('unsupported taskset')
        if type(config.agent.runtime) is not DockerConfig or config.agent.runtime.image!=IMAGE or config.agent.runtime.workdir!='/work' or config.agent.runtime.allow:
            raise ValueError('runtime boundary override refused')
        super().__init__(config)
        if type(self._harnesses['agent']) is not ModelHarness:raise ValueError('model Env requires the bounded host harness')
        if self._harnesses['agent'].config.environment!=config.environment:raise ValueError('environment/harness mismatch')

    async def run(self,task,agents):
        module=bindings()[self.config.environment]
        if type(task) is not getattr(module,self.config.environment+'Task'):raise ValueError('native task type required')
        with tempfile.TemporaryDirectory(prefix='p5a-',dir=WORK) as directory:
            work=Path(directory);work.chmod(0o777);runtime=CheckedRuntime(work)
            try:
                await runtime.start()
                await agents.agent.run(task,runtime=runtime)
            finally:await runtime.stop()


async def run_model_episode(environment,seed,tier,client,limits=None):
    if environment not in WINDOWS or type(seed) is not int or not WINDOWS[environment][0]<=seed<=WINDOWS[environment][1] or tier not in ('T1','T2','T3','T4'):
        raise ValueError('outside committed P5a dev window or unsupported environment')
    limits=limits or Limits()
    module=bindings()[environment]
    native_config=getattr(module,environment+'Config')(id=PLUGIN_IDS[environment],first_seed=seed,count=1)
    config=ModelEnvConfig(environment=environment,taskset=native_config,
                         agent=vf.AgentConfig(harness=ModelHarnessConfig(environment=environment),runtime=DockerConfig(image=IMAGE,workdir='/work',allow=[])))
    env=ModelEnv(config)
    task=next(task for task in env.taskset if task.data.tier==tier)
    context=vf.ModelContext(model='p5a-mock-host-only',client=vf.EvalClientConfig(base_url='http://127.0.0.1:9/v1',api_key_var='P5A_DISABLED_FRAMEWORK_MODEL'))
    token=_CLIENT.set(client);limit_token=_LIMITS.set(limits)
    try:episode=await env.run_episode(task,context)
    finally:_LIMITS.reset(limit_token);_CLIENT.reset(token)
    if not episode.traces or not episode.traces[0].ok:
        # Preserve infrastructure classification, never print raw provider errors.
        from qi_runtime.infrastructure import _CURRENT
        state=_CURRENT.get();cause=state.framework_error if state is not None else None
        raise RuntimeError('P5a native lifecycle failed') from cause
    trace=episode.traces[0];evidence=dict(trace.info[environment.lower()+'_evidence'])
    harness=trace.info.get('p5a_harness',{})
    harness['reward']=evidence['reward']
    harness['seed']=seed;harness['tier']=tier
    harness['hack_monitors']['runtime_flagged']=bool(evidence.get('solver',{}).get('flagged'))
    harness['hack_monitors']['reexecution_failures']=sum(bool(evidence.get(stage,{}).get('container_id')) and
              (evidence[stage].get('exit_code',0)!=0 or evidence[stage].get('flagged',False) or evidence[stage].get('answer') is None)
              for stage in ('primary','replay'))
    from .transcripts import write_transcript
    root=Path('artifacts/p5a/transcripts');root.mkdir(parents=True,exist_ok=True)
    harness['transcript_ref']=write_transcript(root/(trace.id+'.json'),harness,max_bytes=limits.transcript_bytes)
    return {**evidence,'harness':harness}
