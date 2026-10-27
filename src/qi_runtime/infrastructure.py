"""Attempt-local infrastructure evidence and a bounded whole-rollout retry."""
from __future__ import annotations
import contextvars
import asyncio
import dataclasses
import hashlib
import functools
import json
import math
import time
import traceback
import uuid
from pathlib import Path

class InfrastructureError(RuntimeError):pass
class DockerFailure(InfrastructureError):pass
class HostTimeout(InfrastructureError):pass
class PolicyFailure(RuntimeError):pass
class PolicyOutputLimit(ValueError):pass
class RetryLimitExceeded(RuntimeError):pass

ROOT=Path(__file__).resolve().parents[2]/'logs'/'p2d3_exceptions'
_CURRENT=contextvars.ContextVar('qi_runtime_attempt',default=None)

@dataclasses.dataclass
class Attempt:
    metadata:dict
    root:Path
    resources:list=dataclasses.field(default_factory=list)
    exceptions:list=dataclasses.field(default_factory=list)
    policy_evidence:bool=False
    runtimes:list=dataclasses.field(default_factory=list)

class RetryBudget:
    def __init__(self,planned):
        if type(planned) is not int or planned<=0:raise ValueError('positive planned count required')
        self.planned=planned;self.max_retries=planned//200;self.used=0
    def reserve(self):
        if self.used>=self.max_retries:raise RetryLimitExceeded('fixed 0.5 percent retry limit reached')
        self.used+=1

def chain(error):
    seen=set();todo=[error]
    while todo:
        item=todo.pop()
        if id(item) in seen:continue
        seen.add(id(item));yield item
        if item.__cause__ is not None:todo.append(item.__cause__)
        if item.__context__ is not None:todo.append(item.__context__)
        if isinstance(item,BaseExceptionGroup):todo.extend(item.exceptions)

def classify_exception(error,policy_evidence=False):
    if policy_evidence or any(isinstance(e,(PolicyFailure,PolicyOutputLimit)) for e in chain(error)):return 'policy'
    if any(isinstance(e,InfrastructureError) for e in chain(error)):return 'infrastructure'
    return 'unknown'

def record_exception(error,root=None,metadata=None):
    current=_CURRENT.get();folder=Path(root or (current.root if current else ROOT));folder.mkdir(parents=True,exist_ok=True)
    identity=uuid.uuid4().hex
    # No locals or environment values. Preserve both cause and implicit context,
    # including suppressed context, rather than relying on the final message.
    rendered='\n\n'.join(''.join(traceback.format_exception(type(e),e,e.__traceback__,chain=False)) for e in chain(error))
    payload=rendered.encode();parts=[]
    for offset in range(0,max(len(payload),1),262144):
        path=folder/f'{identity}-{offset//262144:03d}.txt';path.write_bytes(payload[offset:offset+262144]);parts.append(str(path))
    item={'id':identity,'metadata':dict(metadata or (current.metadata if current else {})),
        'kind':classify_exception(error,bool(current and current.policy_evidence)),
        'types':[type(e).__name__ for e in chain(error)],'message_previews':[str(e)[:2000] for e in chain(error)],
        'full_traceback_parts':parts,'traceback_sha256':hashlib.sha256(payload).hexdigest()}
    (folder/f'{identity}.json').write_text(json.dumps(item,sort_keys=True,indent=2)+'\n')
    if current:current.exceptions.append(item)
    return item

def note_policy():
    current=_CURRENT.get()
    if current:current.policy_evidence=True

def track_runtime(runtime):
    current=_CURRENT.get()
    if current:current.runtimes.append(runtime)

def note_resource(name,container_id=None,event='created'):
    current=_CURRENT.get()
    if current:current.resources.append({'name':name,'container_id':container_id,'event':event})

def _resource_keys(resources):
    return {str(v[k]) for v in resources for k in ('name','container_id') if v.get(k)}

