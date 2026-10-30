"""Beta(4,2) raw proper loss and explicitly non-proper bounded task reward."""
import json
import math

L_REF = 3 / 400


def raw_loss(q, y):
    if type(q) not in (int, float) or not math.isfinite(q) or not 0 <= q <= 1 or type(y) not in (int, bool) or y not in (0, 1):
        raise ValueError('invalid probability or binary truth')
    if y:
        return max(0., 1/60-q**4/4+2*q**5/5-q**6/6)
    return q**5/5-q**6/6


def execution_reward(probabilities, truth):
    if not probabilities or len(probabilities) != len(truth):
        raise ValueError('nonempty matching vectors required')
    loss = math.fsum(raw_loss(q, y) for q, y in zip(probabilities, truth, strict=True))/len(truth)
    return max(0., min(1., 1-loss/L_REF))


def combine_executions(primary, replay, *, valid_schema=True, safe_execution=True, tamper=False):
    if not valid_schema or not safe_execution or tamper:
        return 0.
    if any(type(q) not in (int,float) or not math.isfinite(q) or not 0 <= q <= 1 for q in (primary,replay)):
        return 0.
    return min(primary, replay)


def parse_submission(output, ids):
    if not isinstance(output, (str, bytes)) or len(output) > 65536 or len(ids) != len(set(ids)):
        raise ValueError('bounded JSON and unique IDs required')
    def pairs(items):
        value={}
        for key,item in items:
            if key in value: raise ValueError('duplicate key')
            value[key]=item
        return value
    def invalid(value):
        raise ValueError('nonfinite JSON')
    try:
        value=json.loads(output, object_pairs_hook=pairs, parse_constant=invalid)
    except (TypeError, ValueError, RecursionError, UnicodeError) as exc:
        raise ValueError('invalid JSON') from exc
    if not isinstance(value,dict) or set(value) != set(ids):
        raise ValueError('exact candidate IDs required')
    for probability in value.values():
        raw_loss(probability,0)
    return value
