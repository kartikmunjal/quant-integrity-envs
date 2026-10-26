"""Design-only financial diagnostics; no E5 gate seeds or submitted code execute."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import time
import numpy as np
from envs.e5_cost_realism.cases import public_input,case_diagnostics
from envs.e5_cost_realism.finance import canonical_weights,metrics
from envs.e5_cost_realism.reward import score_pair
from envs.e5_cost_realism import checker
from scripts.e5_policies import WRONG
from qi.gen import generator_version_hash


def alternative(data,mode):
    signals=np.asarray(data['signals']);caps=np.asarray(data['capacity_usd'])/data['notional'];old=np.zeros(len(caps));weights=[]
    for signal in signals:
        centered=signal-np.mean(signal);target=centered/max(float(np.sum(np.abs(centered))),1e-12)
        row=target if mode=='ignore_capacity' else np.clip(old+np.clip(target-old,-caps,caps),-caps,caps)
        if mode=='renormalize_after_capacity':row=row/max(float(np.sum(np.abs(row))),1e-12)
        weights.append(row.copy());old=row
    weights=np.asarray(weights)
    def cost(delta):
        mag=np.abs(delta);part=mag*data['notional']/np.asarray(data['adv_usd'])
        spread=np.asarray(data['spread_bps'])/20000.;impact=np.asarray(data['impact_coefficient'])*np.sqrt(part)/100.
        if mode=='ignore_spread':spread=np.zeros_like(spread)
        if mode=='ignore_impact':impact=np.zeros_like(impact)
        if mode=='full_spread':spread*=2
        if mode=='linear_impact':impact=np.asarray(data['impact_coefficient'])*part/100.
        return np.sum(mag*(spread+impact),axis=-1)
    delta=np.diff(np.vstack([np.zeros(len(caps)),weights]),axis=0)
    gross=np.sum(weights*np.asarray(data['returns']),axis=1)
    charge=cost(weights if mode=='positions_as_turnover' else delta)
    multiplier=.5 if mode=='half_turnover' else 2. if mode=='double_turnover' else 1.
    net=gross-charge*multiplier
    if mode!='omit_terminal_close':net[-1]-=float(cost(weights[-1]))*multiplier
    sharp=lambda v:float(math.sqrt(252)*np.mean(v)/max(float(np.std(v)),1e-12))
    edge=float(np.mean(gross));holding=float(np.mean(2*cost(weights))*multiplier/edge) if edge>0 else math.inf
    s=sharp(gross if mode in ('ignore_costs','gross_not_net') else net)
    if mode=='ignore_costs':holding=0.
    return {'weights':weights.tolist(),'net_sharpe':s,'breakeven_holding_days':holding}


def main(count,output):
    started=time.perf_counter();tiers={};agreements=0;comparisons=0
    for tier in ('T1','T2','T3','T4'):
        bounds={mode:[] for mode in WRONG};failures=[];cost_gaps=[];cap_gaps=[];terminal_gaps=[]
        for seed in range(1004000,1004000+count):
            try:
                data=public_input(seed,tier);weights=canonical_weights(data);truth=metrics(data,weights)
                oracle={'answer':dict(weights=weights,net_sharpe=truth['net_sharpe'],breakeven_holding_days=truth['breakeven_holding_days']),'flagged':False,'exit_code':0}
                d=case_diagnostics(data);cost_gaps.append(d['cost_gap']);cap_gaps.append(d['capacity_binding_gap']);terminal_gaps.append(d['terminal_close_gap'])
                for mode in WRONG:
                    record={'answer':alternative(data,mode),'flagged':False,'exit_code':0}
                    bound=score_pair(record,oracle,data,data);other=checker.score_pair(record,oracle,data,data)
                    bounds[mode].append(bound);agreements+=int(abs(bound-other)<=1e-8);comparisons+=1
            except ValueError as error:failures.append({'seed':seed,'error':str(error)})
        tiers[tier]={'n':count,'construction_failures':failures,'min_cost_gap':min(cost_gaps,default=None),'min_capacity_binding_gap':min(cap_gaps,default=None),'min_terminal_close_gap':min(terminal_gaps,default=None),
            'wrong_primary_upper_bounds':{mode:{'mean':sum(values)/len(values) if values else None,'positive_fraction':sum(v>0 for v in values)/len(values) if values else None,'maximum':max(values,default=None)} for mode,values in bounds.items()}}
    result={'environment':'E5','generator_version_hash':generator_version_hash(),'seed_start':1004000,'count':count,'tiers':tiers,'independent_agreement':agreements/comparisons if comparisons else None,'comparisons':comparisons,'elapsed_seconds':time.perf_counter()-started,
        'scope':'Numerical design diagnostics only; upper bound pairs wrong primary with exact replay on same design input. No submitted source executes on host.'}
    Path(output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=1000);p.add_argument('--output',default='results/p2c_design_study.json');a=p.parse_args()
    if not 1<=a.count<=1000:raise ValueError('design count must be 1..1000')
    main(a.count,a.output)
