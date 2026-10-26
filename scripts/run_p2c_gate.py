"""One-shot frozen E5 real-runtime gate. Only explicitly reserved fresh dev seeds."""
from __future__ import annotations
import argparse
import asyncio
from collections import Counter
import gzip
import hashlib
import json
import logging
from pathlib import Path
import subprocess
import time

import yaml
from qi_runtime import IMAGE
from qi.gen import generator_version_hash
from envs.e5_cost_realism import checker
from envs.e5_cost_realism.cases import public_input,case_diagnostics
from envs.e5_cost_realism.reward import score_pair,check_answer
from envs.e5_cost_realism.v1_taskset import run_policy
from scripts.e5_policies import policies,source_for

FREEZE=Path('results/p2c_freeze.json')
CALLS=Path('logs/p2c_gate_calls.json')
TIERS=('T1','T2','T3','T4')
NEAR=('near_miss','near_sharpe_only')


def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_sources():
    files=sorted([*Path('envs/e5_cost_realism').rglob('*.py'),*Path('src/qi_runtime').rglob('*.py'),
        *Path('src/qi_e5').rglob('*.py'),*Path('src/qi_cost_realism').rglob('*.py'),*Path('src/qi/gen').rglob('*.py'),Path('envs/e1_pit_backtest/runtime.py'),
        Path('scripts/run_p2c_gate.py'),Path('scripts/e5_policies.py'),Path('scripts/design_p2c.py'),
        Path('reports/P2c_design.md'),Path('prereg.yaml'),Path('pyproject.toml'),Path('uv.lock'),
        Path('configs/e5_scripted.toml'),Path('envs/e5_cost_realism/schema.json'),Path('envs/e5_cost_realism/runtime_schema.json'),Path('envs/e1_pit_backtest/container/Dockerfile'),Path('.github/workflows/ci.yml')])
    return {str(path):file_hash(path) for path in files}


def verify_freeze():
    saved=json.loads(FREEZE.read_text())
    if saved['sources']!=frozen_sources() or saved['image']!=IMAGE or saved['generator_version_hash']!=generator_version_hash():
        raise RuntimeError('changed source/design/image/generator after freeze')
    if subprocess.check_output(['git','show','HEAD:results/p2c_freeze.json'])!=FREEZE.read_bytes():
        raise RuntimeError('freeze must be committed before fresh results')
    subprocess.run(['git','merge-base','--is-ancestor',saved['implementation_commit'],'HEAD'],check=True)
    return saved


def summarize_stage(stage):
    out={k:v for k,v in stage.items() if k!='answer'}
    answer=stage.get('answer')
    if answer is None:out['answer']=None
    else:
        weights=answer['weights']
        out['answer']={'net_sharpe':answer['net_sharpe'],'breakeven_holding_days':answer['breakeven_holding_days'],
            'weights_shape':[len(weights),len(weights[0])],
            'weights_sha256':hashlib.sha256(json.dumps(weights,separators=(',',':')).encode()).hexdigest()}
    return out


def compact(value):
    out={key:value[key] for key in ('seed','tier','policy','reward','flagged','replay_seed','lifecycle','diagnostics','source_sha256')}
    if 'error' in value:out['error']=value['error']
    for stage in ('solver','primary','replay'):out[stage]=summarize_stage(value[stage])
    return out


def unit_comparison(value,data,fresh_data,index):
    # Pure-function variants are separate from actual Task evidence and never attached to a Task.
    first=value['primary'];fresh=value['replay'];mode=index%8
    if mode==0:first=None
    elif mode==1:fresh=None
    elif mode==2:first={**first,'flagged':True}
    elif mode==3:fresh={**fresh,'flagged':True}
    elif mode==4:first={**first,'exit_code':False}
    elif mode==5:fresh={**fresh,'answer':dict(fresh['answer'],net_sharpe=fresh['answer']['net_sharpe']*1.02)}
    elif mode==6:first={**first,'answer':dict(first['answer'],net_sharpe=first['answer']['net_sharpe']*1.00505,breakeven_holding_days=first['answer']['breakeven_holding_days']*1.00505)}
    else:first={**first,'answer':dict(first['answer'],weights=[[True]*8 for _ in range(48)])}
    return abs(score_pair(first,fresh,data,fresh_data)-checker.score_pair(first,fresh,data,fresh_data))<=1e-8


