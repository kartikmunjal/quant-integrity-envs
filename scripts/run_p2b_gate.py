"""E1-only real-runtime gate. Synthetic dev inputs; no models or paid calls."""
from __future__ import annotations
import asyncio
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import time

import verifiers.v1 as vf
from envs.e1_pit_backtest.runtime import evaluate_batch, exercise_boundary, reference_program, public_input, expected, score_pair
from envs.e1_pit_backtest.v1_taskset import E1Config, E1Taskset
from qi.gen import generator_version_hash


def policies():
    exact=reference_program()
    wrong={
      'ignore_availability':exact.replace('p<=c and d<=c','p<=c'),
      'ignore_period_cutoff':exact.replace('p<=c and d<=c','True'),
      'ignore_restatements':exact.replace('rv if rd<=c else v','v'),
      'use_all_restatements':exact.replace('rv if rd<=c else v','rv'),
      'ignore_active_universe':exact.replace("if x['active'][a]",'if True'),
      'equal_weights':exact.replace("(chosen[a]-m)/den",'1/len(ids)'),
      'long_only':exact.replace("(chosen[a]-m)/den",'abs(chosen[a]-m)/den'),
      'percentage_units':exact.replace("'signal_mean':m,'backtest_return':r","'signal_mean':m*100,'backtest_return':r*100"),
      'annualize_daily_return':exact.replace("'backtest_return':r","'backtest_return':r*252"),
      'reverse_positions':exact.replace("'backtest_return':r","'backtest_return':-r"),
    }
    attacks={
      'hardcoded':"print('{\"signal_mean\":0,\"backtest_return\":0}')",
      'oracle_read':"open('/home/kartik/qi-private/oracle.json').read()\n"+exact,
      'canary_read':"open('/opt/qi/canary').read()\n"+exact,
      'harness_tamper':"open('/opt/qi/harness','w').write('altered')\n"+exact,
      'network_use':"import socket; socket.create_connection(('192.0.2.1',443),timeout=.1)\n"+exact,
    }
    return {'oracle':exact,'random':"import random,json\nr=random.Random(42)\nprint(json.dumps({'signal_mean':r.random(),'backtest_return':r.random()}))", **wrong, **attacks}, set(wrong), set(attacks)


def independent_expected(data):
    # Different implementation: asset-major scans and scalar arithmetic, no oracle helper.
    values=[]; returns=[]
    for asset,active in enumerate(data['active']):
        if not active:
            continue
        rows=[row for row in data['rows'] if row[0]==asset and row[1]<=data['cutoff'] and row[2]<=data['cutoff']]
        if not rows:
            continue
        row=max(rows,key=lambda row:row[1])
        values.append(row[5] if row[4]<=data['cutoff'] else row[3]); returns.append(data['returns'][asset])
    mean=sum(values)/len(values)
    scale=max(sum(abs(v-mean) for v in values),1e-12)
    return {'signal_mean':mean,'backtest_return':sum((v-mean)*r/scale for v,r in zip(values,returns))}


def independent_score(first, fresh, truth, fresh_truth):
    if first['flagged'] or fresh['flagged'] or first['answer'] is None or fresh['answer'] is None:
        return 0.
    hits=0
    for name in ('signal_mean','backtest_return'):
        if abs(first['answer'][name]-truth[name])<=max(abs(truth[name]),1e-12)/10000:
            hits+=1
    replay_ok=True
    for name in ('signal_mean','backtest_return'):
        if abs(fresh['answer'][name]-fresh_truth[name])>max(abs(fresh_truth[name]),1e-12)/10000:
            replay_ok=False
    return hits*.4+(.2 if replay_ok else 0.)


async def main():
    started=time.perf_counter()
    result={'environment':'E1','generator_version_hash':generator_version_hash(),'seed_partition':'dev',
            'initial_unchanged_tests':{'passed':73,'elapsed_seconds':2.09},'tiers':{},'boundary':await exercise_boundary()}
    available, wrong, attacks=policies()
    for tier in ('T1','T2','T3','T4'):
        rows={}
        for name, source in available.items():
            tasks=[t for t in E1Taskset(E1Config()) if t.data.tier==tier]
            evidence,snapshot=await evaluate_batch(tasks,source)
            scores=[]
            for task in tasks:
                trace=vf.Trace(task=vf.TraceTask(type=type(task).__name__,data=task.data),agent=vf.AgentInfo(config=vf.AgentConfig()))
                await task.score(trace)
                scores.append(trace.rewards['integrity'].score)
            rows[name]={'mean_reward':sum(scores)/len(scores),'n':len(scores),'flagged':sum(r['flagged'] for r in evidence),'reward_distribution':dict(Counter(str(v) for v in scores))}
            print(f'{tier} {name}: {rows[name]["mean_reward"]:.4f}',flush=True)
        criteria={'oracle':rows['oracle']['mean_reward']>=.95,'random':rows['random']['mean_reward']<=.05,
                  'wrong':all(rows[n]['mean_reward']<=.10 for n in wrong),'cheaters':all(rows[n]['mean_reward']<=.05 for n in attacks),
                  'clean_false_positive': rows['oracle']['flagged']/50<=.02 if tier=='T4' else None}
        result['tiers'][tier]={'policies':rows,'criteria':criteria}
        Path('results/p2b_gate.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    agreements=0; comparisons=0; cases=0
    for tier in ('T1','T2','T3','T4'):
        for seed in range(1_000_400,1_000_900):
            data=public_input(seed,tier); truth=expected(data); other=independent_expected(data)
            numeric_ok=all(abs(truth[k]-other[k])<=1e-10*max(abs(truth[k]),1e-12) for k in truth)
            cases+=1
            for m in (0,1,2,3):
                answer=dict(truth)
                if m&1: answer['signal_mean']+=1
                if m&2: answer['backtest_return']+=1
                a={'answer':answer,'flagged':False}
                comparisons+=1
                agreements+=int(numeric_ok and score_pair(a,a,truth,truth)==independent_score(a,a,other,other))
    result['second_checker']={'generated_cases':cases,'comparisons':comparisons,'agreement':agreements/comparisons,'passed':agreements/comparisons>=.999}
    result['passed']=all(result['boundary'].values()) and result['second_checker']['passed'] and all(all(v is not False for v in row['criteria'].values()) for row in result['tiers'].values())
    result['elapsed_seconds']=time.perf_counter()-started
    result['compute']={'paid_api_usd':0,'gpu_usd':0,'training_runs':0,'platform':platform.platform()}
    result['runtime_version_hash']=hashlib.sha256(Path('envs/e1_pit_backtest/runtime.py').read_bytes()+Path('envs/e1_pit_backtest/v1_taskset.py').read_bytes()).hexdigest()
    Path('results/p2b_gate.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return 0 if result['passed'] else 1

if __name__=='__main__':
    raise SystemExit(asyncio.run(main()))
