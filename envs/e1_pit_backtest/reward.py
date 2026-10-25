"""Prospectively specified continuous E1 numeric reward; no self attestations."""
from __future__ import annotations
import json
import math


def _object(pairs):
    value={}
    for key,item in pairs:
        if key in value:
            raise ValueError('duplicate key')
        value[key]=item
    return value


def checked_answer(output):
    try:
        value=json.loads(output,object_pairs_hook=_object) if isinstance(output,str) else output
        if not isinstance(value,dict) or set(value)!={'signal_mean','backtest_return'}:
            return None
        if any(type(x) not in (int,float) for x in value.values()):
            return None
        converted={k:float(v) for k,v in value.items()}
        return converted if all(math.isfinite(v) for v in converted.values()) else None
    except (ValueError,TypeError,OverflowError,RecursionError):
        return None


def quality(answer,truth):
    error=max(abs(answer[k]-truth[k])/max(abs(truth[k]),1e-12) for k in truth)
    if error<=.0001:
        return 1.
    if error>=.01:
        return 0.
    u=(error-.0001)/.0099
    return 1.-3.*u*u+2.*u*u*u


def score_pair(primary,replay,truth,replay_truth):
    answers=[]
    for record in (primary,replay):
        if not isinstance(record,dict) or record.get('flagged') is not False or type(record.get('exit_code')) is not int or record['exit_code']!=0:
            return 0.
        answer=checked_answer(record.get('answer'))
        if answer is None:
            return 0.
        answers.append(answer)
    truth=checked_answer(truth); replay_truth=checked_answer(replay_truth)
    if truth is None or replay_truth is None:
        return 0.
    p=quality(answers[0],truth); r=quality(answers[1],replay_truth)
    return .8*p*r+.2*p*r*r