def fractions(rows):
    n=len(rows)
    full=sum(abs(v['reward']-1)<=1e-10 for v in rows)
    partial=sum(0<v['reward']<1-1e-10 for v in rows)
    numeric={'within_full_tolerance':0,'in_partial_band':0,'at_or_beyond_zero_scale':0,'invalid_or_flagged':0}
    for value in rows:
        errors=value['primary'].get('errors')
        if errors is None:numeric['invalid_or_flagged']+=1
        elif max(errors)<=1e-4:numeric['within_full_tolerance']+=1
        elif max(errors)<.01:numeric['in_partial_band']+=1
        else:numeric['at_or_beyond_zero_scale']+=1
    return {'full_reward':full/n,'partial_reward':partial/n,'zero_reward':sum(v['reward']==0 for v in rows)/n,
            'primary_numeric_error_fractions':{key:count/n for key,count in numeric.items()}}


def minimum_gaps(diagnostics):
    return {key:min((d[key] for d in diagnostics),default=None) for key in ('cost_gap','capacity_binding_gap','terminal_close_gap')}


def oracle_checks(rows,limits):
    return {'mean_passed':sum(v['reward'] for v in rows)/len(rows)>=limits['oracle_policy_min_mean_reward'],
        'false_positive_passed':sum(v['flagged'] for v in rows)/len(rows)<=limits['clean_episode_false_positive_ceiling']}


