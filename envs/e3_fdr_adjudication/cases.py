"""Development-only generator-derived selected strategy returns; no policy calls."""
import hashlib
import json
import math
from functools import lru_cache

import numpy as np
from qi.gen import GeneratorConfig, generate_market, generator_version_hash

TIERS=('T1','T2','T3','T4')
SCHEDULES={'T1':([1,4,16],1.,.1),'T2':([20,100,500],.5,.3),
           'T3':([1,50,500],.5,.7),'T4':([1,500],None,.5)}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


@lru_cache(maxsize=4)
def market_for(seed):
    if type(seed) is not int or not 1000000<=seed<=1009999:
        raise ValueError('E3 development seed required')
    return generate_market(seed,config=GeneratorConfig(n_assets=200,n_days=500,force_alpha=True))


def make_case(seed,tier):
    if tier not in TIERS:
        raise ValueError('unknown tier')
    market=market_for(seed)
    material=hashlib.sha256(f'E3:{seed}:{tier}:round2'.encode()).digest()
    rng=np.random.default_rng(int.from_bytes(material[:16],'big'))
    returns=market.returns[1:]
    alpha=np.mean(market.signal[:-1]*returns,axis=1)
    scale=.01/float(np.std(returns))
    n_days=returns.shape[0]
    def null_paths(count):
        assets=rng.integers(0,returns.shape[1],size=(count,n_days))
        signs=rng.integers(0,2,size=(count,n_days))*2-1
        return returns[np.arange(n_days),assets]*signs
    shared=null_paths(2)
    labels=np.array([0]*10+[1]*10)
    rng.shuffle(labels)
    counts,coefficient,rho=SCHEDULES[tier]
    per_class=[0,0];public=[];truth={};effects={};details={}
    hypothesis={}
    for c in ((.4,1.5) if tier=='T4' else (coefficient,)):
        hypothesis[str(c)]=float(c*np.mean(alpha)/np.std(returns)*math.sqrt(n_days))
    for i,y in enumerate(labels.tolist()):
        index=per_class[y];per_class[y]+=1
        trials=500 if tier=='T4' and not y else counts[index%len(counts)]
        effect_coefficient=(.4 if index%2==0 else 1.5) if tier=='T4' else coefficient
        group=i%2
        paths=math.sqrt(1-rho)*null_paths(trials)+math.sqrt(rho)*shared[group]
        if y:
            paths=paths+effect_coefficient*alpha
        paths*=scale
        deviations=np.std(paths,axis=1,ddof=1)
        if not np.isfinite(paths).all() or (deviations<=0).any():
            raise ValueError('inadmissible nonfinite or constant return path')
        means=np.mean(paths,axis=1)
        selected=int(np.argmax(means/deviations))
        values=paths[selected]
        identifier='s-'+hashlib.sha256(f'{seed}:{tier}:{i}'.encode()).hexdigest()[:16]
        public.append({'id':identifier,'N':trials,'group':group,'rho':rho,
                       'returns':values.tolist(),'t_stat':float(means[selected]/deviations[selected]*math.sqrt(n_days)),
                       'sharpe':float(means[selected]/deviations[selected]*math.sqrt(252))})
        truth[identifier]=y
        effects[identifier]=float(effect_coefficient*np.mean(alpha)*scale) if y else 0.
        details[identifier]={'real':y,'effect_coefficient':effect_coefficient if y else 0.,
                             'added_mean':effects[identifier],'selected_trial':selected,
                             'N':trials,'group':group,'rho':rho}
    public={'candidates':public,'hypothesis':{'effect_t_by_coefficient':hypothesis},
            'contract':'Selected best of N in-sample trial paths; output JSON mapping every candidate id to P(real). Membership is mixed, exactly ten of twenty real. The hypothesis effect distribution is common to all candidates and does not reveal their individual mixing coefficient. Group-shared signed market paths introduce correlation. Admit only above .75 for 3:1 decision costs.'}
    return {'public':public,'truth':truth,'effects':effects,'oracle_details':details,
            'generator_version_hash':generator_version_hash(),'data_sha256':digest(public),
            'seed':seed,'tier':tier,'real_fraction':.5}
