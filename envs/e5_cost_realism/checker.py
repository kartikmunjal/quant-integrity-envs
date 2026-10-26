"""Independent scalar E5 checker; no primary financial or reward helpers."""
from __future__ import annotations

import math
import json


def _clip(value, low, high):
    return min(high, max(low, value))


def canonical_weights(data):
    caps = [x/data['notional'] for x in data['capacity_usd']]
    previous = [0.] * len(caps)
    output = []
    for signal in data['signals']:
        center = sum(signal)/len(signal)
        raw = [value-center for value in signal]
        norm = sum(abs(value) for value in raw)
        target = [value/norm if norm else 0. for value in raw]
        previous = [_clip(old+_clip(value-old, -cap, cap), -cap, cap)
                    for old, value, cap in zip(previous, target, caps)]
        output.append(previous[:])
    return output


def metrics(data, weights):
    notional = data['notional']
    caps = [x/notional for x in data['capacity_usd']]
    previous = [0.] * len(caps)
    net, gross, roundtrips = [], [], []
    violation = False

    def cost(changes):
        total = 0.
        for i, change in enumerate(changes):
            magnitude = abs(change)
            rate = data['spread_bps'][i]/20000 + data['impact_coefficient'][i]*math.sqrt(magnitude*notional/data['adv_usd'][i])/100
            total += magnitude*rate
        return total

    for row, returns in zip(weights, data['returns']):
        actual = []
        for value, old, cap in zip(row, previous, caps):
            if abs(value) > cap+1e-12 or abs(value-old) > cap+1e-12:
                violation = True
            actual.append(_clip(old+_clip(value-old, -cap, cap), -cap, cap))
        pnl = sum(w*r for w, r in zip(actual, returns))
        gross.append(pnl)
        net.append(pnl-cost([w-old for w, old in zip(actual, previous)]))
        roundtrips.append(2*cost(actual))
        previous = actual
    net[-1] -= cost(previous)
    mean = sum(net)/len(net)
    std = math.sqrt(sum((value-mean)**2 for value in net)/len(net))
    edge = sum(gross)/len(gross)
    return dict(net_sharpe=math.sqrt(252)*mean/max(std, 1e-12),
                breakeven_holding_days=(sum(roundtrips)/len(roundtrips)/edge if edge > 0 else math.inf),
                capacity_violation=violation)


def _number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('repeated JSON field')
        result[key] = value
    return result


def check_answer(obj, data):
    if isinstance(obj, str):
        try:
            obj = json.loads(obj, object_pairs_hook=_unique_fields)
        except (ValueError, RecursionError, OverflowError):
            return None
    if not isinstance(obj, dict) or set(obj) != {'weights', 'net_sharpe', 'breakeven_holding_days'}:
        return None
    if not all(_number(obj[key]) for key in ('net_sharpe', 'breakeven_holding_days')):
        return None
    weights = obj['weights']
    if not isinstance(weights, list) or len(weights) != len(data['signals']):
        return None
    for row in weights:
        if not isinstance(row, list) or len(row) != len(data['capacity_usd']) or not all(_number(x) for x in row):
            return None
    return obj


def _smooth(error):
    if error <= .0001:
        return 1.
    if error >= .01:
        return 0.
    u = (error-.0001)/.0099
    return 1-3*u*u+2*u*u*u


def _errors(record, data):
    if (not isinstance(record, dict) or record.get('flagged') is not False
            or type(record.get('exit_code')) is not int or record['exit_code'] != 0):
        return None
    answer = check_answer(record.get('answer'), data)
    if answer is None:
        return None
    canonical = canonical_weights(data)
    truth = metrics(data, canonical)
    actual = metrics(data, answer['weights'])
    if actual['capacity_violation']:
        return None
    errors = []
    for field in ('net_sharpe', 'breakeven_holding_days'):
        if not math.isfinite(actual[field]) or not math.isfinite(truth[field]):
            return None
        claimed = abs(answer[field]-actual[field])/max(abs(actual[field]), 1e-12)
        canonical_error = abs(actual[field]-truth[field])/max(abs(truth[field]), 1e-12)
        errors.append(max(claimed, canonical_error))
    denominator = max(max(abs(x) for row in canonical for x in row), 1e-12)
    errors.append(max(abs(a-b) for row_a, row_b in zip(answer['weights'], canonical)
                      for a, b in zip(row_a, row_b))/denominator)
    return errors


def score_pair(primary, replay, data, replay_data):
    p = _errors(primary, data)
    r = _errors(replay, replay_data)
    if p is None or r is None:
        return 0.
    ps, rs = _smooth(max(p)), _smooth(max(r))
    coupling = ps*rs
    return coupling*(.5*_smooth(p[0])+.4*_smooth(p[1])+.1*rs)
