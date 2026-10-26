"""Deterministic E5 exercises over the frozen synthetic generator's cost model."""
from __future__ import annotations
from functools import lru_cache
import json
import math
import numpy as np
from .task import _market
from .finance import canonical_weights,metrics

TIERS=('T1','T2','T3','T4')
STARTS={'T1':range(80,121),'T2':range(160,201),'T3':range(240,281),'T4':range(320,361)}


def case_diagnostics(data):
    signals=np.asarray(data['signals']);centered=signals-signals.mean(axis=1,keepdims=True)
    raw=centered/np.maximum(np.sum(np.abs(centered),axis=1,keepdims=True),1e-12)
    caps=np.asarray(data['capacity_usd'])/data['notional']
    truth=metrics(data,canonical_weights(data))
    return {'cost_gap':abs(truth['gross_sharpe']-truth['net_sharpe'])/max(abs(truth['net_sharpe']),1e-12),
        'capacity_binding_gap':float(np.max(np.abs(raw)/caps)-1),
        'oracle_gross_mean':truth['gross_mean']}


@lru_cache(maxsize=128)
def _encoded(seed,tier):
    if not 1004000<=seed<1010000:raise ValueError('P2c design/fresh E5 dev seeds only')
    market=_market(seed)
    for start in STARTS[tier]:
        candidates=np.flatnonzero(market.active[start-1:start+48].all(axis=0))
        if len(candidates)<8:continue
        for offset in range(0,len(candidates)-7,8):
            assets=candidates[offset:offset+8]
            if tier=='T4':assets=assets[::-1]
            signals=market.signal[start-1:start+47,assets]
            returns=market.returns[start:start+48,assets]
            for factor in (2.,4.,8.):
                data={'signals':signals.tolist(),'returns':returns.tolist(),
                    'spread_bps':market.spread_bps[assets].tolist(),
                    'impact_coefficient':market.impact_coefficient[assets].tolist(),
                    'adv_usd':market.adv_usd[assets].tolist(),'capacity_usd':market.capacity_usd[assets].tolist(),
                    'notional':float(factor*8*np.median(market.capacity_usd[assets])),
                    'asset_ids':[f'A{int(a):05d}' for a in assets],
                    'rules':{'target':'demean each signal row, divide by its sum of absolute centered values, clip trades and positions by capacity_usd/notional, do not renormalize',
                    'one_way_rate':'spread_bps/20000 + impact_coefficient*sqrt(abs(delta_weight)*notional/adv_usd)/100',
                    'net_pnl':'sum(weight*return) minus actual trade cost; start from zero and charge terminal liquidation to final session',
                    'net_sharpe':'sqrt(252)*mean(net_pnl)/max(population_std(net_pnl),1e-12)',
                    'breakeven_holding_days':'mean hypothetical fresh roundtrip cost of each session portfolio divided by mean daily gross PnL; stationary-edge approximation'},
                    'context':{
                        'T1':'Explicit cost exercise: charge half-spread plus square-root impact on every opening, change and closing trade; cash left by capacity clipping is not reinvested.',
                        'T2':'Audit daily turnover and holding-period conventions for the specified gross strategy.',
                        'T3':'Combine binding position/trade capacity and transaction-cost accounting. Descriptive summaries do not replace actual turnover.',
                        'T4':'Clean control: units are correctly labelled and asset order is reversed consistently. These are harmless presentation choices; capacity and all costs still apply.'}[tier]}
                if tier=='T3':data['summary_decoy']={'equal_weight_spread_bps':float(np.mean(market.spread_bps[assets]))}
                if tier=='T4':data['units']={'spread_bps':'basis points, quoted full spread','notional':'synthetic USD','weights':'fractions of fixed notional; no post-clip renormalization'}
                weights=canonical_weights(data);truth=metrics(data,weights);diagnostic=case_diagnostics(data)
                if (truth['gross_mean']>1e-7 and abs(truth['net_sharpe'])>1e-6
                    and math.isfinite(truth['breakeven_holding_days']) and truth['breakeven_holding_days']>0
                    and diagnostic['cost_gap']>=.02 and diagnostic['capacity_binding_gap']>=.02):
                    return json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False)
    raise ValueError(f'no positive-edge cost/capacity-separated E5 candidate for {seed}/{tier}')


def public_input(seed,tier):return json.loads(_encoded(seed,tier))
