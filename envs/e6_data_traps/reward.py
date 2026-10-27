"""Continuous E6 reward from protected truth and actual replay records."""
import json
import math
import numpy as np

FIELDS={'listing_id','day','identifier','ticker','active','price','adjusted_price','total_return'}
NUMERIC=('price','adjusted_price','total_return')

def _unique(pairs):
    out={}
    for key,value in pairs:
        if key in out:raise ValueError('duplicate JSON key')
        out[key]=value
    return out

def check_answer(value,data=None):
    try:
        if isinstance(value,str):value=json.loads(value,object_pairs_hook=_unique)
        if type(value) is not dict or set(value)!={'universe','anomalies'}:return None
        rows=value['universe'];flags=value['anomalies']
        if type(rows) is not list or type(flags) is not list or len(rows)>2000 or len(flags)>2000:return None
        if any(type(v) is not str for v in flags) or len(set(flags))!=len(flags):return None
        keys=set()
        for row in rows:
            if type(row) is not dict or set(row)!=FIELDS:return None
            if any(type(row[k]) is not str for k in ('listing_id','identifier','ticker')):return None
            if type(row['day']) is not int or type(row['active']) is not bool:return None
            if any(type(row[k]) not in (int,float) or not math.isfinite(float(row[k])) for k in NUMERIC):return None
            key=(row['listing_id'],row['day'])
            if key in keys:return None
            keys.add(key)
        return value
    except (ValueError,TypeError,OverflowError,RecursionError):return None

def quality(error):
    if error<=.0001:return 1.
    if error>=.01:return 0.
    u=(error-.0001)/.0099
    return (1-u)**2*(1+2*u)

def error_terms(record,truth):
    if not isinstance(record,dict) or record.get('flagged') is not False or type(record.get('exit_code')) is not int or record['exit_code']!=0:return None
    answer=check_answer(record.get('answer'))
    if answer is None:return None
    expected={(r['listing_id'],r['day']):r for r in truth['universe']};submitted={(r['listing_id'],r['day']):r for r in answer['universe']}
    error=float(set(expected)!=set(submitted))
    for key in set(expected)&set(submitted):
        a=submitted[key];b=expected[key]
        if any(a[k]!=b[k] for k in ('identifier','ticker','active')):error=max(error,1.)
        av=np.array([a[k] for k in NUMERIC]);bv=np.array([b[k] for k in NUMERIC])
        with np.errstate(over='ignore',invalid='ignore'):
            error=max(error,float(np.max(np.abs(av-bv)/np.maximum(np.abs(bv),1e-12))))
    flags=set(answer['anomalies']);correct=set(truth['anomalies']);tp=len(flags&correct)
    f1=2*tp/(len(flags)+len(correct)) if flags or correct else 1.
    anomaly=f1**32 if correct else (1+len(flags))**-4
    return [error,anomaly,f1]

def score_pair(primary,replay,truth,replay_truth):
    p=error_terms(primary,truth);r=error_terms(replay,replay_truth)
    if p is None or r is None:return 0.
    u=quality(p[0]);fresh=quality(r[0]);coupled=u*p[1]*fresh*r[1]
    return coupled*(.6*u+.4*p[1])
