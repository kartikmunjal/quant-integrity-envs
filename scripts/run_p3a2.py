"""Infrastructure-only E2 stress, historical exact regression, and fresh gate."""
import argparse
import asyncio
import contextlib
import gzip
import hashlib
import json
import logging
from pathlib import Path
import subprocess
import time

from scripts.p3a2_support import Archive,canonical,shards,sha,ensure_tracked_capacity
from scripts.run_p3a_gate import POLICIES,TIERS,statistics,source_files as prior_sources
from qi_runtime.infrastructure import RetryBudget,run_with_retry
from qi_runtime import IMAGE
from qi_runtime.phase import runtime_version_hash,e6_fresh_context
from qi.gen import generator_version_hash
from envs.e2_leakage_audit import v1_taskset as e2
from envs.e2_leakage_audit.runtime import reference_program

ROOT=Path(__file__).resolve().parents[1]


def source_files():
    paths=set(prior_sources())
    paths.update(str(p.relative_to(ROOT)) for p in ROOT.glob('scripts/*p3a2*.py'))
    paths.update(str(p.relative_to(ROOT)) for p in ROOT.glob('tests/validation/*p3a2*.py'))
    paths.update(str(p.relative_to(ROOT)) for name in ('e1_pit_backtest','e5_cost_realism','e6_data_traps') for p in (ROOT/'envs'/name).glob('*.py'))
    paths.update(['reports/P3a2_design.md','results/p3a2_regression_plan.json.gz','scripts/e1_policies.py','scripts/e5_policies.py','scripts/e6_policies.py','scripts/review_p3a.py'])
    return {p:sha((ROOT/p).read_bytes()) for p in sorted(paths)}


def review_plan():
    from scripts.review_p3a import sample_plan
    return [(p,t,s+2000) for p,t,s in sample_plan()]


@contextlib.contextmanager
def fresh_context():
    old_guard=e2.guard;old_replay=e2.replay_seed
    def guard(seed):
        if 1003000<=seed<=1003499:
            if not e2.FRESH_AUTHORIZED.get():raise ValueError('round two fresh gate authorization required')
            return
        return old_guard(seed)
    def replay(seed,tier,patch):
        if 1003000<=seed<=1003499:
            return 1004000+int.from_bytes(hashlib.sha256(f'E2:{seed}:{tier}:{patch}'.encode()).digest()[:8],'big')%1000
        return old_replay(seed,tier,patch)
    e2.guard=guard;e2.replay_seed=replay
    try:yield
    finally:e2.guard=old_guard;e2.replay_seed=old_replay


def freeze_check():
    path=ROOT/'results/p3a2_freeze.json';freeze=json.loads(path.read_text())
    if freeze['sources']!=source_files():raise ValueError('round two frozen sources drifted')
    if json.loads(subprocess.check_output(['git','show','HEAD:results/p3a2_freeze.json']))!=freeze:raise ValueError('uncommitted freeze')
    if freeze['image']!=IMAGE or freeze['runtime_version_hash']!=runtime_version_hash() or freeze['generator_version_hash']!=generator_version_hash():raise ValueError('runtime/image/generator mismatch')
    from scripts.freeze_p3a2 import verify_prerequisites
    if freeze['prerequisites']!=verify_prerequisites():raise ValueError('prerequisite evidence drift')
    if freeze['author_review_plan']!=[list(r) for r in review_plan()]:raise ValueError('review selection drift')
    return freeze


