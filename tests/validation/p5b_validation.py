"""Independent P15 prospective live contracts and exact historical regressions.

No execution occurs without a committed source-bound plan and explicit opt-in.
Model actions are MockClient calls only; no provider/client credential is used.
"""
from __future__ import annotations
import argparse
import asyncio
from collections import Counter
from contextlib import ExitStack
from functools import lru_cache
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
ENVS=('E1','E2','E5','E6')
TIERS=('T1','T2','T3','T4')
FAMILIES={'E1':'e1_pit_backtest','E2':'e2_leakage_audit','E5':'e5_cost_realism','E6':'e6_data_traps'}
BOMB="import os,time\nfor _ in range(80):\n _pid=os.fork()\n if _pid==0:\n  time.sleep(30);os._exit(0)\n"
MODEL_WINDOWS={'E1':1002500,'E2':1000800,'E5':1005500,'E6':1003500}


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(path):
    raw=(ROOT/path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)
@lru_cache(maxsize=128)
def checked(path,expected):
    raw=(ROOT/path).read_bytes()
    if sha(raw)!=expected:raise ValueError('historical artifact hash mismatch')
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],stderr=subprocess.DEVNULL)


def sources():
    files={Path(__file__).resolve(),ROOT/'tests/validation/test_p5b_process_allowance.py',
           ROOT/'tests/validation/test_p5b_validation.py',
           ROOT/'results/p3a2_regression_plan.json.gz',ROOT/'results/p3a3_screen.json',
           ROOT/'results/p3a3-gate.json',ROOT/'results/p3a3-stress-c8.json',
           ROOT/'scripts/run_p3a3.py',ROOT/'scripts/p3a3_support.py',ROOT/'prereg.yaml'}
    for directory in ('src/qi_runtime','src/qi_harness','src/qi/gen','src/qi/mutate'):
        files.update((ROOT/directory).glob('*.py'))
    for family in FAMILIES.values():files.update((ROOT/'envs'/family).glob('*.py'))
    files.update((ROOT/'scripts').glob('e[156]_policies.py'))
    return {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(files)}


def historical_rows(summary_path):
    summary=load(summary_path);rows=[]
    for shard in summary['compact_shards']:
        raw=(ROOT/shard['path']).read_bytes()
        if sha(raw)!=shard['sha256']:raise ValueError('historical shard changed')
        rows.extend(json.loads(line) for line in gzip.decompress(raw).splitlines())
    return sorted(rows,key=lambda row:row['index'])


def regression_rows(environment):
    if environment!='E2':
        original=load('results/p3a2_regression_plan.json.gz')['environments'][environment]
        rows=[]
        for old in original:
            baseline=checked(old['baseline_path'],old['baseline_sha256'])[old['baseline_index']]
            value=baseline if 'reward' in baseline else baseline['value']
            if baseline['seed']!=old['seed'] or baseline['tier']!=old['tier'] or value['reward']!=old['reward']:
                raise ValueError('historical regression identity mismatch')
            rows.append({**old,'environment':environment,'kind':'regression',
                         'expected_reward':value['reward'],'expected_replay_seed':value['replay_seed']})
        if len(rows)!=1000:raise ValueError('exact historical1000 required')
        return rows
    cells={}
    for old in historical_rows('results/p3a3-gate.json'):
        cells.setdefault((old['tier'],old['policy']),[]).append(old)
    policies=sorted({policy for tier,policy in cells})
    if len(policies)!=32:raise ValueError('historical policy roster drift')
    rows=[]
    for tier in TIERS:
        for rank,policy in enumerate(policies):
            # Metadata-only, balanced250/tier; no reward-based selection.
            for old in cells[(tier,policy)][:8 if rank<26 else 7]:
                raw=checked(old['archive']['path'],old['archive']['sha256'])
                value=raw['run']['value']
                if value['reward']!=old['reward'] or value['replay_seed']!=old['replay_seed']:
                    raise ValueError('historical E2 raw/compact mismatch')
                rows.append({'environment':'E2','kind':'regression','policy':policy,'tier':tier,'seed':old['seed'],
                             'historical_index':old['index'],'baseline_archive':old['archive'],
                             'expected_reward':value['reward'],'expected_replay_seed':value['replay_seed']})
    if len(rows)!=1000:raise ValueError('exact E2 historical1000 required')
    return rows


