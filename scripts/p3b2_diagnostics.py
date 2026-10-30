"""Trusted design-vector diagnostics after committed structural screen.

These are not Docker rollouts, stress, or the one-shot environment gate. They
check the named deterministic policy mathematics without running submitted code
on the host. No case is removed after a policy is measured.
"""
import hashlib
import gzip
import math
import importlib.util
import json
from pathlib import Path
import time

from envs.e3_fdr_adjudication.cases import TIERS
from envs.e3_fdr_adjudication.presentation import make_case
from envs.e3_fdr_adjudication.reward import execution_reward
from envs.e3_fdr_adjudication.v1_taskset import populations,replay_seed


def load_independent(name):
    path=Path('tests/validation')/(name+'.py')
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def diagnostics(seeds):
    policies=load_independent('e3_round2_policies')
    checker=load_independent('e3_round2_checker')
    modes=('oracle','random','honest','shallow')+policies.WRONG_POLICIES
    rows=[];agreements=0;comparisons=0
    for seed in seeds:
        for tier in TIERS:
            cases=[make_case(s,tier) for s in (seed,replay_seed(seed,tier))]
            scores={};answers={}
            for mode in modes:
                if mode=='hardcoded_ids':
                    snapshot=policies.probability_vectors(cases[0]['public'],'honest')
                    vectors=[snapshot,snapshot]
                else:
                    vectors=[case['truth'] if mode=='oracle' else policies.probability_vectors(case['public'],mode) for case in cases]
                rewards=[]
                for case,vector in zip(cases,vectors):
                    ids=list(case['truth'])
                    if set(vector)!=set(case['truth']):
                        rewards.append(0.)
                        continue
                    q=[vector[key] for key in ids];y=list(case['truth'].values())
                    reward=execution_reward(q,y)
                    audited=float(checker.execution(q,y))
                    comparisons+=1;agreements+=abs(reward-audited)<=1e-12
                    rewards.append(reward)
                scores[mode]=min(rewards);answers[mode]=vectors
            gaps={mode:scores['honest']-scores[mode] for mode in policies.WRONG_POLICIES}
            rows.append({'seed':seed,'tier':tier,'replay_seed':cases[1]['seed'],
                         'data_sha256':[case['data_sha256'] for case in cases],
                         'truth':[case['truth'] for case in cases],
                         'probabilities':answers,'scores':scores,'honest_minus_wrong_gaps':gaps,
                         'all_gaps_pass':all(gap>=.02 for gap in gaps.values())})
        print(json.dumps({'completed_design_seeds':len(rows)//4,'rows':len(rows)}),flush=True)
    return {'rows':rows,'agreement':agreements/comparisons if comparisons else None,
            'comparisons':comparisons,'agreements':agreements,
            'all_case_gaps_pass':bool(rows) and all(row['all_gaps_pass'] for row in rows)}


def store_rows(rows):
    folder=Path('results/p3b2_design_vectors')
    folder.mkdir(exist_ok=False)
    shards=[]
    for start in range(0,len(rows),25):
        batch=rows[start:start+25]
        raw=b'\n'.join(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False).encode() for row in batch)+b'\n'
        packed=gzip.compress(raw,mtime=0)
        if len(packed)>1024*1024:
            raise ValueError('diagnostic shard exceeds tracked file cap')
        path=folder/f'{start//25:04d}.jsonl.gz'
        path.write_bytes(packed)
        shards.append({'path':str(path),'sha256':hashlib.sha256(packed).hexdigest(),'bytes':len(packed),'rows':len(batch)})
    return shards


def main():
    started=time.monotonic()
    seeds=populations()['design']
    result=diagnostics(seeds)
    from qi.gen import generator_version_hash
    sources=[Path(__file__),*Path('envs/e3_fdr_adjudication').glob('*.py'),*Path('tests/validation').glob('e3_round2*.py')]
    result.update(environment='E3',generator_version_hash=generator_version_hash(),
                  kind='trusted mathematical design vectors; not checked executions or a gate',
                  source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                  screened_design_population=seeds,policy_rows=sum(len(row['scores']) for row in result['rows']),
                  docker_rollouts=0,api_usd=0,gpu_usd=0,wall_seconds=time.monotonic()-started)
    rows=result.pop('rows')
    result['per_policy_tier']={}
    for tier in TIERS:
        for mode in rows[0]['scores'] if rows else []:
            values=[row['scores'][mode] for row in rows if row['tier']==tier]
            result['per_policy_tier'][mode+'/'+tier]={'count':len(values),'mean':sum(values)/len(values)}
    result['failed_case_count']=sum(not row['all_gaps_pass'] for row in rows)
    result['row_shards']=store_rows(rows)
    with Path('results/p3b2_design_vectors.json').open('x') as f:
        json.dump(result,f,sort_keys=True,indent=2);f.write('\n')

if __name__=='__main__':
    main()
