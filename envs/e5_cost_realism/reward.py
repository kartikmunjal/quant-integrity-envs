"""Continuous E5 reward from server-computed financial metrics and replay evidence."""
from __future__ import annotations
import json
import math
from .finance import canonical_weights,metrics


def _pairs(pairs):
    obj={}
    for key,value in pairs:
        if key in obj:raise ValueError('duplicate key')
        obj[key]=value
    return obj


def _finite(value):
    try:return type(value) in (int,float) and math.isfinite(float(value))
    except (ValueError,TypeError,OverflowError):return False


def check_answer(value,data):
    try:
        if isinstance(value,str):value=json.loads(value,object_pairs_hook=_pairs)
        if not isinstance(value,dict) or set(value)!={'weights','net_sharpe','breakeven_holding_days'}:return None
        if not all(_finite(value[k]) for k in ('net_sharpe','breakeven_holding_days')):return None
        weights=value['weights']
        if not isinstance(weights,list) or len(weights)!=len(data['signals']):return None
        if any(not isinstance(row,list) or len(row)!=len(data['capacity_usd']) or not all(_finite(v) for v in row) for row in weights):return None
        return value
    except (ValueError,TypeError,RecursionError,OverflowError):return None


def quality(error):
    if error<=1e-4:return 1.
    if error>=.01:return 0.
    u=(error-1e-4)/.0099
    return (1-u)**2*(1+2*u)


def error_terms(record,data):
    if not isinstance(record,dict) or record.get('flagged') is not False or type(record.get('exit_code')) is not int or record['exit_code']!=0:return None
    answer=check_answer(record.get('answer'),data)
    if answer is None:return None
    target=canonical_weights(data);truth=metrics(data,target);actual=metrics(data,answer['weights'])
    if actual['capacity_violation']:return None
    errors=[]
    for field in ('net_sharpe','breakeven_holding_days'):
        if not _finite(actual[field]) or not _finite(truth[field]):return None
        errors.append(max(abs(answer[field]-actual[field])/max(abs(actual[field]),1e-12),
            abs(actual[field]-truth[field])/max(abs(truth[field]),1e-12)))
    scale=max(max(abs(v) for row in target for v in row),1e-12)
    errors.append(max(abs(a-b) for row,expected in zip(answer['weights'],target) for a,b in zip(row,expected))/scale)
    return errors


def score_pair(primary,replay,data,replay_data):
    first=error_terms(primary,data);fresh=error_terms(replay,replay_data)
    if first is None or fresh is None:return 0.
    p=quality(max(first));r=quality(max(fresh));coupled=p*r
    return .5*coupled*quality(first[0])+.4*coupled*quality(first[1])+.1*coupled*r
