"""Design-only deterministic numeric diagnostics; never accepts gate seeds."""
import json
from pathlib import Path
import time
import numpy as np
from envs.e1_pit_backtest.cases import public_input,expected,relative_error
from qi.gen import generator_version_hash

WRONG=('ignore_availability','ignore_period_cutoff','ignore_restatements','use_all_restatements','ignore_active_universe','equal_weights','long_only','percentage_units','annualize_daily_return','reverse_positions')


def alternative(data,name):
    chosen={}
    c=data['cutoff']
    for a,p,d,v,rd,rv in sorted(data['rows'],key=lambda row:row[1]):
        eligible=(p<=c and d<=c)
        if name=='ignore_availability': eligible=p<=c
        if name=='ignore_period_cutoff': eligible=True
        if eligible:
            chosen[a]=v if name=='ignore_restatements' else (rv if name=='use_all_restatements' or rd<=c else v)
    ids=sorted(a for a in chosen if data['active'][a] or name=='ignore_active_universe')
    v=np.array([chosen[a] for a in ids]); m=float(np.mean(v)); weights=(v-m)/max(float(np.sum(np.abs(v-m))),1e-12)
    if name=='equal_weights': weights=np.ones(len(ids))/len(ids)
    if name=='long_only': weights=np.abs(weights)
    r=float(np.sum(weights*np.array([data['returns'][a] or 0 for a in ids])))
    if name=='percentage_units': m*=100;r*=100
    if name=='annualize_daily_return': r*=252
    if name=='reverse_positions': r=-r
    return {'signal_mean':m,'backtest_return':r}


def main(count=1000):
    started=time.perf_counter(); rows={}
    for tier in ('T1','T2','T3','T4'):
        gaps={name:[] for name in WRONG}; failures=[]
        for seed in range(1_001_000,1_001_000+count):
            try:
                data=public_input(seed,tier); truth=expected(data)
                for name in WRONG: gaps[name].append(relative_error(alternative(data,name),truth))
            except ValueError as error:
                failures.append({'seed':seed,'error':str(error)})
        rows[tier]={'n':count,'construction_failures':failures,'wrong':{name:{'min_error':min(values) if values else None,'below_zero_scale':sum(v<.01 for v in values)} for name,values in gaps.items()}}
    record={'environment':'E1','generator_version_hash':generator_version_hash(),'seed_start':1001000,'count':count,'tiers':rows,'elapsed_seconds':time.perf_counter()-started}
    Path('results/p2b2_design_study.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=1000);a=p.parse_args()
    if not 1<=a.count<=1000: raise ValueError('design count must be 1..1000')
    main(a.count)
