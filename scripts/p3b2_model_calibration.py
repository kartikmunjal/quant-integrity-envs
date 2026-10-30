"""Prospective normal-max model calibration from construction parameters only.

No submitted policy or actual-episode reward is evaluated. These model-based
bounds are hypotheses for validation, not guarantees for heavy-tailed portfolios.
"""
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist
import time
from collections import Counter

from envs.e3_fdr_adjudication.cases import TIERS
from envs.e3_fdr_adjudication.presentation import make_case
from envs.e3_fdr_adjudication.reward import raw_loss,L_REF
from envs.e3_fdr_adjudication.v1_taskset import populations


def model_posterior(z,count,effects):
    def log_density(mean):
        x=z-mean
        return math.log(count)-x*x/2-math.log(2*math.pi)/2+(count-1)*math.log(max(.5*math.erfc(-x/math.sqrt(2)),1e-300))
    values=[log_density(effect) for effect in effects]
    pivot=max(values)
    log_real=pivot+math.log(sum(math.exp(value-pivot) for value in values)/len(values))
    odds=max(-700,min(700,log_real-log_density(0.)))
    return 1/(1+math.exp(-odds))


def expected_candidate(count,effects,actual_effect,truth,cells=512):
    loss=0.;false_admit=0
    for i in range(cells):
        uniform=(i+.5)/cells
        z=NormalDist().inv_cdf(uniform**(1/count))+actual_effect
        probability=model_posterior(z,count,effects)
        loss+=raw_loss(probability,truth)
        false_admit+=not truth and probability>.75
    return loss/cells,false_admit/cells


def main():
    started=time.monotonic();rows=[]
    seeds=populations()['design']
    for seed in seeds:
        for tier in TIERS:
            case=make_case(seed,tier)
            effect_map=case['public']['hypothesis']['effect_t_by_coefficient']
            effects=list(effect_map.values())
            configurations=Counter()
            for candidate in case['public']['candidates']:
                key=candidate['id'];truth=case['truth'][key]
                count=1+(candidate['N']-1)*(1-candidate['rho'])
                coefficient=case['oracle_details'][key]['effect_coefficient']
                actual=effect_map[str(coefficient)] if truth else 0.
                configurations[(count,actual,truth)]+=1
            loss=0.;false_admit=0.
            for (count,actual,truth),number in configurations.items():
                expected,fp=expected_candidate(count,effects,actual,truth)
                loss+=number*expected/20
                false_admit+=number*fp/10
            rows.append({'seed':seed,'tier':tier,'expected_raw_loss':loss,'expected_null_false_admit_rate':false_admit,'hypothesis_effect_t':effects,'primitive_data_sha256':case['primitive_data_sha256']})
    tiers={}
    for tier in TIERS:
        selected=[row for row in rows if row['tier']==tier]
        loss=sum(row['expected_raw_loss'] for row in selected)/len(selected)
        fp=sum(row['expected_null_false_admit_rate'] for row in selected)/len(selected)
        bound=max(0.,1-2*loss/L_REF)
        tiers[tier]={'model_expected_raw_loss':loss,'model_paired_reward_lower_bound':bound,
                     'honest_floor':math.floor(.5*bound*100)/100,
                     'model_null_false_admit_rate':fp,'honest_false_admit_ceiling':min(1.,math.ceil((fp+.02)*100)/100)}
    from qi.gen import generator_version_hash
    value={'environment':'E3','generator_version_hash':generator_version_hash(),
           'kind':'pre-policy construction-parameter model calculation, not measured E3 policy performance',
           'formula':'R>=1-L/Lref; min(R1,R2)>=1-(L1+L2)/Lref. Under stated approximate marginals use half of positive paired mean bound, rounded down .01, as floor. Null false-admit ceiling is model mean plus .02 rounded up .01.',
           'limitations':'Normal effective-max marginal approximation; not a proven bound for actual heavy-tailed correlated portfolio returns. Floors cannot be lowered after actual policy measurement.',
           'tiers':tiers,'rows':rows,'policy_runs_before_calculation':0,'api_usd':0,'gpu_usd':0,'wall_seconds':time.monotonic()-started,
           'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path('envs/e3_fdr_adjudication/cases.py'),Path('results/p3b2_screen.json')]}}
    with Path('results/p3b2_model_calibration.json').open('x') as f:
        json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps(tiers,indent=2))

if __name__=='__main__':
    main()
