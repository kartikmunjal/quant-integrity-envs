"""One-shot E1 round-2 gate: frozen code, fresh dev seeds, independent real rollouts."""
from __future__ import annotations
import argparse
import asyncio
from collections import Counter
import hashlib
import json
import logging
from pathlib import Path
import subprocess
import time

import yaml
from envs.e1_pit_backtest import checker
from envs.e1_pit_backtest.cases import public_input,expected,naive_expected,relative_error
from envs.e1_pit_backtest.reward import checked_answer,score_pair
from envs.e1_pit_backtest.runtime import IMAGE
from envs.e1_pit_backtest.v1_taskset import run_policy
from qi.gen import generator_version_hash
from scripts.e1_policies import policies,source_for

FREEZE=Path('results/p2b2_freeze.json')
CALLS=Path('logs/p2b2_gate_calls.json')


def file_hash(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_sources():
    files=sorted([*Path('envs/e1_pit_backtest').rglob('*.py'),*Path('src/qi_e1').rglob('*.py'),
        Path('scripts/run_p2b2_gate.py'),Path('scripts/e1_policies.py'),Path('scripts/design_p2b2.py'),
        Path('reports/P2b2_design.md'),Path('prereg.yaml'),Path('pyproject.toml'),Path('uv.lock'),Path('configs/e1_scripted.toml'),Path('envs/e1_pit_backtest/container/Dockerfile')])
    return {str(path):file_hash(path) for path in files}


def verify_freeze():
    saved=json.loads(FREEZE.read_text())
    if saved['sources']!=frozen_sources() or saved['image']!=IMAGE:
        raise RuntimeError('gate refuses changed code/design/image after freeze')
    if saved['generator_version_hash']!=generator_version_hash():
        raise RuntimeError('generator changed after freeze')
    committed=subprocess.check_output(['git','show','HEAD:results/p2b2_freeze.json'])
    if committed!=FREEZE.read_bytes(): raise RuntimeError('freeze must be committed before gate')
    subprocess.run(['git','merge-base','--is-ancestor',saved['implementation_commit'],'HEAD'],check=True)
    return saved


def checker_comparisons(value,data):
    truth=expected(data);other=checker.expected(data)
    pairs=[]
    first=value['primary'];replay=value['replay']
    fresh_data=public_input(value['replay_seed'],value['tier'])
    fresh_truth=expected(fresh_data);fresh_other=checker.expected(fresh_data)
    numeric_ok=all(abs(truth[k]-other[k])<=1e-9*max(abs(truth[k]),1e-12) for k in truth)
    numeric_ok &= all(abs(fresh_truth[k]-fresh_other[k])<=1e-9*max(abs(fresh_truth[k]),1e-12) for k in truth)
    pairs.append((first,replay))
    for error in (.000099,.000101,.002,.00505,.009999,.01,.02):
        a={**first,'answer':{**truth,'backtest_return':truth['backtest_return']*(1+error)}}
        b={**replay,'answer':{**fresh_truth,'backtest_return':fresh_truth['backtest_return']*(1+error)}}
        pairs.extend([(a,replay),(first,b),(a,b)])
    pairs.extend([(None,replay),(first,None),({**first,'flagged':True},replay),(first,{**replay,'flagged':True}),
        ({**first,'exit_code':1},replay),(first,{**replay,'exit_code':1}),
        ({**first,'answer':{'signal_mean':True,'backtest_return':0}},replay),
        ({**first,'answer':{**truth,'availability_discipline':True}},replay),
        ({**first,'answer':{'signal_mean':float('nan'),'backtest_return':0}},replay)])
    comparisons=len(pairs);agreed=0
    for a,b in pairs:
        left=score_pair(a,b,truth,fresh_truth);right=checker.score_pair(a,b,other,fresh_other)
        agreed+=int(numeric_ok and abs(left-right)<=1e-8)
    for raw in ('null','[]','{}','{"signal_mean":true,"backtest_return":0}',
                '{"signal_mean":0,"signal_mean":1,"backtest_return":0}',
                '{"signal_mean":NaN,"backtest_return":0}',
                json.dumps(truth)):
        comparisons+=1;agreed+=int(checked_answer(raw)==checker.check_answer(raw))
    return agreed,comparisons


def compact(value):
    record={k:value[k] for k in ('seed','tier','policy','reward','flagged','replay_seed','lifecycle')}
    for stage in ('solver','primary','replay'):
        record[stage]={k:v for k,v in value[stage].items() if k!='commands'}
    return record


async def main(concurrency):
    freeze=verify_freeze()
    if CALLS.exists(): raise RuntimeError('round-two gate already called; no rerun after results')
    CALLS.parent.mkdir(exist_ok=True)
    with CALLS.open('x') as file:
        json.dump({'started':time.time(),'freeze_sha256':file_hash(FREEZE),'status':'started'},file,indent=2)
    logging.disable(logging.CRITICAL)
    started=time.perf_counter();available,wrong,attacks=policies()
    outdir=Path('results/p2b2_rollouts');outdir.mkdir(exist_ok=True)
    semaphore=asyncio.Semaphore(concurrency)
    all_rows={};completed=0

    async def one(seed,tier,name):
        nonlocal completed
        async with semaphore:
            try:
                value=await run_policy(seed,tier,source_for(name,seed,tier,available))
                value.update(seed=seed,tier=tier,policy=name)
                value['availability_gap']=relative_error(naive_expected(public_input(seed,tier)),expected(public_input(seed,tier)))
            except Exception as error:
                empty={'answer':None,'flagged':True,'exit_code':-1,'container_id':None}
                value={'seed':seed,'tier':tier,'policy':name,'reward':0.,'flagged':True,'replay_seed':None,
                    'lifecycle':[],'primary':empty,'replay':empty,'solver':empty,'availability_gap':None,'error':str(error)}
            completed+=1
            if completed%50==0: print(f'completed {completed} independent rollouts',flush=True)
            return value

    # Oracle/checker cases all run complete real rollouts, not pure-function surrogates.
    plan=[(tier,'oracle',range(1002000,1002500)) for tier in ('T1','T2','T3','T4')]
    plan += [(tier,name,range(1002000,1002050)) for tier in ('T1','T2','T3','T4') for name in available if name!='oracle']
    # Bound the scheduling queue by one policy/tier group. Each episode has its own Env,
    # task, interpreter and containers; concurrency shares no submitted-code process.
    agreements=0;comparisons=0;checker_cases=0;failures=[]
    real_agreements=0;real_comparisons=0
    for tier,name,seeds in plan:
        rows=await asyncio.gather(*(one(seed,tier,name) for seed in seeds))
        path=outdir/f'{tier}-{name}.json'
        path.write_text(json.dumps([dict(compact(value),availability_gap=value['availability_gap'],**({'error':value['error']} if 'error' in value else {})) for value in rows],indent=1,sort_keys=True)+'\n')
        all_rows[(tier,name)]=rows
        for value in rows:
            real_comparisons+=1
            if 'error' in value: continue
            target=checker.expected(public_input(value['seed'],tier))
            fresh_target=checker.expected(public_input(value['replay_seed'],tier)) if value['replay_seed'] is not None else target
            independent_value=checker.score_pair(value['primary'],value['replay'],target,fresh_target)
            real_agreements+=int(abs(independent_value-value['reward'])<=1e-8)
        if name=='oracle':
            for value in rows:
                checker_cases+=1
                if value['replay_seed'] is None:
                    failures.append({'seed':value['seed'],'tier':tier,'error':value.get('error','missing replay')})
                    comparisons+=1
                    continue
                a,n=checker_comparisons(value,public_input(value['seed'],tier));agreements+=a;comparisons+=n
        print(f'{tier} {name} mean {sum(v["reward"] for v in rows)/len(rows):.8f}',flush=True)

    thresholds=yaml.safe_load(Path('prereg.yaml').read_text())['verifier_gates']
    tiers={}
    for tier in ('T1','T2','T3','T4'):
        stats={}
        for name in available:
            # Frozen prereg policy-cell count: first 50; extra oracle rollouts support checker coverage.
            rows=all_rows[(tier,name)][:50]
            stats[name]={'n':len(rows),'mean_reward':sum(v['reward'] for v in rows)/len(rows),
                'flagged':sum(v['flagged'] for v in rows),'errors':sum('error' in v for v in rows),
                'reward_distribution':dict(Counter(f'{v["reward"]:.10f}' for v in rows)),
                'min_availability_gap':min((v['availability_gap'] for v in rows if v['availability_gap'] is not None),default=None)}
        checks={'oracle':stats['oracle']['mean_reward']>=thresholds['oracle_policy_min_mean_reward'],
            'random':stats['random']['mean_reward']<=thresholds['random_policy_max_mean_reward'],
            'wrong_individual':all(stats[name]['mean_reward']<=thresholds['wrong_solution_max_mean_reward'] for name in wrong),
            'wrong_aggregate':sum(stats[name]['mean_reward'] for name in wrong)/len(wrong)<=thresholds['wrong_solution_max_mean_reward'],
            'cheaters':all(stats[name]['mean_reward']<=thresholds['cheater_policy_max_mean_reward'] for name in attacks),
            'availability':all(v['availability_gap'] is not None and v['availability_gap']>=.02 for (t,_),values in all_rows.items() if t==tier for v in values),
            'complete_rollouts':all(v['lifecycle']==['setup','solver','finalize','score'] and 'error' not in v for (t,_),values in all_rows.items() if t==tier for v in values),
            'near_miss_partial':0<stats['near_miss']['mean_reward']<1}
        if tier=='T4':checks['clean_false_positive']=stats['oracle']['flagged']/50<=thresholds['clean_episode_false_positive_ceiling']
        tiers[tier]={'policies':stats,'checks':checks}
    container_ids=[v[stage].get('container_id') for values in all_rows.values() for v in values for stage in ('solver','primary','replay') if v[stage].get('container_id') is not None]
    containers_unique=len(container_ids)==len(set(container_ids))
    agreement=agreements/comparisons
    result={'environment':'E1','generator_version_hash':generator_version_hash(),'freeze':freeze,'seed_partition':'fresh dev',
        'tiers':tiers,'second_checker':{'cases':checker_cases,'unit_comparisons':comparisons,'unit_agreement':agreement,'real_comparisons':real_comparisons,'agreement':real_agreements/real_comparisons,'failed_cases':failures,
            'passed':checker_cases>=2000 and agreement>=thresholds['dual_checker_min_agreement'] and real_agreements/real_comparisons>=thresholds['dual_checker_min_agreement']},
        'rollouts':completed,'elapsed_seconds':time.perf_counter()-started,'spend':{'api_usd':0,'gpu_usd':0},
        'concurrency':concurrency,'container_count':len(container_ids),'containers_unique':containers_unique,'source_hashes_unchanged':freeze['sources']==frozen_sources()}
    result['passed']=result['containers_unique'] and result['source_hashes_unchanged'] and result['second_checker']['passed'] and all(all(t['checks'].values()) for t in tiers.values())
    Path('results/p2b2_gate.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    CALLS.write_text(json.dumps({'started':json.loads(CALLS.read_text())['started'],'status':'complete','passed':result['passed'],'elapsed_seconds':result['elapsed_seconds']},indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('tiers','freeze')},indent=2),flush=True)
    return 0 if result['passed'] else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--concurrency',type=int,default=8);args=parser.parse_args()
    if not 1<=args.concurrency<=16:raise ValueError('concurrency must be 1..16')
    raise SystemExit(asyncio.run(main(args.concurrency)))
