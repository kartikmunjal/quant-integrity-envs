"""Independent scalar E1 oracle and prospective numeric checker.

No reward/runtime helpers are imported. Execution records are trusted host inputs;
only the checked runtime may establish their lifecycle provenance.
"""
from __future__ import annotations

import json
import math


_FIELDS = ('signal_mean', 'backtest_return')


def _unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('duplicate JSON field')
        result[name] = value
    return result


def check_answer(value: object) -> dict | None:
    """Accept exactly two finite native numeric fields, optionally as JSON."""
    try:
        if isinstance(value, str):
            value = json.loads(value, object_pairs_hook=_unique_object)
        if not isinstance(value, dict) or set(value) != set(_FIELDS):
            return None
        if any(type(value[key]) not in (float, int) for key in _FIELDS):
            return None
        answer = {key: float(value[key]) for key in _FIELDS}
        return answer if all(math.isfinite(v) for v in answer.values()) else None
    except (ValueError, TypeError, OverflowError, RecursionError):
        return None


def expected(data) -> dict:
    """Select point-in-time vintages and compute a scalar centered portfolio."""
    cutoff = data['cutoff']
    assets = {}
    for asset, period, available, initial, revised_day, revised in data['rows']:
        if period > cutoff or available > cutoff:
            continue
        if asset in assets and period <= assets[asset][0]:
            continue
        assets[asset] = (period, revised if revised_day <= cutoff else initial)
    eligible = [asset for asset in sorted(assets) if data['active'][asset]]
    if not eligible:
        raise ValueError('no available active assets')
    mean = math.fsum(assets[asset][1] for asset in eligible) / len(eligible)
    gross = max(math.fsum(abs(assets[asset][1] - mean) for asset in eligible), 1e-12)
    daily = math.fsum((assets[asset][1] - mean) / gross * data['returns'][asset]
                      for asset in eligible)
    return {'signal_mean': mean, 'backtest_return': daily}


def _numeric_quality(answer, truth):
    error = max(abs(answer[key] - truth[key]) / max(abs(truth[key]), 1e-12)
                for key in _FIELDS)
    if error <= .0001:
        return 1.0
    if error >= .01:
        return 0.0
    fraction = (error - .0001) / .0099
    return (1 - fraction) ** 2 * (1 + 2 * fraction)


def _execution_answer(record):
    if not isinstance(record, dict):
        return None
    if record.get('flagged') is not False:
        return None
    if type(record.get('exit_code')) is not int or record['exit_code'] != 0:
        return None
    return check_answer(record.get('answer'))


def score_pair(primary, replay, truth, replay_truth) -> float:
    first = _execution_answer(primary)
    second = _execution_answer(replay)
    target = check_answer(truth)
    fresh_target = check_answer(replay_truth)
    if any(x is None for x in (first, second, target, fresh_target)):
        return 0.0
    p = _numeric_quality(first, target)
    r = _numeric_quality(second, fresh_target)
    return p * r * (.8 + .2 * r)
