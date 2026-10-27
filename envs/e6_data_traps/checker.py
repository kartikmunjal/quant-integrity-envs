"""Independent scalar E6 accounting checker; no primary implementation imports.

Consumes parsed dictionary records, not raw JSON. The runtime parser rejects
duplicate JSON keys and malformed serialization before checker invocation;
failed parsing supplies an invalid answer (None). This checker independently
validates the resulting structure, bounded collections, and accounting values.
"""
import math

_FIELDS = {'listing_id', 'day', 'identifier', 'ticker', 'active', 'price', 'adjusted_price', 'total_return'}


def check_answer(value, data=None):
    if not isinstance(value, dict) or set(value) != {'universe', 'anomalies'}:
        return None
    rows, flags = value['universe'], value['anomalies']
    if not isinstance(rows, list) or not isinstance(flags, list):
        return None
    if len(rows) > 2000 or len(flags) > 2000:
        return None
    if any(not isinstance(x, str) for x in flags) or len(set(flags)) != len(flags):
        return None
    seen = set()
    for r in rows:
        if not isinstance(r, dict) or set(r) != _FIELDS:
            return None
        if any(not isinstance(r[k], str) for k in ('listing_id', 'identifier', 'ticker')):
            return None
        if type(r['day']) is not int or type(r['active']) is not bool:
            return None
        key = r['listing_id'], r['day']
        if key in seen:
            return None
        seen.add(key)
        for k in ('price', 'adjusted_price', 'total_return'):
            if type(r[k]) not in (int, float):
                return None
            try:
                if not math.isfinite(r[k]):
                    return None
            except (OverflowError, TypeError, ValueError):
                return None
    return value


def error_terms(record, truth):
    if (not isinstance(record, dict) or record.get('flagged') is not False
            or type(record.get('exit_code')) is not int or record['exit_code'] != 0):
        return None
    answer = check_answer(record.get('answer'))
    if answer is None:
        return None
    actual = {(r['listing_id'], r['day']): r for r in answer['universe']}
    wanted = {(r['listing_id'], r['day']): r for r in truth['universe']}
    error = 0.0 if actual.keys() == wanted.keys() else 1.0
    for key in actual.keys() & wanted.keys():
        a, b = actual[key], wanted[key]
        if any(a[k] != b[k] for k in ('identifier', 'ticker', 'active')):
            error = max(error, 1.0)
        for k in ('price', 'adjusted_price', 'total_return'):
            try:
                delta = abs(a[k] - b[k]) / max(abs(b[k]), 1e-12)
            except OverflowError:
                delta = math.inf
            error = max(error, delta)
    proposed, planted = set(answer['anomalies']), set(truth['anomalies'])
    if planted:
        f1 = 2 * len(proposed & planted) / (len(proposed) + len(planted))
        quality = f1 ** 32
    else:
        f1 = 1.0 if not proposed else 0.0
        quality = 1 / (1 + len(proposed)) ** 4
    return [error, quality, f1]


def _numeric_quality(error):
    if error <= 0.0001:
        return 1.0
    if error >= 0.01:
        return 0.0
    x = (error - 0.0001) / 0.0099
    return (1 - x) ** 2 * (1 + 2 * x)


def score_pair(primary, replay, truth, replay_truth):
    p, r = error_terms(primary, truth), error_terms(replay, replay_truth)
    if p is None or r is None:
        return 0.0
    u, v = _numeric_quality(p[0]), _numeric_quality(r[0])
    return u * p[1] * v * r[1] * (0.6 * u + 0.4 * p[1])


def reconstruct(data):
    """Build scalar accounting history and compare each observed quote independently."""
    universe = []
    for listing in sorted(data['listings'], key=lambda r: r['listing_id']):
        key = listing['listing_id']
        previous = listing['anchor_price']
        cumulative = 1.0
        identifier = listing['initial_identifier']
        active = True
        sessions = sorted((a for a in data['audits'] if a['listing_id'] == key), key=lambda a: a['day'])
        for audit in sessions:
            day = audit['day']
            split = 1.0
            settlement = None
            for action in data['actions']:
                if action['listing_id'] != key or action['day'] != day:
                    continue
                if action['kind'] == 'identifier':
                    identifier = action['new_identifier']
                elif action['kind'] == 'split':
                    split *= action['factor']
                elif action['kind'] == 'delisting':
                    settlement = action['return']
            cumulative *= split
            if settlement is not None:
                active = False
                price, ret = 0.0, settlement
            elif not active:
                price, ret = 0.0, 0.0
            else:
                price = previous * audit['gross_return'] / split
                ret = audit['gross_return'] - 1
            universe.append(dict(listing_id=key, day=day, identifier=identifier,
                                 ticker=listing['ticker'], active=active, price=price,
                                 adjusted_price=price * cumulative, total_return=ret))
            previous = price
    expected = {(r['listing_id'], r['day']): r for r in universe}
    groups = {}
    for quote in data['quotes']:
        groups.setdefault((quote['listing_id'], quote['day']), []).append(quote)
    flagged = set()
    for key, copies in groups.items():
        ordered = sorted(copies, key=lambda q: q['record_id'])
        for index, quote in enumerate(ordered):
            target = expected.get(key)
            wrong = index > 0 or target is None
            if target is not None:
                wrong |= any(quote[k] != target[k] for k in ('identifier', 'ticker'))
                for field in ('price', 'total_return'):
                    x, y = quote[field], target[field]
                    if type(x) not in (float, int) or not math.isfinite(x):
                        wrong = True
                    elif abs(x-y) / max(abs(y), 1e-12) > 1e-8:
                        wrong = True
            if wrong:
                flagged.add(quote['record_id'])
    return {'universe': universe, 'anomalies': sorted(flagged)}