async def run_with_retry(call,metadata=None,ledger=None,journal_root=None):
    if ledger is None:raise ValueError('fixed retry budget is required')
    attempts=[];prior=set()
    for number in (0,1):
        state=Attempt(dict(metadata or {},attempt=number),Path(journal_root or ROOT));token=_CURRENT.set(state);started=time.perf_counter();value=None;error=None
        try:value=await call()
        except (Exception,asyncio.CancelledError) as e:
            error=e;record_exception(e)
        finally:
            try:
                cleanup_errors=[]
                for runtime in state.runtimes:
                    if runtime._container and not runtime._stopped:
                        try:await runtime.stop()
                        except (Exception,asyncio.CancelledError) as cleanup:
                            cleanup_errors.append(cleanup);record_exception(cleanup)
                cancelled_cleanup=next((e for e in cleanup_errors if isinstance(e,asyncio.CancelledError)),None)
                if cancelled_cleanup is not None:error=cancelled_cleanup
                elif cleanup_errors and error is None:error=cleanup_errors[0]
            finally:
                _CURRENT.reset(token)
        keys=_resource_keys(state.resources);overlap=bool(keys&prior);prior|=keys
        kind='complete'
        if error:
            kinds=[e['kind'] for e in state.exceptions]
            kind='policy' if state.policy_evidence else 'infrastructure' if 'infrastructure' in kinds else 'unknown'
        cleanup_complete=all(not v._container or v._stopped for v in state.runtimes)
        if not cleanup_complete:
            kind='policy' if state.policy_evidence else 'infrastructure'
            error=error or DockerFailure('attempt cleanup incomplete')
        if isinstance(error,asyncio.CancelledError):
            kind='policy' if state.policy_evidence else 'unknown'
        if overlap:
            kind='unknown';error=RuntimeError('retry reused a runtime name or container ID')
            state.exceptions.append(record_exception(error,root=state.root,metadata=state.metadata))
        attempt={'attempt':number,'elapsed_seconds':time.perf_counter()-started,'kind':kind,'resources':state.resources,
            'exceptions':state.exceptions,'policy_evidence':state.policy_evidence,'resource_overlap':overlap,'cleanup_complete':cleanup_complete}
        attempts.append(attempt)
        if error is None:return {'value':value,'attempts':attempts,'complete':True,'retried':number==1,'terminal_kind':None}
        if kind!='infrastructure' or number==1 or not cleanup_complete:return {'value':({'reward':0.,'flagged':True,'incomplete':True} if kind=='policy' else None),'attempts':attempts,'complete':False,'retried':number==1,'terminal_kind':kind}
        try:ledger.reserve()
        except RetryLimitExceeded as e:
            attempt['retry_budget_error']=str(e)
            return {'value':None,'attempts':attempts,'complete':False,'retried':False,'terminal_kind':'retry_limit'}
    raise AssertionError('unreachable')

def install_rollout_diagnostics():
    from verifiers.v1.rollout import Rollout
    if getattr(Rollout.fail,'_qi_diagnostics',False):return
    original=Rollout.fail
    original_open=Rollout.open
    def guard_origin(error,method):
        # The final traceback frame must be the installed framework method,
        # never a solver/scorer exception with coincidentally similar wording.
        tail=error.__traceback__
        while tail is not None and tail.tb_next is not None:tail=tail.tb_next
        return type(error) is ValueError and tail is not None and tail.tb_frame.f_code is method.__code__
    def record_lifetime(error,origin):
        typed=InfrastructureError('trusted framework borrowed-runtime lifetime guard')
        typed.__cause__=error
        record_exception(typed,metadata={'origin':origin,**(_CURRENT.get().metadata if _CURRENT.get() else {})})
    @functools.wraps(original_open)
    async def open(self):
        borrowed_stopped=not self._owns_runtime and self.runtime is not None and self.runtime.stopped
        try:return await original_open(self)
        except (Exception,asyncio.CancelledError) as error:
            if borrowed_stopped and guard_origin(error,original_open):record_lifetime(error,'Rollout.open.lifetime_guard')
            else:record_exception(error,metadata={'origin':'Rollout.open',**(_CURRENT.get().metadata if _CURRENT.get() else {})})
            raise
    def fail(self,error):
        from qi_runtime import CheckedRuntime
        record_exception(error,metadata={'origin':'Rollout.fail',**(_CURRENT.get().metadata if _CURRENT.get() else {})})
        runtime=self.runtime
        # This project has deliberately transferred/destroyed its solver before
        # host scoring. Preserve the scorer's real exception at that boundary;
        # retain upstream lifetime guards everywhere else.
        timing=self.trace.timing
        closed_scoring=(type(runtime) is CheckedRuntime and runtime._stopped and self._closed
                        and bool(timing.finalize.end) and bool(timing.scoring.start))
        owned=self._owns_runtime
        borrowed_stopped=not owned and runtime is not None and runtime.stopped and not closed_scoring
        try:
            if closed_scoring:self._owns_runtime=True
            return original(self,error)
        except Exception as secondary:
            if borrowed_stopped and guard_origin(secondary,original):record_lifetime(secondary,'Rollout.fail.lifetime_guard')
            else:record_exception(secondary)
            raise
        finally:self._owns_runtime=owned
    fail._qi_diagnostics=True;fail._qi_original=original;Rollout.fail=fail
    open._qi_diagnostics=True;open._qi_original=original_open;Rollout.open=open


def journal_boundary(fn):
    @functools.wraps(fn)
    async def wrapped(*args,**kwargs):
        try:return await fn(*args,**kwargs)
        except Exception as error:
            record_exception(error,metadata={'origin':fn.__qualname__,**(_CURRENT.get().metadata if _CURRENT.get() else {})})
            raise
    return wrapped
