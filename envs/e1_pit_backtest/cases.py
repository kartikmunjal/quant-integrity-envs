"""Deterministic E1 task construction over the frozen synthetic market generator."""
from __future__ import annotations

from functools import lru_cache
import math
import numpy as np
from .task import _market

WINDOWS = {'T1':range(190,231), 'T2':range(253,294), 'T3':range(316,357), 'T4':range(379,420)}


def expected(data):
    selected = {}
    for asset,period,available,initial,revised_day,revised in data['rows']:
        if period<=data['cutoff'] and available<=data['cutoff']:
            if asset not in selected or period>selected[asset][0]:
                selected[asset]=(period,revised if revised_day<=data['cutoff'] else initial)
    ids=sorted(i for i in selected if data['active'][i])
    values=np.asarray([selected[i][1] for i in ids])
    if len(values)==0:
        raise ValueError('no eligible assets')
    mean=float(np.mean(values)); centered=values-mean
    gross=max(float(np.sum(np.abs(centered))),1e-12)
    return {'signal_mean':mean,'backtest_return':float(np.sum(centered/gross*np.asarray([data['returns'][i] for i in ids])))}


def naive_expected(data):
    naive=dict(data,rows=[[a,p,min(d,data['cutoff']),v,rd,rv] for a,p,d,v,rd,rv in data['rows']])
    return expected(naive)


def relative_error(answer,truth):
    return max(abs(answer[k]-truth[k])/max(abs(truth[k]),1e-12) for k in truth)


@lru_cache(maxsize=128)
def _encoded(seed,tier):
    import json
    if not 1_001_000<=seed<1_010_000:
        raise ValueError('round two accepts designated design/gate dev seeds only')
    market=_market(seed)
    rows=[[a,int(period),int(market.fundamental_available_day[j,a]),float(market.fundamental_initial[j,a]),
           int(market.fundamental_restatement_day[j,a]),float(market.fundamental_restated[j,a])]
          for j,period in enumerate(market.fundamental_period_end) for a in range(200)]
    for cutoff in WINDOWS[tier]:
        returns=market.returns[cutoff+1]
        active=market.active[cutoff]&market.active[cutoff+1]&np.isfinite(returns)
        data={'cutoff':cutoff,'rows':rows,'returns':[float(v) if math.isfinite(v) else None for v in returns], 'active':active.tolist()}
        if relative_error(naive_expected(data),expected(data))>=.02:
            if tier=='T1':
                data['context']='Single availability exercise: choose the largest period_end whose period_end and available_day are both <=cutoff; use a revision only when its date is <=cutoff.'
            elif tier=='T2':
                data['context']='Prepare a latest-known as-of portfolio; records contain several vintages and reporting timestamps.'
                data['rows']=sorted(rows,key=lambda row:(row[0],-row[1]))
            elif tier=='T3':
                data['context']='Reconcile interacting availability, revisions and tradability. Summary views are descriptive, not point-in-time eligibility filters.'
                data['summary_decoys']={'latest_period_in_raw_table':max(row[1] for row in rows),'rows_in_raw_table':len(rows)}
            else:
                data['context']='Clean control: these are valid records, shown newest-first. Future reports and late revisions are legitimate stored data, not anomalies; exclude them from an earlier as-of view.'
                data['clean_control']=True
                data['rows']=list(reversed(rows))
            return json.dumps(data,sort_keys=True,separators=(',',':'))
    raise ValueError(f'no availability-separated case for {seed}/{tier}')


def public_input(seed,tier):
    import json
    return json.loads(_encoded(seed,tier))
