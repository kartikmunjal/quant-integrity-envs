"""Reproduce incentives, reliability and construction gaps from retained vectors."""
import gzip
import hashlib
import json
import math
from pathlib import Path
from fractions import Fraction
from envs.e3_fdr_adjudication.reward import execution_reward
from scripts.p3b2_diagnostics import load_independent

TEMPERATURES=(0.,.25,.5,.75,1.,1.5,2.,4.,100.)


def transform(q,kind,amount):
    if kind=='toward_zero':
        return amount*q
    if kind=='toward_one':
        return 1-amount*(1-q)
    if amount==0:
        return .5
    if q in (0,1):
        return q
    odds=max(-700,min(700,amount*(math.log(q)-math.log1p(-q))))
    return 1/(1+math.exp(-odds))


def main():
    path=Path('results/p3b2_design_vectors.json')
    summary=json.loads(path.read_text())
    rows=[]
    for shard in summary['row_shards']:
        raw=Path(shard['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=shard['sha256']:
            raise ValueError('diagnostic evidence drift')
        rows.extend(json.loads(line) for line in gzip.decompress(raw).splitlines())
    output={}
    settings=[('temperature',t) for t in TEMPERATURES]+[(kind,t) for kind in ('toward_zero','toward_one') for t in (0.,.25,.5,.75,1.)]
    floors=json.loads(Path('results/p3b2_model_calibration.json').read_text())['tiers']
    for tier in ('T1','T2','T3','T4'):
        selected=[row for row in rows if row['tier']==tier]
        bins=[{'count':0,'probability_sum':0.,'real_count':0} for _ in range(10)]
        null_count=0;false_admit=0;oracle_false=0
        transformed={f'{kind}:{amount}':[] for kind,amount in settings}
        for row in selected:
            for stage in range(2):
                for key,y in row['truth'][stage].items():
                    q=row['probabilities']['honest'][stage][key]
                    slot=bins[min(9,int(q*10))]
                    slot['count']+=1;slot['probability_sum']+=q;slot['real_count']+=y
                    null_count+=not y;false_admit+=not y and q>.75
                    oracle_false+=not y and row['probabilities']['oracle'][stage][key]>.75
            for kind,amount in settings:
                rewards=[]
                for stage in range(2):
                    truth=row['truth'][stage];prob=row['probabilities']['honest'][stage]
                    rewards.append(execution_reward([transform(prob[key],kind,amount) for key in truth],list(truth.values())))
                transformed[f'{kind}:{amount}'].append(min(rewards))
        baseline=sum(row['scores']['honest'] for row in selected)/len(selected)
        means={key:sum(values)/len(values) for key,values in transformed.items()}
        best=max(means,key=means.get)
        reliability=[{'bin':[i/10,(i+1)/10],'count':b['count'],'mean_probability':b['probability_sum']/b['count'] if b['count'] else None,'real_fraction':b['real_count']/b['count'] if b['count'] else None} for i,b in enumerate(bins)]
        ece=sum(abs(b['mean_probability']-b['real_fraction'])*b['count'] for b in reliability if b['count'])/sum(b['count'] for b in reliability)
        wrong=[key.split('/')[0] for key in summary['per_policy_tier'] if key.endswith('/'+tier) and key.split('/')[0] not in ('oracle','random','honest','shallow')]
        output[tier]={'design_case_count':len(selected),'failed_case_gaps':sum(not row['all_gaps_pass'] for row in selected),
                      'per_wrong_min_gap':{mode:min(row['honest_minus_wrong_gaps'][mode] for row in selected) for mode in wrong},
                      'baseline_honest_mean':baseline,'adopted_floor':floors[tier]['honest_floor'],
                      'transformed_means':means,'best_transform':best,'maximum_gain':means[best]-baseline,
                      'incentive_pass':means[best]-baseline<=.02,
                      'honest_null_false_admits':false_admit,'oracle_null_false_admits':oracle_false,
                      'null_candidate_executions':null_count,'honest_null_false_admit_rate':false_admit/null_count,
                      'adopted_honest_false_admit_ceiling':floors[tier]['honest_false_admit_ceiling'],
                      'honest_false_admit_pass':false_admit/null_count<=floors[tier]['honest_false_admit_ceiling'],
                      'reliability':reliability,'expected_calibration_error':ece}
    checker=load_independent('e3_round2_checker');p=Fraction(9,10)
    a=[1]*4+[0]*4;b=[0]*4+[1]*4;q=[p]*4+[1-p]*4
    fixture={'K':8,'truthful_expected':str(p*checker.execution(q,a)+(1-p)*checker.execution(q,b)),
             'deterministic_expected':str(p*checker.execution(a,a)+(1-p)*checker.execution(a,b))}
    result={'environment':'E3','generator_version_hash':summary['generator_version_hash'],'kind':'development-vector sensitivity; not checked gate results',
            'tiers':output,'fixed_reference_exact_rational_counterexample':fixture,'design_summary_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'api_usd':0,'gpu_usd':0}
    with Path('results/p3b2_sensitivity.json').open('x') as f:
        json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps({tier:{key:v[key] for key in ('failed_case_gaps','maximum_gain','honest_null_false_admit_rate','honest_false_admit_pass')} for tier,v in output.items()},indent=2))

if __name__=='__main__':
    main()
