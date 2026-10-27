"""Scoped seed admission and archived-reward replay for infrastructure regression."""
import contextlib
import functools
import hashlib
import json
from pathlib import Path
import subprocess
import types

ROOT=Path(__file__).resolve().parents[2]

def runtime_version_hash():
    digest=hashlib.sha256()
    for name in ('__init__.py','infrastructure.py','phase.py'):
        p=Path(__file__).parent/name;digest.update(name.encode()+b'\0'+p.read_bytes())
    return digest.hexdigest()

@contextlib.contextmanager
def e6_fresh_context():
    from envs.e6_data_traps import cases,runtime,v1_taskset
    original=cases._case;fn=original.__wrapped__;constants=fn.__code__.co_consts
    assert sum(type(v) is int and v==1004999 for v in constants)==1
    revised=fn.__code__.replace(co_consts=tuple(1006999 if type(v) is int and v==1004999 else v for v in constants))
    assert revised.co_code==fn.__code__.co_code
    expanded=functools.lru_cache(maxsize=128)(types.FunctionType(revised,fn.__globals__,fn.__name__,fn.__defaults__,fn.__closure__))
    def admitted(seed,tier):
        if 1005500<=seed<=1005999:raise ValueError('unreserved E6 seed gap')
        return expanded(seed,tier)
    previous_runtime=runtime.replay_seed;previous_task=v1_taskset.replay_seed
    def replay(seed,tier,source):
        if 1005000<=seed<=1005499:
            return 1006000+int.from_bytes(hashlib.sha256(f'E6:{seed}:{tier}:{source}'.encode()).digest()[:8],'big')%1000
        return previous_runtime(seed,tier,source)
    cases._case=admitted;runtime.replay_seed=replay;v1_taskset.replay_seed=replay
    try:yield
    finally:cases._case=original;runtime.replay_seed=previous_runtime;v1_taskset.replay_seed=previous_task

@contextlib.contextmanager
def historical_e6_context():
    from envs.e6_data_traps import v1_taskset
    freeze=json.loads((ROOT/'results/p2d_freeze.json').read_text());commit=freeze['implementation_commit']
    path='envs/e6_data_traps/reward.py';source=subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
    assert hashlib.sha256(source).hexdigest()==freeze['sources'][path]
    namespace={'__name__':'qi_runtime.archived_e6_reward'}
    exec(compile(source,commit+':'+path,'exec'),namespace)
    score=v1_taskset.score_pair;terms=v1_taskset.error_terms
    v1_taskset.score_pair=namespace['score_pair'];v1_taskset.error_terms=namespace['error_terms']
    try:yield
    finally:v1_taskset.score_pair=score;v1_taskset.error_terms=terms