def rows_for(mode,environment,concurrency):
    if mode=='regression':return regression_rows(environment)
    if mode=='e2-stress':
        return [{'kind':'normal','environment':'E2','tier':r['tier'],'seed':r['seed'],'policy':r['policy']}
                for r in historical_rows('results/p3a3-stress-c8.json')[:2000]]
    if mode=='probes':
        rows=[]
        for env in ENVS:
            for tier in TIERS:
                for stage in ('solver','primary','replay')+(('poison',) if env=='E2' else ()):
                    rows.append({'kind':'bomb','environment':env,'tier':tier,'seed':MODEL_WINDOWS[env],'stage':stage})
                rows.append({'kind':'forgery','environment':env,'tier':tier,'seed':MODEL_WINDOWS[env]})
        return rows
    rows=[]
    for i in range(concurrency*4):
        pair=i//2;env=ENVS[pair%4];tier=TIERS[(pair//4)%4]
        stages=('solver','primary','replay')+(('poison',) if env=='E2' else ())
        rows.append({'kind':'bomb' if i%2==0 else 'normal','environment':env,'tier':tier,
                     'seed':MODEL_WINDOWS[env],'stage':stages[(pair//4)%len(stages)],'policy':'oracle'})
    return rows


def make_plan(mode,environment,concurrency):
    if concurrency not in (8,12):raise ValueError('declared concurrency8or12 only')
    identity='E1/E2/E5/E6' if mode in ('probes','mixed') else 'E2' if mode=='e2-stress' else environment
    return {'phase':'P5b','independent_author':'/root/e1_review','mode':mode,'environment':identity,
            'concurrency':concurrency,'sources':sources(),'rows':rows_for(mode,environment,concurrency),
            'generator_version_hash':'eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921'}


def module(environment):return importlib.import_module('envs.'+FAMILIES[environment]+'.v1_taskset')
def policy_source(environment,policy,seed,tier):
    if environment=='E2':
        from envs.e2_leakage_audit.runtime import reference_program
        return reference_program(policy)
    policies=importlib.import_module('scripts.'+environment.lower()+'_policies')
    available,_,_=policies.policies()
    return policies.source_for(policy,seed,tier,available)


def stage_bomb_source(environment,stage,seed,tier):
    task=module(environment)
    primary=task.make_case(seed,tier)['data'] if environment=='E2' else task.public_input(seed,tier)
    primary_hash=sha(canonical(primary))
    if environment=='E2':
        from envs.e2_leakage_audit.runtime import poison
        poison_hash=sha(canonical(poison(primary,seed)[0]))
        condition={'primary':f'_digest=={primary_hash!r}', 'poison':f'_digest=={poison_hash!r}',
                   'replay':f'_digest not in ({primary_hash!r},{poison_hash!r})'}[stage]
    else:condition=f'_digest {"==" if stage=="primary" else "!="} {primary_hash!r}'
    guard=("import os,json,sys,hashlib\n_digest=hashlib.sha256(json.dumps(json.load(open(sys.argv[1])),"
           "sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()\n"
           f"if not os.path.exists('/work/p5b-solver-marker') and ({condition}):\n"+
           ''.join(' '+line+'\n' for line in BOMB.splitlines()))
    oracle=policy_source(environment,'oracle',seed,tier)
    if environment=='E2':
        target="print(json.dumps({'findings':findings,'patched_source':PATCH},allow_nan=False))"
        if oracle.count(target)!=1:raise ValueError('E2 native submission template drift')
        return oracle.replace(target,'PATCH='+repr(guard)+'+PATCH\n'+target)
    return guard+oracle


def exhaustion_commands(evidence):
    return [command for stage in ('solver','primary','replay','poison')
            for command in (evidence.get(stage) or {}).get('commands',[])
            if command.get('policy_outcome')=='process_allowance_exhausted']


async def model_bomb(row):
    from qi_harness.client import MockClient,Reply,ToolCall
    from qi_harness.environments import run_model_episode
    env=row['environment'];stage=row['stage']
    if stage=='solver':
        calls=(ToolCall('bomb','run_python',{'code':BOMB}),)
    else:
        source=stage_bomb_source(env,stage,row['seed'],row['tier'])
        calls=(ToolCall('marker','run_python',{'code':"open('/work/p5b-solver-marker','w').write('public solver marker')"}),
               ToolCall('submit','submit',{'source':source}))
    evidence=await run_model_episode(env,row['seed'],row['tier'],MockClient([Reply(tool_calls=calls)]))
    observed=evidence.get(stage) or {}
    positive=exhaustion_commands({stage:observed})
    passed=evidence['reward']==0 and observed.get('flagged') is True and bool(observed.get('container_id')) and bool(positive)
    return {'passed':passed,'evidence':evidence,'positive_host_exhaustion_records':positive}


async def forgery(row):
    from qi_runtime import CheckedRuntime,WORK
    from qi_runtime.process_allowance import host_pids_snapshot
    with tempfile.TemporaryDirectory(prefix='p5b-forgery-',dir=WORK) as directory:
        work=Path(directory);work.chmod(0o777);runtime=CheckedRuntime(work)
        try:
            await runtime.start();before=await host_pids_snapshot(runtime)
            result=await runtime.run(['python','-I','-B','-c',
                "open('/sys/fs/cgroup/pids.events','w').write('max 999999\\n')"],{})
            after=await host_pids_snapshot(runtime)
            passed=result.exit_code!=0 and before is not None and after is not None and before==after
            return {'passed':passed,'before':before,'after':after,'exit_code':result.exit_code,
                    'container_id':runtime.info.id,'commands':runtime.commands,'snapshot':runtime.snapshot}
        finally:await runtime.stop()


async def native(row):
    env=row['environment'];task=module(env)
    source=policy_source(env,row['policy'],row['seed'],row['tier'])
    # Existing historical contexts are installed once per batch, never nested
    # independently across concurrently interleaved tasks.
    token=task.FRESH_AUTHORIZED.set(True) if env=='E2' else None
    try:evidence=await task.run_policy(row['seed'],row['tier'],source)
    finally:
        if token is not None:task.FRESH_AUTHORIZED.reset(token)
    if row['kind']=='regression':
        passed=evidence['reward']==row['expected_reward'] and evidence.get('replay_seed')==row['expected_replay_seed']
    else:passed=evidence['reward']>=.95 if row.get('policy')=='oracle' else True
    passed &= not bool(exhaustion_commands(evidence))
    return {'passed':passed,'evidence':evidence,'reward':evidence['reward'],'replay_seed':evidence.get('replay_seed')}


def compact_evidence(evidence):
    if evidence is None:return None
    keep=('reward','replay_seed','flagged','schema_ok','security_ok','source_sha256','oracle_sha256')
    result={k:evidence[k] for k in keep if k in evidence}
    for stage in ('solver','primary','replay','poison'):
        if stage not in evidence:continue
        value=evidence[stage]
        if value is None:result[stage]=None;continue
        result[stage]={k:v for k,v in value.items() if k not in ('answer','computed','errors','raw_stdout','stdout','stderr')}
        result[stage]['answer_sha256']=sha(canonical(value.get('answer')))
    return result


async def execute(plan,output):
    from qi_runtime.infrastructure import RetryBudget,run_with_retry
    mode=plan['mode'];tag=output.stem;raw_root=ROOT/'artifacts/p5b'/tag
    raw_root.mkdir(parents=True,exist_ok=False)
    proof_root=output.with_suffix('');proof_root.mkdir(parents=True,exist_ok=False)
    rows=[];ledger=RetryBudget(len(plan['rows']));semaphore=asyncio.Semaphore(plan['concurrency']);stop=False
    started=time.monotonic()
    async def one(index,row):
        nonlocal stop
        async with semaphore:
            if stop:return
            if sources()!=plan['sources']:raise ValueError('source drift during validation')
            begin=time.monotonic();result={};error=None
            operation=model_bomb if row['kind']=='bomb' else forgery if row['kind']=='forgery' else native
            try:
                result=await run_with_retry(lambda:operation(row),metadata={'phase':'P5b','index':index,**row},
                    ledger=ledger,journal_root=raw_root/'exceptions')
            except Exception as failure:error=type(failure).__name__
            value=result.get('value') or {};attempts=result.get('attempts',[])
            cleanup=all(a['cleanup_complete'] for a in attempts)
            accounting=all(Counter(r['container_id'] for r in a['resources'] if r['event']=='created')==
                           Counter(r['container_id'] for r in a['resources'] if r['event']=='removed' and r['container_id']) for a in attempts)
            passed=bool(result.get('complete') and result.get('infrastructure_ok') and not result.get('retried')
                        and value.get('passed') is True and cleanup and accounting and error is None)
            if mode=='regression' and not passed:stop=True
            record={'index':index,**row,'passed':passed,'started_monotonic':begin,'ended_monotonic':time.monotonic(),
                    'result':result,'error':error}
            packed=gzip.compress(canonical(record),mtime=0);path=raw_root/f'{index:05d}.json.gz';path.write_bytes(packed)
            compact={k:v for k,v in record.items() if k!='result'}
            compact.update(raw={'path':str(path.relative_to(ROOT)),'bytes':len(packed),'sha256':sha(packed)},
                complete=result.get('complete',False),infrastructure_ok=result.get('infrastructure_ok',False),
                retried=result.get('retried',False),cleanup_complete=cleanup,resource_accounting=accounting,
                evidence=compact_evidence(value.get('evidence')),
                attempts=[{k:a[k] for k in ('attempt','kind','policy_evidence','cleanup_complete','resources')} for a in attempts])
            rows.append(compact)
            if len(rows)%25==0 or not passed:print(json.dumps({'mode':mode,'rows':len(rows),'failed':sum(not r['passed'] for r in rows),'retries':ledger.used}),flush=True)
    with ExitStack() as stack:
        if any(row['environment']=='E6' for row in plan['rows']):
            from qi_runtime.phase import e6_fresh_context
            stack.enter_context(e6_fresh_context())
        if any(row['environment']=='E2' for row in plan['rows']):
            from scripts.run_p3a3 import fresh_context
            stack.enter_context(fresh_context())
        await asyncio.gather(*(one(i,row) for i,row in enumerate(plan['rows'])))
    rows.sort(key=lambda r:r['index']);shards=[]
    for start in range(0,len(rows),25):
        group=rows[start:start+25];packed=gzip.compress(b'\n'.join(canonical(r) for r in group)+b'\n',mtime=0)
        if len(packed)>512*1024:raise ValueError('compact proof shard too large; raw records retained')
        path=proof_root/f'{len(shards):04d}.jsonl.gz';path.write_bytes(packed)
        shards.append({'path':str(path.relative_to(ROOT)),'bytes':len(packed),'sha256':sha(packed),'rows':len(group)})
    by_cell={}
    for r in rows:
        key='/'.join(str(r.get(k,'')) for k in ('environment','tier','kind','stage','policy'))
        c=by_cell.setdefault(key,{'rows':0,'passed':0});c['rows']+=1;c['passed']+=r['passed']
    summary={'phase':'P5b','independent_author':'/root/e1_review','mode':mode,'environment':plan['environment'],
             'generator_version_hash':plan['generator_version_hash'],'rows':len(rows),'planned':len(plan['rows']),
             'failed_rows':sum(not r['passed'] for r in rows),'retries':ledger.used,'concurrency':plan['concurrency'],
             'passed':len(rows)==len(plan['rows']) and all(r['passed'] for r in rows) and ledger.used==0,
             'wall_seconds':time.monotonic()-started,'sources':plan['sources'],'row_shards':shards,
             'per_cell':by_cell,'api_usd':0,'gpu_usd':0,'raw_directory':str(raw_root.relative_to(ROOT))}
    output.write_bytes(canonical(summary)+b'\n');return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('probes','mixed','regression','e2-stress'))
    parser.add_argument('--environment',choices=ENVS,default='E1');parser.add_argument('--concurrency',type=int,default=8)
    parser.add_argument('--output',required=True);parser.add_argument('--write-plan',action='store_true')
    parser.add_argument('--confirm-mock-docker',action='store_true');args=parser.parse_args()
    output=Path(args.output);output=output if output.is_absolute() else ROOT/output
    if not output.resolve().is_relative_to(ROOT):raise SystemExit('repo output required')
    plan_path=output.with_name(output.stem+'_plan.json.gz')
    if args.write_plan:
        plan=make_plan(args.mode,args.environment,args.concurrency)
        with plan_path.open('xb') as stream:stream.write(gzip.compress(canonical(plan),mtime=0))
        print('Commit '+str(plan_path.relative_to(ROOT))+' before execution.');raise SystemExit(0)
    if not args.confirm_mock_docker:raise SystemExit('explicit mock Docker authorization required')
    plan_raw=plan_path.read_bytes()
    if git('show','HEAD:'+str(plan_path.relative_to(ROOT)))!=plan_raw:raise SystemExit('plan must be committed')
    plan=json.loads(gzip.decompress(plan_raw))
    if plan!=make_plan(args.mode,args.environment,args.concurrency):raise SystemExit('plan/source drift')
    summary=asyncio.run(execute(plan,output))
    print(json.dumps({k:summary[k] for k in ('mode','rows','failed_rows','retries','passed')}))
    raise SystemExit(0 if summary['passed'] else 1)
