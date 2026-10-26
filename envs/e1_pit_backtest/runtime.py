"""E1-specific program/case adapters over the shared checked Docker runtime."""
from __future__ import annotations
import hashlib
import tempfile
from pathlib import Path
from qi_runtime import CheckedRuntime as E1Runtime,WORK,PRIVATE,IMAGE,MAX_SOURCE,cli,audit,execute_program
from .cases import expected,public_input
from .reward import checked_answer,score_pair

def reference_program(mode='exact'):
    source='''import json, sys
x=json.load(open(sys.argv[1]))
c=x['cutoff']; chosen={}
for a,p,d,v,rd,rv in sorted(x['rows'],key=lambda r:r[1]):
    if p<=c and d<=c:
        chosen[a]=rv if rd<=c else v
ids=sorted(a for a in chosen if x['active'][a])
v=[chosen[a] for a in ids]; m=sum(v)/len(v)
den=max(sum(abs(z-m) for z in v),1e-12)
r=sum((chosen[a]-m)/den*x['returns'][a] for a in ids)
'''
    source += {'exact':'','near_miss':'r*=1.00505\n','wrong_return':'r+=1\n','wrong_signal':'m+=1\n','wrong_both':'m+=1;r+=1\n'}[mode]
    return source+"print(json.dumps({'signal_mean':m,'backtest_return':r}))\n"


def replay_seed(seed,tier,source):
    start,width=(1001000,1000) if seed<1002000 else (1003000,7000)
    digest=hashlib.sha256(f'{seed}:{tier}:{source}'.encode()).digest()
    value=start+int.from_bytes(digest[:8],'big')%width
    return start+(value-start+1)%width if value==seed else value


async def execute_once(data,program):
    return await execute_program(data,program,checked_answer,namespace='e1')


async def evaluate_program(seed,tier,program):
    # Compatibility entry point: no caller-supplied execution evidence accepted.
    from .v1_taskset import run_policy
    return await run_policy(seed,tier,program)


async def exercise_boundary():
    data=public_input(1001000,'T1')
    probe=await execute_once(data,"import os;assert not os.path.exists('/home/kartik/qi-private');print('{}')")
    canary=await execute_once(data,"open('/opt/qi/canary').read();print('{}')")
    tamper=await execute_once(data,"open('/opt/qi/harness','w').write('bad')")
    network=await execute_once(data,"import socket;socket.create_connection(('192.0.2.1',443),timeout=.1)")
    # The runtime enforces inspection on every start; retain a concrete inspect as evidence.
    with tempfile.TemporaryDirectory(prefix='e1-',dir=WORK) as directory:
        work=Path(directory);work.chmod(0o777);runtime=E1Runtime(work)
        try:
            await runtime.start();snapshot=runtime.snapshot
        finally: await runtime.stop()
    cfg=snapshot['HostConfig']
    return {'network_none':cfg['NetworkMode']=='none','readonly_rootfs':cfg['ReadonlyRootfs'],
        'unprivileged':not cfg['Privileged'],'only_work_mount':len(snapshot['Mounts'])==1,
        'oracle_unreachable':probe['exit_code']==0,'canary_detected':canary['flagged'],
        'tamper_detected':tamper['flagged'],'network_attempt_failed':network['exit_code']!=0,
        'inspection':snapshot}
