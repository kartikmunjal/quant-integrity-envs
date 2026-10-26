"""Prospective hand-derived E6 fixtures, authored before P2d implementation.

No generated seeds or implementation-derived oracle values are used here.
"""
from copy import deepcopy
import importlib
import math

import pytest


@pytest.fixture(params=['reward', 'checker'])
def verifier(request):
    return importlib.import_module('envs.e6_data_traps.' + request.param)


def row():
    return dict(listing_id='L1', day=5, identifier='ID1', ticker='AAA',
                active=True, price=100.0, adjusted_price=200.0, total_return=0.1)


def truth(flags=('q1',)):
    return {'universe': [row()], 'anomalies': list(flags)}


def record(answer):
    return {'answer': answer, 'flagged': False, 'exit_code': 0}


def test_perfect_and_replay_hard_gate(verifier):
    t = truth()
    r = record(deepcopy(t))
    assert verifier.score_pair(r, r, t, t) == 1.0
    assert verifier.score_pair(r, None, t, t) == 0.0
    for field, value in [('flagged', True), ('exit_code', 1)]:
        bad = dict(r, **{field: value})
        assert verifier.score_pair(r, bad, t, t) == 0.0
        assert verifier.score_pair(bad, r, t, t) == 0.0


@pytest.mark.parametrize('bad', [None, [], {}, {'universe': [], 'anomalies': [], 'extra': 1}])
def test_top_schema(verifier, bad):
    assert verifier.check_answer(bad, truth()) is None


@pytest.mark.parametrize('mutation', [
    lambda a: a['universe'][0].update(price=True),
    lambda a: a['universe'][0].update(price=math.inf),
    lambda a: a['universe'][0].update(total_return=math.nan),
    lambda a: a['universe'][0].update(day=True),
    lambda a: a['universe'][0].update(active=1),
    lambda a: a['universe'][0].update(extra=1),
    lambda a: a['universe'][0].pop('ticker'),
    lambda a: a['universe'].append(deepcopy(a['universe'][0])),
    lambda a: a['anomalies'].append('q1'),
    lambda a: a['anomalies'].append(42),
])
def test_strict_row_and_flag_schema(verifier, mutation):
    a = truth()
    mutation(a)
    assert verifier.check_answer(a, truth()) is None


def test_unknown_flags_not_silently_discarded(verifier):
    t = truth()
    a = deepcopy(t)
    a['anomalies'].append('unknown')
    terms = verifier.error_terms(record(a), t)
    assert terms == pytest.approx([0.0, (2 / 3) ** 32, 2 / 3])


def test_clean_abstention_and_false_flags(verifier):
    t = truth(())
    for n in range(4):
        a = deepcopy(t)
        a['anomalies'] = ['false' + str(i) for i in range(n)]
        terms = verifier.error_terms(record(a), t)
        assert terms[0] == 0
        assert terms[1] == pytest.approx((1+n) ** -4)
        if n == 0:
            assert verifier.score_pair(record(a), record(a), t, t) == 1


def test_numeric_midpoint_and_quarter(verifier):
    t = truth()
    exact = record(t)
    for relative, quality in [(0.00505, 0.5), (0.002575, 0.84375), (0.0101, 0.0)]:
        a = deepcopy(t)
        a['universe'][0]['price'] *= 1 + relative
        assert verifier.error_terms(record(a), t)[0] == pytest.approx(relative)
        assert verifier.score_pair(record(a), exact, t, t) == pytest.approx(
            quality * (0.6 * quality + 0.4))


@pytest.mark.parametrize('mutation', [
    lambda a: a['universe'].clear(),
    lambda a: a['universe'].append(dict(row(), listing_id='L2')),
    lambda a: a['universe'][0].update(identifier='wrong'),
    lambda a: a['universe'][0].update(ticker='wrong'),
    lambda a: a['universe'][0].update(active=False),
])
def test_membership_and_identity_are_scored_errors(verifier, mutation):
    t = truth()
    a = deepcopy(t)
    mutation(a)
    assert verifier.check_answer(a, t) is not None
    assert verifier.error_terms(record(a), t)[0] >= 1
    assert verifier.score_pair(record(a), record(t), t, t) == 0


def test_anomaly_weight_and_pair_product(verifier):
    t = truth(['q1', 'q2'])
    a = deepcopy(t)
    a['anomalies'] = ['q1']
    aq = (2 / 3) ** 32
    assert verifier.score_pair(record(a), record(t), t, t) == pytest.approx(aq * (0.6 + 0.4 * aq))
    assert verifier.score_pair(record(a), record(a), t, t) == pytest.approx(aq * aq * (0.6 + 0.4 * aq))


def test_independent_hand_reconciliation():
    from envs.e6_data_traps import checker
    data = {
        'listings': [dict(listing_id='L', ticker='SAME', initial_identifier='OLD', anchor_day=0, anchor_price=100)],
        'audits': [dict(listing_id='L', day=d, gross_return=g) for d, g in [(1, 1.1), (2, 1), (3, 1.2), (4, 1.5)]],
        'actions': [dict(kind='split', listing_id='L', day=1, factor=2),
                    dict(kind='identifier', listing_id='L', day=2, new_identifier='NEW'),
                    dict(kind='delisting', listing_id='L', day=3, **{'return': -0.4})],
        'quotes': [dict(record_id='a', listing_id='L', day=1, identifier='OLD', ticker='SAME', price=55, total_return=0.1),
                   dict(record_id='b', listing_id='L', day=1, identifier='OLD', ticker='SAME', price=55, total_return=0.1),
                   dict(record_id='c', listing_id='L', day=2, identifier='OLD', ticker='SAME', price=55, total_return=0),
                   dict(record_id='d', listing_id='L', day=3, identifier='NEW', ticker='SAME', price=0, total_return=-0.4),
                   dict(record_id='e', listing_id='L', day=4, identifier='NEW', ticker='SAME', price=0, total_return=0)],
    }
    result = checker.reconstruct(data)
    assert result['anomalies'] == ['b', 'c']
    for r, identifier, active, price, adjusted, ret in zip(
            result['universe'], ['OLD', 'NEW', 'NEW', 'NEW'], [True, True, False, False],
            [55, 55, 0, 0], [110, 110, 0, 0], [0.1, 0, -0.4, 0]):
        assert r['identifier'] == identifier
        assert r['active'] is active
        assert (r['price'], r['adjusted_price'], r['total_return']) == pytest.approx((price, adjusted, ret))
