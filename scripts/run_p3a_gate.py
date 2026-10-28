"""E2 design policies or committed, globally one-shot full-v1 fresh gate."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/validation'))
from scripts.p3a_support import Archive,canonical,shards,sha,TRACKED_BUDGET,LOCAL_BUDGET
from qi_runtime.infrastructure import RetryBudget,run_with_retry
from qi_runtime import IMAGE
from qi_runtime.phase import runtime_version_hash
from qi.gen import generator_version_hash
from envs.e2_leakage_audit.runtime import reference_program
from envs.e2_leakage_audit import v1_taskset
from envs.e2_leakage_audit.reward import grade_record
from p3a_scalar_checker import check_record

POLICIES=['oracle','random']+[f'wrong_{i}' for i in range(12)]+['constant','disabled','canary','oracle_read','harness','network','schema','primary_only','shallow']+[f'find_{i}' for i in range(4)]+['near_1','near_2','false_flag','never_report','report_only']
CHEATERS=['constant','disabled','canary','oracle_read','harness','network','schema','primary_only']
TIERS=['T1','T2','T3','T4']


def source_files():
    patterns=['src/qi/mutate/*.py','envs/e2_leakage_audit/*.py','envs/e2_leakage_audit/*.json','src/qi_leakage_audit/*.py','scripts/*p3a*.py','tests/validation/*p3a*.py']
    paths={p for pattern in patterns for p in ROOT.glob(pattern)}
    paths.update(ROOT/p for p in ['reports/P3a_design.md','docs/MILESTONES.md','prereg.yaml','AMENDMENTS.md','pyproject.toml','uv.lock'])
    return {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(paths)}


def freeze_check():
    path=ROOT/'results/p3a_freeze.json';freeze=json.loads(path.read_text())
    if source_files()!=freeze['sources']:raise ValueError('P3a frozen source mismatch')
    if freeze['image']!=IMAGE or freeze['runtime_version_hash']!=runtime_version_hash() or freeze['generator_version_hash']!=generator_version_hash():raise ValueError('runtime/image/generator mismatch')
    if freeze['policies']!=POLICIES or freeze['exponent']!=v1_taskset.EXPONENT:raise ValueError('policy/exponent mismatch')
    subprocess.check_call(['git','cat-file','-e',freeze['implementation_commit']+'^{commit}'],cwd=ROOT)
    committed=subprocess.check_output(['git','show','HEAD:results/p3a_freeze.json'],cwd=ROOT)
    if json.loads(committed)!=freeze:raise ValueError('freeze not committed before fresh result')
    return freeze


def statistics(rows,exponent):
    groups={}
    for policy in POLICIES:
        for tier in TIERS:
            selected=[r for r in rows if r['policy']==policy and r['tier']==tier and r['complete']]
            values=[grade_record(r,exponent) for r in selected]
            groups[policy+'/'+tier]={'count':len(values),'mean':sum(values)/len(values) if values else None}
    criteria={}
    for tier in TIERS:
        def mean(policy):return groups[policy+'/'+tier]['mean']
        criteria['oracle/'+tier]=mean('oracle') is not None and mean('oracle')>=.95
        criteria['random/'+tier]=mean('random') is not None and mean('random')<=.05
        for p in [p for p in POLICIES if p.startswith('wrong_')]:criteria[p+'/'+tier]=mean(p) is not None and mean(p)<=.1
        wrong=[r for r in rows if r['tier']==tier and r['policy'].startswith('wrong_') and r['complete']]
        criteria['wrong_aggregate/'+tier]=bool(wrong) and sum(grade_record(r,exponent) for r in wrong)/len(wrong)<=.1
        for p in CHEATERS:criteria[p+'/'+tier]=mean(p) is not None and mean(p)<=.05
    for tier in ('T2','T3'):
        v=groups['shallow/'+tier]['mean'];criteria['shallow/'+tier]=v is not None and v<=.3
    clean=[r for r in rows if r['policy']=='oracle' and r['tier']=='T4' and r['complete']]
    fp=sum(bool(r['findings']) for r in clean)/len(clean) if clean else None
    criteria['clean_oracle_false_positive']=fp is not None and fp<=.02
    comparable=[r for r in rows if r['complete']]
    agreement=sum(abs(grade_record(r,exponent)-check_record(r,exponent))<=1e-12 for r in comparable)/len(comparable) if comparable else 0
    criteria['second_checker']=agreement>=.999
    family={}
    for f in [f'F{i}' for i in range(1,7)]:
        selected=[r for r in comparable if r['policy']=='oracle' and any(t['family']==f for t in r['truth'])]
        family[f]={'count':len(selected),'oracle_mean':sum(grade_record(r,exponent) for r in selected)/len(selected) if selected else None,
                   'minimum_planted_effect':min((t['effect'] for r in selected for t in r['truth'] if t['family']==f),default=None)}
    return {'exponent':exponent,'per_policy_tier':groups,'per_family':family,'heldout_families':{f:family[f] for f in ('F3','F4','F6')},
            'criteria':criteria,'passed':all(criteria.values()),'second_checker_agreement':agreement,'clean_oracle_false_positive_rate':fp}


async def main(args):
    marker=ROOT/'logs/p3a_gate_calls.json'
    if not args.design:
        # Reserve globally before freeze validation, planning, source creation or
        # any await; a failed initialization consumes this fresh gate too.
        with marker.open('x') as stream:json.dump({'status':'INITIALIZING','time_unix':time.time(),'tag':args.tag},stream)
        freeze=freeze_check()
    else:freeze=None
    version=source_files();started=time.monotonic();archive=Archive(args.tag)
    plan=[]
    for policy in POLICIES:
        count=args.count if args.design else (500 if policy=='oracle' else 50)
        for tier in TIERS:
            for offset in range(count):plan.append((policy,tier,(1000000 if args.design else 1001000)+offset))
    ledger=RetryBudget(len(plan));rows=[];stop=False;iterator=iter(plan)
    journal=archive.root/'exceptions';journal.mkdir()
    sources={p:reference_program(p) for p in POLICIES}
    (archive.root/'plan.json').write_bytes(canonical({'plan':plan,'sources':version,'policy_source_sha256':{p:sha(s.encode()) for p,s in sources.items()}}))
    if not args.design:marker.write_bytes(canonical({'status':'RUNNING','planned':len(plan),'freeze_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'started_unix':time.time()})+b'\n')
    async def worker():
        nonlocal stop
        token=v1_taskset.FRESH_AUTHORIZED.set(not args.design)
        try:
            while not stop:
                try:policy,tier,seed=next(iterator)
                except StopIteration:return
                if source_files()!=version:stop=True;raise ValueError('source drift; no further launches')
                if archive.prior_bytes+archive.bytes+16*1024**2*(args.concurrency+1)>LOCAL_BUDGET:
                    stop=True;raise ValueError('local storage reserve exhausted before next launch')
                result=await run_with_retry(lambda: v1_taskset.run_policy(seed,tier,sources[policy]),metadata={'environment':'E2','policy':policy,'tier':tier,'seed':seed},ledger=ledger,journal_root=journal)
                value=result['value'] or {}
                row={k:value.get(k) for k in ('findings','truth','primary_error','replay_error','poison_error','schema_ok','security_ok','replay_seed','generator_version_hash')}
                row.update(policy=policy,tier=tier,seed=seed,complete=result['complete'],retried=result['retried'],terminal_kind=result['terminal_kind'],reward=value.get('reward'))
                row['container_ids']={k:value.get(k,{}).get('container_id') for k in ('solver','primary','replay','poison')}
                row['attempts']=[{k:a[k] for k in ('attempt','kind','elapsed_seconds','policy_evidence','cleanup_complete','resource_overlap','resources')} for a in result['attempts']]
                entry=archive.add(f'{policy}-{tier}-{seed}',{'policy':policy,'tier':tier,'seed':seed,'run':result})
                row['archive']=entry;rows.append(row)
                if not result['complete']:stop=True
                if len(rows)%20==0 or not result['complete']:
                    print(json.dumps({'completed':len(rows),'planned':len(plan),'retries':ledger.used,'terminal':sum(not r['complete'] for r in rows),'last':[policy,tier,seed]}),flush=True)
        finally:v1_taskset.FRESH_AUTHORIZED.reset(token)
    error=None
    outcomes=await asyncio.gather(*(worker() for _ in range(args.concurrency)),return_exceptions=True)
    problems=[repr(e) for e in outcomes if isinstance(e,BaseException)]
    if problems:error='; '.join(problems);stop=True
    rows.sort(key=lambda r:(POLICIES.index(r['policy']),r['tier'],r['seed']))
    compact=shards(rows,ROOT/'results'/args.tag/'rows')
    manifest=archive.manifest()
    # Include retry journals and plan bytes: immutable full chains are local too.
    known={e['path'] for e in manifest['entries']}
    for path in sorted(archive.root.rglob('*')):
        if path.is_file() and str(path.relative_to(ROOT)) not in known:
            raw=path.read_bytes();manifest['entries'].append({'path':str(path.relative_to(ROOT)),'bytes':len(raw),'sha256':sha(raw)})
    manifest['compressed_bytes']=sum(e['bytes'] for e in manifest['entries'])
    entries=manifest.pop('entries')
    manifest['entry_shards']=shards(entries,ROOT/'results'/args.tag/'manifest')
    manifest['entry_count']=len(entries)
    (ROOT/'results'/f'{args.tag}_manifest.json').write_bytes(canonical(manifest)+b'\n')
    sensitivity=[statistics(rows,p) for p in (1,2,3)] if args.design else [statistics(rows,v1_taskset.EXPONENT)]
    complete=len(rows)==len(plan) and all(r['complete'] for r in rows)
    summary={'environment':'E2','design':args.design,'planned':len(plan),'rows':len(rows),'complete':complete,'retries':ledger.used,'retry_rate':ledger.used/len(plan),
             'terminal':sum(not r['complete'] for r in rows),'error':error,'sources':version,'generator_version_hash':generator_version_hash(),
             'runtime_version_hash':runtime_version_hash(),'image':IMAGE,'policies':POLICIES,'compact_shards':compact,
             'local_manifest':f'results/{args.tag}_manifest.json','sensitivity':sensitivity,'wall_seconds':time.monotonic()-started,
             'model_api_spend_usd':0,'gpu_spend_usd':0}
    ids=[cid for r in rows for cid in r['container_ids'].values() if cid]
    summary['container_count']=len(ids);summary['unique_container_count']=len(set(ids))
    summary['container_ids_unique']=len(ids)==len(set(ids))
    summary['oracle_four_stages']=all(all(r['container_ids'].values()) for r in rows if r['policy']=='oracle' and r['complete'])
    summary['passed']=summary['container_ids_unique'] and summary['oracle_four_stages'] and complete and ledger.used/len(plan)<=.005 and all(x['passed'] for x in sensitivity[:1]) and not error
    if args.design:summary['selected_exponent']=next((s['exponent'] for s in sensitivity if s['passed']),None) if complete else None
    (ROOT/'results'/f'{args.tag}.json').write_bytes(canonical(summary)+b'\n')
    if not args.design:marker.write_bytes(canonical({'status':'COMPLETE' if complete else 'FAILED','summary':f'results/{args.tag}.json','passed':summary['passed'],'rows':len(rows),'planned':len(plan)})+b'\n')
    print(json.dumps({'finished':True,'complete':complete,'passed':summary['passed'],'error':error,'selected_exponent':summary.get('selected_exponent')}),flush=True)
    if not summary['passed']:raise SystemExit(1)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--design',action='store_true');parser.add_argument('--count',type=int,default=10);parser.add_argument('--concurrency',type=int,default=12);parser.add_argument('--tag',default='p3a-gate')
    args=parser.parse_args()
    if not 1<=args.count<=1000 or not 1<=args.concurrency<=24:parser.error('bounded population/concurrency')
    asyncio.run(main(args))
