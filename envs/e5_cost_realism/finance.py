"""Trusted E5 gross-signal execution and cost calculation over synthetic inputs."""
from __future__ import annotations
import math
import numpy as np


def canonical_weights(data):
    signals=np.asarray(data['signals'],dtype=float)
    caps=np.asarray(data['capacity_usd'],dtype=float)/data['notional']
    centered=signals-signals.mean(axis=1,keepdims=True)
    norms=np.abs(centered).sum(axis=1,keepdims=True)
    target=np.divide(centered,norms,out=np.zeros_like(centered),where=norms>0)
    old=np.zeros(len(caps));rows=[]
    for desired in target:
        old=np.clip(old+np.clip(desired-old,-caps,caps),-caps,caps)
        rows.append(old.tolist())
    return rows


def metrics(data,weights):
    submitted=np.asarray(weights,dtype=float)
    returns=np.asarray(data['returns'],dtype=float)
    notional=float(data['notional'])
    caps=np.asarray(data['capacity_usd'],dtype=float)/notional
    spread=np.asarray(data['spread_bps'],dtype=float)/20000.
    impact=np.asarray(data['impact_coefficient'],dtype=float)
    adv=np.asarray(data['adv_usd'],dtype=float)
    previous=np.zeros(len(caps));actual=[];violation=False
    for desired in submitted:
        violation |= bool(np.any(np.abs(desired)>caps+1e-12) or np.any(np.abs(desired-previous)>caps+1e-12))
        previous=np.clip(previous+np.clip(desired-previous,-caps,caps),-caps,caps)
        actual.append(previous.copy())
    positions=np.asarray(actual)
    changes=np.diff(np.vstack([np.zeros(len(caps)),positions]),axis=0)
    def trade_cost(delta):
        magnitude=np.abs(delta)
        return np.sum(magnitude*(spread+impact*np.sqrt(magnitude*notional/adv)/100.),axis=-1)
    gross=np.sum(positions*returns,axis=1)
    net=gross-trade_cost(changes)
    net[-1]-=float(trade_cost(positions[-1]))
    edge=float(np.mean(gross))
    holding=float(np.mean(2*trade_cost(positions))/edge) if edge>0 else math.inf
    return {'net_sharpe':float(math.sqrt(252)*np.mean(net)/max(float(np.std(net)),1e-12)),
            'breakeven_holding_days':holding,'capacity_violation':violation,
            'gross_mean':edge,'gross_sharpe':float(math.sqrt(252)*edge/max(float(np.std(gross)),1e-12)),
            'total_cost':float(np.sum(trade_cost(changes))+trade_cost(positions[-1]))}