async def main(concurrency):
    freeze=verify_freeze()
    with CALLS.open('x') as file:json.dump({'started':time.time(),'freeze_sha256':file_hash(FREEZE),'status':'started'},file,indent=2)
    logging.disable(logging.CRITICAL)
    started=time.perf_counter();available,wrong,attacks=policies();semaphore=asyncio.Semaphore(concurrency)
    folder=Path('results/p2c_rollouts');folder.mkdir(exist_ok=True)
    names=sorted(available)
    wanted={(TIERS[i%4],names[i%len(names)],i//len(names)):i for i in range(50)};samples={}
    plan=[(tier,'oracle',range(1005000,1005500)) for tier in TIERS]
    plan += [(tier,name,range(1005000,1005050)) for tier in TIERS for name in available if name!='oracle']
    groups={};completed=0;real_agree=0;real_count=0;unit_agree=0;unit_count=0;oracle_cases=0;failures=[]

    async def one(seed,tier,name):
        nonlocal completed
        async with semaphore:
            try:
                value=await run_policy(seed,tier,source_for(name,seed,tier,available))
                value.update(seed=seed,tier=tier,policy=name,diagnostics=case_diagnostics(public_input(seed,tier)))
            except Exception as error:
                empty={'answer':None,'flagged':True,'exit_code':-1,'container_id':None,'computed':None,'errors':None}
                value={'seed':seed,'tier':tier,'policy':name,'reward':0.,'flagged':True,'replay_seed':None,'lifecycle':[],
                    'diagnostics':None,'source_sha256':None,'solver':empty,'primary':empty,'replay':empty,'error':str(error)}
            completed+=1
            if completed%50==0:print(f'completed {completed} independent E5 rollouts',flush=True)
            return value

    for tier,name,seeds in plan:
        rows=await asyncio.gather(*(one(seed,tier,name) for seed in seeds));groups[tier,name]=rows
        for index,value in enumerate(rows):
            key=(tier,name,index)
            if key in wanted:samples[wanted[key]]=value
            real_count+=1
            if 'error' in value:
                failures.append({'tier':tier,'seed':value['seed'],'policy':name,'error':value['error']});continue
            data=public_input(value['seed'],tier)
            fresh_data=public_input(value['replay_seed'],tier) if value['replay_seed'] is not None else data
            independent=checker.score_pair(value['primary'],value['replay'],data,fresh_data)
            real_agree+=int(abs(independent-value['reward'])<=1e-8)
            if name=='oracle':
                oracle_cases+=1
                unit_count+=1
                unit_agree+=int(unit_comparison(value,data,fresh_data,index))
        for shard,offset in enumerate(range(0,len(rows),50)):
            (folder/f'{tier}-{name}-{shard:03d}.json').write_text(json.dumps([compact(v) for v in rows[offset:offset+50]],sort_keys=True,indent=1,allow_nan=False)+'\n')
        print(f'{tier} {name} mean {sum(v["reward"] for v in rows)/len(rows):.8f}',flush=True)

    raw=json.dumps({'environment':'E5','generator_version_hash':generator_version_hash(),'label':'author-reviewed sample pending','samples':[samples[i] for i in range(50)]},sort_keys=True,allow_nan=False).encode()
    Path('results/p2c_trajectory_sample.json.gz').write_bytes(gzip.compress(raw,mtime=0))
    limits=yaml.safe_load(Path('prereg.yaml').read_text())['verifier_gates'];tiers={}
    for tier in TIERS:
        stats={}
        for name in available:
            rows=groups[tier,name][:50]
            stats[name]={'n':50,'mean_reward':sum(v['reward'] for v in rows)/50,'flagged':sum(v['flagged'] for v in rows),
                'errors':sum('error' in v for v in rows),'reward_distribution':dict(Counter(f'{v["reward"]:.10f}' for v in rows)),
                'fractions':fractions(rows)}
        all_tier=[value for (t,_),rows in groups.items() if t==tier for value in rows]
        diagnostics=[value['diagnostics'] for value in all_tier if value['diagnostics'] is not None]
        total=len(all_tier);near_count=sum(len(groups[tier,name]) for name in NEAR)
        oracle_all=oracle_checks(groups[tier,'oracle'],limits)
        checks={'oracle_all_episodes':oracle_all['mean_passed'],'oracle':stats['oracle']['mean_reward']>=limits['oracle_policy_min_mean_reward'],
            'random':stats['random']['mean_reward']<=limits['random_policy_max_mean_reward'],
            'wrong_individual':all(stats[name]['mean_reward']<=limits['wrong_solution_max_mean_reward'] for name in wrong),
            'wrong_aggregate':sum(stats[name]['mean_reward'] for name in wrong)/len(wrong)<=limits['wrong_solution_max_mean_reward'],
            'cheaters':all(stats[name]['mean_reward']<=limits['cheater_policy_max_mean_reward'] for name in attacks),
            'complete_rollouts':all(v['lifecycle']==['setup','solver','finalize','score'] and 'error' not in v for v in all_tier),
            'cost_and_capacity_separation':len(diagnostics)==total and all(d['cost_gap']>=.02 and d['capacity_binding_gap']>=.02 and d['terminal_close_gap']>=.02 for d in diagnostics),
            'near_miss_partial':all(0<stats[name]['mean_reward']<1 for name in NEAR),
            'source_binding':all(v['source_sha256'] and all(v[stage].get('source_sha256')==v['source_sha256'] for stage in ('solver','primary','replay') if v[stage].get('container_id')) for v in all_tier)}
        if tier=='T4':
            checks['clean_false_positive']=stats['oracle']['flagged']/50<=limits['clean_episode_false_positive_ceiling']
            checks['clean_false_positive_all_oracles']=oracle_all['false_positive_passed']
        tiers[tier]={'policies':stats,'checks':checks,'minimum_gaps':minimum_gaps(diagnostics),
            'composition':{'all_rollouts':{'n':total,'oracle_fraction':len(groups[tier,'oracle'])/total,'near_miss_fraction':near_count/total},
                'policy_cells_first_50':{'n':50*len(available),'oracle_fraction':1/len(available),'near_miss_fraction':len(NEAR)/len(available)}},
            'oracle_all_episode_fractions':fractions(groups[tier,'oracle'])}
    ids=[value[stage].get('container_id') for rows in groups.values() for value in rows for stage in ('solver','primary','replay') if value[stage].get('container_id')]
    result={'environment':'E5','generator_version_hash':generator_version_hash(),'freeze':freeze,'seed_partition':'fresh E5 dev','tiers':tiers,
        'second_checker':{'oracle_cases':oracle_cases,'real_comparisons':real_count,'agreement':real_agree/real_count,'unit_comparisons':unit_count,'unit_agreement':unit_agree/unit_count if unit_count else 0,'failures':failures},
        'rollouts':completed,'container_count':len(ids),'containers_unique':len(ids)==len(set(ids)),'source_hashes_unchanged':freeze['sources']==frozen_sources(),
        'partial_credit_band':{'full_tolerance':.0001,'zero_scale':.01,'width_relative':.0099},'spend':{'api_usd':0,'gpu_usd':0},'concurrency':concurrency,'elapsed_seconds':time.perf_counter()-started}
    result['passed']=oracle_cases>=2000 and real_agree/real_count>=limits['dual_checker_min_agreement'] and unit_agree/unit_count>=limits['dual_checker_min_agreement'] and result['containers_unique'] and result['source_hashes_unchanged'] and all(all(value['checks'].values()) for value in tiers.values())
    Path('results/p2c_gate.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    call=json.loads(CALLS.read_text());call.update(status='complete',passed=result['passed'],elapsed_seconds=result['elapsed_seconds']);CALLS.write_text(json.dumps(call,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('tiers','freeze')},indent=2),flush=True)
    return 0 if result['passed'] else 1

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--concurrency',type=int,default=12);a=p.parse_args()
    if not 1<=a.concurrency<=16:raise ValueError('concurrency must be 1..16')
    raise SystemExit(asyncio.run(main(a.concurrency)))
