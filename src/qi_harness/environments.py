"""Separate v1 Env adapter over unchanged native tasksets and checked runtime."""
from contextlib import contextmanager
from contextvars import ContextVar
import asyncio
from dataclasses import replace
import time
import uuid
import importlib
from pathlib import Path
import tempfile
import verifiers.v1 as vf
from verifiers.v1.runtimes.docker import DockerConfig
from qi_runtime import CheckedRuntime,WORK,IMAGE
from qi_runtime.infrastructure import HostTimeout,DockerFailure
from .config import Limits
from .tools import ToolSession
from .harness import run_loop
from .prompts import messages_for

_DEADLINE=ContextVar('p5a_model_deadline',default=None)
_CLIENT=ContextVar('p5a_host_client')
_ACTIVE=ContextVar('p5a_active_episode',default=None)
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


async def capture_solver_artifacts(runtime,environment):
    """Audited immutable transfer before removal; native hooks run afterwards.

    This per-instance read handoff is confined to exact native path/cap pairs.
    No host work path is reopened, and the exact runtime/provenance is retained.
    """
    original=runtime.read
    cache={}
    paths=[('/work/program.py',bindings()[environment].MAX_SOURCE)]
    if environment=='E2':paths.append(('/work/submission.json',500000))
    try:
        if environment!='E2' or not runtime.flagged:
            for path,cap in paths:
                try:cache[(path,cap)]=(await original(path,max_bytes=cap),None)
                except (ValueError,UnicodeError) as error:
                    cache[(path,cap)]=(None,error)
                    break  # Native finalize stops transfer on its first error.
    finally:
        await runtime.stop()
    if not runtime.stopped:raise DockerFailure('solver removal not confirmed')
    async def captured_read(path,max_bytes=None):
        if not runtime.stopped:raise DockerFailure('capture consumed before removal')
        if (path,max_bytes) not in cache:raise ValueError('no captured native artifact')
        value,error=cache[(path,max_bytes)]
        if error is not None:raise error
        return value
    runtime._p5a_original_read=original
    runtime.read=captured_read


def restore_solver_reads(runtime):
    if hasattr(runtime,'_p5a_original_read'):
        runtime.read=runtime._p5a_original_read
        del runtime._p5a_original_read


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
        active=_ACTIVE.get()
        if active is not None:active.update(tools=tools,trace_id=trace.id)

        limits=_LIMITS.get();deadline=_DEADLINE.get()
        remaining=limits.wall_seconds if deadline is None else deadline-time.monotonic()
        if remaining<=0:
            runtime.flagged=True
            loop={'reason':'wall_timeout','submitted':False,'reward':0.,'turns':0,
                  'input_tokens':0,'output_tokens':0,'total_tokens':0}
        else:loop=await run_loop(_CLIENT.get(),tools,replace(limits,wall_seconds=remaining))
        trace.info['p5a_harness']={**loop,'terminal':tools.terminal or not tools.submitted,'tools':tools.records,
                                   'provider_execution':'locked during P5a','environment':environment,'hack_monitors':tools.hack_monitors,'trace_refs':tools.trace_refs}
        try:await capture_solver_artifacts(runtime,environment)
        except BaseException as error:
            if active is not None:active['lifecycle_error']=error
            raise
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
            active=_ACTIVE.get()
            if active is not None:active['runtime']=runtime
            try:
                provision=asyncio.create_task(runtime.start())
                try:
                    async with asyncio.timeout_at(_DEADLINE.get()):await asyncio.shield(provision)
                except asyncio.CancelledError:
                    # A Docker client disconnect is not a joined daemon creation.
                    # Finish this adapter-owned start before attempting removal.
                    await provision
                    raise
                except TimeoutError as error:
                    await provision
                    raise HostTimeout('model provisioning deadline') from error
                original_setup=task.setup
                async def bounded_setup(trace,runtime):
                    try:
                        async with asyncio.timeout_at(_DEADLINE.get()):
                            return await original_setup(trace,runtime)
                    except TimeoutError as error:
                        failure=HostTimeout('model setup deadline')
                        if active is not None:active['lifecycle_error']=failure
                        raise failure from error
                task.setup=bounded_setup
                try:await agents.agent.run(task,runtime=runtime)
                finally:task.setup=original_setup
            finally:
                restore_solver_reads(runtime)
                try:
                    await runtime.stop()
                    if active is not None:active['cleanup_complete']=runtime.stopped
                except BaseException as error:
                    if active is not None:active['cleanup_error']=error
                    raise


async def execute_native(environment,seed,tier,client,limits):
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
    active=_ACTIVE.get()
    if active is not None and active.get('cleanup_error'):raise active['cleanup_error']
    if active is not None and active.get('lifecycle_error'):raise active['lifecycle_error']
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
    return {**evidence,'harness':harness,'native_graded':True}


async def run_model_episode(environment,seed,tier,client,limits=None):
    if environment not in WINDOWS or type(seed) is not int or not WINDOWS[environment][0]<=seed<=WINDOWS[environment][1] or tier not in ('T1','T2','T3','T4'):
        raise ValueError('outside committed P5a dev window or unsupported environment')
    limits=limits or Limits();started=time.monotonic();active={}
    token=_ACTIVE.set(active);deadline_token=_DEADLINE.set(started+limits.wall_seconds)
    try:
        # No whole-workflow timeout: grading is joined, never cancelled by the
        # model deadline or by cancellation of this caller.
        native=asyncio.create_task(execute_native(environment,seed,tier,client,limits))
        cancelled=False
        while True:
            try:
                result=await asyncio.shield(native)
                break
            except asyncio.CancelledError:
                if native.cancelled():raise
                cancelled=True
                # Further cancellation requests must not reach native grading.
                continue
        if cancelled:raise asyncio.CancelledError
        harness=result['harness'];harness.update(wall_seconds=time.monotonic()-started,environment=environment,seed=seed,tier=tier)
        budget=getattr(client,'budget',None)
        if getattr(client,'usage_unknown',False):cost=None
        elif budget is not None:cost=str(budget.book.cost(client.config.model,harness.get('input_tokens',0),harness.get('output_tokens',0)))
        else:cost='0'
        harness['cost_usd']=cost;result['cost_usd']=cost
        from .transcripts import write_transcript
        root=Path('artifacts/p5a/transcripts');root.mkdir(parents=True,exist_ok=True)
        identity=active.get('trace_id',uuid.uuid4().hex)
        harness['transcript_ref']=write_transcript(root/(identity+'.json'),harness,max_bytes=limits.transcript_bytes)
        return result
    finally:
        _DEADLINE.reset(deadline_token);_ACTIVE.reset(token)