def stress_plan():
    # Three cheaters occupy 6/12 entries, offset varies across tiers and seeds.
    cycle=['harness','network','canary','oracle','harness','network','canary','random','oracle_read','wrong_0','schema','oracle']
    return [(cycle[i%len(cycle)],TIERS[(i//len(cycle))%4],1000000+(i//(len(cycle)*4))%1000) for i in range(5000)]


def compact_value(value):
    # Full records remain local; compact rows bind exact rewards and runtime provenance.
    result={k:value.get(k) for k in ('reward','flagged','findings','truth','primary_error','replay_error','poison_error','schema_ok','security_ok','replay_seed','generator_version_hash')}
    result['findings']=value.get('findings') or [];result['truth']=value.get('truth') or []
    result['container_ids']={s:value.get(s,{}).get('container_id') for s in ('solver','primary','replay','poison')}
    return result


async def run(args):
    logging.disable(logging.CRITICAL)
    marker=ROOT/'logs/p3a2_gate_calls.json'
    if args.mode=='gate':
        with marker.open('x') as f:json.dump({'status':'INITIALIZING','time_unix':time.time()},f)
        freeze=freeze_check()
        if args.concurrency!=8:raise ValueError('fresh gate fixed concurrency eight')
        e2.EXPONENT=freeze['exponent']
    version=source_files();started=time.monotonic();archive=Archive(args.tag);journal=archive.root/'exceptions';journal.mkdir()
    baseline=None
    if args.mode=='regression':
        raw=(ROOT/'results/p3a2_regression_plan.json.gz').read_bytes()
        if subprocess.check_output(['git','show','HEAD:results/p3a2_regression_plan.json.gz'])!=raw:raise ValueError('regression list must be committed')
        baseline=json.loads(gzip.decompress(raw))['environments'][args.environment]
        plan=[(r['policy'],r['tier'],r['seed']) for r in baseline]
        for r in baseline:
            data=(ROOT/r['baseline_path']).read_bytes()
            if sha(data)!=r['baseline_sha256']:raise ValueError('baseline changed')
        module=__import__('scripts.'+{'E1':'e1','E5':'e5','E6':'e6'}[args.environment]+'_policies',fromlist=['policies'])
        available,_,_=module.policies()
        taskset=__import__('envs.'+{'E1':'e1_pit_backtest','E5':'e5_cost_realism','E6':'e6_data_traps'}[args.environment]+'.v1_taskset',fromlist=['run_policy'])
    elif args.mode=='stress':plan=stress_plan()
    else:plan=[(p,t,1003000+i) for p in POLICIES for t in TIERS for i in range(500 if p=='oracle' else 50)]
    (archive.root/'plan.json').write_bytes(canonical({'plan':plan,'sources':version,'mode':args.mode,'concurrency':args.concurrency}))
    ledger=RetryBudget(len(plan));iterator=iter(enumerate(plan));rows=[];fatal=None;stop=False
    sources={p:reference_program(p) for p in POLICIES}
    if args.mode=='gate':marker.write_bytes(canonical({'status':'RUNNING','planned':len(plan),'freeze_sha256':sha((ROOT/'results/p3a2_freeze.json').read_bytes())}))
    async def worker():
        nonlocal stop,fatal
        token=e2.FRESH_AUTHORIZED.set(args.mode=='gate')
        try:
            for index,(policy,tier,seed) in iterator:
                if stop:return
                if source_files()!=version:stop=True;raise ValueError('source drift')
                try:
                    ensure_tracked_capacity(4*1024**2)
                    archive.ensure_local_capacity(16*1024**2*(args.concurrency+1))
                except Exception:
                    stop=True
                    raise
                if args.mode=='regression':
                    source=module.source_for(policy,seed,tier,available)
                    call=lambda:taskset.run_policy(seed,tier,source)
                else:call=lambda:e2.run_policy(seed,tier,sources[policy])
                result=await run_with_retry(call,metadata={'environment':args.environment,'policy':policy,'tier':tier,'seed':seed,'index':index},ledger=ledger,journal_root=journal)
                value=result['value'] or {}
                # Fully observed policy zeros need no financial re-execution, even if a host operation later failed.
                if args.environment=='E2' and result['complete'] and value.get('policy_evidence'):
                    value.update(schema_ok=False,security_ok=False)
                row=compact_value(value)
                row.update(index=index,policy=policy,tier=tier,seed=seed,complete=result['complete'],retried=result['retried'],terminal_kind=result['terminal_kind'],infrastructure_ok=result['infrastructure_ok'])
                row['attempts']=[{k:a[k] for k in ('attempt','kind','elapsed_seconds','policy_evidence','cleanup_complete','resource_overlap','resources')} for a in result['attempts']]
                row['telemetry']=telemetry(result)
                try:row['archive']=archive.add(f'{index:05d}-{policy}-{tier}-{seed}',{'policy':policy,'tier':tier,'seed':seed,'run':result})
                except Exception:
                    stop=True
                    raise
                if baseline:
                    row['expected_reward']=baseline[index]['reward'];row['exact_match']=result['complete'] and value.get('reward')==baseline[index]['reward']
                    if not row['exact_match']:stop=True;fatal='exact reward regression mismatch; phase stopped'
                rows.append(row)
                if len(rows)%50==0 or not result['infrastructure_ok']:print(json.dumps({'mode':args.mode,'rows':len(rows),'planned':len(plan),'retries':ledger.used,'terminal':sum(not r['infrastructure_ok'] for r in rows)}),flush=True)
        finally:e2.FRESH_AUTHORIZED.reset(token)
    context=e6_fresh_context() if args.environment=='E6' else fresh_context() if args.mode=='gate' else contextlib.nullcontext()
    with context:
        outcomes=await asyncio.gather(*(worker() for _ in range(args.concurrency)),return_exceptions=True)
    failures=[repr(e) for e in outcomes if isinstance(e,BaseException)]
    rows.sort(key=lambda r:r['index']);compact=shards(rows,ROOT/'results'/args.tag/'rows')
    archive.ensure_local_capacity()
    entries=[]
    for path in sorted(archive.root.rglob('*')):
        if path.is_file():
            data=path.read_bytes();entries.append({'path':str(path.relative_to(ROOT)),'bytes':len(data),'sha256':sha(data)})
    manifest={'local_only':True,'entry_count':len(entries),'compressed_bytes':sum(e['bytes'] for e in entries),'entry_shards':shards(entries,ROOT/'results'/args.tag/'manifest')}
    (ROOT/'results'/f'{args.tag}_manifest.json').write_bytes(canonical(manifest)+b'\n')
    ids=[v['container_id'] for r in rows for a in r['attempts'] for v in a['resources'] if v['event']=='created' and v.get('container_id')]
    summary={'environment':args.environment,'mode':args.mode,'concurrency':args.concurrency,'planned':len(plan),'rows':len(rows),'complete_rows':sum(r['complete'] for r in rows),'infrastructure_ok_rows':sum(r['infrastructure_ok'] for r in rows),
             'retries':ledger.used,'retry_rate':ledger.used/len(plan),'compact_shards':compact,'sources':version,'runtime_version_hash':runtime_version_hash(),'generator_version_hash':generator_version_hash(),'image':IMAGE,
             'wall_seconds':time.monotonic()-started,'errors':failures,'fatal':fatal,'telemetry':aggregate_telemetry(rows),'api_usd':0,'gpu_usd':0,
             'container_count':len(ids),'unique_container_count':len(set(ids)),'local_manifest':f'results/{args.tag}_manifest.json'}
    summary['complete']=len(rows)==len(plan) and all(r['complete'] for r in rows)
    summary['passed']=len(rows)==len(plan) and all(r['complete'] and r['infrastructure_ok'] for r in rows) and ledger.used/len(plan)<=.005 and len(ids)==len(set(ids)) and not failures and not fatal
    if baseline:summary['exact_matches']=sum(r['exact_match'] for r in rows);summary['baseline_plan_sha256']=sha((ROOT/'results/p3a2_regression_plan.json.gz').read_bytes())
    if args.mode=='gate':
        summary['statistics']=statistics(rows,e2.EXPONENT)
        summary['oracle_four_stages']=all(all(r['container_ids'].values()) for r in rows if r['policy']=='oracle' and r['complete'])
        summary['passed'] &= summary['statistics']['passed'] and summary['oracle_four_stages']
        marker.write_bytes(canonical({'status':'COMPLETE' if summary['passed'] else 'FAILED','passed':summary['passed'],'summary':f'results/{args.tag}.json','rows':len(rows),'planned':len(plan)}))
    ensure_tracked_capacity(len(canonical(summary))+1)
    (ROOT/'results'/f'{args.tag}.json').write_bytes(canonical(summary)+b'\n')
    print(json.dumps({'finished':True,'passed':summary['passed'],'rows':len(rows),'errors':failures,'fatal':fatal}),flush=True)
    if not summary['passed']:raise SystemExit(1)


def telemetry(result):
    transfers=[t for a in result['attempts'] for t in a['transfers']]
    return {'transfers':len(transfers),'timeouts':sum(t['exception_type']=='HostTimeout' for t in transfers),'duration_seconds':sum(t['duration_seconds'] for t in transfers),
            'maximum_duration_seconds':max((t['duration_seconds'] for t in transfers),default=0.),'daemon_probes':len(transfers),'daemon_probe_failures':sum(not t['daemon_probe']['success'] for t in transfers),
            'daemon_latency_seconds':sum(t['daemon_probe']['duration_seconds'] for t in transfers),'maximum_daemon_latency_seconds':max((t['daemon_probe']['duration_seconds'] for t in transfers),default=0.)}


def aggregate_telemetry(rows):
    result={}
    for row in rows:
        for key,value in row['telemetry'].items():result[key]=max(result.get(key,0),value) if key.startswith('maximum_') else result.get(key,0)+value
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['stress','regression','gate'],required=True);parser.add_argument('--environment',choices=['E1','E2','E5','E6'],default='E2');parser.add_argument('--concurrency',type=int,default=8);parser.add_argument('--tag',required=True)
    args=parser.parse_args()
    if not 1<=args.concurrency<=24:parser.error('concurrency bound')
    if args.mode!='regression' and args.environment!='E2':parser.error('E2 stress/gate only')
    asyncio.run(run(args))
